
import re

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.contrib.auth import login, authenticate
from django.utils.importlib import import_module
from twilio import twiml as twilio

from models import VMBox_Config
from models import get_new_pin_hash, check_pin, callEvent, callEventTarget, callLog

from MHLogin.utils.errlib import err404
from MHLogin.MHLUsers.models import Provider
from MHLogin.utils.decorators import TwilioAuthentication
from MHLogin.utils.mh_logging import get_standard_logger
from MHLogin.MHLPractices.models import PracticeLocation
from MHLogin.DoctorCom.Messaging.models import MessageAttachment, CallbackLog
from MHLogin.DoctorCom.speech.utils import tts
from MHLogin.KMS.utils import store_user_key, get_user_key
from MHLogin.KMS.models import UserPrivateKey, CRED_IVRPIN
from MHLogin.utils.admin_utils import mail_admins

from django.utils.translation import ugettext as _

# Setting up logging
logger = get_standard_logger('%s/DoctorCom/IVR/views_generic.log' % (settings.LOGGING_ROOT),
							'DCom.IVR.views_generic', settings.LOGGING_LEVEL)

# NOTE
# DEPRECATED - most of the calls here are being deprecated (except for getRecording).
# any changes should be replicated to views_generic_v2.py version
# NOTE


@TwilioAuthentication()
def UnaffiliatedNumber(request):
	r = twilio.Response()
	r.append(twilio.Pause())  # one second pause keeps the first words from getting cut off.
	r.append(tts(_("You have called an inactive phone number affiliated with "
				"doctorcom. Please visit us online at w w w dot m d com dot com. Good bye.")))
	r.append(twilio.Hangup())
	return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)


@TwilioAuthentication()
def changePin(request, twilioResponse=None, internalCall=False):
	"""This function gets called three times per successful PIN change. The first
	time, it requests the user's pin. The second time, it requests
	confirmation of the pin. The last time, it finally saves the pin, then

	:returns: to the function specified at request.session['ivr_call_stack'][-1]
	"""
	r = twilioResponse or twilio.Response() 

	if (not internalCall and 'Digits' in request.POST):
		digits = request.POST['Digits']
		if (not 'ivr_changePin_hash' in request.session):
			# This is the first time the PIN has been entered.
			p = re.compile('\d{4,8}#?$')
			if (not p.match(digits)):
				r.append(tts(_("An in valid pin was entered.")))
			else:
				request.session['ivr_changePin_hash'] = get_new_pin_hash(digits)
				gather = twilio.Gather(numDigits=8, action=reverse('changePin'))
				gather.append(tts(_('To verify that we have the correct pin, '
					'please enter it again. Press pound to finish.')))
				r.append(gather)
				return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)
		else:
			# The PIN has been entered once. Time to verify it.
			p = re.compile('\d{4,8}#?$')
			if (p.match(digits)):
				if (check_pin(digits, request.session['ivr_changePin_hash'])):
					r.append(twilio.Redirect(reverse(request.session['ivr_call_stack'].pop())))
					response = HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)
					if ('answering_service' in request.session and 
							request.session['answering_service'] == 'yes'):
						practice = PracticeLocation.objects.get(id=request.session['practice_id'])
						practice.pin = request.session['ivr_changePin_hash']
						practice.save()
					else:
						config = VMBox_Config.objects.get(id=request.session['config_id'])
						# Note: request.user is anon for twilio sessions, issue 1362
						# get_user_key assumes cookie has 'ss' and ss def arg None by def
						old_key = get_user_key(request) if 'ss' in request.COOKIES else None
						config.change_pin(request, old_key=old_key, new_pin=digits)
						config.pin = request.session['ivr_changePin_hash']
						config.save()
					del request.session['ivr_changePin_hash']

					event = callEvent(callSID=request.POST['CallSid'], event='F_PCH')
					event.save()

					request.session.modified = True
					return response
			r.append(tts(_('The entered pins do not match.')))
			del request.session['ivr_changePin_hash']

	if (not 'ivr_changePin_hash' in request.session):
		# This is the code that gets executed on the first run of this function.
		# It also gets run if the PIN verification fails.
		gather = twilio.Gather(numDigits=8, action=reverse('changePin'))
		gather.append(tts(_("Please enter four to eight digits. Press pound to finish.")))
		r.append(gather)

	return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)


