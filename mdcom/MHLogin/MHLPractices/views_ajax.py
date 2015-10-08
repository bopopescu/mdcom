
import json
import datetime
import thread

from django.conf import settings
from django.core.mail import send_mail
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, HttpResponseRedirect
from django.db.models import Q
from django.template.loader import render_to_string
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext as _

from MHLogin.DoctorCom.Messaging.models import Message, MessageRecipient
from MHLogin.Invites.forms import inviteSendForm, OfficeStaffInviteForm
from MHLogin.Invites.models import Invitation
from MHLogin.MHLCallGroups.models import CallGroupMember, CallGroupMemberPending
from MHLogin.MHLCallGroups.Scheduler.models import EventEntry
from MHLogin.MHLPractices.forms_staffsearch import AssociationProviderIdForm, \
	AssociationAssocIdForm, ProviderByMailForm
from MHLogin.MHLPractices.utils import mail_add_association, mail_managers, \
	 changeCurrentPracticeForStaff
from MHLogin.MHLPractices.models import PracticeLocation, Pending_Association, Log_Association
from MHLogin.MHLUsers.utils import get_all_practice_managers
from MHLogin.MHLUsers.models import Office_Manager, OfficeStaff, MHLUser,\
	Provider, Physician, Dietician, Nurse
from MHLogin.utils import ImageHelper
from MHLogin.utils.mh_logging import get_standard_logger

from MHLogin.MHLCallGroups.Scheduler.utils import SessionHelper
from MHLogin.apps.smartphone.v1.utils import notify_user_tab_changed

# Setting up logging
logger = get_standard_logger('%s/MHLPractices/views_ajax.log' % (settings.LOGGING_ROOT),
							'MHLPractices.views_ajax', settings.LOGGING_LEVEL)


def _get_specialty(provider):
	phys = Physician.objects.filter(user=provider)
	if (not phys.exists()):
		return ''
	return phys.get().get_specialty_display()

def get_office_user_type(staff_id, practice):
	if Office_Manager.objects.filter(user__pk=staff_id, practice=practice).exists():
		return _("Practice Manager")
	if Dietician.objects.filter(user__pk=staff_id).exists():
		return _("Dietician")
	if Nurse.objects.filter(user__pk=staff_id).exists():
		return _("Nurse")
	return _('Staff')

def addAssociation(request):
	user = request.user
	office_staff = request.session['MHL_Users']['OfficeStaff']
	practice = office_staff.current_practice

	if (request.method == 'POST'):
		form = AssociationProviderIdForm(request.POST)
	else:
		form = AssociationProviderIdForm(request.GET)

	if (not form.is_valid()):
		return HttpResponse(json.dumps({'err': _('The data is wrong. Please '
					'refresh the page again.')}), mimetype='application/json')

	prov_id = form.cleaned_data['prov_id']

	#check if invitation from provider Exists
	ret_set = Pending_Association.objects.filter(from_user=prov_id, practice_location=practice.id)
	if (ret_set.count() > 0):
		return HttpResponse(json.dumps(['duplicate']))  # , mimetype='application/json')

	association = Pending_Association()
	created_time = datetime.datetime.now()
	resend_time = created_time
	association.from_user_id = user.id
	association.to_user_id = prov_id
	association.practice_location_id = practice.id
	association.created_time = created_time
	association.resent_time = resend_time

	association.save()

	#lets log our action
	log_association = Log_Association()

	log_association.association_id = association.id
	log_association.from_user_id = user.id
	log_association.to_user_id = prov_id
	log_association.practice_location_id = practice.id
	log_association.action_user_id = user.id
	log_association.action = 'CRE'
	log_association.created_time = created_time
	association.resent_time = resend_time
	log_association.save()

	#now let's mail provider invitaion request
	if request.POST['userType'] == '1':
		#provider = Provider.objects.get(user=prov_id)
		provider = Provider.objects.get(user__id=prov_id)
	else:
		#provider = OfficeStaff.objects.get(user=prov_id)
		provider = OfficeStaff.objects.get(user__id=prov_id)

	mail_add_association(request, _('DoctorCom: Invitation To Join Practice'),  # subject,
							"""Dear {{provider_name}},

{{manager_name}} {{manager_name_last}} has sent you an invitation to join {{practice_name}}. 
Please login to DoctorCom to view and accept the pending invitaion. 

You can also accept the invitation by clicking  https://{{server_address}}/Profile/Practices/

Best, 
DoctorCom Staff""",
				provider.user.email,
				practice_name=practice.practice_name,
				manager_name=request.user.first_name,
				manager_name_last=request.user.last_name,
				provider_name=provider.user,
				server_address=settings.SERVER_ADDRESS
				)

	return HttpResponse(json.dumps(['ok']))  # , mimetype='application/json')


