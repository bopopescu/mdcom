
import datetime
import json
import thread

from django.conf import settings
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.utils.translation import ugettext as _
from django.http.response import HttpResponseBadRequest

from MHLogin.DoctorCom.Messaging.models import Message, MessageRecipient
from MHLogin.MHLCallGroups.Scheduler.models import EventEntry
from MHLogin.MHLCallGroups.models import CallGroupMember
from MHLogin.MHLOrganization.utils_org_tab import getOrgMembers
from MHLogin.MHLPractices.models import Pending_Association, Log_Association, \
	PracticeLocation
from MHLogin.MHLPractices.utils import mail_managers
from MHLogin.MHLUsers.forms import AddPracticeToProviderForm, \
	PracticesSearchForm, PractIdAssociationForm, AssocIdAssociationForm, \
	nameSearchFormOld, nameSearchForm, ProximitySearchForm
from MHLogin.MHLUsers.models import MHLUser, Provider, Office_Manager, \
	OfficeStaff, Physician, NP_PA, States, User
from MHLogin.MHLUsers.utils import get_all_practice_managers, \
	get_community_providers_by_zipcode, get_clinical_clerks_by_zipcode, \
	set_providers_result, search_by_name, check_username_another_server, \
	set_practice_members_result, get_user_type_ids, get_practice_org, \
	get_specialty_display_by_provider,search_mhluser,get_fullname
from MHLogin.utils.constants import SPECIALTY_CHOICES, STATE_CHOICES, \
	RESERVED_ORGANIZATION_TYPE_ID_PRACTICE
from MHLogin.apps.smartphone.v1.utils import notify_user_tab_changed


def search_by_name_old(request):
	if (request.method == 'POST'):
		form = nameSearchFormOld(request.POST)
	else:
		form = nameSearchFormOld(request.GET)

	if (form.is_valid()):
		name = form.cleaned_data['q']
		limit = form.cleaned_data['limit']
		user_qry = search_by_name(name, limit)
		return_obj = [
						[
							u.pk, 
							get_fullname(u)
						] for u in user_qry]
		return_obj = ['ok', return_obj]

		return HttpResponse(json.dumps(return_obj), mimetype='application/json')
	else:  # if (not form.is_valid())
		return HttpResponse(json.dumps(['err', _('A server error has occurred.')]), 
			mimetype='application/json')


def search_by_name_new(request):
	if (request.method == 'POST'):
		form = nameSearchForm(request.POST)
	else:
		form = nameSearchForm(request.GET)

	if (form.is_valid()):
		search_terms = unicode.split(form.cleaned_data['q'])
		limit = form.cleaned_data['limit']
		return_set = Provider.objects.filter()
		for term in search_terms:
			return_set = return_set.filter(
							Q(user__first_name__icontains=term) | 
							Q(user__last_name__icontains=term))
		return_set = return_set.only('user__first_name', 'user__last_name')[:limit]

		return_obj = [[str(u.user.pk), ' '.join([u.user.first_name, 
				u.user.last_name])] for u in return_set]

		return_obj = ['ok', return_obj]

		return HttpResponse(json.dumps(return_obj), mimetype='application/json')
	else:  # if (not form.is_valid())
		return HttpResponse(json.dumps(['err', _('A server error has occurred.')]), 
			mimetype='application/json')


