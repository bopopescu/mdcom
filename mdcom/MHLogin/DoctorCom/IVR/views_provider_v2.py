
import re

from django.conf import settings
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.core.mail import mail_admins
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from twilio import twiml as twilio

from models import VMBox_Config
from models import callLog, callEvent
from views_generic_v2 import authenticateSessionNew, _getCallLogOrParent, _copyStateVariables
from views_generic_v2 import _setup_Main_callers, _getOrCreateCallLog, _getMHLUser, _maskProviderCaller
from views_generic_v2 import changePinNew, changeNameNew, changeGreetingNew
from views_generic_v2 import playMessagesNew, getQuickRecordingNew, getRecordingNew

from MHLogin.MHLUsers.models import Provider, OfficeStaff
from MHLogin.utils.decorators import TwilioAuthentication
from MHLogin.utils.mh_logging import get_standard_logger

from MHLogin.DoctorCom.Messaging.models import MessageBodyUserStatus
from MHLogin.DoctorCom.IVR.utils import save_message, _checkCallbackDuration, _makeUSNumber
from MHLogin.DoctorCom.speech.utils import tts

# Setting up logging
logger = get_standard_logger('%s/DoctorCom/IVR/views_provider_v2.log' % (settings.LOGGING_ROOT),
	'DCom.IVR.views_prov', settings.LOGGING_LEVEL)

# new refactored calls to cater for Twilio API 2010-04-01 version
# revised from views_provider.py
#
# The request.session dictionary is heavily used through this codebase. Since
# this is a pretty opaque data structure, we should maintain a list of keys
# here. If you add keys to the dictionary, make sure to note it here.
#
# General Variables
# --------------------------------------------
# authenticated - Whether or not the user is authenticated. If the key exists,
#	   then assume the user is authenticated, regardless of its value. unchanged from prior version
# Called - The phone number the caller is trying to reach. (aka To)
# Caller - The callerID of the person who is calling in. (aka From)
# ivr2_state - The state of call processing tree. IT IS NOT A STACK
# The processing takes the form of a state machine with substates for call subtrees. 
# E.g. The main state is ProviderIVR_Main_New which fans out to:
# by ProviderIVR_TreeRoot_XXX (for main call tree), ProviderIVR_Setup_XXX (for VM setup), 
# ProviderIVR_Options_XXX
# 3 generic functional groups:
# 1. setup/options handling - handling of configuration (pin, name, greetings)
# 2. Voicemail management - listening to messages
# 3. caller handling - outside or other callers
# For each tree/subtree, there are 3 steps:
# 1. gathering what we pass to twilio (start state)
# 2. option processing - where we check what we get from twilio;
#    twilio calls back here with a URLConf name that reverse()
#    may be run on it and an appropriate URL be returned to Twilio. The
#    current convention is to use the function name for the URLConf name.
# 3. actions - where actual processing for the valid options are done
#
# Object IDs
# --------------------------------------------
# config_id - The ID of the VMBox_Config object ID for this voicemail box.
# provider_id - The ID of the provider whose voicemail box this is.


def _getUniqueProvider(number):
	"""
	Fetches provider object based on number passed; must be unique or we raise exception
	returns Provider
	"""
	logger.debug(': _getUniqueProvider is called with %s' % (number))

	provider = Provider.objects.filter(mdcom_phone=number)
	if provider.count() != 1:
		# If we don't allow multiple providers having same mdcom_phone it should
		# be unique in model, this code just logs more information than previously.
		if provider.count() > 1:
			msg = 'Multiple providers have mdcom_phone: %s, providers: %s' % \
					(number, ', '.join("%s" % p for p in provider))
			logger.error(msg)
			raise Exception(msg)
		else:
			msg = 'No providers have mdcom_phone %s' % (number,)
			logger.error(msg)
			raise Exception(msg)

	provider = provider[0]
	return provider


def _getProviderVMConfig(provider):
	"""
	given a provider, we get or create a its vm_config
	"""
	try:
		config = provider.vm_config.get()
	except MultipleObjectsReturned:
		raise Exception("Provider %s %s has multiple vm_config objects." % (
			provider.user.first_name, provider.user.last_name))
	except ObjectDoesNotExist:
		config = VMBox_Config()
		config.owner = provider
		config.save()
	return config


def _makeGreeting(number=None):
	if number:
		spoken_number = []
		[spoken_number.extend([i, ' ']) for i in number]
		spoken_number.pop()  # drop the last element
		spoken_number.insert(5, ',')
		spoken_number.insert(12, ',')
		greetings = ('The person at %s is not available. ' +
			'Please leave a message after the beep. Press pound ' +
			'when finished for options.') % (''.join(spoken_number),)
	else:
		greetings = ('The user is not available. ' +
			'Please leave a message after the beep. Press pound when finished for options.')
	return greetings