def resendAssociation(request):

	#send email and update resent date
	user = request.user
	office_staff = request.session['MHL_Users']['OfficeStaff']
	practice = office_staff.current_practice

	if (request.method == 'POST'):
		form = AssociationAssocIdForm(request.POST)
	else:
		form = AssociationAssocIdForm(request.GET)

	if (not form.is_valid()):
		return HttpResponse(json.dumps({'err': _('The data is error. '
			'Please refresh the page again.')}), mimetype='application/json')

	assoc_id = form.cleaned_data['assoc_id']
	association = Pending_Association.objects.get(pk=assoc_id)
	created_time = datetime.datetime.now()
	association.resent_time = created_time

	association.save()

	#lets log our action
	log_association = Log_Association()

	log_association.association_id = association.id
	log_association.from_user_id = association.from_user_id
	log_association.to_user_id = association.to_user_id
	log_association.practice_location_id = association.practice_location.id
	log_association.action_user_id = user.id
	log_association.action = 'RES'
	log_association.created_time = created_time

	log_association.save()

	provider = Provider.objects.get(user=association.to_user)
	mail_add_association(request, _('DoctorCom: Invitation To Join Practice'),  # subject,
							"""Dear {{provider_name}},

{{manager_name}} {{manager_name_last}} has sent you an invitation to join {{practice_name}}. 
Please login to DoctorCom to view and accept the pending invitaion. 

You can also accept the invitation by clicking  https://{{server_address}}/Profile/Practices/

Best, 
DoctorCom Staff""",
				provider.user.email,
				practice_name=practice.practice_name,
				manager_name=request.user.first_name,
				manager_name_last=request.user.last_name,
				provider_name=provider.user,
				server_address=settings.SERVER_ADDRESS
				)
	return HttpResponse(json.dumps('OK'), mimetype='application/json')


def removeAssociation(request):
	#send email and update resent date
	user = request.user
	office_staff = request.session['MHL_Users']['OfficeStaff']
	practice = office_staff.current_practice
	if (request.method == 'POST'):
		form = AssociationAssocIdForm(request.POST)
	else:
		form = AssociationAssocIdForm(request.GET)

	if (not form.is_valid()):
		return HttpResponse(json.dumps({'err': _('The data is error. '
			'Please refresh the page again.')}), mimetype='application/json')

	assoc_id = form.cleaned_data['assoc_id']
	association = Pending_Association.objects.get(pk=assoc_id)

	provider = Provider.objects.get(user=association.to_user)

	log_association = Log_Association()

	log_association.association_id = association.id
	log_association.from_user_id = association.from_user_id
	log_association.to_user_id = association.to_user_id
	log_association.practice_location_id = association.practice_location.id
	log_association.action_user_id = user.id
	log_association.action = 'CAN'
	log_association.created_time = datetime.datetime.now()

	log_association.save()

	association.delete()

	mail_add_association(request, _('DoctorCom: Invitation To Join Practice Withdrawn'),
							"""Dear {{provider_name}},

We're sorry, but your DoctorCom Invitation to join {{practice_name}} has been withdrawn.

Best,
DoctorCom Staff""",
				provider.user.email,
				practice_name=practice.practice_name,
				provider_name=provider.user,
				server_address=settings.SERVER_ADDRESS
				)
	return HttpResponse(json.dumps('OK'), mimetype='application/json')

