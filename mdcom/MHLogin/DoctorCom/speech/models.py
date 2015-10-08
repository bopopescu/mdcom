
import os
import sys
from hashlib import sha1

from django.conf import settings
from django.conf.global_settings import LANGUAGES
from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.dispatch import receiver

from django.db import models
from django.db.models.signals import pre_save, pre_delete, post_save, post_init, post_delete

from MHLogin.utils.storage import create_file, get_file
from MHLogin.DoctorCom.speech import logger
from MHLogin.DoctorCom.speech.neospeech import driver, driver_h
from MHLogin.DoctorCom.speech.model_utils import InheritanceManager


class SpeechConfig(models.Model):
	""" Base class configuration for our tts vendors.  Currently is_active flag is
	used to check for single speech config in system.  When multiple active configs
	are supported is_active flag will do license validation on server if needed.
	"""

	regex = r'^[A-z0-9]{1,64}$'
	# name of this speech config, must be unique and non-null
	name = models.CharField(max_length=64, blank=False, unique=True, validators=[RegexValidator(regex)])
	# spoken language for this config, dirname in tts will be this entry
	spoken_lang = models.CharField(max_length=16, choices=LANGUAGES, default='en')
	# is configuration active?  Currently support one but do unique validation in
	# signal handler so if we change later we don't change db structure
	is_active = models.BooleanField(default=False)

	objects = InheritanceManager()  # based off django-model-utils

	__unicode__ = lambda self: self.name

	def get_server_status(self):
		""" Request status from server, should be handled in implmented class.
		return format is a dictionary { 'status' : <int code>,
		'status_text : <any text>, 'data' : None }
		 """
		name = sys._getframe().f_code.co_name
		logger.error("%s not implemented in base-class" % name)
		raise NotImplementedError("%s needs to be implemented in sub-class" % name)

	def get_or_create_voice_path(self, text):
		""" Implement in sub-class, which does all the dirty work """
		name = sys._getframe().f_code.co_name
		logger.error("%s not implemented in base-class" % name)
		raise NotImplementedError("%s needs to be implemented in sub-class" % name)

	def get_encoding_string(self):
		""" Implement in sub-class, which does all the dirty work """
		name = sys._getframe().f_code.co_name
		logger.error("%s not implemented in base-class" % name)
		raise NotImplementedError("%s needs to be implemented in sub-class" % name)


class NeospeechConfig(SpeechConfig):
	""" Allows for multiple neospeech configurations.  Values here are
	dependent on license agreements we have with neospeech. """
	# server hostname or ipv4/ipv6
	server = models.CharField(max_length=255, blank=True)
	# tts server port number, typically 7000
	server_port = models.PositiveIntegerField(default=driver_h.TTS_DATA_PORT,
				validators=[MinValueValidator(0), MaxValueValidator(65535)])
	# tts server status port, typically 7777
	status_port = models.PositiveIntegerField(default=driver_h.TTS_STATUS_PORT,
				validators=[MinValueValidator(0), MaxValueValidator(65535)])
	# tts server admin port, typically 7100
	admin_port = models.PositiveIntegerField(default=driver_h.TTS_ADMIN_PORT,
				validators=[MinValueValidator(0), MaxValueValidator(65535)])
	# default voice id for this configuration, may be changed per request
	# but realize it may fail due to licensing specific to neospeech config.
	voice_id = models.IntegerField(default=driver_h.TTS_JULIE_DB,
				choices=((k, v) for k, v in driver_h.VOICES.items() if k != None))
	# storage format of voice data
	encoding = models.IntegerField(default=driver_h.FORMAT_WAV,
				choices=((k, v) for k, v in driver_h.FORMAT.items() if k != None))
	# volume setting range 0-500, default 100
	volume = models.PositiveIntegerField(default=100,
				validators=[MinValueValidator(0), MaxValueValidator(500)])
	# speed setting range 50-400, default 100
	speed = models.PositiveIntegerField(default=100,
				validators=[MinValueValidator(50), MaxValueValidator(400)])
	# pitch setting range 50-200, default 100
	pitch = models.PositiveIntegerField(default=100,
				validators=[MinValueValidator(50), MaxValueValidator(200)])

	def get_server_status(self):
		""" Request status from server """
		# Transient driver should be installed, if not AttributeError
		return self.driver.request_status(self.server, self.status_port)

	def get_or_create_voice_path(self, text):
		""" Lookup text in voiceclip table, creating entry if needed. By default
		encoding uses the encoding value in model if encoding paramter is None
		"""
		path = stat = None
		try:
			vc = VoiceClip.objects.get(config=self, spoken_text=text)
			vc.save()  # access_date field updates when auto_now attribute set    
			# verify existence in fs before moving on
			verify = get_file(os.path.join('tts', vc.config.name, vc.filename))
			if not verify:
				vc.delete()  # cleanup clip - occurs when user changes config name
				raise ObjectDoesNotExist()
			verify.close()
			path = {'confname': self.name, 'filename': vc.filename}
		except ObjectDoesNotExist:
			# first time this tts request is made to this config
			fnamehash = '_'.join([self.name, sha1(text).hexdigest()])
			storage = create_file(os.path.join('tts', self.name, fnamehash))
			if storage:
				stat = self.driver.request_buffer_ex(text, fmt=self.encoding,
							volume=self.volume, speed=self.speed, pitch=self.pitch)
				if (stat['status'] == driver_h.TTS_RESULT_SUCCESS):
					vc = VoiceClip.objects.create(filename=fnamehash, spoken_text=text,
						checksum=sha1(''.join(map(chr, stat['data']))).hexdigest(), config=self)
					storage.set_contents(stat['data'])
					storage.close()
					path = {'confname': self.name, 'filename': vc.filename}
				else:
					logger.error("Driver request failed: %s" % stat['status_text'])
			else:  # create_file/get_file api is lacking error handling, we should
				# return more than None if failure possibly preserving exceptions.
				# Saw permission issue once, we should pass that info up stack.
				stat = "Storage creation failure: %s" % fnamehash
				logger.error(stat)

		return (path, stat)

	def get_encoding_string(self):
		""" returns the format string associated with Neospeech encoding

		:returns: text based format of encoding
		"""
		return driver_h.FORMAT[self.encoding]


