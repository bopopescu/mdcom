
import re

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.contrib.auth import login, authenticate
from django.utils.importlib import import_module
from twilio import twiml as twilio
from django.core.exceptions import ObjectDoesNotExist

from models import VMBox_Config
from models import get_new_pin_hash, check_pin, callEvent, callEventTarget, callLog

from MHLogin.MHLUsers.models import Provider, MHLUser
from MHLogin.utils.decorators import TwilioAuthentication
from MHLogin.utils.mh_logging import get_standard_logger
from MHLogin.MHLPractices.models import PracticeLocation
from MHLogin.DoctorCom.Messaging.models import MessageAttachment, CallbackLog
from MHLogin.DoctorCom.speech.utils import tts
from MHLogin.DoctorCom.IVR.utils import _getUSNumber, _sanityCheckNumber
from MHLogin.KMS.utils import store_user_key, get_user_key
from MHLogin.KMS.models import UserPrivateKey, CRED_IVRPIN
from MHLogin.utils.admin_utils import mail_admins

from django.utils.translation import ugettext as _

# Setting up logging
logger = get_standard_logger('%s/DoctorCom/IVR/views_generic_v2.log' % (settings.LOGGING_ROOT),
							'DCom.IVR.views_gen2', settings.LOGGING_LEVEL)


def _getCallLogOrParent(request):
	"""
	get existing callLog based on CALLSID or get callLog based on ParentCallSid
	"""
	callSID = request.POST['CallSid']
	logger.debug('%s: _getCallLogOrParent is called with sid %s' % (
		request.session.session_key, callSID))
	try:
		log = callLog.objects.get(callSID=callSID)
		plog = None
		if 'ParentCallSid' in request.POST:
			pcallSID = request.POST['ParentCallSid']
			plog = callLog.objects.get(callSID=pcallSID)
	except ObjectDoesNotExist:
		# for 2010-04-01 api 2nd leg calls have their own sid, try
		# parent if exists, re-raise if no parent or not found.
		if 'ParentCallSid' in request.POST:
			pcallSID = request.POST['ParentCallSid']
			plog = callLog.objects.get(callSID=pcallSID)
			logger.debug('%s: _getCallLogOrParent create new child log - getting parentsid %s of callsid %s caller %s called %s' % (
				request.session.session_key, pcallSID, callSID, request.POST['From'], request.POST['To']))
			# we should create the child log here
			log = _getOrCreateCallLog(request, callSID, 
				_getUSNumber(request.POST['From']), _getUSNumber(request.POST['To']), 'FC')
			# same caller/called info if any as parent for the case of call forward
			log.mdcom_caller = plog.mdcom_caller
			log.mdcom_called = plog.mdcom_called
			log.c2c_entry_id = plog.c2c_entry_id
			log.caller_spoken_name = plog.caller_spoken_name
			log.save()
		else:
			logger.info('%s: _getCallLogOrParent unidentified callsid %s' % (
				request.session.session_key, callSID))
			raise
	return (log, plog)


def _getOrCreateCallLog(request, callSID, caller, called, csource, mdcomcalled=None, mdcomcaller=None):
	"""
	get existing callLog based on CALLSID or create it
	"""
	logger.debug('%s: _getOrCreateCallLog is called with Caller %s, Called %s source %s' % (
		request.session.session_key, caller, called, csource))
	log_qs = callLog.objects.filter(callSID=callSID)
	if (log_qs.exists()):
		# FIXME: This condition shouldn't be hit! This init function is getting
		# run multiple times per call, and I don't know why. --BK
		log = log_qs.get()
	else:
# workaround for django bug - #7551
		args = {"caller_number": caller,
				"called_number": called,
				"callSID": callSID,
				"call_source": csource,
				}
		if(mdcomcalled and mdcomcaller):
			args = {"caller_number": caller,
					"called_number": called,
					"callSID": callSID,
					"call_source": csource,
					"mdcom_called": mdcomcalled,
					"mdcom_caller": mdcomcaller,
					}
		elif(mdcomcaller):
			args = {"caller_number": caller,
					"called_number": called,
					"callSID": callSID,
					"call_source": csource,
					"mdcom_caller": mdcomcaller,
					}
		elif(mdcomcalled):
			args = {"caller_number": caller,
					"called_number": called,
					"callSID": callSID,
					"call_source": csource,
					"mdcom_called": mdcomcalled,
					}
		log = callLog(**args)
	return log


def _getMHLUser(number):
	"""
	returns MHLuser associated with a phone number (no country code) - if any; otherwise returns None
	we may want to throw an exception here if we get > 1 user associated with the number
	"""
	logger.debug(' _getMHLUser is called with number %s' % (number))
	user = None
	mhlusers_mobile_phone = MHLUser.objects.filter(mobile_phone=number)
	mhlusers_phone = MHLUser.objects.filter(phone=number)
	total_users = mhlusers_mobile_phone.count() + mhlusers_phone.count()
	if (total_users == 1):
		# First, get the MHLUser involved.
		if (mhlusers_mobile_phone.count()):
			user = mhlusers_mobile_phone.get()
		else:
			user = mhlusers_phone.get()
	return user


def _maskProviderCaller(request, caller_mhluser):
	"""
	given a caller that is an mhluser (or none), we check if the user is a provider and get the mdcom
	number to replace the actual caller number
	"""
	logger.debug('%s: _maskProviderCaller is called with Caller_mhluser %s' % (
		request.session.session_key, caller_mhluser))
	caller_provider = None
	if caller_mhluser:
		caller_provider_qs = Provider.objects.filter(user=caller_mhluser)
		if (caller_provider_qs.exists()):
			caller_provider = caller_provider_qs.get(user=caller_mhluser)
			if (caller_provider.mdcom_phone):
				request.session['Caller'] = caller_provider.mdcom_phone
	logger.debug('%s: _maskProviderCaller found caller provider %s' % (
		request.session.session_key, caller_provider))
	return caller_provider