def PracticesSearch(request):
	user = request.user
	# we will need to filter out, current practice for this doctor
	mhluser = request.session['MHL_Users']['MHLUser']
	user_type_ids = get_user_type_ids(mhluser)

	provider = request.session['MHL_Users']['Provider']
	return_set = provider.practices.filter(\
			organization_type__pk=RESERVED_ORGANIZATION_TYPE_ID_PRACTICE)
	practice_id = return_set.only('id')

	if (request.method == 'POST'):
		form = PracticesSearchForm(request.POST)
	else:
		form = PracticesSearchForm(request.GET)

	if (form.is_valid()):
		search_terms = unicode.split(form.cleaned_data['search_name'])
		pending = Pending_Association.objects.filter(Q(to_user=user) | 
			Q(from_user=user)).values('practice_location_id')

		# Skip geolocation for now.
		return_set = PracticeLocation.active_practice

		managers = Office_Manager.objects.filter().values('practice_id')
		for term in search_terms:
			return_set = return_set.filter(
				~Q(pk__in=practice_id), ~Q(pk__in=pending),
				Q(practice_name__icontains=term), Q(pk__in=managers))

		include_ids = []
		for p in return_set:
			allow_user_types = [l[0] for l in p.get_org_sub_user_types_tuple()]
			if set(user_type_ids) & set(allow_user_types):
				include_ids.append(p.id)
		return_set = return_set.filter(id__in=include_ids)

		return_set = [
			{
				'id':u.pk,
				'practice_name': u.practice_name,
				'practice_address': ' '.join([u.practice_address1, u.practice_address2]),
				'practice_city': u.practice_city,
				'practice_state': u.practice_state,
				'practice_zip': u.practice_zip
			}
			for u in return_set
		]
		return HttpResponse(json.dumps(return_set))  # , mimetype='application/json')
	else:  # if (not form.is_valid())
		return_set = []
		return HttpResponse(json.dumps(return_set))  # , mimetype='application/json')


def getPendingPracticesTo(request):
	#provider who logged in
	user = request.user

	return_set = Pending_Association.objects.filter(from_user=user,\
			practice_location__organization_type=RESERVED_ORGANIZATION_TYPE_ID_PRACTICE)

	#id is from provider tables user_id column
	return_set = [
				{
					'pract_id':u.practice_location.id,
					'req_name':' '.join([u.from_user.first_name, u.from_user.last_name, ]), 	
					'pract_name':u.practice_location.practice_name,
					'assoc_id':u.pk,
					'created_time':str(u.created_time),
				}
				for u in return_set				
			]
	return HttpResponse(json.dumps(return_set))  # , mimetype='application/json')	


def getPendingPracticesFrom(request):
	#provider who logged in
	user = request.user

	return_set = Pending_Association.objects.filter(to_user=user,\
		practice_location__organization_type=RESERVED_ORGANIZATION_TYPE_ID_PRACTICE)

	return_set = [
			{
				'pract_id':u.practice_location.id,
				'req_name':' '.join([u.from_user.first_name, u.from_user.last_name]), 	
				'pract_name':u.practice_location.practice_name,
				'assoc_id':u.pk
			}
			for u in return_set
		]
	return HttpResponse(json.dumps(return_set))  # , mimetype='application/json')	


#come back here and figure out iteration over practices in provider
def getCurrentPractices(request):
	#get practices of logged in user
	provider = request.session['MHL_Users']['Provider']

	return_set = provider.practices.filter(\
			organization_type__pk=RESERVED_ORGANIZATION_TYPE_ID_PRACTICE)

	return_set = [
			{
				'pract_id': u.id,
				'pract_name': u.practice_name,
				'make_current':practice_not_current(u.id, provider.current_practice),
			}			
			for u in return_set
		]
	return HttpResponse(json.dumps(return_set))  # , mimetype='application/json')


def practice_not_current(id, current_practice):
	if (current_practice == None):
		return 'yes'
	elif (current_practice.id == id):
		return 'no'
	else:
		return 'yes'


