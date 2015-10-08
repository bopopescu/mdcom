
import collections
import time
import urllib2
import json
import sys
import xml.etree.ElementTree as ET

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist  # , KeyError
from django.core.mail import EmailMessage
from django.http import HttpResponse
from django.utils.translation import ugettext_lazy as _

from twilio import TwilioRestException
from twilio.rest.resources import make_twilio_request

from MHLogin.KMS.shortcuts import encrypt_object
from MHLogin.MHLUsers.utils import get_all_practice_managers
from MHLogin.DoctorCom.IVR.models import callLog, IVR_Prompt, NON_URGENT_PROMPT, \
	NO_SPECIALTY_PROMPT, SGS_PROMPT, MGS_PROMPT, SPECIALTIES_PROMPT, \
	default_prompt_verbage, AnsSvcDLFailure, AnsSvcDLFailureActivityLog, \
	VMBox_Config, callEvent, callEventTarget
from MHLogin.DoctorCom.Messaging.models import Message, MessageRecipient, \
	MessageCC, MessageAttachment
from MHLogin.MHLCallGroups.models import Specialty
from MHLogin.utils.mh_logging import get_standard_logger
from MHLogin.MHLPractices.utils import message_super_managers
from MHLogin.utils.admin_utils import mail_admins
from MHLogin.utils.twilio_utils import client, client2008

# Setting up logging
USE_MP3 = True
logger = get_standard_logger('%s/DoctorCom/IVR/utils.log' % (settings.LOGGING_ROOT),
							'DCom.IVR.utils', settings.LOGGING_LEVEL)


def save_answering_service_message(request, urgent, recipients, cc=None):
	cc = cc or []
	callback_number = request.session['ivr_makeRecording_callbacknumber']
	if(urgent):
		subject = _('Ans. Svc. - Urgent message from %s') % callback_number
	else:
		subject = _('Ans. Svc. - NON Urgent message from %s') % callback_number
	save_message(request, subject, recipients, cc, 'ANS', urgent)


def save_message(request, subject, recipients, cc=None, message_type='VM', urgent=False):
	#now that we live about 1.5ms away from twilio instead of 100ms,
	#we sometimes end up requesting recordings before twilio has put them up.
	#so we sleep for 100ms as a workaround
	time.sleep(.1)
	cc = cc or []
	msg = Message(sender=None, sender_site=None, subject=subject)
	msg.urgent = urgent
	msg.message_type = message_type
	msg.callback_number = request.session['ivr_makeRecording_callbacknumber']
	msg.save()
	attachments = []
	all_recipients = recipients[:]

	for recipient in all_recipients:
		MessageRecipient(message=msg, user=recipient).save()
	if isinstance(cc, collections.Iterable):
		for recipient in cc:
			MessageCC(message=msg, user=recipient).save()
	if ('ivr_makeRecording_recording' in request.session):
		#make a file out of twilio recording
		attachment = save_voice_attachment(request, msg)
		if (attachment):
			attachments.append(attachment)

	#'For ANS ONLY! ivr_caller_id_area_code' present means the call back number contained no area code,
	#and we saved twillio's caller id are code
	if (message_type == 'ANS' and 'ivr_caller_id_area_code' in request.session):
		caller_id_area_code = " Area Code From Caller Id :%s." % \
			request.session['ivr_caller_id_area_code']
	else:
		caller_id_area_code = ""

	if ('ivr_only_callbacknumber' in request.session and request.session['ivr_only_callbacknumber']):
		if ('ivr_no_pound' in request.session and request.session['ivr_no_pound'] == True):
			formatted_body = _("Caller hung up from CONFIRMED %s before leaving message. "
				"No attachment.") % request.session['ivr_makeRecording_callbacknumber']
			msg.vmstatus = 'C'
		else:
			formatted_body = _("Caller hung up from unconfirmed %s before leaving message. "
				"No attachment.") % request.session['ivr_makeRecording_callbacknumber']
			msg.vmstatus = 'U'
	else:
		msg.vmstatus = 'R'
		if (attachments):
			formatted_body = "Message from %s.%s" % (
				request.session['ivr_makeRecording_callbacknumber'], caller_id_area_code)
		else:
			# There was a recording, but Twilio must have errored when we
			# tried to get it.
			formatted_body = _("Message from %(callbacknumber)s. Unfortunately, an error occurred "
							"downloading the recording from our telephone company. We will "
							"automatically retry the download and you will receive a new "
							"message once the recording is successfully retrieved. This call "
							"will be referenced using the following ID: %(CallSid)s.\nWe "
							"apologize for any inconvenience.\nDoctorCom Staff") % \
							{'callbacknumber': request.session['ivr_makeRecording_callbacknumber'],
								'CallSid': request.REQUEST['CallSid']}

			url = request.session['ivr_makeRecording_recording']
			log = AnsSvcDLFailure(
						practice_id=request.session.get('practice_id', 0),
						error_message_uuid=msg.uuid,
						recording_url=url,
						callback_number=request.session['ivr_makeRecording_callbacknumber'],
						failure_type='DL',
				)
			log.init_from_post_data(request.REQUEST)
			log.save()
	msg_body = msg.save_body(formatted_body)

	event = callEvent(callSID=request.POST['CallSid'], event='V_NMG')
	target = callEventTarget(event=event, target=msg)
	# Send the message
	msg.send(request, msg_body, attachments)


