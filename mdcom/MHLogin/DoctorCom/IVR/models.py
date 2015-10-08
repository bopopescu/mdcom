
import kronos
import datetime

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.db import models
from django.utils.encoding import smart_str
from django.utils.translation import ugettext_lazy as _

from MHLogin.KMS.utils import recrypt_keys, strengthen_key
from MHLogin.KMS.shortcuts import recrypt_ivr_key_via_web_creds
from MHLogin.KMS.models import UserPrivateKey, CRED_IVRPIN
from MHLogin.utils.admin_utils import mail_admins
from MHLogin.utils.fields import MHLPhoneNumberField
from MHLogin.utils.mh_logging import get_standard_logger


# Setting up logging
logger = get_standard_logger('%s/DoctorCom/IVR/models.log' % (settings.LOGGING_ROOT),
							'DCom.IVR.models', settings.LOGGING_LEVEL)


def get_hexdigest(algorithm, salt, raw_pin):
	"""
	Returns a string of the hexdigest of the given plaintext password and salt
	using the given algorithm ('md5', 'sha1' or 'crypt').

	This was taken from Based on Django 1.1.1's password hash generator.
	"""
	from hashlib import sha1, md5
	raw_pin, salt, digest = smart_str(raw_pin), smart_str(salt), None
	if algorithm == 'crypt':
		try:
			import crypt
		except ImportError:
			raise ValueError(_('"crypt" password algorithm not supported in this environment'))
		digest = crypt.crypt(raw_pin, salt)
	elif algorithm == 'md5':
		digest = md5(salt + raw_pin).hexdigest()
	elif algorithm == 'sha1':
		digest = sha1(salt + raw_pin).hexdigest()
	else:
		raise ValueError(_("Got unknown password algorithm type in password."))
	return digest


def check_pin(raw_pin, enc_pin):
	"""Returns a boolean of whether the raw_password was correct. Handles
	encryption formats behind the scenes.

	This was taken from Based on Django 1.1.1's password hash generator.
	"""
	algo, salt, hsh = enc_pin.split('$')
	return hsh == get_hexdigest(algo, salt, raw_pin)


def get_new_pin_hash(pin):
	import random
	algo = 'sha1'
	salt = get_hexdigest(algo, str(random.random()), str(random.random()))[:5]
	hash = get_hexdigest(algo, salt, pin)
	return '%s$%s$%s' % (algo, salt, hash)


class VMMessage(models.Model):
	# The "individual" whose voicemail this is. We are going with a generic
	# relation here so that messages can be associated with any object type,
	# be it a user, office, site, or something we haven't thought of.
	owner_type = models.ForeignKey(ContentType)	
	owner_id = models.PositiveIntegerField()
	owner = generic.GenericForeignKey('owner_type', 'owner_id')

	callerID = models.CharField(max_length=64)

	# Path to a recording of the user speaking his/her voice OR the twilio ID of
	# the recording. Note that the distinction shall be that paths start with a
	# forward slash character, while the Twilio recordings start with the
	# letters 'RE'.
	# 
	# Please do not get the recording field value directly. Rather, please use
	# the getRecordingUrl method instead so that the read_timestamp can be set
	# and so that the correct URL is given back, regardless of where the
	# recording is stored.
	recording = models.TextField()

	# Management Fields
	deleted = models.BooleanField(default=False)  # We don't delete just mark as deleted
	read_flag = models.BooleanField(default=False)
	read_timestamp = models.DateTimeField(null=True)

	# Book keeping
	timestamp = models.DateTimeField(auto_now_add=True)
	#answering service
	answeringservice = models.BooleanField(default=False)
	callbacknumber = MHLPhoneNumberField(blank=True)

	def delete(self, *args, **kwargs):
		# Don't delete this message. Just mark it as deleted.
		self.deleted = True
		self.save()
		# Alternatively
		#raise Exception('Voicemail messages may not be deleted.')

	def sanitize(self):
		""" Sanitizes any personally identifying data from this object. NOTE THAT THIS
		DOES NOT SAVE THE OBJECT!"""
		if (not settings.DEBUG):
			raise Exception('You must be in DEBUG mode to use this function.')
		self.callerID = '8004664411'
		self.recording = 'http://api.twilio.com/2008-08-01/Accounts/'\
			'AC087cabfd0a453a05acceb2810c100f69/Recordings/REf8afc497f43d8e1e9bc229a415ebe100'

	def getRecordingUrl(self):
		if (not self.read_timestamp):
			self.read_timestamp = datetime.datetime.now()
			self.read_flag = True
			self.save()
		# TODO_RECORDING:
		# check to see if this is a Twilio URL or a cloud storage URL, then
		# modify it appropriately if needed.
		return self.recording


