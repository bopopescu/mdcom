import base64
import json
import logging
import os

from Crypto.Cipher import XOR
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db.models.query_utils import Q

from django.http import HttpResponse, HttpResponseBadRequest
from django.utils.translation import ugettext as _

from MHLogin.KMS.models import UserPrivateKey, CRED_WEBAPP
from MHLogin.KMS.utils import get_user_key, split_user_key, recrypt_keys
from MHLogin.MHLUsers.models import Provider, Office_Manager, OfficeStaff
from MHLogin.apps.smartphone.models import SmartPhoneAssn
from MHLogin.apps.smartphone.v1.errlib import err_GE002, err_GE022, err_GE031,\
		err_GE100, err_DM002, err_DM020, err_DM005
from MHLogin.apps.smartphone.v1.forms import PushTokenForm
from MHLogin.apps.smartphone.v1.forms_device import AssociationForm, CheckInForm, \
	CheckUserForm, VersionUpdateForm
from MHLogin.apps.smartphone.v1.utils_messaging import rx_message_list_data, tx_message_list_data
from MHLogin.apps.smartphone.v1.utils import setSystemInfoToResponse
from MHLogin.apps.smartphone.v1.decorators import AppAuthentication
from MHLogin.utils.mh_logging import get_standard_logger 
from MHLogin.MHLUsers.utils import staff_is_active
from MHLogin.utils.constants import USER_TYPE_DOCTOR, USER_TYPE_OFFICE_STAFF, USER_TYPE_OFFICE_MANAGER
from MHLogin.MHLOrganization.utils import get_prefer_logo

# Setting up logging
logger = get_standard_logger('%s/apps/smartphone/v1/views_device.log' % \
	(settings.LOGGING_ROOT), 'DCom.apps.smartphone.v1.views_device', logging.DEBUG)


def check_user(request):
	if (request.method == 'GET'):
		return err_GE002()
	form = CheckUserForm(request.POST)
	if (not form.is_valid()):
		return err_GE031(form)

	try:
		User.objects.get(username=form.cleaned_data['username'])
		response = {
			'data': {
				},
			'warnings': {},
		}
		return HttpResponse(content=json.dumps(response), mimetype='application/json')
	except User.DoesNotExist:
		err_obj = {
			'errno': 'PF001',
			'descr': _('User not found.'),
		}
		return HttpResponseBadRequest(content=json.dumps(err_obj), mimetype='application/json')


def associate(request):
	logger.debug(''.join([str(request.session.session_key), '-Request: ', str(request)]))
	if (request.method == 'GET'):
		logger.debug(''.join([str(request.session.session_key), '-Returning GE002!!!']))
		return err_GE002()
	form = AssociationForm(request.POST, auto_id=False)
	if (not form.is_valid()):
		return err_GE031(form)

	# Consider the compatibility, use the key: "allow_staff_login" -- it's optional,
	# distinguish different client version
	allow_staff_login = False
	if "allow_staff_login" in form.cleaned_data and form.cleaned_data["allow_staff_login"]:
		allow_staff_login = True

	user = authenticate(username=form.cleaned_data['username'],
				password=form.cleaned_data['password'])
	if (not user):
		err_obj = {
			'errno': 'DM001',
			'descr': _('Username or password incorrect.'),
		}
		return HttpResponseBadRequest(content=json.dumps(err_obj), mimetype='application/json')
	# TESTING_KMS_INTEGRATION check if user is g'fathered
	uprivs = UserPrivateKey.objects.filter(user=user, credtype=CRED_WEBAPP, gfather=True)
	if uprivs.exists():
		recrypt_keys(uprivs, settings.SECRET_KEY, form.cleaned_data['password'])

	if (not user.is_active):
		return err_DM002()

	# Okay, everything checks out. Now check that the user is a Provider or Practice Manager
	providers = Provider.objects.filter(user=user.id)
	staff = OfficeStaff.objects.filter(user__pk=user.id)

	mobile_phone = ''
	mdcom_number = ''
	utype = None
	if providers and len(providers) > 0:
		utype = USER_TYPE_DOCTOR
		mdcom_number = providers[0].mdcom_phone
		mobile_phone = providers[0].user.mobile_phone
	elif staff and len(staff) > 0:
		staff = staff[0]

		if not staff_is_active(staff):
			return err_DM002()

		if not staff.user.has_perm('MHLUsers.access_smartphone'):
			return err_DM005()

		utype = USER_TYPE_OFFICE_STAFF
		manager_practice = staff.current_practice
		if manager_practice:
			mdcom_number = manager_practice.mdcom_phone
		mobile_phone = staff.user.mobile_phone

		if Office_Manager.objects.filter(user=staff).exists():
			utype = USER_TYPE_OFFICE_MANAGER
		else:
			if not allow_staff_login:
				return err_DM020()
	else:
		return err_DM020()

	# When user login from app, clean some assn, such as:
	#	1. Other user's assn in the same app client.
	#	2. Same user's assn in other app client.
	#		But, one user can login one mobile device and one tablet at the same time.
	# Now, the platform is only three options iPhone, Android, iPad. 
	# If available platform options changed, please change the following logic.
	platform = form.cleaned_data['platform']
	old_assns = None
	if platform in ('iPhone', 'Android'):
		old_assns = SmartPhoneAssn.objects.filter(Q(device_serial=form.cleaned_data['device_id']) | 
			Q(user__pk=user.pk, platform__in=('iPhone', 'Android')))
	else:
		old_assns = SmartPhoneAssn.objects.filter(Q(device_serial=form.cleaned_data['device_id']) | 
			Q(user__pk=user.pk, platform='iPad'))
	if (old_assns and old_assns.exists()):
		for old_assn in old_assns:
			old_assn.dissociate(request, True)

	# get/set up all necessary crypto values.
	password = form.cleaned_data['password']  # key strengthened below in different way
	local, remote = split_user_key(password)
	# NOTE: splitkey result reversed compared to web, but we should be
	# OK as long as whatever deemed remote is not stored server side.
	db_key = os.urandom(32)
	xor = XOR.new(base64.b64decode(remote))
	dbsplit = base64.b64encode(xor.encrypt(db_key))

	# Next, create the association object
	assn = SmartPhoneAssn(
			user_id=user.pk,
			device_serial=form.cleaned_data['device_id'],
			version=form.cleaned_data['app_version'],
			platform=platform,
			user_type=utype,
		)
	if ('name' in form.cleaned_data):
		assn.name = form.cleaned_data['name']
	assn.save(request)
	assn.update_secret(local, password)
	assn.update_db_secret(dbsplit, db_key)

	response = {
		'data': {
				'mdcom_id': assn.device_id,
				'secret': remote,
				'mdcom_number': mdcom_number,
				'mobile_phone': mobile_phone,
				'user_id': user.pk,
				# about the number of user_type, please read USER_TYPE_CHOICES 
				# in the MHLogin.utils.contants.py 
				'user_type': utype,
				'gcm_project_id': settings.GCM_PROJECT_ID,
				'call_available': settings.CALL_ENABLE and bool(mobile_phone)
			},
		'warnings': {},
	}

	setSystemInfoToResponse(response)
	response["settings"]['prefer_logo'] = get_prefer_logo(user.pk)
	return HttpResponse(content=json.dumps(response), mimetype='application/json')