def save_voice_attachment(request, msg):
	wav_data, metadata = _download_recording(request)
	metadata = json.dumps(metadata)
	if(not wav_data):
		admin_email_body = ''.join([
				('Answering service recording download failed on call SID '),
				request.REQUEST['CallSid'], ('. Since the automatic '),
				('downloader hasn\'t been implemented yet, please go and'),
				('manually deal with the message.\n\n'), settings.SERVER_ADDRESS])
		admin_email_subject = _('Answering Service Message Download Failed')
		mail_admins(admin_email_subject, admin_email_body)
		return None
	attachment = encrypt_object(
		MessageAttachment,
		{
			'message': msg,
			'size': len(wav_data),
			'encrypted': True,
			'metadata': metadata
		})
	attachment.encrypt_url(request, ''.join(['file://', attachment.uuid]))
	attachment.encrypt_filename(request, ''.join(['call_from_',
				request.session['ivr_makeRecording_callbacknumber'], '.mp3']))
	try:
		attachment.encrypt_file(request, [wav_data])
	except Exception as e:
		log = AnsSvcDLFailure(
			practice_id=request.session.get('practice_id', 0),
			error_message_uuid=msg.uuid,
			recording_url=request.session['ivr_makeRecording_recording'],
			callback_number=request.session['ivr_makeRecording_callbacknumber'],
			failure_type='UL',
		)
		log.init_from_post_data(request.REQUEST)
		log.save()
		admin_email_body = ''.join([
				('Answering service recording upload failed on call SID '),
				request.REQUEST['CallSid'], ('. Since the automatic '),
				('downloader hasn\'t been implemented yet, please go and'),
				('manually deal with the message.\n\n'), settings.SERVER_ADDRESS,
				('\n\nException: '), repr(e)])
		admin_email_subject = _('Answering Service Message Upload Failed')
		mail_admins(admin_email_subject, admin_email_body)
		return None

	if(not USE_MP3):
		attachment.suffix = 'wav'
		attachment.content_type = 'audio/wav'
	else:
		attachment.suffix = 'mp3'
		attachment.content_type = 'audio/mp3'

	attachment.save()
	return attachment


