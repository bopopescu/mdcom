
import urlparse

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned, ValidationError
from django.core.urlresolvers import reverse
from twilio.twiml import Say, Play

from MHLogin.DoctorCom.speech import logger
from MHLogin.DoctorCom.speech.models import SpeechConfig


def validate_no_other_active_configs(exclude):
	"""
	This function can be commented out or deprecated when we support
	more than one speech config.

	:raises: ValidationError - only one active speech config currently allowed
	"""
	# make sure no others are active, disable or remove when we support more than one
	other = SpeechConfig.objects.filter(is_active=True).exclude(id=exclude.id)
	if other.exists():
		raise ValidationError("Currently one active speech config allowed, turn "
			"off %s for this to be active." % (', '.join("%s" % o.name for o in other)))


# Temporary until we support more than one speech config
def get_active_speech_config():
	"""" Temporary until we design speech configs into our Subscription/Groups, We
	will use neospeech and the one configuration for it.  Speech configs may depend
	on license agreements we have with certain text to speech vendors as they provide
	voices/languages depending on package. """
	try:
		speechConfig = SpeechConfig.objects.get_subclass(is_active=True)
	except (ObjectDoesNotExist, MultipleObjectsReturned):
		speechConfig = None

	return speechConfig


def tts(text, sconf=None, voice=None, language=None):
	""" Until we support multiple speech configs use the current active one.
	Note if sconf parameter is not set by caller we hit the db.  The caller
	should cache the speech config where possible.
	"""
	say_or_play = None
	try:
		sconf = sconf or get_active_speech_config()
		if sconf:
			try:
				path, stat = sconf.get_or_create_voice_path(text)
				if path != None:
					abs_uri = '://'.join([settings.SERVER_PROTOCOL, settings.SERVER_ADDRESS])
					url = reverse('MHLogin.DoctorCom.speech.views.get_voice_clip', kwargs=path)
					say_or_play = Play(urlparse.urljoin(abs_uri, url))
				else:
					logger.error("Path is null, details: %s" % str(stat))
			except NotImplementedError as nie:
				logger.error("Most likely calling base class: %s" % str(nie))
		else:
			logger.info("Primary speech config not configured, using default")
	except Exception as err:
		# enclose in try/catch Exception for now
		logger.critical("Unexpected, bug: %s" % str(err))

	say_or_play = say_or_play or Say(text, voice=voice)
	logger.info("Returning say or play: %s" % str(say_or_play))

	return say_or_play

