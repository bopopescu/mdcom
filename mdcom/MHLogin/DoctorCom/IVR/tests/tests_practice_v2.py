
import hmac
import mock
import os

from hashlib import sha1
from base64 import encodestring
from django.conf import settings
from pytz import timezone
from datetime import datetime, timedelta
from .base import TestIVRBase
from MHLogin.MHLPractices.models import PracticeLocation, PracticeHours
from MHLogin.DoctorCom.IVR.models import callLog
from MHLogin.DoctorCom.IVR.views_generic_v2 import _getMHLUser
from MHLogin.MHLCallGroups.Scheduler.models import EventEntry
from MHLogin.KMS.utils import generate_keys_for_users

# helper to generate signature for twilio validation
generate_sig = lambda path: encodestring(hmac.new(
	settings.TWILIO_ACCOUNT_TOKEN, path, sha1).digest()).strip()


@mock.patch('MHLogin.DoctorCom.speech.utils.Play', autospec=True)
@mock.patch('MHLogin.DoctorCom.speech.utils.Say', autospec=True)
@mock.patch('MHLogin.DoctorCom.IVR.views_practice_v2.twilio', autospec=True)
@mock.patch('MHLogin.DoctorCom.IVR.views_generic_v2.twilio', autospec=True)
class TestIVRPracticeV2(TestIVRBase):

	def setUp(self):
		super(TestIVRPracticeV2, self).setUp()

	def tearDown(self):
		super(TestIVRPracticeV2, self).tearDown()