def _setup_Main_callers(request):
	"""
	sets up initial caller/called or To/from for the request
	IMPORTANT NOTE:
	In the case of new Twilio API, I strip the phone numbers to a us number 
	to match the database - to get the actual country code, etc, use the request.POST values.
	mail admins if invalid sanity check numbers
	Within the session variables, we will still user Caller and Called for From and To.
	"""
	requestDataDict = {"GET": request.GET, "POST": request.POST}[request.method]
	# need to get Caller/From and Called/To and do sanity checks
	if (settings.TWILIO_API_VERSION == '2010-04-01'):
		if ('From' in requestDataDict):
			caller = requestDataDict['From']
			if (not _sanityCheckNumber(caller)):
				if (caller != '' and caller != None):
					subject = _('GenericIVR_Main_callers Incoming CallerID Sanitation Fail')
					message = _('GenericIVR_Main_callers incoming CallerID failed on input %s.') % (caller,)
					mail_admins(subject=subject, message=message, fail_silently=False)
				caller = ''
			caller = _getUSNumber(caller)
		else:
			caller = ''

		if ('To' in requestDataDict):
			called = requestDataDict['To']
			if (not _sanityCheckNumber(called)):
				called = ''
			called = _getUSNumber(called)
		else:
			called = ''
		logger.debug('%s: _setup_Main_callers is called with From %s, To %s' % (
			request.session.session_key, caller, called))
	else:  # we may not need this, but just in case
		if ('Caller' in requestDataDict):
			caller = requestDataDict['Caller']
			if (not _sanityCheckNumber(caller)):
				caller = ''
		else:
			caller = ''

		if ('Called' in requestDataDict):
			called = requestDataDict['Called']
			if (not _sanityCheckNumber(called)):
				called = ''
		else:
			called = ''
		logger.debug('%s: _setup_Main_callers is called with Caller %s, Called %s' % (
			request.session.session_key, caller, called))

	# now we save Caller and Called in request session for future use
	if (not 'Caller' in request.session):
		request.session['Caller'] = caller
	elif (request.session['Caller'] == ''):
		request.session['Caller'] = caller
	else:
		# if it is already set, we don't do anything; but check if unexpected value
		if request.session['Caller'] != caller:
			logger.debug('%s: _setup_Main_callers has caller set to %s, vs from Twilio %s' % (
				request.session.session_key, request.session['Caller'], caller))

	if (not 'Called' in request.session):
		request.session['Called'] = called
	elif (request.session['Called'] == ''):
		request.session['Called'] = called
	else:
		# if it is already set, we don't do anything; but check if unexpected value
		if request.session['Called'] != called:
			logger.debug('%s: _setup_Main_callers has called set to %s, vs from Twilio %s' % (
				request.session.session_key, request.session['Called'], called))
	return caller, called


def _copyStateVariables(request):
	"""
	copy corresponding required state vars so it works with old style save_message
	"""
	if ('ivr2_Record_callbacknumber' in request.session):
		request.session['ivr_makeRecording_callbacknumber'] = request.session['ivr2_Record_callbacknumber']
	if ('ivr2_Record_recording' in request.session):
		request.session['ivr_makeRecording_recording'] = request.session['ivr2_Record_recording']
	if ('ivr2_caller_id_area_code' in request.session):
		request.session['ivr_caller_id_area_code'] = request.session['ivr2_caller_id_area_code']
	if ('ivr2_only_callbacknumber' in request.session):
		request.session['ivr_only_callbacknumber'] = request.session['ivr2_only_callbacknumber']


def saveRecordingReturn(request):
	"""
	figures out what to do with the recording url based on ivr2_state and where to return to
	this is only for those with voice recording, not pins
	"""
	state = request.session.get('ivr2_state', None)
	logger.debug('%s: saveRecordingReturn state is %s' % (
		request.session.session_key, state))
	if ((state == 'ProviderIVR_Setup_New') or (state == 'ProviderIVR_Options_New') or
		(state == 'PracticeIVR_Setup_New') or (state == 'PracticeIVR_Options_New')):
		# must have substates to decide whether we are recording name or greeting
		substate = request.session.get('ivr2_sub_state', None)
		logger.debug('%s: saveRecordingReturn substate %s' % (request.session.session_key, substate))
		if ((substate == 'ProviderIVR_Setup_Name') or (substate == 'ProviderIVR_Options_1') or
			(substate == 'PracticeIVR_Setup_2') or (substate == 'PracticeIVR_Options_1')):
			return changeNameConfirm(request)
		if ((substate == 'ProviderIVR_Setup_Greeting') or (substate == 'ProviderIVR_Options_3') or
			(substate == 'PracticeIVR_Setup_3') or (substate == 'PracticeIVR_Options_2') or
			(substate == 'PracticeIVR_Setup_4') or (substate == 'PracticeIVR_Options_3')):
			return changeGreetingConfirm(request)
	# otherwise, it is simply caller leaving a name
	else:
		r = twilio.Response()
		nextUrl = _getNextRedirectState(request)
		logger.debug('%s: saveRecordingReturn redirect to %s' % (request.session.session_key, nextUrl))
		r.append(twilio.Redirect(reverse(nextUrl)))
		request.session.modified = True
		return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)


def _getNextRedirectState(request):
	"""
	based on ivr2_state of the session, this decides where to go next
	in most cases, we go back to the ivr2_state, but where we split New/Action,
	we need to decide if we return to the New or the Action part of the call
	"""
	state = request.session.get('ivr2_state', None)
	logger.debug('%s: _getNextRedirectState current %s' % (
		request.session.session_key, state))
	if (state == 'ProviderIVR_Options_Actions' or state == 'ProviderIVR_Options_New'):
		return 'ProviderIVR_Options_New'
	if (state == 'ProviderIVR_LeaveMsg_New' or state == 'ProviderIVR_LeaveMsg_Action'):
		return 'ProviderIVR_LeaveMsg_Action'
	if (state == 'PracticeIVR_CallerResponse_New'):
		return 'PracticeIVR_CallerResponse_Action'
	else:
		return state


@TwilioAuthentication()
def changePinNew(request, twilioResponse=None):
	"""This function has 3 steps for a successful PIN change.
	The first step, we request the user's pin.
	The second step, we request confirmation of the pin.
	The third step, we save the pin per caller state
	- whether it is a practice pin or VMBox config pin is based on ivr2_state
	"""
	logger.debug('%s: changePinNew' % (request.session.session_key))
	r = twilioResponse or twilio.Response()
	if ('ivr2_prompt_str' in request.session):
		r.append(tts(request.session['ivr2_prompt_str']))
	gather = twilio.Gather(finishOnKey='#', numDigits=8, action=reverse('changePinStep1'))
	gather.append(tts(_("Please enter four to eight digits. Press pound to finish.")))
	r.append(gather)
	# if user did not enter anything - we fall through back here
	return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)


@TwilioAuthentication()
def changePinStep1(request):
	"""
	we are called from twilio with user entered 4-8 digits from changePinNew
	if not valid digits, we go back to changePinNew
	if valid, we go to changePinStep2 with request for pin verification
	"""
	logger.debug('%s: changePinStep1 POST data is %s' % (request.session.session_key, str(request.POST)))
	r = twilio.Response()
	if (request.method == 'POST' and 'Digits' in request.POST):
		digits = request.POST['Digits']
		p = re.compile('\d{4,8}#?$')
		if (not p.match(digits)):
			r.append(tts(_("An in valid pin was entered.")))
			return changePinNew(request, r)
		else:
			# save this pin in the session
			request.session['ivr2_changePin_hash'] = get_new_pin_hash(digits)
			logger.debug('%s: changePinStep1 hash is %s' % (
				request.session.session_key, request.session['ivr2_changePin_hash']))
			gather = twilio.Gather(action=reverse('changePinStep2'), finishOnKey='#', numDigits=8)
			gather.append(tts(_('To verify that we have the correct pin, '
				'please enter it again. Press pound to finish.')))
			r.append(gather)
			return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)
	else:
		logger.debug('%s: changePinStep1 is called with no post or digits' % (
			request.session.session_key))
		return changePinNew(request, r)