@AppAuthentication
def dissociate(request):
	request.device_assn.dissociate(request, remote_request=True)

	response = {
		'data': {},
		'warnings': {},
	}
	return HttpResponse(content=json.dumps(response), mimetype='application/json')


@AppAuthentication
def check_in(request):
	if (request.method == 'GET'):
		return err_GE002()

	response = {
		'data': {},
		'warnings': {},
	}
	data = response['data']

	data['status'] = 'ok'
	if (not request.device_assn.is_active):
		data['status'] = 'wipe'
		return HttpResponse(content=json.dumps(response), mimetype='application/json')

	data['password_changed'] = request.device_assn.password_reset

	form = CheckInForm(request.POST, auto_id=False)
	if (not form.is_valid()):
		return err_GE031(form)

	if ('key' in request.POST):
		key = get_user_key(request, ss=form.cleaned_data['key'])
		if (not request.device_assn.verify_key(key)):
			return err_GE022()
		data['key'] = base64.b64encode(key)
	if ('rx_timestamp' in request.POST):
		data['received_messages'] = rx_message_list_data(request, 
						form.cleaned_data['rx_timestamp'], None, None, None)
	if ('tx_timestamp' in request.POST):
		data['sent_messages'] = tx_message_list_data(request, 
						form.cleaned_data['tx_timestamp'], None, None, None)

	return HttpResponse(content=json.dumps(response), mimetype='application/json')


@AppAuthentication
def re_key(request):
	return err_GE100()


@AppAuthentication
def app_version_update(request):
	if (request.method == 'GET'):
		return err_GE002()	
	form = VersionUpdateForm(request.POST, auto_id=False)
	if (not form.is_valid()):
		return err_GE031(form)

	request.device_assn.version = form.cleaned_data['app_version']
	request.device_assn.save(request)

	response = {
		'data': {},
		'warnings': {},
	}
	return HttpResponse(content=json.dumps(response), mimetype='application/json')


@AppAuthentication
def register_push_token(request):
	if(request.method == 'POST'):
		form = PushTokenForm(request.POST)
		if(form.is_valid()):
			#SmartPhoneAssn.objects.filter(user=request.user).\
			#	update(push_token=form.cleaned_data['token'])
			SmartPhoneAssn.objects.filter(pk=request.device_assn.pk).\
				update(push_token=form.cleaned_data['token'])
			response = {
				'data': {},
				'warnings': {},
			}
			return HttpResponse(content=json.dumps(response), mimetype='application/json')
		return err_GE031(form)
	return err_GE002()
