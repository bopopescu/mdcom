import json
import time
import thread

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.models.query_utils import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _

from MHLogin.DoctorCom.IVR.forms import PinChangeForm
from MHLogin.DoctorCom.IVR.models import VMBox_Config, get_new_pin_hash
from MHLogin.MHLOrganization.forms import OrganizationProfileSimpleForm, \
	ParentOrgForm, OrganizationSearchForm, OrgTypeForm
from MHLogin.MHLOrganization.utils import format_tree_data, \
	get_orgs_I_can_manage, can_we_remove_this_org,\
	can_we_move_this_org_under_that_org,\
	which_orgs_contain_this_org, get_exclude_provider_ids,\
	notify_org_users_tab_chanaged
from MHLogin.MHLOrganization.utils_org_member import \
	send_invite_mail_to_org_manager, send_cancel_mail_to_org_manager, \
	accept_member_org_invite, rejected_member_org_invite
from MHLogin.MHLPractices.forms import PracticeProfileForm, AccessNumberForm, \
	RemoveForm, HolidaysForm, HoursForm
from MHLogin.MHLPractices.forms_org import OrganizationSettingForm
from MHLogin.MHLPractices.models import PracticeLocation, \
	OrganizationRelationship, OrganizationType, PracticeHours, PracticeHolidays, \
	AccessNumber, DAYSNAMES, AccountActiveCode, OrganizationMemberOrgs, \
	Pending_Org_Association, Log_Org_Association, Pending_Association
from MHLogin.MHLPractices.utils import getNewCreateCode
from MHLogin.MHLUsers.decorators import RequireOrganizationManager
from MHLogin.MHLUsers.forms import CreateOfficeStaffForm, CreateMHLUserForm, \
	CreateProviderForm, UserTypeSelecterForm
from MHLogin.MHLUsers.models import Dietician, Nurse, Physician, NP_PA, \
	OfficeStaff, Broker, Provider, Office_Manager
from MHLogin.MHLUsers.utils import update_staff_address_info_by_practice, \
	get_managed_practice, get_practice_org, get_fullname
from MHLogin.genbilling.models import Account
from MHLogin.utils import ImageHelper
from MHLogin.utils.constants import RESERVED_ORGANIZATION_ID_SYSTEM, \
	USER_TYPE_DOCTOR, USER_TYPE_NPPA, USER_TYPE_MEDICAL_STUDENT, \
	USER_TYPE_OFFICE_MANAGER, USER_TYPE_NURSE, USER_TYPE_DIETICIAN, \
	USER_TYPE_OFFICE_STAFF
from MHLogin.utils.errlib import err403, err404
from MHLogin.utils.templates import get_context_for_organization, phone_formater, \
	get_context
from MHLogin.utils.timeFormat import getDisplayedTimeZone, hour_format, \
	minute_format, OLD_TIME_ZONES_MIGRATION, getCurrentTimeZoneForUser, \
	formatTimeSetting
from MHLogin.MHLPractices.forms_staffsearch import ProviderByMailForm
from MHLogin.MHLOrganization.views_member import _get_specialty, addAssociation
from MHLogin.Invites.models import Invitation
from MHLogin.MHLPractices.utils_pendding import user_is_pendding_in_org
from MHLogin.KMS.utils import create_default_keys
from MHLogin.utils.mh_logging import get_standard_logger

logger = get_standard_logger('%s/MHLOrganization/views.log' % (settings.LOGGING_ROOT),
							'MHLOrganization.views', settings.LOGGING_LEVEL)


def org_list(request):
	context = get_context(request)
	return render_to_response(
		'MHLOrganization/includes/organization_template.html', context)


def org_tree(request):
	root_node = request.POST.get('root_node', None)
	show_parent = request.POST.get('show_parent', None)
	if show_parent and root_node:
		try:
			root_node = OrganizationRelationship.objects\
					.get(organization=root_node).parent.id
		except:
			root_node = None

	user_id = request.user.id
	org_rs = get_orgs_I_can_manage(user_id, root_id=root_node)
	result_set = format_tree_data(org_rs)
	return HttpResponse(json.dumps(result_set), mimetype='application/json')


@RequireOrganizationManager
def org_setting_edit(request):
	context = get_context_for_organization(request)
	context['save_sucess'] = False
	inherit_org_type = True
	if request.org.organization_setting and \
			not request.org.organization_setting.delete_flag:
		inherit_org_type = False
	org_setting = request.org.get_setting()

	old_display_in_contact_list_tab = \
		request.org.get_setting_attr("display_in_contact_list_tab")

	setting_form = OrganizationSettingForm(instance=org_setting)
	if request.method == 'POST':
		setting_form = OrganizationSettingForm(data=request.POST, instance=org_setting)
		if 'inherit_org_type' in request.POST and \
				request.POST['inherit_org_type']:
			inherit_org_type = request.POST['inherit_org_type']
			if request.org.organization_setting:
				request.org.organization_setting.delete_flag = True
				request.org.organization_setting.save()
		else:
			inherit_org_type = False
			if request.org.organization_setting:
				setting_form = OrganizationSettingForm(request.POST, \
						instance=request.org.organization_setting)
				if setting_form.is_valid():
					org_setting = setting_form.save()
					org_setting.delete_flag = False
					org_setting.save()
			else:
				setting_form = OrganizationSettingForm(request.POST)
				org_setting = setting_form.save()
				request.org.organization_setting = org_setting
				request.org.save()

		new_display_in_contact_list_tab = \
			request.org.get_setting_attr("display_in_contact_list_tab")
		logger.debug("new display_in_contact_list_tab: %s, old display_in_contact_list_tab: %s"\
			% (str(new_display_in_contact_list_tab), str(old_display_in_contact_list_tab)))
		if not new_display_in_contact_list_tab == old_display_in_contact_list_tab:
			# send notification to related users
			thread.start_new_thread(notify_org_users_tab_chanaged,\
						(request.org.id,), {"include_member_org": True})

		context['save_sucess'] = True
	context['inherit_org_type'] = inherit_org_type
	context['form'] = setting_form
	return render_to_response('MHLOrganization/Settings/org_setting.html', context)


