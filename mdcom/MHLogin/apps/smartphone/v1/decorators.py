
import json
from functools import wraps

from django.conf import settings
from django.http import HttpResponseBadRequest
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.utils.translation import ugettext as _

from forms import DeviceIDForm
from MHLogin.apps.smartphone.models import SmartPhoneAssn
from MHLogin.utils.constants import USER_TYPE_OFFICE_MANAGER,\
	USER_TYPE_OFFICE_STAFF, USER_TYPE_DOCTOR
from MHLogin.apps.smartphone.v1.utils import setSystemInfoToResponse
from MHLogin.utils.timeFormat import getCurrentTimeZoneForUser
from MHLogin.utils import ImageHelper
from MHLogin.MHLUsers.models import OfficeStaff, Provider, Nurse
from MHLogin.MHLOrganization.utils import get_prefer_logo
from MHLogin.MHLUsers.utils import get_fullname

APP_PATH_PREFIX = '/app/smartphone/v1/'
VALIDATE_MOBILE_EXCLUDE_PATH = [
	APP_PATH_PREFIX + "Device/Check_In/",
	APP_PATH_PREFIX + "Device/UpdatePushToken/",
	APP_PATH_PREFIX + "Device/Dissociate/",
	APP_PATH_PREFIX + "Account/GetKey/",
	APP_PATH_PREFIX + "Validations/SendCode/",
	APP_PATH_PREFIX + "Validations/Validate/"
]


def AppAuthentication(func, *args, **kwargs):
	"""
	Used as a decorator for smartphone app view functions
	"""
	@wraps(func)
	def f(request, *args, **kwargs):
		# We need to allow for DCOM_DEVICE_ID as a POST argument if the DEBUG
		# flag is True.
		device_id = None

		if (settings.APP_INTERFACE_DEBUG):
			if ('DCOM_DEVICE_ID' in request.REQUEST):
				device_id = _validate_device_id(request.REQUEST['DCOM_DEVICE_ID'])
				if (not device_id):
					err_obj = {
							'errno': 'GE004',
							'descr': _('Unrecognized DCOM_DEVICE_ID.'),
						}
					return HttpResponseBadRequest(content=json.dumps(err_obj), mimetype='application/json')
				request.META['HTTP_DCOM_DEVICE_ID'] = device_id

		# If we're not in a development environment, or if we *are* in a dev
		# environment, but the DCOM_DEVICE_ID wasn't included as POST data.
		#
		# Also, note that DCOM_DEVICE_ID has 'HTTP_' prepended to it by Django,
		# so we're looking for HTTP_DCOM_DEVICE_ID.
		if (not device_id):
			if (not 'HTTP_DCOM_DEVICE_ID' in request.META):
				err_obj = {
						'errno': 'GE001',
						'descr': _('HTTP request header DCOM_DEVICE_ID missing.'),
					}
				return HttpResponseBadRequest(content=json.dumps(err_obj), mimetype='application/json')
			device_id = _validate_device_id(request.META['HTTP_DCOM_DEVICE_ID'])
			if (not device_id):
				err_obj = {
						'errno': 'GE004',
						'descr': _('Unrecognized DCOM_DEVICE_ID.'),
					}
				return HttpResponseBadRequest(content=json.dumps(err_obj), mimetype='application/json')

		if (_get_session(request, device_id)):
			if (not request.device_assn.is_active):
				err_obj = {
						'errno': 'DM003',
						'descr': _('Your session has expired, please login again.'),
					}
				return HttpResponseBadRequest(content=json.dumps(err_obj), mimetype='application/json')
			if (_need_validate_mobile_phone(request)):
				mhluser = request.user
				err_obj = {
						'errno': 'GE005',
						'descr': _('Your mobile phone has not been validated.'),
						'data': {
								'mobile_phone': mhluser.mobile_phone,
								'mobile_confirmed': mhluser.mobile_confirmed
							}
					}
				return HttpResponseBadRequest(content=json.dumps(err_obj), mimetype='application/json')
			if (not request.user.has_perm('MHLUsers.access_smartphone')):
				err_obj = {
						'errno': 'DM005',
						'descr': _('Your mobile account is currently not authorized.'),
						'data': {
								'username': request.user.username,
							}
					}
				return HttpResponseBadRequest(content=json.dumps(err_obj), mimetype='application/json')

			resp = func(request, *args, **kwargs)
			return appendSettingInfoToResponse(request, resp)

		err_obj = {
				'errno': 'GE004',
				'descr': _('Unrecognized DCOM_DEVICE_ID.'),
			}
		return HttpResponseBadRequest(content=json.dumps(err_obj), mimetype='application/json')

	return f


def _validate_device_id(device_id):
	form = DeviceIDForm({'device_id': device_id}, auto_id=False)
	if (form.is_valid()):
		return form.cleaned_data['device_id']
	return False


def _get_session(request, device_id):
	try:
		assn = SmartPhoneAssn.all_objects.get(device_id=device_id)
	except (MultipleObjectsReturned, ObjectDoesNotExist):
		return False

	request.user = assn.user
	request.device_assn = assn
	request.session['key'] = assn.secret
	# about user_type please read USER_TYPE_CHOICES in MHLogin.utils.contants.py 
	request.user_type = int(assn.user_type)

	request.role_user = None
	if USER_TYPE_OFFICE_MANAGER == request.user_type or \
			USER_TYPE_OFFICE_STAFF == request.user_type:
		request.role_user = OfficeStaff.objects.get(user=request.user)
	else:
		request.role_user = Provider.objects.get(user=request.user)

	return True


def _need_validate_mobile_phone(request):
	mhluser = request.user
	path = request.path

	# office staff & office manager mobile phone can be null
	if not mhluser.mobile_phone or ('mobile_phone' in request.POST 
			and not request.POST['mobile_phone']):
		if request.user_type in [USER_TYPE_OFFICE_MANAGER, USER_TYPE_OFFICE_STAFF]:
			return False

	if settings.CALL_ENABLE and mhluser and mhluser.mobile_phone and not \
			mhluser.mobile_confirmed and path not in VALIDATE_MOBILE_EXCLUDE_PATH:
		return True

	return False


def appendSettingInfoToResponse(request, resp):
	if hasattr(resp, "content") and resp.content:
		try:
			response = json.loads(resp.content)
			response = setSystemInfoToResponse(response)
			settings_json = response["settings"]
			mhluser = request.user
			user_type = int(request.user_type)
			role_user = request.role_user
			if mhluser:
				settings_json['current_time_zone'] = getCurrentTimeZoneForUser(mhluser, role_user)
				settings_json['time_setting'] = mhluser.time_setting if mhluser.time_setting else 0

				default_picture_type = "Provider"
				if USER_TYPE_DOCTOR != user_type:
					default_picture_type = "Staff"
					if Nurse.objects.filter(user=role_user).exists():
						default_picture_type = "Nurse"
				settings_json['user_photo_m'] = ImageHelper.get_image_by_type(
					mhluser.photo, "Middle", default_picture_type)
				settings_json['real_name'] = get_fullname(mhluser)
				settings_json['prefer_logo'] = get_prefer_logo(mhluser.id)

			return resp.__class__(content=json.dumps(response), mimetype='application/json')
		except ValueError:
			pass
	return resp

