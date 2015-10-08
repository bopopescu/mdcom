
import re
import json
from twilio import twiml as twilio
from twilio.rest.resources import make_twilio_request

from django.conf import settings
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.http import HttpResponse

from models import VMBox_Config
from models import callLog, callEvent
from views_generic import authenticateSession, changePin, changeName
from views_generic import changeGreeting, getRecording
from views_generic import playMessages, getQuickRecording

from MHLogin.MHLUsers.models import Provider, MHLUser, OfficeStaff
from MHLogin.utils.decorators import TwilioAuthentication
from MHLogin.utils.mh_logging import get_standard_logger 
from MHLogin.utils.admin_utils import mail_admins
from MHLogin.utils.twilio_utils import client2008 as client

from MHLogin.DoctorCom.Messaging.models import MessageBodyUserStatus
from MHLogin.DoctorCom.IVR.utils import save_message
from MHLogin.DoctorCom.speech.utils import tts

# Setting up logging
logger = get_standard_logger('%s/DoctorCom/IVR/views_provider.log' % (settings.LOGGING_ROOT), 
							'DCom.IVR.views_provider', settings.LOGGING_LEVEL)

# 
# The request.session dictionary is heavily used through this codebase. Since
# this is a pretty opaque data structure, we should maintain a list of keys
# here. If you add keys to the dictionary, make sure to note it here.
# 
# General Variables
# --------------------------------------------
# authenticated - Whether or not the user is authenticated. If the key exists,
#	   then assume the user is authenticated, regardless of its value.
# Called - The phone number the caller is trying to reach.
# Caller - The callerID of the person who is calling in.
# ivr_call_stack - The call stack for this call. As functions close out, they
#	   should instruct Twilio to return to the last item in the stack. If no
#	   items remain, the call should be terminated. This is implemented as a
#	   list of strings. Each string must be a URLConf name so that reverse()
#	   may be run on it and an appropriate URL be returned to Twilio. The
#	   current convention is to use the function name for the URLConf name.
# ivr_setup_stage - A counter so that we know where in the setup process we are.
#	   This variable should only occur should control flow have passed through
#	   ProviderIVR_Setup.
# 
# Object IDs
# --------------------------------------------
# config_id - The ID of the VMBox_Config object ID for this voicemail box.
# provider_id - The ID of the provider whose voicemail box this is.
# 