@TwilioAuthentication()
def getCallBackNumber(request, twilioResponse=None):
	"""
	Gets call back number from users input, verifies number, sends it back to 
	be used in msg or sms
	"""
	if 'CallStatus' in request.POST:
		logger.debug('%s: Into getCallBackNumber with call status %s' % (
			request.session.session_key, request.POST['CallStatus']))

	r = twilioResponse or twilio.Response() 
	request.session.modified = True

	if ('CallStatus' in request.POST and request.POST['CallStatus'] == 'completed'):
		# First, check to see if the caller has hung up.
		if ('ivr_has_number' in request.session and 'ivr_callback_returnOnHangup' in
			request.session and 'ivr_makeRecording_callbacknumber' in request.session):
			#call caller function, just to send empty msg or sms
			request.session['ivr_only_callbacknumber'] = True
			view = request.session.get('ivr_callback_returnOnHangup', None)
			if view:
				try:  # TODO: no more exec() but validation on view is needed
					mod, func = view.rsplit('.', 1)
					mod = import_module(mod)
					getattr(mod, func)(request)  # call the view function
				except Exception as e:
					mail_admins("Problem calling view in getCallBackNumber", str(e))

		return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)

	# after hung up we need to clear first time < 10 digit numbers for urgent calls
	if ('ivr_urgent_second_time' in request.session):
		request.session.pop('ivr_makeRecording_callbacknumber', None)
		request.session.pop('ivr_caller_id_area_code', None)

	if 'Digits' in request.POST:
		digits = request.POST['Digits']

		if ('ivr_makeRecording_callbacknumber' in request.session):
			p = re.compile('[0-9]$')
			if (not p.match(digits)):
				del request.session['ivr_makeRecording_callbacknumber']
				del request.session['ivr_has_number']
				request.session.pop('ivr_caller_id_area_code', None)
				r.append(tts('I\'m sorry, I didn\'t understand that.'))
				r.append(twilio.Redirect(reverse('getCallBackNumber')))
			elif (digits == '1'):
				# correct number - leave function, and get voice recordng
				r.append(twilio.Redirect(reverse(request.session['ivr_call_stack'].pop())))
				request.session.modified = True
				#r.append(twilio.Redirect(reverse('getCallBackNumber')))
			elif (digits == '3'):
				#user said, bad number, reinit and enter number again
				del request.session['ivr_makeRecording_callbacknumber']
				del request.session['ivr_has_number']
				request.session.pop('ivr_caller_id_area_code', None)
				r.append(twilio.Redirect(reverse('getCallBackNumber')))
			else:
				r.append(tts('I\'m sorry, I didn\'t understand that.'))
				gather = twilio.Gather(finishOnKey='', numDigits=1, 
									action=reverse('getCallBackNumber'))
				spoken_number = []
				[spoken_number.extend([i, ' ']) for i in 
					request.session['ivr_makeRecording_callbacknumber']]
				spoken_number.pop()  # drop the last element
				gather.append(tts(_('Eye got %s. If this is correct, press one. Or'
					'press three to enter eh different number') % (''.join(spoken_number),)))
				r.append(gather)
				#r.append(twilio.Redirect(reverse('getCallBackNumber')))

			return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)

		if ('ivr_has_number' in request.session):
			#first time thru phone was entered ivr_makeRecording_callbacknumber does 
			# not have phone number in it yet.
			if (not 'ivr_makeRecording_callbacknumber' in request.session or
					'ivr_urgent_second_time' in request.session):
				if(re.match(r'[0-9]+', digits)):
					spoken_number = []
					[spoken_number.extend([i, ' ']) for i in digits]
					spoken_number.pop()  # drop the last element
					#spoken_number.insert(5, ',')
					#spoken_number.insert(12, ',')
					request.session['ivr_makeRecording_callbacknumber'] = digits
					#take first three digits from caller, in case less than 10 digits are
					# entered, we do this for ALL calls where call back number is < 10 digits
					if (len(digits) < 10 and 'Caller' in request.session and 
							len(request.session['Caller']) > 2):
						request.session['ivr_caller_id_area_code'] = request.session['Caller'][0:3]

					# for bug 829, ONLY on FIRST pass, we need to make sure its at least 
					# 10 digits, if not say please make sure you entered area code
					# only if this is URGENT call, rest of callers are free to leave any 
					# number of digits also, if after first try, users still enters < 10 
					# digits, let it go thru (ivr_urgent_second_time var is used for that)
					view = request.session.get('ivr_callback_returnOnHangup', None)
					if (not 'ivr_urgent_second_time' in request.session and len(digits) < 10 
							and view and view.split('.')[-1] == 'PracticeIVR_LeaveUrgentMsg'): 
						gather = twilio.Gather(finishOnKey='#', numDigits=12, timeout=30,
												action=reverse('getCallBackNumber'))
						gather.append(tts('I\'m sorry, It appears your call back number '
									'is less than ten digits. Please enter your call back '
									'number including area code now. Then press pound.'))
						r.append(gather)
						r.append(twilio.Redirect(reverse('getCallBackNumber')))
						request.session['ivr_urgent_second_time'] = True

						return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)
					#========= end of bug 829 =======================
					else:
						gather = twilio.Gather(finishOnKey='', numDigits=1,
											action=reverse('getCallBackNumber'))
						gather.append(tts('Eye got %s . If this is correct, press one. '
										'Or press three to enter eh different number' % \
											(''.join(spoken_number),)))
						r.append(gather)
						r.append(twilio.Redirect(reverse('getCallBackNumber')))
						request.session.pop('ivr_urgent_second_time', None)

						return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)
				else:
					r.append(tts(_('I\'m sorry, I didn\'t understand that.')))
					r.append(twilio.Redirect(reverse('getCallBackNumber')))

					request.session.pop('ivr_has_number', None)
					request.session.pop('ivr_makeRecording_callbacknumber', None)
					return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)

	if (not 'ivr_has_number' in request.session):
		# This is the code that gets executed on the first run of this function.
		#'digits' get posted for next itteration
		# It also gets run if the call back number verification fails
		gather = twilio.Gather(finishOnKey='#', numDigits=12, timeout=30,
							action=reverse('getCallBackNumber'))
		gather.append(tts(_('On the keypad, please enter your call back number '
									'including area code now, then press pound.')))
		r.append(gather)
		r.append(twilio.Redirect(reverse('getCallBackNumber')))
		request.session['ivr_has_number'] = True

		return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)

	#this is the case of user pressing just pound at call back number, there are no digits.
	if ('ivr_has_number' in request.session and 'Digits' not in request.POST):
		del request.session['ivr_has_number']
		request.session.pop('ivr_makeRecording_callbacknumber', None)
		r.append(tts(_('I\'m sorry, I didn\'t understand that.')))
		r.append(twilio.Redirect(reverse('getCallBackNumber')))
		return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)

	raise Exception(_('should never get here'))