def addPracticeToProvider(request):
	provider = request.session['MHL_Users']['Provider']
	current_practice = provider.current_practice

	if (request.method == 'POST'):
		form = AddPracticeToProviderForm(request.POST)
	else:
		form = AddPracticeToProviderForm(request.GET)

	if (not form.is_valid()):
		err_obj = {
			'errors': form.errors,
		}
		return HttpResponseBadRequest(json.dumps(err_obj), mimetype='application/json')

	pract_id = form.cleaned_data['pract_id']
	assoc_id = form.cleaned_data['assoc_id']

	#add practice association row
	practice = PracticeLocation.objects.get(pk=pract_id)
	provider.practices.add(practice)

	#update current practice if needed
	new_current_practice = get_practice_org(practice)
	if (current_practice == None and new_current_practice):
		provider.current_practice = new_current_practice
		provider.save()

	#remove association record
	association = Pending_Association.objects.filter(pk=assoc_id)
	if association and len(association) > 0:
		association = association[0]

		log_association = Log_Association()

		log_association.association_id = association.id
		log_association.from_user_id = association.from_user_id
		log_association.to_user_id = association.to_user_id
		log_association.practice_location_id = association.practice_location.id
		log_association.action_user_id = request.user.id
		log_association.action = 'ACC'
		log_association.created_time = datetime.datetime.now()
		log_association.save()

		association.delete()

		# Add the provider to the call group, ONLY if practice set up before V2 of answering service
		if (practice.uses_original_answering_serice() and not CallGroupMember.objects.filter(
						call_group=practice.call_group, member=provider).exists()):
			CallGroupMember(
					call_group=practice.call_group,
					member=provider,
					alt_provider=1).save()
		# send notification to related users
		thread.start_new_thread(notify_user_tab_changed, (provider.user.id,))

		ret_data = {
			"success": True,
		}
		return HttpResponse(json.dumps(ret_data), mimetype='application/json')
	else:
		ret_data = {
			"success": False,
			"message": _("You already have been added to the organization or "
						"your invitation has been canceled from other client.")
		}
		return HttpResponse(json.dumps(ret_data), mimetype='application/json')


def rejectAssociation(request):
	if (request.method == 'POST'):
		form = AssocIdAssociationForm(request.POST)
	else:
		form = AssocIdAssociationForm(request.GET)
	if (not form.is_valid()):
		return HttpResponse(json.dumps(_('A server error has occurred.')))

	assoc_id = form.cleaned_data['assoc_id']
	association = Pending_Association.objects.filter(pk=assoc_id)
	if association and len(association) > 0:
		association = association[0]
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

		practice = association.practice_location
		mail_managers(practice,
						_('DoctorCom: Request To Join Practice Rejected'),
						"""Dear Manager,

We're sorry, but {{provider_name}} {{provider_name_last}} turned down your request 
to join {{practice_name}}.

Best,
DoctorCom Staff
""",
					practice_name=practice.practice_name,
					provider_name=request.user.first_name,
					provider_name_last=request.user.last_name
					)
		ret_data = {
			"success": True
		}
		return HttpResponse(json.dumps(ret_data), mimetype='application/json')
	else:
		ret_data = {
			"success": False,
			"message": _("You already have been added to the organization or your "
						"invitation has been canceled from other client.")
		}
		return HttpResponse(json.dumps(ret_data), mimetype='application/json')


def addAssociationForPractice(request):
	user = request.user

	if (request.method == 'POST'):
		form = PractIdAssociationForm(request.POST)
	else:
		form = PractIdAssociationForm(request.GET)	

	if (not form.is_valid()):
		return HttpResponse(json.dumps(_('A server error has occurred.')))

	pract_id = form.cleaned_data['pract_id']
	#get practice
	practice = PracticeLocation.objects.get(pk=pract_id)
	#check if manager sent association request to this provider already
	ret_set = Pending_Association.objects.filter(to_user=user, practice_location=pract_id)
	if (ret_set.count() > 0):
		return HttpResponse(json.dumps(['duplicate']))  # , mimetype='application/json')

	#get practices Managers
	OfficeManagers = get_all_practice_managers(pract_id)
	if (len(OfficeManagers) == 0):
		raise Exception(' '.join([_('Practice with id'), str(pract_id),
				_('doesn\'t seem to have any managers!')]))

	association = Pending_Association()
	created_time = datetime.datetime.now()

	association.from_user_id = user.id
	association.to_user_id = OfficeManagers[0].user.id
	association.practice_location_id = practice.id
	association.created_time = created_time
	association.resent_time = created_time
	association.save()

	log_association = Log_Association()

	log_association.association_id = association.id
	log_association.from_user_id = association.from_user_id
	log_association.to_user_id = association.to_user_id
	log_association.practice_location_id = association.practice_location.id
	log_association.action_user_id = request.user.id
	log_association.action = 'CRE'
	log_association.created_time = created_time

	log_association.save()

	#now let's mail all managers invitaion request
	mail_managers(practice,
					_('DoctorCom: Request To Join Practice'),
					"""Dear Manager,

{{provider_name}} {{provider_name_last}} wants to join {{practice_name}}.

Please log into DoctorCom to view and accept the request. You can also accept 
the request by clicking https://{{server_address}}/Practice/Staff/

Best,
DoctorCom Staff
""",

				practice_name=practice.practice_name,
				provider_name=request.user.first_name,
				provider_name_last=request.user.last_name,
				server_address=settings.SERVER_ADDRESS
				)

	return HttpResponse(json.dumps('ok'))  # , mimetype='application/json')