@TwilioAuthentication()
def ProviderIVR_Setup(request, config=None):
	"""
	This function is heavily dependent upon request.session; Twilio is kind
	enough to keep session cookies for us.
	"""
	# DEBUG:
	#if (not 'ProviderIVR_Setup' in request.session['callCounts']):
	#   request.session['callCounts']['ProviderIVR_Setup'] = 1
	#else:
	#   request.session['callCounts']['ProviderIVR_Setup'] += 1

	# DEBUG:
	#if (not 'debug_semaphore' in request.session):
	#   request.session['ivr_setup_stage'] = 1
	#   request.session['debug_semaphore'] = True
	#else:
	#   raise Exception(request.session['ivr_call_stack'])
	if ('CallStatus' in request.POST and request.POST['CallStatus'] == 'completed'):
		# call ended
		#raise Exception('Ending inappropriately. Call stack is %s'%(str(
		# request.session['ivr_call_stack']),)) # DEBUG
		r = twilio.Response()
		return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)
	elif (not 'CallStatus' in request.POST):
		# call ended
		#raise Exception('Ending inappropriately. Call stack is %s'%(str(
		# request.session['ivr_call_stack']),)) # DEBUG
		r = twilio.Response()
		return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)

	if 'ivr_setup_stage' not in request.session:
		# Okay, this is the first time this function is being executed for this
		# call.
		#raise Exception(request.session['ivr_call_stack']) # DEBUG

		r = twilio.Response()

		# Set up our session variables.
		request.session['ivr_setup_stage'] = 1
		request.session['ivr_call_stack'].append('ProviderIVR_Setup')
		request.session.modified = True

		provider = Provider.objects.get(id=request.session['provider_id'])
		if (not provider.vm_config.count()):
			# This user needs a voicemailbox configuration object
			config = VMBox_Config()
			config.owner = provider
			config.save()
			request.session['config_id'] = config.id

		r.append(twilio.Pause())  # one second pause keeps the first words from getting cut off.
		r.append(tts("Welcome to your voicemail account. It looks like some "
			"setup is needed. Let's get started."))
		r.append(tts("First, we need to set up your pin number."))

		event = callEvent(callSID=request.POST['CallSid'], event='I_STR')
		event.save()

		#raise Exception(request.session['ivr_call_stack']) # DEBUG
		return changePin(request, r, True)

	elif (request.session['ivr_setup_stage'] == 1):  # Record name
		request.session['ivr_call_stack'].append('ProviderIVR_Setup')
		request.session.modified = True
		request.session['ivr_setup_stage'] = 2

		return changeName(request, 'Now, we need to record your name.')
	elif (request.session['ivr_setup_stage'] == 2):  # Record a greeting
		request.session['ivr_call_stack'].append('ProviderIVR_Setup')
		request.session.modified = True
		request.session['ivr_setup_stage'] = 3

		return changeGreeting(request, 'Finally, we need to set up a greeting.')
	elif (request.session['ivr_setup_stage'] == 3):  # Configuration complete!
		#raise Exception(request.session['ivr_call_stack']) # DEBUG
		#raise Exception(request.session['callCounts']) # DEBUG
		# Automatically "log" this user in.
		request.session['authenticated'] = True

		config = VMBox_Config.objects.get(id=request.session['config_id'])
		config.config_complete = True
		config.save()

		r = twilio.Response()
		r.append(tts('Your voice mail account is now set up. You may hang up '
					'now, or stay on the line to be taken to your voice mail box home.'))

		event = callEvent(callSID=request.POST['CallSid'], event='I_FIN')
		event.save()

		r.append(twilio.Redirect(reverse(request.session['ivr_call_stack'].pop())))
		request.session.modified = True
		return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)

	raise Exception('Reached the end of ProviderIVR_Setup. This should never happen.')


@TwilioAuthentication()
def ProviderIVR_Options(request, internalCall=False):
	r = twilio.Response()

	if (not internalCall and request.method == 'POST' and 'Digits' in request.POST):
		digits = request.POST['Digits']
		p = re.compile('[0-9#*]$')
		if (not p.match(digits)):
			r.append(tts('I\'m sorry, I didn\'t understand that.'))
		elif (digits == '1'):
			# Change name
			request.session['ivr_call_stack'].append('ProviderIVR_Options')
			request.session.modified = True
			event = callEvent(callSID=request.POST['CallSid'], event='F_NCH')
			return changeName(request)
		elif (digits == '3'):
			# Change greeting
			request.session['ivr_call_stack'].append('ProviderIVR_Options')
			request.session.modified = True
			event = callEvent(callSID=request.POST['CallSid'], event='F_GCH')
			return changeGreeting(request)
		elif (digits == '5'):
			# Change pin
			request.session['ivr_call_stack'].append('ProviderIVR_Options')
			request.session.modified = True
			event = callEvent(callSID=request.POST['CallSid'], event='F_PCH')
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
			r.append(tts('I\'m sorry, that wasn\t a valid selection.'))

	gather = twilio.Gather(finishOnKey='', numDigits=1, action=reverse('ProviderIVR_Options'))

	gather.append(tts('Options menu'))
	gather.append(tts('To re-record your name, press 1'))
	gather.append(tts('To record a new greeting, press 3'))
	gather.append(tts('To change your pin, press 5'))
	gather.append(tts('To return to the main menu, press 9'))
	gather.append(tts('To repeat this menu, press star'))

	r.append(gather)
	return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)