def addProviderToPractice(request):
	if (request.method == 'POST'):
		form = AssociationAssocIdForm(request.POST)
	else:
		form = AssociationAssocIdForm(request.GET)

	if (not form.is_valid()):
		return HttpResponse(json.dumps({'err': _('A server error has occurred.')}), 
			mimetype='application/json')

	assoc_id = form.cleaned_data['assoc_id']
	association = Pending_Association.objects.get(pk=assoc_id)

	#add practice association row
	practice = PracticeLocation.objects.get(pk=association.practice_location.id)
	provider = Provider.objects.get(user=association.from_user)
	provider.practices.add(practice)

	#do not update provider's current practice even if it is NULL, only providers can do it

	log_association = Log_Association()

	log_association.association_id = association.id
	log_association.from_user_id = association.from_user_id
	log_association.to_user_id = association.to_user_id
	log_association.practice_location_id = association.practice_location.id
	log_association.action_user_id = request.user.id
	log_association.action = 'ACC'
	log_association.created_time = datetime.datetime.now()

	log_association.save()

	#remove association record
	association.delete()

	# Add the provider to the call group. ONLY if practice set up before V2 of answering service
	if (practice.uses_original_answering_serice() and not CallGroupMember.objects.filter(
					call_group=practice.call_group, member=provider).exists()):
		CallGroupMember(
				call_group=practice.call_group,
				member=provider,
				alt_provider=1).save()

	# send notification to related users
	thread.start_new_thread(notify_user_tab_changed, (provider.user.id,))

	return HttpResponse(json.dumps('ok'), mimetype='application/json')


def rejectAssociation(request):
	office_staff = request.session['MHL_Users']['OfficeStaff']
	practice = office_staff.current_practice

	if (request.method == 'POST'):
		form = AssociationAssocIdForm(request.POST)
	else:
		form = AssociationAssocIdForm(request.GET)

	if (not form.is_valid()):
		return HttpResponse(json.dumps({'err': _('The data is error. Please refresh '
			'the page again.')}), mimetype='application/json')

	assoc_id = form.cleaned_data['assoc_id']
	association = Pending_Association.objects.get(pk=assoc_id)

	provider = Provider.objects.get(user=association.from_user)

	log_association = Log_Association()

	log_association.association_id = association.id
	log_association.from_user_id = association.from_user_id
	log_association.to_user_id = association.to_user_id
	log_association.practice_location_id = association.practice_location.id
	log_association.action_user_id = request.user.id
	log_association.action = 'REJ'
	log_association.created_time = datetime.datetime.now()

	log_association.save()

	association.delete()

	mail_add_association(request, _('DoctorCom: Request To Join Practice Rejected'),
							"""Dear {{provider_name}},

We're sorry, but your DoctorCom Invitation to join {{practice_name}} practice has been rejected. 

Best,
DoctorCom Staff""",
				provider.user.email,
				practice_name=practice.practice_name,
				provider_name=provider.user)

	return HttpResponse(json.dumps('OK'), mimetype='application/json')