@TwilioAuthentication()
def authenticateSession(request, twilioResponse=None):
	"""
	:param request: The standard Django request argument
	:param request.session Keys: config_id - The ID of the VMBox_Config object
		pertaining to the current voicemail session.
	:param twilioResponse: A twilio response object. Use this to pass in any verbs
		that should be run before the prompt. Note that any verbs passed
		in will be lost on subsequent runs through this function (e.g.,
		when the user enters an incorrect pin)
	:returns: django.http.HttpResponse -- the result
	"""
	r = twilioResponse or twilio.Response() 
	if (not 'pin_errCount' in request.session):
		request.session['pin_errCount'] = 0

	if 'Digits' in request.POST:
		call_sid = request.POST['CallSid']
		digits = request.POST['Digits']
		p = re.compile('\d{4,8}#?$')
		if (p.match(digits)):
			if ('answering_service' in request.session and 
					request.session['answering_service'] == 'yes'):
				practice = PracticeLocation.objects.get(id=request.session['practice_id'])
				if (practice.verify_pin(digits)):
					request.session['authenticated'] = True
					r.append(twilio.Redirect(reverse(request.session['ivr_call_stack'].pop())))
					request.session.modified = True
					return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)
			else:
				user = authenticate(config_id=request.session['config_id'], pin=digits)
				if (user):
					login(request, user)
					# TESTING_KMS_INTEGRATION
					uprivs = UserPrivateKey.objects.filter(user=user,
						credtype=CRED_IVRPIN, gfather=True)
					if uprivs.exists():
						config = VMBox_Config.objects.get(id=request.session['config_id'])
						config.change_pin(request, new_pin=digits)
					request.session['authenticated'] = True
					event = callEvent(callSID=call_sid, event='V_ASU')
					event.save()
					r.append(twilio.Redirect(reverse(request.session['ivr_call_stack'].pop())))
					request.session.modified = True
					response = HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)
					store_user_key(request, response, digits)
					return response

		event = callEvent(callSID=call_sid, event='V_AFL')
		event.save()

		r.append(tts('An in valid pin was entered.'))
		request.session['pin_errCount'] += 1
		if (request.session['pin_errCount'] >= 3):  # give the user three erroneous pin entries.
			r.append(tts('Good bye.'))
			r.append(twilio.Hangup())
			return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)

	# This is the code that gets executed on the first run of this function.
	gather = twilio.Gather(numDigits=8, action=reverse('authenticateSession'))
	gather.append(tts(_("Please enter your pin number. Press pound to finish.")))
	r.append(gather)

	return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)


