import json
import base64
import thread
from Crypto.Cipher import XOR

from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest
from django.utils.translation import ugettext as _

from MHLogin.MHLUsers.models import MHLUser, Provider
from MHLogin.MHLUsers.utils import has_mhluser_with_mobile_phone, get_managed_practice
from MHLogin.apps.smartphone.models import SmartPhoneAssn
from MHLogin.apps.smartphone.v1.decorators import AppAuthentication
from MHLogin.apps.smartphone.v1.errlib import err_GE002, err_GE022, err_GE031, err_DM020, err_AM020
from MHLogin.apps.smartphone.v1.forms_account import GetKeyForm, SetPracticeForm, SetSiteForm, GetFwdPrefsForm, UpdateMobileForm,\
	CallForwardForm, PreferenceForm
from MHLogin.apps.smartphone.v1.views_users import practice_providers, practice_staff
from MHLogin.apps.smartphone.v1.views_users import site_providers, site_staff, site_students
from MHLogin.utils.errlib import err403
from MHLogin.utils.constants import USER_TYPE_OFFICE_MANAGER, USER_TYPE_OFFICE_STAFF, USER_TYPE_DOCTOR,\
	TIME_ZONES_CHOICES, RESERVED_ORGANIZATION_TYPE_ID_PRACTICE
from MHLogin.utils.timeFormat import getCurrentTimeZoneForUser, getCurrentPracticeTimeZone
from MHLogin.apps.smartphone.v1.utils import notify_user_tab_changed

@AppAuthentication
def get_key(request):
	if (request.method != 'POST'):
		return err_GE002()
	form = GetKeyForm(request.POST)
	if (not form.is_valid()):
		return err_GE031(form)
	
	#dbkey = get_user_key(request, ss=form.cleaned_data['secret'])
	db_secret = request.device_assn.db_secret
	xor = XOR.new(base64.b64decode(form.cleaned_data['secret']))
	db_key = xor.encrypt(base64.b64decode(db_secret))
	
	if (not request.device_assn.verify_db_key(db_key)):
		return err_GE022()
	
	# Okay, we need to test the validity of this key before we return it.
	# Otherwise, we could return an invalid key.

	response = {
			'data': {
					'key':base64.b64encode(db_key),
#					'gcm_project_id': settings.GCM_PROJECT_ID
				},
			'warnings':{}
		}
	return HttpResponse(content=json.dumps(response), mimetype='application/json')


@AppAuthentication
def practice_mgmt(request):
	user_type = int(request.user_type)
	role_user = request.role_user
	if (request.method != 'POST'):
		# Get the user's current practices, and list them.
		practices = role_user.practices.filter(organization_type__id = RESERVED_ORGANIZATION_TYPE_ID_PRACTICE)
		if USER_TYPE_OFFICE_MANAGER == user_type:
			practices = get_managed_practice(role_user)

		practices = [[p.id, p.practice_name] for p in practices]
		current_practice = role_user.current_practice
		if ('pk' in dir(current_practice)):
			current_practice = current_practice.pk
		response = {
					'data': {
							'practices':practices,
							'current_practice':current_practice,
						},
					'warnings': {},
				}
		return HttpResponse(content=json.dumps(response), mimetype='application/json')

	# office staff can't change current practice
	if USER_TYPE_OFFICE_STAFF == user_type:
		return err403(request)

	form = SetPracticeForm(request.POST, user_type=user_type)
	if (not form.is_valid()):
		return err_GE031(form)
	
	new_practice = form.cleaned_data['current_practice']
	response = {
			'data': {
				},
			'warnings':{}
		}
	res_data = response['data']
	old_cur_prac = role_user.current_practice
	if (new_practice == None):
		# Clearing the current practice.
		role_user.current_practice = None
		role_user.save()
		res_data = {
			'providers': [],
			'staff': [],
		}
	elif (new_practice in role_user.practices.values_list('id', flat=True)):
		# great, do the change.
		role_user.current_practice_id = new_practice
		role_user.save()
		res_data = {
			'providers': practice_providers(request, 
					return_python=True)['data']['users'],
			'staff': practice_staff(request, 
					return_python=True)['data']['users'],
		}

	if (old_cur_prac is None and new_practice is not None) \
		or (old_cur_prac is not None and not old_cur_prac.id == new_practice):
		# send notification to related users
		thread.start_new_thread(notify_user_tab_changed, (request.user.id,))
	return HttpResponse(content=json.dumps(response), mimetype='application/json')

	err_obj = {
		'errno': 'AM001',
		'descr': _('Invalid practice selection.'),
	}
	return HttpResponseBadRequest(content=json.dumps(err_obj), mimetype='application/json')