@TwilioAuthentication()
def changePinStep2(request):
	"""
	This function gets pin confirmation input Digits and compares with the saved session pin
	Then it updates the pin based on ivr2_state - for provider or practice
	Also, based on the ivr2-_state, we call different callbacks
	"""
	logger.debug('%s: changePinStep2 POST data is %s' % (request.session.session_key, str(request.POST)))
	r = twilio.Response()
	assert(request.session['ivr2_changePin_hash'])
	if (request.method == 'POST' and 'Digits' in request.POST):
		digits = request.POST['Digits']
		# The PIN has been entered once. Time to verify it.
		p = re.compile('\d{4,8}#?$')
		if (p.match(digits)):
			if (check_pin(digits, request.session['ivr2_changePin_hash'])):
				# based on ivr2_state, we set either practice.pin or VMBox_config.pin
				nextUrl = _getNextRedirectState(request)
				# log where we go next
				logger.debug('%s: changePinStep2 check_pin ok; nexturl is %s' % (
					request.session.session_key, nextUrl))
				r.append(twilio.Redirect(reverse(nextUrl)))
				if (request.session.get('answering_service', None) == 'yes'):
					practice = PracticeLocation.objects.get(id=request.session['practice_id'])
					practice.pin = request.session['ivr2_changePin_hash']
					practice.save()
					logger.debug('%s: changePinStep2 saved practice %s pin %s' % (
						request.session.session_key, practice, practice.pin))
				else:
					config = VMBox_Config.objects.get(id=request.session['config_id'])
					# Note: request.user is anon for twilio sessions, issue 1362
					# get_user_key assumes cookie has 'ss' and ss def arg None by def
					logger.debug('%s: changePinStep2 got vmconfig %s pin %s' % (
						request.session.session_key, config.id, request.session['ivr2_changePin_hash']))
					old_key = get_user_key(request) if 'ss' in request.COOKIES else None
					config.change_pin(request, old_key=old_key, new_pin=digits)
					config.pin = request.session['ivr2_changePin_hash']
					config.save()
					logger.debug('%s: changePinStep2 saved vmconfig %s pin %s' % (
						request.session.session_key, config.id, config.pin))
				del request.session['ivr2_changePin_hash']
				event = callEvent(callSID=request.POST['CallSid'], event='F_PCH')
				event.save()
				return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)

		r.append(tts(_('The entered pins do not match.')))
		# where do we go next? back to changePinNew or whatever calls it?
		del request.session['ivr2_changePin_hash']
		return changePinNew(request, r)
	else:
		logger.debug('%s: changePinStep2 is called with no post or digits' % (
			request.session.session_key))
		return changePinNew(request, r)


def _returnCallBack(request, r):
	"""
	go back to getCallBackNumberNew - begin afresh
	"""
	r.append(tts(_('I\'m sorry, I didn\'t understand that.')))
	# cleanup session vars used
	request.session.pop('ivr2_Record_callbacknumber', None)
	request.session.pop('ivr2_caller_id_area_code', None)
	request.session.pop('ivr2_urgent_flag', None)
	return getCallBackNumberNew(request, r)


def _sayCallBackNumber(request, r):
	"""
	says the callback number in ivr2_Record_callbacknumber and ask for confirmation
	"""
	spoken_number = []
	[spoken_number.extend([i, ' ']) for i in request.session['ivr2_Record_callbacknumber']]
	spoken_number.pop()  # drop the last element
	gather = twilio.Gather(finishOnKey='', numDigits=1, action=reverse('getCallBackNumberAction'))
	gather.append(tts(_('Eye got %s. If this is correct, press one. Or '
				'press three to enter eh different number') % (''.join(spoken_number),)))
	r.append(gather)
	r.append(twilio.Redirect(reverse('getCallBackNumberAction')))


def _checkCallerHangUp(request):
	"""
	check if call is ended (user has hung up)
	if we get callback number or recording and if we have returnonHangup set,
	we want to return to caller to continue sms/text OR continue processing
	"""
	requestDataDict = {"GET": request.GET, "POST": request.POST}[request.method]
	# First, check to see if the caller has hung up.
	if ('CallStatus' in requestDataDict and requestDataDict['CallStatus'] == 'completed'):
			# check if we just got a callback number only
		if ('ivr2_Record_callbacknumber' in request.session):
			request.session['ivr2_only_callbacknumber'] = True
		# check if we got a recording before user hung up
		request.session['ivr_no_pound'] = True
		if ('RecordingUrl' in requestDataDict):
			request.session['ivr2_Record_recording'] = request.POST['RecordingUrl']
			request.session['ivr2_only_callbacknumber'] = False
			logger.debug('%s: _checkCallerHangUp got recording %s' %
				(request.session.session_key, request.session['ivr2_Record_recording']))
		else:
			if ('ivr2_Record_recording' in request.session):
				request.session['ivr2_only_callbacknumber'] = False
			else:
				request.session['ivr2_only_callbacknumber'] = True

		if ('ivr2_returnOnHangup' in request.session):
#			return_function = request.session['ivr2_returnOnHangup']
			view = request.session.get('ivr2_returnOnHangup', None)
			if view:
				logger.debug('%s: _checkCallerHangUp return to function %s' %
					(request.session.session_key, view))
				try:  # TODO: no more exec() but validation on view is needed
					mod, func = view.rsplit('.', 1)
					mod = import_module(mod)
					getattr(mod, func)(request)  # call the view function
				except Exception as e:
					subject = ''.join([('Problem calling view '), view])
					mail_admins(subject, str(e))
		# The user hung up. Return out and tell Twilio to do nothing.
		_getRecording_cleanup(request, resetPrompt=True)
		r = twilio.Response()
		logger.debug('%s: _checkCallerHangUp returning response to twilio' %
			(request.session.session_key))
		return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)
	else:
		return False


@TwilioAuthentication()
def getCallBackNumberNew(request, twilioResponse=None):
	"""
	Gets call back number from users input
	we use session variable ivr2_callback_step only within getCallBackNumber calls to
	decide what state within getCallBackNumber we are in
	Start getting callback number by asking caller to enter their callback number
	"""
	logger.debug('%s: getCallBackNumberNew POST data is %s' %
		(request.session.session_key, str(request.POST)))

	r = twilioResponse or twilio.Response()

	gather = twilio.Gather(finishOnKey='#', numDigits=12, timeout=30,
						action=reverse('getCallBackNumberAction'))
	gather.append(tts(_('On the keypad, please enter your call back number '
							'including area code now, then press pound.')))
	r.append(gather)
	r.append(twilio.Redirect(reverse('getCallBackNumberAction')))
	request.session['ivr2_callback_step'] = 1

	return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)