@RequireOrganizationManager
def org_add(request):
	context = get_context_for_organization(request)
	if request.method == "GET":
		try:
			form = OrganizationProfileSimpleForm(request.GET,
						initial={'user_id': request.user.id})
			context['form'] = form
			context['organization_type_errors'] = ""
			if form.fields['parent_org_ids'].choices and\
					form.fields['organization_type'].choices:
				return render_to_response('MHLOrganization/Information/org_add.html',\
					context)
			return render_to_response('MHLOrganization/Information/org_no_permission.html',\
					context)
		except:
			return render_to_response('MHLOrganization/Information/org_no_permission.html',\
				context)


@RequireOrganizationManager
def org_save(request):
	if request.method == 'POST':
		user_id = request.user.id
		org_rs = get_orgs_I_can_manage(user_id)
		form = OrganizationProfileSimpleForm(request.REQUEST,
					initial={
						'parent_org_ids': format_tree_data(org_rs, True),
						'user_id': request.user.id,
				})

		if(form.is_valid()):
			try:
				org = form.save(commit=False)
				org_type = OrganizationType.objects.get(
					pk=int(form.cleaned_data['organization_type']))
				org.organization_type = org_type
				org.practice_lat = 0
				org.practice_longit = 0
				org.save()

				org_rs = OrganizationRelationship()
				org_rs.organization_id = org.id
				org_rs.parent_id = int(form.cleaned_data['parent_org_ids'])
				org_rs.create_time = int(time.time())
				org_rs.save()
			except:
				transaction.rollback()
				context = get_context_for_organization(request)
				context['form'] = form 
				return render_to_response('MHLOrganization/Information/org_save.html',\
						context)
		else:
			context = get_context_for_organization(request)
			context['form'] = form 
			return render_to_response('MHLOrganization/Information/org_save.html',\
		context)
	return HttpResponse(json.dumps({"org_id": request.org.id}), mimetype='application/json')


def get_context_manager_role(request, context):
	mgr = request.org_mgr
	manager_role = 2 if request.org_admin else mgr.manager_role

	#is this office manager super manager or not
	context['manager_role'] = manager_role
	context['show_cc'] = manager_role

	if (manager_role == 2 and not request.org_admin):
		#only for practice with group set set up and if this is super 
		#manager show manage CC link
		practice_group = request.org.get_parent_org()
		if (practice_group is None):
			context['show_cc'] = 1

		#until, we convert all practices to have accounts, only show links to 
		# practices that actually have billing account
		try:
			Account.objects.get(practice_group_new=practice_group)
		except ObjectDoesNotExist:
			context['manager_role'] = 1


@RequireOrganizationManager
def org_view(request):
	context = get_context_for_organization(request)
	org = request.org
	get_context_manager_role(request, context)

	mhluser = request.session['MHL_Users']['MHLUser']

	context['has_move_btn'] = True if org.id != RESERVED_ORGANIZATION_ID_SYSTEM else False
	context['has_remove_btn'] = True if org.id != RESERVED_ORGANIZATION_ID_SYSTEM and \
			'Administrator' in request.session['MHL_Users'] else False

	# get the office location info
	context['org_type'] = org.organization_type.name if org.organization_type\
			else ""
	parent_org = OrganizationRelationship.active_objects.filter(\
			organization__pk=request.org.id)[0].parent
	context['org_parent_org_name'] = parent_org.practice_name if parent_org else ""

	context['office_name'] = org.practice_name
	context['office_address1'] = org.practice_address1
	context['office_address2'] = org.practice_address2
	context['office_city'] = org.practice_city
	context['office_state'] = org.practice_state
	context['office_zip'] = org.practice_zip
	tz = getDisplayedTimeZone(org.time_zone)
	context['office_time_zone'] = tz if tz else _("(none)")
	context['office_phone'] = phone_formater(org.practice_phone)
	context['backline_phone'] = phone_formater(org.backline_phone)

	context['office_logo'] = ImageHelper.get_image_by_type(\
		org.practice_photo, size='Middle', type='Practice',\
		resize_type='img_size_practice')

	#now we need to get office hours
	practiceHoursList = PracticeHours.objects.filter(practice_location=org.id)
	result = []
	for p in practiceHoursList:
		obj = {}
		obj['open'] = hour_format(mhluser, p.open)
		obj['close'] = hour_format(mhluser, p.close)
		obj['lunch_start'] = hour_format(mhluser, p.lunch_start)
		obj['lunch_duration'] = p.lunch_duration
		obj['day_of_week'] = p.day_of_week
		result.append(obj)
	context['hours'] = result

	practiceHolidayList = PracticeHolidays.objects.filter(practice_location=org.id)
	context['holidays'] = practiceHolidayList

	#get whether we can remove this org 
	can_remove_org = can_we_remove_this_org(org.id, mhluser.id)
	context['can_remove_org'] = can_remove_org

	context['member_of'] = which_orgs_contain_this_org(org.id)
	return render_to_response('MHLOrganization/Information/org_view.html', context)


@RequireOrganizationManager
def org_remove(request):
	org = request.org
	mhluser = request.session['MHL_Users']['MHLUser']
	can_remove_org = can_we_remove_this_org(org.id, mhluser.id)
	if(can_remove_org):
		request.org.delete_flag = True
		request.org.practice_name = ' '.join([request.org.practice_name,
				'Removed', str(int(time.time()))])

		request.org.save()
		# send notification to related users
		thread.start_new_thread(notify_org_users_tab_chanaged,\
					(request.org.id,), {"include_member_org": True})
		return HttpResponse(json.dumps({'status': 'ok'}), mimetype='application/json')
	else:
		return err403(request, err_msg=_("You can't remove this organization."))