class VMBox_Config(models.Model):	
	# The "individual" whose voicemailbox this is. We are going with a generic
	# relation here so that we can use this system for offices/sites who wish
	# to have a voicemailbox for the office/site itself.
	owner_type = models.ForeignKey(ContentType)
	owner_id = models.PositiveIntegerField()
	owner = generic.GenericForeignKey('owner_type', 'owner_id')

	# A hash of the PIN should be set here. May be blank in the event of this
	# being an office/site voicemail box.
	pin = models.CharField(max_length=120, blank=True)

	# Path to a recording of the user speaking his/her voice OR the twilio ID of
	# the recording. Note that the distinction shall be that paths start with a
	# forward slash character, while the Twilio recordings start with the
	# letters 'RE'.
	name = models.TextField()

	# Path to the voicemail greeting OR the twilio ID of the recording. Note
	# that the distinction shall be that paths start with a forward slash
	# character, while the Twilio recordings start with the letters 'RE'.
	greeting = models.TextField()

	# give us an easy way to check to make sure that the voicemail box
	# configuration is complete
	config_complete = models.BooleanField(default=False)

	# Allow the user to set how they wish to be notified of new voicemail
	# messages.
	notification_email = models.BooleanField(default=False)
	notification_sms = models.BooleanField(default=True)
	notification_page = models.BooleanField(default=True, 
		help_text=_("Send pager notifications for received answering service messages"))

	def _set_pin(self, raw_pin):
		"""
		Based on Django 1.1.1's password hash generator.
		"""
		import random
		algo = 'sha1'
		salt = get_hexdigest(algo, str(random.random()), str(random.random()))[:5]
		hash = get_hexdigest(algo, salt, raw_pin)
		self.pin = '%s$%s$%s' % (algo, salt, hash)

	def change_pin(self, request, **kwargs):
		new_pin = kwargs.get('new_pin', None)
		if not new_pin:
			raise Exception('new_pin is required')
		old_key = kwargs.get('old_key', None)
		# TESTING_KMS_INTEGRATION
		from MHLogin.MHLUsers.models import MHLUser
		user = MHLUser.objects.get(id=self.owner.id)
		uprivs = UserPrivateKey.objects.filter(user=user, credtype=CRED_IVRPIN, gfather=True)
		if uprivs.exists():
			recrypt_keys(uprivs, settings.SECRET_KEY, new_pin)
		elif old_key:
			uprivs = UserPrivateKey.objects.filter(user=user, credtype=CRED_IVRPIN)
			recrypt_keys(uprivs, old_key, strengthen_key(new_pin), True)
		else:  # business logic: recrypt ivr key via user's webapp based ivr key
			recrypt_ivr_key_via_web_creds(user, request, new_pin)

		self._set_pin(new_pin)
		self.save()

	#add by xlin 20120718
	def set_pin(self, pin):
		self._set_pin(pin)
		self.save()

	def verify_pin(self, raw_pin):
		"""
		Returns a boolean of whether the raw_password was correct. Handles
		encryption formats behind the scenes.

		Based on Django 1.1.1's password hash generator.
		"""
		return check_pin(raw_pin, self.pin)

	def sanitize(self):
		"""Sanitizes any personally identifying data from this object. NOTE THAT THIS 
		DOES NOT SAVE THE OBJECT!"""
		if (not settings.DEBUG):
			raise Exception('You must be in DEBUG mode to use this function.')
		self._set_pin('1234')
		self.greeting = 'http://api.twilio.com/2008-08-01/Accounts/'\
			'AC087cabfd0a453a05acceb2810c100f69/Recordings/REf8afc497f43d8e1e9bc229a415ebe100'
		self.name = 'http://api.twilio.com/2008-08-01/Accounts/'\
			'AC087cabfd0a453a05acceb2810c100f69/Recordings/REf8afc497f43d8e1e9bc229a415ebe100'

SOURCE_CHOICES = (
		# Initial Configuration
		('OC', _('Outside Call to Doctor Com')),
		('AS', _('Answering Service Call')),
		('VM', _('Checking voicemall')),
		('CB', _('Callback for answering service')),
		('CC', _('Click 2 Call')),
		('FC', _('Forwarded or Second Leg Call')),
		)