class VoiceClip(models.Model):
	""" VoiceClip store information about audio clips (typically voice clips
	generated by tts servers).  Filename generation is done by SpeechConfig
	subclasses but typically is an sha1 hash of the text to be spoken. """

	# pointer back to configuration used to create this clip
	config = models.ForeignKey(SpeechConfig, null=False, blank=False)
	# filename <config name>_<sha1(spoken_text)>
	filename = models.CharField(max_length=128, blank=False, editable=False)
	# checksum sha1() of the file contents
	checksum = models.CharField(max_length=128, blank=True, editable=False)

	# the text to convert to audible speech
	spoken_text = models.TextField(editable=False)
	# counter how many times this voice clip has been accessed
	access_count = models.PositiveIntegerField(default=0, editable=False)
	# last time this voice clip was accessed
	access_date = models.DateTimeField(auto_now=True, editable=False)
	# datetime of voice clip creation
	create_date = models.DateTimeField(auto_now_add=True, editable=False)

	def get_encoding_string(self):
		""" Returns the mimetype encoding of the speech config this voice clip
		is associated with. """
		return SpeechConfig.objects.get_subclass(id=self.config.id).get_encoding_string()


""" The following are signals and helpers to manage speech models """


@receiver(pre_delete, sender=VoiceClip)
def pre_delete_voiceclip_callback(sender, **kwargs):
	""" Signal before voiceclip deleted, remove associated media from storage """
	# delete media associated with this voiceclip
	vc = kwargs['instance']
	try:
		# Assume local storage until we have delete() support in utils.storage
		os.remove(os.path.join(settings.MEDIA_ROOT, 'tts', vc.config.name, vc.filename))
	except (OSError), oe:
		logger.error("Problems removing VoiceClip: %s, filename empty or not in "
					"filesystem.  Error: %s" % (vc.filename, str(oe)))


@receiver(pre_save, sender=SpeechConfig)
@receiver(pre_save, sender=NeospeechConfig)
def pre_save_speechconfig_callback(sender, **kwargs):
	# Before save check only one active speech config in system, this is
	# temporary constraint until if we support more speech configs.
	conf_ram = kwargs['instance']
	if (conf_ram.is_active == True):
		# Remove this when we support more than 1 active config
		from MHLogin.DoctorCom.speech.utils import validate_no_other_active_configs
		validate_no_other_active_configs(conf_ram)


@receiver(post_init, sender=NeospeechConfig)
def post_init_neospeech_callback(sender, **kwargs):
	# create transient driver element based db configuration
	update_neo_inst(kwargs['instance'])


@receiver(post_save, sender=NeospeechConfig)
def post_save_neospeech_callback(sender, **kwargs):
	# create transient driver element based db configuration
	update_neo_inst(kwargs['instance'])


@receiver(post_delete, sender=NeospeechConfig)
def post_delete_neospeech_callback(sender, **kwargs):
	# create transient driver element based db configuration
	config = kwargs['instance']
	config.driver.shutdown()
	try:
		# Assume local storage until we have delete() support in utils.storage
		os.rmdir(os.path.join(settings.MEDIA_ROOT, 'tts', config.name))
	except (OSError), oe:  # don't recurse delete directory
		logger.error("Problems removing SpeecConfig: %s, error: %s" % (config.name, str(oe)))


def update_neo_inst(neo_config):
	# helper to update transient driver
	if not hasattr(neo_config, 'driver'):
		neo_config.driver = driver.create_neo_driver()
	# update driver settings
	neo_config.driver.server_ip = neo_config.server
	neo_config.driver.server_port = neo_config.server_port
	neo_config.driver.server_status_port = neo_config.status_port
	neo_config.driver.voice = neo_config.voice_id