@TwilioAuthentication()
def ProviderIVR_TreeRoot(request):

	r = twilio.Response()
	provider = Provider.objects.get(id=request.session['provider_id'])

	if (request.method == 'POST' and 'Digits' in request.POST):
		digits = request.POST['Digits']
		p = re.compile('[0-9#*]$')
		if (not p.match(digits)):
			r.append(tts('I\'m sorry, I didn\'t understand that.'))
		elif (digits == '1'):
			# play messages
			request.session['ivr_call_stack'].append('ProviderIVR_TreeRoot')
			request.session.modified = True
			messages = MessageBodyUserStatus.objects.filter(user=provider.user, 
				delete_flag=False, msg_body__message___resolved_by=None, 
					msg_body__message__message_type__in=('ANS', 'VM'))
			return playMessages(request, messages, r)
		elif (digits == '2'):
			request.session['ivr_call_stack'].append('ProviderIVR_TreeRoot')
			request.session.modified = True
			messages = MessageBodyUserStatus.objects.filter(user=provider.user, 
				delete_flag=False, msg_body__message___resolved_by=None, 
					msg_body__message__message_type__in=('ANS',))
			return playMessages(request, messages, r)
		elif (digits == '3'):
			request.session['ivr_call_stack'].append('ProviderIVR_TreeRoot')
			request.session.modified = True
			messages = MessageBodyUserStatus.objects.filter(user=provider.user, 
				delete_flag=False, msg_body__message___resolved_by=None, 
					msg_body__message__message_type__in=('VM',))
			# fix for issue 2257 - if we go to playMessages, it will use 3 in its digit and try to replay
			# current message which fails if there are no messages
			if (messages == [] or len(messages) == 0):
				pass
			else:
				request.session['ivr_call_stack'].append('ProviderIVR_TreeRoot')
				return playMessages(request, messages, r)

		elif (digits == '4'):
			request.session['ivr_call_stack'].append('ProviderIVR_TreeRoot')
			request.session.modified = True
			return ProviderIVR_Options(request, True)
		elif (digits == '*'):
			pass
		else:
			r.append(tts('I\'m sorry, I didn\'t understand that.'))

	gather = twilio.Gather(finishOnKey='', numDigits=1)
#	messages = MessageBodyUserStatus
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

	say_str = []

	say_str.append('You have %i new, and %i saved urgent messages,' % (
			unread_anssvc_msg_count, saved_anssvc_msg_count))
	say_str.append(' ')
	say_str.append('and %i new, and %i saved voice messages,' % (unread_msg_count, saved_msg_count))

	if (any((unread_msg_count, unread_anssvc_msg_count, saved_msg_count, saved_anssvc_msg_count))):
		say_str.append('To listen to all your messages, press one. ')
		say_str.append('To listen to your urgent messages, press two. ')
		say_str.append('To listen to your voice mail, press three. ')
	gather.append(tts(''.join(say_str)))

	gather.append(tts('To manage your voicemail settings, press four.'))
	gather.append(tts('To repeat this menu, press star.'))
	r.append(gather)

	return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)

#	options = [
#		[1, reverse()],
#		[3, reverse()],
#		[7, reverse()],
#		[9, reverse()],
#	]
#	return UnaffiliatedNumber(request)