@TwilioAuthentication()
def getCallBackNumberAction(request, twilioResponse=None):
	"""
	After getting a call back number from users input:
	1. we get and repeat the number and ask the caller if this is correct
	2. get and process response from caller to accept callback number as correct or reenter,
	3. sends the number back to be used in msg or sms
	If caller hangs up, we return control to caller function
	"""
	logger.debug('%s: Into getCallBackNumberAction with call status %s' % (
		request.session.session_key, request.POST['CallStatus']))
	logger.debug('%s: getCallBackNumberAction POST data is %s' % (request.session.session_key, str(request.POST)))
	# if user hangs up, return control to caller function
	result = _checkCallerHangUp(request)

	r = twilioResponse or twilio.Response()
	if (not 'ivr2_callback_step' in request.session):
		# unknown state - repeat getCallBackNumberNew
		r.append(tts(_('I\'m sorry, I didn\'t understand that.')))
		return getCallBackNumberNew(request, r)

	if (request.session['ivr2_callback_step'] == 3):
		# we are done - return to caller
		nextState = _getNextRedirectState(request)
		logger.debug('%s: In getCallBackNumberAction step 3 state %s next %s callbacknumber is %s' % (
			request.session.session_key, request.session['ivr2_state'], nextState,
			request.session['ivr2_Record_callbacknumber']))
		r.append(twilio.Redirect(reverse(nextState)))
		return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)
	elif ('Digits' in request.POST):
		# other states require user to have entered digits
		digits = request.POST['Digits']
		if (request.session['ivr2_callback_step'] == 1):
			# first time through after user enters callback number
			if(re.match(r'[0-9]+', digits)):
				# we save and repeat the number to the user for verification
				request.session['ivr2_Record_callbacknumber'] = digits
				# take first three digits from caller, in case less than 10 digits are
				# entered, we do this for ALL calls where call back number is < 10 digits
				if (len(digits) < 10):
					if ('Caller' in request.session and len(request.session['Caller']) > 2):
						request.session['ivr2_caller_id_area_code'] = request.session['Caller'][0:3]

					#for bug 829, ONLY on FIRST pass, we need to make sure its at least 10 digits,
					# if not say please make sure you entered area code
					# only if this is URGENT call, rest of callers are free to leave any number of digits
					# also, if after first try, users still enters < 10 digits, let it
					# go thru (ivr2_urgent_flag var is used for that)
					if (not 'ivr2_urgent_flag' in request.session and 'ivr2_returnOnHangup'
						in request.session and request.session['ivr2_returnOnHangup'] ==
							'MHLogin.DoctorCom.IVR.views_practice_v2.PracticeIVR_LeaveUrgentMsg_New'):
						gather = twilio.Gather(finishOnKey='#', numDigits=12, timeout=30,
							action=reverse('getCallBackNumberAction'))
						r.append(tts('I\'m sorry, It appears your call back number '
							'is less than ten digits. Please enter your call back '
							'number including area code now. Then press pound.'))
						r.append(gather)
						r.append(twilio.Redirect(reverse('getCallBackNumberAction')))
						request.session['ivr2_urgent_flag'] = True
						return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)
					# end of bug 829
				# go to next step and request confirmation from caller
				if 'ivr2_urgent_flag' in request.session:
					del request.session['ivr2_urgent_flag']
				request.session['ivr2_callback_step'] = 2
				_sayCallBackNumber(request, r)
				return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)

			else:  # digits doesn't match multiple numbers
				return _returnCallBack(request, r)

		elif(request.session['ivr2_callback_step'] == 2):
			# second time through after entering callback number - confirm or reenter?
			if (not re.match('[0-9]$', digits)):
				# got something unexpected, start over
				request.session['ivr2_callback_step'] = 1
				return _returnCallBack(request, r)

			if (digits == '1'):
				# we got correct callback number number; go back to next state or calling function
				request.session['ivr2_callback_step'] = 3
				nextState = _getNextRedirectState(request)
				logger.debug('%s: In getCallBackNumberAction step 2 state %s next %s callbacknumber is %s' % (
					request.session.session_key, request.session['ivr2_state'], nextState,
					request.session['ivr2_Record_callbacknumber']))
				r.append(twilio.Redirect(reverse(nextState)))

			elif (digits == '3'):
				#user choose option to reenter callback number; go back 1 step
				request.session['ivr2_callback_step'] = 1
				del request.session['ivr2_Record_callbacknumber']
				if 'ivr2_caller_id_area_code' in request.session:
					del request.session['ivr2_caller_id_area_code']
				r.append(twilio.Redirect(reverse('getCallBackNumberAction')))

			else:
				r.append(tts('I\'m sorry, I didn\'t understand that.'))
				# say the number and request confirmation - state remains the same if ok, restart otherwise
				if ('ivr2_Record_callbacknumber' in request.session):
					_sayCallBackNumber(request, r)
				else:
					request.session['ivr2_callback_step'] = 1
					return _returnCallBack(request, r)

			return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)

	# if we got here, we start over
	return _returnCallBack(request, r)


@TwilioAuthentication()
def authenticateSessionNew(request, twilioResponse=None):
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
	if (not 'pin2_errCount' in request.session):
		request.session['pin2_errCount'] = 0

	if (request.method == 'POST' and 'Digits' in request.POST):
		logger.debug('%s: authenticateSessionNew POST is %s' % (
			request.session.session_key, str(request.POST)))

		call_sid = request.POST['CallSid']
		digits = request.POST['Digits']
		p = re.compile('\d{4,8}#?$')
		if (p.match(digits)):
			if (request.session.get('answering_service', None) == 'yes'):
				practice = PracticeLocation.objects.get(id=request.session['practice_id'])
				if (practice.verify_pin(digits)):
					request.session['authenticated'] = True
					r.append(twilio.Redirect(reverse(request.session['ivr2_state'])))
					request.session.modified = True
					return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)
			else:
				config_id = request.session['config_id']
				user = authenticate(config_id=config_id, pin=digits)
				if(user):
					# save session state since login will change state
					nextState = request.session['ivr2_state']
					login(request, user)
					uprivs = UserPrivateKey.objects.filter(user=user,
						credtype=CRED_IVRPIN, gfather=True)
					if uprivs.exists():
						config = VMBox_Config.objects.get(id=config_id)
						config.change_pin(request, new_pin=digits)
					request.session['authenticated'] = True
					event = callEvent(callSID=call_sid, event='V_ASU')
					event.save()
					r.append(twilio.Redirect(reverse(nextState)))
					request.session.modified = True
					response = HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)
					store_user_key(request, response, digits)
					return response

		event = callEvent(callSID=call_sid, event='V_AFL')
		event.save()

		r.append(tts('An in valid pin was entered.'))
		request.session['pin2_errCount'] += 1
		request.session.modified = True
		if (request.session['pin2_errCount'] >= 3):  # give the user three erroneous pin entries.
			r.append(tts('Good bye.'))
			r.append(twilio.Hangup())
			return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)

	# This is the code that gets executed on the first run of this function.
	gather = twilio.Gather(numDigits=8, action=reverse('authenticateSessionNew'))
	gather.append(tts(_("Please enter your pin number. Press pound to finish.")))
	r.append(gather)

	return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)


