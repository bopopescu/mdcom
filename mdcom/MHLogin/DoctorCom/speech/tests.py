
import hmac
import mock
import urlparse
import time

from hashlib import sha1
from base64 import encodestring

from django.utils import unittest
from django.conf import settings
from django.core.urlresolvers import reverse
from django.test.client import Client
from django.core.exceptions import ObjectDoesNotExist

from twilio.twiml import Play
from MHLogin.DoctorCom.speech.neospeech import driver
from MHLogin.DoctorCom.speech.neospeech import driver_h
from MHLogin.DoctorCom.speech.models import SpeechConfig, NeospeechConfig, VoiceClip
from MHLogin.DoctorCom.speech.utils import get_active_speech_config, tts


# list supported servers here: type and configuration
SPEECH_SERVERS = {"neospeech": ("unittest_speech", "dev-maint.mdcom.com"), }

test_driver = driver.create_neo_driver(server_ip=SPEECH_SERVERS['neospeech'][1])
test_driverserver_port = driver_h.TTS_DATA_PORT
test_driver.server_status_port = driver_h.TTS_STATUS_PORT
test_driver.voice = driver_h.TTS_JULIE_DB

SPEECH_TESTS_ON = False
if (test_driver.request_status(SPEECH_SERVERS['neospeech'][1], 
		test_driver.server_status_port)['status'] == driver_h.TTS_STATUS_SERVICE_ON):
	SPEECH_TESTS_ON = True