@TwilioAuthentication()
def ProviderIVR_LeaveMsg(request):
	"""
	Records a voicemail message.

	Arguments:
		request - The standard Django request argument

	request.session Keys:
		provider_id - The ID of the Provider user who owns this voicemail box.
	"""
	# TODO: Update this code so that users can hit the pound key to 
	# pop back and log into their own voicemail box.
	provider = Provider.objects.get(id=request.session['provider_id'])

	config = None
	config_complete = provider.vm_config.count() == 1 and provider.vm_config.get().config_complete
	if (config_complete):
		config = provider.vm_config.get()

	if('CallStatus' in request.POST and request.POST['CallStatus'] == 'completed'):
		try:
			callSID = request.POST['CallSid']
			auth, uri, = client.auth, client.account_uri
			resp = make_twilio_request('GET', uri + '/Calls/%s' % callSID, auth=auth)
			content = json.loads(resp.content)
			log = callLog.objects.get(callSID=callSID)
			log.call_duration = content['TwilioResponse']['Call']['Duration']
			log.save()
		except:
			pass  # this is really ugly, but letting this exception fall through
				# destroys a message analytics will pick up the duration later on if it's missing

	if ('ivr_makeRecording_recording' in request.session):
		provider_qs = Provider.objects.filter(mobile_phone=request.session['Caller'])
		if(provider_qs):
			request.session['ivr_makeRecording_callbacknumber'] = provider_qs[0].mdcom_phone
			subject = "Voice Mail from %s %s" % (provider_qs[0].first_name, provider_qs[0].last_name)
		else:
			request.session['ivr_makeRecording_callbacknumber'] = request.session['Caller']
			subject = "Voice Mail from %s" % request.session['ivr_makeRecording_callbacknumber']
		save_message(request, subject, [provider.user], None, "VM", False)
		request.session.pop('ivr_makeRecording_recording')

		r = twilio.Response()
		r.append(tts('Good bye'))
		r.append(twilio.Hangup())
		return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)

	# Get the configuration file for this Provider
	if (not config_complete):
		# FIXME:
		# Probably not the best way to create the spoken number. We need to
		# break the number down so that there are spaces between each digit, and
		# so that there are commas after the third and sixth digits.
		if (not 'Called' in request.session or (not request.session['Called'])):
			# This will occur if click2call calls this function
			request.session['ivr_makeRecording_prompt'] = tts('The user is not available. '
					'Please leave a message after the beep. Press pound when finished for options.')
		else:
			number = request.session['Called']
			spoken_number = []
			[spoken_number.extend([i, ' ']) for i in number]
			spoken_number.pop()  # drop the last element
			spoken_number.insert(5, ',')
			spoken_number.insert(12, ',')
			request.session['ivr_makeRecording_prompt'] = tts('The person at %s '
				'is not available. Please leave a message after the beep. Press pound '
				'when finished for options.' % (''.join(spoken_number),))
	else:
		p = re.compile('http')
		if (p.match(config.greeting)):
			# This is a Twilio recording.
			request.session['ivr_makeRecording_prompt'] = twilio.Play(config.greeting)
		else:
			# TODO: 
			raise Exception('Unimplemented playback of local files')

	request.session['ivr_makeRecording_maxLength'] = 120  # 2 minutes
	request.session['ivr_makeRecording_leadSilence'] = 2
	request.session['ivr_makeRecording_promptOnce'] = True
	request.session['ivr_makeRecording_returnOnHangup'] = \
		'MHLogin.DoctorCom.IVR.views_provider.ProviderIVR_LeaveMsg'
	request.session['ivr_call_stack'].append('ProviderIVR_LeaveMsg')
	request.session.modified = True

	# Pass off the recording action to the getRecording function.
	return getRecording(request)


