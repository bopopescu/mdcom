
import json
import re
from pytz import timezone
from datetime import datetime
from twilio import twiml as twilio

from django.contrib.auth.models import User
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.template.loader import render_to_string
from twilio import TwilioRestException
from twilio.rest.resources import make_twilio_request

from models import callLog, callEvent
from views_generic import authenticateSession, changePin, changeName
from views_generic import changeGreeting, getCallBackNumber
from views_generic import getQuickRecording

from utils import save_answering_service_message, create_dynamic_greeting, create_call_group_list
from django.conf import settings

from MHLogin.DoctorCom.speech.utils import tts
from MHLogin.MHLUsers.models import MHLUser, Provider, OfficeStaff
from MHLogin.MHLUsers.utils import get_all_practice_managers
from MHLogin.utils.decorators import TwilioAuthentication
from MHLogin.utils.mh_logging import get_standard_logger 
from MHLogin.utils.admin_utils import mail_admins

from MHLogin.MHLPractices.models import PracticeLocation
from MHLogin.MHLPractices.utils import message_managers

from MHLogin.MHLCallGroups.Scheduler.utils import getPrimaryOnCall, getLastPrimaryOnCall
from MHLogin.utils.twilio_utils import client2008 as client

from django.utils.translation import ugettext as _


#list practice numbers that will roll over to temp closed instead of opened after X rings
SPECIAL_PRACTICE = [3]


# Setting up logging
logger = get_standard_logger('%s/DoctorCom/IVR/views_practice.log' % (settings.LOGGING_ROOT), 
							'DCom.IVR.views_practice', settings.LOGGING_LEVEL)


@TwilioAuthentication()
def PracticeIVR_Init(request):
	"""
	Initialize stack, caller, caller, housekeeping when first call enters our system
	This method is a block of copied code again :-(, with minor changes
	"""
	request.session['answering_service'] = 'yes'
	# First, make sure that the call stack is initialized:
	if (not 'ivr_call_stack' in request.session):
		request.session['ivr_call_stack'] = []

	caller = request.POST['Caller']
	called = request.POST['Called']

	# Now, get the Practice being called
	try:
		practice = PracticeLocation.objects.get(mdcom_phone=called)
	except MultipleObjectsReturned:
		raise Exception(_('Multiple Practice Locations have mdcom_phone %s') % (called,))
	except ObjectDoesNotExist:
		raise Exception(_('No Practice Location have mdcom_phone %s') % (called,))

	#  Next, check for and store caller and called.
	if (not 'caller' in request.session or not 'called' in request.session):
		# Note: Twilio's international caller ID is just the full international
		# number all run together. For example, an international call from England
		# would be passed to us as 44XXXXXXXXXX, where 44 is the international
		# country code.
		# TODO: This sanitation could be much more sophisticated, albeit at the
		# risk of making future maintenance more difficult. I think that at the
		# moment, we're going to have to just accept that the caller ID we get from
		# Twilio is a trusted value.
		log_qs = callLog.objects.filter(callSID=request.POST['CallSid'])
		if (log_qs.count()):
			log = log_qs.get()
		else:
			log = callLog(
					caller_number=caller,
					called_number=called,
					callSID=request.POST['CallSid'],
					call_source='OC',
					mdcom_called=practice
				)
			log.save()

		p = re.compile('\d+$')
		if (not p.match(caller)):
			if (caller != '' and caller != None):
				subject = _('PracticeIVR_Main Incoming CallerID Sanitation Fail')
				message = _('PracticeIVR_Main incoming CallerID failed on input %s.') % (caller,)
				mail_admins(subject=subject, message=message, fail_silently=False)
			caller = ''
		if (not p.match(called)):
			# The number being called doesn't seem to be valid. Since we can't find
			# out which provider is being called, just raise an Exception and let
			# Django and Twilio deal with it.
			raise Exception(_('Invalid called value: %s') % (called,))

		request.session['Caller'] = caller
		request.session['Called'] = called

	#request.session['practice'] = practice #removed, look up practice by id as needed, 
	# do not store objects in the session
	request.session['practice_id'] = practice.id
	if (practice.uses_original_answering_serice()): 
		# ONLY for V 1 groups, for V2 determine based on user selection later
		request.session['callgroup_id'] = practice.call_group.id
	request.session['practice_phone'] = practice.practice_phone
	request.session['ivr_only_callbacknumber'] = False
	# Is the caller an existing user with a DoctorCom number? If so, mask the
	# caller's number with the DoctorCom number.
	mhlusers_mobile_phone = MHLUser.objects.filter(mobile_phone=request.session['Caller'])
	mhlusers_phone = MHLUser.objects.filter(phone=request.session['Caller'])
	total_users = mhlusers_mobile_phone.count() + mhlusers_phone.count()
	if (total_users == 1):
		# First, get the MHLUser involved.
		if (mhlusers_mobile_phone.count()):
			user = mhlusers_mobile_phone.get()
		else:
			user = mhlusers_phone.get()

		provider_qs = Provider.objects.filter(user=user)
		if (provider_qs.count()):
			provider = provider_qs.get(user=user)
			if (provider.mdcom_phone):
				# Mask the caller's caller ID since they have a doctorcom number
				request.session['Caller'] = provider.mdcom_phone
	return practice


