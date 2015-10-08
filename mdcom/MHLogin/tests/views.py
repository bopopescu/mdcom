
import json
from urlparse import urljoin

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render_to_response
from twilio import twiml as twilio
from twilio.rest.resources import make_twilio_request

from MHLogin.MHLUsers.decorators import RequireAdministrator
import MHLogin.utils.errlib as errlib
from MHLogin.utils.templates import get_context
from MHLogin.utils.decorators import TwilioAuthentication

from MHLogin.MHLUsers.models import MHLUser, Provider
from MHLogin.tests.models import TwilioCallGatherTest, TwilioRecordTest, \
					DoctorComC2CTest, DoctorComPagerTest, DoctorComSMSTest

from MHLogin.DoctorCom.views import click2call_initiate, page_execute
from MHLogin.utils.admin_utils import mail_admins
from MHLogin.utils.twilio_utils import client, validate_sid


test_types = {
	'1': 'DoctorCom C2C Test',
	'2': 'DoctorCom Pager Test',

	'10': 'Twilio Call & Gather Test',
}


@RequireAdministrator
def home(request):
	context = get_context(request)
	context['user_id'] = request.user.id
	return render_to_response("tests/home.html", context)


@RequireAdministrator
def confirm_test(request):
	context = get_context(request)
	success = 0

	if (request.POST['test_result'] == '1'):
		context['result'] = 'Success'
		context['success'] = 1
		success = 1
	else:
		context['result'] = 'Failure'
		context['success'] = 0

		# email admins
		mail_admins('Failed Test', ''.join([
						'Test harness failure ',
						test_types[request.POST['test_type']],
						', with ID ', request.POST['test_id']
					]))

	import re
	log_id = re.match('\d+', request.POST['test_id'])
	if (log_id == None):
		raise Exception("The log ID failed the regex check.")
	log_id = log_id.group(0)

	log = None

	# this isn't too efficient, but it works.
	if (request.POST['test_type'] == '1'):
		log = DoctorComC2CTest.objects.filter(id=log_id).get()
	elif (request.POST['test_type'] == '2'):
		log = DoctorComPagerTest.objects.filter(id=log_id).get()
	elif (request.POST['test_type'] == '10'):
		log = TwilioCallGatherTest.objects.filter(id=log_id).get()

	if (log == None):
		raise Exception("Failed to retrieve the log.")

	log.success = success
	log.save()

	context['admins'] = settings.ADMINS
	return render_to_response("tests/confirm_finish.html", context)


@RequireAdministrator
def DCom_C2C_test(request):
	log = DoctorComC2CTest()
	log.tester = MHLUser.objects.get(id=request.user.id)

	if (not log.tester.mobile_phone):
		return errlib.err500(request, err_msg="You need to have a mobile phone "
							"number in your profile to use this function.")
	log.save()

	c2cLog = click2call_initiate(request, test_flag=True, called_id=request.user.id)
	#c2cLog = None
	if (c2cLog.__class__.__name__ == 'HttpResponse'):
		# this is an error message from c2c_init
		return c2cLog

	log.call = c2cLog
	log.save()

	context = get_context(request)
	context['test_type'] = 1
	context['test_id'] = log.id
	context['form_action'] = reverse('MHLogin.tests.views.confirm_test',)
	return render_to_response("tests/confirm_test.html", context)


@RequireAdministrator
def DCom_Page_test(request):
	log = DoctorComPagerTest()
	log.tester = Provider.objects.get(id=request.user.id)

	if (not log.tester.pager):
		return errlib.err500(request, err_msg="You need to have a pager number "
					"in your profile to use this function.")
	if (not log.tester.mobile_phone):
		return errlib.err500(request, err_msg="You need to have a mobile phone "
					"number in your profile to use this function.")

	log.save()

	pageLog = page_execute(request, log.tester, log.tester, log.tester.mobile_phone, test_flag=True)
	#pageLog = None
	if (pageLog.__class__.__name__ == 'HttpResponse'):
		# this is an error message
		return pageLog

	log.call = pageLog
	log.save()

	context = get_context(request)
	context['test_type'] = 2
	context['test_id'] = log.id
	context['form_action'] = reverse('MHLogin.tests.views.confirm_test',)
	return render_to_response("tests/confirm_test.html", context)