@TwilioAuthentication()
def getQuickRecording(request):
	"""Takes a recording from the user. This function uses the session dictionary
	at request.session for inputs and outputs. This is done to maintain code
	base flexibility with this and getRecording.

	This function differs from getRecording in that strictly gets a
	recording from the user, without allowing the user to confirm that they wish
	to keep the recording.

	:param request: The standard Django request argument
	:returns: django.http.HttpResponse -- the result

	Required Session Keys:
		request.session['ivr_makeRecording_prompt'] - A Twilio verb object
				(pretty much always Say or Play) that is used to lead into the
				recording. e.g., tts('Leave a message.')

	Optional Session Keys:
		request.session['ivr_makeRecording_maxLength'] - The Twilio gather
				max_length value. Default is 5: 5 seconds.
		request.session['ivr_makeRecording_timeout'] - The Twilio record timeout
				value. Default is 6.
		request.session['ivr_makeRecording_leadSilence'] - How many seconds of
				silence to give before starting any prompts. This is necessary
				because the first second or so of sound at the very beginning of
				any Twilio call is lost. Default is 1.
		request.session['ivr_makeRecording_playBeep'] - Set to True if you want
				the recording to be prompted with a tone. Default is True.
		request.session['ivr_makeRecording_finishOnKey'] - The Twilio gather
				finishOnKey value. Default is any key.

	Output Session Keys:
		request.session['ivr_makeRecording_recording'] - The Twilio URL of the recording
				Make sure you clear this key using the 'del' built-in function
				so that other fucntions can test against it to see if
				getRecording has succeeded.

	To "return" to your function, push it onto the end of
	request.session['ivr_call_stack'], as per the usual IVR philosophy.
	"""
	if 'CallStatus' in request.POST:
		logger.debug('%s: Into getQuickRecording with call status %s' % (
			request.session.session_key, request.POST['CallStatus']))

	r = twilio.Response()
	request.session.modified = True
	request.session['ivr_only_callbacknumber'] = True

	if 'CallStatus' in request.POST and request.POST['CallStatus'] == 'completed':
		view = request.session.get('ivr_makeRecording_returnOnHangup', None)
		if view:
			# The user hung up. Return out and tell twilio no message recorded.
			request.session['ivr_no_pound'] = True
			if 'RecordingUrl' in request.POST:
				request.session['ivr_makeRecording_recording'] = request.POST['RecordingUrl']
				request.session['ivr_only_callbacknumber'] = False
			else:
				request.session['ivr_only_callbacknumber'] = True

			try:  # TODO: no more exec() but validation on view is needed
				mod, func = view.rsplit('.', 1)
				mod = import_module(mod)
				getattr(mod, func)(request)  # call the view function
			except Exception as e:
				mail_admins("Problem calling view in getQuickRecording", str(e))

		cleanup_recording_state(request)
		return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)

	if 'CallStatus' in request.POST and 'RecordingUrl' in request.POST:
		if request.POST['CallStatus'] == 'completed':
			# The user hung up. Return out and tell Twilio to do nothing.
			return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)

		recording_url = request.POST['RecordingUrl']

		p1 = re.compile('http://api.twilio.com/\d{4}-\d{2}-\d{2}/Accounts/AC[0-9a-f]{32}'\
					'/Recordings/RE[0-9a-f]{32}$')
		if (not p1.match(recording_url)):
			raise Exception(_('Recording url failed to match regex: %s') % (recording_url,))

		request.session['ivr_makeRecording_recording'] = recording_url
		request.session['ivr_only_callbacknumber'] = False

		cleanup_recording_state(request)
		del request.session['getQuickRecording_subsequentExcecution']
		r.append(twilio.Redirect(reverse(request.session['ivr_call_stack'].pop())))

		return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)

	# Check for required values
	if (not 'ivr_makeRecording_prompt' in request.session):
		raise Exception(_('Error. Required session key \'ivr_makeRecording_prompt\' '
						'undefined. Request.method is %s.') % (request.POST,))

	# Set up default values
	if (not 'ivr_makeRecording_maxLength' in request.session):
		request.session['ivr_makeRecording_maxLength'] = 5
	if (not 'ivr_makeRecording_timeout' in request.session):
		request.session['ivr_makeRecording_timeout'] = 6
	if (not 'ivr_makeRecording_leadSilence' in request.session):
		request.session['ivr_makeRecording_leadSilence'] = 1
	if (not 'ivr_makeRecording_playBeep' in request.session):
		request.session['ivr_makeRecording_playBeep'] = True
	if (not 'ivr_makeRecording_finishOnKey' in request.session):
		request.session['ivr_makeRecording_finishOnKey'] = '1234567890*#'

	# Use this to keep track of if we've been through here before.
	if ('getQuickRecording_subsequentExcecution' in request.session):
		r.append(tts('Sorry, I didn\'t get that.'))
	request.session['getQuickRecording_subsequentExcecution'] = True

	if (request.session['ivr_makeRecording_leadSilence']):
		r.append(twilio.Pause(length=request.session['ivr_makeRecording_leadSilence']))
	r.append(request.session['ivr_makeRecording_prompt'])
	r.append(twilio.Record(
					action=reverse('getQuickRecording'),
					maxLength=request.session['ivr_makeRecording_maxLength'],
					finishOnKey=request.session['ivr_makeRecording_finishOnKey'],
					timeout=request.session['ivr_makeRecording_timeout'],
					playBeep=request.session['ivr_makeRecording_playBeep'],
					))
	r.append(twilio.Redirect(reverse('getQuickRecording')))
	#raise Exception(str(r))

	return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)