@TwilioAuthentication()
def PracticeIVR_Setup(request):
	"""
	This function is heavily dependent upon request.session; Twilio is kind
	enough to keep session cookies for us.
	setting up doctor com answering service greetings and pin
	"""
	if ('CallStatus' in request.POST and request.POST['CallStatus'] == 'completed'):
		# call ended
		#raise Exception('Ending inappropriately. Call stack is %s'%(str(
				#request.session['ivr_call_stack']),)) # DEBUG
		r = twilio.Response()
		return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)
	elif (not 'CallStatus' in request.POST):
		# call ended
		#raise Exception('Ending inappropriately. Call stack is %s'%(str(
				#request.session['ivr_call_stack']),)) # DEBUG
		r = twilio.Response()
		return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)

	if 'ivr_setup_stage' not in request.session:
		# Okay, this is the first time this function is being executed for this call.

		#raise Exception(request.session['ivr_call_stack']) # DEBUG

		r = twilio.Response()

		# Set up our session variables.
		request.session['ivr_setup_stage'] = 1
		request.session['ivr_call_stack'].append('PracticeIVR_Setup')
		request.session.modified = True

		#will need to Practice Location and see if this needs set up and values that are there already

		r.append(twilio.Pause())  # one second pause keeps the first words from getting cut off.
		r.append(tts(_("Welcome to your voicemail account. It looks like some "
							"setup is needed. Let's get started.")))
		r.append(tts(_("First, we need to set up your pin number.")))

		return changePin(request, r, True)
	elif (request.session['ivr_setup_stage'] == 1):  # Record name
		request.session['ivr_call_stack'].append('PracticeIVR_Setup')
		request.session.modified = True
		request.session['ivr_setup_stage'] = 2

		return changeName(request, 'Now, we need to record your office name.')

	elif (request.session['ivr_setup_stage'] == 2):  # Record a greeting
		request.session['ivr_call_stack'].append('PracticeIVR_Setup')
		request.session.modified = True
		request.session['ivr_setup_stage'] = 3

		return changeGreeting(request, _('Next, we need to set up your answering service '
							'greeting. This will be played when the office is closed.'))

	elif (request.session['ivr_setup_stage'] == 3):  # Record a greeting
		request.session['ivr_call_stack'].append('PracticeIVR_Setup')
		request.session.modified = True
		request.session['ivr_setup_stage'] = 4

		return changeGreeting(request, _('Finally, we need to set up a greeting that '
										'will be played when the office is open.'))
	elif (request.session['ivr_setup_stage'] == 4):  # Configuration complete!
		#store new information in Practice Locations
		practice = PracticeLocation.objects.get(id=request.session['practice_id'])
		practice.config_complete = True
		practice.save()

		r = twilio.Response()
		r.append(tts(_('Your voice mail account is now set up. You may hang up now.')))

		r.append(twilio.Redirect(reverse(request.session['ivr_call_stack'].pop())))
		request.session.modified = True
		return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)

	raise Exception(_('Reached the end of PracticeIVR_Setup. This should never happen.'))


@TwilioAuthentication()
def PracticeIVR_CallerResponse(request, twilioResponse=None):
	"""
	This function process callers response, 
	1=leave msg in doc com mailbox, 
	2=page doctor on call
	"""
	practice = PracticeLocation.objects.get(id=request.session['practice_id'])
	r = twilioResponse or twilio.Response() 

	if ('Digits' in request.POST):
		digits = request.POST['Digits']
		p = re.compile('[0-9#*]$')
		if (not p.match(digits)):
			r.append(tts(_('I\'m sorry, I didn\'t understand that.')))
		elif (digits == '1'):
			# leave msg in doctor com mailbox
			request.session['ivr_call_stack'].append('PracticeIVR_CallerResponse')
			request.session.modified = True
			return PracticeIVR_LeaveRegularMsg(request)
		elif (digits == '2'):
			request.session['ivr_call_stack'].append('PracticeIVR_CallerResponse')
			request.session.modified = True
			request.session['provider_id'] = _getRecentOncallProvider(request).id
			if(not request.session['provider_id']):
				r.append(tts(_('We\'re sorry, an application error has '
										'occurred. Goodbye.', voice='woman')))
				r.append(twilio.Hangup())
				return r
			return PracticeIVR_ForwardCall(request)
		elif (digits == '*'):
			pass
		else:
			r.append(tts(_('I\'m sorry, I didn\'t understand that.')))

	gather = twilio.Gather(finishOnKey='', numDigits=1, timeout=60)

	if (not 'practice_greeting' in request.session):
		if (practice.is_open()):
			request.session['practice_greeting'] = practice.greeting_lunch
		else:
			request.session['practice_greeting'] = practice.greeting_closed
	if (practice.skip_to_rmsg and practice.is_open()):
		r.append(twilio.Play(request.session['practice_greeting']))
		r.append(twilio.Redirect(reverse('PracticeIVR_LeaveRegularMsg')))
	else:
		gather.append(twilio.Play(request.session['practice_greeting']))
		r.append(gather)

	return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)


