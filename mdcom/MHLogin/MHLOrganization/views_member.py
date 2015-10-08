'''
Created on 2013-3-28

@author: wxin
'''

import json
from urllib2 import urlopen
import datetime
import thread

from django.conf import settings
from django.core.mail import send_mail
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.db.models import Q
from django.template.loader import render_to_string
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import render_to_response, get_object_or_404
from django.utils.translation import ugettext as _
from django.contrib.sessions.models import Session

from MHLogin.DoctorCom.Messaging.models import Message, MessageRecipient
from MHLogin.Invites.forms import OfficeStaffInviteForm, inviteResendForm
from MHLogin.Invites.models import Invitation
from MHLogin.MHLCallGroups.models import CallGroupMember, CallGroupMemberPending
from MHLogin.MHLCallGroups.Scheduler.models import EventEntry
from MHLogin.MHLPractices.forms_staffsearch import staffSearchForm, AssociationProviderIdForm, \
	AssociationAssocIdForm, ProviderByMailForm
from MHLogin.MHLPractices.utils import mail_add_association, mail_managers, \
	get_level_by_staff, get_role_display, get_role_options, get_pending_accoc_list,\
	get_delta_time_string
from MHLogin.MHLPractices.models import PracticeLocation, Pending_Association, Log_Association
from MHLogin.MHLUsers.utils import get_all_practice_managers,get_fullname
from MHLogin.MHLUsers.models import Office_Manager, OfficeStaff, MHLUser,\
	Provider, Physician, Dietician, Nurse
from MHLogin.utils import ImageHelper
from MHLogin.utils.mh_logging import get_standard_logger

from MHLogin.utils.templates import get_context_for_organization
from MHLogin.utils.timeFormat import time_format, convert_dt_to_utz
from MHLogin.MHLUsers.views_ajax import validate_email_and_phone
from MHLogin.Invites.views import invitation_check_with_email
from MHLogin.MHLUsers.decorators import RequireOrganizationManager
from MHLogin.utils.constants import SMART_PHONE_OPTIONS
from MHLogin.MHLPractices.utils_pendding import user_is_pendding_in_org
from MHLogin.apps.smartphone.v1.utils import notify_user_tab_changed

# Setting up logging
logger = get_standard_logger('%s/MHLPractices/views_ajax.log' % (settings.LOGGING_ROOT),
							'MHLPractices.views_ajax', settings.LOGGING_LEVEL)

@RequireOrganizationManager
def staffSearch(request):
	#in case we will need to filter out, current practice docotor,
	#need specs, or remove if not needed
	practice = request.org

	if (request.method == 'POST'):
		form = staffSearchForm(request.POST)
	else:
		form = staffSearchForm(request.GET)

	if (form.is_valid()):
		search_terms = unicode.split(form.cleaned_data['search_name'])
		pending_to = Pending_Association.objects.filter(practice_location=practice).values('to_user')
		pending_from = Pending_Association.objects.filter(practice_location=practice).values('from_user')

		# Skip geographic restrictions for now.
		return_set = Provider.objects

		for term in search_terms:
			return_set = return_set.filter(
							 ~Q(practices=practice), ~Q(user__in=pending_to), ~Q(user__in=pending_from),
							(Q(user__first_name__icontains=term) | 
							Q(user__last_name__icontains=term))
							)
		#id is from provider tables user_id column
		return_set = [
				{
					'id':u.user.pk,
					'name':' '.join([u.user.first_name, u.user.last_name, ]),
					# use mhluser's address information #1272
					'address': ' '.join([u.user.address1, u.user.address2, ]),
					'city': u.user.city,
					'state': u.user.state,
					'zip': u.user.zip,
					'specialty': _get_specialty(u),
				}
				for u in return_set
			]
		return HttpResponse(json.dumps(return_set))  # , mimetype='application/json')
	else:  # if (not form.is_valid())
		return_set = []
		return HttpResponse(json.dumps(return_set))  # , mimetype='application/json')


