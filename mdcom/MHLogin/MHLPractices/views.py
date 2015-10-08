# -*- coding: utf-8 -*-
import json

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _

from MHLogin.DoctorCom.IVR.models import VMBox_Config
from MHLogin.DoctorCom.NumberProvisioner.forms import LocalNumberForm
from MHLogin.DoctorCom.NumberProvisioner.utils import \
	twilio_ConfigureProviderLocalNumber
from MHLogin.DoctorCom.view_boxes import box_recent_sent
from MHLogin.KMS.utils import create_default_keys
from MHLogin.MHLCallGroups.models import CallGroupMember
from MHLogin.MHLFavorite.utils import get_my_favorite
from MHLogin.MHLOrganization.utils import get_org_type_name
from MHLogin.MHLOrganization.utils_org_tab import getOrganizationsOfUser, \
	renderOrganizationForDashbord
from MHLogin.MHLPractices.forms import HolidaysForm, HoursForm, \
	PracticeProfileForm, RemoveForm, AccessNumberForm, AccessNumber, \
	ActiveAccountForm, CallerAnssvcForm
from MHLogin.MHLPractices.models import PracticeHours, PracticeHolidays, \
	PracticeLocation, AccountActiveCode, Pending_Association, DAYSNAMES
from MHLogin.MHLPractices.utils import get_practices_by_position, \
	getNewCreateCode, set_practices_result
from MHLogin.MHLUsers.forms import CreateProviderForm, CreateOfficeStaffForm, \
	CreateMHLUserForm, UserTypeSelecterForm
from MHLogin.MHLUsers.models import Provider, Nurse, Physician, NP_PA, Dietician, \
	OfficeStaff, Office_Manager, MHLUser
from MHLogin.MHLUsers.utils import get_all_site_providers, all_practice_members, \
	set_providers_result, get_community_professionals, set_practice_members_result, \
	update_staff_address_info_by_practice, get_practice_org, get_all_site_staff, \
	set_site_staff_result
from MHLogin.genbilling.models import Account
from MHLogin.utils import ImageHelper
from MHLogin.utils.errlib import err403
from MHLogin.utils.mh_logging import get_standard_logger
from MHLogin.utils.templates import phone_formater, get_context
from MHLogin.utils.timeFormat import hour_format, minute_format, \
	getDisplayedTimeZone, OLD_TIME_ZONES_MIGRATION


MSG_ACTIVE_OR_EMAIL_WRONG = _('Your active code or email is wrong. Please check your email.')

# Setting up logging
logger = get_standard_logger('%s/MHLPractices/views.log' % (settings.LOGGING_ROOT),
							'MHLPractices.views', settings.LOGGING_LEVEL)


def practice_main_view(request):
	"""Displays office manager/staff home page."""

	if (not 'OfficeStaff' in request.session['MHL_UserIDs']):
		return err403(request)
		#print "%s %s is an Office_Manager"%(request.user.first_name, request.user.last_name)

	context = get_context(request)
	providerDict = dict()
	siteStaffDict = dict()
	local_practicesDict = dict()
	comm_professionalsDict = dict()
	practice_membersDict = dict()

	context['recent_sent_box'] = box_recent_sent(request)

	office_staff = request.session['MHL_Users']['OfficeStaff']
	current_practice = office_staff.current_practice
	context['zip'] = office_staff.user.zip

	if current_practice:
		context['mdcom_phone'] = phone_formater(current_practice.mdcom_phone)
		#list of practice for this location:
		practice_list = get_practices_by_position(current_practice.practice_lat, 
			current_practice.practice_longit).only('practice_name', 'id')
		local_practicesDict['providers'] = set_practices_result(practice_list, request)

		#list of providers for this practice:
		practice_members = all_practice_members(current_practice.id, 
			strip_staff_mobile=False, strip_staff_pager=False)
		practice_membersDict['providers'] = set_practice_members_result(practice_members, request)

	else:
		context['mdcom_phone'] = '(none)'
		#list of practice for this location:
		local_practicesDict['providers'] = []
		#list of providers for this practice:
		practice_membersDict['providers'] = []

	current_site = office_staff.current_site
	if (current_site != None):
		#context['site_providers'] = get_all_site_providers(office_staff.current_site.id)