def removeProviderCallGroup(request):
	if (request.method == 'POST'): 
		form = AssociationProviderIdForm(request.POST)
	else:
		form = AssociationProviderIdForm(request.GET)

	if (not form.is_valid()):
		return HttpResponse(json.dumps({'err': _('The data is error. Please '
			'refresh page again.')}), mimetype='application/json')

	prov_id = form.cleaned_data['prov_id']

	#get managers' practice, and practices call group
	office_staff = request.session['MHL_Users']['OfficeStaff']
	practice = office_staff.current_practice
	call_groups = practice.call_groups.all()

	current_date = datetime.datetime.now()
	two_weeks_date = current_date + datetime.timedelta(days=15)

	#get provider to be removed, modify by xlin 121214 that test cases
	#provider = Provider.objects.get(user=prov_id)
	provider = Provider.objects.get(id=prov_id)
	user = provider.user

	#if schedule exists in next two weeks massage managers, so they can cover gaps
	events_set = EventEntry.objects.filter(callGroup__in=call_groups, \
			oncallPerson=user, eventStatus=1, endDate__gt=current_date)
	#raise Exception('return set is', events_set, practice, user)

	if (events_set.count() > 0):

		subject = 'DoctorCom: Gaps in On Call Schedule'
		body = _("""Dear Manager,

%(first_name)s %(last_name)s has removed %(user)s from %(practice_name)s. %(user)s was 
removed from the on-call schedule, creating gaps in coverage. Please update your 
on-call schedule to fill these gaps.

Best,
DoctorCom Staff""") \
		% {
			'first_name': request.user.first_name,
			'last_name': request.user.last_name,
			'user': provider.user,
			'practice_name': practice.practice_name
		}
			#work around message_managers fails to message:

			#message_managers(request, practice, subject,
			#				body, 
			#	practice_name=practice.practice_name,
			#	manager_name=request.user.first_name,
			#	manager_name_last=request.user.last_name,
			#	provider_name=provider.user
			#	)

		#get a list of all office managers for this practice
		OfficeManagers = get_all_practice_managers(practice.id)
		#this will be message for office managers, next key makes sms not being sent out 
		#with message-because office managers do not have to carry cell phones, dahsboard only
		request.session['answering_service'] = 'yes'

		#create message object
		msg = Message(sender=None, sender_site=None, subject=subject)
		msg.save()

		msg_body = msg.save_body(body)

		#create list of recepients - all office manager of the practice in question
		for OfficeStaff in OfficeManagers:
			MessageRecipient(message=msg, user=OfficeStaff.user).save()

		msg.send(request, msg_body)

		#send email as well to all managers
		mail_managers(practice, subject, body)

	today = datetime.date.today()
	#remove from schedule - mark as deleted
	EventEntry.objects.filter(callGroup__in=call_groups, oncallPerson=user, 
			startDate__gte=today).update(eventStatus=0, lastupdate=current_date)
	EventEntry.objects.filter(callGroup__in=call_groups, oncallPerson=user, 
			endDate__gte=today, startDate__lt=today).update(endDate=today, lastupdate=current_date)

	CallGroupMember.objects.filter(call_group__in=call_groups, member=user).delete()

	#remove from provider
	if (provider.current_practice == practice):
		provider.current_practice = None
		provider.save()

	provider.practices.remove(practice)

	return HttpResponse(json.dumps('ok'), mimetype='application/json')


def removeProviderPractice(request):
	if (request.method == 'POST'):
		form = AssociationProviderIdForm(request.POST)
	else:
		form = AssociationProviderIdForm(request.GET)

	if (not form.is_valid()):
		return HttpResponse(json.dumps({'err': _('The data is error. Please '
						'refresh page again.')}), mimetype='application/json')

	prov_id = form.cleaned_data['prov_id']

	#get managers' practice, and practices call group
	office_staff = request.session['MHL_Users']['OfficeStaff']
	practice = office_staff.current_practice
	call_group = practice.call_group

	current_date = datetime.datetime.now()
	two_weeks_date = current_date + datetime.timedelta(days=15)

	#get provider to be removed
	provider = Provider.objects.get(user=prov_id)
	user = provider.user

	#if schedule exists in next two weeks massage managers, so they can cover gaps
	events_set = EventEntry.objects.filter(callGroup=call_group, oncallPerson=user, 
			eventStatus=1, endDate__gt=current_date)
	#raise Exception('return set is', events_set, practice, user)

	if (events_set.count() > 0):

		subject = 'DoctorCom: Gaps in On Call Schedule'
		body = _("""Dear Manager,

%(first_name)s %(last_name)s has removed %(user)s from %(practice_name)s. %(user)s was 
removed from the on-call schedule, creating gaps in coverage. Please update your 
on-call schedule to fill these gaps.

Best,
DoctorCom Staff""") \
		% {
			'first_name': request.user.first_name,
			'last_name': request.user.last_name,
			'user': provider.user,
			'practice_name': practice.practice_name
		}
			#work around message_managers fails to message:

			#message_managers(request, practice, subject,
			#				body, 
			#	practice_name=practice.practice_name,
			#	manager_name=request.user.first_name,
			#	manager_name_last=request.user.last_name,
			#	provider_name=provider.user
			#	)

		#get a list of all office managers for this practice
		OfficeManagers = get_all_practice_managers(practice.id)
		#this will be message for office managers, next key makes sms not being sent out with
		#message-becasue office managers do not have to carry cell phones, dahsboard only
		request.session['answering_service'] = 'yes'

		#create message object
		msg = Message(sender=None, sender_site=None, subject=subject)
		msg.save()

		msg_body = msg.save_body(body)

		#create list of recepients - all office manager of the practice in question
		for OfficeStaff in OfficeManagers:
			MessageRecipient(message=msg, user=OfficeStaff.user).save()

		msg.send(request, msg_body)

		#send email as well to all managers
		mail_managers(practice, subject, body)

	today = datetime.date.today()
	#remove from schedule - mark as deleted
	EventEntry.objects.filter(callGroup=call_group, oncallPerson=user, 
		startDate__gte=today).update(eventStatus=0, lastupdate=current_date)
	EventEntry.objects.filter(callGroup=call_group, oncallPerson=user, 
		endDate__gte=today, startDate__lt=today).update(endDate=today, lastupdate=current_date)

	CallGroupMember.objects.filter(call_group=call_group, member=user).delete()

	#remove from provider
	if (provider.current_practice == practice):
		provider.current_practice = None
		provider.save()

	provider.practices.remove(practice)

	return HttpResponse(json.dumps('ok'), mimetype='application/json')