def resendAssociation(request):
	if (request.method == 'POST'):
		form = AssocIdAssociationForm(request.POST)
	else:
		form = AssocIdAssociationForm(request.GET)

	if (not form.is_valid()):
		return HttpResponse(json.dumps(_('A server error has occurred.')))

	assoc_id = form.cleaned_data['assoc_id']
	association = Pending_Association.objects.get(pk=assoc_id)
	practice = association.practice_location

	created_time = datetime.datetime.now()
	association.resent_time = created_time

	association.save()

	log_association = Log_Association()
	log_association.association_id = association.id
	log_association.from_user_id = association.from_user_id
	log_association.to_user_id = association.to_user_id
	log_association.practice_location_id = association.practice_location.id
	log_association.action_user_id = request.user.id
	log_association.action = 'RES'
	log_association.created_time = created_time

	log_association.save()

	mail_managers(practice,
				_('DoctorCom: Request To Join Practice'),
						"""Dear Manager,

{{provider_name}} {{provider_name_last}} wants to join {{practice_name}}.

Please log into DoctorCom to view and accept the request. You can also accept 
the request by clicking https://{{server_address}}/Practice/Staff/

Best,
DoctorCom Staff
""",

				practice_name=practice.practice_name,
				provider_name=request.user.first_name,
				provider_name_last=request.user.last_name,
				server_address=settings.SERVER_ADDRESS
				)
	return HttpResponse(json.dumps('ok'))


def removeAssociation(request):
	if (request.method == 'POST'):
		form = AssocIdAssociationForm(request.POST)
	else:
		form = AssocIdAssociationForm(request.GET)

	if (not form.is_valid()):
		return HttpResponse(json.dumps(_('A server error has occurred.')))

	assoc_id = form.cleaned_data['assoc_id']
	association = Pending_Association.objects.get(pk=assoc_id)
	practice = association.practice_location

	log_association = Log_Association()

	log_association.association_id = association.id
	log_association.from_user_id = association.from_user_id
	log_association.to_user_id = association.to_user_id
	log_association.practice_location_id = association.practice_location.id
	log_association.action_user_id = request.user.id
	log_association.action = 'CAN'
	log_association.created_time = datetime.datetime.now()

	log_association.save()

	association.delete()

	mail_managers(practice,
					_('DoctorCom: Request To Join Practice Canceled'),
					"""Dear Manager,

We're sorry, but the request from {{provider_name}} {{provider_name_last}} to 
join {{practice_name}} has been cancelled.

Best,
DoctorCom Staff
""",

				practice_name=practice.practice_name,
				provider_name=request.user.first_name,
				provider_name_last=request.user.last_name
				)
	return HttpResponse(json.dumps('ok'))