@RequireOrganizationManager
def org_drag_move(request):
	sub_org_name = ""
	parent_org_name = ""
	if request.method == "POST":
		try:
			org_id = int(request.POST['org_id'])
			org_parent_id = int(request.POST['org_parent_id'])
			sub_org = PracticeLocation.objects.get(id=org_id)
			parent_org = PracticeLocation.objects.get(id=org_parent_id)
			sub_org_name = sub_org.practice_name
			parent_org_name = parent_org.practice_name
			if can_we_move_this_org_under_that_org(sub_org, parent_org):
				org_rs = OrganizationRelationship.active_objects.get(\
						organization=org_id)
				old_parent_id = org_rs.parent_id
				org_rs.parent_id = org_parent_id
				org_rs.save()

				logger.debug("new parent_id: %s, old parent_id: %s"\
					% (str(org_parent_id), str(old_parent_id)))
				if not old_parent_id == org_parent_id:
					# send notification to related users
					thread.start_new_thread(notify_org_users_tab_chanaged,
							(org_id,), {"include_self_tree": True})
				return HttpResponse(json.dumps({'status': 'OK'}), 
						mimetype='application/json')
		except:
			pass
	if sub_org_name and parent_org_name:
		err_msg = _("You cannot move [%(sub_org_name)s] to [%(parent_org_name)s].") % \
				{"sub_org_name": sub_org_name, "parent_org_name": parent_org_name}
	else:
		err_msg = ("You cannot move to root node.")

	return HttpResponse(json.dumps({'status': 'err', 'err_msg': err_msg}), 
			mimetype='application/json')


@RequireOrganizationManager
def org_move(request):
	context = get_context_for_organization(request)
	context['show_form_errors'] = True
	org = request.org
	parent_org = OrganizationRelationship.active_objects.filter(\
			organization__pk=request.org.id)[0].parent
	if 'parent_org_ids' in request.REQUEST:
		parent_org_ids = request.REQUEST['parent_org_ids']
		context['showChange'] = True
	else:
		parent_org_ids = parent_org.id if parent_org \
				else RESERVED_ORGANIZATION_ID_SYSTEM 
		context['showChange'] = False

	if 'organization_type' in request.REQUEST:
		organization_type = request.REQUEST['organization_type']
	else:
		organization_type = org.organization_type.id

	org_type = get_object_or_404(OrganizationType, id=organization_type)

	pareorg_form = ParentOrgForm(data={'parent_org_ids': parent_org_ids,
			'organization_type': organization_type},
			parent_org_ids=parent_org_ids, user_id=request.user.id,
			org_id=org.id)
	context['pareorg_form'] = pareorg_form

	if not pareorg_form.fields['parent_org_ids'].choices:
		context['has_move_per'] = True
		return render_to_response('MHLOrganization/Information/org_no_permission.html',\
					context)

	if (request.method == 'POST'):
		if pareorg_form.is_valid():
			old_display_in_contact_list_tab = \
				request.org.get_setting_attr("display_in_contact_list_tab")
			request.org.organization_type = org_type
			request.org.save()
			new_display_in_contact_list_tab = \
				request.org.get_setting_attr("display_in_contact_list_tab")

			org_rs = OrganizationRelationship.active_objects.get(organization=org)
			old_parent_id = org_rs.parent_id
			org_parent_id = int(parent_org_ids)
			org_rs.parent_id = org_parent_id
			org_rs.save()
			logger.debug("new parent_id: %s, old parent_id: %s"\
					% (str(org_parent_id), str(old_parent_id)))
			logger.debug("new display_in_contact_list_tab: %s, old display_in_contact_list_tab: %s"\
					% (str(new_display_in_contact_list_tab), str(old_display_in_contact_list_tab)))
			if not old_parent_id == org_parent_id \
				or not new_display_in_contact_list_tab == old_display_in_contact_list_tab:
				include_self_tree = not old_parent_id == org_parent_id
				include_member_org = not new_display_in_contact_list_tab \
						== old_display_in_contact_list_tab
				# send notification to related users
				thread.start_new_thread(notify_org_users_tab_chanaged, (request.org.id,),\
						{
							"include_member_org": include_member_org,
							"include_self_tree": include_self_tree
						})
			return HttpResponse(json.dumps({'status': 'ok'}), mimetype='application/json')
		else:
			context['show_form_errors'] = True

		try:
			org.time_zone = OLD_TIME_ZONES_MIGRATION[org.time_zone]
		except:
			pass
	else:
		context['show_form_errors'] = False
	return render_to_response('MHLOrganization/Information/org_move.html', context)


@RequireOrganizationManager
def org_edit(request):
	context = get_context_for_organization(request)
	context['show_form_errors'] = True
	org = request.org
	context["save_success"] = False

	if 'organization_type' in request.REQUEST:
		organization_type = request.REQUEST['organization_type']
	else:
		organization_type = org.organization_type.id

	org_type = get_object_or_404(OrganizationType, id=organization_type)

	type_form = OrgTypeForm(data={\
			'organization_type': organization_type}, \
			user_id=request.user.id, org_id=request.org.id)
	context['pareorg_form'] = type_form

	old_display_in_contact_list_tab = org.get_setting_attr("display_in_contact_list_tab")

	if (request.method == 'POST'):
		old_url = None
		if org.practice_photo:
			old_url = org.practice_photo.name
		form = PracticeProfileForm(request.POST, request.FILES, instance=org)
		if form.is_valid() and type_form.is_valid():
			org = form.save(commit=False)
			org.practice_lat = form.cleaned_data['practice_lat']
			org.practice_longit = form.cleaned_data['practice_longit']
			org.organization_type = org_type
			org.save()

			update_staff_address_info_by_practice(org)
			new_url = None
			if org.practice_photo:
				new_url = org.practice_photo.name
			if old_url != new_url:
				ImageHelper.generate_image(old_url, new_url, 'img_size_practice')
			context["save_success"] = True

			new_display_in_contact_list_tab = \
				org.get_setting_attr("display_in_contact_list_tab")

			logger.debug("new display_in_contact_list_tab: %s, old display_in_contact_list_tab: %s"\
				% (str(new_display_in_contact_list_tab), str(old_display_in_contact_list_tab)))
			if not new_display_in_contact_list_tab == old_display_in_contact_list_tab:
				# send notification to related users
				thread.start_new_thread(notify_org_users_tab_chanaged,\
						(org.id,), {"include_member_org": True})

		context['form'] = form
		try:
			org.time_zone = OLD_TIME_ZONES_MIGRATION[org.time_zone]
		except:
			pass
	else:
		context['show_form_errors'] = False
		context['form'] = PracticeProfileForm(instance=org)
	context['type_form'] = type_form
	return render_to_response('MHLOrganization/Information/org_edit.html', context)