def removeProvider(request):
	office_staff = request.session['MHL_Users']['OfficeStaff']
	practice = office_staff.current_practice
	if practice.call_group:
		return removeProviderPractice(request)
	else:
		return removeProviderCallGroup(request)

def changeSmartphonePermission(request):
	pk = request.POST['pk'] if 'pk' in request.POST else None
	smartstat = request.POST['newSmart'] if 'newSmart' in request.POST else None
	try:  # TODO: WIP...
		if pk and smartstat:
			user = OfficeStaff.objects.get(pk=pk).user
			p = Permission.objects.get_or_create(codename='access_smartphone', 
				name='Can use smartphone app', 
					content_type=ContentType.objects.get_for_model(MHLUser))
			if smartstat == 'enabled':
				if not user.has_perm('MHLUsers.access_smartphone'):
					user.user_permissions.add(p[0])
					user.save()
				resp = HttpResponse(json.dumps('OK'))
			elif smartstat == 'disabled':
				if user.has_perm('MHLUsers.access_smartphone'):
					user.user_permissions.remove(p[0])
					user.save()
				resp = HttpResponse(json.dumps('OK'))
			else:
				resp = HttpResponse(json.dumps(['err', "Unknown state: %s" % 
						str(smartstat)]), mimetype='application/json')
			# critical warning if created, shouldn't happen if we ran
			# syncdb and set_def_mobile_access_perm management command.
			if p[1] == True:
				logger.critical("Created %s. This permission should already be in DB, "\
					"now all users default to not having smartphone access.  We should "\
					"run: syncdb, then management command: set_def_mobile_access_perm, "\
					"granting this permission to all users by default." % p[0].codename)
		else:
			resp = HttpResponse(json.dumps(['err', "Expected POST keys missing"]), 
							mimetype='application/json')
	except ObjectDoesNotExist, odne:
		msg = _('A server error has occured: ') + str(odne)
		resp = HttpResponse(json.dumps(['err', msg]), mimetype='application/json')

	return resp

#add by xlin in 20120307 
#cancel invitation just like Invites.views.cancelInvite
def cancelInvitation(request):
	if request.method == 'POST':
		recipient = request.POST['email']
		type = int(request.POST['type'])
		current_practice = request.session['MHL_Users']['OfficeStaff'].current_practice

		invite = Invitation.objects.filter(recipient=recipient, 
							userType=type, assignPractice=current_practice)
		if invite:
			invite = invite[0]
		else:
			return HttpResponse(json.dumps(['err', _('A server error has occured.')]))

		#add by xlin in 20120510 to send mail
		if not User.objects.filter(email=recipient):
			emailContext = dict()
			emailContext['code'] = invite.code
			emailContext['email'] = invite.recipient
			emailContext['type'] = current_practice
			emailContext['server_address'] = settings.SERVER_ADDRESS
			msgBody = render_to_string('Invites/inviteRevokeEmail.html', emailContext)
			send_mail(_('DoctorCom Invitation Cancelled'), msgBody, 
					settings.SERVER_EMAIL, [invite.recipient], fail_silently=False)

		invite.delete()
		return HttpResponse(json.dumps(['ok']))
	else:
		return HttpResponse(json.dumps(['err', _('A server error has occured.')]))