@TwilioAuthentication()
def getRecording(request, twilioResponse=None):
	"""
	Takes a recording from the user. This function uses the session dictionary
	at request.session for inputs and outputs. This is necessary because
	Twilio will make multiple calls to this function. This function differs
	from getQuickRecording in that it allows a user to confirm their recording.

	:param request: The standard Django request argument
	:returns: django.http.HttpResponse -- the result

	Required Session Keys:
		request.session['ivr_makeRecording_prompt'] - A Twilio verb object
				(pretty much always Say or Play) that is used to lead into the
				recording. e.g., tts('Leave a message.')

	Optional Session Keys:
		request.session['ivr_makeRecording_promptOnce'] - A flag that specifies
				if the prompt should be spoken only once, if True. The stored
				value must be one that can be tested against for truth. (i.e.,
				the value must be able to be used in an if statement such as,
				"if (request.session['ivr_makeRecording_promptOnce']):...."
		request.session['ivr_makeRecording_maxLength'] - The Twilio gather
				max_length value. Default is 180: 3 minutes.
		request.session['ivr_makeRecording_timeout'] - The Twilio record timeout
				value. Default is 5.
		request.session['ivr_makeRecording_transcribe'] - The Twilio gather
				transcribe value. Default is False.
		request.session['ivr_makeRecording_finishOnKey'] - The Twilio gather
				finishOnKey value. Default is any key.
		request.session['ivr_makeRecording_playBeep'] - The Twilio gather
				playBeep value. Default is True.
		request.session['ivr_makeRecording_leadSilence'] - How many seconds of
				silence to give before starting any prompts. This is necessary
				because the first second or so of sound at the very beginning of
				any Twilio call is lost. Default is 0.
		request.session['ivr_makeRecording_returnOnHangup'] - The name of the
				function to return control flow to, should the user hang up on
				the recording (e.g., to terminate a voicemail message). The
				function gets called with a single argument -- the standard
				Django request object, default is None.

	Output Session Keys:
		request.session['ivr_makeRecording_recording'] - The Twilio URL of the recording
				Make sure you clear this key using the 'del' built-in function
				so that other fucntions can test against it to see if
				getRecording has succeeded.

	To "return" to your function, push it onto the end of
	request.session['ivr_call_stack'], as per the usual IVR philosophy.
	"""
	# FIXME:
	# There's gotta be a less complicated way of doing this. The biggest
	# complicating factor when writing a generic function for Twilio is that
	# every time we want to get anything from the user, we need to return and
	# wait for Twilio to establish a new HTTP connection.
	#
	# There are two design patterns that I've come up with so far. The first is
	# what you see implemented here, where Twilio accesses this function
	# directly via a REST API we provide. The two biggest problems here are that
	# it requires us to rely heavily on the session database, and that we become
	# reliant on Twilio to functionally return to the calling function. This
	# second problem is generally annoying, but becomes a meaningful problem
	# when Twilio won't redirect for us -- e.g., when the user hangs up on the
	# recording. The current solution is to use an eval() statement to directly
	# call the "caller" function, but this is kind of kludgey.
	#
	# The other design pattern is to have Twilio keep calling the "caller"
	# function, and have that call this function. The problem is that it makes
	# caller functions more complicated since they have to check the return
	# data from this function to determine what happened, and potentially keep
	# track of where this function is, in terms of its execution path across
	# HTTP connections.
	#
	# I'm not sure what we want to do about this. I'm inclined to say that the
	# latter implementation is going to be somewhat cleaner since we can
	# probably just pass a tuple of values with state and whatnot, as well as
	# the return value for the function at large?
	if 'CallStatus' in request.POST:
		logger.debug('%s: Into getRecording with call status %s' % (
			request.session.session_key, request.POST['CallStatus']))

	r = twilioResponse or twilio.Response() 
	request.session.modified = True
	# First, check to see if the caller has hung up.
	#if (request.POST['CallStatus'] == 'completed'):
	if ('CallStatus' in request.POST and request.POST['CallStatus'] == 'completed'):
		if('RecordingUrl' in request.POST):
			request.session['ivr_makeRecording_recording'] = request.POST['RecordingUrl']
		if 'ivr_makeRecording_recording' in request.session:
			view = request.session.get('ivr_makeRecording_returnOnHangup', None)
			if view:
				try:  # TODO: no more exec() but validation on view is needed
					mod, func = view.rsplit('.', 1)
					mod = import_module(mod)
					getattr(mod, func)(request)  # call the view function
				except Exception as e:
					mail_admins("Problem calling view in getRecording", str(e))

		cleanup_recording_state(request)
		return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)

	if 'RecordingUrl' in request.POST:
		recording_url = request.POST['RecordingUrl']

		p1 = re.compile('http://api.twilio.com/\d{4}-\d{2}-\d{2}/Accounts/AC[0-9a-f]'\
					'{32}/Recordings/RE[0-9a-f]{32}$')
		if (not p1.match(recording_url)):
			raise Exception(_('Recording url failed to match regex: %s') % (recording_url,))
		request.session['ivr_makeRecording_recording'] = recording_url
		getRecording_playRecordingAndConfirmation(request, r)
		return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)
	elif ('ivr_makeRecording_recording' in request.session):
		if 'Digits' in request.POST:
			digits = request.POST['Digits']
			p2 = re.compile('[0-9*#]$')
			if (not p2.match(digits)):
				raise Exception('')

			if (digits == '1'):
				# User accepted the recording.
				cleanup_recording_state(request)
				r.append(twilio.Redirect(reverse(request.session['ivr_call_stack'].pop())))
				return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)
			if (digits == '3'):
				del request.session['ivr_makeRecording_recording']
				# And just fall through. User wishes to record again, so pretty much start over.
			else:
				getRecording_playRecordingAndConfirmation(request, r)
				return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)
		else:
			getRecording_getConfirmation(request, r)
			return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)

	# Check for required values
	if (not 'ivr_makeRecording_prompt' in request.session):
		raise Exception(_('Error. Required session key \'ivr_makeRecording_prompt\' undefined.'))

	# Set up default values
	if (not 'ivr_makeRecording_promptOnce' in request.session):
		request.session['ivr_makeRecording_promptOnce'] = False
	if (not 'ivr_makeRecording_maxLength' in request.session):
		request.session['ivr_makeRecording_maxLength'] = 180
	if (not 'ivr_makeRecording_timeout' in request.session):
		request.session['ivr_makeRecording_timeout'] = 5
	if (not 'ivr_makeRecording_transcribe' in request.session):
		request.session['ivr_makeRecording_transcribe'] = False
	if (not 'ivr_makeRecording_finishOnKey' in request.session):
		request.session['ivr_makeRecording_finishOnKey'] = '1234567890*#'
	if (not 'ivr_makeRecording_playBeep' in request.session):
		request.session['ivr_makeRecording_playBeep'] = True
	if (not 'ivr_makeRecording_leadSilence' in request.session):
		request.session['ivr_makeRecording_leadSilence'] = 0
	if (not 'ivr_makeRecording_returnOnHangup' in request.session):
		request.session['ivr_makeRecording_returnOnHangup'] = None

	if (request.session['ivr_makeRecording_promptOnce']):
		if (not 'ivr_makeRecording_promptOnce_played' in request.session):
			request.session['ivr_makeRecording_promptOnce_played'] = True
			r.append(request.session['ivr_makeRecording_prompt'])
	else:
		r.append(request.session['ivr_makeRecording_prompt'])
	if (request.session['ivr_makeRecording_leadSilence']):
		r.append(twilio.Pause(length=request.session['ivr_makeRecording_leadSilence']))

	r.append(twilio.Record(
					action=reverse('getRecording'),
					maxLength=request.session['ivr_makeRecording_maxLength'],
					timeout=request.session['ivr_makeRecording_timeout'],
					finishOnKey=request.session['ivr_makeRecording_finishOnKey'],
					transcribe=request.session['ivr_makeRecording_transcribe'],
					playBeep=request.session['ivr_makeRecording_playBeep'],
					))

	r.append(twilio.Redirect(reverse('getRecording')))

	return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)