@RequireOrganizationManager
def member_org_view(request):
	context = get_context_for_organization(request)
	return render_to_response('MHLOrganization/MemberOrg/member_org_view.html', context)


@RequireOrganizationManager
def member_org_show_org(request):
	context = get_context_for_organization(request)
	member_orgs = OrganizationMemberOrgs.objects.filter(\
			from_practicelocation__pk=request.org.id)\
			.select_related('to_practicelocation')\
			.order_by('to_practicelocation__practice_name')

	qf = Q()
	context['search_input'] = ""
	if request.method == "POST":
		search_input = request.POST.get("search_input", "")
		if search_input:
			context['search_input'] = search_input
			qf = Q(to_practicelocation__practice_name__icontains=search_input)

	member_orgs = member_orgs.filter(qf)
	context['member_org_count'] = len(member_orgs)

	user = request.session['MHL_Users']['MHLUser']
	local_tz = getCurrentTimeZoneForUser(user, \
			current_practice=context['current_practice'])

	context['index'] = index = int(request.REQUEST.get('index', 0))
	context['count'] = count = int(request.REQUEST.get('count', 10))

	return_set = [{
			'id': mo.id,
			'to_name': mo.to_practicelocation.practice_name,
			'provider_count': Provider.active_objects.filter(\
					Q(practices=mo.to_practicelocation)).count(),
			'to_logo': ImageHelper.get_image_by_type(\
					mo.to_practicelocation.practice_photo,
					"Small", "Practice"),
			'create_date': formatTimeSetting(user, mo.create_time, local_tz),
			'billing_flag': mo.billing_flag
		} for mo in member_orgs[index*count:(index+1)*count]]

	context['member_orgs'] = return_set

	return render_to_response('MHLOrganization/MemberOrg/member_org_list.html', context)


@RequireOrganizationManager
def member_org_show_invite(request):
	context = get_context_for_organization(request)
	current_org_id = request.org.id
	pendings = Pending_Org_Association.objects.filter(from_practicelocation__id=current_org_id)
	context['total_count'] = len(pendings)

	user = request.session['MHL_Users']['MHLUser']
	local_tz = getCurrentTimeZoneForUser(user, \
			current_practice=context['current_practice'])

	context['index'] = index = int(request.REQUEST.get('index', 0))
	context['count'] = count = int(request.REQUEST.get('count', 10))

	# get member organization invitations
	context['member_org_invitations'] = [{
				'pending_id': pending.id,
				'to_id': pending.to_practicelocation.id,
				'to_name': pending.to_practicelocation.practice_name,
				'provider_count': Provider.active_objects.filter(\
						Q(practices=pending.to_practicelocation)).count(),
				'to_logo': ImageHelper.get_image_by_type(\
						pending.to_practicelocation.practice_photo,
						"Small", "Practice"),
				'create_date': formatTimeSetting(user, pending.create_time, local_tz)
			} for pending in pendings[index*count:(index+1)*count]]
	return render_to_response('MHLOrganization/MemberOrg/member_org_invite_list.html', context)


@RequireOrganizationManager
def member_org_invite_step1(request):
	context = get_context_for_organization(request)
	return render_to_response('MHLOrganization/MemberOrg/invite_step1.html', context)


@RequireOrganizationManager
def member_org_invite_step2(request):
	context = get_context_for_organization(request)
	form = OrganizationSearchForm(request.POST)
	context["org_list"] = []
	context["org_count"] = 0
	if form.is_valid():
		org_name = form.cleaned_data["org_name"]
		current_org_id = request.org.id
		pending_ids = Pending_Org_Association.objects.filter(
			from_practicelocation__id=current_org_id).\
				values_list("to_practicelocation__id", flat=True)
		member_ids = OrganizationMemberOrgs.objects.filter(
			from_practicelocation__id=current_org_id).\
				values_list("to_practicelocation__id", flat=True)
		orgs = PracticeLocation.objects.filter(practice_name__icontains=org_name).\
			exclude(id__in=member_ids).exclude(id__in=pending_ids).exclude(id=request.org.id)

		orgs = [
				{
					'id': org.id,
					'practice_name': org.practice_name,
					'practice_address1': org.practice_address1,
					'practice_address2': org.practice_address2,
					'practice_city': org.practice_city,
					'practice_state': org.practice_state,
					'practice_photo': ImageHelper.get_image_by_type(org.practice_photo, 
								"Middle", 'Practice', 'img_size_practice')
				} for org in orgs]

		context["org_list"] = orgs
		context["org_count"] = len(orgs)
	return render_to_response('MHLOrganization/MemberOrg/invite_step2.html', context)


@RequireOrganizationManager
def member_org_invite_step3(request):
	context = get_context_for_organization(request)
	sel_org_id = request.POST["sel_org_id"]
	sel_org = get_object_or_404(PracticeLocation, pk=sel_org_id)
	if request.org_admin:
		sel_org_id
		request.org.save_member_org(member_org=sel_org)

		# send notification to related users
		thread.start_new_thread(notify_org_users_tab_chanaged, (sel_org.id,), 
				{"include_self_tree": True})
	else:
		create_time = time.time()
		pending = Pending_Org_Association(
				from_practicelocation_id=request.org.id,
				to_practicelocation_id=sel_org_id,
				sender_id=request.user.id,
				create_time=create_time,
				resent_time=create_time
			)
		pending.save() 
		pending_log = Log_Org_Association(
				association_id=pending.id,
				from_practicelocation_id=request.org.id,
				to_practicelocation_id=sel_org_id,
				sender_id=request.user.id,
				action_user_id=request.user.id,
				action='CRE'
			)
		pending_log.save()
		# send email
		send_invite_mail_to_org_manager(pending)
	return render_to_response('MHLOrganization/MemberOrg/invite_step3.html', context)