#add by xlin in 20120606 to fix bug in 869
def cancelExistInvitation(request):
	if request.method == 'POST':
		recipient = request.POST['email']
		type = int(request.POST['type'])
		current_practice = request.session['MHL_Users']['OfficeStaff'].current_practice
		invite = Invitation.objects.filter(recipient=recipient, userType=type, 
						assignPractice=current_practice)
		if invite:
			invite = invite[0]
			invite.delete()
			return HttpResponse(json.dumps(['ok']))
		else:
			return HttpResponse(json.dumps(['err', _('A server error has occured.')]))
	else:
		return HttpResponse(json.dumps(['err', _('A server error has occured.')]))


#add by xlin in 20120309
#send a mail to new doctor
def sendNewProviderEmail(request):
	if('Office_Manager' in request.session['MHL_UserIDs']):
		formclass = OfficeStaffInviteForm
	else:
		formclass = inviteSendForm
	if (request.method == 'POST'):
		inviteForm = formclass(request.POST)
		if (inviteForm.is_valid()):
			if not User.objects.filter(email=request.POST['recipient']):
				invite = inviteForm.save(commit=False)
				if('Office_Manager' in request.session['MHL_UserIDs']):
					invite.assignPractice = OfficeStaff.objects.filter(user=request.user).\
						only('current_practice').get().current_practice
				invite.sender = request.user
				if('Office_Manager' in request.session['MHL_UserIDs']):
					invite.userType = inviteForm.cleaned_data['userType']
				else:
					invite.userType = 1
				invite.save()
				if('Office_Manager' in request.session['MHL_UserIDs'] and 'createnow' in request.POST):
					return HttpResponseRedirect(invite.get_link({'createnow': True}))
				if (not invite.testFlag):
					invite.email_invite(inviteForm.cleaned_data['msg'])
				return HttpResponse(json.dumps('ok'))
			else:
				return HttpResponse(json.dumps({'err': _('This email address is already '
						'associated with a DoctorCom account.')}))
		else:
			#return HttpResponse(json.dumps({'err': inviteForm.errors['__all__'][0]}))
			return HttpResponse(json.dumps({'err': inviteForm.errors}))
	else:
		return HttpResponse(json.dumps({'err': _('A server error has occurred when '
							'you send a email. Please refresh page again.')}))


#add by xlin in 20120323 to check pendding exist
def checkPenddingExist(request):
	office_staff = request.session['MHL_Users']['OfficeStaff']
	practice = office_staff.current_practice
	user = request.POST['id']
	lst = Pending_Association.objects.filter(practice_location=practice).\
			values_list('from_user', flat=True)
	rst = Pending_Association.objects.filter(practice_location=practice).\
			values_list('to_user', flat=True)
	for item in lst:
		if int(item) == int(user):
			return HttpResponse(json.dumps('err'))

	for item in rst:
		if int(item) == int(user):
			return HttpResponse(json.dumps('err'))
	return HttpResponse(json.dumps('ok'))

def changeCurrentPractice(request):
	id = request.POST['id']
	user = request.session['MHL_UserIDs']['MHLUser']
	try:
		current_practice = changeCurrentPracticeForStaff(id, user)
		view = '{"name":"month"}'
		request.session[SessionHelper.SCHEDULE_LASTVIEW] = view
		SessionHelper.clearSessionStack(request, SessionHelper.CURRENT_CALLGROUP_ID)
		callgroup_id = 0
		if current_practice.uses_original_answering_serice():
			callgroup_id = current_practice.call_group.id

		return HttpResponse(json.dumps({'view': view, 'status': 'ok', 
				'callgroup_id': callgroup_id, 
				'uses_original_answering_serice': 
					current_practice.uses_original_answering_serice()}))
	except PracticeLocation.DoesNotExist, MHLUser.DoesNotExist:
		return HttpResponse(json.dumps('err'))

