
import re
#import urllib2
#from lxml.sax import etree
from pytz import timezone
from datetime import datetime
from twilio import twiml as twilio

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.template.loader import render_to_string

from models import callLog, callEvent
from views_generic_v2 import _setup_Main_callers, _getOrCreateCallLog, _getMHLUser, _maskProviderCaller
from views_generic_v2 import changePinNew, changeNameNew, changeGreetingNew
from views_generic_v2 import getQuickRecordingNew, getCallBackNumberNew
from views_generic_v2 import authenticateSessionNew, _getCallLogOrParent, _copyStateVariables
from utils import save_answering_service_message, create_dynamic_greeting, create_call_group_list

from MHLogin.DoctorCom.speech.utils import tts
from MHLogin.MHLUsers.models import MHLUser, Provider, OfficeStaff
from MHLogin.MHLUsers.utils import get_all_practice_managers
from MHLogin.utils.decorators import TwilioAuthentication
from MHLogin.utils.mh_logging import get_standard_logger
from MHLogin.utils.admin_utils import mail_admins

from MHLogin.MHLPractices.models import PracticeLocation
from MHLogin.MHLPractices.utils import message_managers

from MHLogin.MHLCallGroups.Scheduler.utils import getPrimaryOnCall, getLastPrimaryOnCall
from django.utils.translation import ugettext as _
from MHLogin.DoctorCom.IVR.utils import _checkCallbackDuration, _getUSNumber

#list practice numbers that will roll over to temp closed instead of opened after X rings
SPECIAL_PRACTICE = [3]


# Setting up logging
logger = get_standard_logger('%s/DoctorCom/IVR/views_practice_v2.log' % (settings.LOGGING_ROOT),
	'DCom.IVR.views_prac', settings.LOGGING_LEVEL)


@TwilioAuthentication()
def PracticeIVR_Setup_New(request):
	"""
	This function is heavily dependent upon request.session; Twilio is kind
	enough to keep session cookies for us.
	sets up doctor com answering service practice open/closed greetings and pin
	"""
	assert(request.session['practice_id'])
	assert(request.session['ivr2_state'] == 'PracticeIVR_Setup_New')
	_checkCallbackDuration(request)
	logger.debug('%s: PracticeIVR_Setup_New POST data is %s' % (
		request.session.session_key, str(request.POST)))
	logger.debug('%s: PracticeIVR_Setup_New state %s practice %s' % (
		request.session.session_key, request.session['ivr2_state'], request.session['practice_id']))

	# TODO - check if we need to create event for this
	if ('ivr2_sub_state' not in request.session):
		request.session['ivr2_sub_state'] = 'PracticeIVR_Setup_Start'
	else:
		logger.debug('%s: PracticeIVR_Setup_New sub_state %s' % (
			request.session.session_key, request.session['ivr2_sub_state']))
	if (request.session['ivr2_sub_state'] == 'PracticeIVR_Setup_Start'):
		# Okay, this is the first time this function is being executed for this call.
		request.session['ivr2_sub_state'] = 'PracticeIVR_Setup_1'
		#will need to Practice Location and see if this needs set up and values that are there already
		r = twilio.Response()
		r.append(twilio.Pause())  # one second pause keeps the first words from getting cut off.
		request.session['ivr2_prompt_str'] = "Welcome to your voicemail account. It looks like some setup is needed. \
Let's get started. First, we need to set up your pin number."
		return changePinNew(request, r)

	elif (request.session['ivr2_sub_state'] == 'PracticeIVR_Setup_1'):  # Record name
		request.session['ivr2_sub_state'] = 'PracticeIVR_Setup_2'
		return changeNameNew(request, _('Now, we need to record your office name.'))

	elif (request.session['ivr2_sub_state'] == 'PracticeIVR_Setup_2'):
		# Record a greeting for closed office
		request.session['ivr2_sub_state'] = 'PracticeIVR_Setup_3'
#		request.session['ivr2_setup_stage'] = 3  # deprecated
		return changeGreetingNew(request, _('Next, we need to set up your answering service '
			'greeting. This will be played when the office is closed.'))

	elif (request.session['ivr2_sub_state'] == 'PracticeIVR_Setup_3'):  # Record a greeting for open
		request.session['ivr2_sub_state'] = 'PracticeIVR_Setup_4'
#		request.session['ivr2_setup_stage'] = 4  # deprecated
		return changeGreetingNew(request, _('Finally, we need to set up a greeting that '
			'will be played when the office is open.'))

	elif (request.session['ivr2_sub_state'] == 'PracticeIVR_Setup_4'):  # Configuration complete!
		#store new information in Practice Locations
		del request.session['ivr2_sub_state']
		request.session['ivr2_state'] = 'PracticeIVR_TreeRoot_New'
		practice = PracticeLocation.objects.get(id=request.session['practice_id'])
		practice.config_complete = True
		practice.save()
		# we don't need the welcome msg anymore
		if ('ivr2_prompt_str' in request.session):
			del request.session['ivr2_prompt_str']

		r = twilio.Response()
		r.append(tts(_('Your voice mail account is now set up. You may hang up now.')))
		r.append(twilio.Redirect(reverse('PracticeIVR_TreeRoot_New')))
		return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)

	else:
		# should not get here with unknown state - log state and return to main; or throw exception?
		logger.debug('%s: PracticeIVR_Setup_New has unhandled state set to %s' % (
			request.session.session_key, request.session['ivr2_state']))
		request.session['ivr2_state'] = 'PracticeIVR_Main_New'
		return PracticeIVR_Main_New(request)