@RequireOrganizationManager
def member_org_remove(request):
	if request.method == "POST":
		try:
			org_rs_id = request.POST.get("org_rs_id", None)
			org_rs = OrganizationMemberOrgs.objects.get(pk=org_rs_id)
			org_rs.delete()
			# send notification to related users
			thread.start_new_thread(notify_org_users_tab_chanaged, \
					(org_rs.to_practicelocation.id,), {"include_self_tree": True})
		except:
			pass
	return HttpResponse(json.dumps({'status': 'OK'}), mimetype='application/json')


@RequireOrganizationManager
def member_org_cancel_invite(request, pending_id):
	context = get_context_for_organization(request)
	pending = Pending_Org_Association.objects.filter(id=pending_id)
	if pending:
		pending = pending[0]
		pending_log = Log_Org_Association(
				association_id=pending.id,
				from_practicelocation_id=pending.from_practicelocation_id,
				to_practicelocation_id=pending.to_practicelocation_id,
				sender_id=pending.sender_id,
				action_user_id=request.user.id,
				action='CAN',
				create_time=time.time()
			)
		pending_log.save()
		pending.delete()
		send_cancel_mail_to_org_manager(pending)
	return HttpResponseRedirect(reverse(
		'MHLogin.MHLOrganization.views.member_org_show_invite'))


@RequireOrganizationManager
def member_org_resend_invite(request, pending_id):
	context = get_context_for_organization(request)
	pending = Pending_Org_Association.objects.filter(id=pending_id)
	resent_time = time.time()
	if pending:
		pending = pending[0]
		pending_log = Log_Org_Association(
				association_id=pending.id,
				from_practicelocation_id=pending.from_practicelocation_id,
				to_practicelocation_id=pending.to_practicelocation_id,
				sender_id=pending.sender_id,
				action_user_id=request.user.id,
				action='RES',
				create_time=resent_time
			)
		pending_log.save()
		pending.resent_time = resent_time
		pending.save()
		# send email
		send_invite_mail_to_org_manager(pending)
	return HttpResponse(json.dumps({'status': 'OK'}), mimetype='application/json')


def member_org_accept_invite(request, pending_id):
	user_id = request.user.id
	ret_data = accept_member_org_invite(user_id, pending_id)
	return HttpResponse(json.dumps(ret_data), mimetype='application/json')


def member_org_rejected_invite(request, pending_id):
	mhluser_id = request.user.id
	first_name = request.user.first_name
	last_name = request.user.last_name
	fullname=get_fullname(request.user)
	ret_data = rejected_member_org_invite(mhluser_id, last_name, pending_id)
	return HttpResponse(json.dumps(ret_data), mimetype='application/json')


def member_org_invite_incoming(request):
	context = get_context(request)
	if ('Office_Manager' in request.session['MHL_Users']):
		manager = request.session['MHL_Users']['Office_Manager']
		# get_managed_practice can only get the root managed practices
		managed_organizations = get_managed_practice(manager.user)
		org_ids = [org.id for org in managed_organizations]
		pendings = Pending_Org_Association.objects.filter(to_practicelocation__id__in=org_ids).\
			select_related('from_practicelocation', 'to_practicelocation')
		org_pendings = [
		{
			'pending_id': pending.id,
			'sender_name': " ".join([pending.sender.first_name, pending.sender.last_name]),
			'from_practicelocation_logo': ImageHelper.get_image_by_type(
				pending.from_practicelocation.practice_photo, "Middle", 
					'Practice', 'img_size_practice'),
			'from_practicelocatin_type': pending.from_practicelocation.organization_type.name,
			'from_practicelocation_name': pending.from_practicelocation.practice_name,
			'to_practicelocation_name': pending.to_practicelocation.practice_name,
			'to_practicelocatin_type': pending.to_practicelocation.organization_type.name,
		} for pending in pendings]

		org_pendings_ret = [
			render_to_string('MHLOrganization/MemberOrg/invitation_notification.html', p)
				for p in org_pendings]
		return HttpResponse(json.dumps(org_pendings_ret), mimetype='application/json')


@RequireOrganizationManager
def information_sub_ivr_view(request):

	context = get_context_for_organization(request)
	context['isClearData'] = 0

	org_id = request.REQUEST['org_id']
	try:
		practice = PracticeLocation.objects.get(pk=org_id)
	except:
		return err404(request)

	context['access_numbers'] = practice.accessnumber_set.all()
	if(request.method == 'POST'):
		# p = request.POST
		if('newnumber' in request.POST):
			addform = AccessNumberForm(request.POST)
			if(addform.is_valid()):
				number = addform.save(commit=False)
				number.practice = practice
				context['isClearData'] = 1
				number.save()
		else:
			addform = AccessNumberForm()

		if('delnumber' in request.POST):
			removeform = RemoveForm(request.POST, choices=[(n.id, n.id) \
				for n in context['access_numbers']])
			if(removeform.is_valid()):
				ids = removeform.cleaned_data['remove']
				AccessNumber.objects.filter(practice=practice, id__in=ids)\
					.delete()
	else:
		addform = AccessNumberForm()
	context['addform'] = addform
	context['access_numbers'] = practice.accessnumber_set.all()
	return render_to_response(
		'MHLOrganization/InformationSub/information_sub_ivr_view.html', context)


@RequireOrganizationManager
def information_sub_pin_change(request):
	context = get_context_for_organization(request)
	if (request.method == 'POST'):
		form = PinChangeForm(request.POST)
		form.user = request.user
		if (form.is_valid()):
			if 'Provider' in request.session['MHL_Users']:	
				provider = Provider.objects.get(user__id=request.user.id)
				config = provider.vm_config.get()
				config.change_pin(request, new_pin=form.cleaned_data['pin1'])
				return HttpResponseRedirect(reverse('MHLogin.MHLOrganization.views.org_view'))
				#return render_to_response('MHLOrganization/InformationSub/
				#    information_sub_pin_change.html', context)
			elif 'Broker' in request.session['MHL_Users']:	
				broker = Broker.objects.get(user__id=request.user.id)
				config = broker.vm_config.get()
				config.change_pin(request, new_pin=form.cleaned_data['pin1'])
				return HttpResponseRedirect(reverse('MHLogin.MHLOrganization.views.org_view'))
			#add by xlin 121119 to fix bug 855 that practice mgr can change pin
			elif 'OfficeStaff' in request.session['MHL_Users']:
				os = OfficeStaff.objects.get(user__id=request.user.id)
				practice = os.current_practice
				practice.pin = get_new_pin_hash(form.cleaned_data['pin1'])
				practice.save()
				return HttpResponseRedirect(reverse('MHLogin.MHLOrganization.views.org_view'))

		context['form'] = form
	if (not 'form' in context):
		context['form'] = PinChangeForm()

	return render_to_response(
		'MHLOrganization/InformationSub/information_sub_pin_change.html', context)