@AppAuthentication
def site_mgmt(request):
	role_user = request.role_user
	user_type = request.user_type
	if (request.method != 'POST'):
		# Get the user's current practices, and list them.
		sites = role_user.sites.values('id', 'name')
		sites = [[s['id'], s['name']] for s in sites]
		current_site = role_user.current_site
		if ('pk' in dir(current_site)):
			current_site = current_site.pk
		response = {
					'data': {
							'sites':sites,
							'current_site':current_site,
						},
					'warnings': {},
				}
		return HttpResponse(content=json.dumps(response), mimetype='application/json')
	
	form = SetSiteForm(request.POST)
	if (not form.is_valid()):
		return err_GE031(form)
	
	new_site = form.cleaned_data['current_site']
	if (new_site == None):
		# Clearing the current site.
		role_user.current_site = None
		role_user.save()
		
		response = {
				'data': {
						'providers': [],
						'staff': [],
						'med_students': [],
					},
				'warnings':{},
			}
		return HttpResponse(content=json.dumps(response), mimetype='application/json')
	if (new_site in role_user.sites.values_list('id', flat=True)):
		# great, do the change.
		role_user.current_site_id = new_site
		role_user.save()
		
		response = {
				'data': {
						'providers': site_providers(request, 
								return_python=True)['data']['users'],
						'staff': site_staff(request, 
								return_python=True)['data']['users'],
						'med_students': site_students(request, 
								return_python=True)['data']['users'] if USER_TYPE_DOCTOR == user_type else [],
					},
				'warnings':{}
			}
		return HttpResponse(content=json.dumps(response), mimetype='application/json')
	
	err_obj = {
		'errno': 'AM001',
		'descr': _('Invalid site selection.'),
	}
	return HttpResponseBadRequest(content=json.dumps(err_obj), mimetype='application/json')


@AppAuthentication
def call_fwd_prefs(request):
	role_user = request.role_user
	user_type = int(request.user_type)
	if not USER_TYPE_DOCTOR == user_type:
		return err_DM020()
	
	response = {
			'data': {},
			'warnings': {},
		}
	if (request.method == 'GET'):
		choices = response['data']['choices'] = ['Voicemail']
		if (request.user.mobile_phone):
			choices.append('Mobile')
		if (role_user.office_phone):
			choices.append('Office')
		if (request.user.phone):
			choices.append('Other')
		
		response['data']['current'] = role_user.get_forward_voicemail_display()
		return HttpResponse(content=json.dumps(response), mimetype='application/json')

	form = GetFwdPrefsForm(request.POST)
	if (not form.is_valid()):
		return err_GE031(form)

	choice = form.cleaned_data['forward']
	if (choice == 'Mobile'):
		if (not role_user.user.mobile_phone):
			return _err_AM010()
		role_user.forward_voicemail = "MO"
	elif (choice == 'Office'):
		if (not role_user.office_phone):
			return _err_AM010()
		role_user.forward_voicemail = "OF"
	elif (choice == 'Other'):
		if (not role_user.user.phone):
			return _err_AM010()
		role_user.forward_voicemail = "OT"
	else:
		role_user.forward_voicemail = "VM"

	role_user.save()
	return HttpResponse(content=json.dumps(response), mimetype='application/json')

def _err_AM010():
	err_obj = {
		'errno': 'AM010',
		'descr': _('Invalid forwarding selection.'),
	}
	return HttpResponseBadRequest(content=json.dumps(err_obj), mimetype='application/json')

@AppAuthentication
def get_dcom_number(request):
	role_user = request.role_user
	user_type = int(request.user_type)
	number = ''
	if USER_TYPE_OFFICE_MANAGER == user_type or USER_TYPE_OFFICE_STAFF == user_type:
		current_practice = role_user.current_practice
		if current_practice:
			number = current_practice.mdcom_phone
	else:
		number = role_user.mdcom_phone
	response = {
			'data': {"number":number},
			'warnings': {},
		}
	
	return HttpResponse(content=json.dumps(response), mimetype='application/json')