@TwilioAuthentication()
def PracticeIVR_V2_CallerResponse(request, twilioResponse=None):
	"""
	This function process callers response,
	1=leave msg in doc com mailbox,
	create greeting based on call_groups info in db
	if 1 call group  for THIS practice, take message,
	if > 1 call group, add a layer to first pick call group, then pick type of message
	"""
	practice = PracticeLocation.objects.get(id=request.session['practice_id'])

	r = twilioResponse or twilio.Response()
	gather = twilio.Gather(finishOnKey='', numDigits=1, timeout=60)	 	

	#first iteration on options , fall into this statement IF 'callgroup_id' NOT in request.session
	if ('Digits' in request.POST):
		digits = request.POST['Digits']
		call_groups_map = request.session['call_groups_map']
		specialties_map = request.session['specialties_map']

		p = re.compile('[0-9]$')
		if (not p.match(digits)):
			gather.append(tts(_('I\'m sorry, I didn\'t understand that.')))
			gather.append(tts(_('%s.') % (''.join(request.session['last_played']),)))
			r.append(gather)

		elif (digits == '1' and request.session['one_ok'] == '1'):
			# leave msg in doctor com mailbox
			request.session['ivr_call_stack'].append('PracticeIVR_V2_CallerResponse')
			request.session.modified = True
			return PracticeIVR_LeaveRegularMsg(request)

		elif (digits in call_groups_map):
			#Call Group reached, get provider on call
			request.session['callgroup_id'] = call_groups_map.get(digits)
			request.session['ivr_call_stack'].append('PracticeIVR_V2_CallerResponse')
			request.session.modified = True
			request.session['provider_id'] = _getRecentOncallProvider(request).id
			if(not request.session['provider_id']):
				r.append(tts(_('We\'re sorry, an application error has '
										'occurred. Goodbye.', voice='woman')))
				r.append(twilio.Hangup())
				return r
			return PracticeIVR_ForwardCall(request)
		elif (digits in specialties_map):
			#specialty reached, get list of call groups, 
			#populates request.session['call_groups_map'] and blanks out request.session['specialty_map'] 
			call_groups_greeting = create_call_group_list(request, specialties_map.get(digits)) 
			gather.append(tts(_(call_groups_greeting)))	
			request.session['last_played'] = call_groups_greeting
			r.append(gather)
		#elif (digits == '*'): treat * as invalid input
			#pass
		else:
			gather.append(tts(_('I\'m sorry, I didn\'t understand that.')))
			gather.append(tts(_('%s.') % (''.join(request.session['last_played']),)))
			r.append(gather)

		return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)

	if (not 'practice_greeting' in request.session):
		if (practice.is_open()):
			request.session['practice_greeting'] = practice.greeting_lunch
		else:
			request.session['practice_greeting'] = practice.greeting_closed
	if(practice.skip_to_rmsg and practice.is_open()):
		r.append(twilio.Play(request.session['practice_greeting']))
		r.append(twilio.Redirect(reverse('PracticeIVR_LeaveRegularMsg')))
	else:
		#layer 1 greeting, it recites call group lists, 
		#populates  request.session['call_groups_map'] and request.session['specialty_map']
		dynamic_greeting = create_dynamic_greeting(request, practice)

		gather.append(twilio.Play(request.session['practice_greeting']))
		gather.append(tts(_('%s.') % (''.join(dynamic_greeting),)))
		request.session['last_played'] = dynamic_greeting
		r.append(gather)

	return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)


def _getRecentOncallProvider(request):
	if 'ivr_provider_onCall' in request.session:
		return request.session['ivr_provider_onCall']

	call_time = request.session['calltime_local']
	call_time_string = request.session['calltime_local_string']
	callGroupId = request.session['callgroup_id']
	#which provider is on call right now?
	oncall_qs = getPrimaryOnCall(callGroupId, call_time_string)
	oncall_count = len(oncall_qs)
	callback = ''
	provider = None
	if (oncall_count == 0):
		provider_qs = getLastPrimaryOnCall(callGroupId, call_time_string)
		if (not provider_qs):
			message_managers(request, request.session['practice_id'],
						'DoctorCom Error: No On-Call User Defined',
						render_to_string("DoctorCom/IVR/no_oncall_error.txt", {
							'timestamp': call_time,
							'callsid': request.POST['CallSid'],
							'callback': callback,
							'callerid': request.POST['Caller'],
						})
					)
			mail_admins('DoctorCom Error: No On-Call User Defined', 
					render_to_string('DoctorCom/IVR/no_oncall_error_admins.txt', {
					'practice': request.session['practice_id'],
					'timestamp': call_time,
					'callsid': request.POST['CallSid'],
					'callback': callback,
					'callerid': request.POST['Caller'],
				}))

			return None
		else:
			provider = provider_qs[0]
			message_managers(request, request.session['practice_id'],
						_('DoctorCom Error: No On-Call User Defined'),
						_("""Dear Manager,

An urgent call was received on {{timestamp|date:'l, F d, Y'}} at 
{{timestamp|date:'h:i A'}}, at which time nobody was defined as being on-call.

Because this is an urgent call, we automatically routed the message to the last 
on-call user: {{chosen_provider.first_name}} {{chosen_provider.last_name}}.

If you have any questions, please feel free to email us at support@mdcom.com 
with the following data
    {{callsid}}
    {{timestamp}}
and we will be happy to assist you in any way we can.

Best,
DoctorCom Staff
"""),
						timestamp=call_time,
						callsid=request.POST['CallSid'],
						chosen_provider=User.objects.filter(
								pk=provider.user_id).values('first_name', 'last_name')[0]
					)
	elif (oncall_count > 1):
		# Multiple providers are defined as being on-call for this call.
		# We've already picked one, and let the practice manager know how 
		# we're handling it.
		provider = oncall_qs[0]
		message_managers(request, request.session['practice_id'],
					_('DoctorCom Warning: Multiple On-Call Users Defined'),
					_("""Dear Manager,

An urgent call was received on {{timestamp|date:'l, F d, Y'}} at {{timestamp|date:'h:i A'}}, 
at which time the following users were listed as being on-call:
{% for provider in providers %}
     {{provider.first_name}} {{provider.last_name}}{% endfor %}

Because we could not determine which user should have received the call, 
{{chosen_provider.first_name}} {{chosen_provider.last_name}} was chosen.

If you have any questions, please feel free to email us at support@mdcom.com with 
the following data
    {{callsid}}
    {{timestamp}}
and we will be happy to assist you in any way we can.

Best,
DoctorCom Staff
"""),
					timestamp=call_time,
					callsid=request.POST['CallSid'],
					providers=User.objects.filter(pk__in=[p.pk for p in oncall_qs]),
					chosen_provider=provider
   				)
	else:
		# This handles the nominal one provider on-call situation, and also
		# randomly picks one provider if multiple are defined. The warning for
		# the latter situation is sent later.
		provider = oncall_qs[0]

	request.session['ivr_provider_onCall'] = provider
	return provider