def makePracticeCurrent(request):
	if (request.method == 'POST'):
		form = PractIdAssociationForm(request.POST)
	else:
		form = PractIdAssociationForm(request.GET)

	if (not form.is_valid()):
		return HttpResponse(json.dumps(['err', 'A server error has occurred.']), 
				mimetype='application/json')

	pract_id = form.cleaned_data['pract_id']

	provider = request.session['MHL_Users']['Provider']

	old_cur_prac_id = 0
	if provider.current_practice:
		old_cur_prac_id = provider.current_practice.id

	if (pract_id == 0):
		provider.current_practice = None
		provider.save()
	else:
		practice = PracticeLocation.objects.get(pk=pract_id)
		provider.current_practice = practice
		provider.save()

	if not old_cur_prac_id == pract_id:
		# send notification to related users
		thread.start_new_thread(notify_user_tab_changed, (provider.user.id,))
	return HttpResponse(json.dumps(['err', 'No errors.']), mimetype='application/json')


def removePractice(request):
	if (request.method == 'POST'):
		form = PractIdAssociationForm(request.POST)
	else:
		form = PractIdAssociationForm(request.GET)

	if (not form.is_valid()):
		return HttpResponse(json.dumps(['err', 'A server error has occurred.']), 
						mimetype='application/json')

	pract_id = form.cleaned_data['pract_id']
	current_date = datetime.datetime.now()
	two_weeks_date = current_date + datetime.timedelta(days=15)

	user = request.user
	provider = request.session['MHL_Users']['Provider']
	practice = PracticeLocation.objects.get(pk=pract_id)

	#remove from call group for this practice
	#if schedule exists in next two weeks massage managers, so they can cover gaps
	if practice.call_group:
		call_group = practice.call_group
		events_set = EventEntry.objects.filter(callGroup=call_group, 
			oncallPerson=user, eventStatus=1, endDate__range=(current_date, two_weeks_date))
	else:
		call_group = practice.call_groups.all()
		events_set = EventEntry.objects.filter(callGroup__in=call_group, 
			oncallPerson=user, eventStatus=1, endDate__range=(current_date, two_weeks_date))
	if (events_set.count() > 0):	

		subject = _('DoctorCom: Gaps in On Call Schedule')
		body = """Dear Manager,

%(user)s has left %(practice_name)s. %(user)s was removed from the on-call schedule, 
creating gaps in coverage. Please update your on-call schedule to fill these gaps.

Best,
DoctorCom Staff""" % {'user': provider.user, 'practice_name': practice.practice_name}

		#get a list of all office managers for this practice
		OfficeManagers = get_all_practice_managers(practice.id)
		#this will be message for office managers, next key makes sms not being sent out 
		#with message-becasue office managers do not have to carry cell phones, dahsboard only
		request.session['answering_service'] = _('yes')

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

	#remove from schedule - mark as deleted	
	if practice.call_group:
		CallGroupMember.objects.filter(call_group=call_group, member=user).delete()
		EventEntry.objects.filter(callGroup=call_group, oncallPerson=user, 
			endDate__gte=current_date).update(eventStatus=0, lastupdate=current_date)
	else:
		CallGroupMember.objects.filter(call_group__in=call_group, member=user).delete()
		EventEntry.objects.filter(callGroup__in=call_group, oncallPerson=user, 
			endDate__gte=current_date).update(eventStatus=0, lastupdate=current_date)

	#remove from provider
	if (provider.current_practice == practice):
		provider.current_practice = None
		provider.save()

	provider.practices.remove(practice)

	# send notification to related users
	thread.start_new_thread(notify_user_tab_changed, (provider.user.id,))

	return HttpResponse(json.dumps(['err', 'No errors.']), mimetype='application/json')


