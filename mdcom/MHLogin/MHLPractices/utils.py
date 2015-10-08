import datetime
import time
import random
import string
import uuid
import thread

from django.conf import settings
from django.db.models.query_utils import Q
from django.contrib.auth.models import User
from django.core.mail import send_mass_mail, send_mail
from django.template import Context, Template
from django.utils.translation import ugettext as _

from MHLogin.DoctorCom.Messaging.models import Message, MessageRecipient
from MHLogin.MHLUsers.models import Office_Manager, OfficeStaff, MHLUser, Provider
from MHLogin.utils.geocode import miles2latlong_range
from MHLogin.MHLCallGroups.Scheduler.models import EventEntry
from MHLogin.MHLPractices.models import PracticeLocation, Pending_Association
from MHLogin.MHLUsers.utils import getCurrentUserInfo, getCurrentUserMobile,get_fullname
from MHLogin.utils.constants import ALL_MEMBER_ROLE_TYPES, ROLE_TYPE,\
	ROLE_TYPE_MEMBER
from MHLogin.utils.timeFormat import convert_dt_to_utz
from MHLogin.apps.smartphone.v1.utils import notify_user_tab_changed


def get_practices_by_position(lat, longit, distance=None):
	if (not distance):
		distance = settings.PROXIMITY_RANGE
	latmin, latmax, longitmin, longitmax = miles2latlong_range(lat, longit, distance)
	return PracticeLocation.active_practice.filter(practice_lat__range=(latmin, latmax), 
		practice_longit__range=(longitmin, longitmax))


def set_practices_result(practices, request):
	current_user = getCurrentUserInfo(request)
	current_user_mobile = getCurrentUserMobile(current_user)
	if (practices):
		for practice in practices:
			has_manager = Office_Manager.active_objects.filter(practice__id=practice.id).exists()
			practice.has_manager = has_manager
			if current_user_mobile and settings.CALL_ENABLE:
				practice.call_available = bool(practice.practice_phone)\
												or (practice.backline_phone)
			else:
				practice.call_available = False
	return practices


def mail_managers(practice, subject, body, sender=None, **kwargs):
	"""
	Creates and sends an email to all practice managers with the given subject
	and body, from the optional argument sender.

	Note that the body will always be rendered with kwargs as the render
	context. Additionally, the following context variables are defined:

	- manager The MHLUser of the manager being emailed.
	- managers The list of MHLUsers of all managers

	:param practice: A PracticeLocation object or pk.
	:param subject: The subject the email should be sent with.
	:param body: The body of the email. This should be a string containing optional
		template markup. See the docstring for details of the render context.
	:param sender: (optional): The email address the email should be sent from. If
		this argument is omitted, the email is sent from settings.SERVER_EMAIL.
	:returns: None
	:raises: All exceptions from django.core.mail are passed.

	"""
	if (not sender):
		sender = settings.SERVER_EMAIL

	template = Template(body)
	context = Context(kwargs)

	officemanagers = Office_Manager.objects.filter(practice=practice).values_list('user', flat=True)
	officestaff = OfficeStaff.objects.filter(pk__in=officemanagers).values_list('user', flat=True)
	managers = MHLUser.objects.filter(pk__in=officestaff).values('first_name', 'last_name', 'email')

	context['managers'] = managers

	#emails = [] # Used to store the emails 
	#for manager in managers:
	#	send_mail()
	send_mass_mail(
		[
			[
				subject,
				template.render(
					_mail_managers_context_update(context, i)),
				sender,
				[i['email']]
			]
			for i in managers
		]
	)


def _mail_managers_context_update(context, manager):
	context['manager'] = manager
	return context


def message_managers(request, practice, subject, body, **kwargs):
	"""
	Creates and sends an email to all practice managers with the given subject
	and body, from the optional argument sender.

	Note that the body will always be rendered with kwargs as the render
	context. Additionally, the following context variables are defined:

	- manager: The MHLUser of the manager being emailed.
	- managers: The list of MHLUsers of all managers

	:param practice: A PracticeLocation object or pk.
	:param subject: The subject the email should be sent with.
	:param body: The body of the email. This should be a string containing optional
		template markup. See the docstring for details of the render context.
	:returns: None
	:raises: All exceptions from django.core.mail are passed.
	"""

	template = Template(body)
	context = Context(kwargs)

	officemanagers = Office_Manager.objects.filter(practice=practice).values_list('user', flat=True)
	officestaff = OfficeStaff.objects.filter(pk__in=officemanagers).values_list('user', flat=True)
	managers = list(User.objects.filter(pk__in=officestaff))

	#raise Exception(repr(managers))

	context['managers'] = managers

	#emails = [] # Used to store the emails 
	#for manager in managers:
	#	send_mail()

	msg = Message(
			sender=None,
			sender_site=None,
			subject=subject,
		)
	msg.save()
	msg_body = msg.save_body(template.render(context))
	for mgr in managers:
		MessageRecipient(message=msg, user=mgr).save()
	#msg.recipients.add(*managers),
	msg.send(request, msg_body)