@TwilioAuthentication()
def ProviderIVR_Setup_New(request, provider=None):
	"""
	New version of ProviderIVR_Setup processing. This is done in 4 consecutive steps:
	0. initial sub state: ProviderIVR_Setup_Start
	1. setup pin
	2. setup Name
	3. setup Greeting
	We use generic calls to setup Pin, Name and Greeting, but use ivr2_state
	to direct the return calls here so it could be redirected to the next step
	"""
	# we always need provider
	assert(request.session['provider_id'])
	assert(request.session['ivr2_state'] == 'ProviderIVR_Setup_New')
	if (provider == None):
		provider = Provider.objects.get(id=request.session['provider_id'])
	# we also need VMBox_config's config_id 
	if (not 'config_id' in request.session):
		config = _getProviderVMConfig(provider)
		request.session['config_id'] = config.id

	logger.debug('%s: ProviderIVR_Setup_New state %s provider %s config %s' % (
		request.session.session_key, request.session['ivr2_state'], provider, request.session['config_id']))
	if ('ivr2_sub_state' not in request.session):
		# new setup processing
		request.session['ivr2_sub_state'] = 'ProviderIVR_Setup_Start'
	else:
		logger.debug('%s: ProviderIVR_Setup_New sub_state %s' % (
			request.session.session_key, request.session['ivr2_sub_state']))
	if (request.session['ivr2_sub_state'] == 'ProviderIVR_Setup_Start'):
		# set up pin
		r = twilio.Response()
		r.append(twilio.Pause())  # one second pause keeps the first words from getting cut off.
		request.session['ivr2_prompt_str'] = "Welcome to your voicemail account. It "\
			"looks like some setup is needed. Let's get started. First, we need to "\
			"set up your pin number."
		event = callEvent(callSID=request.POST['CallSid'], event='I_STR')
		event.save()
		request.session['ivr2_sub_state'] = 'ProviderIVR_Setup_Pin'
		return changePinNew(request, r)

	elif (request.session['ivr2_sub_state'] == 'ProviderIVR_Setup_Pin'):
		request.session['ivr2_sub_state'] = 'ProviderIVR_Setup_Name'
		return changeNameNew(request, 'Now, we need to record your name.')

	elif (request.session['ivr2_sub_state'] == 'ProviderIVR_Setup_Name'):
		request.session['ivr2_sub_state'] = 'ProviderIVR_Setup_Greeting'
		return changeGreetingNew(request, 'Finally, we need to set up a greeting.')

	elif (request.session['ivr2_sub_state'] == 'ProviderIVR_Setup_Greeting'):
		# setup is complete - automatically "log" user in
		request.session['authenticated'] = True
		del request.session['ivr2_sub_state']
		request.session['ivr2_state'] = 'ProviderIVR_TreeRoot_New'
		config = VMBox_Config.objects.get(id=request.session['config_id'])
		config.config_complete = True
		config.save()

		event = callEvent(callSID=request.POST['CallSid'], event='I_FIN')
		event.save()
		logger.debug('%s: ProviderIVR_Setup is complete config %s' % (
			request.session.session_key, config))
		# we don't need the welcome msg anymore
		if ('ivr2_prompt_str' in request.session):
			del request.session['ivr2_prompt_str']
		r = twilio.Response()
		r.append(tts('Your voice mail account is now set up. You may hang up '
			'now, or stay on the line to be taken to your voice mail box home.'))
		# after VM Setup, we go to main
		r.append(twilio.Redirect(reverse('ProviderIVR_TreeRoot_New')))
		return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)

	else:
		# should not get here with unknown state - log state and return to main
		logger.debug('%s: ProviderIVR_Setup has unhandled state set to %s' % (
			request.session.session_key, request.session['ivr2_state']))
		request.session['ivr2_state'] = 'ProviderIVR_Main_New'
		return ProviderIVR_Main_New(request)


@TwilioAuthentication()
def ProviderIVR_Options_New(request, twilioResponse=None):
	"""
	Options Menu to change VM settings
	Sets up what we say to user for options choices
	"""
	r = twilioResponse or twilio.Response()
	request.session['ivr2_state'] = 'ProviderIVR_Options_New'
	# reset sub_state
	if ('ivr2_sub_state' in request.session):
		del request.session['ivr2_sub_state']
	gather = twilio.Gather(finishOnKey='', numDigits=1, action=reverse('ProviderIVR_Options_Actions'))
	gather.append(tts('Options menu'))
	gather.append(tts('To re-record your name, press 1'))
	gather.append(tts('To record a new greeting, press 3'))
	gather.append(tts('To change your pin, press 5'))
	gather.append(tts('To return to the main menu, press 9'))
	gather.append(tts('To repeat this menu, press star'))
	r.append(gather)
	return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)