@TwilioAuthentication()
def PracticeIVR_CallerResponse_New(request, twilioResponse=None):
	"""
	This function process callers response - set up practice greeting based on practice hours and
	callgroups and specialties (via create_dynamic_greeting)
	"""
	request.session['ivr2_state'] = 'PracticeIVR_CallerResponse_New'
	practice = PracticeLocation.objects.get(id=request.session['practice_id'])
	logger.debug('%s: PracticeIVR_CallerResponse_New state %s practice %s' % (
		request.session.session_key, request.session['ivr2_state'], practice))

	r = twilioResponse or twilio.Response()
	gather = twilio.Gather(action=reverse('PracticeIVR_CallerResponse_Action'),
		finishOnKey='', numDigits=1, timeout=60)
	if (not 'practice_greeting' in request.session):
		if (practice.is_open()):
			request.session['practice_greeting'] = practice.greeting_lunch
		else:
			request.session['practice_greeting'] = practice.greeting_closed

	if(practice.skip_to_rmsg and practice.is_open()):
		request.session['ivr2_state'] = 'PracticeIVR_LeaveRegularMsg_New'
		r.append(twilio.Play(request.session['practice_greeting']))
		r.append(twilio.Redirect(reverse('PracticeIVR_LeaveRegularMsg_New')))
		logger.debug('%s: PracticeIVR_CallerResponse_New skip to leave msg for %s open greeting' % (
			request.session.session_key, practice))
	else:
		if practice.uses_original_answering_serice():
			gather.append(twilio.Play(request.session['practice_greeting']))
			r.append(gather)
			logger.debug('%s: PracticeIVR_CallerResponse_New practice %s orig greeting' % (
				request.session.session_key, practice))
		else:
			#layer 1 greeting, it recites call group lists,
			#populates  request.session['call_groups_map'] and request.session['specialty_map']
			dynamic_greeting = create_dynamic_greeting(request, practice)
			request.session['last_played'] = dynamic_greeting
			gather.append(twilio.Play(request.session['practice_greeting']))
			gather.append(tts(_('%s.') % (''.join(request.session['last_played']))))
			r.append(gather)
			logger.debug('%s: PracticeIVR_CallerResponse_New practice %s greeting %s' % (
				request.session.session_key, practice, request.session['last_played']))

	return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)


@TwilioAuthentication()
def PracticeIVR_CallerResponse_Action(request, twilioResponse=None):
	"""
	This function process callers response in 2 ways:
	old way (original answering service):
		1=leave msg in doc com  mailbox via PracticeIVR_LeaveRegularMsg_New (to all practice managers)
		2=page doctor on call (LeaveUrgentMsg_New)
	new way (dynamic greeting already called):
		create greeting based on call_groups info in db
		if 1 call group  for THIS practice, take message via PracticeIVR_LeaveRegularMsg_New
		if > 1 call group, add a layer to first pick call group, then pick type of message
		PracticeIVR_ForwardCall_New
	"""
	practice = PracticeLocation.objects.get(id=request.session['practice_id'])
	logger.debug('%s: PracticeIVR_CallerResponse_Action practice %s POST data is %s' % (
		request.session.session_key, practice, str(request.POST)))

	r = twilioResponse or twilio.Response()
	if (request.method == 'POST' and 'Digits' in request.POST):
		digits = request.POST['Digits']
		if practice.uses_original_answering_serice():  # old way
			logger.debug('%s: PracticeIVR_CallerResponse_Action via old ans svc' % (
				request.session.session_key))
			p = re.compile('[0-9#*]$')
			if (not p.match(digits)):
				r.append(tts(_('I\'m sorry, I didn\'t understand that.')))
			elif (digits == '1'):
				# leave msg in doctor com mailbox
				request.session['ivr2_state'] = 'PracticeIVR_LeaveRegularMsg_New'
				request.session.modified = True
				return PracticeIVR_LeaveRegularMsg_New(request)
			elif (digits == '2'):
				# forward the call
				request.session['ivr2_state'] = 'PracticeIVR_ForwardCall_New'
				request.session.modified = True
				request.session['provider_id'] = _getRecentOncallProviderId(request)
				logger.debug('%s: PracticeIVR_CallerResponse_Action old ans svc NO oncall provider' %
					(request.session.session_key))
				if(not request.session['provider_id']):
					r.append(tts(_('We\'re sorry, an application error has occurred. Goodbye.',
						voice='woman')))
					r.append(twilio.Hangup())
					# return r
					return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)
				return PracticeIVR_ForwardCall_New(request)
			elif (digits == '*'):
				pass
			else:
				r.append(tts(_('I\'m sorry, I didn\'t understand that.')))
			return PracticeIVR_CallerResponse_New(request, r)
		else:
			# new V2 dynamic greeting and call groups
			call_groups_map = request.session['call_groups_map']
			specialties_map = request.session['specialties_map']
			logger.debug('%s: PracticeIVR_CallerResponse_Action via new ans svc cg %s sp %s' % (
				request.session.session_key, call_groups_map, specialties_map))
			gather = twilio.Gather(action=reverse('PracticeIVR_CallerResponse_Action'),
				finishOnKey='', numDigits=1, timeout=60)

			p = re.compile('[0-9]$')
			if (not p.match(digits)):
				r.append(tts(_('I\'m sorry, I didn\'t understand that.')))
				r.append(tts(_('%s.') % (''.join(request.session['last_played']),)))
				r.append(gather)

			elif (digits == '1' and request.session['one_ok'] == '1'):  # one_ok is set in create_dynamic_greeting
				# leave msg in doctor com mailbox
				request.session['ivr2_state'] = 'PracticeIVR_LeaveRegularMsg_New'
				request.session.modified = True
				return PracticeIVR_LeaveRegularMsg_New(request)

			elif (digits in call_groups_map):
				#Call Group reached, get provider on call
				request.session['callgroup_id'] = call_groups_map.get(digits)
				request.session['ivr2_state'] = 'PracticeIVR_ForwardCall_New'
				request.session.modified = True
				request.session['provider_id'] = _getRecentOncallProviderId(request)
				logger.debug('%s: PracticeIVR_CallerResponse_Action new ans svc NO oncall provider' %
					(request.session.session_key))
				if(not request.session['provider_id']):
					r.append(tts(_('We\'re sorry, an application error has occurred. Goodbye.',
						voice='woman')))
					r.append(twilio.Hangup())
					# return r
					return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)
				return PracticeIVR_ForwardCall_New(request)
			elif (digits in specialties_map):
				#specialty reached, get list of call groups,
				#populates request.session['call_groups_map'] and blanks out request.session['specialty_map']
				call_groups_greeting = create_call_group_list(request, specialties_map.get(digits))
				gather.append(tts(_('%s.') % (''.join(call_groups_greeting),)))
				request.session['last_played'] = call_groups_greeting
				r.append(gather)
			#elif (digits == '*'): treat * as invalid input
				#pass
			else:
				gather.append(tts(_('I\'m sorry, I didn\'t understand that.')))
				gather.append(tts(_('%s.') % (''.join(request.session['last_played']),)))
				r.append(gather)
			return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)
	else:
		# should never happen - but if we get here without Digits, we log and go back to Main
		logger.debug('%s: PracticeIVR_CallerResponse_Action is called with no post or digits' %
			(request.session.session_key))
		request.session['ivr2_state'] = 'PracticeIVR_Main_New'
		return PracticeIVR_Main_New(request)