class callLog(models.Model):
	"""
	Call session information. This keeps track of call attributes that are across 
	all Twilio requests, such as caller, called, phone numbers, call duration, etc.
	"""
	# Callers
	caller_type = models.ForeignKey(ContentType, null=True, blank=True, 
		related_name="callLog_callertype")
	caller_id = models.PositiveIntegerField(null=True, blank=True)
	mdcom_caller = generic.GenericForeignKey('caller_type', 'caller_id')
	# The following is *always* set, just so that we know what number the call
	# was made from. This should be the number the caller is coming from, *not*
	# the caller's DoctorCom number if they have one. This is intentional
	# duplicative information.
	caller_number = MHLPhoneNumberField(blank=True)

	# Calleds (recipients)
	called_type = models.ForeignKey(ContentType, null=True, blank=True, 
				related_name="callLog_calledtype")
	called_id = models.PositiveIntegerField(null=True, blank=True)
	mdcom_called = generic.GenericForeignKey('called_type', 'called_id')
	# The following is *always* set, just so that we know what number the call
	# was received at. This is intentional duplicative information. This may
	# be the user's DoctorCom number. It's the number that the user dialed.
	called_number = MHLPhoneNumberField(blank=True)

	caller_spoken_name = models.TextField()

	callSID = models.CharField(max_length=64, unique=True, db_index=True)
	call_connected = models.BooleanField(default=False)

	# C2C Call Data
	# FIXME: The following import creates a circular import, which results in
	# import failures a plenty. For the time being, we're going to use an
	# Integer field that Django would be using.
	#from MHLogin.DoctorCom.models import Click2Call_Log
	#c2c_entry = models.ForeignKey(DCom.models.Click2Call_Log, null=True, blank=True)
	c2c_entry_id = models.IntegerField(null=True, blank=True)

	call_duration = models.IntegerField(null=True)
	#current_site = models.ForeignKey(Site, null=True, blank=True, 
	#  related_name="ivr_calllog_current_site")
	# Book keeping
	timestamp = models.DateTimeField(auto_now_add=True)
	call_source = models.CharField(max_length=2, choices=SOURCE_CHOICES)


EVENT_CHOICES = (
		# Initial Configuration
		('I_STR', _('Initial Configuration Start')),
		('I_FIN', _('Initial Configuration Finish')),

		# Configuration Changes
		('F_PCH', _('Pin Change')),
		('F_GCH', _('Greeting Change')),
		('F_NCH', _('Name Change')),

		# Call Events
		('C_ACC', _('Call Accepted/Connected')),
		('C_REJ', _('Call Rejected')),

		# Voicemail Events
		('V_AFL', _('Authentication Failure')),
		('V_ASU', _('Authentication Success')),
		('V_NMP', _('New Message Play')),
		('V_NAP', _('New Answering Service Message Play')),
		('V_OAP', _('OldAnswering Service Message Play')),
		('V_OMP', _('Old Message Play')),
		('V_MDL', _('Message Delete')),
		('V_NMG', _('New Message')),
	)


class callEvent(models.Model):
	callSID = models.CharField(max_length=64, db_index=True)
	event = models.CharField(max_length=5, choices=EVENT_CHOICES)

	timestamp = models.DateTimeField(auto_now_add=True)


class callEventTarget(models.Model):
	event = models.ForeignKey(callEvent, unique=True)

	# The following field is used for keeping track of what objects this event
	# is acting on. The original implementation had voicemail messages in mind
	# (e.g., which message was played? which message was deleted?).
	target_type = models.ForeignKey(ContentType)	
	target_id = models.PositiveIntegerField()
	target = generic.GenericForeignKey('target_type', 'target_id')


FAILURE_CHOICES = (
	('DL', _('Failure to download recording from twilio')),
	('UL', _('Failure to upload recording to rackspace cloud')),
)


class AnsSvcDLFailure(models.Model):
	"""
	Keeps track of which answering service messages have had message fetch failures.
	"""
	# Meta
	practice_id = models.IntegerField()  # The PK for the practice
	error_timestamp = models.DateTimeField(auto_now_add=True)
	resolved = models.BooleanField(default=False, db_index=True)
	resolution_timestamp = models.DateTimeField(null=True, blank=True)
	failure_type = models.CharField(max_length=2, choices=FAILURE_CHOICES, default='DL')
	# Call Data
	post_data = models.TextField()
	call_sid = models.CharField(max_length=255, db_index=True)
	caller = models.CharField(max_length=20)
	called = models.CharField(max_length=20)
	recording_url = models.TextField(null=True, blank=True)
	callback_number = MHLPhoneNumberField()

	# Message objects
	# The PK for the original error notice message.	
	error_message_uuid = models.CharField(max_length=32, blank=True, null=True)
	# The PK for the resolution notification message.	
	resolution_message_uuid = models.CharField(max_length=32, blank=True, null=True)

	def init_from_post_data(self, post_data_dict):
		"""
		Initialize this object based on POST data from Twilio. This is simply
		a shortcut/utility method.

		Warning: post_data_dict is assumed to be sanitized!
		"""
		self.post_data = repr(dict(post_data_dict))
		self.call_sid = post_data_dict['CallSid']
		self.caller = post_data_dict['Caller']
		self.called = post_data_dict['Called']

	def save(self, *args, **kwargs):
		if (self.pk):
			raise Exception(_('Saving existing entries is disallowed. Update this '
				'object through its access methods.'))
		super(AnsSvcDLFailure, self).save(*args, **kwargs)

		log = AnsSvcDLFailureActivityLog(call_sid=self.call_sid, action='NEW')
		log.save()

	def mark_resolved(self, message):
		self.resolved = True
		self.resolution_timestamp = datetime.datetime.now()
		if (hasattr(message, 'uuid')):
			self.resolution_message_uuid = message.uuid
		else:
			self.resolution_message_uuid = message
		self.recording_url = None
		super(AnsSvcDLFailure, self).save()