@TwilioAuthentication()
def getRecording_playRecordingAndConfirmation(request, twilioResponse):
	gather = twilio.Gather(numDigits=1, finishOnKey='', action=reverse('getRecording'))
	gather.append(tts(_("You said")))
	gather.append(twilio.Play(request.session['ivr_makeRecording_recording']))
	gather.append(tts(_('If you wish to record again, please press three.'
			'Press one to continue. Press any other key to replay the recording.')))
	twilioResponse.append(gather)
	twilioResponse.append(twilio.Redirect())


@TwilioAuthentication()
def getRecording_getConfirmation(request, twilioResponse):
	gather = twilio.Gather(numDigits=1, finishOnKey='', action=reverse('getRecording'))
	gather.append(tts(_('If you wish to record again, please press three. '
			'Press one to continue. Press any other key to replay the recording.')))
	twilioResponse.append(gather)
	twilioResponse.append(twilio.Redirect())


@TwilioAuthentication()
def cleanup_recording_state(request):
	request.session.pop('ivr_makeRecording_prompt', None)
	request.session.pop('ivr_makeRecording_maxLength', None)
	request.session.pop('ivr_makeRecording_timeout', None)
	request.session.pop('ivr_makeRecording_transcribe', None)
	request.session.pop('ivr_makeRecording_finishOnKey', None)
	request.session.pop('ivr_makeRecording_playBeep', None)
	request.session.pop('ivr_makeRecording_leadSilence', None)
	request.session.pop('ivr_makeRecording_returnOnHangup', None)
	request.session.pop('ivr_makeRecording_promptOnce', None)
	request.session.pop('ivr_makeRecording_promptOnce_played', None)


@TwilioAuthentication()
def changeName(request, prependPrompt=''):
	"""Requests the user record their name and stores it in the config with id
	at request.session['config_id'].

	:param request: the usual Django view argument
	:param prependPrompt: The string to prepend to the start of the request. Note
		that sending None will result in an error. If you don't wish to
		prepend anything explicitly, please pass in an empty string.
	:returns: django.http.HttpResponse -- the result
	"""

	if ('ivr_makeRecording_recording' in request.session):
		if ('answering_service' in request.session and 
				request.session['answering_service'] == 'yes'):
			practice = PracticeLocation.objects.get(id=request.session['practice_id'])
			practice.name_greeting = request.session['ivr_makeRecording_recording']
			del request.session['ivr_makeRecording_recording']
			practice.save()
		else:
			config = VMBox_Config.objects.get(id=request.session['config_id'])
			config.name = request.session['ivr_makeRecording_recording']
			del request.session['ivr_makeRecording_recording']
			config.save()

		event = callEvent(callSID=request.POST['CallSid'], event='F_NCH')
		event.save()

		r = twilio.Response()
		r.append(twilio.Redirect(reverse(request.session['ivr_call_stack'].pop())))
		request.session.modified = True
		return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)

	request.session['ivr_makeRecording_prompt'] = tts(_("Please say your name "
							"after the tone. Press pound to finish."))
	request.session['ivr_makeRecording_maxLength'] = 10
	request.session['ivr_makeRecording_timeout'] = 3

	request.session['ivr_call_stack'].append('changeName')
	return getRecording(request)