@TwilioAuthentication()
def PracticeIVR_LeaveUrgentMsg(request):
	"""
	Records a voicemail message for the doctor on call
	and leave notification to the doctor based on preferences.
	"""
	# TODO: Update this code so that users can hit the pound key to pop 
	# back and log into their own voicemail box.
	if('CallStatus' in request.POST and request.POST['CallStatus'] == 'completed'):
		try:
			callSID = request.POST['CallSid']
			auth, uri, = client.auth, client.account_uri
			resp = make_twilio_request('GET', uri + '/Calls/%s' % callSID, auth=auth)
			content = json.loads(resp.content)
			log = callLog.objects.get(callSID=callSID)
			log.call_duration = content['TwilioResponse']['Call']['Duration']
			log.save()
		except TwilioRestException as tre:
			logger.critical('Unable to get call status: %s' % tre.msg)
		except ObjectDoesNotExist as odne:
			logger.warning('Call log does not exist for sid: %s.' % str(odne))

	logger.debug('%s: Into PracticeIVR_LeaveUrgentMsg with call status %s' %
				(request.session.session_key, request.POST['CallStatus']))

	if ('ivr_makeRecording_callbacknumber' in request.session):
		callback = request.session['ivr_makeRecording_callbacknumber']

	provider = _getRecentOncallProvider(request)
	# TODO: we do nothing with config
	config = None
	config_complete = provider.vm_config.count() == 1 and provider.vm_config.get().config_complete
	if (config_complete):
		config = provider.vm_config.get()

	if ('ivr_makeRecording_recording' in request.session or 
			request.session['ivr_only_callbacknumber'] == True):
		if (request.session['ivr_only_callbacknumber'] == False):
			mgrs = get_all_practice_managers(request.session['practice_id'])
			# after unique'ifying save_answering_service_message() expects recips 
			# as a list, see https://redmine.mdcom.com/issues/1374 for details
			save_answering_service_message(request, True, [provider], 
										list(set(m.user for m in mgrs)))
			#this is calling doctor on call we keep events for that even if called 
			#via answering service, just like doctor com does
			# Cleanup
			del request.session['ivr_makeRecording_recording']
		else:
			if('CallStatus' in request.POST and request.POST['CallStatus'] == 'completed'):
				mgrs = get_all_practice_managers(request.session['practice_id'])
				# after unique'ifying save_answering_service_message() expects recips 
				# as a list, see https://redmine.mdcom.com/issues/1374 for details
				save_answering_service_message(request, True, [provider], 
											list(set(m.user for m in mgrs)))

		# Notify the user, always by sms, but provider better have mobile phone
		if (provider.mobile_phone):
			if (request.session['ivr_only_callbacknumber'] == False):
				body = render_to_string('DoctorCom/IVR/voicemail_sms.txt', {
						#'caller': '(%s) %s-%s'%(request.session['Caller'][:3], 
						#request.session['Caller'][3:6], request.session['Caller'][6:]),
						'caller': '%s' % (request.session['ivr_makeRecording_callbacknumber']),
						})
			else:
				if ('ivr_no_pound' in request.session and request.session['ivr_no_pound'] == True):
					body = _("You have a new call from DoctorCom. Caller hung up from "
						"CONFIRMED number %s") % (request.session['ivr_makeRecording_callbacknumber'])
				else:
					body = _("You have a new call from DoctorCom. Caller hung up "
							"from unconfirmed number %s") % \
								(request.session['ivr_makeRecording_callbacknumber'])
			# TODO: we do nothing with body, sms send?
		# if pager number is entered, also page call back number
		r = twilio.Response()
		r.append(tts(_('Your message has been sent. Good bye')))
		r.append(twilio.Hangup())
		return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)

	if ('ivr_makeRecording_callbacknumber' in request.session):	
		request.session['ivr_makeRecording_prompt'] = tts(_('Please say your message '
				'for the doctor on call after the beep. Press pound when finished.'))

		request.session['ivr_makeRecording_maxLength'] = 600  # 10 minutes
		request.session['ivr_makeRecording_leadSilence'] = 2
		request.session['ivr_makeRecording_promptOnce'] = True

		request.session['ivr_makeRecording_returnOnHangup'] = \
			'MHLogin.DoctorCom.IVR.views_practice.PracticeIVR_LeaveUrgentMsg'
		request.session['ivr_call_stack'].append('PracticeIVR_LeaveUrgentMsg')
		request.session.modified = True

		# Pass off the recording action to the getRecording function.
		return getQuickRecording(request)

	#get call back number
	request.session['ivr_call_stack'].append('PracticeIVR_LeaveUrgentMsg')
	request.session['ivr_callback_returnOnHangup'] = \
		'MHLogin.DoctorCom.IVR.views_practice.PracticeIVR_LeaveUrgentMsg'
	return getCallBackNumber(request)