def message_super_managers(request, practice, subject, body, **kwargs):
	"""
	Creates and sends a message t to all practice SUPER managers, if ANY exist with the given subject
	and body, from the optional argument sender.

	- manager: The MHLUser of the manager being emailed.
	- managers: The list of MHLUsers of all managers

	:param practice: A PracticeLocation object or pk.
	:param subject: The subject the email should be sent with.
	:param body: The body of the email. This should be a string containing optional
		template markup. See the docstring for details of the render context.
	:returns: None
	:raises: All exceptions from django.core.mail are passed.
	"""
	template = Template(body)
	context = Context(kwargs)

	officemanagers = Office_Manager.objects.filter(practice=practice, manager_role=2).\
		values_list('user', flat=True)
	officestaff = OfficeStaff.objects.filter(pk__in=officemanagers).\
		values_list('user', flat=True)
	managers = list(User.objects.filter(pk__in=officestaff))

	context['managers'] = managers

	if (len(managers) > 0):
		msg = Message(
			sender=None,
			sender_site=None,
			subject=subject,
		)
		msg.save()
		msg_body = msg.save_body(template.render(context))
		for mgr in managers:
			MessageRecipient(message=msg, user=mgr).save()

		msg.send(request, msg_body)	


def mail_add_association(request, subject, body, recipient, **kwargs):
	"""
	Creates and sends an email to a provider with the given subject
	and body, and sender.

	Note that the body will always be rendered with kwargs as the render
	context. Additionally, the following context variables are defined:

	:param subject: The subject the email should be sent with.
	:param body: The body of the email. This should be a string containing optional
		template markup. See the docstring for details of the render context.
	:param sender: The email address the email should be sent to
	:param recipient: The email address the email should be sent to
	:returns: None
	:raises: All exceptions from django.core.mail are passed.
	"""
	template = Template(body)
	context = Context(kwargs)
	sender = settings.SERVER_EMAIL

	#context['practice_name'] = practice_name
	email_body = template.render(context)

	send_mail(subject, email_body, sender, [recipient], fail_silently=False)


def get_level_by_staff(id, practice):
	"""
	get role value of this OfficeStaff. (ALL_MEMBER_ROLE_TYPES)
	:param id: staff's id
	:param practice: is an instance of PracticeLocation
	:returns: int
	"""
	try:
		o = Office_Manager.objects.get(user=id, practice=practice)
		return o.manager_role
	except:
		return 0


def get_role_display(role):
	"""
	get role displayed string.
	:param role: role's key, is an int value
	:returns: str
	"""
	if role is None:
		return ''
	try:
		role = int(role)
		return dict(ALL_MEMBER_ROLE_TYPES)[role]
	except:
		return ''


def get_role_options(current_role=None, practice=None):
	"""
	Get role options.
	:param current_role: current user's role.
	:param practice: is an instance of PracticeLocation
	:returns: tuple of role options
	"""
	ret_roles = ALL_MEMBER_ROLE_TYPES
	if practice is not None:
		ret_roles = ()
		if practice.get_setting_attr('can_have_manager'):
			ret_roles = ret_roles + ROLE_TYPE
		if practice.can_have_staff_member():
			ret_roles = ret_roles + ROLE_TYPE_MEMBER

	if current_role is not None:
		current_role = int(current_role)
		ret_roles_n = ()
		for role in ret_roles:
			if role[0] <= current_role:
				ret_roles_n = ret_roles_n + (role,)
		return ret_roles_n
	return ret_roles


def checkUserCrossDay(user):
	lst = EventEntry.objects.filter(oncallPerson=user)
	now = datetime.datetime.now()
	for i in lst:
		if (i.startDate < now and i.endDate > now) or (i.endDate < now):
			return False
	return True