@unittest.skipIf(SPEECH_TESTS_ON == False, "Skipping Speech tests")
class SpeechTest(unittest.TestCase):
	""" SpeechTest unittester
	"""
	@classmethod
	def setUpClass(cls):
		# create supported drivers to test, right now neo
		cls.neo = SPEECH_SERVERS['neospeech']
		NeospeechConfig.objects.get_or_create(name=cls.neo[0],
			server=cls.neo[1], server_port=driver_h.TTS_DATA_PORT,
			status_port=driver_h.TTS_STATUS_PORT, admin_port=driver_h.TTS_ADMIN_PORT,
			voice_id=driver_h.TTS_JULIE_DB, speed=85, is_active=True)

	@classmethod
	def tearDownClass(cls):
		try:
			sc = SpeechConfig.objects.get_subclass(name=cls.neo[0])
			sc.delete()	 # comment if we want to examine media files
		except ObjectDoesNotExist:
			# TODO: tearDownClass() called twice when running Suite but not when individually:
			# http://docs.python.org/2/library/unittest.html#class-and-module-fixtures
			# http://sourceforge.net/tracker/index.php?func=detail&aid=3394792&group_id=85796&atid=577329
			# Not sure of a solution here, setUpModule(), tearDownModule()?
			pass

	@mock.patch.object(driver.UnixDriver, 'request_status', 
		return_value={'status': driver_h.TTS_STATUS_SERVICE_ON, 'status_text': 'OK'})
	def test_neo_speech_status(self, req_status):
		""" Sends request status message to neospeech server """
		sc = SpeechConfig.objects.get_subclass(name=self.neo[0])
		rc = sc.get_server_status()
		self.assertTrue(rc['status'] == driver_h.TTS_STATUS_SERVICE_ON, rc['status_text'])

	def test_neo_speech_voice_clip(self):
		""" Sends request buffer message to neospeech server """
		sc = SpeechConfig.objects.get_subclass(name=self.neo[0])
		# get url of the .wav or .mp3 that will say this text
		tts_text = "This is a test of the emergency broadcast system."
		retry = 5
		# sleep 3 seconds if max error (only for trial version) and retry up to 5 times
		while retry > 0:
			path_tup = sc.get_or_create_voice_path(tts_text)
			if path_tup[1]['status'] == driver_h.TTS_MAX_ERROR:
				time.sleep(3.0)
			else:
				break
			retry -= 1
		self.assertTrue(path_tup[0] != None, path_tup[1])

		vc = VoiceClip.objects.get(config=sc, spoken_text=tts_text)
		# would raise exception if more than one, check spoken_text
		self.assertTrue(vc.spoken_text == tts_text, vc.spoken_text)

	def test_call_to_utility_function(self):
		sc = get_active_speech_config()
		self.assertTrue(sc.name == self.neo[0], sc.name)

	def test_speech_uri_join(self):
		abs_uri = '://'.join([settings.SERVER_PROTOCOL, settings.SERVER_ADDRESS])
		# filename does not support extensions, do we want to keep it like that?
		url = reverse('MHLogin.DoctorCom.speech.views.get_voice_clip',
			kwargs={'confname': 'test_conf', 'filename': 'test'})
		# see if we can joing them
		urlparse.urljoin(abs_uri, url)
		# this test raises numerous exceptions if failed, mainly ValueError

	def test_speech_base_raises_nie(self):
		sp = SpeechConfig.objects.create(name='spooch_confeeg')

		test = SpeechConfig.objects.get_subclass(name=sp.name)
		self.assertRaises(NotImplementedError, test.get_or_create_voice_path, "Boo!")
		self.assertRaises(NotImplementedError, test.get_server_status)

	def test_voice_clip_view(self):
		""" Test the speech view request """
		sc = SpeechConfig.objects.get_subclass(name=self.neo[0])
		c = Client()
		tts_text = "Bingo!  Press 1 to change your attitude, 2 to change outlook on life."
		retry = 5
		# sleep 3 seconds if max error (only for trial version) and retry up to 5 times
		while retry > 0:
			path_tup = sc.get_or_create_voice_path(tts_text)
			if path_tup[1]['status'] == driver_h.TTS_MAX_ERROR:
				time.sleep(3.0)
			else:
				break
			retry -= 1
		self.assertTrue(path_tup[0] != None, path_tup[1])

		vc = VoiceClip.objects.get(config__name=path_tup[0]['confname'], spoken_text=tts_text)

		conf = {'confname': sc.name, 'filename': vc.filename}
		url = reverse('MHLogin.DoctorCom.speech.views.get_voice_clip', kwargs=conf)
		path = "http://testserver" + url  # TODO: figure better way to get server name
		sig = encodestring(hmac.new(settings.TWILIO_ACCOUNT_TOKEN, path, sha1).digest()).strip()
		response = c.get(url, **{'HTTP_X_TWILIO_SIGNATURE': sig})
		# do more validation but check generally we OK and no exceptions
		self.assertTrue(response.status_code == 200)

	def test_util_tts(self):
		""" Test the speech view request using tts() """
		c = Client()
		tts_text = "Is the universe a holographic simulation?"
		retry = 5
		# sleep 3 seconds if max error (only for trial version) and retry up to 5 times
		while retry > 0:
			sayplay = tts(tts_text, SpeechConfig.objects.get_subclass(name=self.neo[0]))
			if not isinstance(sayplay, Play):
				time.sleep(3.0)
			else:
				break
			retry -= 1
		self.assertTrue(sayplay != None)
		self.assertIsInstance(sayplay, Play, sayplay.__class__)

		url_path = urlparse.urlsplit(sayplay.body).path.split('/')
		conf = {'confname': url_path[-3], 'filename': url_path[-2]}

		url = reverse('MHLogin.DoctorCom.speech.views.get_voice_clip', kwargs=conf)
		path = "http://testserver" + url  # TODO: figure better way to get server name
		sig = encodestring(hmac.new(settings.TWILIO_ACCOUNT_TOKEN, path, sha1).digest()).strip()
		response = c.get(url, **{'HTTP_X_TWILIO_SIGNATURE': sig})

		# do more validation but check generally we OK and no exceptions
		self.assertTrue(response.status_code == 200)

		# verify content disposition field set in view and filenames match
		filename = response['Content-Disposition'].split('=')[1]
		self.assertTrue(filename == conf['filename'], filename)