DLFAILUREACTIVITY_ACTIONS = (
	('NEW', _('Failure Entry Creation')),
	('FAI', _('Resolution Failure')),
	('SUC', _('Resolution Success')),
	# Generated whenever we initially try to download the WAV file, but fail to.
	('DLF', _('Download Failure')),
)


class AnsSvcDLFailureActivityLog(models.Model):
	"""Keeps track of actions on answering service fetch failures.
	"""
	call_sid = models.CharField(max_length=255, db_index=True)
	timestamp = models.DateTimeField(auto_now_add=True)

	action = models.CharField(choices=DLFAILUREACTIVITY_ACTIONS, max_length=3)

	# Store data about failures, if appropriate.
	error_data = models.TextField(blank=True, null=True)

	def set_error_data(self, exception):
		"""
		Takes a urllib2.HTTPError or urllib2.URLError argument and formats it
		in a way that makes sense and stores it into self.error_data.
		"""
		error_data = dict()

		error_data['repr'] = repr(exception)

		if (hasattr(exception, 'reason')):
			# We have a URLError.
			error_data['reason'] = exception.reason
		else:
			# We have an HTTPError or similar.
			error_data['code'] = exception.code
			error_data['payload'] = exception.read()

		self.error_data = repr(error_data)

#type of IVR prompts with version 2
NON_URGENT_PROMPT = '1'
NO_SPECIALTY_PROMPT = '2'
SGS_PROMPT = '3'
MGS_PROMPT = '4'
SPECIALTIES_PROMPT = '5'

PROMPT_CHOICES = (
		(NON_URGENT_PROMPT, 'Non Urgent Message'),
		(NO_SPECIALTY_PROMPT, 'Urgent Message for Practice Without Specialty'),
		(SGS_PROMPT, 'Urgent Message for Single Call Group OR Single Specialty'),
		(MGS_PROMPT, 'Urgent Message for Multi Call Group Specialty'),
		(SPECIALTIES_PROMPT, 'Select Specialty for Multi Call Group Multi Specialties'),
		)


def default_prompt_verbage(prompt_type):
	return {
		NON_URGENT_PROMPT: "To leave non urgent message for staff press 1",
		NO_SPECIALTY_PROMPT: "To reach doctor on call press 2",
		SGS_PROMPT: "To reach the on call {specialty} doctor. For {team} press {number}",
		MGS_PROMPT: "To reach the on call {specialty} doctor. For {team} press {number}",
		SPECIALTIES_PROMPT: "To reach {specialty} press {number}",
		}.get(prompt_type, "Prompt Not Defined.")


class IVR_Prompt(models.Model):
	"""Verbage said to user who calls IVR tree, if not present, current hardcoded strings are used
	"""
	practice_location = models.ForeignKey('MHLPractices.PracticeLocation')
	prompt = models.CharField(max_length=1, choices=PROMPT_CHOICES, verbose_name="Prompt Type")
	prompt_verbage = models.CharField(max_length=200, null=False, blank=False,
		help_text="For Specialty Call Groups prompts: Use {specialty} for specialty "
			"name, {team} for call group team name, {number} for number selection. Ex: "
				"To reach the on call {specialty} doctor. For {team} press  {number}")

	class Meta():
		unique_together = (('practice_location', 'prompt',),)
		ordering = ['practice_location']

	def __unicode__(self):
		return "%s's prompt type: %s '%s'" % (
			self.practice_location.practice_name, self.prompt, self.prompt_verbage)


@kronos.register("* * * * *")  # every minute
def resolve_anssvc_dl_failures():
	"""
	Entry point used by kronos to resolve anssvc dl failures, checks every minute.  For 
	django kronos installtasks command to work decorated function must be in python 
	module loaded at startup such as: models, __init__, admin, .cron, etc..
	"""
	try:
		from MHLogin.DoctorCom.IVR.utils import resolve_download_failure
		msgs = AnsSvcDLFailure.objects.filter(resolved=False)
		for msg in msgs:
			resolve_download_failure(msg)
		logger.info("resolve_anssvc_dl_failures, DONE.")
	except Exception as e:
		# enclose in try/catch Exception for now, resolve_download_failure()
		# is run every minute, code was not active on production until 1.64.00.
		mail_admins("Problems in resolve_anssvc_dl_failures()", str(e))
		logger.error("Problems in resolve_anssvc_dl_failures() %s" % str(e))

