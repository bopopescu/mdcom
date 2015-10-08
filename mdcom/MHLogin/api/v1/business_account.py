# -*- coding: utf-8 -*-
'''
Created on 2012-10-08

@author: mwang
'''
import json

from django.http import HttpResponseBadRequest

from MHLogin.MHLUsers.models import MHLUser, Physician
from MHLogin.api.v1.errlib import err_GE031, err_DM020, _err_AM010, err_GE002, err_AM020
from MHLogin.api.v1.forms_account import SetPracticeForm, SetSiteForm, \
	GetFwdPrefsForm, UpdateMobileForm
from MHLogin.api.v1.utils_practices import getPracticeProviders, getPracticeStaff
from MHLogin.api.v1.utils_sites import getSiteStudents, getSiteProviders, getSiteStaff
from MHLogin.api.v1.utils import HttpJSONSuccessResponse
from MHLogin.MHLUsers.utils import has_mhluser_with_mobile_phone, change_pass_common, \
	get_managed_practice
from MHLogin.MHLUsers.forms import ChangePasswordForm, ProviderForm, \
	PhysicianForm, OfficeStaffForm, UserForm, BrokerForm, BrokerUserForm
from MHLogin.api.v1.utils_account import providerProfileView, officeStaffProfileView, \
	brokerProfileView
from MHLogin.utils import ImageHelper
from MHLogin.utils.constants import RESERVED_ORGANIZATION_TYPE_ID_PRACTICE, \
	USER_TYPE_OFFICE_MANAGER, USER_TYPE_OFFICE_STAFF
from MHLogin.utils.errlib import err403

def practiceManageLogic(request):
	user_type = int(request.user_type)
	role_user = request.role_user
	if (request.method != 'POST'):
		# Get the user's current practices, and list them.
		practices = role_user.practices.filter(\
				organization_type__id=RESERVED_ORGANIZATION_TYPE_ID_PRACTICE)
		if USER_TYPE_OFFICE_MANAGER == user_type:
			practices = get_managed_practice(role_user)

		practices = [[p.id, p.practice_name] for p in practices]
		current_practice = role_user.current_practice
		if ('pk' in dir(current_practice)):
			current_practice = current_practice.pk
			data = {
					'practices':practices,
					'current_practice':current_practice,
				}
		return HttpJSONSuccessResponse(data=data)

	# office staff can't change current practice
	if USER_TYPE_OFFICE_STAFF == user_type:
		return err403(request)

	form = SetPracticeForm(request.POST, user_type=user_type)
	if (not form.is_valid()):
		return err_GE031(form)
	
	new_practice = form.cleaned_data['current_practice']
	if (new_practice == None):
		# Clearing the current practice.
		role_user.current_practice = None
		role_user.save()
		data = {
				'providers': [],
				'staff': [],
			}
		return HttpJSONSuccessResponse(data=data)
	if (new_practice in role_user.practices.values_list('id', flat=True)):
		# great, do the change.
		role_user.current_practice_id = new_practice
		role_user.save()
		data = {
				'providers': getPracticeProviders(new_practice)['users'],
				'staff': getPracticeStaff(new_practice)['users'],
			}
		return HttpJSONSuccessResponse(data=data)
	
	err_obj = {
		'errno': 'AM001',
		'descr': _('Invalid practice selection.'),
	}
	return HttpResponseBadRequest(content=json.dumps(err_obj), mimetype='application/json')