@TwilioAuthentication()
def PracticeIVR_LeaveRegularMsg(request):
	"""
	Sends office manager text message, in attachment there is voice file of recording
	"""		
	if 'CallStatus' in request.POST:
		logger.debug('%s: Into LeaveTextMsg with call status %s' % (
				request.session.session_key, request.POST['CallStatus']))
	if('CallStatus' in request.POST and request.POST['CallStatus'] == 'completed'):
		try:
			callSID = request.POST['CallSid']
			auth, uri, = client.auth, client.account_uri
			resp = make_twilio_request('GET', uri + '/Calls/%s' % callSID, auth=auth)
			content = json.loads(resp.content)
			log = callLog.objects.get(callSID=callSID)
			log.call_duration = content['TwilioResponse']['Call']['Duration']
			log.save()
		except TwilioRestException as tre:
			logger.critical('Unable to get call status: %s' % tre.msg)
		except ObjectDoesNotExist as odne:
			logger.warning('Call log does not exist for sid: %s. Caller may have '
				'hung up shortly after Twilio starts call process.' % str(odne))

	#if already got recording - this must be second ittiration	
	if ('ivr_makeRecording_recording' in request.session or 
			request.session['ivr_only_callbacknumber'] == True):
		# get a list of all office managers for this practice
		mgrs = get_all_practice_managers(request.session['practice_id'])

		# after unique'ifying save_answering_service_message() expects recips 
		# as a list, see https://redmine.mdcom.com/issues/1374 for details
		save_answering_service_message(request, False, list(set(m.user for m in mgrs)))

		r = twilio.Response()
		r.append(tts(_('Your message have been sent. Good Buy')))
		r.append(twilio.Hangup())
		return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)
	else:
		# first or second iteration, get call back number and message recoding
		if ('ivr_makeRecording_callbacknumber' in request.session):	
			# get recording for non urgent message
			request.session['ivr_makeRecording_maxLength'] = 600  # 10 minutes
			request.session['ivr_makeRecording_leadSilence'] = 2
			request.session['ivr_makeRecording_promptOnce'] = True
			request.session['ivr_makeRecording_prompt'] = tts(_('Please say your '
					'non urgent message after the beep. Please state your name and '
					'speak clearly. Press pound when finished.'))
			request.session['ivr_makeRecording_returnOnHangup'] = \
				'MHLogin.DoctorCom.IVR.views_practice.PracticeIVR_LeaveRegularMsg'
			request.session['ivr_call_stack'].append('PracticeIVR_LeaveRegularMsg')
			request.session.modified = True

			# Pass off the recording action to the getRecording function.
			return getQuickRecording(request)
		else:	 
			#get call back number
			request.session['ivr_call_stack'].append('PracticeIVR_LeaveRegularMsg')
			request.session['ivr_callback_returnOnHangup'] = \
				'MHLogin.DoctorCom.IVR.views_practice.PracticeIVR_LeaveRegularMsg'
			return getCallBackNumber(request)


@TwilioAuthentication()
def PracticeIVR_Options(request, internalCall=False):
	"""
	changes setting on doctor com number for practice
	"""	
	r = twilio.Response()

	if (not internalCall and 'Digits' in request.POST):
		digits = request.POST['Digits']
		p = re.compile('[0-9#*]$')
		if (not p.match(digits)):
			r.append(tts(_('I\'m sorry, I didn\'t understand that.')))
		elif (digits == '1'):
			# Change name
			request.session['ivr_call_stack'].append('PracticeIVR_Options')
			request.session.modified = True
			return changeName(request)
		elif (digits == '3'):
			# Change closed greeting
			request.session['ivr_setup_stage'] = 3
			request.session['ivr_call_stack'].append('PracticeIVR_Options')
			request.session.modified = True
			return changeGreeting(request)
		elif (digits == '5'):
			# change temporarily closed office greeting
			request.session['ivr_setup_stage'] = 5
			request.session['ivr_call_stack'].append('PracticeIVR_Options')
			request.session.modified = True
			return changeGreeting(request)
		elif (digits == '7'):
			# change pin
			request.session['ivr_call_stack'].append('PracticeIVR_Options')
			request.session.modified = True
			return changePin(request, None, True)
		elif (digits == '*'):
			# Repeat menu
			pass
		elif (digits == '9'):
			# Return to the main menu
			r.append(twilio.Redirect(reverse(request.session['ivr_call_stack'].pop())))
			request.session.modified = True
			return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)
		else:
			r.append(tts(_('I\'m sorry, that wasn\t a valid selection.')))

	gather = twilio.Gather(finishOnKey='', numDigits=1, action=reverse('PracticeIVR_Options'))

	gather.append(tts(_('Options menu')))
	gather.append(tts(_('To re-record your name, press 1')))
	gather.append(tts(_('To record a new closed office greeting, press 3')))
	gather.append(tts(_('To record a new greeting while the office is open, press 5')))
	gather.append(tts(_('To change your pin, press 7')))
	gather.append(tts(_('To return to the main menu, press 9')))
	gather.append(tts(_('To repeat this menu, press star')))

	r.append(gather)
	return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)