@TwilioAuthentication()
def ProviderIVR_ForwardCall(request):
	"""Forward the call to the dialed user, as per the user's preferences.

	Uses the following session variables:
		ProviderIVR_ForwardCall_state: The most recent "state" of execution. May
			have the following values:
				- None/Undefined/Empty String: First execution of this function.
				- Getting_Name: Getting the caller's name, if one hasn't been
						defined.
				- Dialing: Phone(s) have been dialed, and waiting for a response Caller
	"""
	r = twilio.Response()
	request.session.modified = True
	provider = Provider.objects.get(id=request.session['provider_id'])

	if('CallStatus' in request.POST and request.POST['CallStatus'] == 'completed'):
		if('Duration' in request.POST):
			callSID = request.POST['CallSid']
			log = callLog.objects.get(callSID=callSID)
			log.call_duration = request.POST['Duration']
			log.save()

	if(not 'ProviderIVR_ForwardCall_forward' in request.session):
		request.session['ProviderIVR_ForwardCall_forward'] = provider.forward_voicemail
	forward = provider.forward_voicemail
	if (forward == 'VM'):
		return ProviderIVR_LeaveMsg(request)

	if (not 'ProviderIVR_ForwardCall_state' in request.session or
			not request.session['ProviderIVR_ForwardCall_state']):
		# New call. First, check to see if we should go straight to voicemail

		# Okay, the call isn't going to voicemail directly. Now, set state.
		request.session['ProviderIVR_ForwardCall_state'] = 'Getting_Name'

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
							request.session['ProviderIVR_ForwardCall_state'],
						))
					log.caller_spoken_name = prov_vmconfig.name
					log.save()
					return ProviderIVR_ForwardCall(request)  # restart execution of this function
				else:
					logger.debug('%s/%s: Caller\'s vm_config incomplete!' % (
							request.session.session_key,
							request.session['ProviderIVR_ForwardCall_state'],
						))
			else:
				logger.debug('%s/%s: An unsuitable number of vm_config objects found: %i' % 
					(request.session.session_key,
						request.session['ProviderIVR_ForwardCall_state'],
						log.mdcom_caller.vm_config.count(),
					))
		else:
			logger.debug('%s/%s: mdcom_caller %s either isn\'t defined or doesn\'t '
						'seem to be a Provider' % (request.session.session_key,
					request.session['ProviderIVR_ForwardCall_state'],
					str(log.mdcom_caller),
				))

		# Okay, it's not a user with a name recording. Get one.
		request.session['ivr_call_stack'].append('ProviderIVR_ForwardCall')
		request.session['ivr_makeRecording_prompt'] = \
			tts('Please say your name after the tone.')
		request.session['ivr_makeRecording_maxLength'] = 4
		request.session['ivr_makeRecording_timeout'] = 2
		request.session['ivr_makeRecording_leadSilence'] = 1
		return getQuickRecording(request)

	if (request.session['ProviderIVR_ForwardCall_state'] == 'Getting_Name'):
		request.session['ProviderIVR_ForwardCall_state'] = 'Dialed'

		logger.debug('%s/%s: Set session to %s' % (
				request.session.session_key,
				request.session['ProviderIVR_ForwardCall_state'],
				request.session['ProviderIVR_ForwardCall_state'],
			))

		callSID = request.POST['CallSid']
		log = callLog.objects.get(callSID=callSID)
		if (not log.caller_spoken_name):
			log.caller_spoken_name = request.session.pop('ivr_makeRecording_recording')
			log.save()

		logger.debug('%s/%s: got provider \'%s\' \'%s\' with id %s' % (
				request.session.session_key,
				request.session['ProviderIVR_ForwardCall_state'],
				provider.first_name,
				provider.last_name,
				provider.pk,
			))
		logger.debug('%s/%s: Provider phone is \'%s\' and forward_other is \'%s\'' % (
				request.session.session_key,
				request.session['ProviderIVR_ForwardCall_state'],
				provider.user.phone,
				str(provider.forward_other),
			))

		# Okay, let's dial!
		user_number = None
		if (forward == 'MO'):
			logger.debug('%s/%s: provider.forward_mobile True' % (
					request.session.session_key,
					request.session['ProviderIVR_ForwardCall_state'],
				))
			user_number = provider.user.mobile_phone
			logger.debug('%s/%s: Setting user_number to \'%s\'' % (
					request.session.session_key,
					request.session['ProviderIVR_ForwardCall_state'],
					provider.user.mobile_phone,
				))
		elif (forward == 'OF'):
			logger.debug('%s/%s: provider.forward_office True' % (
					request.session.session_key,
					request.session['ProviderIVR_ForwardCall_state'],
				))
			user_number = provider.office_phone
			logger.debug('%s/%s: Setting user_number to \'%s\'' % (
					request.session.session_key,
					request.session['ProviderIVR_ForwardCall_state'],
					provider.office_phone,
				))
		elif (forward == 'OT'):
			logger.debug('%s/%s: provider.forward_other True' % (
					request.session.session_key,
					request.session['ProviderIVR_ForwardCall_state'],
				))
			user_number = provider.user.phone
			logger.debug('%s/%s: Setting user_number to \'%s\'' % (
					request.session.session_key,
					request.session['ProviderIVR_ForwardCall_state'],
					provider.user.phone,
				))

		logger.debug('%s/%s: Tried to get called\'s number. Got \'%s\'' % (
				request.session.session_key,
				request.session['ProviderIVR_ForwardCall_state'],
				user_number,
			))
		logger.debug('%s/%s: Provider phone is \'%s\' and forward_other is \'%s\'' % (
				request.session.session_key,
				request.session['ProviderIVR_ForwardCall_state'],
				provider.user.phone,
				str(provider.forward_other),
			))

		if (not user_number):
			# no flags were set.
			if (provider.user.mobile_phone):
				user_number = provider.user.mobile_phone
			else:
				return ProviderIVR_LeaveMsg(request)

		dial = twilio.Dial(
				action=reverse('ProviderIVR_ForwardCall'),
				timeout=22,
				timeLimit=14400,  # 4 hours
				callerId=request.session['Caller']
			)
		dial.append(twilio.Number(user_number,
				url=reverse('ProviderIVR_ForwardCall_VetAnswer')
			))
		r.append(dial)
		r.append(twilio.Redirect(reverse('ProviderIVR_LeaveMsg')))
		return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)

	if (request.session['ProviderIVR_ForwardCall_state'] == 'Dialed'):
		callSID = request.POST['CallSid']
		log = callLog.objects.get(callSID=callSID)

		if (log.call_connected):
			r.append(twilio.Hangup())
			return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)

		return ProviderIVR_LeaveMsg(request)

	r = twilio.Response()
	if (request.POST['DialStatus'] != 'answered'):
		if (request.POST['DialStatus'] == 'failed'):
			# TODO: Figure out how to deal with connection problems. Most
			# likely, send an email to the user and administrators.
			subject = 'ProviderIVR_ForwardCall Call Forward DialStatus Fail'
			message = 'ProviderIVR_ForwardCall got DialStatus failed. Post data: %s' % \
				(str(request.POST),)
			mail_admins(subject=subject, message=message, fail_silently=False)
		# else request.POST['DialStatus'] == 'busy' or request.POST['DialStatus'] == 'no-answer'
		return ProviderIVR_LeaveMsg(request)
	# else: Do nothing so that the call continues un-interrupted
	return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)