def resolve_download_failure(failure_record):
	url = failure_record.recording_url
	request = _FauxRequest()
	request.REQUEST = {"CallSid": failure_record.call_sid}
	request.session['ivr_makeRecording_recording'] = url
	request.session.session_key = ''

	wav_data, metadata = _download_recording(request)
	metadata = json.dumps(metadata)
	if (not wav_data):
		log = AnsSvcDLFailureActivityLog(
				call_sid=failure_record.call_sid, action='FAI')
		log.save()
		return False

	log = AnsSvcDLFailureActivityLog(call_sid=failure_record.call_sid, action='SUC')
	log.save()

	managers = get_all_practice_managers(failure_record.practice_id)

	msg = Message(sender=None, sender_site=None, subject='Answering Service - Recording Retrieved')
	msg.save()

	if(managers):
		# Assign all practice managers as recipients of this message.
		for staffer in managers:
			MessageRecipient(message=msg, user=staffer.user).save()
	else:
		#if this was a voicemail on a provider number
		error_msg = Message.objects.get(uuid=failure_record.error_message_uuid)
		recipients = error_msg.recipients.all()
		for user in recipients:
			MessageRecipient(message=msg, user=user).save()

	body = _('We were able to successfully retrieve a recording we had trouble '
		'downloading earlier today (callback number %(callbacknumber)s with '
		'ID %(call_sid)s). Please see the attached recording.\nAgain, we apologize '
		'for any inconvenience and thank you for your patience.\nDoctorCom Staff') % \
		{'callbacknumber': failure_record.callback_number, 'call_sid': failure_record.call_sid}

	body = msg.save_body(body)

	attachment = encrypt_object(
		MessageAttachment,
		{
			'message': msg,
			'size': len(wav_data),
			'encrypted': True,
			'metadata': metadata
		})
	attachment.encrypt_url(None, ''.join(['file://', attachment.uuid]))
	attachment.encrypt_filename(None, ''.join(['call_from_',
							failure_record.callback_number, '.mp3']))
	attachment.encrypt_file(None, [wav_data])
	if(not USE_MP3):
		attachment.suffix = 'wav'
		attachment.content_type = 'audio/wav'
	else:
		attachment.suffix = 'mp3'
		attachment.content_type = 'audio/mp3'

	attachment.save()
	attachments = [attachment]

	request.session['answering_service'] = 'yes'
	# Send the message
	msg.send(request, body, attachments)

	failure_record.mark_resolved(msg)
	return True


class _FauxRequest(object):
	class Session(dict):
		session_key = ''
	session = Session()


def _download_recording(request):
	try_count = 0
	response = None
#	wav_data = None
	url = request.session['ivr_makeRecording_recording']
	xmlurl = ''.join([url, '.xml'])
	if USE_MP3:
		url += '.mp3'

	while (not response and try_count < 3):
		try:
			response = urllib2.urlopen(xmlurl, timeout=10)
		except (urllib2.HTTPError, urllib2.URLError) as e:
			log = AnsSvcDLFailureActivityLog(
				call_sid=request.REQUEST['CallSid'], action='DLF')
			log.set_error_data(e)
			log.save()
			time.sleep(1)
			response = None
	if not response:
		return (None, None)

	try:
		root = ET.parse(response)
		duration = int(root.findall('./Recording/Duration')[0].text)
	except Exception as e:
		logger.critical('BUG parsing xml recording response: %s' % str(e))
		duration = None
	metadata = {'duration': duration}
	try_count = 0
	response = None
	while (not response and try_count < 3):
		try:
			# Setting the timeout manually, rather than relying on the global default.
			response = urllib2.urlopen(url, timeout=10)
		except (urllib2.HTTPError, urllib2.URLError) as e:
			log = AnsSvcDLFailureActivityLog(
				call_sid=request.REQUEST['CallSid'], action='DLF')
			log.set_error_data(e)
			log.save()

			try_count += 1
			time.sleep(1)
			response = None

	if (response):
		return (response.read(), metadata)
	return (None, None)


class _IVR_AuthBackend:
	# set to default values
	supports_object_permissions = False
	supports_anonymous_user = False

	def authenticate(self, **kwargs):
		user = None
		if all(arg in kwargs for arg in ("config_id", "pin")):
			try:
				config = VMBox_Config.objects.get(id=kwargs['config_id'])
				if config.verify_pin(kwargs['pin']):
					if isinstance(config.owner, User):
						user = config.owner
					else:  # By django convention authenticator backends return User type 
						logger.critical('TODO: need to derive User type from, '
							'owner type: %s' % config.owner.__class__.__name__)
			except ObjectDoesNotExist as odne:
				logger.error("VMBox Config not found: %s" % str(odne))

		return user

	def get_user(self, user_id):
		try:
			return User.objects.get(pk=user_id)
		except User.DoesNotExist:
			return None