def _getRecentOncallProviderId(request):
	"""
	clone from V1 replacing Caller with From: gets current oncall provider returning provider ID
	"""
	if 'ivr2_provider_onCall' in request.session:
		return request.session['ivr2_provider_onCall']

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
			logger.debug('%s: _getRecentOncallProviderId none on call. No previous.' % (
				request.session.session_key))
			message_managers(request, request.session['practice_id'],
						'DoctorCom Error: No On-Call User Defined',
						render_to_string("DoctorCom/IVR/no_oncall_error.txt", {
							'timestamp': call_time,
							'callsid': request.POST['CallSid'],
							'callback': callback,
							'callerid': request.POST['From'],
						})
					)
			mail_admins('DoctorCom Error: No On-Call User Defined',
					render_to_string('DoctorCom/IVR/no_oncall_error_admins.txt', {
					'practice': request.session['practice_id'],
					'timestamp': call_time,
					'callsid': request.POST['CallSid'],
					'callback': callback,
					'callerid': request.POST['From'],
				}))

			return None
		else:
			provider = provider_qs[0]
			logger.debug('%s: _getRecentOncallProviderId none on call. Previous %s' % (
				request.session.session_key, provider))
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
		logger.debug('%s: _getRecentOncallProviderId multiple on call. Assigning %s' % (
			request.session.session_key, provider))
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
		logger.debug('%s: _getRecentOncallProviderId on call prov %s' % (
			request.session.session_key, provider))

	request.session['ivr2_provider_onCall'] = provider.id
	return provider.id