@AppAuthentication
def get_mobile_phone(request):
	mobile_phone = ''
	mobile_confirmed = ''
	mhluser = MHLUser.objects.filter(pk=request.user.id)
	if mhluser and len(mhluser) > 0:
		mobile_phone = mhluser[0].mobile_phone
		mobile_confirmed = mhluser[0].mobile_confirmed

	response = {
			'data': {
						'mobile_phone': mobile_phone,
						'mobile_confirmed': mobile_confirmed
					},
			'warnings': {},
		}
	
	return HttpResponse(content=json.dumps(response), mimetype='application/json')

@AppAuthentication
def update_mobile_phone(request):
	if (request.method != 'POST'):
		return err_GE002()
	user_type = int(request.user_type)
	form = UpdateMobileForm(request.POST, user_type=user_type)
	if (not form.is_valid()):
		return err_GE031(form)

	mobile_phone = form.cleaned_data["mobile_phone"]
	# If CALL_ENABLE = True, and mobile_phone is not empty,
	# this function can't be accessed directly.
	# If CALL_ENABLE = True, mobile phone must be stored after validation.
	if (settings.CALL_ENABLE and mobile_phone):
		return err403(request)

	# If the mobile_phone number is used by others, return error.
	if mobile_phone and has_mhluser_with_mobile_phone(mobile_phone, request.user.id): 
		return err_AM020()

	if mobile_phone:
		MHLUser.objects.filter(id=request.user.id).update(mobile_phone=mobile_phone)
	else:
		if user_type not in [USER_TYPE_OFFICE_MANAGER, USER_TYPE_OFFICE_STAFF]:
			return err403(request)
		MHLUser.objects.filter(id=request.user.id).update(mobile_phone='', mobile_confirmed=False)

	response = {
			'data': {},
			'warnings': {},
		}
	
	return HttpResponse(content=json.dumps(response), mimetype='application/json')

@AppAuthentication
def anssvc_forwarding(request):
	role_user = request.role_user
	user_type = int(request.user_type)

	if not USER_TYPE_DOCTOR == user_type:
		return err_DM020()

	response = {
			'data': {},
			'warnings': {},
		}
	if (request.method == 'GET'):
		choices = response['data']['choices'] = ['Voicemail']
		if (request.user.mobile_phone):
			choices.append('Mobile')
		if (role_user.office_phone):
			choices.append('Office')
		if (request.user.phone):
			choices.append('Other')

		response['data']['current'] = role_user.get_forward_anssvc_display()
		return HttpResponse(content=json.dumps(response), mimetype='application/json')

	form = CallForwardForm(request.POST)
	if (not form.is_valid()):
		return err_GE031(form)
	choice = form.cleaned_data['forward']
	role_user.forward_anssvc = getForwardChoicesKeyByValue(choice)
	role_user.save()
	return HttpResponse(content=json.dumps(response), mimetype='application/json')

@AppAuthentication
def preference(request):
	mhluser = request.user
	role_user = request.role_user
	if (request.method == 'GET'):
		response = {
			'data': {
				'time_setting': mhluser.time_setting if mhluser.time_setting else 0,
				'user_time_zone': mhluser.time_zone if mhluser.time_zone else "",
				'practice_time_zone': getCurrentPracticeTimeZone(role_user),
				'time_zone_options': (("", "(None)"),)+TIME_ZONES_CHOICES,
			},
			'warnings': {},
		}
		return HttpResponse(content=json.dumps(response), mimetype='application/json')

	form = PreferenceForm(request.POST)
	if (not form.is_valid()):
		return err_GE031(form)
	time_setting = form.cleaned_data['time_setting']
	time_zone = form.cleaned_data['time_zone']

	mhluser.time_setting=time_setting
	mhluser.time_zone=time_zone
	mhluser.save()

	response = {
		'data': {
		},
		'warnings': {},
	}
	return HttpResponse(content=json.dumps(response), mimetype='application/json')

def getForwardChoicesKeyByValue(value):
	forward_choices = {
		'MO': 'Mobile',
		'OF': 'Office',
		'OT': 'Other',
		'VM': 'Voicemail',
	}

	for key,val in forward_choices.iteritems():
		if val == value:
			return key