def _convertVoicemails(output=sys.stderr):
	from models import VMMessage
	from django.db.models import Model
	vms = VMMessage.objects.all()
	for vm in vms:
		try:
			oldconfig = VMBox_Config.objects.get(owner_id=vm.owner_id)
			config = VMBox_Config.objects.get(owner_id=vm.owner_id)

			#url = vm.recording
			msg = Message(sender=None, sender_site=None, subject="Voice mail")
			msg.urgent = False
			msg.message_type = 'VM'
			msg.callback_number = vm.callbacknumber
			msg.read_flag = vm.read_flag
			msg.delete_flag = vm.deleted
			msg.save()
			MessageRecipient(message=msg, user=vm.owner).save()
			request = _FauxRequest()
			request.session['ivr_makeRecording_recording'] = vm.recording
			request.session['ivr_makeRecording_callbacknumber'] = vm.callbacknumber
			attachment = save_voice_attachment(request, msg)
			msg_body = msg.save_body("Message from %s." % msg.callback_number)
			config.notification_page = False
			config.notification_sms = False
			config.save()
			msg.send(request, msg_body, [attachment])
			msg.send_timestamp = time.mktime(vm.timestamp.timetuple())
			Model.save(msg)
			oldconfig.save()
		except Exception as e:
			err_msg = "Warning no VMBoxConfig found for: %s, Exception: %s\n" \
							% (repr(vm.owner), str(e))
			output.write(err_msg)
			logger.warning(err_msg)


def update_missing_durations(output=sys.stderr):
	logs = callLog.objects.filter(duration=None)

	for log in logs:
		try:
			if (settings.TWILIO_PHASE == 2):
				call = client.calls.get(log.callSID)
			else:
				call = client2008.calls.get(log.callSID)	
			log.call_duration = int(call.duration)
			log.save()
		except (urllib2.HTTPError, urllib2.URLError) as e:
			err_msg = "Error in update_missing_durations(): %s\n" % str(e)
			output.write(err_msg)
			logger.error(err_msg)


def get_prompt_verbage(practice, prompt_type, d={}):
	# get prompt, if not in database, use default verbage
	try:
		prompt = IVR_Prompt.objects.get(practice_location=practice, prompt=prompt_type)
		prompt_verbage = prompt.prompt_verbage
	except ObjectDoesNotExist:
		prompt_verbage = default_prompt_verbage(prompt_type)

	if (d):
		try:
			verbage = prompt_verbage.format(**d) + '.     '
		except KeyError:
			verbage = "Please check customer prompt setting. You have invalid key value specified."
	else:
		verbage = prompt_verbage
	return verbage


def _checkCallbackDuration(request, returnflag=True):
	"""
	checks call duration and updates callLog 
	plus optional returnflag default to return response
	"""
	from twilio import twiml as twilio
	if('CallStatus' in request.POST and request.POST['CallStatus'] == 'completed'):
#		import pdb; pdb.set_trace()
		try:
			callSID = request.POST['CallSid']
			if ('CallDuration' in request.POST):
				log = callLog.objects.get(callSID=callSID)
				log.call_duration = request.POST['CallDuration']
				log.save()
				logger.debug('%s: _checkCallbackDuration is called with sid %s call duration %s' % (
					request.session.session_key, callSID, request.POST['CallDuration']))
				if ('ParentCallSid' in request.POST):
					# also update parent log
					pcallSID = request.POST['ParentCallSid']
					plog = callLog.objects.get(callSID=pcallSID)
					plog.call_duration = request.POST['CallDuration']
					plog.save()
#  we will get callback with CallDuration if from Status
#			else:
#				auth, uri, = client.auth, client.account_uri
#				resp = make_twilio_request('GET', uri + '/Calls/%s' % callSID, auth=auth)
#				content = json.loads(resp.content)
#				log = callLog.objects.get(callSID=callSID)
#				log.call_duration = content['duration']
#				log.save()
#				logger.debug('%s: _checkCallbackDuration is called with sid %s log duration %s' % (
#					request.session.session_key, callSID, log.call_duration))
		except TwilioRestException as tre:
			logger.critical('Unable to get call status: %s' % tre.msg)
		except ObjectDoesNotExist as odne:
			# check for parent sid
			if 'ParentCallSid' in request.POST:
				pcallSID = request.POST['ParentCallSid']
				plog = callLog.objects.get(callSID=pcallSID)
				if ('CallDuration' in request.POST):
					plog.call_duration = request.POST['CallDuration']
					plog.save()
					logger.debug('%s: _checkCallbackDuration updating sid %s call duration %s' % (
						request.session.session_key, pcallSID, request.POST['CallDuration']))
				else:
					logger.debug('%s: _checkCallbackDuration psid %s no call duration found' % (
						request.session.session_key, pcallSID))
			else:
				logger.warning('Call log does not exist for sid: %s. Caller may have '
					'hung up shortly after Twilio starts call process.' % str(odne))
		if returnflag:
			r = twilio.Response()
			return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)
	else:
		return False