#		providerDict['providers'] = get_all_site_providers(office_staff.current_site.id)

		providers = get_all_site_providers(office_staff.current_site.id)
		set_providers_result(providers, request) 
		providerDict['providers'] = providers
		site_staffs = get_all_site_staff(office_staff.current_site.id)
		siteStaffDict['users'] = set_site_staff_result(site_staffs, office_staff)

		#context['current_site_short_name'] = office_staff.current_site.short_name
		if current_site.short_name:
			providerDict['current_site'] = current_site.short_name
		else:
			providerDict['current_site'] = current_site.name
	else:
		providerDict['current_site'] = _("Hospital Site")

	comm_professionals = get_community_professionals(current_practice)	
	set_providers_result(comm_professionals, request) 
	#raise Exception ('practice_providers', context)
	comm_professionalsDict['providers'] = comm_professionals
	#does this manager have business cell phone?
	#context['business_cell'] = office_staff.user.mobile_phone
#	local_practicesDict['business_cell'] = office_staff.user.mobile_phone
	#does this practice have pending incoming requests for joining practice, 
	#get all managers for this practice

	# refer to ticket #1292, make the search condition same with staff page.
#	practice_staff = OfficeStaff.objects.filter(current_practice=current_practice).values('user')
	practice_staff = OfficeStaff.objects.filter().values('user')
#	#get all pending to ANY manager from this practice
#	#raise Exception(current_practice,OfficeManagers) 
	pend_assoc = Pending_Association.objects.filter(practice_location=current_practice, 
		to_user__in=practice_staff).filter(~Q(from_user__in=practice_staff)).count()

	context['receive_request_count'] = pend_assoc

	context['auto_refresh_time'] = settings.MSGLIST_AUTOREFRESH_TIME

	context['practice_members'] = render_to_string('userInfo3.html', practice_membersDict)
	context['site_provider'] = render_to_string('userInfo.html', providerDict)
	context['site_staff'] = render_to_string('userInfo4.html', siteStaffDict)
	context['comm_professionals'] = render_to_string('userInfo.html', comm_professionalsDict)
	context['local_practices'] = render_to_string('userInfo2.html', local_practicesDict)

	mhluser = request.session['MHL_Users']['MHLUser']
	orgs = getOrganizationsOfUser(mhluser, current_practice=current_practice)
	providerDict['org'] = orgs

	context['orgOroviders'] = renderOrganizationForDashbord(orgs, request)
	context['my_favorite'] = get_my_favorite(mhluser, html=True)

	providerDict["current_organization_type"] = get_org_type_name(current_practice, none_text="")
	if Office_Manager.objects.filter(user=office_staff, practice=current_practice).exists():
		context['caller_anssvc'] = office_staff.get_caller_anssvc_display()
		context['mobile_phone'] = phone_formater(office_staff.user.mobile_phone)
		context['office_phone'] = phone_formater(office_staff.office_phone)
		context['other_phone'] = phone_formater(office_staff.user.phone)

		#add by xlin 20100208 for html code refacting
		providerDict['userType'] = 1

		context['tabUI'] = render_to_string('tabUI.html', providerDict)
		return render_to_response('dashboard_office_manager.html', context)

	providerDict['userType'] = 2
	context['tabUI'] = render_to_string('tabUI.html', providerDict)
	return render_to_response('dashboard_office_staff.html', context)