@TwilioAuthentication()
def ProviderIVR_Options_Actions(request):
	"""
	Options to change VM settings - twilio calls back here
	We do the option processing here
	We track the ivr2_sub_state so we know where recording and pin go since
	we call the same method for setup
	"""
	assert(request.session['provider_id'])
	assert(request.session['ivr2_state'] == 'ProviderIVR_Options_New')
	provider = Provider.objects.get(id=request.session['provider_id'])
	logger.debug('%s: ProviderIVR_Options_Actions provider %s POST data is %s' % (
		request.session.session_key, provider, str(request.POST)))
	r = twilio.Response()
	if (request.method == 'POST' and 'Digits' in request.POST):
		digits = request.POST['Digits']
		p = re.compile('[0-9#*]$')
		if (not p.match(digits)):
			r.append(tts('I\'m sorry, I didn\'t understand that.'))
		elif (digits == '1'):
			# Change name
			event = callEvent(callSID=request.POST['CallSid'], event='F_NCH')
			request.session['ivr2_sub_state'] = 'ProviderIVR_Options_1'			
			return changeNameNew(request)
		elif (digits == '3'):
			# Change greeting
			event = callEvent(callSID=request.POST['CallSid'], event='F_GCH')
			request.session['ivr2_sub_state'] = 'ProviderIVR_Options_3'			
			return changeGreetingNew(request)
		elif (digits == '5'):
			# change pin
			event = callEvent(callSID=request.POST['CallSid'], event='F_PCH')
			request.session['ivr2_sub_state'] = 'ProviderIVR_Options_5'			
			return changePinNew(request)
		elif (digits == '9'):
			# Return to the main menu
			request.session['ivr2_state'] = 'ProviderIVR_TreeRoot_New'
			r.append(twilio.Redirect(reverse('ProviderIVR_TreeRoot_New')))
			return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)
		elif (digits == '*'):
			# Repeat menu
			pass
		else:
			r.append(tts('I\'m sorry, that wasn\'t a valid selection.'))
		return ProviderIVR_Options_New(request, r)
	else:
		# should never happen - but if we get here without Digits, we log and go back to Main
		logger.debug('%s: ProviderIVR_TreeRoot_Actions is called with no post or digits' % (
			request.session.session_key))
		request.session['ivr2_state'] = 'ProviderIVR_Main_New'
		return ProviderIVR_Main_New(request)


@TwilioAuthentication()
def ProviderIVR_TreeRoot_New(request, provider=None, twilioResponse=None):
	"""
	call tree of a provider:
	1 to listen to all msgs;
	2 to listen to urgent msgs
	3 to listen to voice mail
	4 to manage voicemail settings
	* to repeat menu
	Require: session variable: provider_id to be set
	Require: request.session['ivr2_state'] == ProviderIVR_TreeRoot_New
	sets up twilio response with message and url to go to ProviderIVR_TreeRoot_Actions
	"""
	if (provider == None):
		provider = Provider.objects.get(id=request.session['provider_id'])
	logger.debug('%s: ProviderIVR_TreeRoot_New prov %s' % 
		(request.session.session_key, provider))
	request.session['ivr2_state'] = 'ProviderIVR_TreeRoot_New'
	unread_anssvc_msg_count = MessageBodyUserStatus.objects.filter(user=provider.user,
		read_flag=False, delete_flag=False, msg_body__message___resolved_by=None,
			msg_body__message__message_type='ANS').count()
	unread_msg_count = MessageBodyUserStatus.objects.filter(user=provider.user,
			read_flag=False, delete_flag=False, msg_body__message___resolved_by=None,
				msg_body__message__message_type='VM').count()
	saved_msg_count = MessageBodyUserStatus.objects.filter(user=provider.user, read_flag=True,
			delete_flag=False, msg_body__message___resolved_by=None,
				msg_body__message__message_type='VM').count()
	saved_anssvc_msg_count = MessageBodyUserStatus.objects.filter(user=provider.user,
			read_flag=True, delete_flag=False, msg_body__message___resolved_by=None,
				msg_body__message__message_type='ANS').count()
	logger.debug('%s: ProviderIVR_TreeRoot_New msg counts %d, %d, %d, %d' % 
		(request.session.session_key, unread_anssvc_msg_count, unread_msg_count,
			saved_msg_count, saved_anssvc_msg_count))

	say_str = []
	say_str.append('You have %i new, and %i saved urgent messages,' % (
						unread_anssvc_msg_count, saved_anssvc_msg_count))
	say_str.append(' ')
	say_str.append('and %i new, and %i saved voice messages,' % (unread_msg_count, saved_msg_count))

	if (any((unread_msg_count, unread_anssvc_msg_count, saved_msg_count, saved_anssvc_msg_count))):
		say_str.append('To listen to all your messages, press one. ')
		say_str.append('To listen to your urgent messages, press two. ')
		say_str.append('To listen to your voice mail, press three. ')

	r = twilioResponse or twilio.Response()
	gather = twilio.Gather(action=reverse('ProviderIVR_TreeRoot_Actions'), finishOnKey='', numDigits=1)
	gather.append(tts(''.join(say_str)))
	gather.append(tts('To manage your voicemail settings, press four.'))
	gather.append(tts('To repeat this menu, press star.'))
	r.append(gather)
	return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)