def _get_specialty(provider):
	phys = Physician.objects.filter(user=provider)
	if (not phys.exists()):
		return ''

	return phys.get().get_specialty_display()

@RequireOrganizationManager
def currentProviders(request):
	context = get_context_for_organization(request)
	practice = request.org
	firstName = request.REQUEST.get("firstName", "")
	lastName = request.REQUEST.get("lastName", "")

	filter = Q()
	if lastName == '':
		filter = Q(first_name__icontains=firstName) | \
			Q(last_name__icontains=firstName) | Q(email__icontains=firstName)
	else:
		filter = Q(first_name__icontains=firstName) & Q(last_name__icontains=lastName) | \
			Q(first_name__icontains=lastName) & Q(last_name__icontains=firstName)
	#return_set = Provider.active_objects.filter(Q(practices=practice)).filter(filter)
	return_set = Provider.objects.filter(Q(practices=practice)).filter(filter)
	context['total_count'] = len(return_set)
	context['index'] = index = int(request.REQUEST.get('index', 0))
	context['count'] = count = int(request.REQUEST.get('count', 10))
	return_set = [
			{
				'id':u.user.pk,
				'name':get_fullname(u.user),
				'status':u.user.is_active,
				 #add by xlin for issue437 to show last login
				'last_login':str(u.user.last_login.strftime('%m/%d/%Y')),
				'practice':str(practice),
			}
			for u in return_set[index*count:(index+1)*count]
		]
	context['datas'] = return_set
	return render_to_response('MHLOrganization/Member/member_provider_list.html', context)

@RequireOrganizationManager
def currentOfficeStaff(request):
	context = get_context_for_organization(request)
	practice = request.org
	firstName = request.REQUEST.get("firstName", "")
	lastName = request.REQUEST.get("lastName", "")
	filter = Q()
	if lastName == '':
		filter = Q(user__first_name__icontains=firstName) | \
			Q(user__last_name__icontains=firstName) | Q(user__email__icontains=firstName)
	else:
		filter = Q(user__first_name__icontains=firstName) & Q(user__last_name__icontains=lastName) | \
			Q(user__first_name__icontains=lastName) & Q(user__last_name__icontains=firstName)

	user = request.session['MHL_Users']['MHLUser']
	current_user_id = user.id

	current_role = 0
	if "OfficeStaff" in request.session['MHL_Users']:
		office_staff = request.session['MHL_Users']['OfficeStaff']
		office_staff_id = office_staff.id
		current_role = get_level_by_staff(office_staff_id, practice)
	elif "Administrator" in request.session['MHL_Users']:
		current_role = 999

	ret_staff = OfficeStaff.objects.filter(practices=practice).filter(filter)
	context['total_count'] = len(ret_staff)
	context['index'] = index = int(request.REQUEST.get('index', 0))
	context['count'] = count = int(request.REQUEST.get('count', 10))
	ret_staff = ret_staff[index*count:(index+1)*count]
	return_set = []
	role_options = get_role_options(current_role, practice)
	for u in ret_staff:
		role = get_level_by_staff(u.id, practice)
		role_display = get_role_display(role)

		tmp_role_options = ()
		not_in_option = True
		for i_role in role_options:
			if role > i_role[0] and not_in_option:
				not_in_option = False
				tmp_role_options = tmp_role_options+((role,role_display),)
			if role == i_role[0]:
				not_in_option = False
			tmp_role_options = tmp_role_options+(i_role,)
		if not_in_option:
			tmp_role_options = tmp_role_options+((role,role_display),)

		return_set.append({
				'id':u.user.id,
				'pk':u.pk,
				'name':', '.join([u.user.last_name, u.user.first_name]),
				'role': role,
				'role_display':role_display,
				'status':u.user.is_active,
				 #add by xlin for issue437 to show last login
				'last_login':str(u.user.last_login.strftime('%m/%d/%Y')),
				'can_change_this_role': current_role >= role and not current_user_id == u.user.id,
				'can_remove': not current_user_id == u.user.id,
				'smartphone': u.user.has_perm('MHLUsers.access_smartphone'),
				'user_type': get_office_user_type(u.id, practice),
				'role_options': tmp_role_options
			})

	context['datas'] = return_set
	context['smart_phone_options'] = SMART_PHONE_OPTIONS

	return render_to_response('MHLOrganization/Member/member_staff_list.html', context)

