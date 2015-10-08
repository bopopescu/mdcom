import json
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest
from django.utils.translation import ugettext as _

from MHLogin.MHLUsers.utils import has_mhluser_with_mobile_phone
from MHLogin.Validates.forms import SendCodeForm, ValidateForm
from MHLogin.Validates.utils import sendCodeLogic, validateLogic
from MHLogin.apps.smartphone.v1.decorators import AppAuthentication
from MHLogin.apps.smartphone.v1.errlib import err_GE002, err_GE031, err_AM020
from MHLogin.utils import errlib


@AppAuthentication
def sendCode(request):
	if (request.method != 'POST'):
		return err_GE002()
	form = SendCodeForm(request.POST)
	if (not form.is_valid()):
		return err_GE031(form)

	# uniqueness check for mobile phone
	type = form.cleaned_data["type"]
	recipient = form.cleaned_data["recipient"]
	if "2" == type and has_mhluser_with_mobile_phone(recipient, request.user.id): 
		return err_AM020()

	request.session['key'] = request.device_assn.secret
	ret_json = sendCodeLogic(form, request.user, request)
	if "error_code" in ret_json:
		if ret_json["error_code"] == 403:
			return errlib.err403(request)
		elif ret_json["error_code"] == 404:
			err_obj = {
				'errno': 'VA001',
				'descr': _('The number is invalid, we can\'t send code to you. '
						'Please input a valid mobile phone number.'),
			}
			return HttpResponseBadRequest(content=json.dumps(err_obj), mimetype='application/json')

	ret_json["settings_send_code_waiting_time"] = settings.SEND_CODE_WAITING_TIME
	ret_json["settings_validate_lock_time"] = settings.VALIDATE_LOCK_TIME
	response = {
		'data': ret_json,
		'warnings': {},
	}

	return HttpResponse(content=json.dumps(response), mimetype='application/json')


@AppAuthentication
def validate(request):
	if (request.method != 'POST'):
		return err_GE002()
	form = ValidateForm(request.POST)
	if (not form.is_valid()):
		return err_GE031(form)

	user_type = request.user_type
	ret_json = validateLogic(form, request.user, user_type)
	ret_json["settings_validate_lock_time"] = settings.VALIDATE_LOCK_TIME

	response = {
		'data': ret_json,
		'warnings': {},
	}
	return HttpResponse(content=json.dumps(response), mimetype='application/json')