@TwilioAuthentication()
def ProviderIVR_TreeRoot_Actions(request):
	"""
	called after IVR_TreeRoot_New for Main calltree related operations
	gets and checks choice digit from user and do the next step
	"""
	assert(request.session['provider_id'])
	provider = Provider.objects.get(id=request.session['provider_id'])
	logger.debug('%s: ProviderIVR_TreeRoot_Actions Provider %s POST data is %s' % (
		request.session.session_key, provider, str(request.POST)))

	r = twilio.Response()
	if (request.method == 'POST' and 'Digits' in request.POST):
		digits = request.POST['Digits']
		p = re.compile('[0-9#*]$')
		if (not p.match(digits)):
			r.append(tts('I\'m sorry, I didn\'t understand that.'))
			# invalids - go back to tree root
			return ProviderIVR_TreeRoot_New(request, provider, r)
		elif (digits == '1'):
			# all messages
			messages = MessageBodyUserStatus.objects.filter(user=provider.user,
				delete_flag=False, msg_body__message___resolved_by=None,
				msg_body__message__message_type__in=('ANS', 'VM'))
			if (messages == [] or len(messages) == 0):
				return ProviderIVR_TreeRoot_New(request, provider, r)
			else:
				request.session['ivr2_state'] = 'ProviderIVR_TreeRoot_New'
				return playMessagesNew(request, messages, r)
		elif (digits == '2'):
			# urgent msgs
			messages = MessageBodyUserStatus.objects.filter(user=provider.user,
				delete_flag=False, msg_body__message___resolved_by=None,
				msg_body__message__message_type__in=('ANS',))
			if (messages == [] or len(messages) == 0):
				return ProviderIVR_TreeRoot_New(request, provider, r)
			else:
				request.session['ivr2_state'] = 'ProviderIVR_TreeRoot_New'
				return playMessagesNew(request, messages, r)
		elif (digits == '3'):
			# voicemail
			messages = MessageBodyUserStatus.objects.filter(user=provider.user,
				delete_flag=False, msg_body__message___resolved_by=None,
				msg_body__message__message_type__in=('VM',))
			if (messages == [] or len(messages) == 0):
				return ProviderIVR_TreeRoot_New(request, provider, r)
			else:
				request.session['ivr2_state'] = 'ProviderIVR_TreeRoot_New'
				return playMessagesNew(request, messages, r)
		elif (digits == '4'):
			# manage VM Settings
			request.session['ivr2_state'] = 'ProviderIVR_Options_New'
			return ProviderIVR_Options_New(request, r)
		elif (digits == '*'):
			return ProviderIVR_TreeRoot_New(request, provider, r)
		else:
			r.append(tts('I\'m sorry, I didn\'t understand that.'))
			return ProviderIVR_TreeRoot_New(request, provider, r)
	else:
		# should never happen - but if we get here without Digits, we log and go back to Main
		logger.debug('%s: ProviderIVR_TreeRoot_Actions is called with no post or digits' % (
			request.session.session_key))
		request.session['ivr2_state'] = 'ProviderIVR_Main_New'
		return ProviderIVR_Main_New(request)


@TwilioAuthentication()
def ProviderIVR_LeaveMsg_New(request, twilioResponse=None):
	"""
	Sets up to record a voicemail message with provider's greeting
	(or anonymous one if VMBox is not set).
	This can be from a provider - in which case we get the callback number
	from the provider's mdcom_phone (mask original caller number)
	Or it could be an external call, in which case we get the callback number 
	from session variable ivr2_Record_callbacknumber which we collect when we 
	call getRecordingNew
	step1: get name or callback number
	step2: get message from caller through twilio

	Arguments:
		request - The standard Django request argument

	request.session Keys:
		provider_id - The ID of the Provider user who owns this voicemail box.
	"""
	provider = Provider.objects.get(id=request.session['provider_id'])
	r = twilioResponse or twilio.Response()
	# check if vmbox config - has greeting set for provider that we can play for the caller
	# otherwise, say user at phone number is not available - please leave a message
	config_complete = provider.vm_config.count() == 1 and provider.vm_config.get().config_complete
	# get vm_config for provider to get greeting
	logger.debug('%s: ProviderIVR_LeaveMsg_New prov %s state %s config complete %s' % (
		request.session.session_key, provider, request.session['ivr2_state'], config_complete))
	config = None
	if (config_complete):
		config = provider.vm_config.get()
		p = re.compile('http')
		if (p.match(config.greeting)):
			# This is a Twilio recording.
			request.session['ivr2_Record_prompt_url'] = config.greeting
		else:
			# TODO:
			raise Exception('Unimplemented playback of local files')
	else:
		if (not 'Called' in request.session or (not request.session['Called'])):
			request.session['ivr2_Record_prompt_str'] = _makeGreeting()
		else:
			request.session['ivr2_Record_prompt_str'] = _makeGreeting(request.session['Called'])
	if ('ivr2_Record_prompt_url' in request.session):
		logger.debug('%s: ProviderIVR_LeaveMsg_New greeting url %s' % (
			request.session.session_key, request.session['ivr2_Record_prompt_url']))
	else:  # assume prompt str
		logger.debug('%s: ProviderIVR_LeaveMsg_New greeting str %s' % (
			request.session.session_key, request.session['ivr2_Record_prompt_str']))

	request.session['ivr2_Record_maxLength'] = 120  # 2 minutes
	request.session['ivr2_Record_leadSilence'] = 2
	request.session['ivr2_Record_promptOnce'] = True
	# where do we come back to after leaving a message
	request.session['ivr2_returnOnHangup'] = 'MHLogin.DoctorCom.IVR.views_provider_v2.ProviderIVR_LeaveMsg_Action'
	request.session['ivr2_state'] = 'ProviderIVR_LeaveMsg_New'
	request.session.modified = True

	# Pass off the recording action to the getRecording function to get the message.
	return getRecordingNew(request, r)