@TwilioAuthentication()
def PracticeIVR_LeaveUrgentMsg_New(request):
	"""
	This lets caller leave an urgent message for a practice in foll steps:
	1. get callback number
	2. Records a voicemail message for the doctor on call
	3. leave notification to the doctor based on preferences.
	"""
	# TODO:
	# Update this code so that users can hit the pound key to pop back and log
	# into their own voicemail box.
	requestDataDict = {"GET": request.GET, "POST": request.POST}[request.method]
	logger.debug('%s: PracticeIVR_LeaveUrgentMsg_New state %s POST data is %s' % (
		request.session.session_key, request.session['ivr2_state'], str(request.POST)))
	# if caller hangs up, we still continue
	if ('ivr2_sub_state' not in request.session):
		request.session['ivr2_sub_state'] = 'PracticeIVR_LeaveUrgentMsg_Start'
	else:
		logger.debug('%s: PracticeIVR_LeaveUrgentMsg_New sub_state %s' % (
			request.session.session_key, request.session['ivr2_sub_state']))

	callEnded = _checkCallbackDuration(request, False)
	if (callEnded):
		logger.debug('%s: PracticeIVR_LeaveUrgentMsg_New caller hung up. State %s' % (
			request.session.session_key, request.session.get('ivr2_sub_state', 'None')))
		# we deal with leftover recording or , if any
		if (request.session['ivr2_sub_state'] == 'PracticeIVR_LeaveUrgentMsg_GetMsg' or
			'ivr2_Record_recording' in request.session or
			('ivr2_only_callbacknumber' in request.session and
				request.session['ivr2_only_callbacknumber'] == True)):
			# send msg to office managers
			del request.session['ivr2_sub_state']
			provider = Provider.objects.get(id=_getRecentOncallProviderId(request))
			logger.debug('%s: PracticeIVR_LeaveUrgentMsg_New caller hung up -- saving urgent msg for %s' % (
				request.session.session_key, provider))
			config = None
			config_complete = provider.vm_config.count() == 1 and provider.vm_config.get().config_complete
			if (config_complete):
				config = provider.vm_config.get()
			mgrs = get_all_practice_managers(request.session['practice_id'])
			_copyStateVariables(request)
			save_answering_service_message(request, True, [provider],
				list(set(m.user for m in mgrs)))
	else:
		if (request.session['ivr2_sub_state'] == 'PracticeIVR_LeaveUrgentMsg_Start'):
			# step 1: get callback number
			request.session['ivr2_sub_state'] = 'PracticeIVR_LeaveUrgentMsg_GetCallback'
			request.session['ivr2_returnOnHangup'] = \
				'MHLogin.DoctorCom.IVR.views_practice_v2.PracticeIVR_LeaveUrgentMsg_New'
			return getCallBackNumberNew(request)

		elif request.session['ivr2_sub_state'] == 'PracticeIVR_LeaveUrgentMsg_GetCallback':
			# step 2: after getting callback number, we get caller's message
			request.session['ivr2_sub_state'] = 'PracticeIVR_LeaveUrgentMsg_GetMsg'
			request.session['ivr2_Record_prompt_str'] = 'Please say your message \
					for the doctor on call after the beep. Press pound when finished.'
			request.session['ivr2_Record_maxLength'] = 600  # 10 minutes
			request.session['ivr2_Record_leadSilence'] = 2
			request.session['ivr2_Record_promptOnce'] = True
			request.session['ivr2_returnOnHangup'] = \
				'MHLogin.DoctorCom.IVR.views_practice_v2.PracticeIVR_LeaveUrgentMsg_New'
			request.session.modified = True
			# Pass off the recording action to the getRecording function.
			return getQuickRecordingNew(request)

		elif (request.session['ivr2_sub_state'] == 'PracticeIVR_LeaveUrgentMsg_GetMsg' or
			'ivr2_Record_recording' in request.session or
			('ivr2_only_callbacknumber' in request.session and
				request.session['ivr2_only_callbacknumber'] == True)):
			# step 3 - send msg to office managers
			del request.session['ivr2_sub_state']
			provider = Provider.objects.get(id=_getRecentOncallProviderId(request))
			logger.debug('%s: PracticeIVR_LeaveUrgentMsg_New saving urgent msg for %s' % (
				request.session.session_key, provider))
			config = None
			config_complete = provider.vm_config.count() == 1 and provider.vm_config.get().config_complete
			if (config_complete):
				config = provider.vm_config.get()
			mgrs = get_all_practice_managers(request.session['practice_id'])
			_copyStateVariables(request)
			save_answering_service_message(request, True, [provider],
				list(set(m.user for m in mgrs)))

			#if pager number is entered, also page call back number
			r = twilio.Response()
			r.append(tts(_('Your message has been sent. Good bye')))
			r.append(twilio.Hangup())
			return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)
		else:  # should not get here
			logger.debug('%s: Into PracticeIVR_LeaveUrgentMsg_New with invalid ivr2_state %s' %
				(request.session.session_key, request.session['ivr2_state']))
			request.session['ivr2_state'] = 'PracticeIVR_LeaveUrgentMsg_New'
			return PracticeIVR_LeaveUrgentMsg_New(request)


@TwilioAuthentication()
def PracticeIVR_LeaveRegularMsg_New(request):
	"""
	3 steps:
	1. get callback number
	2. get message (recording) from caller
	3. Sends office manager text message, in attachment there is voice file of recording
	"""
	callEnded = _checkCallbackDuration(request, False)  # if someone hangs up, we still want to keep processing
	logger.debug('%s: PracticeIVR_LeaveRegularMsg_New state %s' %
		(request.session.session_key, request.session['ivr2_state']))
	if ('ivr2_sub_state' not in request.session):
		# first time around
		request.session['ivr2_sub_state'] = 'PracticeIVR_LeaveRegularMsg_Start'
	else:
		logger.debug('%s: PracticeIVR_LeaveRegularMsg_New sub_state %s' %
			(request.session.session_key, request.session['ivr2_sub_state']))
	# we have recording, or callback number or we are in the GetMsg sub_state
	if ('ivr2_Record_recording' in request.session or 
		('ivr2_only_callbacknumber' in request.session and 
			request.session['ivr2_only_callbacknumber'] == True) or
		request.session['ivr2_sub_state'] == 'PracticeIVR_LeaveRegularMsg_GetMsg'):
		# final or third iteration - get and send message
		del request.session['ivr2_sub_state']
		# get a list of all office managers for this practice
		mgrs = get_all_practice_managers(request.session['practice_id'])
		# after unique'ifying save_answering_service_message() expects recips
		# as a list, see https://redmine.mdcom.com/issues/1374 for details
		_copyStateVariables(request)
		save_answering_service_message(request, False, list(set(m.user for m in mgrs)))
		r = twilio.Response()
		r.append(tts(_('Your message have been sent. Good Buy')))
		r.append(twilio.Hangup())
		return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)
	if (request.session['ivr2_sub_state'] == 'PracticeIVR_LeaveRegularMsg_Start'):
		# first iteration, getCallBackNumber
		request.session['ivr2_sub_state'] = 'PracticeIVR_LeaveRegularMsg_GetCallback'
		request.session['ivr2_returnOnHangup'] = \
			'MHLogin.DoctorCom.IVR.views_practice_v2.PracticeIVR_LeaveRegularMsg_New'
		return getCallBackNumberNew(request)
	elif request.session['ivr2_sub_state'] == 'PracticeIVR_LeaveRegularMsg_GetCallback':
		# second iteration, get Message recording
		request.session['ivr2_sub_state'] = 'PracticeIVR_LeaveRegularMsg_GetMsg'
		request.session['ivr2_Record_maxLength'] = 600  # 10 minutes
		request.session['ivr2_Record_leadSilence'] = 2
		request.session['ivr2_Record_promptOnce'] = True
		request.session['ivr2_Record_prompt_str'] = 'Please say your \
			non urgent message after the beep. Please state your name and \
			speak clearly. Press pound when finished.'
		request.session['ivr2_returnOnHangup'] = \
			'MHLogin.DoctorCom.IVR.views_practice_v2.PracticeIVR_LeaveRegularMsg_New'
		request.session.modified = True
		# Pass off the recording action to the getRecording function.
		return getQuickRecordingNew(request)
	else:
		# should never get here with unknown state
		logger.info('%s: PracticeIVR_LeaveRegularMsg_New called with state %s' % (
			request.session.session_key, request.session['ivr2_state']))
		request.session['ivr2_state'] = 'PracticeIVR_LeaveRegularMsg_New'
		return PracticeIVR_LeaveRegularMsg_New(request)