@TwilioAuthentication()
def getQuickRecordingNew(request, twilioResponse=None):
	"""Takes a quick recording from the user. This function uses the session dictionary
	at request.session for inputs and outputs. This is done in 2 parts:
	1. getQuickRecordingNew - packages the twilio request to get the message
	2. getQuickRecordingAction - twilio calls back with the recorded message
	   which we handle here.

	This function differs from getRecording in that strictly gets a quick
	recording from the user, without allowing the user to confirm that they wish
	to keep the recording. Used for leaving a name or a quick message
	"""
	logger.debug('%s: Into getQuickRecordingNew with state %s, call status %s POST %s' % (
		request.session.session_key, request.session['ivr2_state'],
		request.POST['CallStatus'], str(request.POST)))
	# in case caller hangs up on twilio fallthrough
	result = _checkCallerHangUp(request)
	# check if call ended, we are done
	if result:
		return result
	r = twilioResponse or twilio.Response()
	# Check for required values - first time pass to get recording
	if (not 'ivr2_Record_prompt_url' in request.session and
		not 'ivr2_Record_prompt_str' in request.session):
		raise Exception(_('Error. Required session key \'ivr2_Record_prompt_str_or_url\' '
						'undefined. Request.method is %s.') % (request.POST,))

	# Set up default values for get quick recording
	_getQuickRecordingDefaults(request)

	# Use this to keep track of if we've been through here before.
	if ('getQuickRecording_subsequentExcecution' in request.session):
		r.append(tts('Sorry, I didn\'t get that.'))
	request.session['getQuickRecording_subsequentExcecution'] = True
	request.session.modified = True

	if (request.session['ivr2_Record_leadSilence']):
		r.append(twilio.Pause(length=request.session['ivr2_Record_leadSilence']))
	if ('ivr2_Record_prompt_url' in request.session):
		r.append(twilio.Play(request.session['ivr2_Record_prompt_url']))
	if ('ivr2_Record_prompt_str' in request.session):
		r.append(tts(request.session['ivr2_Record_prompt_str']))
	r.append(twilio.Record(
					action=reverse('getQuickRecordingAction'),
					maxLength=request.session['ivr2_Record_maxLength'],
					finishOnKey=request.session['ivr2_Record_finishOnKey'],
					timeout=request.session['ivr2_Record_timeout'],
					playBeep=request.session['ivr2_Record_playBeep'],
					))
	# if we fall through without recording - we repeat instructions
	r.append(twilio.Redirect(reverse('getQuickRecordingNew')))
	return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)


@TwilioAuthentication()
def getQuickRecordingAction(request):
	"""
	Takes the recording from the user and saves into session variable for processing
	goes back to caller function via _getNextRedirectState
	"""
	logger.debug('%s: Into getQuickRecordingAction with call state %s status %s POST %s' % (
		request.session.session_key, request.session['ivr2_state'],
		request.POST['CallStatus'], str(request.POST)))

	# in case caller hangs up on twilio fallthrough - we still need to process the recording
	_checkCallerHangUp(request)

	r = twilio.Response()
	request.session.modified = True

	if (request.method == 'POST' and 'RecordingUrl' in request.POST):
		# otherwise, we save the recording if valid
		recording_url = request.POST['RecordingUrl']
		p1 = re.compile('http://api.twilio.com/\d{4}-\d{2}-\d{2}/Accounts/AC[0-9a-f]{32}/Recordings/RE[0-9a-f]{32}$')
		if (not p1.match(recording_url)):
			raise Exception(_('Recording url failed to match regex: %s') % (recording_url,))
		# save the recording url for later
		request.session['ivr2_Record_recording'] = recording_url
		request.session['ivr2_only_callbacknumber'] = False
		_getRecording_cleanup(request, resetPrompt=True)
		nextState = _getNextRedirectState(request)
		logger.debug('%s: Into getQuickRecordingAction state %s next %s recorded url is %s' % (
			request.session.session_key, request.session['ivr2_state'], nextState, recording_url))
		r.append(twilio.Redirect(reverse(nextState)))
		return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)
	else:
		if (request.POST['CallStatus'] == 'completed'):
			return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)
		else:
			return getQuickRecordingNew(request, r)


@TwilioAuthentication()
def getRecordingNew(request, twilioResponse=None):
	"""
	gets a longer recording and saves it to RecordingUrl in 3 steps:
	1. package prompt to user to leave a message via twilio
	2. get the recording and ask user to confirm or rerecord
	3. if confirm, we save the message and go back to caller function
	"""
	#sometimes first requests come from twilo as GET
	logger.debug('%s: Into getRecordingNew state %s POST %s' %
		(request.session.session_key, request.session['ivr2_state'], str(request.POST)))

	# in case caller hangs up on twilio fallthrough
	result = _checkCallerHangUp(request)
	# check if call ended, we are done
	if result:
		return result
	r = twilioResponse or twilio.Response()
	# Check for required values - the prompt for recording
	if (not 'ivr2_Record_prompt_url' in request.session and
		not 'ivr2_Record_prompt_str' in request.session):
		raise Exception(_('Error. Required session key \'ivr2_Record_prompt_str_or_url\' undefined.'))

	_getRecordingDefaults(request)
	if ('ivr2_Record_promptOnce' in request.session and
		request.session['ivr2_Record_promptOnce'] == True):
		if ('ivr2_Record_promptOnce_played' in request.session and
			request.session['ivr2_Record_promptOnce_played'] == False):
			request.session['ivr2_Record_promptOnce_played'] = True
			if ('ivr2_Record_prompt_url' in request.session):
				r.append(twilio.Play(request.session['ivr2_Record_prompt_url']))
			if ('ivr2_Record_prompt_str' in request.session):
				r.append(tts(request.session['ivr2_Record_prompt_str']))
	else:  # default case, we say the prompt
		if ('ivr2_Record_prompt_url' in request.session):
			r.append(twilio.Play(request.session['ivr2_Record_prompt_url']))
		if ('ivr2_Record_prompt_str' in request.session):
			r.append(tts(request.session['ivr2_Record_prompt_str']))
	if (request.session['ivr2_Record_leadSilence']):
		r.append(twilio.Pause(length=request.session['ivr2_Record_leadSilence']))

	r.append(twilio.Record(
					action=reverse('getRecordingAction'),
					maxLength=request.session['ivr2_Record_maxLength'],
					timeout=request.session['ivr2_Record_timeout'],
					finishOnKey=request.session['ivr2_Record_finishOnKey'],
					transcribe=request.session['ivr2_Record_transcribe'],
					playBeep=request.session['ivr2_Record_playBeep'],
					))
	# if user did not respond
	r.append(twilio.Redirect(reverse('getRecordingNew')))
	return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)


@TwilioAuthentication()
def getRecordingAction(request, twilioResponse=None):
	"""
	verifies recording is ok, ask for confirmation or repeat getRecordingNew
	"""
	logger.debug('%s: Into getRecordingAction state %s POST %s' % (
		request.session.session_key, request.session['ivr2_state'], str(request.POST)))

	# in case caller hangs up, we save recording etc, if any
	_checkCallerHangUp(request)
	r = twilioResponse or twilio.Response()
	if (request.method == 'POST' and 'RecordingUrl' in request.POST):
		recording_url = request.POST['RecordingUrl']
		p1 = re.compile('http://api.twilio.com/\d{4}-\d{2}-\d{2}/Accounts/AC[0-9a-f]{32}/Recordings/RE[0-9a-f]{32}$')
		if (not p1.match(recording_url)):
			raise Exception(_('Recording url failed to match regex: %s') % (recording_url,))

		# save the recording url for later
		request.session['ivr2_Record_recording'] = recording_url
		request.session['ivr2_only_callbacknumber'] = False
		logger.debug('%s: getRecordingAction recording url %s' % (
			request.session.session_key, str(recording_url)))
		return getRecording_getConfirmation(request, twilioResponse=r, playRecording=True)
	else:
		# didn't get recording url - go to getRecording
		logger.debug('%s: In getRecordingAction without recording url. Go back to getRecordingNew' % (
			request.session.session_key))
		return getRecordingNew(request, r)