@TwilioAuthentication()
def ProviderIVR_LeaveMsg_Action(request):
	"""
	Step 2 of ProviderIVR_LeaveMsg_New - we get called back from getRecording process
	based on ivr2_state. We save the message recorded and continue
	TODO: if caller is a provider, we want to be able to hit the # key to go back to his voice mailbox
	"""
	provider = Provider.objects.get(id=request.session['provider_id'])
	logger.debug('%s: ProviderIVR_LeaveMsg_Action provider %s state %s POST data %s' % (
		request.session.session_key, provider,
		request.session.get('ivr2_state', 'None'), str(request.POST)))

	callEnded = _checkCallbackDuration(request, False)
	if ('ivr2_Record_recording' in request.session):
		# if caller is provider, we mask the callbacknumber; otherwise, show it in message
		provider_qs = Provider.objects.filter(mobile_phone=request.session['Caller'])
		if(provider_qs):
			request.session['ivr2_Record_callbacknumber'] = provider_qs[0].mdcom_phone
			subject = "Voice Mail from %s %s" % (provider_qs[0].first_name, provider_qs[0].last_name)
		else:
			request.session['ivr2_Record_callbacknumber'] = request.session['Caller']
			subject = "Voice Mail from %s" % request.session['ivr2_Record_callbacknumber']

		# set up for save_message
		request.session['ivr_makeRecording_recording'] = request.session['ivr2_Record_recording']
		if ('ivr2_Record_callbacknumber' in request.session):
			request.session['ivr_makeRecording_callbacknumber'] = request.session['ivr2_Record_callbacknumber']
			del request.session['ivr2_Record_callbacknumber']
			logger.debug('%s: ProviderIVR_LeaveMsg_Action recording url: %s callback %s' % (
				request.session.session_key, request.session['ivr_makeRecording_recording'],
				request.session['ivr_makeRecording_callbacknumber']))
		else:
			logger.debug('%s: ProviderIVR_LeaveMsg_Action recording url: %s ' % (
				request.session.session_key, request.session['ivr_makeRecording_recording']))
		_copyStateVariables(request)
		save_message(request, subject, [provider.user], None,  "VM", False)
		del request.session['ivr2_Record_recording']

		r = twilio.Response()
		r.append(tts('Good bye'))
		r.append(twilio.Hangup())
		return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)
	else:
		# no recording? user might have hung up
		logger.debug('%s: ProviderIVR_LeaveMsg_Action is called with no recording for provider %s' % (
							request.session.session_key, request.session['provider_id']))
		r = twilio.Response()
		return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)