@TwilioAuthentication()
def PracticeIVR_Options_New(request, twilioResponse=None):
	"""
	Options Menu to change practice pin, name, greetings
	"""
	r = twilioResponse or twilio.Response()
	gather = twilio.Gather(finishOnKey='', numDigits=1, action=reverse('PracticeIVR_Options_Actions'))
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
def PracticeIVR_Options_Actions(request, internalCall=False):
	"""
	changes setting on doctor com number for practice
	"""
	#practice = PracticeLocation.objects.get(id=request.session['practice_id'])
	logger.debug('%s: PracticeIVR_Options_Actions POST data is %s' % (
		request.session.session_key, str(request.POST)))

	if (not internalCall and request.method == 'POST' and 'Digits' in request.POST):
		digits = request.POST['Digits']
		p = re.compile('[0-9#*]$')
		if (not p.match(digits)):
			r = twilio.Response()
			r.append(tts(_('I\'m sorry, I didn\'t understand that.')))
		elif (digits == '1'):
			# Change name
			request.session['ivr2_sub_state'] = 'PracticeIVR_Options_1'
			request.session.modified = True
			return changeNameNew(request)
		elif (digits == '3'):
			# Change closed greeting - ivr2_setup_stage to indicate which greeting
#			request.session['ivr2_setup_stage'] = 3  # deprecated
			request.session['ivr2_sub_state'] = 'PracticeIVR_Options_2'
			request.session.modified = True
			return changeGreetingNew(request)
		elif (digits == '5'):
			# change temporarily closed office greeting
#			request.session['ivr2_setup_stage'] = 5  # deprecated
			request.session['ivr2_sub_state'] = 'PracticeIVR_Options_3'
			request.session.modified = True
			return changeGreetingNew(request)
		elif (digits == '7'):
			# change pin
			request.session['ivr2_sub_state'] = 'PracticeIVR_Options_4'
			request.session.modified = True
			return changePinNew(request)
		elif (digits == '9'):
			# Return to the main menu
			r = twilio.Response()
			request.session['ivr2_state'] = 'PracticeIVR_TreeRoot_New'
			r.append(twilio.Redirect(reverse('PracticeIVR_TreeRoot_New')))
			return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)
		elif (digits == '*'):
			# Repeat menu
			r = twilio.Response()
			pass
		else:
			r = twilio.Response()
			r.append(tts(_('I\'m sorry, that wasn\'t a valid selection.')))
		return PracticeIVR_Options_New(request, r)
	else:
		# should never happen but if we get here, we log and goto main
		logger.debug('%s: PracticeIVR_Options_Actions is called with no post or digits' % (
			request.session.session_key))
		request.session['ivr2_state'] = 'PracticeIVR_Main_New'
		return PracticeIVR_Main_New(request)


@TwilioAuthentication()
def PracticeIVR_TreeRoot_New(request):
	"""
	will be called if it is practice manager calling and set up was done already
	update set up option only, we have no msgs on this number
	"""
	r = twilio.Response()
	#practice = PracticeLocation.objects.get(id=request.session['practice_id'])
	if ('Digits' in request.POST):
		logger.debug('%s: PracticeIVR_TreeRoot_New digits %s' % (
			request.session.session_key, request.POST['Digits']))
		digits = request.POST['Digits']
		p = re.compile('[0-9#*]$')
		if (not p.match(digits)):
			r.append(tts(_('I\'m sorry, I didn\'t understand that.')))
		elif (digits == '3'):
			request.session['ivr2_state'] = 'PracticeIVR_Options_New'
			request.session.modified = True
			return PracticeIVR_Options_New(request, r)
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