#add by xlin in 20120410 to generate code with username, email, create time and 4 digit.
def getNewCreateCode(username):
	ctime = str(time.time())
	ctime = string.replace(ctime, '.', '')
	chars = username + ctime + uuid.uuid4().hex[0:4]
	code = r''.join([random.choice(chars) for x in range(50)])
	return code


def getCurrentPractice(user):
	user_id = user.id
	p = Provider.objects.filter(user__id=user_id)
	if p and p[0].current_practice:
		return p[0].current_practice.practice_name

	os = OfficeStaff.objects.filter(user__id=user_id)
	if os and os[0].current_practice:
		return os[0].current_practice.practice_name
	return ''


def changeCurrentPracticeForStaff(practice_id, muluser_id):
	"""
	Change office staff's current practice

	Note when changing office staff's current practice, system will change 
	his MHLUser's  address1, address2, city, state, zip, lat, longit
	by using the new practice's related fields.

	:param practice_id: new practice's id.
	:param muluser: the office staff's MHLUser object.
	:returns: current practice
	:raises: PracticeLocation.DoesNotExist, .
	"""
	if not practice_id:
		raise PracticeLocation.DoesNotExist

	if not muluser_id:
		raise MHLUser.DoesNotExist

	practice = PracticeLocation.objects.get(pk = practice_id)
	staff = OfficeStaff.objects.get(user__id=muluser_id)
	old_cur_prac_id = None
	if staff.current_practice is not None:
		old_cur_prac_id = staff.current_practice.id
	staff.current_practice = practice
	staff.save()
	MHLUser.objects.filter(pk=muluser_id).update(
			address1=practice.practice_address1,
			address2=practice.practice_address2,
			city=practice.practice_city,
			state=practice.practice_state,
			zip=practice.practice_zip,
			lat=practice.practice_lat,
			longit=practice.practice_longit,
		)

	if not old_cur_prac_id == practice_id:
		# send notification to related users
		thread.start_new_thread(notify_user_tab_changed, (muluser_id,))

	return practice

def get_pending_accoc_list(org_id, is_apply, mhluser=None, practice=None):
	providers = Provider.objects.all().values_list('user', flat=True)

	pend_assocs = Pending_Association.objects.filter(\
			practice_location__pk=org_id).order_by('-resent_time')
	if is_apply:
		pend_assocs = pend_assocs.filter(~Q(to_user__in=providers))
	else:
		pend_assocs = pend_assocs.filter(Q(to_user__in=providers))

	return_set = [{
			'flag':0,
			'pract_id':u.practice_location.id,
			'req_name': get_fullname(u.from_user) if is_apply else
				get_fullname(u.to_user),
			'pract_name':u.practice_location.practice_name,
			'assoc_id':u.pk,
			'invitation_time': str(convert_dt_to_utz(
					u.created_time, mhluser, practice)),
			'resent_time':str(convert_dt_to_utz(u.resent_time
					, mhluser, practice))
					if u.resent_time else None,
			'delta_time': get_delta_time_string(u.resent_time, mhluser,\
					practice) if u.resent_time else
					get_delta_time_string(u.created_time, mhluser, practice),
			'flag':1 if is_apply else 0,
		} for u in pend_assocs]
	return return_set

def get_delta_time_string(dt, mhluser, practice):
	if not isinstance(dt, datetime.datetime):
		return ''

	ts = convert_dt_to_utz(dt, mhluser, practice)

	delta_milseconds = time.time()-time.mktime(ts.timetuple())
	if delta_milseconds < 0:
		return ''

	delta_val = delta_milseconds/(60*60*24*30*12)

	if int(delta_val) > 1:
		return _("several years ago")

	if int(delta_val) == 1:
		return _("1 year ago")
	
	delta_val = delta_val*12*30/7
	if int(delta_val) > 0:
		return '%d week(s) ago' % int(delta_val)

	delta_val = delta_val*7
	if int(delta_val) > 0:
		return '%d day(s) ago' % int(delta_val)

	delta_val = delta_val*24
	if int(delta_val) > 0:
		return '%d hour(s) ago' % int(delta_val)

	delta_val = delta_val*60
	if int(delta_val) > 0:
		return '%d minute(s) ago' % int(delta_val)

	delta_val = delta_val*60
	if int(delta_val) > 0:
		return '%d second(s) ago' % int(delta_val)

	return _("1 second ago")