@TwilioAuthentication()
def changeGreeting(request, prependPrompt=''):
	"""Requests the user record their greeting and stores it in the config with id
	at request.session['config_id'].

	:param request: the usual Django view argument
	:param prependPrompt: The string to prepend to the start of the request. Note
		that sending None will result in an error. If you don't wish to
		prepend anything explicitly, please pass in an empty string.
	:returns: django.http.HttpResponse -- the result
	"""

	if ('ivr_makeRecording_recording' in request.session):
		if ('answering_service' in request.session and 
				request.session['answering_service'] == 'yes'):
			practice = PracticeLocation.objects.get(id=request.session['practice_id'])
			if (request.session['ivr_setup_stage'] == 3):
				practice.greeting_closed = request.session['ivr_makeRecording_recording']
			else:
				practice.greeting_lunch = request.session['ivr_makeRecording_recording']
			del request.session['ivr_makeRecording_recording']
			practice.save()
		else:
			config = VMBox_Config.objects.get(id=request.session['config_id'])
			config.greeting = request.session['ivr_makeRecording_recording']
			del request.session['ivr_makeRecording_recording']
			config.save()

			event = callEvent(callSID=request.POST['CallSid'], event='F_GCH')
			event.save()

		r = twilio.Response()
		r.append(twilio.Redirect(reverse(request.session['ivr_call_stack'].pop())))
		request.session.modified = True
		return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)

	#make twilio say different things based on who called it, prepend seemed to
	#be never used, i will investigate later and see why not to use it
	if ('answering_service' in request.session and request.session['answering_service'] == 'yes'):
		if (request.session['ivr_setup_stage'] == 3):
			request.session['ivr_makeRecording_prompt'] = tts(_("Please say your "
				"new greeting for closed office after the tone. Press pound to finish."))
		else:
			request.session['ivr_makeRecording_prompt'] = tts(_("Please say your greeting "
				"greeting for temporarily closed office after the tone. Press pound to finish."))
	else:
		request.session['ivr_makeRecording_prompt'] = tts(_("Please say your new "
				"greeting after the tone. Press pound to finish."))

	request.session['ivr_makeRecording_maxLength'] = 120
	request.session['ivr_makeRecording_timeout'] = 3

	request.session['ivr_call_stack'].append('changeGreeting')
	return getRecording(request)


@TwilioAuthentication()
def callBackUser(request, message):
	callerId = Provider.objects.get(id=request.session['provider_id']).mdcom_phone
	r = twilio.Response()
	callSID = request.POST['CallSid']
	log = callLog.objects.get(callSID=callSID)
	if(message.urgent):
		log.call_source = 'CB'
	else:
		log.call_source = 'CC'
	log.save()
	provider_qs = Provider.objects.filter(mobile_phone=message.callback_number)
	if(provider_qs):
		from views_provider import ProviderIVR_OutsideInit, ProviderIVR_ForwardCall
		provider = provider_qs.get()
		ProviderIVR_OutsideInit(request, log.caller_number, provider, log)
		return ProviderIVR_ForwardCall(request)
	dial = twilio.Dial(message.callback_number,
				callerId=callerId,
				timeout=120)
	r.append(dial)
	CallbackLog(message=message).save()
	return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)


