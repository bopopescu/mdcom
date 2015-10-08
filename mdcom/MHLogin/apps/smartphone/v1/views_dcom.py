
import json
from datetime import datetime, timedelta
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest
from django.utils.translation import ugettext as _
from twilio import twiml as twilio
from twilio.util import TwilioCapability

from MHLogin.DoctorCom.IVR.views_provider import ProviderIVR_OutsideInit, ProviderIVR_ForwardCall
from MHLogin.DoctorCom.Messaging.models import Message, MessageBodyUserStatus, CallbackLog
from MHLogin.DoctorCom.models import Click2Call_Log
from MHLogin.DoctorCom.speech.utils import tts
from MHLogin.DoctorCom.views import send_page
from MHLogin.MHLPractices.models import PracticeLocation
from MHLogin.MHLUsers.models import Provider, OfficeStaff, MHLUser, Office_Manager
from MHLogin.MHLUsers.utils import user_is_provider
from MHLogin.apps.smartphone.v1.decorators import AppAuthentication
from MHLogin.apps.smartphone.v1.errlib import err_GE002, err_GE010, err_GE031, \
	err_TE005, err_TE006
from MHLogin.apps.smartphone.v1.forms_dcom import USNumberForm, \
	PagerNumberForm, TwiMLCallbackForm
from MHLogin.utils.decorators import TwilioAuthentication


@AppAuthentication
def call(request, *args, **kwargs):
	if (not request.user.mobile_phone):
		return err_TE005()
	called_number = ''
	mhluser = None
	form = USNumberForm(request.POST)
	if(not form.is_valid()):
		return err_GE031(form)

	if('user_id' in kwargs):
		user_id = kwargs['user_id']
		mhluser = MHLUser.objects.filter(pk=user_id)
		if (not mhluser):
			return err_GE010()

		mhluser = mhluser[0]

		if (not mhluser.mobile_phone):
			return err_TE005()
		called_number = mhluser.mobile_phone
	if('practice_id' in kwargs):
		practice_id = kwargs['practice_id']
		called_practice = PracticeLocation.objects.filter(id=practice_id)
		if not called_practice:
			return err_GE010()

		called_number = called_practice[0].practice_phone
		if called_practice[0].backline_phone:
			called_number = called_practice[0].backline_phone

		if (not called_number):
			return err_TE006()
	elif('number' in request.POST):
		called_number = form.cleaned_data['number']
	elif('number' in kwargs):
		called_number = kwargs['number']
	log = Click2Call_Log()
	log.caller = request.user
	log.called_user = mhluser
	log.called_number = called_number
	log.caller_number = form.cleaned_data['caller_number']
	p = request.role_user
	log.current_site = p.current_site if p else None
	log.source = 'APP'
	log.save()

	response = {
		'data': {
			'number': ''.join(['+1', str(settings.TWILIO_C2C_NUMBER)])},
		'warnings': {},
	}

	return HttpResponse(content=json.dumps(response), mimetype='application/json')


@AppAuthentication
def message_callback(request, message_id):
	try:
		msg = Message.objects.get(uuid=message_id)
		mbus = MessageBodyUserStatus.objects.get(user=request.user.pk, msg_body__message=msg)
		CallbackLog(message=msg).save()

		return call(request, number=msg.callback_number)
	except Message.DoesNotExist, MessageBodyUserStatus.DoesNotExist:
		response = HttpResponse("")
		response.status_code = 404  # ich, __init__ won't accept status_code in its kwargs
		return response


@TwilioAuthentication()
def connect_call(request):
	sid = request.POST['CallSid']
	caller = request.POST['Caller']
	r = twilio.Response()
	log = Click2Call_Log.objects.filter(caller_number=caller, 
			timestamp__gt=datetime.now() - timedelta(minutes=3)).order_by('-timestamp')[:1]
	log = log[0] if len(log) else None

	if not log or log.connected:
		r.append(tts(_("Sorry, this number is a DoctorCOM public number. Please "
					"call back the Answering Service.")))
		return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)
	log.sid = sid
	log.connected = True
	log.save()

	provider_qs = Provider.objects.filter(mobile_phone=log.called_number)
	if provider_qs:
		provider = provider_qs.get()
		ProviderIVR_OutsideInit(request, log.caller_number, provider, log)
		return ProviderIVR_ForwardCall(request)

	# for privacy reasons caller id always our c2c number
	caller_id = settings.TWILIO_C2C_NUMBER 

	dial = twilio.Dial(log.called_number,
				action='',
				callerId=caller_id,
				timeout=120)
	r.append(dial)
	return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)