# PracticeIVR_Main test cases:
# 1. Setup practice (pin, name, open and close greeting)
# 2. forward call go to PracticeIVR_CallerResponse_New (old way & new way with specialties)
# 2a. ForwardCall (for Urgent Messages)
# 2b. LeaveUrgentMessage
# 2c. LeaveRegularMessage
# 3. Leave message when office is closed -> to provider?
#
# Test setup of Practice
#
	def test_PracticeIVR_Main_Setup(self, twiliog, twiliop, say, play):
		"""
		office manager caller calling main
		will go to setup since Practice voicemail is not set up
		"""
		url = '/IVR/PracticeV2/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14086661111',
			'To': '+14085551111',
			'CallStatus': 'ringing',
			'CallSid': '500',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		pcalls = [
			mock.call.Response(),
			mock.call.Pause(),
			mock.call.Response().append(twiliop.Pause()),
			mock.call.Response().append(say('Welcome to your voicemail account.\
It looks like some setup is needed. Let\'s get started. First, we need to set up your pin number.')),
			mock.call.Response().append(twiliog.Gather()),
			]
		twiliop.assert_has_calls(pcalls)
		gcalls = [
			mock.call.Gather(
				action='/IVR/ChangePinV2/1/',
				finishOnKey='#',
				numDigits=8),
			mock.call.Gather().append(say("Welcome to your voicemail account. ")),
			]
		twiliog.assert_has_calls(gcalls)
		assert self.client.session['ivr2_state'] == 'PracticeIVR_Setup_New'
		assert self.client.session['ivr2_sub_state'] == 'PracticeIVR_Setup_1'
		assert self.client.session['practice_id'] == self.practice.id

	def test_PracticeIVR_Main_Auth(self, twiliog, twiliop, say, play):
		"""
		office manager caller calling to practice with config complete
		go to authenticate/signin
		"""
		# caller is manager - practice.config_complete is true -> go to treeroot
		session = self.client.session
		session['practice_id'] = self.practice.id
		self.practice.config_complete = True
		self.practice.save()
		session.save()
		url = '/IVR/PracticeV2/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14086661111',
			'To': '+14085551111',
			'CallStatus': 'ringing',
			'CallSid': '501',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		pcalls = [
			mock.call.Response(),
			mock.call.Response().append(twiliog.Gather()),
			]
		twiliop.assert_has_calls(pcalls)
		gcalls = [
			mock.call.Gather(action='/IVR/SignInV2/', numDigits=8),
			mock.call.Gather().append(say(u'Please enter your pin number. Press pound to finish.')),
			]
		twiliog.assert_has_calls(gcalls)
		assert self.client.session['ivr2_state'] == 'PracticeIVR_TreeRoot_New'
		assert self.client.session['practice_id'] == self.practice.id
		assert self.client.session['practice_phone'] == self.practice.practice_phone

	def test_PracticeIVR_Main_TreeRoot(self, twiliog, twiliop, say, play):
		"""
		office manager caller calling to practice
		after authentication -> to TreeRoot
		"""
		# caller is manager - practice.config_complete is true -> go to treeroot
		session = self.client.session
		session['practice_id'] = self.practice.id
		self.practice.config_complete = True
		self.practice.save()
		session['authenticated'] = True
		session.save()
		url = '/IVR/PracticeV2/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14086661111',
			'To': '+14085551111',
			'CallStatus': 'inprogress',
			'CallSid': '502',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		pcalls = [
			mock.call.Response(),
			mock.call.Gather(finishOnKey='', timeout=30, numDigits=1),
			mock.call.Response().append(say(u'Wecome to you voice mail account. Your set up is complete. This account does not have mail box.')),
			mock.call.Gather().append(say(u'To manage your settings, press 3')),
			mock.call.Gather().append(say(u'To repeat this menu, press star')),
			mock.call.Response().append(twiliop.Gather(finishOnKey='', timeout=30, numDigits=1)),
			]
		twiliop.assert_has_calls(pcalls)
		gcalls = []
		twiliog.assert_has_calls(gcalls)
		assert self.client.session['ivr2_state'] == 'PracticeIVR_TreeRoot_New'
		assert self.client.session['practice_id'] == self.practice.id
		assert self.client.session['practice_phone'] == self.practice.practice_phone

	def test_PracticeIVR_Main_TreeRoot_Alt(self, twiliog, twiliop, say, play):
		"""
		PracticeIVR TreeRoot direct url request after authentication
		"""
		session = self.client.session
		session['practice_id'] = self.practice.id
		self.practice.config_complete = True
		self.practice.save()
		session['authenticated'] = True
		session['ivr2_state'] = 'PracticeIVR_TreeRoot_New'
		session.save()
		url = '/IVR/PracticeV2/TreeRoot/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14086661111',
			'To': '+14085551111',
			'CallStatus': 'inprogress',
			'CallSid': '503',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		pcalls = [
			mock.call.Response(),
			mock.call.Gather(finishOnKey='', timeout=30, numDigits=1),
			mock.call.Response().append(say(u'Welcome to your voicemail account. Your set up is complete. This account does not have mail box.')),
			mock.call.Gather().append(say(u'To manage your settings, press 3')),
			mock.call.Gather().append(say(u'To repeat this menu, press star')),
			mock.call.Response().append(twiliop.Gather(finishOnKey='', timeout=30, numDigits=1)),
			]
		twiliop.assert_has_calls(pcalls)
		gcalls = []
		twiliog.assert_has_calls(gcalls)
		# state unchanged
		assert self.client.session['ivr2_state'] == 'PracticeIVR_TreeRoot_New'

	def test_PracticeIVR_Main_Setup_0(self, twiliog, twiliop, say, play):
		"""
		PracticeIVR - office manager calling to start setup practice settings
		"""
		practice = self.practices[0]
		session = self.client.session
		session['practice_id'] = practice.id
		self.practice.config_complete = False
		self.practice.save()
		session['Caller'] = '4086661111'
		session['Called'] = '4085551111'
		session['ivr2_state'] = 'PracticeIVR_Setup_New'
		session['ivr2_sub_state'] = 'PracticeIVR_Setup_Start'
		session['authenticated'] = True
		session.save()
		url = '/IVR/PracticeV2/Setup/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14086661111',
			'To': '+14085551111',
			'CallStatus': 'inprogress',
			'CallSid': '504',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		pcalls = [
			mock.call.Response(),
			mock.call.Pause(),
			mock.call.Response().append(twiliop.Pause()),
			mock.call.Response().append(say('Welcome to your voicemail account.\
It looks like some setup is needed. Let\'s get started. First, we need to set up your pin number.')),
			mock.call.Response().append(twiliog.Gather()),
			]
		twiliop.assert_has_calls(pcalls)
		gcalls = [
			mock.call.Gather(action='/IVR/ChangePinV2/1/', finishOnKey='#', numDigits=8),
			mock.call.Gather().append(say('Please enter four to eight digits. Press pound to finish.')),
			]
		twiliog.assert_has_calls(gcalls)
		assert self.client.session['ivr2_sub_state'] == 'PracticeIVR_Setup_1'
		assert self.client.session['ivr2_state'] == 'PracticeIVR_Setup_New'

		practiceS = PracticeLocation.objects.filter(mdcom_phone='4085551111')
		practice = practiceS[0]
		assert self.client.session['practice_id'] == practice.id

	def test_PracticeIVR_Main_Setup_1(self, twiliog, twiliop, say, play):
		"""
		PracticeIVR Setup direct request
		office manager caller calling to setup office name
		"""
		practice = self.practices[0]
		session = self.client.session
		session['practice_id'] = practice.id
		practice.config_complete = False
		practice.save()
		session['ivr2_state'] = 'PracticeIVR_Setup_New'
		session['ivr2_sub_state'] = 'PracticeIVR_Setup_1'
		session['Caller'] = '4086661111'
		session['Called'] = '4085551111'
		session['ivr2_Record_recording'] = 'http://api.twilio.com/2010-04-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/RE8e3dfb46277add8bb0b381d087d9424d'
		session['authenticated'] = True
		session.save()
		url = '/IVR/PracticeV2/Setup/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14086661111',
			'To': '+14085551111',
			'CallStatus': 'inprogress',
			'CallSid': '505',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		pcalls = []
		twiliop.assert_has_calls(pcalls)
		gcalls = [
			mock.call.Response().append(say('Now, we need to record your office name.\
Please say your name after the tone. Press pound to finish.')),
			mock.call.Record(
				finishOnKey='1234567890*#', transcribe=False, playBeep=True,
				timeout=3, maxLength=10, action='/IVR/GetRecordingV2/1/'),
			mock.call.Response().append(twiliog.Record()),
			mock.call.Redirect('/IVR/GetRecordingV2/'),
			mock.call.Response().append(twiliog.Redirect()),
			]
		twiliog.assert_has_calls(gcalls)
		assert self.client.session['ivr2_sub_state'] == 'PracticeIVR_Setup_2'
		assert self.client.session['ivr2_state'] == 'PracticeIVR_Setup_New'
		practiceS = PracticeLocation.objects.filter(mdcom_phone='4085551111')
		practice = practiceS[0]
		assert self.client.session['practice_id'] == practice.id

	def test_PracticeIVR_Main_Setup_2(self, twiliog, twiliop, say, play):
		"""
		PracticeIVR Setup direct request
		office manager caller calling to setup closed office greeting
		"""
		practice = self.practices[0]
		session = self.client.session
		session['practice_id'] = practice.id
		practice.config_complete = False
		practice.save()
		session['Caller'] = '4086661111'
		session['Called'] = '4085551111'
		session['ivr2_state'] = 'PracticeIVR_Setup_New'
		session['ivr2_sub_state'] = 'PracticeIVR_Setup_2'
		session['ivr2_Record_recording'] = 'http://api.twilio.com/2010-04-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/RE8e3dfb46277add8bb0b381d087d9424d'
		session['authenticated'] = True
		session.save()
		url = '/IVR/PracticeV2/Setup/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14086661111',
			'To': '+14085551111',
			'CallStatus': 'inprogress',
			'CallSid': '506',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		pcalls = []
		twiliop.assert_has_calls(pcalls)
		gcalls = [
			mock.call.Response(),
			mock.call.Response().append(say(u'Next, we need to set up your answering service greeting. \
This will be played when the office is closed.Please say your new greeting after the tone. Press pound to finish.')),
			mock.call.Record(finishOnKey='1234567890*#', transcribe=False, playBeep=True,
				timeout=3, maxLength=120, action='/IVR/GetRecordingV2/1/'),
			mock.call.Response().append(twiliog.Record()),
			mock.call.Redirect('/IVR/GetRecordingV2/'),
			mock.call.Response().append(twiliog.Redirect()),
			]
		twiliog.assert_has_calls(gcalls)
		assert self.client.session['ivr2_sub_state'] == 'PracticeIVR_Setup_3'
		assert self.client.session['ivr2_state'] == 'PracticeIVR_Setup_New'
		practiceS = PracticeLocation.objects.filter(mdcom_phone='4085551111')
		practice = practiceS[0]
		assert self.client.session['practice_id'] == practice.id

	def test_PracticeIVR_Main_Setup_3(self, twiliog, twiliop, say, play):
		"""
		PracticeIVR Setup direct request
		office manager caller calling to setup open office greeting
		"""
		practice = self.practices[0]
		session = self.client.session
		session['practice_id'] = practice.id
		practice.config_complete = False
		practice.save()
		session['Caller'] = '4086661111'
		session['Called'] = '4085551111'
		session['ivr2_state'] = 'PracticeIVR_Setup_New'
		session['ivr2_sub_state'] = 'PracticeIVR_Setup_3'
		session['ivr2_Record_recording'] = 'http://api.twilio.com/2010-04-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/RE8e3dfb46277add8bb0b381d087d9424d'
		session['authenticated'] = True
		session.save()
		url = '/IVR/PracticeV2/Setup/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14086661111',
			'To': '+14085551111',
			'CallStatus': 'inprogress',
			'CallSid': '507',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		pcalls = []
		twiliop.assert_has_calls(pcalls)
		gcalls = [
			mock.call.Response(),
			mock.call.Response().append(say(u'Finally, we need to set up a greeting that will be played when the office is open.\
Please say your new greeting after the tone. Press pound to finish.')),
			mock.call.Record(finishOnKey='1234567890*#', transcribe=False, playBeep=True,
				timeout=3, maxLength=120, action='/IVR/GetRecordingV2/1/'),
			mock.call.Response().append(twiliog.Record()),
			mock.call.Redirect('/IVR/GetRecordingV2/'),
			mock.call.Response().append(twiliog.Redirect()),
			]
		twiliog.assert_has_calls(gcalls)
		assert self.client.session['ivr2_sub_state'] == 'PracticeIVR_Setup_4'
		assert self.client.session['ivr2_state'] == 'PracticeIVR_Setup_New'
		practiceS = PracticeLocation.objects.filter(mdcom_phone='4085551111')
		practice = practiceS[0]
		assert self.client.session['practice_id'] == practice.id

	def test_PracticeIVR_Setup_Complete(self, twiliog, twiliop, say, play):
		"""
		office manager caller calling to office # with office phone to set up practice
		last step - plus callback for callLog
		"""
		practice = self.practices[0]
		session = self.client.session
		session['practice_id'] = practice.id
		session['Caller'] = '4086661111'
		session['Called'] = '4085551111'
		session['ivr2_state'] = 'PracticeIVR_Setup_New'
		session['ivr2_sub_state'] = 'PracticeIVR_Setup_4'
		session['ivr2_Record_recording'] = 'http://api.twilio.com/2010-04-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/RE8e3dfb46277add8bb0b381d087d9424d'
		session.save()
		caller_mhluser = _getMHLUser('4086661111')
		log = callLog(callSID='500', caller_number='4086661111', called_number='4085551111',
			call_source='OC')
		log.save()
		url = '/IVR/PracticeV2/Setup/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14086661111',
			'To': '+14085551111',
			'CallStatus': 'ringing',
			'CallSid': '500',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		pcalls = [
			mock.call.Response(),
			mock.call.Response().append(say(u'Your voice mail account is now set up. You may hang up now.')),
			mock.call.Redirect('/IVR/PracticeV2/TreeRoot/'),
			mock.call.Response().append(twiliop.Redirect()),
		]
		twiliop.assert_has_calls(pcalls)
		gcalls = []
		twiliog.assert_has_calls(gcalls)
		practiceS = PracticeLocation.objects.filter(mdcom_phone='4085551111')
		practice = practiceS[0]
		assert self.client.session['ivr2_state'] == 'PracticeIVR_TreeRoot_New'
		assert 'ivr2_sub_state' not in self.client.session
		assert self.client.session['practice_id'] == self.practice.id
		assert practice.config_complete is True
		# callback to complete call log
		url = '/IVR/PracticeV2/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14086661111',
			'To': '+14085551111',
			'CallStatus': 'completed',
			'CallSid': '500',
			'CallDuration': '199',
			'Duration': '2'
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		log_qs = callLog.objects.filter(callSID='500')
		if (log_qs.count()):
			log = log_qs.get()
			self.assertEqual(log.call_duration, 199)