@TwilioAuthentication()
def ProviderIVR_ForwardCall_VetAnswer(request):
	"""
	This function is executed on Number nouns within Dial verbs. The idea is to
	try to determine if it's a human who picked up, or a machine. Alternatively,
	this gives the called party a chance to send the call to voicemail without
	the caller knowing they're rejecting the call.
	"""
	r = twilio.Response()
	request.session.modified = True

	callSID = request.POST['CallSid']
	log = callLog.objects.get(callSID=callSID)

	if (request.method == 'POST' and 'Digits' in request.POST):
		# Connect the calls
		log.call_connected = True
		log.save()

		event = callEvent(callSID=callSID, event='C_ACC')
		event.save()

		return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)

	caller_spoken_name = log.caller_spoken_name
	if (log.mdcom_caller):
		# Great. Is it a Provider?
		if (isinstance(log.mdcom_caller, Provider) and log.mdcom_caller.vm_config.count()):
			vm_config = log.mdcom_caller.vm_config.get()
			if (vm_config.config_complete):
				caller_spoken_name = vm_config.name
	gather = twilio.Gather(numDigits=1, finishOnKey='', action=reverse(
					'ProviderIVR_ForwardCall_VetAnswer'))
	gather.append(tts("You have a call from"))
	gather.append(twilio.Play(caller_spoken_name))
	gather.append(tts("Press any key to accept."))
	r.append(gather)
	r.append(twilio.Hangup())

	return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)