@TwilioAuthentication()
def ProviderIVR_ForwardCall_New(request, provider=None, twilioResponse=None):
	"""
	new version of ProviderIVR_ForwardCall - forward call to dialed user as per user preference
	called by ProviderIVR_Main_New
	Steps:
	1. get name
	2. Dial - based on provider.forward_voicemail state to Mobile, office, other (VM already handled)
	3. After dialed: handle failure by going to LeaveMsg or hangup?
	"""
	assert(request.session['provider_id'])
	provider = Provider.objects.get(id=request.session['provider_id'])
	logger.debug('%s: ProviderIVR_ForwardCall_New is initiated provider %s state %s substate %s POST %s' % (
		request.session.session_key, provider, request.session.get('ivr2_state', None), 
		request.session.get('ivr2_sub_state', None), str(request.POST)))
	callEnded = _checkCallbackDuration(request, False)

	# check user forwarding preference
	forward = provider.forward_voicemail
	if (forward == 'VM'):
		# go to voicemail
		request.session['ivr2_state'] = 'ProviderIVR_LeaveMsg_New'
		logger.debug('%s: ProviderIVR_ForwardCall_New forwarding to voicemail of %s' % (
			request.session.session_key, provider))
		return ProviderIVR_LeaveMsg_New(request)

	# State processing - 1. get caller name or ask for it
	r = twilioResponse or twilio.Response()
	if ('ivr2_sub_state' not in request.session):
		request.session['ivr2_sub_state'] = 'ProviderIVR_ForwardCall_Start'
	else:
		logger.debug('%s: ProviderIVR_ForwardCall_New sub_state %s' % (
			request.session.session_key, request.session['ivr2_sub_state']))
	if (request.session['ivr2_sub_state'] == 'ProviderIVR_ForwardCall_Start'):
		request.session['ivr2_sub_state'] = 'ProviderIVR_ForwardCall_GetName'
		# is this a doctorcom user with recorded name?
		callSID = request.POST['CallSid']
		log = callLog.objects.get(callSID=callSID)
		if (log.mdcom_caller and isinstance(log.mdcom_caller, Provider)):
			if (log.mdcom_caller.vm_config.count()):
				prov_vmconfig = log.mdcom_caller.vm_config.get()
				if (prov_vmconfig.config_complete):
					logger.debug('%s/%s: Found the caller\'s name!' % (
							request.session.session_key,
							request.session['ivr2_state'],
						))
					log.caller_spoken_name = prov_vmconfig.name
					log.save()
					# got the recorded name; just go back to the next step - Dial
					return ProviderIVR_ForwardCall_New(request, provider, r)  # next step
				else:
					logger.debug('%s/%s: ProviderIVR_ForwardCall_New GetName: Caller\'s '
						'vm_config incomplete!' % (request.session.session_key, 
							request.session['ivr2_state']))
			else:
				logger.debug('%s/%s: ProviderIVR_ForwardCall_New GetName: unsuitable '
					'number of vm_config objects found: %i' % (request.session.session_key, 
						request.session['ivr2_state'], log.mdcom_caller.vm_config.count()))
		else:
			logger.debug('%s/%s: ProviderIVR_ForwardCall_New GetName: mdcom_caller %s '
				'either isn\'t defined or doesn\'t seem to be a Provider' % 
					(request.session.session_key, request.session['ivr2_state'], 
						str(log.mdcom_caller)))

		# Not a user with a name recording. Get one.
		# ivr2_state already set to ProviderIVR_ForwardCall_GetName
		request.session['ivr2_Record_prompt_str'] = 'Please say your name after the tone.'
		request.session['ivr2_Record_maxLength'] = 4
		request.session['ivr2_Record_timeout'] = 2
		request.session['ivr2_Record_leadSilence'] = 1
		return getQuickRecordingNew(request)

	elif (request.session['ivr2_sub_state'] == 'ProviderIVR_ForwardCall_GetName'):
		request.session['ivr2_sub_state'] = 'ProviderIVR_ForwardCall_Dial'
		# save the caller name
		callSID = request.POST['CallSid']
		log = callLog.objects.get(callSID=callSID)
		if (not log.caller_spoken_name):
			log.caller_spoken_name = request.session['ivr2_Record_recording']
			del request.session['ivr2_Record_recording']
			log.save()
		# Okay, let's find number to dial!
		user_number = None
		if (forward == 'MO'):
			user_number = provider.user.mobile_phone
		elif (forward == 'OF'):
			user_number = provider.office_phone
		elif (forward == 'OT'):
			user_number = provider.user.phone
		logger.debug('%s/%s: ProviderIVR_ForwardCall_New Dial user number is \'%s\' forward %s' % (
				request.session.session_key, request.session['ivr2_state'], user_number, forward))

		if (not user_number):
			# no flags were set.
			if (provider.user.mobile_phone):
				user_number = provider.user.mobile_phone
			else:
				return ProviderIVR_LeaveMsg_New(request, r)
		# when dial action is done, we go back to its actionurl - which is here with state Dial
		dial = twilio.Dial(
				action=reverse('ProviderIVR_ForwardCall_New'),
				timeout=22,
				timeLimit=14400,  # 4 hours
				callerId=_makeUSNumber(request.session['Caller'])
			)
		# we also want to allow call vetting
		dial.append(twilio.Number(user_number,
				url=reverse('ProviderIVR_ForwardCall_Vet')))
		r.append(dial)
		# If the call did not connect, we go to LeaveMsg
		r.append(twilio.Redirect(reverse('ProviderIVR_LeaveMsg_New')))
		return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)

	elif (request.session['ivr2_sub_state'] == 'ProviderIVR_ForwardCall_Dial'):
		# done with forward call
		del request.session['ivr2_sub_state']
		# need to get parent call log for caller and connected; also update child log for duration
		(log, plog) = _getCallLogOrParent(request)
		if log:
			logger.debug('%s/%s: ProviderIVR_ForwardCall_New state connected %s' % (
				request.session.session_key, request.session['ivr2_state'],
				str(log.call_connected)))
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
					logger.debug('%s: ProviderIVR_ForwardCall_New update child diallog '
						'dialSid %s duration %s' % (request.session.session_key, 
							request.POST['DialCallSid'], request.POST['DialCallDuration']))
				else:
					logger.debug('%s: ProviderIVR_ForwardCall_New diallog not found: dialSid %s duration %s' % (
						request.session.session_key, request.POST['DialCallSid'], request.POST['DialCallDuration']))
				# Do nothing so that the second leg call continues un-interrupted
				return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)
			else:
				# (request.POST['DialCallStatus'] != 'completed'):
				logger.debug('%s/%s: ProviderIVR_ForwardCall_New DialStatus not answered' % (
					request.session.session_key, request.session['ivr2_state']))
				if (request.POST['DialCallStatus'] == 'failed'):
					# TODO: Figure out how to deal with connection problems. Most
					# likely, send an email to the user and administrators.
					logger.debug('%s/%s: ProviderIVR_ForwardCall_New DialStatus failed' % (
						request.session.session_key, request.session['ivr2_state']))
					subject = 'ProviderIVR_ForwardCall Call Forward DialStatus Fail'
					message = 'ProviderIVR_ForwardCall got DialStatus failed. Post data: %s' \
						% (str(request.POST),)
					mail_admins(subject=subject, message=message, fail_silently=False)
				# else request.POST['DialStatus'] == 'busy' or request.POST['DialStatus'] == 'no-answer'
				return ProviderIVR_LeaveMsg_New(request, r)
		# if we connected (in Vet), we hang up here
		if (log.call_connected):
			r.append(twilio.Hangup())
			return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)
		# if not connected, we go to LeaveMsg
		return ProviderIVR_LeaveMsg_New(request, r)