@RequireOrganizationManager
def information_sub_hour_edit(request):
	context = get_context_for_organization(request)
	practiceLocationId = request.org.id
	hours = []
	if (request.method == 'POST'):
		commit = True
		remove = []
		update = []
		for i in range(7):
			hoursdict = {'open' : minute_format(request.POST.getlist('open')[i]),
					  'close' : minute_format(request.POST.getlist('close')[i]),
					  'lunch_start' : minute_format(request.POST.getlist('lunch_start')[i]),
					  'lunch_duration' : request.POST.getlist('lunch_duration')[i],
					  'day_of_week' : DAYSNAMES[i][0] }

			try:
				instance = PracticeHours.objects.get(
					practice_location=request.org, day_of_week=DAYSNAMES[i][0])
			except ObjectDoesNotExist:
				instance = None
			except MultipleObjectsReturned:
				# FIXME
				# Multiple hours for day.
				#print 'FIXME: multiple hours for day %i' %(i+1)
				raise Exception(''.join([_('Multiple PracticeHours results found for practice '),
										str(request.org), _(' and weekday '),
										str(DAYSNAMES[i][0])]))
				# The following filter string is invalid. Django doesn't support
				# .delete() on sliced lists.
				# PracticeHours.objects.filter(practice_location=office_staff.current_practice, 
				# day_of_week=DAYSNAMES[i][0])[1:].delete()
			newhours = HoursForm(hoursdict, instance=instance)
			hours.append({'day': DAYSNAMES[i][1], 'form': newhours})
			if(newhours.is_valid()):
				if(newhours.cleaned_data['open']):
					h = newhours.save(commit=False)
					h.practice_location = PracticeLocation.objects.get(id=practiceLocationId)
					update.append(h)
				elif(instance):
					#if the object exists but open was newly blank, delete it
					remove.append(instance)
			else:
				commit = False
		if(commit):
			for h in update:
				h.save()
			for h in remove:
				h.delete()

			return HttpResponseRedirect(reverse(
				'MHLogin.MHLOrganization.views.information_sub_hour_edit'))
	else:
		hours_qs = PracticeHours.objects.filter(practice_location=request.org)

		for (id, day) in DAYSNAMES:
			try:
				hours.append({'day': day,
					'form': HoursForm(instance=hours_qs.get(day_of_week=id))})
			except ObjectDoesNotExist:
				hours.append({'day': day, 'form': HoursForm()})
	context['hourslist'] = hours
	context['office_name'] = request.org.practice_name
	context['office_time_zone'] = request.org.time_zone
	return render_to_response(
		'MHLOrganization/InformationSub/information_sub_hour_edit.html', context)


@RequireOrganizationManager
def information_sub_holiday_view(request):

	org = request.org

	context = get_context_for_organization(request)

	practiceHolidayList = PracticeHolidays.objects.filter(
		practice_location=org.id)

	if(request.method == 'POST'):
		choices = [(holiday.id, holiday.id) for holiday in practiceHolidayList]
		removeform = RemoveForm(request.POST, choices)
		if (removeform.is_valid()):
			ids = removeform.cleaned_data['remove']
			PracticeHolidays.objects.filter(id__in=ids, 
				practice_location=org.id).delete()

	context['holidays'] = practiceHolidayList
	return render_to_response(
		'MHLOrganization/InformationSub/information_sub_holiday_view.html', context)


@RequireOrganizationManager
def information_sub_holiday_add(request, holiday_id):

	context = get_context_for_organization(request)
	practiceLocationId = request.org.id

	#a PracticeHolidays object with id=0 should never exist, it's used by
	#the template create a new object
	if (holiday_id == '0'):
		holiday = None
	else:
		try:
			holiday = PracticeHolidays.objects.get(id=holiday_id, 
				practice_location=practiceLocationId)
		except ObjectDoesNotExist:
			return err403(request)

	if(request.method == 'POST'):
		form = HolidaysForm(request.POST, instance=holiday)
		if (form.is_valid()):
			try:
				PracticeHolidays.objects.get(~Q(id=holiday_id), 
					practice_location=practiceLocationId, 
						designated_day=form.cleaned_data['designated_day'])
				form._errors['designated_day'] = [_("a holiday already exists on that day")]
			except ObjectDoesNotExist:
				newholiday = form.save(commit=False)
				newholiday.practice_location = PracticeLocation.objects.get(id=practiceLocationId)
				newholiday.save()
				return HttpResponseRedirect(reverse(
					'MHLogin.MHLOrganization.views.information_sub_holiday_view'))
	else:
		form = HolidaysForm(instance=holiday)

	context['holiday_id'] = holiday_id
	context['form'] = form
	return render_to_response('MHLOrganization/InformationSub/information_sub_holiday_add.html', 
			context)


@RequireOrganizationManager
def member_view(request):
	context = get_context_for_organization(request)
	return render_to_response('MHLOrganization/Member/member_view.html', context)