@TwilioAuthentication()
def PracticeIVR_OutsideInit_New(request, caller, called_manager, c2c_log=None):
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
	if (not 'ivr2_state' in request.session):
		request.session['ivr2_state'] = 'PracticeIVR_ForwardCall_New'

	# Deal with the called user values first
	request.session['Called'] = called_manager.user.mobile_phone
	request.session['provider_id'] = called_manager.user.id
	request.session.modified = True
	logger.debug('%s: PracticeIVR_OutsideInit_New caller %s called %s' % (
		request.session.session_key, caller, called_manager))

	# Now, deal with the caller values. Does the caller have a DoctorCom number?
	caller_mhluser = _getMHLUser(caller)
	caller_provider = None
	caller_manager = None

	if caller_mhluser:
		# if caller is provider, we mask the number
		caller_provider = _maskProviderCaller(request, caller_mhluser)
		if not caller_provider:
			#let's check if caller is office manager with phone
			caller_manager_qs = OfficeStaff.objects.filter(user=caller_mhluser)
			if (caller_manager_qs.exists()):
				caller_manager = caller_manager_qs.get()
			else:
				logger.debug('%s: called_manager_qs.exists() is False' % (
					request.session.session_key,))
	# Mask the caller's phone number with the DoctorCom number.
	if (not 'Caller' in request.session):
		logger.debug('%s: Defaulting caller ID to \'%s\'' % (
				request.session.session_key,
				settings.TWILIO_CALLER_ID
			))
		request.session['Caller'] = settings.TWILIO_CALLER_ID

	# Else, mask the caller's phone number with the DoctorCom number.
	#caller not a provider, must be office manager with cell phone
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
	# TODO:
	# Flesh out the logging here so that we pull appropriate objects.
	callSID = request.POST['CallSid']
	source = 'CC'
	log = _getOrCreateCallLog(request, callSID, caller, called_manager.user.mobile_phone, source, called_manager, caller_mhluser)
		#once removed c2c log, this should be removed
	if (c2c_log):
		log.c2c_entry_id = c2c_log.pk
	if (caller_provider):
		log.mdcom_caller = caller_provider
		logger.debug('%s: caller_provider is \'%s\'' % (
			request.session.session_key, str(caller_provider)))
	elif (caller_manager):
		log.mdcom_caller = caller_manager
		logger.debug('%s: caller_manager is \'%s\'' % (
				request.session.session_key, str(caller_manager)))
	else:
		log.mdcom_caller = caller_mhluser

	#if we are here, called must be office manager
	log.mdcom_called = called_manager
	log.save()
	# practice settings if any
	if 'practice_id' in request.session:
		try:
			practice = PracticeLocation.objects.get(id=request.session['practice_id'])
			gmttz = timezone('GMT')
			mytz = timezone(practice.time_zone)
			calltime_gmt = datetime.now(gmttz)
			calltime_local = calltime_gmt.astimezone(mytz)
			request.session['calltime_local_string'] = calltime_local.strftime("%Y-%m-%d %H:%M:%S")
			request.session['calltime_local'] = calltime_local
		except:
			pass