@TwilioAuthentication()
def ProviderIVR_ForwardCall_Vet(request):
	"""
	This function is executed on Number nouns within Dial verbs. The idea is to
	try to determine if it's a human who picked up, or a machine. Alternatively,
	this gives the called party a chance to send the call to voicemail without
	the caller knowing they're rejecting the call.
	"""
	logger.debug('%s: ProviderIVR_ForwardCall_Vet POST %s' %
		(request.session.session_key, str(request.POST)))

	r = twilio.Response()
	callSID = request.POST['CallSid']
	# second leg calls have their own callSIDs - may need parentCallSID
	(log, plog) = _getCallLogOrParent(request)

	if (request.method == 'POST' and 'Digits' in request.POST):
		# Connect the calls, get parent log if any
		if log:
			logger.debug('%s: ProviderIVR_ForwardCall_Vet connected callsid %s logSID %s' %
				(request.session.session_key, callSID, log.callSID))
			log.call_connected = True
			log.save()
			if plog:
				plog.call_connected = True
				plog.save()
				logger.debug('%s: ProviderIVR_ForwardCall_Vet update parent of logsid %s plogSID %s' %
					(request.session.session_key, log.callSID, plog.callSID))

		else:
			logger.debug('%s: ProviderIVR_ForwardCall_Vet connected log not found %s' %
				(request.session.session_key, callSID))

		event = callEvent(callSID=request.POST['CallSid'], event='C_ACC')
		event.save()

		return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)

	if log:
		caller_spoken_name = log.caller_spoken_name
		if (log.mdcom_caller):
			# Great. Is it a Provider?
			if (isinstance(log.mdcom_caller, Provider) and log.mdcom_caller.vm_config.count()):
				vm_config = log.mdcom_caller.vm_config.get()
				if (vm_config.config_complete):
					caller_spoken_name = vm_config.name
	else:
		logger.debug('%s: ProviderIVR_ForwardCall_Vet call log sid %s not found' % 
			(request.session.session_key, callSID))

	gather = twilio.Gather(numDigits=1, finishOnKey='', 
		action=reverse('ProviderIVR_ForwardCall_Vet'))
	gather.append(tts("You have a call from"))
	gather.append(twilio.Play(caller_spoken_name))
	gather.append(tts("Press any key to accept."))
	r.append(gather)
	r.append(twilio.Hangup())

	return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)


@TwilioAuthentication()
def ProviderIVR_OutsideInit_New(request, caller, called_provider, c2c_log=None):
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
	# hack-ish - we need to pass in where we are going from init - right now, we usually 
	# go to ProviderIVR_ForwardCall_New
	if (not 'ivr2_state' in request.session):
		request.session['ivr2_state'] = 'ProviderIVR_ForwardCall_New'

	# Deal with the called user values first
	request.session['Called'] = called_provider.mdcom_phone
	request.session['provider_id'] = called_provider.id

	logger.debug('%s: ProviderIVR_OutsideInit_New POST data is %s' % (
		request.session.session_key, str(request.POST)))

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
				logger.debug('%s: called_manager_qs..exists() is False' % (
					request.session.session_key,))
	# Mask the caller's phone number with the DoctorCom number.
	if (not 'Caller' in request.session):
		logger.debug('%s: Defaulting caller ID to \'%s\'' % (
				request.session.session_key,
				settings.TWILIO_CALLER_ID
			))
		request.session['Caller'] = settings.TWILIO_CALLER_ID

	logger.debug('%s: ProviderIVR_OutsideInit_New caller %s called %s provider %s' % 
		(request.session.session_key, request.session['Caller'], request.session['Called'], 
			request.session['provider_id']))

	# Flesh out the logging here so that we pull appropriate objects.
	callSID = request.POST['CallSid']
	log = _getOrCreateCallLog(request, callSID, caller, called_provider.mdcom_phone, 
			'CC', called_provider, caller_mhluser)
	if c2c_log:
		log.c2c_entry_id = c2c_log.pk
	if (caller_provider):
		log.mdcom_caller = caller_provider
		logger.debug('%s: caller_provider is \'%s\'' % (
				request.session.session_key, str(caller_provider)))
	elif (caller_manager):
		log.mdcom_caller = caller_manager
		logger.debug('%s: caller_manager is \'%s\'' % (
				request.session.session_key, str(caller_manager)))
	log.save()


@TwilioAuthentication()
def ProviderIVR_Status(request):
	"""
	callback for call status at the end of call
	first we need to check if there are unhandled state we need to wrap up
	then we get the call back duration and fill the call log
	"""
	logger.debug('%s: ProviderIVR_Status POST data is %s' % 
		(request.session.session_key, str(request.POST)))