#
# TreeRoot Options
#

	def test_PracticeIVR_Main_Tree_Options(self, twiliog, twiliop, say, play):
		"""
		PracticeIVR main -- To TreeRoot to Options (office manager calling office)
		"""
		# caller is manager - practice.config_complete is true -> go to treeroot options
		session = self.client.session
		session['practice_id'] = self.practice.id
		self.practice.config_complete = True
		self.practice.save()
		session['authenticated'] = True
		session.save()
		url = '/IVR/PracticeV2/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14086661111',
			'To': '+14085551111',
			'CallStatus': 'inprogress',
			'CallSid': '510',
			'Digits': '3',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		pcalls = [
			mock.call.Response(),
			mock.call.Gather(action='/IVR/PracticeV2/Options/1/', finishOnKey='', numDigits=1),
			mock.call.Gather().append(say('Options menu')),
			mock.call.Gather().append(say('To re-record your name, press 1')),
			mock.call.Gather().append(say('To record a new closed office greeting, press 3')),
			mock.call.Gather().append(say('To record a new greeting while the office is open, press 5')),
			mock.call.Gather().append(say('To change your pin, press 7')),
			mock.call.Gather().append(say('To return to the main menu, press 9')),
			mock.call.Gather().append(say('To repeat this menu, press star')),
			mock.call.Response().append(twiliop.Gather(action='/IVR/PracticeV2/Options/1/', finishOnKey='', numDigits=1)),
			]
		twiliop.assert_has_calls(pcalls)
		gcalls = []
		twiliog.assert_has_calls(gcalls)
		assert self.client.session['ivr2_state'] == 'PracticeIVR_Options_New'
		assert self.client.session['practice_id'] == self.practice.id

	def test_PracticeIVR_Main_Options_1(self, twiliog, twiliop, say, play):
		"""
		office manager to Options Actions
		with digit 1 - change name
		"""
		# caller is manager - go to options with Digit 1 change Name
		session = self.client.session
		session['practice_id'] = self.practice.id
		self.practice.config_complete = True
		self.practice.save()
		session['authenticated'] = True
		session['ivr2_state'] = 'PracticeIVR_Options_New'
		session.save()
		url = '/IVR/PracticeV2/Options/1/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14086661111',
			'To': '+14085551111',
			'CallStatus': 'inprogress',
			'CallSid': '511',
			'Digits': '1',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		pcalls = []
		twiliop.assert_has_calls(pcalls)
		gcalls = [
			mock.call.Response(),
			mock.call.Response().append(say('Please say your name after the tone. Press pound to finish.')),
			mock.call.Record(
				finishOnKey='1234567890*#', transcribe=False, playBeep=True,
				timeout=3, maxLength=10, action='/IVR/GetRecordingV2/1/'),
			mock.call.Response().append(twiliog.Record()),
			mock.call.Redirect('/IVR/GetRecordingV2/'),
			mock.call.Response().append(twiliog.Redirect()),
			]
		twiliog.assert_has_calls(gcalls)
		assert self.client.session['ivr2_sub_state'] == 'PracticeIVR_Options_1'
		assert self.client.session['ivr2_state'] == 'PracticeIVR_Options_New'
		assert self.client.session['practice_id'] == self.practice.id

	def test_PracticeIVR_Main_Options_3(self, twiliog, twiliop, say, play):
		"""
		office manager to Options Actions
		with digit 3 - change greeting (closed office)
		"""
		session = self.client.session
		session['practice_id'] = self.practice.id
		self.practice.config_complete = True
		self.practice.save()
		session['authenticated'] = True
		session['ivr2_state'] = 'PracticeIVR_Options_New'
		session.save()
		url = '/IVR/PracticeV2/Options/1/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14086661111',
			'To': '+14085551111',
			'CallStatus': 'inprogress',
			'CallSid': '512',
			'Digits': '3',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		pcalls = []
		twiliop.assert_has_calls(pcalls)
		gcalls = [
			mock.call.Response(),
			mock.call.Response().append(say('Please say your new greeting after the tone. Press pound to finish.')),
			mock.call.Record(
				finishOnKey='1234567890*#', transcribe=False, playBeep=True, 
				timeout=3, maxLength=120, action='/IVR/GetRecordingV2/1/'),
			mock.call.Response().append(twiliog.Record()),
			mock.call.Redirect('/IVR/GetRecordingV2/'),
			mock.call.Response().append(twiliog.Redirect()),
			]
		twiliog.assert_has_calls(gcalls)
		assert self.client.session['ivr2_state'] == 'PracticeIVR_Options_New'
		assert self.client.session['ivr2_sub_state'] == 'PracticeIVR_Options_2'
		assert self.client.session['practice_id'] == self.practice.id

	def test_PracticeIVR_Main_Options_5(self, twiliog, twiliop, say, play):
		"""
		office manager to Options Actions
		with digit 5 - change greeting (open office = lunch)
		"""
		session = self.client.session
		session['practice_id'] = self.practice.id
		self.practice.config_complete = True
		self.practice.save()
		session['authenticated'] = True
		session['ivr2_state'] = 'PracticeIVR_Options_New'
		session.save()
		url = '/IVR/PracticeV2/Options/1/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14086661111',
			'To': '+14085551111',
			'CallStatus': 'inprogress',
			'CallSid': '513',
			'Digits': '5',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		pcalls = []
		twiliop.assert_has_calls(pcalls)
		gcalls = [
			mock.call.Response(),
			mock.call.Response().append(say('Please say your new greeting after the tone. Press pound to finish.')),
			mock.call.Record(
				finishOnKey='1234567890*#', transcribe=False, playBeep=True,
				timeout=3, maxLength=120, action='/IVR/GetRecordingV2/1/'),
			mock.call.Response().append(twiliog.Record()),
			mock.call.Redirect('/IVR/GetRecordingV2/'),
			mock.call.Response().append(twiliog.Redirect()),
			]
		twiliog.assert_has_calls(gcalls)
		assert self.client.session['ivr2_state'] == 'PracticeIVR_Options_New'
		assert self.client.session['ivr2_sub_state'] == 'PracticeIVR_Options_3'
		assert self.client.session['practice_id'] == self.practice.id

	def test_PracticeIVR_Main_Options_7(self, twiliog, twiliop, say, play):
		"""
		office manager to Options Actions
		with digit 7 - change pin
		"""
		session = self.client.session
		session['practice_id'] = self.practice.id
		self.practice.config_complete = True
		self.practice.save()
		session['authenticated'] = True
		session['ivr2_state'] = 'PracticeIVR_Options_New'
		session.save()
		url = '/IVR/PracticeV2/Options/1/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14086661111',
			'To': '+14085551111',
			'CallStatus': 'inprogress',
			'CallSid': '514',
			'Digits': '7',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		pcalls = []
		twiliop.assert_has_calls(pcalls)
		gcalls = [
			mock.call.Response(),
			mock.call.Gather(action='/IVR/ChangePinV2/1/', finishOnKey='#', numDigits=8),
			mock.call.Gather().append(say('Please enter four to eight digits. Press pound to finish.')),
			mock.call.Response().append(twiliog.Gather()),
			]
		twiliog.assert_has_calls(gcalls)
		assert self.client.session['ivr2_state'] == 'PracticeIVR_Options_New'
		assert self.client.session['ivr2_sub_state'] == 'PracticeIVR_Options_4'
		assert self.client.session['practice_id'] == self.practice.id

	def test_PracticeIVR_Main_Options_9(self, twiliog, twiliop, say, play):
		"""
		office manager to Options Actions
		with digit 9 - back to Main Menu of TreeRoot
		"""
		session = self.client.session
		session['practice_id'] = self.practice.id
		self.practice.config_complete = True
		self.practice.save()
		session['authenticated'] = True
		session['ivr2_state'] = 'PracticeIVR_Options_New'
		session.save()
		url = '/IVR/PracticeV2/Options/1/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14086661111',
			'To': '+14085551111',
			'CallStatus': 'inprogress',
			'CallSid': '514',
			'Digits': '9',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		pcalls = [
			mock.call.Response(),
			mock.call.Redirect('/IVR/PracticeV2/TreeRoot/'),
			mock.call.Response().append(twiliop.Redirect('/IVR/PracticeV2/TreeRoot/')),
			]
		twiliop.assert_has_calls(pcalls)
		gcalls = []
		twiliog.assert_has_calls(gcalls)
		assert self.client.session['ivr2_state'] == 'PracticeIVR_TreeRoot_New'
		assert self.client.session['practice_id'] == self.practice.id

	def test_PracticeIVR_Main_Options_star(self, twiliog, twiliop, say, play):
		"""
		office manager to Options Actions
		with digit * - Repeat options
		"""
		# caller is manager - go to options with Digit 9 - Main menu
		session = self.client.session
		session['practice_id'] = self.practice.id
		self.practice.config_complete = True
		self.practice.save()
		session['ivr2_state'] = 'PracticeIVR_Options_New'
		session['authenticated'] = True
		session.save()
		url = '/IVR/PracticeV2/Options/1/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14086661111',
			'To': '+14085551111',
			'CallStatus': 'inprogress',
			'CallSid': '514',
			'Digits': '*',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		pcalls = [
			mock.call.Response(),
			mock.call.Gather(action='/IVR/PracticeV2/Options/1/', finishOnKey='', numDigits=1),
			mock.call.Gather().append(say(u'Options menu')),
			mock.call.Gather().append(say(u'To re-record your name, press 1')),
			mock.call.Gather().append(say(u'To record a new closed office greeting, press 3')),
			mock.call.Gather().append(say(u'To record a new greeting while the office is open, press 5')),
			mock.call.Gather().append(say(u'To change your pin, press 7')),
			mock.call.Gather().append(say(u'To return to the main menu, press 9')),
			mock.call.Gather().append(say(u'To repeat this menu, press star')),
			mock.call.Response().append(twiliop.Gather(action='/IVR/PracticeV2/Options/1/', finishOnKey='', numDigits=1)),
			]
		twiliop.assert_has_calls(pcalls)
		gcalls = []
		twiliog.assert_has_calls(gcalls)
		# ivr2_state is unchanged
		assert self.client.session['ivr2_state'] == 'PracticeIVR_Options_New'

	def test_PracticeIVR_Main_Options_bad1(self, twiliog, twiliop, say, play):
		"""
		office manager to Options Actions
		with digit * - Repeat options
		"""
		# caller is manager - go to options with Digit 9 - Main menu
		session = self.client.session
		session['practice_id'] = self.practice.id
		self.practice.config_complete = True
		self.practice.save()
		session['ivr2_state'] = 'PracticeIVR_Options_New'
		session['authenticated'] = True
		session.save()
		url = '/IVR/PracticeV2/Options/1/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14086661111',
			'To': '+14085551111',
			'CallStatus': 'inprogress',
			'CallSid': '514',
			'Digits': '2',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		pcalls = [
			mock.call.Response(),
			mock.call.Response().append(say('I\'m sorry, that wasn\'t a valid selection.')),
			mock.call.Gather(action='/IVR/PracticeV2/Options/1/', finishOnKey='', numDigits=1),
			mock.call.Gather().append(say(u'Options menu')),
			mock.call.Gather().append(say(u'To re-record your name, press 1')),
			mock.call.Gather().append(say(u'To record a new closed office greeting, press 3')),
			mock.call.Gather().append(say(u'To record a new greeting while the office is open, press 5')),
			mock.call.Gather().append(say(u'To change your pin, press 7')),
			mock.call.Gather().append(say(u'To return to the main menu, press 9')),
			mock.call.Gather().append(say(u'To repeat this menu, press star')),
			mock.call.Response().append(twiliop.Gather(action='/IVR/PracticeV2/Options/1/', finishOnKey='', numDigits=1)),
			]
		twiliop.assert_has_calls(pcalls)
		gcalls = []
		twiliog.assert_has_calls(gcalls)
		# ivr2_state is unchanged
		assert self.client.session['ivr2_state'] == 'PracticeIVR_Options_New'

	def test_PracticeIVR_Main_Options_bad2(self, twiliog, twiliop, say, play):
		"""
		office manager to Options Actions
		with digit * - Repeat options
		"""
		# caller is manager - go to options with Digit 9 - Main menu
		session = self.client.session
		session['practice_id'] = self.practice.id
		self.practice.config_complete = True
		self.practice.save()
		session['ivr2_state'] = 'PracticeIVR_Options_New'
		session['authenticated'] = True
		session.save()
		url = '/IVR/PracticeV2/Options/1/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14086661111',
			'To': '+14085551111',
			'CallStatus': 'inprogress',
			'CallSid': '514',
			'Digits': '99',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		pcalls = [
			mock.call.Response(),
			mock.call.Response().append(say('I\'m sorry, I didn\'t understand that.')),
			mock.call.Gather(action='/IVR/PracticeV2/Options/1/', finishOnKey='', numDigits=1),
			mock.call.Gather().append(say(u'Options menu')),
			mock.call.Gather().append(say(u'To re-record your name, press 1')),
			mock.call.Gather().append(say(u'To record a new closed office greeting, press 3')),
			mock.call.Gather().append(say(u'To record a new greeting while the office is open, press 5')),
			mock.call.Gather().append(say(u'To change your pin, press 7')),
			mock.call.Gather().append(say(u'To return to the main menu, press 9')),
			mock.call.Gather().append(say(u'To repeat this menu, press star')),
			mock.call.Response().append(twiliop.Gather(action='/IVR/PracticeV2/Options/1/', finishOnKey='', numDigits=1)),
			]
		twiliop.assert_has_calls(pcalls)
		gcalls = []
		twiliog.assert_has_calls(gcalls)
		# ivr2_state is unchanged
		assert self.client.session['ivr2_state'] == 'PracticeIVR_Options_New'

