
import json
import string
import random
from datetime import datetime

from django.contrib.admin.models import LogEntry, ADDITION
from django.contrib.auth import logout
from django.contrib.sessions.models import Session
from django.contrib.sites.models import RequestSite
from django.core import signing
from django.core.mail import send_mail
from django.core.serializers.json import DjangoJSONEncoder
from django.core.urlresolvers import reverse
from django.forms.forms import NON_FIELD_ERRORS
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext, loader
from django.utils.translation import ugettext as _

from MHLogin.KMS.utils import generate_new_user_keys
from MHLogin.utils.decorators import ratelimitview
from MHLogin.utils.admin_utils import mail_admins
from MHLogin.MHLUsers.models import MHLUser, PasswordResetLog
from MHLogin.MHLUsers.forgotpassword.forms import PasswordForgotForm, PasswordResetForm,\
	FormErrors


LOG_ACTION_ID = "MHLogin.MHLUsers.forgotpassword"
SOME_SALT = "MHLogin.MHLUsers.forgotpassword.views"


@ratelimitview(limit=50)  # 50 per day per remote
def forgot_password(request):
	""" start state of password recovery/change process """
	context, resp = RequestContext(request), None

	if request.method == "POST":
		form = PasswordForgotForm(data=request.POST, error_class=FormErrors)
		context['form'] = form
		if form.is_valid():
			# if here user entered at least two fields
			user = MHLUser.objects.filter(**form.get_query())
			if user.exists() and user.count() == 1:
				send_recovery_email(request, user.get())
				# redirect to confirmation email sent			
				resp = HttpResponseRedirect(reverse('email_sent'))
			else:
				form._errors[NON_FIELD_ERRORS] = form.error_class([_("User not found.")])
	else:
		context['form'] = PasswordForgotForm(error_class=FormErrors)

	return resp or render_to_response('forgotpassword.html', context)


def email_sent(request):
	""" Recovery email sent """
	return render_to_response('email_sent.html', RequestContext(request))


@ratelimitview(limit=50)  # 50 per day per remote
def password_change(request, token, tempcode):
	""" Process url from email and user's input """
	context, resp = RequestContext(request), None

	user, log = validate_user(token, tempcode)
	if user and log:
		context['username'] = user.username
		context['goodsig'] = True
		if request.method == "POST":
			form = PasswordResetForm(user, data=request.POST, error_class=FormErrors)
			context['form'] = form
			if form.is_valid():
				log.delete()
				# send notifications and change their password
				PasswordResetLog.objects.create(user=user, reset=True,
					requestor=user, requestor_ip=request.META['REMOTE_ADDR'],
					reset_ip=request.META['REMOTE_ADDR'], reset_timestamp=datetime.now())
				# if TODO: rm #2115 connect/authenticate w/KMS server OK:
				#     KMS server recrypt user's private keys, pwresetlog resolved=True
				# else:  ...what we do now
				generate_new_user_keys(user, form.cleaned_data['password2'])
				user.set_password(form.cleaned_data['password2'])
				user.save()
				# remove any active sessions before redirect
				get_active_sessions(user).delete()
				# rare corner case if user logged in with this request.session
				if request.user.is_authenticated():
					logout(request)
				resp = HttpResponseRedirect(reverse('password_complete'))
		else:
			context['form'] = PasswordResetForm(user, error_class=FormErrors)

	# displays error page when invalid form or no context vars present
	return resp or render_to_response('newpassword.html', context)


def password_complete(request):
	""" Password change complete """
	return render_to_response('complete.html', RequestContext(request))


def validate_user(token, tempcode):
	""" Validate token and verify internal log and user exist """
	tup = None, None
	try:
		expire = 3600 * 4  # four hours
		user_pk, date = signing.loads(token, max_age=expire, salt=SOME_SALT)
		date = json.loads(date)
		# our first stab at signing... if trusted we don't need LogEntry or tempcode
		log = LogEntry.objects.filter(user__pk=user_pk, object_repr=LOG_ACTION_ID,
			action_flag=ADDITION, change_message=tempcode, action_time=date)
		user = MHLUser.objects.filter(pk=user_pk)
		tup = (user.get(), log) if user.exists() and log.exists() else tup
	except (signing.BadSignature, ValueError) as e:
		msg = "token: %s, tempcode: %s, exception: %s" % (token, tempcode, str(e))
		mail_admins("Expired token or invalid code", msg)
	return tup


def send_recovery_email(request, user):
	""" Helper to send email to user """
	popl = string.ascii_lowercase + string.digits
	tempcode = ''.join(random.sample(popl, 10))
	log = LogEntry.objects.create(user=user, object_repr=LOG_ACTION_ID,
		action_flag=ADDITION, change_message=tempcode)
	date = json.dumps(log.action_time, cls=DjangoJSONEncoder)

	site = RequestSite(request)
	context = {
		'sitedomain': site.domain,
		'username': user.username,
		'token': signing.dumps((user.pk, date), salt=SOME_SALT),
		'tempcode': tempcode,
		'secure': request.is_secure(),
	}
	subj = _('Password recovery from DoctorCom')
	body = loader.render_to_string('email.txt', context).strip()
	send_mail(subj, body, 'support@mdcom.com', [user.email])


def get_active_sessions(user):
	""" Helper to get all active sessions for user """
	active = [s.pk for s in Session.objects.filter(expire_date__gte=datetime.now())
		if user.pk == s.get_decoded().get('_auth_user_id')]	
	return Session.objects.filter(pk__in=active)