def siteManageLogic(request):
	user = request.role_user
	if (request.method != 'POST'):
		# Get the user's current practices, and list them.
		sites = user.sites.values('id', 'name')
		sites = [[s['id'], s['name']] for s in sites]
		current_site = user.current_site
		if ('pk' in dir(current_site)):
			current_site = current_site.pk
			data = {
					'sites':sites,
					'current_site':current_site,
				}
		return HttpJSONSuccessResponse(data=data)
	
	form = SetSiteForm(request.POST)
	if (not form.is_valid()):
		return err_GE031(form)
	
	new_site = form.cleaned_data['current_site']
	if (new_site == None):
		# Clearing the current site.
		user.current_site = None
		user.save()
		data = {
				'providers': [],
				'staff': [],
				'med_students': [],
			}
		return HttpJSONSuccessResponse(data=data)
	if (new_site in user.sites.values_list('id', flat=True)):
		# great, do the change.
		user.current_site_id = new_site
		user.save()
		data = {
				'med_students': getSiteStudents(new_site)['users'],
				'providers': getSiteProviders(new_site)['users'],
				'staff': getSiteStaff(new_site)['users'],
			}
		return HttpJSONSuccessResponse(data=data)
	
	err_obj = {
		'errno': 'AM001',
		'descr': _('Invalid site selection.'),
	}
	return HttpResponseBadRequest(content=json.dumps(err_obj), mimetype='application/json')

def callFwdPrefsLogic(request):
	mhluser = request.mhluser
	role_user = request.role_user
	user_type = request.user_type
	if 100 == user_type:
		return err_DM020()

	if (request.method == 'GET'):
		choices = ['Voicemail']
		if (mhluser.mobile_phone):
			choices.append('Mobile')
		if (role_user.office_phone):
			choices.append('Office')
		if (mhluser.phone):
			choices.append('Other')
		
		data = {
				'choices': choices,
				'current': role_user.get_forward_voicemail_display()
			}
		return HttpJSONSuccessResponse(data=data)

	form = GetFwdPrefsForm(request.POST)
	if (not form.is_valid()):
		return err_GE031(form)

	choice = form.cleaned_data['forward']
	if (choice == 'Mobile'):
		if (not mhluser.mobile_phone):
			return _err_AM010()
		role_user.forward_voicemail = "MO"
	elif (choice == 'Office'):
		if (not role_user.office_phone):
			return _err_AM010()
		role_user.forward_voicemail = "OF"
	elif (choice == 'Other'):
		if (not mhluser.phone):
			return _err_AM010()
		role_user.forward_voicemail = "OT"
	else:
		role_user.forward_voicemail = "VM"

	role_user.save()
	return HttpJSONSuccessResponse()

def getDComNumberLogic(request):
	role_user = request.role_user
	user_type = request.user_type
	number = ''
	if 100 == user_type or 300 == user_type:
		manager_practice = role_user.current_practice
		if manager_practice:
			number = manager_practice.mdcom_phone
	else:
		number = role_user.mdcom_phone
	data = {"number":number}
	return HttpJSONSuccessResponse(data=data)

def getMobilePhoneLogic(request):
	mobile_phone = ''
	mobile_confirmed = ''
	mhluser = request.mhluser
	if mhluser:
		mobile_phone = mhluser.mobile_phone
		mobile_confirmed = mhluser.mobile_confirmed

		data = {
					'mobile_phone': mobile_phone,
					'mobile_confirmed': mobile_confirmed
				}
	return HttpJSONSuccessResponse(data=data)

def updateMobilePhoneLogic(request):
	if (request.method != 'POST'):
		return err_GE002()
	form = UpdateMobileForm(request.POST)
	if (not form.is_valid()):
		return err_GE031(form)
	mhluser_id = request.mhluser.id
	mobile_phone = form.cleaned_data["mobile_phone"]
	if has_mhluser_with_mobile_phone(mobile_phone, mhluser_id): 
		return err_AM020()

	MHLUser.objects.filter(id=mhluser_id).update(mobile_phone=mobile_phone)
	return HttpJSONSuccessResponse()

def changePasswordLogic(request):
	if (request.method != 'POST'):
		return err_GE002()
	form = ChangePasswordForm(request.mhluser, request.POST)
	if (not form.is_valid()):
		return err_GE031(form)
	change_pass_common(form, request)
	return HttpJSONSuccessResponse()