@TwilioAuthentication()
def playMessages(request, msgs_querySet=None, twilioResponse=None):
	"""Plays and gives the menu tree to act on messages.

	:param request: the usual Django view argument
	:param msgs_querySet: django query set of voice messages
	:param twilioResponse: None if direct from Twilio, set if called within IVR  
	:returns: django.http.HttpResponse -- the result
	"""
	# msgs_querySet is None when called from Twilio and session is setup
	if msgs_querySet != None:
		# msgs_querySet is not None when called within IVR tree but may be empty set
		request.session['ivr_playMessages_newMessages'] = list(msgs_querySet.filter(
			read_flag=False, delete_flag=False).order_by('msg_body__message__message_type',
				'-msg_body__message__send_timestamp').all())
		if len(request.session['ivr_playMessages_newMessages']):
			request.session['ivr_playMessages_newMsgsFlag'] = True
		request.session['ivr_playMessages_oldMessages'] = list(msgs_querySet.filter(
			read_flag=True, delete_flag=False).order_by('msg_body__message__message_type',
				'-msg_body__message__send_timestamp').all())
	# We're pretty much always going to be manipulating the session.
	request.session.modified = True

	r = twilioResponse or twilio.Response() 
	replayFlag = False
	playFlag = True

	call_sid = request.POST['CallSid']

	if (not msgs_querySet and 'Digits' in request.POST):
		digits = request.POST['Digits']
		p = re.compile('[0-9#*]$')
		if (not p.match(digits)):
			r.append(tts('I\'m sorry, I didn\'t understand that.'))
			playFlag = False

		if (digits == '1'):
			# do nothing
			pass
		elif (digits == '3'):
			replayFlag = True
		elif (digits == '5'):
			return callBackUser(request, 
				request.session['ivr_playMessages_currentMsg'].msg_body.message)
		elif (digits == '7'):
			# Merely sets the 'deleted' flag to hide the message.
			r.append(tts('Message resolved'))

			event = callEvent(callSID=call_sid, event='V_MDL')
			event.save()
			target = callEventTarget(event=event, 
				target=request.session['ivr_playMessages_currentMsg'])
			target.save()
			request.session['ivr_playMessages_currentMsg'].\
				msg_body.message.resolved_by = request.user
		elif (digits == '9'):
			r.append(twilio.Redirect(reverse(request.session['ivr_call_stack'].pop())))
			return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)

	if (replayFlag):
		r.append(tts('Re-playing message'))
	elif (not playFlag):
		pass  # do nothing -- we don't want to move to the next message.
	elif (len(request.session['ivr_playMessages_newMessages'])):
		if (msgs_querySet):
			r.append(tts('Playing the first new message'))
		else:
			r.append(tts('Playing the next new message'))
		request.session['ivr_playMessages_currentMsg'] = \
			request.session['ivr_playMessages_newMessages'].pop(0)
		event = None

		if(request.session['ivr_playMessages_currentMsg'].msg_body.message.message_type == 'ANS'):
			event = callEvent(callSID=call_sid, event='V_NAP')
			event.save()
		else:
			event = callEvent(callSID=call_sid, event='V_NMP')
			event.save()
		target = callEventTarget(event=event, target=request.session['ivr_playMessages_currentMsg'])
		target.save()
		request.session['ivr_playMessages_currentMsg'].read_flag = True
		request.session['ivr_playMessages_currentMsg'].save()
	elif (len(request.session['ivr_playMessages_oldMessages'])):
		#if (request.session['ivr_playMessages_newMsgsFlag']):
			# Done playing new messages.
		#	pass
		if (msgs_querySet):
			r.append(tts('Playing the first old message'))
		else:
			r.append(tts('Playing the next old message'))
		request.session['ivr_playMessages_currentMsg'] = \
			request.session['ivr_playMessages_oldMessages'].pop(0)

		event = None
		if(request.session['ivr_playMessages_currentMsg'].msg_body.message.message_type == 'ANS'):
			event = callEvent(callSID=call_sid, event='V_OAP')
			event.save()
		else:
			event = callEvent(callSID=call_sid, event='V_OMP')
			event.save()

		target = callEventTarget(event=event, target=request.session['ivr_playMessages_currentMsg'])
		target.save()
	else:
		r.append(tts('End of messages'))
		r.append(twilio.Redirect(reverse(request.session['ivr_call_stack'].pop())))
		return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)

	gather = twilio.Gather(finishOnKey='', numDigits=1, action=reverse('playMessages'))
	if (playFlag):
		url = ''
		if (request.session['ivr_playMessages_currentMsg'].\
				msg_body.message.message_type == 'ANS'):
			spoken_number = []
			digits = request.session['ivr_playMessages_currentMsg'].\
				msg_body.message.callback_number
			[spoken_number.extend([i, ' ']) for i in digits]
			spoken_number.pop()  # drop the last element
			#spoken_number.insert(5, ',')
			#spoken_number.insert(12, ',')
			gather.append(tts('Call from %s .' % (''.join(spoken_number),)))
		msg = request.session['ivr_playMessages_currentMsg'].msg_body.message
		try:
			uuid = MessageAttachment.objects.get(message=msg).uuid
			url = reverse("fetchRecording", kwargs={"uuid": uuid})
			gather.append(twilio.Play(url))
		except MessageAttachment.DoesNotExist:
			errors = {
				'U': _("User hung up before confirming number."),
				'C': _("User hung up before leaving message."),
				'R': _("An error occurred downloading the recording. We will retry until "
					"successful and you will receive a new message at that time."),
			}
			gather.append(tts(errors[msg.vmstatus]))

	gather.append(twilio.Pause())
	gather.append(tts(_('Press 1 to move to the next message. ')))
	gather.append(tts(_('Press 3 to re-play the message. ')))
	callback_number = request.session['ivr_playMessages_currentMsg'].\
		msg_body.message.callback_number
	if(re.match("1?\d{10}", callback_number)):
		gather.append(tts(_('Press 5 to call this person back. ')))
	gather.append(tts(_('Press 7 to mark the message resolved and hide it. ')))
	gather.append(tts(_('Press 9 to return to the main menu. ')))

	r.append(gather)
	return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)

FETCH_ERROR = ''.join([settings.MEDIA_ROOT, "audio/fetch_error.wav"])


@TwilioAuthentication(allow_get=True)
def fetchRecording(request, uuid):
	"""
	:returns: recording to twilio
	"""
	attachment = MessageAttachment.objects.filter(uuid=uuid)
	if attachment:
		attachment = attachment[0]
		response = HttpResponse(content_type=attachment.content_type)
		try:
			attachment.get_file(request, response, ivr=True)
		except:
			body = "Unable to fetch recording, filename in storage: %s" % attachment.uuid
			mail_admins("Error fetching recording", body)
			with open(FETCH_ERROR, "rb") as f:
				return HttpResponse(f.read(), mimetype='audio/wav')
		return response
	return err404()


@TwilioAuthentication()
def callNumber(request):
	pass