def _sanityCheckNumber(number):
	"""
	Matches number to optional + and digits; returns true if match; false otherwise
	all twilio phone numbers now come with international country code
	"""
	import re
	if (number == ''):
		return False
	p = re.compile('^[+]?\d+$')
	if not p.match(number):
		return False
	return True


def _matchUSNumber(number):
	"""
	checks if number has a settings.COUNTRY_CODE (e.g. +1) in front of a string of
	digits (don't care how many)
	"""
	import re
	match_cc_str = '\%s\d+$' % settings.COUNTRY_CODE
	p = re.compile(match_cc_str)
	if not p.match(number):
		return False
	return True


def _getUSNumber(number):
	"""
	returns phone number with + and country code stripped
	future todo: may want to save the country code or base the stripping on country settings
	tie into: from MHLogin.utils.fields MHLPhoneNumberField?
	"""
	if _matchUSNumber(number):
		return "%s" % (number[2:])
	else:
		if number[0] == '+':
			return "%s" % (number[1:])
		else:
			return "%s" % (number)


def _makeUSNumber(number):
	"""
	add COUNTRY_CODE (e.g. +1) to phone number to make it a US number for Twilio

	"""
	if _matchUSNumber(number):
		return number
	else:
		return "%s%s" % (settings.COUNTRY_CODE, number)


def create_call_group_list(request, specialty_id):
	#clear selections if exist
	request.session.pop('specialties_map', None)
	request.session.pop('call_groups_map', None)

	call_groups_map = {}  # call groups for this specialty
	specialties_map = {}  # empty
	s = ''
	error_string = ''
	error = False
	request.session['one_ok'] = '0'

	#get all Specialties for this practice
	specialty = Specialty.objects.get(id=specialty_id)

	call_groups = specialty.call_groups.all().order_by('number_selection')

	for call_group in call_groups:
		#if the same number selection already used, do not add to dictionary, process warning
		key = str(call_group.number_selection)
		if key in call_groups_map:
			error_string = error_string + ' Duplicate Number Selection in your IVR Tree '\
				'at Call Group Level.'
			error = True
		else:
			#build specialty with multi teams string
			#group_line = "To reach the on call %s doctor. For %s press %s.          " % \
				#((specialty.name),(call_group.team),(call_group.number_selection),)
			#replaced with line below:
			group_line = get_prompt_verbage(specialty.practice_location, MGS_PROMPT, \
				{'specialty': specialty.name, 'team': call_group.team, 
					'number': str(call_group.number_selection)})
			s = s + group_line
			call_groups_map[str(call_group.number_selection)] = call_group.id

	if (error):
		message_super_managers(request, specialty.practice.id,
						"DoctorCom Error: Phone Tree Set Up Incorrect",
						"Your practice's Phone Tree Set Up Incorrect:  {{error_text}}. "
						"Please contact support@mdcom.com and we will be happy to assist "
						"you in any way we can. Best,DoctorCom Staff",
						error_text=error_string
					)
		#email support
		email_body = "Practice %s's Phone Tree Set Up Incorrect. %s" % \
			(specialty.practice.practice_name, error_string)
		email_msg = EmailMessage("Customer Phone Tree Set Up Incorrect", 
			email_body, settings.DEFAULT_FROM_EMAIL, settings.SUPPORT_RECIPIENTS)
		email_msg.send()

	request.session['call_groups_map'] = call_groups_map
	request.session['specialties_map'] = specialties_map

	return  s