@RequireOrganizationManager
def member_provider_create(request):
	context = get_context_for_organization(request)
	current_practice = request.org

	if request.method == 'POST':
		provider_form = CreateProviderForm(data=request.POST, current_practice=current_practice)
		if provider_form.is_valid():
			provider = provider_form.save(commit=False)
			provider.lat = provider_form.cleaned_data['lat']
			provider.longit = provider_form.cleaned_data['longit']

			provider.address1 = provider_form.cleaned_data['address1']
			provider.address2 = provider_form.cleaned_data['address2']
			provider.city = provider_form.cleaned_data['city']
			provider.state = provider_form.cleaned_data['state']
			provider.zip = provider_form.cleaned_data['zip']

			provider.current_practice = get_practice_org(current_practice)
			provider.is_active = 0
			provider.office_lat = 0.0
			provider.office_longit = 0.0
			provider.save()

			provider.practices.add(current_practice)
			provider.user_id = provider.pk
			provider.save()

			user_type = int(provider_form.cleaned_data['user_type'])

			if USER_TYPE_DOCTOR == user_type:
				#Physician
				ph = Physician(user=provider)
				ph.save()
			elif USER_TYPE_NPPA == user_type:
				#NP/PA/Midwife
				np = NP_PA(user=provider)
				np.save()
			elif USER_TYPE_MEDICAL_STUDENT == user_type:
				ph = Physician(user=provider)
				ph.save()

			# TESTING_KMS_INTEGRATION
			create_default_keys(provider.user)

			# Generating the user's voicemail box configuration
			config = VMBox_Config(pin='')
			config.owner = provider
			config.save()

			sendAccountActiveCode(request, user_type, current_practice, 
				request.session["MHL_Users"]["MHLUser"])

		else:
			context['user_form'] = provider_form
			return render_to_response('MHLOrganization/Member/member_provider_create.html', context)

	provider_form = CreateProviderForm(current_practice=current_practice)
	context['user_form'] = provider_form
	return render_to_response('MHLOrganization/Member/member_provider_create.html', context)


@RequireOrganizationManager
def member_staff_create(request):
	context = get_context_for_organization(request)
	current_practice = request.org
	if request.method == 'POST':
		staff_form = CreateOfficeStaffForm(request.POST, current_practice=current_practice)
		mhluser_form = CreateMHLUserForm(request.POST, request.FILES)

		if staff_form.is_valid() and mhluser_form.is_valid():
			mhluser = mhluser_form.save(commit=False)
			mhluser.is_active = 0
			mhluser.address1 = current_practice.practice_address1
			mhluser.address2 = current_practice.practice_address2
			mhluser.city = current_practice.practice_city
			mhluser.state = current_practice.practice_state
			mhluser.zip = current_practice.practice_zip
			mhluser.lat = current_practice.practice_lat
			mhluser.longit = current_practice.practice_longit
			mhluser.save()

			staff = staff_form.save(commit=False)
			staff.user = mhluser
			staff.current_practice = current_practice
			staff.save()

			staff.practices.add(current_practice)
			staff.save()

			staff_type = int(staff_form.cleaned_data['staff_type'])

			if USER_TYPE_OFFICE_MANAGER == staff_type:
				manager = Office_Manager(user=staff, practice=current_practice)
				manager.save()
			if USER_TYPE_NURSE == staff_type:
				nurse = Nurse(user=staff)
				nurse.save()
			elif USER_TYPE_DIETICIAN == staff_type:
				dietician = Dietician(user=staff)
				dietician.save()

			# TESTING_KMS_INTEGRATION
			create_default_keys(mhluser)

			sendAccountActiveCode(request, USER_TYPE_OFFICE_STAFF, 
				current_practice, request.session["MHL_Users"]["MHLUser"])
		else:
			context['user_form'] = mhluser_form
			context['staff_form'] = staff_form
			return render_to_response('MHLOrganization/Member/member_staff_create.html', context)
	context['user_form'] = CreateMHLUserForm()

	staff_form = CreateOfficeStaffForm(current_practice=current_practice)
	context['staff_form'] = staff_form

	return render_to_response('MHLOrganization/Member/member_staff_create.html', context)


@RequireOrganizationManager
def invite_view(request):
	context = get_context_for_organization(request)
	#todo when using template tech. render html, refactor following code
	form = UserTypeSelecterForm(current_practice=request.org)
	context["user_type_form"] = form
	return render_to_response('MHLOrganization/Invite/invite_view.html', context)


# todo merge this function with MHLogin/MHLPractices/views.py->sendAccountActiveCode
def sendAccountActiveCode(request, userType, practice, sender):
	""" Send an active code to user.
	:param request: http request
	:param userType: user type 101 or 1
	:param practice: an instance of PracticeLocation
	:param sender: an instance of MHLUser
	"""
	username = request.POST['username']
	recipient_email = request.POST['email']

	code = getNewCreateCode(username)
	log = AccountActiveCode(code=code,
		sender=request.session['MHL_UserIDs']['MHLUser'],
		recipient=recipient_email,
		#userType=int(request.POST['staff_type']),
		userType=userType,
		practice=practice)
	log.save()

	emailContext = dict()
	emailContext['username'] = username
	emailContext['code'] = code
	emailContext['email'] = recipient_email
	emailContext['name'] = request.POST['first_name'] + ' ' + request.POST['last_name']
	emailContext['sender'] = sender
	emailContext['address'] = settings.SERVER_ADDRESS
	emailContext['protocol'] = settings.SERVER_PROTOCOL
	msgBody = render_to_string('Staff/emailText.html', emailContext)
	send_mail('DoctorCom Activation', msgBody, settings.SERVER_EMAIL, [recipient_email, ],
			fail_silently=False)


@RequireOrganizationManager
def invite_provider(request):
	step = int(request.REQUEST['step'])
	context = get_context_for_organization(request)
	return get_template_by_step(request, step, context)