@TwilioAuthentication()
def ProviderIVR_OutsideInit(request, caller, called_provider, c2c_log=None):
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
	request.session['Called'] = called_provider.mdcom_phone
	request.session['provider_id'] = called_provider.id

	# Now, deal with the caller values. Does the caller have a DoctorCom number?
	mhlusers_mobile_phone = MHLUser.objects.filter(mobile_phone=caller)
	mhlusers_phone = MHLUser.objects.filter(phone=caller)
	total_users = mhlusers_mobile_phone.count() + mhlusers_phone.count()
	caller_provider = None
	caller_manager = None
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
						caller_provider.mdcom_phone,))
				request.session['Caller'] = caller_provider.mdcom_phone
			else:
				logger.debug('%s: called_provider.mdcom_phone is False' % (
						request.session.session_key,))
		else:
			logger.debug('%s: called_provider_qs.count() is False' % (
					request.session.session_key,))
			#let's check if caller is office manager with phone
			caller_manager_qs = OfficeStaff.objects.filter(user=user)
			if (caller_manager_qs.count()):
				caller_manager = caller_manager_qs.get()			
			else:
				logger.debug('%s: called_manager_qs.count() is False' % (
					request.session.session_key,))
	else:
		logger.debug('%s: total_users is %i' % (
				request.session.session_key,
				total_users))
	# Else, mask the caller's phone number with the DoctorCom number.
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
				called_number=called_provider.mdcom_phone,
				mdcom_called=called_provider,
				callSID=request.POST['CallSid'],
				c2c_entry_id=c2c_log.pk,
				call_source='CC',
			)
		if (c2c_log):
			log.c2c_entry_id = c2c_log.pk
		logger.debug('%s: caller_provider is \'%s\'' % (
					request.session.session_key,
					str(caller_provider),
				))
		if (caller_provider):
			log.mdcom_caller = caller_provider
			logger.debug('%s: called_provider is \'%s\'' % (
					request.session.session_key,
					str(called_provider),
				))
		elif (caller_manager):
			log.mdcom_caller = caller_manager
			logger.debug('%s: caller_manager is \'%s\'' % (
					request.session.session_key,
					str(caller_manager),
				))
		if (called_provider):
				log.mdcom_called = called_provider

	log.save()


@TwilioAuthentication()
def ProviderIVR_Init(request):
	request.session['answering_service'] = 'no'

	# First, make sure that the call stack is initialized:
	if (not 'ivr_call_stack' in request.session):
		request.session['ivr_call_stack'] = []

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
		caller = request.POST['Caller']
		called = request.POST['Called']
		p = re.compile('\d+$')
		if (not p.match(caller)):
			if (caller != '' and caller != None):
				subject = 'ProviderIVR_Main Incoming CallerID Sanitation Fail'
				message = 'ProviderIVR_Main incoming CallerID failed on input %s.' % (caller,)
				mail_admins(subject=subject, message=message, fail_silently=False)
			caller = ''
		if (not p.match(called)):
			# The number being called doesn't seem to be valid. Since we can't find
			# out which provider is being called, just raise an Exception and let
			# Django and Twilio deal with it.
			raise Exception('Invalid called value: %s' % (called,))

		request.session['Caller'] = caller
		request.session['Called'] = called

	# Now, get the Provider being called
	provider = Provider.objects.filter(mdcom_phone=called)
	if provider.count() != 1:
		# If we don't allow multiple providers having same mdcom_phone it should
		# be unique in model, this code just logs more information than previously.
		if provider.count() > 1:
			msg = 'Multiple providers have mdcom_phone: %s, providers: %s' % \
					(called, ', '.join("%s" % p for p in provider))
			logger.error(msg)
			raise Exception(msg)
		else:
			msg = 'No providers have mdcom_phone %s' % (called,)
			logger.error(msg)
			raise Exception(msg)

	provider = provider[0]
	request.session['provider_id'] = provider.id

	# TODO: Flesh out the logging here so that we pull appropriate objects.
	log_qs = callLog.objects.filter(callSID=request.POST['CallSid'])
	if (log_qs.count()):
		# FIXME: This condition shouldn't be hit! This init function is getting
		# run multiple times per call, and I don't know why. --BK
		log = log_qs.get()
	else:
		log = callLog(
				caller_number=request.session['Caller'],
				called_number=request.session['Called'],
				mdcom_called=provider,
				callSID=request.POST['CallSid'],
				call_source='OC',
			)

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

		caller_provider = Provider.objects.filter(user=user)
		if caller_provider.exists():
			log.mdcom_caller = caller_provider[0]
			if log.mdcom_caller.mdcom_phone:
				# Mask the caller's caller ID since they have a doctorcom number
				request.session['Caller'] = log.mdcom_caller.mdcom_phone
		else:
			log.mdcom_caller = user

	log.save()

	return provider, log