#update by xlin 20120711 to fix bug 983
def removePracticeErrorCheck(request):
	if (request.method == 'POST'):
		form = PractIdAssociationForm(request.POST)
	else:
		form = PractIdAssociationForm(request.GET)
	if (not form.is_valid()):
		return HttpResponse(json.dumps(['err', _('A server error has occurred.')]), 
			mimetype='application/json')
	pract_id = form.cleaned_data['pract_id']
	current_date = datetime.datetime.now()
	two_weeks_date = current_date + datetime.timedelta(days=15)
	user = request.user
	practice = PracticeLocation.objects.get(pk=pract_id)
	#remove from call group for this practice

	if practice.call_group:
		call_group = practice.call_group
		events_set = EventEntry.objects.filter(callGroup=call_group, oncallPerson=user, 
			eventStatus=1, endDate__range=(current_date, two_weeks_date))
	else:
		call_group = practice.call_groups.all()
		events_set = EventEntry.objects.filter(callGroup__in=call_group, 
			oncallPerson=user, eventStatus=1, endDate__range=(current_date, two_weeks_date))

	#check if in the next 2 weeks event exist in scheduler for this provider
	if events_set.count() > 0:
		return HttpResponse(json.dumps('warning'))  # do not neet i10n
	else:
		return HttpResponse(json.dumps('ok'))  # do not neet i10n


def getSpecialtyOptions(request):
	specialty_choices = SPECIALTY_CHOICES
	return HttpResponse(json.dumps(specialty_choices))


def search_by_proximity(request):
	if (request.method == 'POST'):
		form = ProximitySearchForm(request.POST)
	else:
		form = ProximitySearchForm(request.GET)

	if (form.is_valid()):
		community = dict()
		zip = form.cleaned_data['zip']
		proximity = form.cleaned_data['proximity']
		tab_type = form.cleaned_data['tab_type']
		licensure = form.cleaned_data['licensure']

		providers = None
		if (tab_type == 'community_broker'):
			if licensure == 'ALL':
				providers = get_community_providers_by_zipcode(zip, proximity)
			else:
				providers = get_community_providers_by_zipcode(zip, proximity, licensure)
			community['not_show_header'] = True
			community['providers'] = set_providers_result(providers, request)

			return render_to_response('user_info_broker.html', community)
		if (tab_type == "clerk"):
			providers = get_clinical_clerks_by_zipcode(zip, proximity)
		else:
			providers = get_community_providers_by_zipcode(zip, proximity)
		community['providers'] = set_providers_result(providers, request)

		return render_to_response('userInfo.html', community)

	else:  # if (not form.is_valid())
		return HttpResponse(json.dumps(['err', _('A server error has occurred.')]), 
			mimetype='application/json')