#
# Test Handling CallerResponse
#
	def test_PracticeIVR_Main_CallerResponse_1(self, twiliog, twiliop, say, play):
		"""
		Outside caller calling practice (practice has single call group - old way)
		play closed greeting
		"""
		self.practice.greeting_closed = 'http://api.twilio.com/2010-04-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/RE8e3dfb46277add8bb0b381d087d9424d'
		self.practice.save()
		url = '/IVR/PracticeV2/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14081234567',
			'To': '+14085551111',
			'CallStatus': 'ringing',
			'CallSid': '600',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		pcalls = [
			mock.call.Response(),
			mock.call.Gather(action='/IVR/PracticeV2/CallerResponse/1/',
				finishOnKey='', timeout=60, numDigits=1),
			mock.call.Play('http://api.twilio.com/2010-04-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/RE8e3dfb46277add8bb0b381d087d9424d'),
			mock.call.Gather().append(twiliop.Play('')),
			mock.call.Response().append(twiliop.Gather()),
			]
		twiliop.assert_has_calls(pcalls)
		gcalls = []
		twiliog.assert_has_calls(gcalls)
		assert self.client.session['ivr2_state'] == 'PracticeIVR_CallerResponse_New'

	def test_PracticeIVR_Main_CallerResponse_2(self, twiliog, twiliop, say, play):
		"""
		Outside caller calling practice (practice has 1 call group no specialty - new way)
		play dynamically created greeting
		"""
		url = '/IVR/PracticeV2/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14081234567',
			'To': '+14085552222',
			'CallStatus': 'ringing',
			'CallSid': '601',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		pcalls = [
			mock.call.Response(),
			mock.call.Gather(action='/IVR/PracticeV2/CallerResponse/1/',
				finishOnKey='', timeout=60, numDigits=1),
			mock.call.Play(''),
			mock.call.Gather().append(twiliop.Play('')),
			mock.call.Gather().append(say('To leave non urgent message for staff press 1.          To reach doctor on call press 2.')),
			mock.call.Response().append(twiliop.Gather()),
			]
		twiliop.assert_has_calls(pcalls)
		gcalls = []
		twiliog.assert_has_calls(gcalls)
		assert self.client.session['ivr2_state'] == 'PracticeIVR_CallerResponse_New'

	def test_PracticeIVR_Main_CallerResponse_3(self, twiliog, twiliop, say, play):
		"""
		Outside caller calling practice (practice has >1 call group + specialty - new way)
		play dynamically created greeting incl specialty
		"""
		# outside caller calling new practice with >1 call_groups + specialty; new way
		url = '/IVR/PracticeV2/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14081234567',
			'To': '+14085553333',
			'CallStatus': 'ringing',
			'CallSid': '602',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		pcalls = [
			mock.call.Response(),
			mock.call.Gather(action='/IVR/PracticeV2/CallerResponse/1/',
				finishOnKey='', timeout=60, numDigits=1),
			mock.call.Play(''),
			mock.call.Gather().append(twiliop.Play('')),
			mock.call.Gather().append(say('To leave non urgent message for staff press 1.\
          To reach the on call Cardiology doctor. For Team C press 3.\
     To reach the on call ENT doctor. For Team D press 4.     .')),
			mock.call.Response().append(twiliop.Gather()),
			]
		twiliop.assert_has_calls(pcalls)
		gcalls = []
		twiliog.assert_has_calls(gcalls)
		assert self.client.session['ivr2_state'] == 'PracticeIVR_CallerResponse_New'

	def test_PracticeIVR_Main_CallerResponse_2_Open(self, twiliog, twiliop, say, play):
		"""
		Outside caller calling practice - skip_to_rmsg and is_open is true
		setup PracticeHours to make it so
		"""
		with mock.patch('MHLogin.MHLPractices.models.PracticeLocation.is_open', 
					return_value=True):
			nowtime = datetime.now()
			startDate = nowtime + timedelta(days=-1)
			endDate = nowtime + timedelta(days=1)
			# ok,  need to actually set these to be sure the office is OPEN!
			td = timedelta(0, 3600, 0)
			startTime = (nowtime - td).time()
			endTime = (nowtime + td).time()
			lunchTime = endTime
			dayofweek = int(datetime.today().weekday())
			practiceOpen = PracticeHours(practice_location=self.practice1, day_of_week=(dayofweek+1),
				open= startTime, close=endTime, lunch_start=lunchTime, lunch_duration=60)
			event = EventEntry(creator=self.providers[0],
							oncallPerson=self.providers[0],
							callGroup=self.callgroup2,
							startDate=startDate,
							endDate=endDate,
							title='test event',
							oncallLevel='0',
							eventStatus=1,
							checkString='abc'
							)
			event.save()
			practiceOpen.save()
			self.practice1.skip_to_rmsg = True
			self.practice1.save()
			# want to make sure practice is open
			url = '/IVR/PracticeV2/'
			path = 'http://testserver' + url
			post_vars = {
				'From': '+14081234567',
				'To': '+14085552222',
				'CallStatus': 'ringing',
				'CallSid': '610',
				}
			for k, v in sorted(post_vars.items()):
				path += (k + v)
			response = self.client.post(url, post_vars,
				**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
			self.assertEqual(response.status_code, 200)
			self.assertEqual(self.practice1.is_open(), True)
			pcalls = [
				mock.call.Response(),
				mock.call.Gather(action='/IVR/PracticeV2/CallerResponse/1/',
					finishOnKey='', timeout=60, numDigits=1),
				mock.call.Play(''),
				mock.call.Response().append(twiliop.Play('')),
				mock.call.Redirect('/IVR/PracticeV2/LeaveTextMsg/'),
				mock.call.Response().append(twiliop.Redirect()),
				]
			twiliop.assert_has_calls(pcalls)
			gcalls = []
			twiliog.assert_has_calls(gcalls)
			assert self.client.session['ivr2_state'] == 'PracticeIVR_LeaveRegularMsg_New'

	def test_PracticeIVR_Main_CallerResponse_2_LeaveMsg_1(self, twiliog, twiliop, say, play):
		"""
		Outside caller calling practice with callgroups no specialty to leaveRegularMessage
		"""
		gmttz = timezone('GMT')
		mytz = timezone(self.practice.time_zone)
		calltime_gmt = datetime.now(gmttz)
		calltime_local = calltime_gmt.astimezone(mytz)
		session = self.client.session
		session['calltime_local_string'] = calltime_local.strftime("%Y-%m-%d %H:%M:%S")
		session['calltime_local'] = calltime_local
		session['practice_id'] = self.practice1.id
		session['ivr2_state'] = 'PracticeIVR_CallerResponse_New'
		# these are from create_dynamic_greeting
		session['call_groups_map'] = {'2': 2}
		session['specialties_map'] = {}
		session['one_ok'] = '1'
		session['ivr2_provider_onCall'] = self.providers[0].id
#		session['callgroup_id'] = self.practice1.call_group.id
		session.save()
		url = '/IVR/PracticeV2/CallerResponse/1/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14081234567',
			'To': '+14085552222',
			'CallStatus': 'inprogress',
			'Digits': '1',
			'CallSid': '611',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		pcalls = [
			mock.call.Response(),
			]
		twiliop.assert_has_calls(pcalls)
		gcalls = [
			mock.call.Response(),
			mock.call.Gather(action='/IVR/GetCallBackNumberV2/1/',
				finishOnKey='#', timeout=30, numDigits=12),
			mock.call.Gather().append(say('Please enter your callback number')),
			mock.call.Response().append(twiliog.Gather()),
			mock.call.Redirect('/IVR/GetCallBackNumberV2/1/'),
			mock.call.Response().append(twiliog.Redirect()),
			]
		twiliog.assert_has_calls(gcalls)
		assert self.client.session['ivr2_state'] == 'PracticeIVR_LeaveRegularMsg_New'
		assert self.client.session['ivr2_sub_state'] == 'PracticeIVR_LeaveRegularMsg_GetCallback'

	def test_PracticeIVR_Main_CallerResponse_2_ForwardCall_1(self, twiliog, twiliop, say, play):
		"""
		Outside caller calling practice with callgroups no specialty to
		forward call to provider
		main->callerResponse->LeaveUrgentMsg->ForwardCall
		"""
		# TODO - need to set up provider on call so this won't crash
		gmttz = timezone('GMT')
		mytz = timezone(self.practice.time_zone)
		calltime_gmt = datetime.now(gmttz)
		calltime_local = calltime_gmt.astimezone(mytz)
		session = self.client.session
		session['calltime_local_string'] = calltime_local.strftime("%Y-%m-%d %H:%M:%S")
		session['calltime_local'] = calltime_local
		session['practice_id'] = self.practice1.id
		session['ivr2_state'] = 'PracticeIVR_CallerResponse_New'
		my_call_groups = self.practice1.call_groups.all()
		session['callgroup_id'] = my_call_groups[0]
		# these are from create_dynamic_greeting
		session['call_groups_map'] = {'2': 2}
		session['specialties_map'] = {}
		session['one_ok'] = '1'
		session['ivr2_provider_onCall'] = self.providers[0].id
		session.save()
		url = '/IVR/PracticeV2/CallerResponse/1/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14081234567',
			'To': '+14085552222',
			'CallStatus': 'inprogress',
			'Digits': '2',
			'CallSid': '612',
			}
		log = callLog(
			caller_number='4081234567',
			called_number='4085552222',
			callSID='612',
			call_source='OC',
			mdcom_called=self.practice1)
		log.save()
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		pcalls = [
			mock.call.Response(),
#			mock.call.Play('get callback number'),
#			mock.call.Gather(finishOnKey='', timeout=60, numDigits=1),
			]
		twiliop.assert_has_calls(pcalls)
		gcalls = [
			mock.call.Response(),
			mock.call.Gather(action='/IVR/GetCallBackNumberV2/1/',
				finishOnKey='#', timeout=30, numDigits=12),
			mock.call.Gather().append(say('Please enter your callback number')),
			mock.call.Response().append(twiliog.Gather()),
			mock.call.Redirect('/IVR/GetCallBackNumberV2/1/'),
			mock.call.Response().append(twiliog.Redirect())
			]
		twiliog.assert_has_calls(gcalls)
		assert self.client.session['ivr2_state'] == 'PracticeIVR_LeaveUrgentMsg_New'
		assert self.client.session['ivr2_sub_state'] == 'PracticeIVR_LeaveUrgentMsg_GetCallback'

	def test_getCallBackNumber_completed(self, twiliog, twiliop, say, play):
		"""
		practice get callback number completion step
		"""
		url = '/IVR/GetCallBackNumberV2/1/'
		path = 'http://testserver' + url
		post_vars = {
			'CallStatus': 'completed',
			'CallSid': '1301',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)

		session = self.client.session
		session['practice_id'] = self.practice.id
		session['answering_service'] = 'yes'
		session['ivr2_Record_callbacknumber'] = '4081239999'
		session['ivr2_returnOnHangup'] = 'MHLogin.DoctorCom.IVR.views_practice_v2.PracticeIVR_LeaveRegularMsg_New'
		session['ivr2_state'] = 'PracticeIVR_LeaveRegularMsg_New'
		session['ivr2_sub_state'] = 'PracticeIVR_LeaveRegularMsg_GetCallback'
		session['ivr2_callback_step'] = 3
		session.save()
		generate_keys_for_users(open(os.devnull, 'w'))
		# get practice office managers
#		mgrs = get_all_practice_managers(session['practice_id'])
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		gcalls = [
			mock.call.Response(),
 			mock.call.Redirect('/IVR/PracticeV2/LeaveTextMsg/'),
 			mock.call.Response().append(twiliog.Redirect()),
			]
		twiliog.assert_has_calls(gcalls)
		pcalls = [
			mock.call.Response(),
			mock.call.Response().append(say('your message has been sent')),
			mock.call.Hangup(),
			mock.call.Response().append(twiliop.Hangup()),
			]
		twiliop.assert_has_calls(pcalls)
#		assert self.client.session['ivr2_callback_step'] == 1
		assert self.client.session['ivr2_state'] == 'PracticeIVR_LeaveRegularMsg_New'
		assert ('ivr2_sub_state' not in self.client.session)


#	def test_PracticeIVR_ForwardCall_New(self, twilio, say, play):
#		pass