@TwilioAuthentication()
def ProviderIVR_Main(request):
	"""
	DEPRECATED - to be replaced by ProviderIVR_Main_New in views_provider_v2.py
	"""
	# TODO: This function needs to be broken down into sub-functions for both
	# maintenance, and so that we can sanely implement allowing users to check
	# their voicemail from foreign phones.

	# DEBUG:
	#if (not 'callCounts' in request.session):
	#	request.session['callCounts'] = dict()
	#if (not 'ProviderIVR_Main' in request.session['callCounts']):
	#	request.session['callCounts']['ProviderIVR_Main'] = 1
	#else:
	#	request.session['callCounts']['ProviderIVR_Main'] += 1
	logger.info('%s: ProviderIVR_Main POST data is %s' % (request.session.session_key, str(request.POST)))
	if ('CallStatus' in request.POST and request.POST['CallStatus'] == 'completed'):
		# call ended
		#raise Exception('Ending inappropriately. Call 
		# stack is %s'%(str(request.session['ivr_call_stack']),))
		# Update the log entry with the duration of the call
		try:
			log = callLog.objects.get(callSID=request.POST['CallSid'])
			log.call_duration = None
			if ('Duration' in request.POST):
				log.call_duration = int(request.POST['Duration'])
		except ObjectDoesNotExist as odne:  # voicemail won't have a call
			logger.warning('Call log does not exist for sid: %s. Caller may have '
				'hung up shortly after Twilio starts call process.' % str(odne))

		r = twilio.Response()
		return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)
	elif (not 'CallStatus' in request.POST):
		# call ended
		#raise Exception('Ending inappropriately. Call 
		# stack is %s'%(str(request.session['ivr_call_stack']),))
		r = twilio.Response()
		return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)

	# ready to initialize this call, request.session[provider_id] in request stack
	provider, log = ProviderIVR_Init(request)

	# Check to see if the caller doesn't own this mailbox.
	# TODO: This is where we check to see which number of the user's we compare
	# against to assume that the user is calling in. (got it?)
	if (provider.user.mobile_phone != request.REQUEST['Caller']):
		return ProviderIVR_ForwardCall(request)

	log.call_source = 'VM'
	log.save()
	# Great, now we know that this is the owner calling in. First up, check to
	# see if the user has a configuration file and that they've completed setup.
	try:
		config = provider.vm_config.get()
	except MultipleObjectsReturned:
		raise Exception("Provider %s %s has multiple vm_config objects." % (
				provider.user.first_name, provider.user.last_name))
	except ObjectDoesNotExist:
		request.session['ivr_call_stack'].append('ProviderIVR_Main')
		request.session.modified = True
		return ProviderIVR_Setup(request)
	else:
		request.session['config_id'] = config.id

	# Check to see if the PIN value exists in the configuration. If it doesn't,
	# then run the user through configuration.
	if (not config.pin):
		request.session['ivr_call_stack'].append('ProviderIVR_Main')
		request.session.modified = True
		return ProviderIVR_Setup(request)

	if (not 'authenticated' in request.session):
		request.session['ivr_call_stack'].append('ProviderIVR_Main')
		request.session.modified = True

		r = twilio.Response()
		#r.append(tts('Welcome to your voice mail box.')) # campy and wastes time.
		return authenticateSession(request, r)

	# Now, check to ensure that user voicemail configuration was completed successfully.
	if (not config.config_complete):
		request.session['ivr_call_stack'].append('ProviderIVR_Main')
		request.session.modified = True
		return ProviderIVR_Setup(request)

	return ProviderIVR_TreeRoot(request)