@RequireAdministrator
def DCom_SMS_test(request):
	log = DoctorComSMSTest()
	log.tester = MHLUser.objects.get(id=request.user.id)

	if (not log.tester.mobile_phone):
		return errlib.err500(request, err_msg="You need to have a mobile phone number "
							"in your profile to use this function.")

	log.save()

#	FIXME:	
#	smsMsg = send_message('This is a DoctorCom SMS Test.', log.tester, log.tester)
	#c2cLog = None
#	if (smsMsg.__class__.__name__ == 'HttpResponse'):
#		# this is an error message from c2c_init
#		return c2cLog
#	
#	log.call = c2cLog
	log.save()

	context = get_context(request)
	context['test_type'] = 1
	context['test_id'] = log.id
	context['form_action'] = reverse('MHLogin.tests.views.confirm_test',)
	return render_to_response("tests/confirm_test.html", context)


@RequireAdministrator
def Twilio_callGather_initiate(request):
	abs_uri = '://'.join([settings.SERVER_PROTOCOL, settings.SERVER_ADDRESS])
	url = reverse('MHLogin.tests.views.Twilio_callGather')

	return Twilio_call_initiate(request, 1, urljoin(abs_uri, url))


@RequireAdministrator
def Twilio_record_initiate(request):
	abs_uri = '://'.join([settings.SERVER_PROTOCOL, settings.SERVER_ADDRESS])
	url = reverse('MHLogin.tests.views.Twilio_record')
	sid = Twilio_call_initiate(request, 2, urljoin(abs_uri, url))

	mail_admins('Test harness: New keypress recording', ''.join([
						'A new recording has been created with callSID ',
						sid
					]))

	context = get_context(request)
	context['sid'] = sid
	return render_to_response("tests/confirm_recording.html", context)


@RequireAdministrator
def Twilio_call_initiate(request, type, url):
	# type is the model type that we're going to use.
	# 		1: TwilioCallGatherTest
	#		2: TwilioRecordTest
	caller = MHLUser.objects.get(id=request.user.id)
	called = caller

	if (not caller.mobile_phone):
		return errlib.err500(request, err_msg="You do not have a mobile phone number "
							"in your profile. Please enter one to use this function.")
	if (not called.mobile_phone):
		return errlib.err500(request, err_msg="The person you are trying to call "
							"doesn't have a mobile phone number listed.")

	if (type == 1):
		log = TwilioCallGatherTest()
	elif (type == 2):
		log = TwilioRecordTest()
	log.tester = caller
	log.save()

	# TODO: When confirmation gets figured out, generate an appropriate error message here.
	if (not caller.mobile_confirmed):
		pass
	if (not called.mobile_confirmed):
		pass

	response_args = ''
	if (request.GET and request.GET.has_key()):
		response_args = '?record=True'

	d = {
		'Caller': settings.TWILIO_CALLER_ID,
		'Called': caller.mobile_phone,
		'Url': url,
		'Method': 'POST',
		'Timeout': 60,
	}
	auth, uri = client.auth, client.account_uri 
	call_info = make_twilio_request('POST', uri + '/Calls', auth=auth, data=d)
	sid = json.loads(call_info.content).get('sid', '')

	if not validate_sid(sid):
		# This only occurs if the call SID is invalid or has changed formats.
		return errlib.err500(request)

	log.callid = sid
	log.save()

	if (type == 2):
		return sid

	context = get_context(request)
	context['called'] = called
	context['test_type'] = 10
	context['test_id'] = log.id
	context['form_action'] = reverse('MHLogin.tests.views.confirm_test',)
	return render_to_response("tests/confirm_test.html", context)