def get_template_by_step(request, step, context):
	template_dict = {
		'step1': 'MHLOrganization/Member/invite_provider_step1.html',
		'step2-email': 'MHLOrganization/Member/invite_provider_step2_email.html',
		'step2-dcm': 'MHLOrganization/Member/invite_provider_step2_dcm.html',
		'step3': 'MHLOrganization/Member/invite_provider_step3.html'
	}
	if step == 1:
		html = render_to_string(template_dict['step1'], context)
		return HttpResponse(json.dumps({
			"html": html
		}), mimetype='application/json')
	if step == 2:
		index = int(request.POST.get('index', 0))
		providers, pros_count, err_tip = get_invite_valid_providers(request, index)
		if pros_count:
			if pros_count == 1:
				context['title_people'] = _('We found 1 person matches this condition.')
				context['currentItem'] = 'currentItem'
			else:
				context['title_people'] = _('We found %s people match this condition.') % pros_count
				context['currentItem'] = ''

			context['providers'] = providers
			html = render_to_string(template_dict['step2-dcm'], context)
			return HttpResponse(json.dumps({
					"html": html,
					"count": pros_count,
					"step_type": 'dcm'
			}), mimetype='application/json')
		else:
			form = UserTypeSelecterForm(current_practice=request.org)
			context["user_type_form"] = form
			context["email"] = request.POST.get('email', '')
			context['err_tip'] = err_tip
			html = render_to_string(template_dict['step2-email'], context)
			return HttpResponse(json.dumps({
					"html": html,
					"count": pros_count,
					"step_type": 'email'
			}), mimetype='application/json')
	elif step == 3:
		try:
			step_type = request.POST.get('step_type')
			if step_type == 'email':
				email = request.POST.get('email')
				user_type = int(request.POST.get('type'))
				msg = request.POST.get('msg')
				invite_user_email(email, user_type, msg, request.user, request.org)
				html = render_to_string(template_dict['step3'], context)
				return HttpResponse(json.dumps({
					"html": html
				}), mimetype='application/json')
			else:
				user_id = int(request.POST.get('prov_id'))
				if not user_is_pendding_in_org(user_id, request.org):
					addAssociation(request)
					html = render_to_string(template_dict['step3'], context)
					return HttpResponse(json.dumps({
						"html": html
					}), mimetype='application/json')

		except:
			pass
		html = render_to_string('MHLOrganization/Member/invite_err.html', context)
		return HttpResponse(json.dumps({
			"html": html,
			"err": "err"
		}), mimetype='application/json')


def invite_user_email(email, user_type, msg, user, practice):
	invite = Invitation.objects.filter(recipient=email, userType=user_type,\
			 assignPractice=practice)
	if invite:
		invite.resend_invite(msg)
	else:
		invite = Invitation()
		invite.recipient = email
		invite.assignPractice = practice
		invite.sender = user
		invite.userType = user_type
		invite.save_invitation(msg)
	if hasattr(invite, 'error'):
		raise invite.error


def get_invite_valid_providers(request, index):
	if not request.method == 'POST':
		return

	form = ProviderByMailForm(request.POST)
	if form.is_valid():
		practice = request.org
		email = form.cleaned_data['email']
		fname = form.cleaned_data['fullname']
		first_name = form.cleaned_data['firstName']
		last_name = form.cleaned_data['lastName']
		uname = form.cleaned_data['username']

		fname = fname.split()
		q = name_filter(first_name, last_name, query=Q())

		all_providers = Provider.active_objects.filter(Q(email__icontains=email),\
				Q(username__icontains=uname)).filter(q)
		exclude_provider_ids = get_exclude_provider_ids(practice)
		if exclude_provider_ids and len(exclude_provider_ids) > 0:
			all_providers = all_providers.exclude(id__in=exclude_provider_ids)

		providers = all_providers.filter(~Q(practices=practice))

		associ = list(Pending_Association.objects.filter(practice_location=practice)
					.values_list('to_user', flat=True))
		associ = associ + list(Pending_Association.objects.filter(practice_location=practice)
					.values_list('from_user', flat=True))

		providers = list(providers.exclude(id__in=associ))
		invited_providers = list(set(all_providers) - set(providers))

		count = len(providers)
		return_set = [
				{
					'id':u.user.pk,
					'name':', '.join([u.user.last_name, u.user.first_name, ]),
					'photo': ImageHelper.get_image_by_type(u.photo, 'Small', 'Provider'),
					'address1': u.user.address1,
					'address2': u.user.address2,
					'specialty':_get_specialty(u),
				}
				for u in providers[index*4:(index+1)*4]
			]
		err_tip = get_exist_user_names_in_invitation(invited_providers)

		return return_set, count, err_tip


def name_filter(first_name, last_name, query=Q()):
	if last_name:
		query = Q(first_name__icontains=first_name) &\
			Q(last_name__icontains=last_name) |\
			Q(first_name__icontains=last_name) &\
			Q(last_name__icontains=first_name)
	else:
		query = Q(first_name__icontains=first_name) |\
		Q(last_name__icontains=first_name)
	return query


def get_exist_user_names_in_invitation(invited_providers):
	count = len(invited_providers)
	names = ', '.join([str(p) for p in invited_providers])

	if count == 1:
		return _('BTW, we find 1 person (%s) '
			'matching conditions who is already in your practice or has '
				'been invited.') % names
	elif count > 1:
		return _('BTW, we find %(len)s '
			'people (%(names)s) matching conditions who are already in '
				'your practice or have been invited.') % {'len': 
					count, 'names': names}
	else:
		return ''


@RequireOrganizationManager
def invite_staff(request):
	step = int(request.REQUEST['step'])
	context = get_context_for_organization(request)
	return get_template_staff_by_step(request, step, context)


def get_template_staff_by_step(request, step, context):
	if step == 1:
		form = UserTypeSelecterForm(current_practice=request.org)
		context["user_type_form"] = form
		context["email_staff"] = request.POST.get('email', '')
		html = render_to_string('MHLOrganization/Member/invite_staff_step1.html', context)
		return HttpResponse(json.dumps({
				"html": html,
				"step_type": 'email'
		}), mimetype='application/json')
	elif step == 2:
		try:
			email = request.POST.get('email')
			user_type = int(request.POST.get('type'))
			msg = request.POST.get('msg')
			invite_user_email(email, user_type, msg, request.user, request.org)
			html = render_to_string('MHLOrganization/Member/invite_staff_step2.html', context)
			return HttpResponse(json.dumps({
				"html": html
			}), mimetype='application/json')
		except Exception:
			pass
		html = render_to_string('MHLOrganization/Member/invite_err.html', context)
		return HttpResponse(json.dumps({
			"html": html,
			"err": "err"
		}), mimetype='application/json')