@TwilioAuthentication()
def PracticeIVR_TreeRoot(request):
	"""
	will be called if it is practice manager calling and set up was done already
	update set up option only, we have no msg on this number
	"""	
	r = twilio.Response()
	#practice = PracticeLocation.objects.get(id=request.session['practice_id'])
	if ('Digits' in request.POST):	
		digits = request.POST['Digits']
		p = re.compile('[0-9#*]$')
		if (not p.match(digits)):
			r.append(tts(_('I\'m sorry, I didn\'t understand that.')))
		elif (digits == '3'):
			request.session['ivr_call_stack'].append('PracticeIVR_TreeRoot')
			request.session.modified = True
			return PracticeIVR_Options(request, r)
		elif (digits == '*'):
			pass
		else:
			r.append(tts(_('I\'m sorry, I didn\'t understand that.')))

	gather = twilio.Gather(finishOnKey='', numDigits=1, timeout=30)

	r.append(tts(_("Wecome to you voice mail account. Your set up is "
						"complete. This account does not have mail box.")))
	gather.append(tts(_('To manage your settings, press 3')))
	gather.append(tts(_('To repeat this menu, press star')))
	r.append(gather)

	return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)

# TODO: rip this out or fix it to work


@TwilioAuthentication()
def PracticeIVR_OutsideInit(request, caller, called_manager, c2c_log=None):
	"""
	An IVR initialization function that is intended to be called by views outside
	of the IVR, wishing to redirect Twilio functionality here, into the IVR.

	Arguments:
		request: The standard Django view request object. This *MUST* be from
			Twilio or the user will see an error 403.
		caller: The caller's actual number, NOT their DoctorCom number or
			anything like that.
		provider: The provider being called. Note that the provider MUST have a
			DoctorCom number.
	"""
	# First, deal with some random book keeping odds and ends
	request.session.modified = True
	if (not 'ivr_call_stack' in request.session):
		request.session['ivr_call_stack'] = []

	# Deal with the called user values first
	request.session['Called'] = called_manager.user.mobile_phone
	request.session['provider_id'] = called_manager.user.id

	# Now, deal with the caller values. Does the caller have a DoctorCom number?
	mhlusers_mobile_phone = MHLUser.objects.filter(mobile_phone=caller)
	mhlusers_phone = MHLUser.objects.filter(phone=caller)
	total_users = mhlusers_mobile_phone.count() + mhlusers_phone.count()

	#if caller is provider follow this path
	caller_provider = None
	if (total_users == 1):
		# First, get the MHLUser involved.
		if (mhlusers_mobile_phone.count()):
			user = mhlusers_mobile_phone.get()
		else:
			user = mhlusers_phone.get()

		caller_provider_qs = Provider.objects.filter(user=user)
		if (caller_provider_qs.count()):
			caller_provider = caller_provider_qs.get()
			if (caller_provider.mdcom_phone):
				# Mask the caller's caller ID since they have a doctorcom number
				logger.debug('%s: Setting caller to DoctorCom number \'%s\'' % (
						request.session.session_key,
						caller_provider.mdcom_phone,
					))
				request.session['Caller'] = caller_provider.mdcom_phone
			else:
				logger.debug('%s: called_provider.mdcom_phone is False' % (
						request.session.session_key,
					))
		else:
			logger.debug('%s: called_provider_qs.count() is False' % (
					request.session.session_key,
				))
	else:
		logger.debug('%s: total_users is %i' % (
				request.session.session_key,
				total_users
			))
	# Else, mask the caller's phone number with the DoctorCom number.
	#caller not a privider, must be office manager with cell phone
	if (not 'Caller' in request.session):
		logger.debug('%s: Defaulting caller ID to \'%s\'' % (
				request.session.session_key,
				settings.TWILIO_CALLER_ID
			))
		request.session['Caller'] = settings.TWILIO_CALLER_ID

	logger.debug('%s: request.session[\'Caller\'] is \'%s\'' % (
			request.session.session_key,
			request.session['Caller'],
		))	
	# TODO: Flesh out the logging here so that we pull appropriate objects.
	log_qs = callLog.objects.filter(callSID=request.POST['CallSid'])
	if (log_qs.count()):
		# FIXME: This condition shouldn't be hit! This init function is getting
		# run multiple times per call, and I don't know why. --BK
		log = log_qs.get()
	else:
		log = callLog(
				caller_number=caller,
				called_number=called_manager.user.mobile_phone,
				callSID=request.POST['CallSid'],
				c2c_entry_id=c2c_log.pk,
				call_source='CC',
			)

		#once removed c2c log, this should be removed
		if (c2c_log and caller_provider):
			log.c2c_entry_id = c2c_log.pk
		logger.debug('%s: caller_provider is \'%s\'' % (
					request.session.session_key,
					str(caller_provider),
				))
		if (caller_provider):
			log.mdcom_caller = caller_provider
			logger.debug('%s: called_manager is \'%s\'' % (
					request.session.session_key,
					str(called_manager),
					))
		else:
			if (total_users == 1):
				caller_manager_qs = OfficeStaff.objects.filter(user=user)
				if (caller_manager_qs.count()):
					caller_manager = caller_manager_qs.get()
					log.mdcom_caller = caller_manager
				else:
					log.mdcom_caller = user

		#if we are here, called must be office manager
		log.mdcom_called = called_manager
	log.save()