@AppAuthentication
def page_user(request, user_id):
	if (request.method != 'POST'):
		return err_GE002()
	form = PagerNumberForm(request.POST)
	if (not form.is_valid()):
		return err_GE031(form)

	if (not MHLUser.objects.filter(pk=user_id).exists()):
		return err_GE010()

	provider = None
	try:
		provider = Provider.objects.get(user=user_id)
	except Provider.DoesNotExist:
		# This is ok.
		pass

	office_staff = None
	try:
		office_staff = OfficeStaff.objects.get(user=user_id)
	except OfficeStaff.DoesNotExist:
		# this is okay.
		pass

	paged = None  # The user getting paged.
	if (provider):
		paged = provider
		if (not provider.pager):
			err_obj = {
				'errno': 'TE002',
				'descr': _('Requested user doesn\'t have a pager.'),
			}
			return HttpResponseBadRequest(content=json.dumps(err_obj), 
						mimetype='application/json')
	elif (office_staff):
		paged = office_staff
		if (not office_staff.pager):
			err_obj = {
				'errno': 'TE002',
				'descr': _('Requested user doesn\'t have a pager.'),
			}
			return HttpResponseBadRequest(content=json.dumps(err_obj), 
					mimetype='application/json')
	else:
		# Error! User doesn't appear to be a provider or an office staffer.
		return err_GE010()

	send_page(request.user, paged, form.cleaned_data['number'])

	response = {
		'data': {},
		'warnings': {},
	}
	return HttpResponse(content=json.dumps(response), mimetype='application/json')


@AppAuthentication
def capability_token(request):
	mhluser_id = request.user.id
	capability = TwilioCapability(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_ACCOUNT_TOKEN)
	capability.allow_client_outgoing(settings.TWILIO_APP_SID)
	capabilityToken = capability.generate()
	response = {
		'data': {
			'capabilityToken': capabilityToken,
			'mhluser_id': mhluser_id
			},
		'warnings': {},
	}
	print json.dumps(response)
	return HttpResponse(content=json.dumps(response), mimetype='application/json')


@TwilioAuthentication()
def twiMLCall_callback(request):
	form = TwiMLCallbackForm(request.POST)
	r = twilio.Response()
	if (not form.is_valid()):
		r.append(tts(_("A system error has occurred. "
			"Please contact the administrator or try it later.")))
		return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)

	callSid = form.cleaned_data["CallSid"]
	caller_user_id = form.cleaned_data["caller_user_id"]
	called_number = form.cleaned_data["called_number"]
	called_user_id = form.cleaned_data["called_user_id"]
	called_practice_id = form.cleaned_data["called_practice_id"]

	# decide called number or called user.
	called_user = None
	if called_user_id:
		called_users = MHLUser.objects.filter(pk=called_user_id)
		if (not called_users):
			r.append(tts(_("The person you called doesn't exist.")))
			return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)
		called_user = called_users[0]
		called_number = called_user.mobile_phone
	elif called_practice_id:
		called_practice = PracticeLocation.objects.filter(id=called_practice_id)
		if not called_practice:
			r.append(tts(_("The practice you called doesn't exist.")))
			return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)
		called_number = called_practice[0].practice_phone

	# decide which number is caller_number.
	caller_mhluser = MHLUser.objects.get(pk=caller_user_id)
	caller_provider = user_is_provider(caller_mhluser)

	caller_manager = None
	caller_mgrs = Office_Manager.objects.filter(user__user=caller_mhluser)
	if caller_mgrs:
		caller_manager = caller_mgrs[0]

	caller_number = caller_mhluser.mobile_phone
	if not caller_provider and caller_manager:
		staffs = OfficeStaff.objects.filter(user=caller_mhluser)
		if (staffs.count() != 1):
			pass
#
		staff = staffs[0]
		if staff.caller_anssvc == 'MO':
			caller_number = staff.user.mobile_phone
		elif staff.caller_anssvc == 'OF':
			caller_number = staff.office_phone
		elif staff.caller_anssvc == 'OT':
			caller_number = staff.user.phone
		else:
			pass

	log = Click2Call_Log(
			caller=caller_mhluser,
			caller_number=caller_number,
			callid=callSid,
			called_number=called_number,
			called_user=called_user,
			source='APP'
		)
	log.save()

	# decide which number is caller_id.
	caller_id = settings.TWILIO_CALLER_ID
	if (caller_provider and caller_provider.mdcom_phone):
		caller_id = caller_provider.mdcom_phone
	else:
		if caller_manager:
			if caller_manager and caller_manager.user.current_practice and \
					caller_manager.user.current_practice.mdcom_phone:
				caller_id = caller_manager.user.current_practice.mdcom_phone

	# check called person/number, decide call process
	if called_user:
		called_provider = user_is_provider(called_user)
		if (not called_provider):
			#office managers can get phone calls too, but they must have mobile phone
			manager_info = OfficeStaff.objects.filter(user=called_user)
			if (manager_info.count() > 0 and manager_info[0].user.mobile_phone):
				called_manager = manager_info[0]

		if(called_provider):
			# Send the call through the IVR
			ProviderIVR_OutsideInit(request, log.caller_number, called_provider, log)
			request.session['Caller'] = caller_id
			return ProviderIVR_ForwardCall(request)
		elif called_manager:
			# Send the call through the IVR
			from MHLogin.DoctorCom.IVR.views_practice import \
				PracticeIVR_ForwardCall, PracticeIVR_OutsideInit
			PracticeIVR_OutsideInit(request, log.caller_number, called_manager, log)
			request.session['click2call'] = True
			request.session['Caller'] = caller_id
			return PracticeIVR_ForwardCall(request)

	dial = twilio.Dial(called_number,
				callerId=caller_id,
				timeout=120)
	r.append(dial)
	return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)