def get_providers_by_conds(request):
	if (request.method == 'POST'):
		type = request.POST['type']
		search_terms = unicode.split(request.POST['name'])

		q_1 = Q()
		q_2 = Q()
		if search_terms:
			if len(search_terms) == 1:
				first_name = search_terms[0]
				last_name2 = ''
			else:
				first_name = search_terms[0]
				last_name = search_terms[1:]
				last_name2 = ' '.join(last_name)
			if last_name2:
				q_2 = Q(user__first_name__icontains=first_name) \
					& Q(user__last_name__icontains=last_name2) \
					| Q(user__first_name__icontains=last_name2) \
					& Q(user__last_name__icontains=first_name)
				q_1 = Q(user__user__first_name__icontains=first_name) \
					& Q(user__user__last_name__icontains=last_name2) \
					| Q(user__user__first_name__icontains=last_name2) \
					& Q(user__user__last_name__icontains=first_name)
			else:
				q_2 = Q(user__first_name__icontains=first_name) \
					| Q(user__last_name__icontains=first_name)
				q_1 = Q(user__user__first_name__icontains=first_name) \
					| Q(user__user__last_name__icontains=first_name)

		physicians = []
		np_pas = []
		manager_user_ids = []
		office_staffs = []
		if type == 'providers':
			np_pas = NP_PA.active_objects.filter(q_1).distinct().\
				select_related('user', 'user__user', 'user__user__user')
			physicians = Physician.active_objects.filter(q_1).distinct().\
				select_related('user', 'user__user', 'user__user__user')
		elif type == 'staffs':
			manager_user_ids = Office_Manager.active_objects.filter(q_1).distinct().\
				values_list("user__id", flat=True)
			office_staffs = OfficeStaff.active_objects.filter(q_2).distinct().\
				select_related('user', 'user__user')
		else:
			np_pas = NP_PA.active_objects.filter(q_1).distinct().\
				select_related('user', 'user__user', 'user__user__user')
			physicians = Physician.active_objects.filter(q_1).distinct().\
				select_related('user', 'user__user', 'user__user__user')
			manager_user_ids = Office_Manager.active_objects.filter(q_1).\
				distinct().values_list("user__id", flat=True)
			office_staffs = OfficeStaff.active_objects.filter(q_2).distinct().\
				select_related('user', 'user__user')

		return_set = []
		for phy in physicians:
			u = phy.user
			user_info = {
						'id': u.user.id,
						'fullname':get_fullname(u),
						'user_type': _('Doctor'),
						'office_address': ' '.join([u.user.address1, 
							u.user.address2, u.user.city, u.user.state, u.user.zip]),
						'specialty': ''
					}
			if ('specialty' in dir(phy) and phy.specialty):
				user_info['specialty'] = phy.get_specialty_display()
			if u.clinical_clerk:
				user_info['user_type'] = _('Medical Student')
			return_set.append(user_info)

		for np_pa in np_pas:
			u = np_pa.user
			user_info = {
						'id': u.user.id,
						'fullname':get_fullname(u),
						'user_type': _('NP/PA/Midwife'),
						'office_address': ' '.join([u.user.address1, 
							u.user.address2, u.user.city, u.user.state, u.user.zip]),
						'specialty': 'NP/PA/Midwife'
					}
			return_set.append(user_info)

		for staff in office_staffs:
			user_info = {
						'id':staff.user.id,
						'fullname':get_fullname(staff),
						'user_type': _('Staff'),
						'office_address': ' '.join([staff.user.address1, 
							staff.user.address2, staff.user.city, 
								staff.user.state, staff.user.zip]),
						'specialty': 'N/A'
					}
			if len(manager_user_ids) > 0 and staff.id in manager_user_ids:
				user_info['user_type'] = _('Manager')
			return_set.append(user_info)

		return HttpResponse(json.dumps(sorted(return_set, key=lambda item: "%s" % (item['fullname']))))

def get_members_for_org(request):
	id = request.POST['id']
	hosp = request.POST['hosp']
	members = getOrgMembers(int(id), hospital=hosp)
	providers = set_practice_members_result(members, request)
	for p in providers:
		if isinstance(p, Provider):
			p.template_specialty = get_specialty_display_by_provider(p)
		else:
			p.template_specialty = ""
	community = {
			'providers': providers
		}

	return render_to_response('userInfo3.html', community)


def emailExist(request):
	if request.method == 'POST':
		mail = request.POST['email']
		users = User.objects.filter(email=mail)
		if users:
			return HttpResponse(json.dumps({'has_email': True}))
	return HttpResponse(json.dumps({'has_email': False}))


#add by xlin 121011 for issue 1289
def searchStates(request):
	option = request.GET['term'].lower()
	states = []
	for o in STATE_CHOICES:
		if o[1].lower().find(option) == 0:
		#if option in o[1].lower():
			states.append(o[0])

	st = list(States.objects.filter(state__in=states).values('pk', 'state'))
	result = [{'id':s['pk'], 'name':getStateFullName(s['state'])}
			for s in st]
	return HttpResponse(json.dumps(result))


def getStateFullName(state):
	for o in STATE_CHOICES:
		if o[0] == state:
			return o[1]


def validate_email_and_phone(request):
	username = request.POST['username']
	email = request.POST['email']
	phone = request.POST['phone']
	errs = {}
	if MHLUser.objects.filter(Q(username=username)):
		errs['err1'] = 1

	# When refine register feature, remove following 3 lines to a common function in utils.
	for url in settings.CHECKUSERNAME_URL:
		if check_username_another_server(username, url, 0):
			errs['err1'] = 1

	if MHLUser.objects.filter(Q(email=email)):
		errs['err2'] = 1

	if settings.CALL_ENABLE and phone and MHLUser.objects.filter(Q(mobile_phone=phone)):
		errs['err3'] = 1

	return HttpResponse(json.dumps(errs))