def practice_profile_view(request):

	# Permissions checks. We need to check to see if this user is a manager
	# for this office.
	if (not 'OfficeStaff' in request.session['MHL_UserIDs']):
		return err403(request)
	user = request.session['MHL_Users']['MHLUser']
	office_staff = request.session['MHL_Users']['OfficeStaff']
	office_mgr = Office_Manager.objects.filter(user=office_staff,
				practice=office_staff.current_practice)
	if (not office_mgr.exists()):
		return err403(request)

	context = get_context(request)

	#is this office manager super manager or not
	context['manager_role'] = office_mgr[0].manager_role

	#until, we convert all practices to have accounts, only show links to 
	#practices that actually have billing account
	if (office_mgr[0].manager_role == 2):
		try:
			account = Account.objects.get(practice_group_new=office_mgr[0].practice.get_parent_org())
		except ObjectDoesNotExist:
			context['manager_role'] = 1
	#only for practice with group set set up and if this is super manager show manage CC link
	context['show_cc'] = office_mgr[0].manager_role
	if (office_mgr[0].manager_role == 2):
		practice_group = office_mgr[0].practice.get_parent_org()
		if  (practice_group is None):
			context['show_cc'] = 1

	# get the office location info
	context['office_name'] = office_staff.current_practice.practice_name
	context['office_address1'] = office_staff.current_practice.practice_address1
	context['office_address2'] = office_staff.current_practice.practice_address2
	context['office_city'] = office_staff.current_practice.practice_city
	context['office_state'] = office_staff.current_practice.practice_state
	context['office_zip'] = office_staff.current_practice.practice_zip
	context['office_time_zone'] = getDisplayedTimeZone(office_staff.current_practice.time_zone)
	context['office_phone'] = phone_formater(office_staff.current_practice.practice_phone)
	context['backline_phone'] = phone_formater(office_staff.current_practice.backline_phone)

	context['office_logo'] = ImageHelper.DEFAULT_PICTURE['Practice']
	if office_staff.current_practice:
		context['office_logo'] = ImageHelper.get_image_by_type(
			office_staff.current_practice.practice_photo, size='Middle', 
				type='Practice', resize_type='img_size_practice')

	#now we need to get office hours

	practiceHoursList = PracticeHours.objects.filter(
		practice_location=office_staff.current_practice.id)
	result = []
	for p in practiceHoursList:
		obj = {}
		obj['open'] = hour_format(user, p.open)
		obj['close'] = hour_format(user, p.close)
		obj['lunch_start'] = hour_format(user, p.lunch_start)
		obj['lunch_duration'] = p.lunch_duration
		obj['day_of_week'] = p.day_of_week
		result.append(obj)

	context['hours'] = result

	practiceHolidayList = PracticeHolidays.objects.filter(
		practice_location=office_staff.current_practice.id)
	context['holidays'] = practiceHolidayList

	return render_to_response('Profile/practice_profile_view.html', context)


def practice_profile_edit(request):
	"""
	Practice profile edit page.
	"""
	# Permissions checks. We need to check to see if this user is a manager
	# for this office.
	if (not 'OfficeStaff' in request.session['MHL_UserIDs']):
		return err403(request)
	office_staff = request.session['MHL_Users']['OfficeStaff']
	office_mgr = Office_Manager.objects.filter(user=office_staff,
				practice=office_staff.current_practice)
	if (not office_mgr.exists()):
		return err403(request)

	context = get_context(request)
	if (request.method == 'POST'):
		old_url = None
		if office_staff.current_practice.practice_photo:
			old_url = office_staff.current_practice.practice_photo.name
		form = PracticeProfileForm(request.POST, request.FILES,
					instance=office_staff.current_practice)

		if (form.is_valid()):
			practice = form.save(commit=False)
			practice.practice_lat = form.cleaned_data['practice_lat']
			practice.practice_longit = form.cleaned_data['practice_longit']
			practice.save()
			update_staff_address_info_by_practice(practice)
			new_url = None
			if office_staff.current_practice.practice_photo:
				new_url = practice.practice_photo.name
			if old_url != new_url:
				ImageHelper.generate_image(old_url, new_url, 'img_size_practice')
			if not form.non_field_warnings:
				return HttpResponseRedirect(reverse(practice_profile_view))
	else:
		practice = office_staff.current_practice
		try:
			if practice.time_zone:
				practice.time_zone = OLD_TIME_ZONES_MIGRATION[practice.time_zone]
		except Exception as e:
			logger.critical("FIXME: Unexpected bug: %s" % str(e))

		form = PracticeProfileForm(instance=practice)

	context['form'] = form
	return render_to_response('Profile/practice_profile_edit.html', context)