def get_office_user_type(staff_id, practice):
	if Office_Manager.objects.filter(user__pk=staff_id, practice=practice).exists():
		return _("Practice Manager")
	if Dietician.objects.filter(user__pk=staff_id).exists():
		return _("Dietician")
	if Nurse.objects.filter(user__pk=staff_id).exists():
		return _("Nurse")
	return _('Staff')

@RequireOrganizationManager
def addAssociation(request):
	user = request.user
	practice = request.org

	userType = None
	if (request.method == 'POST'):
		form = AssociationProviderIdForm(request.POST)
		userType = request.POST['userType']
	else:
		form = AssociationProviderIdForm(request.GET)
		userType = request.GET['userType']
	form.is_valid()

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
	Log_Association().save_from_association(association, user.id, 'CRE')

	#now let's mail provider invitaion request
	if userType == '1':
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

@RequireOrganizationManager
def resendAssociation(request):

	#send email and update resent date
	user = request.user
	practice = request.org

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
	Log_Association().save_from_association(association, user.id, 'RES')


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

@RequireOrganizationManager
def removeAssociation(request):
	#send email and update resent date
	user = request.user
	practice = request.org
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

	Log_Association().save_from_association(association, user.id, 'CAN')

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

@RequireOrganizationManager
def get_invite_pending(request):
	mhluser = request.session['MHL_Users']['MHLUser']
	context = get_context_for_organization(request)
	practice = context['current_practice']
	return_set = get_pending_accoc_list(request.org.id, 1, mhluser, practice)
	return_set = return_set+\
			get_pending_accoc_list(request.org.id, 0, mhluser, practice)

	index = int(request.REQUEST['index'])
	set_ctx_prev_next_disable(index, 10, len(return_set), context)

	context['pend_invite'] = return_set[index*10:(index+1)*10]

	context['no_requets'] = _('Currently, no %s Join Requests.') %\
			context["selected_organization_type"]
	html = render_to_string('MHLOrganization/Invite/invite_pending_list_view.html', context)
	return HttpResponse(json.dumps({
		"html": html,
		"prev_class": context['prev_class'],
		"next_class": context['next_class'],
		"index": index
	}), mimetype='application/json')


@RequireOrganizationManager
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

	Log_Association().save_from_association(association, request.user.id, 'ACC')

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

@RequireOrganizationManager
def rejectAssociation(request):
	practice = request.org

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

	Log_Association().save_from_association(association, request.user.id, 'REJ')

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

@RequireOrganizationManager
def removeProvider(request):
	if (request.method == 'POST'):
		form = AssociationProviderIdForm(request.POST)
	else:
		form = AssociationProviderIdForm(request.GET)
	if (not form.is_valid()):
		return HttpResponse(json.dumps({'err': _('The data is error. Please '
						'refresh page again.')}), mimetype='application/json')

	prov_id = form.cleaned_data['prov_id']
	practice = request.org
	provider = get_object_or_404(Provider, id=prov_id)
	tmp_practice = provider.practices.filter(id=practice.id)
	if not tmp_practice:
		return HttpResponse(json.dumps('OK'))
	practice = request.org

	# remove provider from call group
	if practice.call_group:
		call_groups = [practice.call_group]
	else:
		call_groups = practice.call_groups.all()

	if call_groups:
		current_date = datetime.datetime.now()
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

	#remove provider from practice
	if (provider.current_practice == practice):
		provider.current_practice = None
		provider.save()
	provider.practices.remove(practice)

	# send notification to related users
	thread.start_new_thread(notify_user_tab_changed, (provider.user.id,))
	return HttpResponse(json.dumps('ok'), mimetype='application/json')