def profileLogic(request):
	user_type = request.user_type
	if 1 == user_type:
		return providerProfileLogic(request)
	elif 100 == user_type:
		return officeStaffProfileLogic(request)
	elif 300 == user_type:
		return brokerProfileLogic(request)
	else:
		return err_DM020()

def providerProfileLogic(request):
	if (request.method != 'POST'):
		return HttpJSONSuccessResponse(data=providerProfileView(request.role_user))
	else:
		return providerEditProfileLogic(request)

def officeStaffProfileLogic(request):
	if (request.method != 'POST'):
		return HttpJSONSuccessResponse(data=officeStaffProfileView(request.role_user))
	else:
		return officeStaffEditProfileLogic(request)

def brokerProfileLogic(request):
	if (request.method != 'POST'):
		return HttpJSONSuccessResponse(data=brokerProfileView(request.role_user))
	else:
		return brokerEditProfileLogic(request)

def providerEditProfileLogic(request):
	if (request.method != 'POST'):
		return err_GE002()
	provider = request.role_user
	phys = Physician.objects.filter(user=provider)
	if phys and len(phys):
		phys = phys[0]
	else:
		phys = None

	old_url = None
	if provider.photo:
		old_url = provider.photo.name
	provider_form = ProviderForm(data=request.POST, files=request.FILES, instance=provider)
	if (not provider_form.is_valid()):
		return err_GE031(provider_form)

	physician_form = None
	if (phys):
		physician_form = PhysicianForm(request.POST, instance=phys)
		if (not physician_form.is_valid()):
			return err_GE031(physician_form)
	
	provider = provider_form.save(commit=False)
	provider.lat = provider_form.cleaned_data['lat']
	provider.longit = provider_form.cleaned_data['longit']
	provider.licensure_states = provider_form.cleaned_data['licensure_states']
	#add by xlin in 20120611 for issue897 that add city, address, zip into database
	provider.address1 = provider_form.cleaned_data['address1']
	provider.address2 = provider_form.cleaned_data['address2']
	provider.city = provider_form.cleaned_data['city']
	provider.state = provider_form.cleaned_data['state']
	provider.zip = provider_form.cleaned_data['zip']
	provider.save()
	if (physician_form):
		physician_form.save()
	
	new_url = None
	if provider.photo:
		new_url = provider.photo.name
	
	#thumbnail creating code moved from here to save method of provider mode
	#use common method to generate
	ImageHelper.generate_image(old_url, new_url)

	return HttpJSONSuccessResponse()

def officeStaffEditProfileLogic(request):
	if (request.method != 'POST'):
		return err_GE002()

	staff = request.role_user
	old_url = None
	if staff.user.photo:
		old_url = staff.user.photo.name

	staff_form = OfficeStaffForm(request.POST, instance=staff)
	if not staff_form.is_valid():
		return err_GE031(staff_form)

	user_form = UserForm(request.POST, request.FILES, instance=staff.user)
	if not user_form.is_valid():
		return err_GE031(user_form)

	user_form.save(commit=False)
	staff_form.save()
	new_url = None
	if staff.user.photo:
		new_url = staff.user.photo.name
	ImageHelper.generate_image(old_url, new_url)
	return HttpJSONSuccessResponse()

def brokerEditProfileLogic(request):
	if (request.method != 'POST'):
		return err_GE002()

	old_url = None
	broker = request.role_user
	if broker.user.photo:
		old_url = broker.user.photo.name

	broker_form = BrokerForm(request.POST, instance=broker)
	if not broker_form.is_valid():
		return err_GE031(broker_form)

	user_form = BrokerUserForm(request.POST, request.FILES, instance=broker.user)
	if not user_form.is_valid():
		return err_GE031(user_form)

	broker_form.save()
	user_form.save()

	new_url = None
	if broker.user.photo:
		new_url = broker.user.photo.name
	ImageHelper.generate_image(old_url, new_url)

	return HttpJSONSuccessResponse()