def practice_manage_hours(request):
	if ('Office_Manager' in request.session['MHL_UserIDs']):
		context = get_context(request)
	else:
		raise Exception(_('Only Office Managers can view Office profile'))

	# we need office staff model - to get office information, but only
	# office manager can change that info
	office_staff = request.session['MHL_Users']['OfficeStaff']	

	if (not office_staff):
		raise Exception(_('This user is NOT office staff'))
	#practiceHoursList = PracticeHours.objects.filter(
			#practice_location=office_staff.current_practice.id)

	practiceLocationId = office_staff.current_practice.id		

	hours = []
	if (request.method == 'POST'):
		commit = True
		remove = []
		update = []
		for i in range(7):
			hoursdict = {'open': minute_format(request.POST.getlist('open')[i]),
				'close': minute_format(request.POST.getlist('close')[i]),
				'lunch_start': minute_format(request.POST.getlist('lunch_start')[i]),
				'lunch_duration': request.POST.getlist('lunch_duration')[i],
				'day_of_week': DAYSNAMES[i][0]}

			try:
				instance = PracticeHours.objects.get(
					practice_location=office_staff.current_practice, day_of_week=DAYSNAMES[i][0])
			except ObjectDoesNotExist:
				instance = None
			except MultipleObjectsReturned:
				# FIXME
				# Multiple hours for day.
				#print 'FIXME: multiple hours for day %i' %(i+1)
				raise Exception(''.join([_('Multiple PracticeHours results found for practice '),
										str(office_staff.current_practice), _(' and weekday '),
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
			return HttpResponseRedirect(reverse('MHLogin.MHLPractices.views.practice_profile_view'))

	else:
		hours_qs = PracticeHours.objects.filter(practice_location=practiceLocationId)

		for (id, day) in DAYSNAMES:
			try:
				hours.append({'day': day,
					'form': HoursForm(instance=hours_qs.get(day_of_week=id))})
			except ObjectDoesNotExist:
				hours.append({'day': day, 'form': HoursForm()})
	context['hourslist'] = hours
	#context['errors'] = forms # ? forms not declared
	context['office_name'] = office_staff.current_practice.practice_name
	context['office_time_zone'] = office_staff.current_practice.time_zone

	return render_to_response('Profile/practice_manage_hours.html', context)


def practice_edit_holidays(request, holidayid):
	if ('Office_Manager' in request.session['MHL_UserIDs']):
		context = get_context(request)
	else:
		raise Exception(_('Only Office Managers can view Office profile'))

	#we need office staff model - to get office information, but only office manager can change that info
	office_staff = request.session['MHL_Users']['OfficeStaff']	

	if (not office_staff):
		raise Exception(_('This user is NOT office staff'))

	practiceLocationId = office_staff.current_practice.id

	#a PracticeHolidays object with id=0 should never exist, it's used by
	#the template create a new object
	if (holidayid == '0'):
		holiday = None
	else:
		try:
			holiday = PracticeHolidays.objects.get(id=holidayid,
				practice_location=practiceLocationId)
		except ObjectDoesNotExist:
			return err403(request)

	if(request.method == 'POST'):
		form = HolidaysForm(request.POST, instance=holiday)
		if (form.is_valid()):
			try:
				PracticeHolidays.objects.get(~Q(id=holidayid), 
					practice_location=practiceLocationId, 
						designated_day=form.cleaned_data['designated_day'])
				form._errors['designated_day'] = [_("a holiday already exists on that day")]
			except ObjectDoesNotExist:
				newholiday = form.save(commit=False)
				newholiday.practice_location = PracticeLocation.objects.get(id=practiceLocationId)
				newholiday.save()
				return HttpResponseRedirect(reverse('MHLogin.MHLPractices.views.practice_manage_holidays'))
	else:
		form = HolidaysForm(instance=holiday)

	context['form'] = form
	return render_to_response("Profile/practice_edit_holidays.html", context)


def practice_manage_holidays(request):
	if ('Office_Manager' in request.session['MHL_UserIDs']):
		context = get_context(request)
	else:
		raise Exception('Only Office Managers can view Office profile')

	# we need office staff model - to get office information,
	# but only office manager can change that info
	office_staff = request.session['MHL_Users']['OfficeStaff']	

	if (not office_staff):
		raise Exception(_('This user is NOT office staff'))

	#practiceLocationId = office_staff.current_practice.id
	practiceHolidayList = PracticeHolidays.objects.filter(
		practice_location=office_staff.current_practice.id)

	if(request.method == 'POST'):
		choices = [(holiday.id, holiday.id) for holiday in practiceHolidayList]
		removeform = RemoveForm(request.POST, choices)
		if (removeform.is_valid()):
			ids = removeform.cleaned_data['remove']
			PracticeHolidays.objects.filter(id__in=ids, 
				practice_location=office_staff.current_practice.id).delete()

	context['holidays'] = practiceHolidayList
	return render_to_response('Profile/practice_manage_holidays.html', context)


#series of functions to handle stuff association with practice
def staffHome(request):
	context = get_context(request)
	if ('Office_Manager' in request.session['MHL_UserIDs']):
		#print "%s %s is an Office_Manager"%(request.user.first_name, request.user.last_name)
		#context = get_context(request)
		practice = context['current_practice']
		context['org_type_name_request'] = ' '.join([\
				get_org_type_name(practice), _('Requests')])

		context['can_have_any_staff'] = practice.can_have_any_staff()
		context['can_have_any_provider'] = practice.can_have_any_provider()
		context["selected_organization_type"] = get_org_type_name(practice)

		#todo when using template tech. render html, refactor following code
		form = UserTypeSelecterForm(current_practice=practice)
		context["user_type_form"] = form

		request.session['SELECTED_ORG_ID'] = practice.id
	else:
		raise Exception(_('Only Office Managers can view Office profile'))

	#context['outstandingInvites'] = Invitation.objects.filter(sender=request.user).all()
	return render_to_response('Staff/staffHome.html', context)


#add by xlin in 20120328 to add new method for issue557
#update by xlin 20120702 to keep same with register
def newProvider(request):
	context = get_context(request)
	office_staff = request.session['MHL_Users']['OfficeStaff']
	current_practice = office_staff.current_practice
	request.session['SELECTED_ORG_ID'] = current_practice.id
	showDialog = 0
	username = ""
	if request.method == 'POST':
		provider_form = CreateProviderForm(data=request.POST, current_practice=current_practice)
		if provider_form.is_valid():
			# todo, using function createNewProvider in /mdcom/MHLogin/MHLUsers/utils_users.py
			username = provider_form.cleaned_data['username']
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
			provider.save()

			provider.practices.add(current_practice)
			provider.user_id = provider.pk
			provider.save()

			user_type = provider_form.cleaned_data['user_type']

			if '1' == user_type:
				#Physician
				ph = Physician(user=provider)
				ph.save()
			elif '2' == user_type:
				#NP/PA/Midwife
				np = NP_PA(user=provider)
				np.save()
			elif '10' == user_type:
				ph = Physician(user=provider)
				ph.save()

			# TESTING_KMS_INTEGRATION
			create_default_keys(provider.user)

			# Generating the user's voicemail box configuration
			config = VMBox_Config(pin='')
			config.owner = provider
			config.save()

			sendAccountActiveCode(request, user_type)

			showDialog = 1
		else:
			context['showDialog'] = showDialog
			context['user_form'] = provider_form
			return render_to_response('Staff/newProvider.html', context)

	context['username'] = username
	context['showDialog'] = showDialog
	context['user_form'] = CreateProviderForm(current_practice=current_practice)
	return render_to_response('Staff/newProvider.html', context)


#add by xlin in 20120329
def newStaff(request):
	context = get_context(request)
	office_staff = request.session['MHL_Users']['OfficeStaff']
	current_practice = office_staff.current_practice
	request.session['SELECTED_ORG_ID'] = current_practice.id
	showDialog = 0
	username = ""
	if request.method == 'POST':
		staff_form = CreateOfficeStaffForm(request.POST, \
				current_practice=current_practice, include_manager=False)
		mhluser_form = CreateMHLUserForm(request.POST, request.FILES)

		if staff_form.is_valid() and mhluser_form.is_valid():
			# todo, using function createNewOfficeStaff in /mdcom/MHLogin/MHLUsers/utils_users.py
			# createNewOfficeStaff(mhluser_form, staff_form, office_staff)
			username = mhluser_form.cleaned_data['username']
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

			staff_type = staff_form.cleaned_data['staff_type']

			if '3' == staff_type:
				nurse = Nurse(user=staff)
				nurse.save()
			elif '4' == staff_type:
				dietician = Dietician(user=staff)
				dietician.save()

			sendAccountActiveCode(request, 101)

			showDialog = 1
			#return HttpResponseRedirect(reverse('MHLogin.MHLPractices.views.staffHome'))
		else:
			context['showDialog'] = showDialog
			context['user_form'] = mhluser_form
			context['staff_form'] = staff_form
			return render_to_response('Staff/newStaff.html', context)
	context['username'] = username
	context['showDialog'] = showDialog
	context['user_form'] = CreateMHLUserForm()
	context['staff_form'] = CreateOfficeStaffForm(current_practice=current_practice,
					include_manager=False)

	return render_to_response('Staff/newStaff.html', context)


#add by xlin in 20120418 for issue671 TODO
#modify by xiln in 20120425 for active accuont according signup module
def active_account(request):
	context = get_context(request)
	context['err'] = ''
	if request.method == 'POST':
		active_form = ActiveAccountForm(data=request.POST)
		if active_form.is_valid():
			password1 = active_form.cleaned_data["password1"]
			code = active_form.cleaned_data['activeCode']
			email = active_form.cleaned_data['email']
			acclog, user, valid_code = checkActiveCode(code, email)
			if valid_code:
				if user.is_active == 1:
					return render_to_response("Staff/sucessActive.html", context)
				else:
					user.set_password(password1)
					#user.is_active = 1
					user.save()
					acclog.delete()

					mhuser = MHLUser.objects.get(pk=user.pk)
					#add by xlin 20120629 to set email confirm
					mhuser.email_confirmed = True
					mhuser.tos_accepted = True
					mhuser.save()

					if acclog.userType == 1 or acclog.userType == 2 or acclog.userType == 10:  # provider
						provider = Provider.objects.filter(mhluser_ptr=user.pk)[0]
						prac = PracticeLocation.objects.filter(
							practice_name=acclog.practice.practice_name)[0]
						#ONLY if practice set up before V2 of answering service
						if (prac.uses_original_answering_serice()):
							cm = CallGroupMember(call_group=prac.call_group,
										member=provider, alt_provider=1)
							cm.save()
					else:  # staff TODO
						pass

					if acclog.userType in (1, 2, 10, 300) and settings.CALL_ENABLE:
						request.session['userID'] = user.pk
						return HttpResponseRedirect(reverse(getDoctorNumber))
					else:
						user.is_active = 1
						user.save()
						request.session.clear()
						return render_to_response("Staff/sucessActive.html", context)
			else:
				context['err'] = MSG_ACTIVE_OR_EMAIL_WRONG
				context['active_form'] = active_form
				return render_to_response("Staff/activeAccount.html", context)
		else:
			context['active_form'] = active_form
			return render_to_response("Staff/activeAccount.html", context)
	else:
		active_form = ActiveAccountForm(initial=request.GET)
		activeCode = active_form.cleaned_data['activeCode']
		email = active_form.cleaned_data['email']
		acclog, user, valid_code = checkActiveCode(activeCode, email)

		if valid_code:
			if user.is_active == 1:
				return render_to_response("Staff/sucessActive.html", context)
			if acclog.userType in (1, 2, 10, 300) and settings.CALL_ENABLE:
				context['getNumber'] = True
		else:
			if user and user.is_active == 1:
				return render_to_response("Staff/sucessActive.html", context)
			context['err'] = MSG_ACTIVE_OR_EMAIL_WRONG
		context['active_form'] = active_form
		return render_to_response("Staff/activeAccount.html", context)	


def checkActiveCode(code, email):
	acclog = AccountActiveCode.objects.filter(code=code, recipient=email)
	user = User.objects.filter(email=email)
	if acclog:
		acclog = acclog[0]
	if user:
		user = user[0]
	return (acclog, user, bool(acclog) and bool(user))


#add by xlin 20120718
def getDoctorNumber(request):
	context = get_context(request)
	uid = request.session['userID']
	if request.method == 'POST':
		provider = Provider.objects.get(user__id=uid)
		form = LocalNumberForm(request.POST)
		if form.is_valid():
			pin = request.POST['pin']

			# LocalNumberForm, area_code, pin, mdcom_phone, mdcom_phone_sid
			mdcom_phone = form.mdcom_phone
			mdcom_phone_sid = form.mdcom_phone_sid

			provider.mdcom_phone = mdcom_phone
			provider.mdcom_phone_sid = mdcom_phone_sid

			#add doctorcom number
			if settings.CALL_ENABLE:
				user_type = ContentType.objects.get_for_model(provider)
				config = VMBox_Config.objects.get(owner_type=user_type, owner_id=provider.id)
				#config.change_pin(request, new_pin=pin)
				config.set_pin(pin)
				config.save()
				twilio_ConfigureProviderLocalNumber(provider, provider.mdcom_phone)
				request.session['userId'] = provider.id
				request.session['pin'] = pin

			provider.is_active = 1
			provider.save()
			return HttpResponseRedirect(reverse(getDoctorNumberSucess))
		context['form'] = form
	else:
		form = LocalNumberForm()
	context['form'] = form
	return render_to_response("Staff/get_doctor_number.html", context)


#add by xlin in 20120419 to active page success
def sucessActive(request):
	context = get_context(request)
	return render_to_response("Staff/sucessActive.html", context)


def getDoctorNumberSucess(request):
	context = get_context(request)
	userid = request.session.get('userId')
	context['pin'] = request.session.get('pin')
	code = Provider.objects.filter(id=userid)[0].mdcom_phone
	code = '(' + code[:3] + ') ' + code[3:6] + '-' + code[6:]
	context['area_code'] = code
	return render_to_response("Staff/sucessActive2.html", context)


def anssvc_caller(request):
	context = get_context(request)
	if (request.POST):
		staff = get_object_or_404(OfficeStaff, user=request.user)
		form = CallerAnssvcForm(request.POST)
		if(form.is_valid()):
			staff.caller_anssvc = form.cleaned_data['forward']
			staff.save()
	return HttpResponse(json.dumps({'fwd_setting': staff.get_caller_anssvc_display()}), 
					mimetype='application/json')


def practice_edit_access_numbers(request):
	context = get_context(request)
	context['isClearData'] = 0
	if('Office_Manager' not in request.session['MHL_UserIDs']):
		raise Exception(_('Only Office Managers can edit practice access numbers'))
	staff = request.session['MHL_Users']['OfficeStaff']
	practice = staff.current_practice
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
			removeform = RemoveForm(request.POST, choices=[(n.id, n.id)
							for n in context['access_numbers']])
			if(removeform.is_valid()):
				ids = removeform.cleaned_data['remove']
				AccessNumber.objects.filter(practice=practice, id__in=ids).delete()
	else:
		addform = AccessNumberForm()
	context['addform'] = addform
	context['access_numbers'] = practice.accessnumber_set.all()
	return render_to_response("Profile/practice_edit_access.html", context)


#update by xlin 121224 to add practice logo TODO
def getPenddings(request):
	pend_assoc = Pending_Association.objects.filter(to_user=request.user).order_by('created_time')
	assoc_lst = [{'practice_location':e.practice_location, 
		'from_user':e.from_user, 'associa_id':e.pk} for e in pend_assoc]

	pend_list = []
	for e in assoc_lst:
		p = {}
		p['user'] = e['from_user'].first_name + ' ' + e['from_user'].last_name
		p['practice_name'] = e['practice_location'].practice_name
		p['type'] = 'provider'
		p['practice_addr1'] = e['practice_location'].practice_address1
		p['practice_addr2'] = e['practice_location'].practice_address2
		p['practice_zip'] = e['practice_location'].practice_zip
		p['pract_id'] = e['practice_location'].pk
		p['assoc_id'] = e['associa_id']
		p['city'] = e['practice_location'].practice_city
		p['state'] = e['practice_location'].practice_state
		p['org_type'] = get_org_type_name(e['practice_location'])
		addr_list = [p['practice_addr1'], p['practice_addr2'], p['city'], p['state']]
		addr_list = [l for l in addr_list if l]
		p['addr'] = ', '.join(addr_list)
		p['practice_photo'] = ''

		if e['practice_location'].practice_photo:
			p['practice_photo'] = ImageHelper.get_image_by_type(
				e['practice_location'].practice_photo, size='Large', type='Practice', 
					resize_type='img_size_practice')
			p['logo_width'] = ImageHelper.get_image_width(
				e['practice_location'].practice_photo, size='Large', type='Practice')
			p['logo_height'] = ImageHelper.get_image_height(
				e['practice_location'].practice_photo, size='Large', type='Practice')
		pend_list.append(p)
	return HttpResponse(json.dumps(pend_list), mimetype='application/json')


# TODO: remove this, use sendAccountActiveCode in MHLogin.MHLUsers/utils_users
def sendAccountActiveCode(request, userType):
	office_staff = request.session['MHL_Users']['OfficeStaff']
	current_practice = office_staff.current_practice
	username = request.POST['username']
	recipient_email = request.POST['email']

	code = getNewCreateCode(username)
	log = AccountActiveCode(code=code,
		sender=request.session['MHL_UserIDs']['MHLUser'],
		recipient=recipient_email,
		#userType=int(request.POST['staff_type']),
		userType=userType,
		practice=current_practice)
	log.save()

	emailContext = dict()
	emailContext['username'] = username
	emailContext['code'] = code
	emailContext['email'] = recipient_email
	emailContext['name'] = request.POST['first_name'] + ' ' + request.POST['last_name']
	emailContext['sender'] = office_staff
	emailContext['address'] = settings.SERVER_ADDRESS
	emailContext['protocol'] = settings.SERVER_PROTOCOL
	msgBody = render_to_string('Staff/emailText.html', emailContext)
	send_mail('DoctorCom Activation', msgBody,
			settings.SERVER_EMAIL, [recipient_email], fail_silently=False)