@TwilioAuthentication()
def PracticeIVR_ForwardCall(request):
	"""
	Forward the call to the dialed user, there are no preferences 
	for office managers, just call their cell phone
	"""
	r = twilio.Response()
	request.session.modified = True
	provider = None
	try:
		provider = Provider.objects.get(id=request.session['provider_id'])	
		if(not 'ProviderIVR_ForwardCall_forward' in request.session):
			request.session['ProviderIVR_ForwardCall_forward'] = provider.forward_anssvc
		forward = provider.forward_anssvc
	except Provider.DoesNotExist:
		pass

	callSID = request.POST['CallSid']
	log = callLog.objects.get(callSID=callSID)
	log.call_source = 'AS'
	log.save()	

	if('click2call' in request.session):
		forward = 'MO'  # hack to keep click2call working

	if(forward == 'VM'):
		return PracticeIVR_LeaveUrgentMsg(request)

	if (not 'PracticeIVR_ForwardCall_state' in request.session or
			not request.session['PracticeIVR_ForwardCall_state']):

		# Okay, the call isn't going to voicemail directly. Now, set state.
		request.session['PracticeIVR_ForwardCall_state'] = 'Getting_Name'

		# Now, get the caller's name

		# Is the user a DoctorCom user with a recorded name?
		callSID = request.POST['CallSid']
		log = callLog.objects.get(callSID=callSID)

		if (log.mdcom_caller and isinstance(log.mdcom_caller, Provider)):
			if (log.mdcom_caller.vm_config.count()):
				prov_vmconfig = log.mdcom_caller.vm_config.get()
				if (prov_vmconfig.config_complete):
					logger.debug('%s/%s: Found the caller\'s name!' % (
							request.session.session_key,
							request.session['PracticeIVR_ForwardCall_state'],
						))
					log.caller_spoken_name = prov_vmconfig.name
					log.save()
					return PracticeIVR_ForwardCall(request)  # restart execution of this function
				else:
					logger.debug('%s/%s: Caller\'s vm_config incomplete!' % (
							request.session.session_key,
							request.session['PracticeIVR_ForwardCall_state'],
						))
			else:
				logger.debug('%s/%s: An unsuitable number of vm_config objects found: %i' % (
						request.session.session_key,
						request.session['PracticeIVR_ForwardCall_state'],
						log.mdcom_caller.vm_config.count(),
					))
		else:
			logger.debug('%s/%s: mdcom_caller %s either isn\'t defined or doesn\'t seem '
							'to be a Provider' % (
					request.session.session_key,
					request.session['PracticeIVR_ForwardCall_state'],
					str(log.mdcom_caller),
				))

		# Okay, it's not a user with a name recording. Get one.
		request.session['ivr_call_stack'].append('PracticeIVR_ForwardCall')
		request.session['ivr_makeRecording_prompt'] = tts(_('Please say your name after the tone.'))
		request.session['ivr_makeRecording_maxLength'] = 4
		request.session['ivr_makeRecording_timeout'] = 2
		request.session['ivr_makeRecording_leadSilence'] = 1
		return getQuickRecording(request)

	if (request.session['PracticeIVR_ForwardCall_state'] == 'Getting_Name'):
		request.session['PracticeIVR_ForwardCall_state'] = 'Dialed'

		logger.debug('%s/%s: Set session to %s' % (
				request.session.session_key,
				request.session['PracticeIVR_ForwardCall_state'],
				request.session['PracticeIVR_ForwardCall_state'],
			))

		callSID = request.POST['CallSid']
		log = callLog.objects.get(callSID=callSID)
		if (not log.caller_spoken_name):
			log.caller_spoken_name = request.session.pop('ivr_makeRecording_recording')
			log.save()
		user_number = ''
		try:
			office_staff = OfficeStaff.objects.get(user=request.session['provider_id']) 
			# manager being called
			logger.debug('%s/%s: got office staff \'%s\' \'%s\' with id %s' % (
					request.session.session_key,
					request.session['PracticeIVR_ForwardCall_state'],
					office_staff.user.first_name,
					office_staff.user.last_name,
					office_staff.pk,
				))
			logger.debug('%s/%s: Office Staff phone is \'%s\' .' % (
					request.session.session_key,
					request.session['PracticeIVR_ForwardCall_state'],
					office_staff.user.mobile_phone,
				))
			user_number = office_staff.user.mobile_phone
		except OfficeStaff.DoesNotExist:
			#it's a provider
			if(forward == 'MO'):
				user_number = provider.mobile_phone
			elif(forward == 'OF'):
				user_number = provider.office_phone
			elif(forward == 'OT'):
				user_number = provider.phone

		logger.debug('%s/%s: Setting user_number to \'%s\'' % (
					request.session.session_key,
					request.session['PracticeIVR_ForwardCall_state'],
					user_number,
				))

		logger.debug('%s/%s: Tried to get called\'s number. Got \'%s\'' % (
				request.session.session_key,
				request.session['PracticeIVR_ForwardCall_state'],
				user_number,
			))

		dial = twilio.Dial(
				action=reverse('PracticeIVR_ForwardCall'),
				timeout=22,
				timeLimit=14400,  # 4 hours
				callerId=request.session['Caller'],
			)
		dial.append(twilio.Number(user_number,
				url=reverse('PracticeIVR_ForwardCall_VetAnswer')
			))
		r.append(dial)
		r.append(twilio.Redirect(reverse('PracticeIVR_LeaveUrgentMsg')))
		return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)

	if (request.session['PracticeIVR_ForwardCall_state'] == 'Dialed'):
		if (log.call_connected):
			r.append(twilio.Hangup())
			return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)
		r.append(tts("The provider is not available right now."))
		r.append(twilio.Redirect(reverse('PracticeIVR_LeaveUrgentMsg')))
		return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)

	r = twilio.Response()

	# else: Do nothing so that the call continues un-interrupted
	return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)