@TwilioAuthentication()
def getRecording_getConfirmation(request, twilioResponse, playRecording=False):
	"""
	ask for confirmation or to rerecord
	"""
	r = twilioResponse or twilio.Response()
	logger.debug('%s: getRecording_getConfirmation play %s' % (
		request.session.session_key, request.session['ivr2_Record_recording']))
	gather = twilio.Gather(numDigits=1, finishOnKey='', action=reverse('getRecordingConfirm'))
	if (playRecording):
		gather.append(tts(_("You said")))
		gather.append(twilio.Play(request.session['ivr2_Record_recording']))
	gather.append(tts(_('If you wish to record again, please press three. '
				'Press one to continue. Press any other key to replay the recording.')))
	r.append(gather)
	# if fallthrough
	r.append(twilio.Redirect(reverse('getRecordingConfirm')))
	return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)


@TwilioAuthentication()
def getRecordingConfirm(request, twilioResponse=None):
	"""
	verifies recording is ok
	"""
	logger.debug('%s: getRecordingConfirm state %s POST %s ' % (
		request.session.session_key, request.session['ivr2_state'], str(request.POST)))
	_checkCallerHangUp(request)
	r = twilioResponse or twilio.Response()
	if ('ivr2_Record_recording' in request.session):
		if (request.method == 'POST' and 'Digits' in request.POST):
			digits = request.POST['Digits']
			p2 = re.compile('[0-9*#]$')
			if (not p2.match(digits)):
				raise Exception('')

			if (digits == '1'):
				# User accepted the recording.
				_getRecording_cleanup(request, resetPrompt=True)
				logger.debug('%s: getRecordingConfirm accepted recording. State is %s' % (
					request.session.session_key, request.session['ivr2_state']))
				return saveRecordingReturn(request)
			if (digits == '3'):
				del request.session['ivr2_Record_recording']
				logger.debug('%s: getRecordingConfirm rejected recording. Going to getRecording' % (
					request.session.session_key))
				return getRecordingNew(request, r)
			else:
				logger.debug('%s: getRecordingConfirm did not get correct digit %s. Retry confirm.' % (
					request.session.session_key, digits))
				return getRecording_getConfirmation(request, r, True)
		else:
			logger.debug('%s: getRecordingConfirm did not get digits. Retry confirm.' % (
				request.session.session_key))
			return getRecording_getConfirmation(request, r, False)
	else:
		#start over
		logger.debug('%s: getRecordingConfirm did not find ivr2_Record_recording. Restart' % (
			request.session.session_key))
		return getRecordingNew(request, r)


def _getQuickRecordingDefaults(request):
	"""
	default values to pass to twilio to get a quick recording
	"""
	# Set up default values
	if (not 'ivr2_Record_maxLength' in request.session):
		request.session['ivr2_Record_maxLength'] = 5
	if (not 'ivr2_Record_timeout' in request.session):
		request.session['ivr2_Record_timeout'] = 6
	if (not 'ivr2_Record_leadSilence' in request.session):
		request.session['ivr2_Record_leadSilence'] = 1
	if (not 'ivr2_Record_playBeep' in request.session):
		request.session['ivr2_Record_playBeep'] = True
	if (not 'ivr2_Record_finishOnKey' in request.session):
		request.session['ivr2_Record_finishOnKey'] = '1234567890*#'


def _getRecordingDefaults(request):
	"""
	default values to pass to twilio to get a recording
	"""
	logger.debug('%s: _getRecordingSetupDefaults' % (request.session.session_key))
	# Set up default values - prompt is required
	if (not 'ivr2_Record_promptOnce' in request.session):
		request.session['ivr2_Record_promptOnce'] = False
	if (not 'ivr2_Record_maxLength' in request.session):
		request.session['ivr2_Record_maxLength'] = 180
	if (not 'ivr2_Record_timeout' in request.session):
		request.session['ivr2_Record_timeout'] = 5
	if (not 'ivr2_Record_transcribe' in request.session):
		request.session['ivr2_Record_transcribe'] = False
	if (not 'ivr2_Record_finishOnKey' in request.session):
		request.session['ivr2_Record_finishOnKey'] = '1234567890*#'
	if (not 'ivr2_Record_playBeep' in request.session):
		request.session['ivr2_Record_playBeep'] = True
	if (not 'ivr2_Record_leadSilence' in request.session):
		request.session['ivr2_Record_leadSilence'] = 0
	if (not 'ivr2_returnOnHangup' in request.session):
		request.session['ivr2_returnOnHangup'] = None
	if (not 'ivr2_Record_promptOnce_played' in request.session):
		request.session['ivr2_Record_promptOnce_played'] = False


def _getRecording_cleanup(request, resetPrompt=False):
	"""
	cleanup makeRecording values set up in the session to get a recording
	"""
	logger.debug('%s: in _getRecording_cleanup reset %s' % 
		(request.session.session_key, resetPrompt))
	if resetPrompt:
		request.session.pop('ivr2_Record_prompt_url', None)
		request.session.pop('ivr2_Record_prompt_str', None)
	request.session.pop('ivr2_Record_maxLength', None)
	request.session.pop('ivr2_Record_timeout', None)
	request.session.pop('ivr2_Record_transcribe', None)
	request.session.pop('ivr2_Record_finishOnKey', None)
	request.session.pop('ivr2_Record_playBeep', None)
	request.session.pop('ivr2_Record_leadSilence', None)
	request.session.pop('ivr2_returnOnHangup', None)
	request.session.pop('ivr2_Record_promptOnce', None)
	request.session.pop('ivr2_Record_promptOnce_played', None)
	request.session.pop('getQuickRecording_subsequentExcecution', None)


@TwilioAuthentication()
def changeNameNew(request, prependPrompt=''):
	"""
	Requests the user record their name and stores it in the config with id
	at request.session['config_id'].

	:param request: the usual Django view argument
	:param prependPrompt: The string to prepend to the start of the request. Note
		that sending None will result in an error. If you don't wish to
		prepend anything explicitly, please pass in an empty string.
	:returns: django.http.HttpResponse -- the result
	This is done in 2 steps:
	1. get the recording of a name
	2. replay to user and ask for confirmation or replay
	3. saves the recording with the associated provider or practice
	"""
	# for now, this called from either ProviderIVR_Options_1 or ProviderIVR_Setup_1
	# or PracticeIVR_Setup or PracticeIVR_Options to record a name - not called directly otherwise
	logger.debug('%s: changeNameNew state %s' % (request.session.session_key, request.session['ivr2_state']))
	assert(request.session['ivr2_state'])
	request.session['ivr2_Record_prompt_str'] = prependPrompt + " Please say your name after the tone. Press pound to finish."
	request.session['ivr2_Record_maxLength'] = 10
	request.session['ivr2_Record_timeout'] = 3
	return getRecordingNew(request)


@TwilioAuthentication()
def changeNameConfirm(request):
	"""Requests the user record their name and stores it in the config with id
	at request.session['config_id'].

	:param request: the usual Django view argument
	:param prependPrompt: The string to prepend to the start of the request. Note
		that sending None will result in an error. If you don't wish to
		prepend anything explicitly, please pass in an empty string.
	:returns: django.http.HttpResponse -- the result
	"""
	logger.debug('%s: changeNameConfirm POST data is %s' % (request.session.session_key, str(request.POST)))