@RequireOrganizationManager
def removeStaff(request):
	if request.method == 'POST':
		staff_id = request.POST['staff_id']
		practice = request.org
		staff = get_object_or_404(OfficeStaff, id=staff_id)
		Office_Manager.objects.filter(user=staff, practice=practice).delete()
		staff.practices.remove(practice)
		if practice == staff.current_practice:
			staff.current_practice = None
		staff.save()
		# send notification to related users
		thread.start_new_thread(notify_user_tab_changed, (staff.user.id,))
		return HttpResponse(json.dumps('OK'))
	else:
		return HttpResponse(json.dumps({'err': _('There is an error occured when '
				'removing the staff. Please refresh the page again.')}))

@RequireOrganizationManager
def changeRole(request):
	id = request.POST['pk']
	newRole = request.POST['newRole']
	practice = request.org
	oldRole = str(get_level_by_staff(id, practice))
	if newRole == '0':
		Office_Manager.objects.filter(user=id, practice=practice).delete()
	else:
		os = OfficeStaff.objects.get(pk=id)
		if oldRole == '0':
			obm = Office_Manager(user=os, practice=practice, manager_role=newRole)
			obm.save()
		else:
			om = Office_Manager.objects.get(user=os, practice=practice)
			om.manager_role = newRole
			om.save()

	#after change staff role susscee and delete session
	sessions = Session.objects.all()
	for session in sessions:
		values = session.get_decoded()
		if 'MHL_UserIDs' in values and 'MHLUser' in values['MHL_UserIDs']:
			staffID = values['MHL_UserIDs']['MHLUser']
			session_key = session.session_key
			os = OfficeStaff.objects.get(pk=id)
			if os.user.id == staffID:
				ss = Session.objects.get(session_key=session_key)
				ss.delete()
	return HttpResponse(json.dumps('OK'))

@RequireOrganizationManager
def changeSmartphonePermission(request):
	pk = request.POST['pk'] if 'pk' in request.POST else None
	smartstat = request.POST['newSmart'] if 'newSmart' in request.POST else None
	try:  # TODO: WIP...
		if pk and smartstat:
			user = OfficeStaff.objects.get(pk=pk).user
			p = Permission.objects.get_or_create(codename='access_smartphone', 
				name='Can use smartphone app', 
					content_type=ContentType.objects.get_for_model(MHLUser))
			if smartstat == 'True':
				if not user.has_perm('MHLUsers.access_smartphone'):
					user.user_permissions.add(p[0])
					user.save()
				resp = HttpResponse(json.dumps('OK'))
			elif smartstat == 'False':
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

@RequireOrganizationManager
def checkProviderSchedule(request):
	if (request.method == 'POST'):
		form = AssociationProviderIdForm(request.POST)
	else:
		form = AssociationProviderIdForm(request.GET)

	if (not form.is_valid()):
		return HttpResponse(json.dumps(['err', _('A server error has occurred.')]), 
						mimetype='application/json')

	prov_id = form.cleaned_data['prov_id']
	#get managers' practice, and practices call group
	practice = request.org

	if practice.call_group:
		call_group = practice.call_group
	else:
		call_group = practice.call_groups.all()

	current_date = datetime.datetime.now()
	two_weeks_date = current_date + datetime.timedelta(days=15)
	#get provider to be removed
	provider = Provider.objects.get(user=prov_id)
	user = provider.user

	if practice.call_group:
#		return_set = CallGroupMember.objects.filter(call_group=call_group, member=user)
		return_set = CallGroupMember.objects.filter(call_group=call_group, member=provider)
	else:
		return_set = CallGroupMember.objects.filter(call_group__in=call_group, member=provider)

	if (return_set.count() > 0):
		#check if in the next 2 weeks event exist in scheduler for this provider
		if practice.call_group:
			events_set = EventEntry.objects.filter(callGroup=call_group, 
				oncallPerson=user, eventStatus=1, endDate__gte=current_date)
		else:
			events_set = EventEntry.objects.filter(callGroup__in=call_group, 
				oncallPerson=user, eventStatus=1, endDate__gte=current_date)

		if (events_set.count() > 0):
			return HttpResponse(json.dumps(['warning']))  # , mimetype='application/json')    
	return HttpResponse(json.dumps(['ok']))  # , mimetype='application/json')

def set_ctx_prev_next_disable(index, count, total, context):
	prev_class = ""
	next_class = ""
	if index == 0:
		prev_class = "disable"
	if index == int((total-1)/count):
		next_class = "disable"
	
	if not total:
		prev_class = "hide"
		next_class = "hide"

	context['prev_class'] = prev_class
	context['next_class'] = next_class

@RequireOrganizationManager
def getInvitations(request):
	mhluser = request.session['MHL_Users']['MHLUser']
	practice = request.org
	context = get_context_for_organization(request)

	invations = Invitation.objects.filter(assignPractice=practice)\
			.order_by('-requestTimestamp')

	index = int(request.REQUEST.get('index', 0))
	set_ctx_prev_next_disable(index, 10, len(invations), context)
	return_set = [{
				'id':u.id,
				'recipient':u.recipient,
				'type': u.userType,
				'delta_time': get_delta_time_string(u.requestTimestamp,\
						mhluser, practice)
			}for u in invations[index*10:(index+1)*10]]

	context['invites'] = return_set
	context['no_requets'] = _('Currently, no DoctorCom Invitations.')

	html = render_to_string('MHLOrganization/Invite/invite_list_view.html', context)
	return HttpResponse(json.dumps({
		"html": html,
		"prev_class": context['prev_class'],
		"next_class": context['next_class'],
		"index": index
	}), mimetype='application/json')

@RequireOrganizationManager
def resendInvitation(request):
	if request.method == 'POST':
		inviteID = request.POST['id']
		invite = Invitation.objects.get(id=inviteID)
		inviteResend = inviteResendForm(request.POST)
		msg = ''
		if (inviteResend.is_valid()):
			msg = inviteResend.cleaned_data['msg']

		invite.resend_invite(msg)
		if hasattr(invite, 'error'):
			return HttpResponse(json.dumps({'err': _('This email address is already '
							'associated with a DoctorCom account.')}))
		else:
			return HttpResponse(json.dumps({'err': 'ok'}))
	else:
		return HttpResponse(json.dumps(['err', _('A server error has occurred.')]))

@RequireOrganizationManager
def cancelInvitation(request):
	if request.method == 'POST':
		recipient = request.POST['email']
		type = int(request.POST['type'])
		current_practice = request.org

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


@RequireOrganizationManager
def cancelExistInvitation(request):
	if request.method == 'POST':
		recipient = request.POST['email']
		type = int(request.POST['type'])
		current_practice = request.org
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

@RequireOrganizationManager
def sendNewProviderEmail(request):
	context = get_context_for_organization(request)
	if (request.method == 'POST'):
		inviteForm = OfficeStaffInviteForm(request.POST)
		if (inviteForm.is_valid()):
			if not User.objects.filter(email=request.POST['recipient']):
				invite = inviteForm.save(commit=False)
				invite.assignPractice = request.org
				invite.sender = request.user
				invite.userType = inviteForm.cleaned_data['userType']
				invite.save()
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

@RequireOrganizationManager
def checkPenddingExist(request):
	user_id = int(request.POST['id'])
	if user_is_pendding_in_org(user_id, request.org):
		return HttpResponse(json.dumps('err'))
	return HttpResponse(json.dumps('ok'))

@RequireOrganizationManager
def valideInvitation(request):
	practice = request.org
	practice_id = practice.id
	return invitation_check_with_email(request, practice_id)
