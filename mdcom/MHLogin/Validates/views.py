from django.forms.models import model_to_dict
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.utils.translation import ugettext as _
import json

from MHLogin.MHLUsers.models import MHLUser, Provider, OfficeStaff, Broker
from MHLogin.MHLUsers.utils import has_mhluser_with_email, has_mhluser_with_mobile_phone, getCurrentUserInfo
from MHLogin.Validates.forms import ValidateForm, SendCodeForm, ContactInfoForm
from MHLogin.Validates.utils import checkSendCodeEnable, sendCodeLogic, validateLogic
from MHLogin.utils import errlib
from MHLogin.utils.templates import get_context

ValidateConfigs = {
	"1": {
		"desc": "Email"
	},
	"2": {
		"desc": "Mobile"
	},
	"3": {
		"desc": "Pager"
	},
}

def validationPage(request):
	if (request.method == 'POST'):
		# Reserved. Process special case: pager is blank.
		if not "pager" in request.POST or not request.POST["pager"]:
			if ('Provider' in request.session['MHL_Users']):
				Provider.objects.filter(id=request.user.id).update(pager_confirmed=False, pager='')
			elif ('OfficeStaff' in request.session['MHL_Users']):
				OfficeStaff.objects.filter(user__id=request.user.id).update(pager_confirmed=False, pager='')
			elif ('Broker' in request.session['MHL_Users']):
				Broker.objects.filter(user__id=request.user.id).update(pager_confirmed=False, pager='')
		if not "mobile_phone" in request.POST or not request.POST["mobile_phone"]:
			MHLUser.objects.filter(id=request.user.id).update(mobile_confirmed=False, mobile_phone='')
		return HttpResponseRedirect('/')

	user = getCurrentUserInfo(request)
	mhluser = request.session['MHL_Users']['MHLUser']
	context = get_context(request)
	if not user or not user.needValidateContactInfo:
		return HttpResponseRedirect('/')
	context["form"] = ContactInfoForm(mhluser, user)

	context["mobile_required"] = 'Provider' in request.session['MHL_Users'] or \
											'Broker' in request.session['MHL_Users']

	return render_to_response('Validates/validation.html', context)

def contactInfo(request):
	fields = ('email', 'email_confirmed', 
				'mobile_phone', 'mobile_confirmed', 
				'pager', 'pager_confirmed')

	email = "email" in request.GET and request.GET["email"] or None
	mobile_phone = "mobile_phone" in request.GET and request.GET["mobile_phone"] or None
	pager = "pager" in request.GET and request.GET["pager"] or None

	retDict = dict()
	if ('Provider' in request.session['MHL_Users']):
		user = Provider.objects.get(id=request.user.id)
		retDict = model_to_dict(user, fields = fields)

	elif ('OfficeStaff' in request.session['MHL_Users']):
		staff = OfficeStaff.objects.get(user=request.user.id)
		user = staff.user
		retDict = model_to_dict(user, fields = fields)
		retDict.update(model_to_dict(staff, fields = fields))

	elif ('Broker' in request.session['MHL_Users']):
		broker = Broker.objects.get(user=request.user.id)
		user = broker.user
		retDict = model_to_dict(user, fields = fields)
		retDict.update(model_to_dict(broker, fields = fields))

	else:
		raise Exception('User is of unknown type')

	extends = {
		'email_send_enable': checkSendCodeEnable("1", request.user.id, email),
		'mobile_phone_send_enable': checkSendCodeEnable("2", request.user.id, mobile_phone),
		'pager_send_enable': checkSendCodeEnable("3", request.user.id, pager)
	}
	retDict.update(extends)

	if email:
		retDict["email_unique"] = not has_mhluser_with_email(email, request.user.id)
	else:
		retDict["email_unique"] = True

	if mobile_phone:
		retDict["mobile_phone_unique"] = not has_mhluser_with_mobile_phone(mobile_phone, request.user.id)
	else:
		retDict["mobile_phone_unique"] = True

	return HttpResponse(content=json.dumps({'user': retDict}), mimetype='application/json')

def sendCode(request):
	if (request.method == 'POST'):
		form = SendCodeForm(request.POST)
		if (form.is_valid()):
			ret_json = sendCodeLogic(form, request.user, request)
			if "error_code" in ret_json and ret_json["error_code"] == 403:
				return errlib.err403(request)
			return HttpResponse(content=json.dumps(ret_json), mimetype='application/json')

def validate(request):
	if (request.method == 'POST'):
		form = ValidateForm(request.POST)
		user_type = None
		if ('Provider' in request.session['MHL_Users']):
			user_type = 1
		elif ('OfficeStaff' in request.session['MHL_Users']):
			user_type = 101
		elif ('Broker' in request.session['MHL_Users']):
			user_type = 300
		ret_json = validateLogic(form, request.user, user_type)
		return HttpResponse(content=json.dumps(ret_json), mimetype='application/json')