def create_dynamic_greeting(request, practice):
	#clear selections if exist
	request.session.pop('specialties_map', None)
	request.session.pop('call_groups_map', None)

	call_groups_map = {}  # specialties with ONE call group, no more iterations if reached
	specialties_map = {}  # specialties with multiple call groups
	error_string = ''
	error = False
	s_list = ''
	g_list = ''

	#get all Specialties for this practice
	specialties = Specialty.objects.filter(practice_location=practice).order_by('number_selection')

	#no specialties set up, should be only 1 call group
	if (len(specialties) == 0):
		call_groups = practice.call_groups.all()

		urgent_line = get_prompt_verbage(practice, NO_SPECIALTY_PROMPT)
		#urgent_line="To reach doctor on call press 2"

		g_list = urgent_line
		call_groups_map[str(2)] = call_groups[0].id
		# if more than one call groups for this practice, process warning here
		if (len(call_groups) > 1):
			error_string = error_string + ' Multiple Call Groups Exist Without Specialty Set Up.'
			error = True
	else:
		for specialty in specialties:
			#get all call group numbers associated with this location
			call_groups = specialty.call_groups.all().order_by('number_selection')

			#if same number already used do not add to dictionary, process warning
			key = str(specialty.number_selection)
			if key in call_groups_map or key in specialties_map:
				error_string = error_string + ' Duplicate Number Selection in your '\
					'IVR Tree at Specialty Level.'
				error = True
			else:				
				# if only 1 call groups for this specialty, make it call_groups_map, # 
				# pressed to match is that FROM SPECIALTY
				if (len(call_groups) == 1):
					#group_line = "To reach the on call %s doctor. For %s press %s.    " % \
						#((specialty.name),(call_groups[0].team),(specialty.number_selection),)
					#replaced with line below:
					group_line = get_prompt_verbage(practice, SGS_PROMPT, \
						{'specialty': specialty.name, 'team': call_groups[0].team, 
							'number': str(specialty.number_selection)})
					g_list = g_list + group_line
					call_groups_map[str(specialty.number_selection)] = call_groups[0].id
				# if only 1 specialty but multiple call groups, make it call_groups_map, # 
				# pressed to match is that FROM CALL GROUP
				elif (len(specialties) == 1):	
					for call_group in call_groups:	
						#if the same number selection already used, do not add 
						# to dictionary, process warning
						key = str(call_group.number_selection)
						if key in call_groups_map:
							error_string = error_string + \
								' Duplicate Number Selection in your IVR Tree at Call Group Level.'
							error = True
						else:
							#group_line = "To reach the on call %s doctor. For %s press 
							# %s.          " % ((specialty.name),(call_group.team),
							# (call_group.number_selection),)
							#replaced with line below:
							group_line = get_prompt_verbage(practice, SGS_PROMPT, \
								{'specialty': specialty.name, 'team': call_group.team, 
									'number': str(call_group.number_selection)})
							g_list = g_list + group_line
							call_groups_map[str(call_group.number_selection)] = call_group.id
				else:
					#build specialty with multi teams string
					#group_line = "To reach %s press %s.          " % ((specialty.name),
					# (specialty.number_selection),)
					#replaced with line below:
					group_line = get_prompt_verbage(practice, SPECIALTIES_PROMPT, \
						{'specialty': specialty.name, 'number': str(specialty.number_selection)})
					s_list = s_list + group_line
					specialties_map[str(specialty.number_selection)] = specialty.id

	#non_urgent_line="To leave non urgent message for staff press 1"
	non_urgent_line = get_prompt_verbage(practice, NON_URGENT_PROMPT)
	#THIS IS WHERE WE CREATE ACTUAL STRING TO SAY BACK TO CALLER:
	s = non_urgent_line + ".          " + g_list + s_list
	request.session['one_ok'] = '1'

	request.session['specialties_map'] = specialties_map
	request.session['call_groups_map'] = call_groups_map

	if (error):
		message_super_managers(request, practice.id,
						"DoctorCom Error: Phone Tree Set Up Incorrect",
						"Your practice's Phone Tree Set Up Incorrect:  {{error_text}}. "
						"Please contact support@mdcom.com and we will be happy to assist "
						"you in any way we can. Best,DoctorCom Staff",
						error_text=error_string
					)
		#email support
		email_body = "Practice %s's Phone Tree Set Up Incorrect. %s" % \
			(practice.practice_name, error_string)
		email_msg = EmailMessage("Customer Phone Tree Set Up Incorrect", 
			email_body, settings.DEFAULT_FROM_EMAIL, settings.SUPPORT_RECIPIENTS)
		email_msg.send()

	return s


TYPE_CALLED, TYPE_CALLER, TYPE_EITHER = 1, 2, 3
CTYPES = {TYPE_CALLED: 'Called', TYPE_CALLER: 'Caller', TYPE_EITHER: None}