@TwilioAuthentication()
def Twilio_callGather(request):
	import cPickle

	# Save debugging data
	sid = request.POST['CallSid']
	status = request.POST['CallStatus']

	log = TwilioCallGatherTest.objects.get(callid=sid)

	if (not log.debug_data):
		debugData = []
	else:
		debugData = cPickle.loads(log.debug_data.encode('ascii'))
	newEntry = ['Twilio_callGather', cPickle.dumps(request.POST)]
	debugData.append(newEntry)
	log.debug_data = cPickle.dumps(debugData)

	log.save()

	# We don't care about which session this is associated with as all
	# verification is the same across all sessions.
	r = twilio.Response()
	if (status != 'completed'):
		abs_uri = '://'.join([settings.SERVER_PROTOCOL, settings.SERVER_ADDRESS])
		url = reverse('MHLogin.tests.views.Twilio_callGather_complete')

		gather = twilio.Gather(action=urljoin(abs_uri, url),
					numDigits=1, finishOnKey='', timeout=10)
		gather.append(twilio.Say("Please press the number one.", 
					voice=twilio.Say.MAN, language=twilio.Say.ENGLISH))
		r.append(gather)

	log.success = log.success + '1'  # should be 11 or 101 here
	debugData.append(str(r))
	log.debug_data = cPickle.dumps(debugData)
	log.save()

	return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)


@TwilioAuthentication()
def Twilio_callGather_complete(request):
	import cPickle

	# Save debugging data
	sid = request.POST['CallSid']
	status = request.POST['CallStatus']
	key = request.POST['Digits']

	log = TwilioCallGatherTest.objects.get(callid=sid)

	debugData = cPickle.loads(log.debug_data.encode('ascii'))
	newEntry = ['Twilio_callGather_complete', cPickle.dumps(request.POST)]
	debugData.append(newEntry)
	log.debug_data = cPickle.dumps(debugData)

	log.save()

	# We don't care about which session this is associated with as all
	# verification is the same across all sessions.
	r = twilio.Response()
	if (key):
		say = twilio.Say("You pressed the %s key" % (key, ),
						voice=twilio.Say.MAN, language=twilio.Say.ENGLISH)
	else:
		say = twilio.Say("No key press was recorded.", 
						voice=twilio.Say.MAN, language=twilio.Say.ENGLISH)
	r.append(say)
	hangup = twilio.Hangup()
	r.append(hangup)

	log.success = log.success + '2'  # should be 11 or 101 here
	debugData.append(str(r))
	log.debug_data = cPickle.dumps(debugData)
	log.save()

	return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)


@TwilioAuthentication()
def Twilio_record(request):
	import cPickle

	# Save debugging data
	sid = request.POST['CallSid']
	status = request.POST['CallStatus']

	log = TwilioRecordTest.objects.get(callid=sid)

	if (not log.debug_data):
		debugData = []
	else:
		debugData = cPickle.loads(log.debug_data.encode('ascii'))
	newEntry = ['Twilio_record', cPickle.dumps(request.POST)]
	debugData.append(newEntry)
	log.debug_data = cPickle.dumps(debugData)

	log.save()

	# We don't care about which session this is associated with as all
	# verification is the same across all sessions.
	r = twilio.Response()
	say = twilio.Say("After the tone, please press 1, 2, and 3, then pound to finish.", 
			voice=twilio.Say.MAN, language=twilio.Say.ENGLISH)
	r.append(say)

	abs_uri = '://'.join([settings.SERVER_PROTOCOL, settings.SERVER_ADDRESS])
	url = reverse('MHLogin.tests.views.Twilio_record_complete')

	record = twilio.Record(
				action=urljoin(abs_uri, url),
				transcribe=False,
				finishOnKey='#',
				playBeep='true',
				timeout=30,
				)
	r.append(record)

	debugData.append(str(r))
	log.debug_data = cPickle.dumps(debugData)
	log.save()

	return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)


@TwilioAuthentication()
def Twilio_record_complete(request):
	import cPickle

	# Save debugging data
	sid = request.POST['CallSid']
	status = request.POST['CallStatus']

	log = TwilioCallGatherTest.objects.get(callid=sid)
	log.recordingurl = request.POST['RecordingUrl']

	debugData = cPickle.loads(log.debug_data.encode('ascii'))
	newEntry = ['Twilio_record_complete', cPickle.dumps(request.POST)]
	debugData.append(newEntry)
	log.debug_data = cPickle.dumps(debugData)

	log.save()

	# We don't care about which session this is associated with as all
	# verification is the same across all sessions.
	r = twilio.Response()
	say = twilio.Say("Thank you. Goodbye.", voice=twilio.Say.MAN, language=twilio.Say.ENGLISH)
	r.append(say)
	hangup = twilio.Hangup()
	r.append(hangup)

	debugData.append(str(r))
	log.debug_data = cPickle.dumps(debugData)
	log.save()

	return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)