@TwilioAuthentication()
def PracticeIVR_ForwardCall_New(request, twilioResponse=None):
	"""
	Forward the call to the dialed user, there are no preferences
	for office managers, just call their cell phone
	Done in 3 steps:
	1. get caller name
	2. forward call
	3. if connected, done; if fail to connect, go to LeaveUrgentMsg_New
	"""
	provider = None
	forward = None
	try:
		provider = Provider.objects.get(id=request.session['provider_id'])
		if(not 'ProviderIVR_ForwardCall_forward' in request.session):
			request.session['ProviderIVR_ForwardCall_forward'] = provider.forward_anssvc
		forward = provider.forward_anssvc
	except Provider.DoesNotExist:
		pass
	logger.debug('%s: PracticeIVR_ForwardCall_New provider %s practice %s state %s substate %s' % (
		request.session.session_key, provider, request.session.get('practice_id', None), 
		request.session.get('ivr2_state', None), request.session.get('ivr2_sub_state', None)))

	callSID = request.POST['CallSid']
	# TODO - what if we don't get the callLog?
	log = callLog.objects.get(callSID=callSID)
	log.call_source = 'AS'
	log.save()

	if('click2call' in request.session):
		forward = 'MO'  # hack to keep click2call working

	if(forward == 'VM'):
		request.session['ivr2_state'] = 'PracticeIVR_LeaveUrgentMsg_New'
		logger.debug('%s: PracticeIVR_ForwardCall_New forward to VM - LeaveUrgentMsg_New to %s' % (
			request.session.session_key, provider))
		return PracticeIVR_LeaveUrgentMsg_New(request)

	r = twilioResponse or twilio.Response()
	if ('ivr2_sub_state' not in request.session):
		request.session['ivr2_sub_state'] = 'PracticeIVR_ForwardCall_Start'
	else:
		logger.debug('%s: PracticeIVR_ForwardCall_New sub_state %s' % (
			request.session.session_key, request.session['ivr2_sub_state']))
	# now we get caller name, dial and handle failure to connect by going to leave urgent message
	if (request.session['ivr2_sub_state'] == 'PracticeIVR_ForwardCall_Start'):
		request.session['ivr2_sub_state'] = 'PracticeIVR_ForwardCall_GetName'

		# Is the user a DoctorCom user with a recorded name?
		if (log.mdcom_caller and isinstance(log.mdcom_caller, Provider)):
			if (log.mdcom_caller.vm_config.count()):
				prov_vmconfig = log.mdcom_caller.vm_config.get()
				if (prov_vmconfig.config_complete):
					logger.debug('%s/%s sub %s: Found the caller\'s name! Forwarding call' % (
							request.session.session_key, request.session['ivr2_state'],
							request.session['ivr2_sub_state'],
						))
					log.caller_spoken_name = prov_vmconfig.name
					log.save()
					return PracticeIVR_ForwardCall_New(request, r)  # restart execution of this function
				else:
					logger.debug('%s/%s sub %s: Caller\'s vm_config incomplete!' % (
							request.session.session_key, request.session['ivr2_state'],
							request.session['ivr2_sub_state'],
						))
			else:
				logger.debug('%s/%s sub %s: An unsuitable number of vm_config objects found: %i' % (
						request.session.session_key, request.session['ivr2_state'],
						request.session['ivr2_sub_state'],
						log.mdcom_caller.vm_config.count(),
					))
		else:
			logger.debug('%s/%s sub %s: mdcom_caller %s either isn\'t defined or doesn\'t seem to be a Provider' % (
					request.session.session_key, request.session['ivr2_state'],
					request.session['ivr2_sub_state'],
					str(log.mdcom_caller),
				))

		# Okay, it's not a user with a name recording. Get one.
		request.session['ivr2_Record_prompt_str'] = 'Please say your name after the tone.'
		request.session['ivr2_Record_maxLength'] = 4
		request.session['ivr2_Record_timeout'] = 2
		request.session['ivr2_Record_leadSilence'] = 1
		return getQuickRecordingNew(request)

	elif (request.session['ivr2_sub_state'] == 'PracticeIVR_ForwardCall_GetName'):
		request.session['ivr2_sub_state'] = 'PracticeIVR_ForwardCall_Dial'
		# save caller name
		logger.debug('%s/%s: Set session to %s' % (
				request.session.session_key, request.session['ivr2_state'],
				request.session['ivr2_sub_state']
			))
		if (not log.caller_spoken_name):
			log.caller_spoken_name = request.session['ivr2_Record_recording']
			del request.session['ivr2_Record_recording']
			log.save()
		# now find the number to dial
		user_number = ''
		try:
			office_staff = OfficeStaff.objects.get(user=request.session['provider_id'])  # manager being called
			logger.debug('%s/%s: got office staff \'%s\' \'%s\' with id %s office phone \'%s\'.' % (
					request.session.session_key,
					request.session['ivr2_state'],
					office_staff.user.first_name,
					office_staff.user.last_name,
					office_staff.pk,
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
					request.session['ivr2_state'],
					user_number,
				))

		logger.debug('%s/%s: Tried to get called\'s number. Got \'%s\'' % (
				request.session.session_key,
				request.session['ivr2_state'],
				user_number,
			))

		dial = twilio.Dial(
				action=reverse('PracticeIVR_ForwardCall_New'),
				timeout=22,
				timeLimit=14400,  # 4 hours
				callerId=request.session['Caller'],
			)
		dial.append(twilio.Number(user_number,
				url=reverse('PracticeIVR_ForwardCall_Vet')
			))
		r.append(dial)
		r.append(twilio.Redirect(reverse('PracticeIVR_LeaveUrgentMsg_New')))
		return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)

	elif (request.session['ivr2_sub_state'] == 'PracticeIVR_ForwardCall_Dial'):
		del request.session['ivr2_sub_state']
		(clog, plog) = _getCallLogOrParent(request)
		if clog:
			logger.debug('%s/%s: PracticeIVR_ForwardCall_New state connected %s' % (
				request.session.session_key, request.session['ivr2_state'],
				str(clog.call_connected)))
		else:
			logger.debug('%s/%s: ProviderIVR_ForwardCall_New state no log SID %s' % (
				request.session.session_key, request.session['ivr2_state'],
				request.POST['CallSid']))
		if ('DialCallStatus' in request.POST):
			if (request.POST['DialCallStatus'] == 'completed'):
				# update child log call duration
				diallog = callLog.objects.get(callSID=request.POST['DialCallSid'])
				if diallog:
					diallog.call_duration = request.POST['DialCallDuration']
					diallog.save()
					logger.debug('%s: PracticeIVR_ForwardCall_New update child diallog dialSid %s duration %s' % (
						request.session.session_key, request.POST['DialCallSid'], request.POST['DialCallDuration']))
				else:
					logger.debug('%s: PracticeIVR_ForwardCall_New diallog not found: dialSid %s duration %s' % (
						request.session.session_key, request.POST['DialCallSid'], request.POST['DialCallDuration']))
				# Do nothing so that the second leg call continues un-interrupted
				return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)
		if (clog.call_connected):
			r.append(twilio.Hangup())
			return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)
		r.append(tts("The provider is not available right now."))
		r.append(twilio.Redirect(reverse('PracticeIVR_LeaveUrgentMsg_New')))
		# redirecting to LeaveUrgentMsg_New
		request.session['ivr2_state'] = 'PracticeIVR_LeaveUrgentMsg_New'
		return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)

	else:
		# else: Do nothing so that the call continues un-interrupted
		return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)