#add by xlin 121128 that add new method for call group
def getProviderByEmailOrNameInCallGroup(request):
	if (request.method == 'POST'):
		form = ProviderByMailForm(request.POST)
		if form.is_valid():
			office_staff = request.session['MHL_Users']['OfficeStaff']
			practice = office_staff.current_practice
			email = form.cleaned_data['email']
			fname = form.cleaned_data['fullname']
			firstName = form.cleaned_data['firstName']
			lastName = form.cleaned_data['lastName']
			uname = form.cleaned_data['username']
			call_group = request.POST['call_group']

			filter = Q()
			fname = fname.split()
			if lastName == '':
				filter = Q(first_name__icontains=firstName) | Q(last_name__icontains=firstName)
			else:
				filter = Q(first_name__icontains=firstName) & Q(last_name__icontains=lastName) | \
					Q(first_name__icontains=lastName) & Q(last_name__icontains=firstName)

			#providers = Provider.active_objects.filter(~Q(practices=practice), \
				#Q(email__icontains=email) , Q(username__icontains=uname)).filter(filter)
			providers = Provider.active_objects.filter(Q(email__icontains=email),
				Q(username__icontains=uname)).filter(filter)

			#associ = list(Pending_Association.objects.filter(practice_location=practice).\
			#	values_list('to_user', flat=True))
			#associ = associ + list(Pending_Association.objects.filter(
			#	practice_location=practice).values_list('from_user', flat=True))
			associ = list(CallGroupMemberPending.objects.filter(practice=practice, 
					call_group=call_group).values_list('to_user', flat=True))

			sets = []
			prviderIn = []
			provider_in_associa = 0
			for provider in providers:
				if (provider.id not in associ):
					sets.append(provider)
				else:
					prviderIn.append(provider)
					provider_in_associa = provider_in_associa + 1 
			return_set = [
					{
						'id':u.user.pk,
						'name':', '.join([u.user.last_name, u.user.first_name, ]),
						'photo': ImageHelper.get_image_by_type(u.photo, 'Small', 'Provider'),
						# In order to avoid modifying client's code, don't change the key.
						'address1': u.user.address1,
						'address2': u.user.address2,
						'specialty':_get_specialty(u),
					}
					for u in sets
				]

			names = ''
			if len(return_set) > 0:
				return HttpResponse(json.dumps(return_set))
			else:
				filter = Q()
				if lastName == '':
					filter = Q(first_name__icontains=firstName) | \
						Q(last_name__icontains=firstName)
				else:
					filter = Q(first_name__icontains=firstName) & \
						Q(last_name__icontains=lastName) | \
						Q(first_name__icontains=lastName) & \
						Q(last_name__icontains=firstName)

				current_provider = Provider.active_objects.filter(practices=practice, 
					email__icontains=email, username__icontains=uname).filter(filter) 
				rs = [{'id':u.user.pk}for u in current_provider]

				names = ''
				for n in current_provider:
					names = names + str(n) + ', '

				for fn in prviderIn:
					names = names + str(fn) + ', '
				if names:
					names = names[0:len(names) - 2]
					if names.find(',') == -1:
						return HttpResponse(json.dumps({'err': _('BTW, we find 1 person '
							'(%s) matching conditions who is already in your call '
								'group or has been invited.') % names}))
					else:
						return HttpResponse(json.dumps({'err': _('BTW, we find %(len)s '
							'people (%(names)s) matching conditions who are already in '
								'your call group or have been invited.') % 
									{'len': str(len(prviderIn) + len(rs)), 'names': names}}))
				else:
					return HttpResponse(json.dumps(return_set))
		else:
			return HttpResponse(json.dumps({'err': _('A invalid email.')}))
	else:
		return HttpResponse(json.dumps({'err': _('A server error has occurred.')}), 
					mimetype='application/json')