@TwilioAuthentication()
def PracticeIVR_ForwardCall_VetAnswer(request):
	"""
	This function is executed on Number nouns within Dial verbs. The idea is to
	try to determine if it's a human who picked up, or a machine. Alternatively,
	this gives the called party a chance to send the call to voicemail without
	the caller knowing they're rejecting the call.
	"""
	r = twilio.Response()
	request.session.modified = True

	# First, find the recording to play
	callSID = request.POST['CallSid']
	log = callLog.objects.get(callSID=callSID)

	if 'Digits' in request.POST:
		# Connect the calls
		log.call_connected = True
		log.save()

		event = callEvent(callSID=request.POST['CallSid'], event='C_ACC')
		event.save()

		return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)

	caller_spoken_name = log.caller_spoken_name

	gather = twilio.Gather(numDigits=1, finishOnKey='', 
					action=reverse('PracticeIVR_ForwardCall_VetAnswer'))
	if('click2call' in request.session):
		gather.append(tts(_("You have a call from")))
		gather.append(twilio.Play(caller_spoken_name))
		gather.append(tts(_("Press any key to accept.")))
	else:
		gather.append(tts(_("You have an urgent answering service call from")))
		gather.append(twilio.Play(caller_spoken_name))
		gather.append(tts(_("Press any key to accept.")))

	r.append(gather)
	r.append(twilio.Hangup())

	return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)


@TwilioAuthentication()
def PracticeIVR_Main(request):
	"""
	DEPRECATED - to be replaced by PracticeIVR_Main_New in views_practice_v2.py
	entry point when call comes in to doctor.com number associated with Practice
	"""

	#if the practice's answering service is not available
	called = request.POST['Called']
	try:
		practice = PracticeLocation.objects.get(mdcom_phone=called)
		can_have_answering_service = practice.get_setting_attr('can_have_answering_service')
		if (not can_have_answering_service):
			r = twilio.Response()
			r.append(tts(_("I'm sorry, answering service is not available. Good bye.")))
			return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)
	except MultipleObjectsReturned:
		raise Exception(_('Multiple Practice Locations have mdcom_phone %s') % (called,))
	except ObjectDoesNotExist:
		raise Exception(_('No Practice Location have mdcom_phone %s') % (called,))

	if (request.COOKIES and 'CallStatus' not in request.POST or
			request.POST['CallStatus'] == 'completed'):

		callSID = request.POST['CallSid']
		try:
			if 'Duration' in request.POST:
				# if getrecording starts redirecting here on call completed, this becomes wrong
				# the 2008 api overloads 'Duration' for both call duration (minutes), and recording duration (seconds)
				log = callLog.objects.get(callSID=callSID)
				log.duration = int(request.POST['Duration'])
				log.save()
			else:
				auth, uri, = client.auth, client.account_uri
				resp = make_twilio_request('GET', uri + '/Calls/%s' % callSID, auth=auth)
				content = json.loads(resp.content)
				log = callLog.objects.get(callSID=callSID)
				log.call_duration = content['TwilioResponse']['Call']['Duration']
				log.save()
		except TwilioRestException as tre:
			logger.critical('Unable to get call status: %s' % tre.msg)
		except ObjectDoesNotExist as odne:
			logger.warning('Call log does not exist for sid: %s. Caller may have '
				'hung up shortly after Twilio starts call process.' % str(odne))

		r = twilio.Response()		
		return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)

	# ready to initialize this call, request.session[practice_id] in request stack
	practice = PracticeIVR_Init(request)

	############################################################################	
	#see if this is office manager calling, if yes - set up
	#TO DO - MANAGERS CELL ALSO NEED TO BE ADDED, also if not set up yet
	if (request.session['practice_phone'] == request.REQUEST['Caller']
		or practice.accessnumber_set.filter(number=request.REQUEST['Caller'])):
		# Great, now we know that this is the owner calling in. First up, check to
		# see if the user has a configuration file and that they've completed setup
		# it is stored with practice location, for now act like first time
		# Now, check to ensure that user voicemail configuration was completed successfully.
		if (not practice.config_complete):
			request.session['ivr_call_stack'].append('PracticeIVR_Main')
			request.session.modified = True
			return PracticeIVR_Setup(request)
		else:  # config was complete, but call is made, ask if want to change settings
			# make sure they have pin for setting
			if (not 'authenticated' in request.session):
				request.session['ivr_call_stack'].append('PracticeIVR_Main')
				request.session.modified = True	
				r = twilio.Response()
				return authenticateSession(request, r)

			request.session['ivr_call_stack'].append('PracticeIVR_Main')
			request.session.modified = True
			return PracticeIVR_TreeRoot(request)

	############################################################################	
	#phone call from outside called, they want to call answering service
	#lets see if we open/close/or lunch - based on that we decide on call tree
	#get current time in timezone of our practice, use gmt and then make it into local, 
	#calltime_local is the time we use.

	gmttz = timezone('GMT')
	mytz = timezone(practice.time_zone)
	calltime_gmt = datetime.now(gmttz)
	calltime_local = calltime_gmt.astimezone(mytz)

	request.session['calltime_local_string'] = calltime_local.strftime("%Y-%m-%d %H:%M:%S")
	request.session['calltime_local'] = calltime_local

	#if this is newly V2 and later set up practice, call new version of getting input
	if (practice.uses_original_answering_serice()):
		return PracticeIVR_CallerResponse(request)  # old way
	else:
		return PracticeIVR_V2_CallerResponse(request)  # V2 way