@TwilioAuthentication()
def PracticeIVR_ForwardCall_Vet(request):
	"""
	This function is executed on Number nouns within Dial verbs. The idea is to
	try to determine if it's a human who picked up, or a machine. Alternatively,
	this gives the called party a chance to send the call to voicemail without
	the caller knowing they're rejecting the call.
	"""
	logger.debug('%s: PracticeIVR_ForwardCall_Vet ' % (request.session.session_key))

	r = twilio.Response()
	# First, find the recording to play
	callSID = request.POST['CallSid']
	# second leg calls have their own callSIDs - may need parentCallSID
	(log, plog) = _getCallLogOrParent(request)

	if (request.method == 'POST' and 'Digits' in request.POST):
		# Connect the calls
		log.call_connected = True
		log.save()
		if plog:
			plog.call_connected = True
			plog.save()
			logger.debug('%s: PracticeIVR_ForwardCall_Vet update parent of logsid %s plogSID %s' %
				(request.session.session_key, log.callSID, plog.callSID))

		event = callEvent(callSID=callSID, event='C_ACC')
		event.save()

		return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)

	caller_spoken_name = log.caller_spoken_name

	gather = twilio.Gather(numDigits=1, finishOnKey='',
						action=reverse('PracticeIVR_ForwardCall_Vet'))
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
def PracticeIVR_Status(request):
	"""
	callback for call status at the end of call
	first we need to check if there are unhandled state we need to wrap up (mainly from getting recording)
	then we get the call back duration and fill the call log
	"""
	state = request.session.get('ivr2_state', 'None')
	logger.debug('%s: PracticeIVR_Status POST %s state is %s' %
		(request.session.session_key, str(request.POST), state))
#	if state == 'PracticeIVR_LeaveRegularMsg_New':
#		return PracticeIVR_LeaveRegularMsg_New(request)
#	elif state == 'PracticeIVR_LeaveUrgentMsg_New':
#		return PracticeIVR_LeaveUrgentMsg_New(request)
#	else:
	return _checkCallbackDuration(request)


@TwilioAuthentication()
def PracticeIVR_Main_New(request):
	"""
	entry point when call comes in to doctor.com number associated with Practice
	"""
	logger.debug('%s: PracticeIVR_Main_New POST data is %s' % (request.session.session_key, str(request.POST)))
#	logger.debug('%s: PracticeIVR_Main_New META data is %s' % (request.session.session_key, str(request.META)))

	# if call ended, we don't process anymore; just get call duration
	callEnded = _checkCallbackDuration(request)
	if callEnded:
		# we are done
		return callEnded
	request.session['answering_service'] = 'yes'

	(caller, called) = _setup_Main_callers(request)
	# set up practice_id in session
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

	# if caller is an existing user with doctorcom number, mask the caller number with doctorcom number
	caller_mhluser = _getMHLUser(caller)
	caller_provider = _maskProviderCaller(request, caller_mhluser)
	logger.debug('%s: PracticeIVR_Main_New practice %s caller %s provider %s' % (
		request.session.session_key, practice, caller_mhluser, caller_provider))

	# set up callLog if none is defined:
	callSID = request.POST['CallSid']
	log = _getOrCreateCallLog(request, callSID, caller, called, 'OC', practice, caller_mhluser)
	if caller_provider:
		log.mdcom_caller = caller_provider
	log.save()

	# setup session variables needed
	# request.session['practice'] = practice #removed, look up practice by id as needed, do not store objects in the session
	request.session['practice_id'] = practice.id
#	request.session['callgroup_id'] = practice.call_group.id
	if (practice.uses_original_answering_serice()):
		request.session['callgroup_id'] = practice.call_group.id  # ONLY for V 1 groups, for V2 determine based on user selection later
	request.session['practice_phone'] = practice.practice_phone
	request.session['ivr2_only_callbacknumber'] = False
	# done with initialization

############################################################################
	# see if this is office manager calling, if yes - goto set up
	# NOTE: compare phone numbers without country code if from the database vs. with country code if from twilio parameters
	# TO DO - MANAGERS CELL ALSO NEED TO BE ADDED
	if (request.session['practice_phone'] == caller
		or practice.accessnumber_set.filter(number=caller)):

	# Great, now we know that this is the owner calling in. First up, check to
	# see if the user has a configuration file and that they've completed setup
	#it is stored with practice location, for now act like first time

	# Now, check to ensure that user voicemail configuration was completed successfully.
		if (not practice.config_complete):
			request.session['ivr2_state'] = 'PracticeIVR_Setup_New'
			request.session.modified = True
			logger.debug('%s: PracticeIVR_Main_New need setup for practice %s' % (
				request.session.session_key, practice))
			return PracticeIVR_Setup_New(request)

	#config was complete, but call is made, ask if want to change settings
		else:
			#make sure they have pin for setting
			logger.debug('%s: PracticeIVR_Main_New setup complete; need auth for practice %s' % (
				request.session.session_key, practice))
			if (not 'authenticated' in request.session):
				request.session['ivr2_state'] = 'PracticeIVR_TreeRoot_New'
				request.session.modified = True
				r = twilio.Response()
				return authenticateSessionNew(request, r)

			request.session['ivr2_state'] = 'PracticeIVR_TreeRoot_New'
			request.session.modified = True
			logger.debug('%s: PracticeIVR_Main_New setup complete; need auth for practice %s' % (
				request.session.session_key, practice))
			return PracticeIVR_TreeRoot_New(request)

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
	return PracticeIVR_CallerResponse_New(request)  # both old and new way