def get_active_call(mhphone, ctype=TYPE_CALLED):
	""" Helper to get active call, defaults to in_progress state. 
		for ref: http://www.twilio.com/docs/api/2008-08-01/rest/call

	:param mhphone: the Doctorcom number we are querying
	:param ctype: call type is called, caller, or either
	:param status: 0 = Not Yet Dialed, 1 = In Progress, 
		2 = Complete, 3 = Busy, 4 = Application Error, 5 = No Answer
	:returns: call or None if no match found
	* note:
	status is changed to string in 2010 twilio API, since this is active calls,
	I've changed status to 'in_progress'.
	Flags does not exist;
	Called = To; Caller = From; 
	"""
	if (settings.TWILIO_PHASE == 2):
		auth, uri, call = client.auth, client.account_uri, None
		status = "in-progress"
		usmhphone = _makeUSNumber(mhphone)
		try:
			if (ctype == TYPE_EITHER):
				params = '/Calls.json?Status=%s' % (status)
			else:
				if (ctype == TYPE_CALLED):
					params = '/Calls.json?Status=%s&To=%s' % (status, str(usmhphone))
				else:
					params = '/Calls.json?Status=%s&From=%s' % (status, str(usmhphone))
			# twilio req appends .json in wrong place when params and no headers
			resp = make_twilio_request('GET', uri + params, auth=auth,
				**{'headers': {'Accept': 'application/json'}})
			content = json.loads(resp.content)
			calls = content['calls']
			logger.debug('get_active_call new params %s content %s calls %s' % (
				params, content, calls))
			call = calls[0] if calls else None
		except (TwilioRestException, ValueError, KeyError) as err:
			logger.critical("Problems querying active call list: %s" % str(err))
	else:
		auth, uri, call = client2008.auth, client2008.account_uri, None
		status = 1
		try:
			params = '/Calls.json?Status=%d&Flags=4' % (status) if ctype == TYPE_EITHER \
				else '/Calls.json?Status=%d&%s=%s' % (status, CTYPES[ctype], str(mhphone))
			# twilio req appends .json in wrong place when params and no headers
			resp = make_twilio_request('GET', uri + params, auth=auth,
				**{'headers': {'Accept': 'application/json'}})
			content = json.loads(resp.content)
			logger.debug('get_active_call content %s ' % content)
			calls = content['TwilioResponse']['Calls']
			fn = lambda call: mhphone in (call['Call']['Called'], call['Call']['Caller']) \
				if ctype == TYPE_EITHER else mhphone in (call['Call'][CTYPES[ctype]], )
			results = filter(fn, calls)
			if results:  # get 1st match but should be only 1
				if len(results) > 1:
					logger.error("Unexpected additional results for: %s" % str(mhphone))
				call = results[0]['Call']
		except (TwilioRestException, ValueError, KeyError) as err:
			logger.critical("Problems querying active call list: %s" % str(err))

	return call


def get_call_by_sid(callSid):
	""" 
	Helper to get call info based on SID
	"""
	if (settings.TWILIO_PHASE == 2):
		auth, uri, call = client.auth, client.account_uri, None
		try:
			params = '/Calls/%s.json' % (callSid)
			# twilio req appends .json in wrong place when params and no headers
			resp = make_twilio_request('GET', uri + params, auth=auth,
				**{'headers': {'Accept': 'application/json'}})
			content = json.loads(resp.content)
			call = content['call']
			logger.debug('get_call_by_sid content %s' % (call))
		except (TwilioRestException, ValueError, KeyError) as err:
			logger.critical("Problems querying call sid %s: %s" % (callSid, str(err)))
	else:
		auth, uri, call = client2008.auth, client2008.account_uri, None
		try:
			params = '/Calls/%s' % (callSid)
			# twilio req appends .json in wrong place when params and no headers
			resp = make_twilio_request('GET', uri + params, auth=auth,
				**{'headers': {'Accept': 'application/json'}})
			content = json.loads(resp.content)
			logger.debug('get_call_by_sid content %s ' % content)
			call = content['TwilioResponse']['Call']
		except (TwilioRestException, ValueError, KeyError) as err:
			logger.critical("Problems querying call sid %s: %s" % (callSid, str(err)))
	return call


def get_preferred_prov_number(provider):
	""" Helper returns current preferred number of a provider """
	forward, number = provider.forward_voicemail, provider.mdcom_phone
	if forward == 'MO':
		number = provider.user.mobile_phone
	elif forward == 'OF':
		number = provider.office_phone
	elif forward == 'OT':
		number = provider.user.phone
	return number