#	state = request.session.get('ivr2_state', 'None')
#	logger.debug('%s: ProviderIVR_Status state is %s' %
#		(request.session.session_key, state))
	# wrap up if user was in the process of leaving a msg
	return _checkCallbackDuration(request, returnflag=True)


@TwilioAuthentication()
def ProviderIVR_Main_New(request):
	"""
	initial call into provider -- Only called with new Twilio 2010 API
	initializes caller, called, provider_id, callLog and mask caller number with 
	doctorcom Number if caller has a doctorcom number
	I leave the numbers with + and country code but strip them off the number of 
	caller/called when we lookup the database for provider or mhluser
	"""
	if (not 'ivr2_state' in request.session):
		# beginning of the very first call
		request.session['ivr2_state'] = 'ProviderIVR_Main_New'
		logger.debug('%s: ProviderIVR_Main_New is initiated' % (request.session.session_key))
	elif (request.session['ivr2_state'] and (request.session['ivr2_state'] != 'ProviderIVR_Main_New') and
		(request.session['ivr2_state'] != 'ProviderIVR_TreeRoot_New')):
		# this shouldn't happen, but if it did, and we log and keep going
		if (not 'provider_id' in request.session):
			logger.debug('%s: ProviderIVR_Main_New is called with state already set to %s, prov.id is null' % (
				request.session.session_key, request.session['ivr2_state']))
		else:
			logger.debug('%s: ProviderIVR_Main_New is called with state already set to %s, prov.id %s' % (
				request.session.session_key, request.session['ivr2_state'], request.session['provider_id']))
		request.session['ivr2_state'] = 'ProviderIVR_Main_New'

	logger.debug('%s: ProviderIVR_Main_New POST data is %s' % (request.session.session_key, str(request.POST)))
#	logger.debug('%s: ProviderIVR_Main_New META data is %s' % (request.session.session_key, str(request.META)))

	# check if this is the callback when call is completed (should redirect to ProviderIVR_Status)
	callEnded = _checkCallbackDuration(request)
	if callEnded:
		# we are done
		return callEnded

	# main functionality of this call
	(caller, called) = _setup_Main_callers(request)
	# set up provider_id in session
	provider_called = _getUniqueProvider(called)
	request.session['provider_id'] = provider_called.id

	# if caller has a doctorcom number, mask it
	caller_mhluser = _getMHLUser(caller)
	caller_provider = _maskProviderCaller(request, caller_mhluser)

	# set up callLog if none is defined:
	callSID = request.POST['CallSid']
	log = _getOrCreateCallLog(request, callSID, caller, called, 'OC', provider_called, caller_mhluser)
	if caller_provider:
		log.mdcom_caller = caller_provider
	log.save()

	logger.debug('%s: ProviderIVR_Main_New caller %s called %s callSid %s prov mobile %s' % (
		request.session.session_key, caller, called, callSID, provider_called.user.mobile_phone))

	if provider_called.user.mobile_phone != caller:
		request.session['ivr2_state'] = 'ProviderIVR_ForwardCall_New'
		logger.debug('%s: ProviderIVR_Main_New forwarding caller %s called %s called mobile %s' % (
			request.session.session_key, caller, called, provider_called.user.mobile_phone))
		return ProviderIVR_ForwardCall_New(request, provider_called)

	# otherwise, this is owner calling in
	log.call_source = 'VM'
	log.save()
	# check if VM config is all set up - if not, we go to ProviderIVR_Setup
	try:
		config = provider_called.vm_config.get()
	except MultipleObjectsReturned:
		raise Exception("Provider %s %s has multiple vm_config objects." % (
				provider_called.user.first_name, provider_called.user.last_name))
	except ObjectDoesNotExist:
		request.session['ivr2_state'] = 'ProviderIVR_Setup_New'
		return ProviderIVR_Setup_New(request)

	# Check to see if the PIN value exists in the configuration. Pin *should* be set through the web interface
	# or it won't be able to be set/changed as anonymous user
	if (not config.pin):
		logger.debug('%s: ProviderIVR_Main_New config pin not set - provider %s' % (
			request.session.session_key, provider_called.user.mobile_phone))
		request.session['ivr2_state'] = 'ProviderIVR_Setup_New'
		request.session.modified = True
		return ProviderIVR_Setup_New(request)

	request.session['config_id'] = config.id
	if (not 'authenticated' in request.session):
		logger.debug('%s: ProviderIVR_Main_New authenticating - provider %s' % (
			request.session.session_key, provider_called.user.mobile_phone))
		request.session['ivr2_state'] = 'ProviderIVR_Main_New'
		request.session.modified = True
		r = twilio.Response()
		return authenticateSessionNew(request, r)

	# Now, check to ensure that user voicemail configuration was completed successfully.
	if (not config.config_complete):
		logger.debug('%s: ProviderIVR_Main_New config incomplete - provider %s' % (
			request.session.session_key, provider_called.user.mobile_phone))
		request.session['ivr2_state'] = 'ProviderIVR_Setup_New'
		return ProviderIVR_Setup_New(request, provider_called)

	# everything else goes to main call tree
	request.session['ivr2_state'] = 'ProviderIVR_TreeRoot_New'
	return ProviderIVR_TreeRoot_New(request, provider_called)
