
from traceback import extract_stack

from django.conf import settings
from django.contrib import admin
from django.contrib.admin.sites import AlreadyRegistered, AdminSite
from django.core.mail import mail_admins as django_mail_admins
from django.db.models import get_models, get_app

from MHLogin.utils import logger
from MHLogin.utils.twilio_utils import client


def registerallmodels(app):
	models = get_app(app)
	for model in get_models(models):
		try:
			admin.site.register(model)
		except AlreadyRegistered:
			pass


def mail_admins(subject, message, fail_silently=False, connection=None,
			html_message=None, send_sms=False, include_stack=True):
	""" Helper wrapper to send mail to admins.  If there are problems sending
	mail to admins a critical notification is logged as well as notifification
	via sms.  If the caller wishes they can also forward an sms message."""
	try:
		if include_stack:  # Typically true except in ExceptionDumpMiddleware
			tracemsg = '\n'.join('...%s:%d in %s() %s' % (fname[-32:], lnum, fn, line.strip()
					if line else '') for fname, lnum, fn, line in extract_stack())
			message = "%s\n\n\nTraceback:\n%s" % (message, tracemsg)

			if html_message:
				html_message = "%s<br/><br/><br/>Traceback:<br/>%s" % \
					(html_message, '<br/>'.join(tracemsg.split('\n')))

		django_mail_admins(subject, message, fail_silently, connection, html_message)
		if send_sms:
			sms_admins(message)
	except (Exception), e:
		exception_msg = "Failure in mail_admins, exception: %s" % (repr(e))
		msg = "mail_admins failure, exception details in previous log. %s" % str(message)
		logger.critical(exception_msg)
		logger.critical(msg)
		sms_admins(exception_msg)


def sms_admins(msg, mobile_nums=None):
	""" Helper to send sms message to admins' mobile phone. If mobile_nums is defined
	as an array of mobile phone strings that will be used instead of the mobile
	numbers stored in the Administrator user table.
	"""
	if mobile_nums is None:
		from MHLogin.MHLUsers.models import Administrator
		mobile_nums = Administrator.objects.all().values_list('user__mobile_phone', flat=True)
	else:
		mobile_nums = mobile_nums if isinstance(mobile_nums, (list, set)) else [mobile_nums]

	try:
		from MHLogin.DoctorCom.SMS.views import msg_fragmenter  # TODO: move to utils?
		frags = msg_fragmenter(msg)
	except Exception:  # limited to 100 fragments, if too large send first
		frags = [msg[:159]]

	for mobile in mobile_nums:
		try:
			for frag in frags:
				client.sms.messages.create(body=frag, to=mobile,
					from_=settings.TWILIO_CALLER_ID)
		except (Exception), e:
			logger.critical("Unable to send sms to admins: %s" % str(e))


def password_change(self, request):
	"""
	Patch Admin Site's password_change for the admin, we need to pass in our custom
	Form.  Unfortunately AdminSite does not have a password_change_form variable in
	self as does the UserAdmins do, so redirect to our password form
	"""
	from MHLogin.MHLUsers.views import change_password
	return change_password(request, redirect_view='admin:password_change_done')

# monkey patch AdminSite's password change and redirect to ours
setattr(AdminSite, password_change.__name__, password_change)