#	logger.debug('%s: changeNameConfirm META data is %s' % (request.session.session_key, str(request.META)))
	if ('ivr2_Record_recording' in request.session):
		if (request.session.get('answering_service', None) == 'yes'):
			practice = PracticeLocation.objects.get(id=request.session['practice_id'])
			practice.name_greeting = request.session['ivr2_Record_recording']
			del request.session['ivr2_Record_recording']
			practice.save()
		else:
			cid = request.session['config_id']
			logger.debug('%s: changeNameConfirm updating config %s' % (
				request.session.session_key, cid))
#			import pdb; pdb.set_trace()
			config = VMBox_Config.objects.get(id=request.session['config_id'])
			config.name = request.session['ivr2_Record_recording']
			del request.session['ivr2_Record_recording']
			config.save()

		event = callEvent(callSID=request.POST['CallSid'], event='F_NCH')
		event.save()

		r = twilio.Response()
		nextUrl = _getNextRedirectState(request)
		logger.debug('%s: changeNameConfirm redirect to %s' % (request.session.session_key, nextUrl))
		r.append(twilio.Redirect(reverse(nextUrl)))
		request.session.modified = True
		return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)
	else:
		return changeNameNew(request)


@TwilioAuthentication()
def changeGreetingNew(request, prependPrompt=''):
	"""Requests the user record their greeting and stores it in the config with id
	at request.session['config_id'].

	:param request: the usual Django view argument
	:param prependPrompt: The string to prepend to the start of the request. Note
		that sending None will result in an error. If you don't wish to
		prepend anything explicitly, please pass in an empty string.
	:returns: django.http.HttpResponse -- the result
	"""
	logger.debug('%s: changeGreetingNew' % (request.session.session_key))
	#make twilio say different things based on who called it, prepend seemed to
	#be never used, i will investigate later and see why not to use it
	if (request.session.get('answering_service', None) == 'yes'):
		if ('ivr2_sub_state' in request.session and request.session['ivr2_sub_state'] == 'PracticeIVR_Setup_3'):
			request.session['ivr2_Record_prompt_str'] = prependPrompt + "Please say your new greeting for closed office after the tone. Press pound to finish."
		else:
			request.session['ivr2_Record_prompt_str'] = prependPrompt + "Please say your new greeting for temporarily closed office after the tone. Press pound to finish."
	else:
		request.session['ivr2_Record_prompt_str'] = prependPrompt + "Please say your new greeting after the tone. Press pound to finish."

	request.session['ivr2_Record_maxLength'] = 120
	request.session['ivr2_Record_timeout'] = 3
	# need to figure out how to tell getRecordings where to come back to
	return getRecordingNew(request)


@TwilioAuthentication()
def changeGreetingConfirm(request):
	"""Requests the user record their greeting and stores it in the config with id
	at request.session['config_id'].
	"""
	logger.debug('%s: changeGreetingConfirm POST data is %s' % (request.session.session_key, str(request.POST)))
	if ('ivr2_Record_recording' in request.session):
		if (request.session.get('answering_service', None) == 'yes'):
			practice = PracticeLocation.objects.get(id=request.session['practice_id'])
			if ('ivr2_sub_state' in request.session and
				request.session['ivr2_sub_state'] == 'PracticeIVR_Setup_3'):
				practice.greeting_closed = request.session['ivr2_Record_recording']
			else:
				practice.greeting_lunch = request.session['ivr2_Record_recording']
			del request.session['ivr2_Record_recording']
			practice.save()
		else:
			config = VMBox_Config.objects.get(id=request.session['config_id'])
			config.greeting = request.session['ivr2_Record_recording']
			del request.session['ivr2_Record_recording']
			config.save()

		event = callEvent(callSID=request.POST['CallSid'], event='F_GCH')
		event.save()

		r = twilio.Response()
		nextUrl = _getNextRedirectState(request)
		logger.debug('%s: changeGreetingConfirm redirect to %s' % (request.session.session_key, nextUrl))
		r.append(twilio.Redirect(reverse(nextUrl)))
		request.session.modified = True
		return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)
	else:
		return changeGreetingNew(request)


@TwilioAuthentication()
def callBackUserNew(request, message):
	"""
	called by play_Messages, given a message with callback number, create twilio request to callback
	need to specify:
	. where we go once the call ends (set in dial actionURL)
	. if call is not answered or dial encountered error - redirectUrl
	At the end, we go back to playMessagesNew (since it is called from there)
	"""
	callerId = Provider.objects.get(id=request.session['provider_id']).mdcom_phone
	logger.debug('%s: GenericIVR_callBackUserNew is called with caller %s' % (
		request.session.session_key, callerId))
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
		# if callback is to a provider - we forward the call
		from views_provider_v2 import ProviderIVR_OutsideInit_New, ProviderIVR_ForwardCall_New
		provider = provider_qs.get()
		ProviderIVR_OutsideInit_New(request, log.caller_number, provider, log)
		return ProviderIVR_ForwardCall_New(request)

	# need actionURL for dial and redirect after for Dial falling through
	dial = twilio.Dial(message.callback_number,
				action=reverse('playMessagesNew'),
				callerId=callerId,
				timeout=120)
	r.append(dial)
	CallbackLog(message=message).save()
	r.append(twilio.Redirect(reverse('playMessagesNew')))
	return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)


@TwilioAuthentication()
def playMessagesNew(request, msgs_querySet=None, playFlag=True, replayFlag=False, twilioResponse=None):
	"""
	Start of playing messages passed in through msgs_querySet
	setup messages and session state;
	gets a message to play and gives the menu tree to act on messages as follows:
	gets the next message and puts it in the twilio response
	firstTime - used to say if we are playing the first message
	playFlag - used to indicate if we want to get next message or use existing message
	replayFlag - used to say if we want to replay the current message
	assumptions:
	messages are stored in session variables:
	ivr2_playMessages_newMessages - new message queue initialized with msgs_querySet in playMessagesNew
	ivr2_playMessages_oldMessages - old message queue initialized with msgs_querySet in playMessagesNew
	ivr2_playMessages_currentMsg - current message being played
	"""
	logger.debug('%s: playMessagesNew playFlag %s replay %s' % 
		(request.session.session_key, playFlag, replayFlag))
	call_sid = request.POST['CallSid']
	firstTime = False
	if (msgs_querySet):
		firstTime = True
		request.session['ivr2_playMessages_newMessages'] = list(msgs_querySet.filter(
			read_flag=False, delete_flag=False).order_by('msg_body__message__message_type',
					'-msg_body__message__send_timestamp').all())
#		if (len(request.session['ivr2_playMessages_newMessages'])):
#			request.session['ivr2_playMessages_newMsgsFlag'] = True
		request.session['ivr2_playMessages_oldMessages'] = list(msgs_querySet.filter(
			read_flag=True, delete_flag=False).order_by('msg_body__message__message_type',
					'-msg_body__message__send_timestamp').all())
		# We're pretty much always going to be manipulating the session.
		request.session.modified = True
		logger.debug('%s: playMessagesNew first time newmsgs %d oldmsgs %d' % 
			(request.session.session_key, len(request.session['ivr2_playMessages_newMessages']),
				len(request.session['ivr2_playMessages_oldMessages'])))

	r = twilioResponse or twilio.Response()
	# we decide what to tell the user with the message
	# each iteration of this call, we decide to put a message to current from either
	# ivr2_playMessages_newMessages or ivr2_playMessages_oldMessages lists
	# the current msg is stored in session var: ivr2_playMessages_currentMsg
	if (replayFlag):
		r.append(tts('Re-playing message'))
	elif (not playFlag):
		# don't move to next message - keep current msg as it is
		pass
	elif (len(request.session['ivr2_playMessages_newMessages'])):
		if (firstTime):
			r.append(tts('Playing the first new message'))
		else:
			r.append(tts('Playing the next new message'))
		logger.debug('%s: playMessagesNew newmsg ' % (request.session.session_key))
		request.session['ivr2_playMessages_currentMsg'] = request.session['ivr2_playMessages_newMessages'].pop(0)
		logger.debug('%s: playMessagesNew newmsg %s' % 
			(request.session.session_key, request.session['ivr2_playMessages_currentMsg']))
		event = None
		if(request.session['ivr2_playMessages_currentMsg'].msg_body.message.message_type == 'ANS'):
			event = callEvent(callSID=call_sid, event='V_NAP')
			event.save()
		else:
			event = callEvent(callSID=call_sid, event='V_NMP')
			event.save()
		target = callEventTarget(event=event, target=request.session['ivr2_playMessages_currentMsg'])
		target.save()
		request.session['ivr2_playMessages_currentMsg'].read_flag = True
		request.session['ivr2_playMessages_currentMsg'].save()
	elif (len(request.session['ivr2_playMessages_oldMessages'])):
		if (firstTime):
			r.append(tts('Playing the first old message'))
		else:
			r.append(tts('Playing the next old message'))
		request.session['ivr2_playMessages_currentMsg'] = request.session['ivr2_playMessages_oldMessages'].pop(0)
		logger.debug('%s: playMessagesNew oldmsg %s' % 
			(request.session.session_key, request.session['ivr2_playMessages_currentMsg']))
		event = None
		if(request.session['ivr2_playMessages_currentMsg'].msg_body.message.message_type == 'ANS'):
			event = callEvent(callSID=call_sid, event='V_OAP')
			event.save()
		else:
			event = callEvent(callSID=call_sid, event='V_OMP')
			event.save()
		target = callEventTarget(event=event, target=request.session['ivr2_playMessages_currentMsg'])
		target.save()
	else:
		logger.debug('%s: playMessagesNew end of msgs' % (request.session.session_key))
		r.append(tts('End of messages'))
		# need to check if we can do this for all callers to playMessagesNew
		nextUrl = _getNextRedirectState(request)
		r.append(twilio.Redirect(reverse(nextUrl)))
		# TODO: do we need to clear session variables from old messages here?
		return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)

	# we now get the msg to send to twilio
	gather = twilio.Gather(finishOnKey='', numDigits=1, 
		action=reverse('playMessagesAction'))
	# gets next message to be played - if needed
	if (playFlag):
		url = ''
		if (request.session['ivr2_playMessages_currentMsg'].msg_body.message.message_type == 'ANS'):
			spoken_number = []
			digits = request.session['ivr2_playMessages_currentMsg'].msg_body.message.callback_number
			[spoken_number.extend([i, ' ']) for i in digits]
			spoken_number.pop()  # drop the last element
			#spoken_number.insert(5, ',')
			#spoken_number.insert(12, ',')
			gather.append(tts('Call from %s .' % (''.join(spoken_number),)))
		msg = request.session['ivr2_playMessages_currentMsg'].msg_body.message
		logger.debug('%s: playMessagesNew playing msg %s' % 
			(request.session.session_key, str(msg)))
		try:
			uuid = MessageAttachment.objects.get(message=msg).uuid
			url = reverse("fetchRecording", kwargs={"uuid": uuid})
			logger.debug('%s: playMessagesNew msg url %s' % 
				(request.session.session_key, url))
			gather.append(twilio.Play(url))
		except MessageAttachment.DoesNotExist:
			errors = {
				'U': _("User hung up before confirming number."),
				'C': _("User hung up before leaving message."),
				'R': _("An error occurred downloading the recording. We will retry until "
					"successful and you will receive a new message at that time."),
			}
			gather.append(tts(errors[msg.vmstatus]))

	gather.append(twilio.Pause(length=1))
	gather.append(tts(_('Press 1 to move to the next message. ')))
	gather.append(tts(_('Press 3 to re-play the message. ')))
	callback_number = request.session['ivr2_playMessages_currentMsg'].msg_body.message.callback_number
	logger.debug('%s: playMessagesNew callback %s' % 
		(request.session.session_key, str(callback_number)))
	if(re.match("1?\d{10}", callback_number)):
		gather.append(tts(_('Press 5 to call this person back. ')))
	gather.append(tts(_('Press 7 to mark the message resolved and hide it. ')))
	gather.append(tts(_('Press 9 to return to the main menu. ')))
	r.append(gather)
	return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)


@TwilioAuthentication()
def playMessagesAction(request, twilioResponse=None):
	"""
	when we get here, we are called from twilio after we play a message and the user selected an option
	"""
	playFlag = True
	replayFlag = False
	logger.debug('%s: playMessagesAction digits %s state %s' % (
		request.session.session_key, request.POST['Digits'], request.session['ivr2_state']))
	call_sid = request.POST['CallSid']
	r = twilioResponse or twilio.Response()
	if (request.method == 'POST' and 'Digits' in request.POST):
		digits = request.POST['Digits']
		p = re.compile('[0-9#*]$')
		if (not p.match(digits)):
			r.append(tts('I\'m sorry, I didn\'t understand that.'))
			playFlag = False
		if (digits == '1'):
			# do nothing - move to next message
			pass
		elif (digits == '3'):
			# replay mesage - don't move to next msg
			replayFlag = True
		elif (digits == '5'):
			# callback caller
			return callBackUserNew(request, request.session['ivr2_playMessages_currentMsg'].msg_body.message)
		elif (digits == '7'):
			# mark resolved -- sets the 'deleted' flag to hide the message.
			r.append(tts('Message resolved'))
			event = callEvent(callSID=call_sid, event='V_MDL')
			event.save()
			target = callEventTarget(event=event, target=request.session['ivr2_playMessages_currentMsg'])
			target.save()
			request.session['ivr2_playMessages_currentMsg'].msg_body.message.resolved_by = request.user
		elif (digits == '9'):
			# return to main menu		
			nextUrl = _getNextRedirectState(request)
			r.append(twilio.Redirect(reverse(nextUrl)))
			return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)
		else:
			r.append(tts('I\'m sorry, I didn\'t understand that.'))
#			playFlag = False
			replayFlag = True
		return playMessagesNew(request, None, playFlag, replayFlag, r)
	else:
		# posted but no digits
		logger.debug('%s: playMessagesAction is called with no post or digits' % (
			request.session.session_key))
		r.append(tts('I\'m sorry, I didn\'t understand that.'))
		playFlag = False
		return playMessagesNew(request, None, playFlag, replayFlag, r)





