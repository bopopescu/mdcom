
import os
import hmac
import mock

from hashlib import sha1
from base64 import encodestring
from django.conf import settings
from .base import TestIVRBase

from MHLogin.DoctorCom.IVR.models import VMBox_Config, callLog
from MHLogin.DoctorCom.IVR.views_provider_v2 import _getProviderVMConfig
from MHLogin.DoctorCom.IVR.views_generic_v2 import _getMHLUser
from MHLogin.MHLPractices.models import PracticeLocation
from MHLogin.KMS.utils import generate_keys_for_users
from MHLogin.KMS.models import RSAKeyPair, RSAPubKey, IVR_RSAKeyPair, IVR_RSAPubKey

generate_sig = lambda path: encodestring(hmac.new(
	settings.TWILIO_ACCOUNT_TOKEN, path, sha1).digest()).strip()


@mock.patch('MHLogin.DoctorCom.speech.utils.Play', autospec=True)
@mock.patch('MHLogin.DoctorCom.speech.utils.Say', autospec=True)
@mock.patch('MHLogin.DoctorCom.IVR.views_generic_v2.twilio', autospec=True)
class TestIVRGenericV2(TestIVRBase):

	def setUp(self):
		super(TestIVRGenericV2, self).setUp()

	def tearDown(self):
		super(TestIVRGenericV2, self).tearDown()

	#
	# test authenticate/sign in
	#
	def test_authenticateSession_Provider(self, twilio, say, play):
		"""
		provider sign in - initial
		"""
		provider = self.providers[0]
		config = _getProviderVMConfig(provider)
		config.pin = 'sha1$52958$8d282c07727dece284f4bed71a94cc469e1c9418'
		config.save()
		session = self.client.session
		session['provider_id'] = provider.id
		session['config_id'] = config.id
		session['ivr2_state'] = 'ProviderIVR_Main_New'
		session.save()
		url = '/IVR/SignInV2/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085551234',
			'To': '+18004664411',
			'CallStatus': 'inprogress',
			'CallSid': '1190',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		calls = [
			mock.call.Response(),
			mock.call.Gather(action='/IVR/SignInV2/', numDigits=8),
			mock.call.Gather().append(say('Please enter your pin and press #')),
			mock.call.Response().append(twilio.Gather())
			]
		twilio.assert_has_calls(calls)
		assert (not 'authenticated' in self.client.session or self.client.session['authenticated'] == False)

	def test_authenticateSession_Provider_1(self, twilio, say, play):
		"""
		provider sign in - with correct pin entered
		"""
		generate_keys_for_users(open(os.devnull, 'w'))
		provider = self.providers[0]
		config = _getProviderVMConfig(provider)
		config.set_pin('1234')
		config.save()
		session = self.client.session
		session['provider_id'] = provider.id
		session['config_id'] = config.id
		session['ivr2_state'] = 'ProviderIVR_Main_New'
		session.save()
		url = '/IVR/SignInV2/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085551234',
			'To': '+18004664411',
			'CallStatus': 'inprogress',
			'CallSid': '1191',
			'Digits': '1234',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		calls = [
			mock.call.Response(),
			mock.call.Redirect('/IVR/ProviderV2/'),
			mock.call.Response().append(twilio.Redirect()),
			]
		twilio.assert_has_calls(calls)
		assert self.client.session['authenticated'] == True
		self.cleanup_rsa()

	def test_authenticateSession_Provider_2(self, twilio, say, play):
		"""
		test provider signin - incorrect pin entered
		"""
		provider = self.providers[0]
		config = _getProviderVMConfig(provider)
		config.pin = 'sha1$52958$8d282c07727dece284f4bed71a94cc469e1c9418'
		config.save()
		session = self.client.session
		session['provider_id'] = provider.id
		session['config_id'] = config.id
		session['ivr2_state'] = 'ProviderIVR_Main_New'
		session.save()
		url = '/IVR/SignInV2/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085551234',
			'To': '+18004664411',
			'CallStatus': 'inprogress',
			'CallSid': '1192',
			'Digits': '1111',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		calls = [
			mock.call.Response(),
			mock.call.Response().append(say('An in valid pin was entered')),
			mock.call.Gather(action='/IVR/SignInV2/', numDigits=8),
			mock.call.Gather().append(say('Please enter your 4-8 digit pin; press pound to finish')),
			mock.call.Response().append(twilio.Gather())
			]
		twilio.assert_has_calls(calls)
		assert (not 'authenticated' in self.client.session or self.client.session['authenticated'] == False)
		assert self.client.session['pin2_errCount'] == 1

	def test_authenticateSession_Provider_3(self, twilio, say, play):
		"""
		provider sign in - bad pin entered 3rd time
		"""
		provider = self.providers[0]
		config = _getProviderVMConfig(provider)
		config.pin = 'sha1$52958$8d282c07727dece284f4bed71a94cc469e1c9418'
		config.save()
		session = self.client.session
#		generate_keys_for_users()
		session['provider_id'] = provider.id
		session['config_id'] = config.id
		session['pin2_errCount'] = 2
		session['ivr2_state'] = 'ProviderIVR_Main_New'
		session.save()
		url = '/IVR/SignInV2/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085551234',
			'To': '+18004664411',
			'CallStatus': 'inprogress',
			'CallSid': '1193',
			'Digits': '1000',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		calls = [
			mock.call.Response(),
			mock.call.Response().append(say('An in valid pin was entered')),
			mock.call.Response().append(say('good bye')),
			mock.call.Hangup(),
			mock.call.Response().append(twilio.Hangup())
			]
		twilio.assert_has_calls(calls)
		assert (not 'authenticated' in self.client.session or self.client.session['authenticated'] == False)
		assert self.client.session['pin2_errCount'] == 3

	def test_authenticateSession_Practice(self, twilio, say, play):
		"""
		test practice sign in - start
		"""
		session = self.client.session
		session['practice_id'] = self.practice.id
		self.practice.set_pin('1234')
		self.practice.save()
		session['answering_service'] = 'yes'
		session['ivr2_state'] = 'PracticeIVR_Main_New'
		session.save()
		url = '/IVR/SignInV2/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085551234',
			'To': '+18004664411',
			'CallStatus': 'inprogress',
			'CallSid': '1190',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		calls = [
			mock.call.Response(),
			mock.call.Gather(action='/IVR/SignInV2/', numDigits=8),
			mock.call.Gather().append(say('Please enter your pin and press #')),
			mock.call.Response().append(twilio.Gather())
			]
		twilio.assert_has_calls(calls)
		assert (not 'authenticated' in self.client.session or self.client.session['authenticated'] == False)

	def test_authenticateSession_Practice_1(self, twilio, say, play):
		"""
		test practice sign in - correct pin entered
		"""
		session = self.client.session
		session['practice_id'] = self.practice.id
		self.practice.set_pin('1234')
		self.practice.save()
		session['answering_service'] = 'yes'
		session['ivr2_state'] = 'PracticeIVR_Main_New'
		session.save()
		url = '/IVR/SignInV2/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085551234',
			'To': '+18004664411',
			'CallStatus': 'inprogress',
			'CallSid': '1190',
			'Digits': '1234',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		calls = [
			mock.call.Response(),
			mock.call.Redirect('/IVR/PracticeV2/'),
			mock.call.Response().append(twilio.Redirect())
			]
		twilio.assert_has_calls(calls)
		assert self.client.session['authenticated'] == True
		assert self.client.session['pin2_errCount'] == 0

	def test_authenticateSession_Practice_2(self, twilio, say, play):
		"""
		test practice sign in - bad pin entered
		"""
		session = self.client.session
		session['practice_id'] = self.practice.id
		self.practice.set_pin('1234')
		self.practice.save()
		session['answering_service'] = 'yes'
		session['ivr2_state'] = 'PracticeIVR_Main_New'
		session.save()
		url = '/IVR/SignInV2/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085551234',
			'To': '+18004664411',
			'CallStatus': 'inprogress',
			'CallSid': '1190',
			'Digits': '1999',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		calls = [
			mock.call.Response(),
			mock.call.Response().append(say('An in valid pin was entered')),
			mock.call.Gather(action='/IVR/SignInV2/', numDigits=8),
			mock.call.Gather().append(say('Please enter your 4-8 digit pin; press pound to finish')),
			mock.call.Response().append(twilio.Gather())
			]
		twilio.assert_has_calls(calls)
		assert (not 'authenticated' in self.client.session or self.client.session['authenticated'] == False)
		assert self.client.session['pin2_errCount'] == 1

	def test_authenticateSession_Practice_3(self, twilio, say, play):
		"""
		test practice sign in - bad pin entered 3rd time
		"""
		session = self.client.session
		session['practice_id'] = self.practice.id
		self.practice.set_pin('1234')
		self.practice.save()
		session['answering_service'] = 'yes'
		session['pin2_errCount'] = 2
		session['ivr2_state'] = 'PracticeIVR_Main_New'
		session.save()
		url = '/IVR/SignInV2/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085551234',
			'To': '+18004664411',
			'CallStatus': 'inprogress',
			'CallSid': '1190',
			'Digits': '1999',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		calls = [
			mock.call.Response(),
			mock.call.Response().append(say('An in valid pin was entered')),
			mock.call.Response().append(say('good bye')),
			mock.call.Hangup(),
			mock.call.Response().append(twilio.Hangup())
			]
		twilio.assert_has_calls(calls)
		assert (not 'authenticated' in self.client.session or self.client.session['authenticated'] == False)
		assert self.client.session['pin2_errCount'] == 3

	#
	# test change pin
	#
	def test_ChangePin_Provider_1(self, twilio, say, play):
		"""
		provider change pin request - called with provider's mobile #
		setup pin step 1
		"""
		provider = self.providers[0]
		session = self.client.session
		session['provider_id'] = provider.id
		session['ivr2_state'] = 'ProviderIVR_Setup_New'
		session['ivr2_sub_state'] = 'ProviderIVR_Setup_Start'
		session['authenticated'] = True
		session.save()
		url = '/IVR/ChangePinV2/1/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085551234',
			'To': '+18004664411',
			'CallStatus': 'inprogress',
			'CallSid': '1200',
			'Digits': '1234',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		calls = [
			mock.call.Response(),
			mock.call.Gather(action='/IVR/ChangePinV2/2/',
				finishOnKey='#',
				numDigits=8,),
			mock.call.Gather().append(say("To verify that we have the correct pin, please enter it again. Press pound to finish.")),
			mock.call.Response().append(twilio.Gather(action='/IVR/ChangePinV2/2/',
				finishOnKey='#',
				numDigits=8,)),
			]
		twilio.assert_has_calls(calls)
		assert self.client.session['ivr2_state'] == 'ProviderIVR_Setup_New'
		assert self.client.session['ivr2_sub_state'] == 'ProviderIVR_Setup_Start'

	def test_ChangePin_Provider_1_bad(self, twilio, say, play):
		"""
		provider change pin request - called with provider's mobile #
		setup pin step 1 - enter < 4 digits
		"""
		provider = self.providers[0]
		session = self.client.session
		session['provider_id'] = provider.id
		session['ivr2_state'] = 'ProviderIVR_Setup_New'
		session['ivr2_sub_state'] = 'ProviderIVR_Setup_Start'
		session['authenticated'] = True
		session.save()
		url = '/IVR/ChangePinV2/1/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085551234',
			'To': '+18004664411',
			'CallStatus': 'inprogress',
			'CallSid': '1200',
			'Digits': '12',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		calls = [
			mock.call.Response(),
			mock.call.Response().append(say("An in valid pin was entered.")),
			mock.call.Gather(
				action='/IVR/ChangePinV2/1/',
				finishOnKey='#',
				numDigits=8,
				),
			mock.call.Gather().append(say("Please enter four to eight digits. Press pound to finish.")),
			mock.call.Response().append(twilio.Gather()),
			]
		twilio.assert_has_calls(calls)
		twilio.assert_has_calls(calls)
		assert self.client.session['ivr2_state'] == 'ProviderIVR_Setup_New'
		assert self.client.session['ivr2_sub_state'] == 'ProviderIVR_Setup_Start'

	def test_ChangePin_Provider_2_good(self, twilio, say, play):
		"""
		provider setup/change pin step 2: confirm pin, good pin
		"""
		generate_keys_for_users(open(os.devnull, 'w'))
		provider = self.providers[0]
		config = _getProviderVMConfig(provider)
		config.save()
		session = self.client.session
		session['provider_id'] = provider.id
		session['ivr2_state'] = 'ProviderIVR_Setup_New'
		session['ivr2_sub_state'] = 'ProviderIVR_Setup_Pin'
		session['config_id'] = config.id
		session['authenticated'] = True
		session['ivr2_changePin_hash'] = 'sha1$52958$8d282c07727dece284f4bed71a94cc469e1c9418'
		session.save()
		url = '/IVR/ChangePinV2/2/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085551234',
			'To': '+18004664411',
			'CallStatus': 'inprogress',
			'CallSid': '1201',
			'Digits': '1234',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		calls = [
			mock.call.Response(),
			mock.call.Redirect('/IVR/ProviderV2/Setup/'),
			mock.call.Response().append(twilio.Redirect()),
			]
		twilio.assert_has_calls(calls)
		assert self.client.session['ivr2_state'] == 'ProviderIVR_Setup_New'
		assert self.client.session['ivr2_sub_state'] == 'ProviderIVR_Setup_Pin'
		self.cleanup_rsa()

	def test_ChangePin_Provider_2_bad(self, twilio, say, play):
		"""
		provider setup/change pin step 2: confirm pin - bad pin
		"""
		provider = self.providers[0]
		config = _getProviderVMConfig(provider)
		config.save()
		session = self.client.session
		session['provider_id'] = provider.id
		session['ivr2_state'] = 'ProviderIVR_Setup_New'
		session['ivr2_sub_state'] = 'ProviderIVR_Setup_Pin'
		session['config_id'] = config.id
		session['authenticated'] = True
		session['ivr2_changePin_hash'] = 'sha1$52958$8d282c07727dece284f4bed71a94cc469e1c9418'
		session.save()
		url = '/IVR/ChangePinV2/2/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085551234',
			'To': '+18004664411',
			'CallStatus': 'inprogress',
			'CallSid': '1202',
			'Digits': '1212',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		calls = [
			mock.call.Response(),
			mock.call.Response().append(say("The entered pins do not match.")),
			mock.call.Gather(
				action='/IVR/ChangePinV2/1/',
				finishOnKey='#',
				numDigits=8,
				),
			mock.call.Gather().append(say("Please enter four to eight digits. Press pound to finish.")),
			mock.call.Response().append(twilio.Gather()),
			]
		twilio.assert_has_calls(calls)
		assert self.client.session['ivr2_state'] == 'ProviderIVR_Setup_New'
		assert self.client.session['ivr2_sub_state'] == 'ProviderIVR_Setup_Pin'

	def test_ChangePin_Practice_1(self, twilio, say, play):
		"""
		practice setup/change pin initial - step 1
		"""
		session = self.client.session
		session['practice_id'] = self.practice.id
		session['answering_service'] = 'yes'
		session['ivr2_state'] = 'PracticeIVR_Setup_New'
		session['ivr2_sub_state'] = 'PracticeIVR_Setup_1'
		session['authenticated'] = True
		session.save()
		url = '/IVR/ChangePinV2/1/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14086661111',
			'To': '+14085551111',
			'CallStatus': 'inprogress',
			'CallSid': '1210',
			'Digits': '1234',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		calls = [
			mock.call.Response(),
			mock.call.Gather(action='/IVR/ChangePinV2/2/',
				finishOnKey='#',
				numDigits=8,),
			mock.call.Gather().append(say("To verify that we have the correct pin, please enter it again. Press pound to finish.")),
			mock.call.Response().append(twilio.Gather(action='/IVR/ChangePinV2/2/',
				finishOnKey='#',
				numDigits=8,)),
			]
		twilio.assert_has_calls(calls)
		assert self.client.session['ivr2_state'] == 'PracticeIVR_Setup_New'
		assert self.client.session['ivr2_sub_state'] == 'PracticeIVR_Setup_1'

	def test_ChangePin_Practice_1_bad(self, twilio, say, play):
		"""
		practice setup/change pin initial - step 1
		"""
		session = self.client.session
		session['practice_id'] = self.practice.id
		session['answering_service'] = 'yes'
		session['ivr2_state'] = 'PracticeIVR_Setup_New'
		session['ivr2_sub_state'] = 'PracticeIVR_Setup_1'
		session['authenticated'] = True
		session.save()
		url = '/IVR/ChangePinV2/1/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14086661111',
			'To': '+14085551111',
			'CallStatus': 'inprogress',
			'CallSid': '1210',
			'Digits': '1234567890',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		calls = [
			mock.call.Response(),
			mock.call.Response().append(say("An in valid pin was entered.")),
			mock.call.Gather(
				action='/IVR/ChangePinV2/1/',
				finishOnKey='#',
				numDigits=8,
				),
			mock.call.Gather().append(say("Please enter four to eight digits. Press pound to finish.")),
			mock.call.Response().append(twilio.Gather()),
			]
		twilio.assert_has_calls(calls)
		assert self.client.session['ivr2_state'] == 'PracticeIVR_Setup_New'
		assert self.client.session['ivr2_sub_state'] == 'PracticeIVR_Setup_1'

	def test_ChangePin_Practice_2(self, twilio, say, play):
		"""
		practice setup/change pin step 2 - confirm with good pin
		"""
		session = self.client.session
		session['practice_id'] = self.practice.id
		session['answering_service'] = 'yes'
		session['ivr2_state'] = 'PracticeIVR_Setup_New'
		session['ivr2_sub_state'] = 'PracticeIVR_Setup_1'
#		generate_keys_for_users()
		session['authenticated'] = True
		session['ivr2_changePin_hash'] = 'sha1$52958$8d282c07727dece284f4bed71a94cc469e1c9418'
		session.save()
		url = '/IVR/ChangePinV2/2/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14086661111',
			'To': '+14085551111',
			'CallStatus': 'inprogress',
			'CallSid': '1211',
			'Digits': '1234',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		calls = [
			mock.call.Response(),
			mock.call.Redirect('/IVR/PracticeV2/Setup/'),
			mock.call.Response().append(twilio.Redirect('/IVR/PracticeV2/Setup/')),
			]
		twilio.assert_has_calls(calls)
		assert self.client.session['ivr2_state'] == 'PracticeIVR_Setup_New'
		assert self.client.session['ivr2_sub_state'] == 'PracticeIVR_Setup_1'

	def test_ChangePin_Practice_2_bad(self, twilio, say, play):
		"""
		practice setup/change pin step 2 - confirm with bad pin
		"""
		session = self.client.session
		session['practice_id'] = self.practice.id
		session['answering_service'] = 'yes'
		session['ivr2_state'] = 'PracticeIVR_Setup_New'
		session['ivr2_sub_state'] = 'PracticeIVR_Setup_1'
		session['authenticated'] = True
		session['ivr2_changePin_hash'] = 'sha1$52958$8d282c07727dece284f4bed71a94cc469e1c9418'
		session.save()
		url = '/IVR/ChangePinV2/2/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14086661111',
			'To': '+14085551111',
			'CallStatus': 'inprogress',
			'CallSid': '1212',
			'Digits': '1111',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		calls = [
			mock.call.Response(),
			mock.call.Response().append(say("The entered pins do not match.")),
			mock.call.Gather(
				action='/IVR/ChangePinV2/1/',
				finishOnKey='#',
				numDigits=8,
				),
			mock.call.Gather().append(say("Please enter four to eight digits. Press pound to finish.")),
			mock.call.Response().append(twilio.Gather()),
			]
		twilio.assert_has_calls(calls)
		assert self.client.session['ivr2_state'] == 'PracticeIVR_Setup_New'
		assert self.client.session['ivr2_sub_state'] == 'PracticeIVR_Setup_1'

	#
	# test change name
	#
	def test_ChangeName_Provider_1(self, twilio, say, play):
		"""
		provider setup/change name step 2 - save name of recording (confirmed by caller)
		step 1 is in provider/practice call to ChangeName via Setup or Options
		"""
		provider = self.providers[0]
		config = _getProviderVMConfig(provider)
		config.pin = 'sha1$52958$8d282c07727dece284f4bed71a94cc469e1c9418'
		config.save()
		session = self.client.session
		session['provider_id'] = provider.id
		session['ivr2_state'] = 'ProviderIVR_Setup_New'
		session['ivr2_sub_state'] = 'ProviderIVR_Setup_Name'
		session['ivr2_Record_recording'] = 'http://api.twilio.com/2010-04-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/RE8e3dfb46277add8bb0b381d087d9424d'
		session['config_id'] = config.id
		session['authenticated'] = True
		session.save()
		url = '/IVR/ChangeNameV2/1/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085551234',
			'To': '+18004664411',
			'CallStatus': 'inprogress',
			'CallSid': '1220',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		calls = [
			mock.call.Response(),
			mock.call.Redirect('/IVR/ProviderV2/Setup/'),
			mock.call.Response().append(twilio.Redirect()),
			]
		twilio.assert_has_calls(calls)
		assert self.client.session['ivr2_state'] == 'ProviderIVR_Setup_New'
		assert self.client.session['ivr2_sub_state'] == 'ProviderIVR_Setup_Name'
		config = VMBox_Config.objects.get(id=self.client.session['config_id'])
		assert config.name == 'http://api.twilio.com/2010-04-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/RE8e3dfb46277add8bb0b381d087d9424d'

	def test_ChangeName_Provider_2(self, twilio, say, play):
		"""
		provider setup/change name initial - step 1 is done either by Provider/Practice
		step 2 of change provider with no ivr2_Record_recording url
		"""
		provider = self.providers[0]
		config = _getProviderVMConfig(provider)
		config.pin = 'sha1$52958$8d282c07727dece284f4bed71a94cc469e1c9418'
		config.save()
		session = self.client.session
		session['provider_id'] = provider.id
		session['ivr2_state'] = 'ProviderIVR_Setup_New'
		session['ivr2_sub_state'] = 'ProviderIVR_Setup_Name'
		session['config_id'] = config.id
		session['authenticated'] = True
		session.save()
		url = '/IVR/ChangeNameV2/1/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085551234',
			'To': '+18004664411',
			'CallStatus': 'inprogress',
			'CallSid': '1221',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		calls = [
			mock.call.Response(),
			mock.call.Response().append(say("Now, we need to record your name. Please say your name after the tone. Press pound to finish.")),
			mock.call.Record(finishOnKey='1234567890*#',
				transcribe=False, playBeep=True, timeout=3, maxLength=10,
				action='/IVR/GetRecordingV2/1/'),
			mock.call.Response().append(twilio.Record()),
			mock.call.Redirect('/IVR/GetRecordingV2/'),
			mock.call.Response().append(twilio.Redirect())
			]
		twilio.assert_has_calls(calls)
		assert self.client.session['ivr2_state'] == 'ProviderIVR_Setup_New'
		assert self.client.session['ivr2_sub_state'] == 'ProviderIVR_Setup_Name'

	def test_ChangeName_Practice_1(self, twilio, say, play):
		"""
		practice setup/change name step 2 - save practice name
		"""
		session = self.client.session
		session['practice_id'] = self.practice.id
		session['answering_service'] = 'yes'
		session['ivr2_state'] = 'PracticeIVR_Setup_New'
		session['ivr2_sub_state'] = 'PracticeIVR_Setup_2'
		session['ivr2_Record_recording'] = 'http://api.twilio.com/2010-04-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/RE8e3dfb46277add8bb0b381d087d9424d'
		session['authenticated'] = True
		session.save()
		url = '/IVR/ChangeNameV2/1/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085551234',
			'To': '+18004664411',
			'CallStatus': 'inprogress',
			'CallSid': '1223',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		calls = [
			mock.call.Response(),
			mock.call.Redirect('/IVR/PracticeV2/Setup/'),
			mock.call.Response().append(twilio.Redirect()),
			]
		twilio.assert_has_calls(calls)
		assert self.client.session['ivr2_state'] == 'PracticeIVR_Setup_New'
		assert self.client.session['ivr2_sub_state'] == 'PracticeIVR_Setup_2'
		practice = PracticeLocation.objects.get(id=self.client.session['practice_id'])
		assert practice.name_greeting == 'http://api.twilio.com/2010-04-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/RE8e3dfb46277add8bb0b381d087d9424d'

	def test_ChangeName_Practice_2(self, twilio, say, play):
		"""
		practice setup/change name step 2 - no ivr2_Record_recording
		"""
		session = self.client.session
		session['practice_id'] = self.practice.id
		session['answering_service'] = 'yes'
		session['ivr2_state'] = 'PracticeIVR_Setup_New'
		session['ivr2_sub_state'] = 'PracticeIVR_Setup_1'
		session['authenticated'] = True
		session.save()
		url = '/IVR/ChangeNameV2/1/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085551234',
			'To': '+18004664411',
			'CallStatus': 'inprogress',
			'CallSid': '1222',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		calls = [
			mock.call.Response(),
			mock.call.Response().append(say("Now, we need to record your name. Please say your name after the tone. Press pound to finish.")),
			mock.call.Record(finishOnKey='1234567890*#',
				transcribe=False, playBeep=True, timeout=3, maxLength=10,
				action='/IVR/GetRecordingV2/1/'),
			mock.call.Response().append(twilio.Record()),
			mock.call.Redirect('/IVR/GetRecordingV2/'),
			mock.call.Response().append(twilio.Redirect()),
			]
		twilio.assert_has_calls(calls)
		assert self.client.session['ivr2_state'] == 'PracticeIVR_Setup_New'
		assert self.client.session['ivr2_sub_state'] == 'PracticeIVR_Setup_1'

	#
	# test change greeting
	#
	def test_ChangeGreeting_Provider_1(self, twilio, say, play):
		"""
		provider setup/change greeting - step 2 - confirm greeting
		"""
		provider = self.providers[0]
		config = _getProviderVMConfig(provider)
		config.pin = 'sha1$52958$8d282c07727dece284f4bed71a94cc469e1c9418'
		config.save()
		session = self.client.session
		session['provider_id'] = provider.id
		session['config_id'] = config.id
		session['ivr2_state'] = 'ProviderIVR_Setup_New'
		session['ivr2_sub_state'] = 'ProviderIVR_Setup_Greeting'
		session['ivr2_Record_recording'] = 'http://api.twilio.com/2010-04-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/RE8e3dfb46277add8bb0b381d087d9424d'
		session['authenticated'] = True
		session.save()
		url = '/IVR/ChangeGreetingV2/1/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085551234',
			'To': '+18004664411',
			'CallStatus': 'inprogress',
			'CallSid': '1231',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		calls = [
			mock.call.Response(),
			mock.call.Redirect('/IVR/ProviderV2/Setup/'),
			mock.call.Response().append(twilio.Redirect()),
			]
		twilio.assert_has_calls(calls)
		assert self.client.session['ivr2_state'] == 'ProviderIVR_Setup_New'
		assert self.client.session['ivr2_sub_state'] == 'ProviderIVR_Setup_Greeting'
		config = VMBox_Config.objects.get(id=self.client.session['config_id'])
		assert config.greeting == 'http://api.twilio.com/2010-04-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/RE8e3dfb46277add8bb0b381d087d9424d'

	def test_ChangeGreeting_Provider_2(self, twilio, say, play):
		"""
		provider setup/change greeting - no recording
		"""
		provider = self.providers[0]
		config = _getProviderVMConfig(provider)
		config.pin = 'sha1$52958$8d282c07727dece284f4bed71a94cc469e1c9418'
		config.save()
		session = self.client.session
		session['provider_id'] = provider.id
		session['ivr2_state'] = 'ProviderIVR_Setup_New'
		session['ivr2_sub_state'] = 'ProviderIVR_Setup_Greeting'
		session['config_id'] = config.id
		session['authenticated'] = True
		session.save()
		url = '/IVR/ChangeGreetingV2/1/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085551234',
			'To': '+18004664411',
			'CallStatus': 'inprogress',
			'CallSid': '1230',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		calls = [
			mock.call.Response(),
			mock.call.Response().append(say("Finally, we need to set up a greeting.Please say your new greeting after the tone. Press pound to finish.")),
			mock.call.Record(finishOnKey='1234567890*#',
				transcribe=False, playBeep=True, timeout=3, maxLength=120,
				action='/IVR/GetRecordingV2/1/'),
			mock.call.Response().append(twilio.Record()),
			mock.call.Redirect('/IVR/GetRecordingV2/'),
			mock.call.Response().append(twilio.Redirect()),
			]
		twilio.assert_has_calls(calls)
		assert self.client.session['ivr2_state'] == 'ProviderIVR_Setup_New'
		assert self.client.session['ivr2_sub_state'] == 'ProviderIVR_Setup_Greeting'

	def test_ChangeGreeting_Practice_1(self, twilio, say, play):
		"""
		practice setup/change greeting - step 2, confirm closed greeting
		"""
		session = self.client.session
		session['practice_id'] = self.practice.id
		session['answering_service'] = 'yes'
		session['ivr2_state'] = 'PracticeIVR_Setup_New'
		session['ivr2_sub_state'] = 'PracticeIVR_Setup_2'
		session['ivr2_Record_recording'] = 'http://api.twilio.com/2010-04-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/RE8e3dfb46277add8bb0b381d087d9424d'
		session['authenticated'] = True
		session.save()
		url = '/IVR/ChangeGreetingV2/1/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085551234',
			'To': '+18004664411',
			'CallStatus': 'inprogress',
			'CallSid': '1233',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		calls = [
			mock.call.Response(),
			mock.call.Redirect('/IVR/PracticeV2/Setup/'),
			mock.call.Response().append(twilio.Redirect()),
			]
		twilio.assert_has_calls(calls)
		assert self.client.session['ivr2_state'] == 'PracticeIVR_Setup_New'
		assert self.client.session['ivr2_sub_state'] == 'PracticeIVR_Setup_2'
		practice = PracticeLocation.objects.get(id=self.client.session['practice_id'])
		assert practice.greeting_lunch == 'http://api.twilio.com/2010-04-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/RE8e3dfb46277add8bb0b381d087d9424d'

	def test_ChangeGreeting_Practice_2(self, twilio, say, play):
		"""
		practice setup/change greeting - step 2, no ivr2_Record_recording
		"""
		session = self.client.session
		session['practice_id'] = self.practice.id
		session['answering_service'] = 'yes'
		session['ivr2_state'] = 'PracticeIVR_Setup_New'
		session['ivr2_sub_state'] = 'PracticeIVR_Setup_2'
		session['authenticated'] = True
		session.save()
		url = '/IVR/ChangeGreetingV2/1/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085551234',
			'To': '+18004664411',
			'CallStatus': 'inprogress',
			'CallSid': '1232',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		calls = [
			mock.call.Response(),
			mock.call.Response().append(say(u'Next, we need to set up your answering service greeting. This will be played when the office is closed.\
Please say your new greeting for closed office after the tone. Press pound to finish.')),
			mock.call.Record(finishOnKey='1234567890*#',
				transcribe=False, playBeep=True, timeout=3, maxLength=120,
				action='/IVR/GetRecordingV2/1/'),
			mock.call.Response().append(twilio.Record()),
			mock.call.Redirect('/IVR/GetRecordingV2/'),
			mock.call.Response().append(twilio.Redirect()),
			]
		twilio.assert_has_calls(calls)
		assert self.client.session['ivr2_state'] == 'PracticeIVR_Setup_New'
		assert self.client.session['ivr2_sub_state'] == 'PracticeIVR_Setup_2'

	def test_ChangeGreeting_Practice_3(self, twilio, say, play):
		"""
		practice setup/change greeting - step 3, closed office greeting confirm
		"""
		session = self.client.session
		session['practice_id'] = self.practice.id
		session['answering_service'] = 'yes'
		session['ivr2_state'] = 'PracticeIVR_Setup_New'
		session['ivr2_sub_state'] = 'PracticeIVR_Setup_3'
		session['ivr2_Record_recording'] = 'http://api.twilio.com/2010-04-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/RE8e3dfb46277add8bb0b381d087d9424d'
		session['authenticated'] = True
		session.save()
		url = '/IVR/ChangeGreetingV2/1/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085551234',
			'To': '+18004664411',
			'CallStatus': 'inprogress',
			'CallSid': '1235',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		calls = [
			mock.call.Response(),
			mock.call.Redirect('/IVR/PracticeV2/Setup/'),
			mock.call.Response().append(twilio.Redirect()),
			]
		twilio.assert_has_calls(calls)
		assert self.client.session['ivr2_state'] == 'PracticeIVR_Setup_New'
		assert self.client.session['ivr2_sub_state'] == 'PracticeIVR_Setup_3'
		practice = PracticeLocation.objects.get(id=self.client.session['practice_id'])
		assert practice.greeting_closed == 'http://api.twilio.com/2010-04-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/RE8e3dfb46277add8bb0b381d087d9424d'

	def test_ChangeGreeting_Practice_4(self, twilio, say, play):
		"""
		practice setup/change greeting - step 3, closed office greeting no ivr2_Record_recording
		"""
		session = self.client.session
		session['practice_id'] = self.practice.id
		session['answering_service'] = 'yes'
		session['ivr2_state'] = 'PracticeIVR_Setup_New'
		session['ivr2_sub_state'] = 'PracticeIVR_Setup_3'
		session['authenticated'] = True
		session.save()
		url = '/IVR/ChangeGreetingV2/1/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085551234',
			'To': '+18004664411',
			'CallStatus': 'inprogress',
			'CallSid': '1234',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		calls = [
			mock.call.Response(),
			mock.call.Response().append(say(u'Finally, we need to set up a greeting that will be played when the office is open.\
				Please say your new greeting for temporarily closed office after the tone. Press pound to finish.')),
			mock.call.Record(finishOnKey='1234567890*#',
				transcribe=False, playBeep=True, timeout=3, maxLength=120,
				action='/IVR/GetRecordingV2/1/'),
			mock.call.Response().append(twilio.Record()),
			mock.call.Redirect('/IVR/GetRecordingV2/'),
			mock.call.Response().append(twilio.Redirect()),
			]
		twilio.assert_has_calls(calls)
		assert self.client.session['ivr2_state'] == 'PracticeIVR_Setup_New'
		assert self.client.session['ivr2_sub_state'] == 'PracticeIVR_Setup_3'

	# 
	# test getQuickRecording - called by Practice LeaveRegularMsg and LeaveUrgentMsg
	#
	def test_getQuickRecording_0(self, twilio, say, play):
		"""
		get quick recording - no prompt, raise exception
		"""
		session = self.client.session
		provider = self.providers[0]
		session['provider_id'] = provider.id
		session['ivr2_state'] = 'ProviderIVR_LeaveMsg_New'
		# or PracticeIVR_LeaveUrgentMsg_GetMsg
		session['ivr2_returnOnHangup'] = 'MHLogin.DoctorCom.IVR.views_provider_v2.ProviderIVR_LeaveMsg_Action'
		session['authenticated'] = True
		session.save()
		url = '/IVR/GetQuickRecordingV2/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085551234',
			'To': '+18004664411',
			'CallStatus': 'inprogress',
			'CallSid': '1246',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		with self.assertRaises(Exception):
			response = self.client.post(url, post_vars,
				**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
#		self.assertRaises(Exception, 'Error. Required session key \'ivr2_Record_prompt\' undefined')

	def test_getQuickRecording_1(self, twilio, say, play):
		"""
		get quick recording - via practice leave message regular (or urgent)
		"""
		session = self.client.session
		session['practice_id'] = self.practice.id
		session['answering_service'] = 'yes'
		session['ivr2_state'] = 'PracticeIVR_LeaveRegularMsg_New'
		session['ivr2_sub_state'] = 'PracticeIVR_LeaveRegularMsg_GetMsg'
		# or PracticeIVR_LeaveUrgentMsg_GetMsg
		session['ivr2_Record_prompt_str'] = 'Please leave your message'
		session['authenticated'] = True
		session.save()
		url = '/IVR/GetQuickRecordingV2/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085551234',
			'To': '+18004664411',
			'CallStatus': 'inprogress',
			'CallSid': '1240',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		calls = [
			mock.call.Response(),
			mock.call.Pause(length=1),
			mock.call.Response().append(twilio.Pause()),
			mock.call.Response().append(say('Please leave your message')),
			mock.call.Record(finishOnKey='1234567890*#',
				action='/IVR/GetQuickRecordingV2/1/',
				timeout=6, playBeep=True, maxLength=5),
			mock.call.Response().append(twilio.Record()),
			mock.call.Redirect('/IVR/GetQuickRecordingV2/'),
			mock.call.Response().append(twilio.Redirect()),
			]
		twilio.assert_has_calls(calls)
		assert self.client.session['ivr2_state'] == 'PracticeIVR_LeaveRegularMsg_New'
		assert self.client.session['ivr2_sub_state'] == 'PracticeIVR_LeaveRegularMsg_GetMsg'

	def test_getQuickRecording_2(self, twilio, say, play):
		"""
		get quick recording - via practice leave message (regular or urgent)
		second time through
		"""
		session = self.client.session
		session['practice_id'] = self.practice.id
		session['answering_service'] = 'yes'
		session['ivr2_state'] = 'PracticeIVR_LeaveRegularMsg_New'
		session['ivr2_sub_state'] = 'PracticeIVR_LeaveRegularMsg_GetMsg'
		# or PracticeIVR_LeaveUrgentMsg_GetMsg
		session['ivr2_Record_prompt_str'] = 'Please leave your message'
		session['getQuickRecording_subsequentExcecution'] = True
		session['authenticated'] = True
		session.save()
		url = '/IVR/GetQuickRecordingV2/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085551234',
			'To': '+18004664411',
			'CallStatus': 'inprogress',
			'CallSid': '1241',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		calls = [
			mock.call.Response(),
			mock.call.Response().append(say('sorry didn\'t get that')),
			mock.call.Pause(length=1),
			mock.call.Response().append(twilio.Pause()),
			mock.call.Response().append(say('Please leave your message')),
			mock.call.Record(finishOnKey='1234567890*#',
				action='/IVR/GetQuickRecordingV2/1/',
				timeout=6, playBeep=True, maxLength=5),
			mock.call.Response().append(twilio.Record()),
			mock.call.Redirect('/IVR/GetQuickRecordingV2/'),
			mock.call.Response().append(twilio.Redirect()),
			]
		twilio.assert_has_calls(calls)
		assert self.client.session['ivr2_state'] == 'PracticeIVR_LeaveRegularMsg_New'
		assert self.client.session['ivr2_sub_state'] == 'PracticeIVR_LeaveRegularMsg_GetMsg'

	def test_getQuickRecording_3(self, twilio, say, play):
		"""
		get quick recording - via practice leave message (regular or urgent)
		caller hang up - no msg
		"""
		session = self.client.session
		session['practice_id'] = self.practice.id
		session['answering_service'] = 'yes'
		session['ivr2_state'] = 'PracticeIVR_LeaveRegularMsg_New'
		session['ivr2_sub_state'] = 'PracticeIVR_LeaveRegularMsg_GetMsg'
		# or PracticeIVR_LeaveUrgentMsg_GetMsg 
		session['ivr2_Record_prompt_str'] = 'Please leave your message'
		session['getQuickRecording_subsequentExcecution'] = True
		session['authenticated'] = True
		session.save()
		url = '/IVR/GetQuickRecordingV2/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085551234',
			'To': '+18004664411',
			'CallStatus': 'completed',
			'CallSid': '1242',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		calls = [
			mock.call.Response(),
			]
		twilio.assert_has_calls(calls)
		assert self.client.session['ivr2_state'] == 'PracticeIVR_LeaveRegularMsg_New'
		assert self.client.session['ivr2_sub_state'] == 'PracticeIVR_LeaveRegularMsg_GetMsg'

	def test_getQuickRecording_4(self, twilio, say, play):
		"""
		get quick recording - via practice leave message (regular or urgent)
		caller hang up - with recording url - no return on hangup
		"""
		session = self.client.session
		session['practice_id'] = self.practice.id
		session['answering_service'] = 'yes'
		session['ivr2_state'] = 'PracticeIVR_LeaveRegularMsg_New'
		session['ivr2_sub_state'] = 'PracticeIVR_LeaveRegularMsg_GetMsg'
		# or PracticeIVR_LeaveUrgentMsg_GetMsg 
		session['ivr2_Record_prompt_str'] = 'Please leave your message'
		session['authenticated'] = True
		session.save()
		url = '/IVR/GetQuickRecordingV2/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085551234',
			'To': '+18004664411',
			'CallStatus': 'completed',
			'CallSid': '1243',
			'RecordingUrl': 'http://api.twilio.com/2010-04-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/RE8e3dfb46277add8bb0b381d087d9424d',
			'CallDuration': '30',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		calls = [
			mock.call.Response(),
			]
		twilio.assert_has_calls(calls)
		assert self.client.session['ivr2_state'] == 'PracticeIVR_LeaveRegularMsg_New'
		assert self.client.session['ivr2_sub_state'] == 'PracticeIVR_LeaveRegularMsg_GetMsg'

	def test_getQuickRecording_5(self, twilio, say, play):
		"""
		get quick recording - via practice leave message (regular or urgent)
		caller hang up - with recording url, with return on hangup state
		"""
		session = self.client.session
		session['practice_id'] = self.practice.id
		session['answering_service'] = 'yes'
		session['ivr2_state'] = 'PracticeIVR_LeaveRegularMsg_New'
		session['ivr2_sub_state'] = 'PracticeIVR_LeaveRegularMsg_GetMsg'
		# or PracticeIVR_LeaveUrgentMsg_GetMsg 
		session['ivr2_Record_prompt_str'] = 'Please leave your message'
		session['ivr2_returnOnHangup'] = 'MHLogin.DoctorCom.IVR.views_practice_v2.PracticeIVR_LeaveRegularMsg_New'
		session['authenticated'] = True
		# need to set up callLog and callback number for state
		session['ivr2_Record_callbacknumber'] = '4085551234'
		caller_mhluser = _getMHLUser('4085551234')
		log = callLog(callSID='1243', caller_number='4085551234', called_number='8004664411',
			call_source='OC')
		log.save()
		session.save()
		url = '/IVR/GetQuickRecordingV2/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085551234',
			'To': '+18004664411',
			'CallStatus': 'completed',
			'CallSid': '1243',
			'RecordingUrl': 'http://api.twilio.com/2010-04-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/RE8e3dfb46277add8bb0b381d087d9424d',
			'CallDuration': '30',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		calls = [
			mock.call.Response(),
			]
		twilio.assert_has_calls(calls)
		assert self.client.session['ivr2_state'] == 'PracticeIVR_LeaveRegularMsg_New'
#		assert we got a message sent/saved
		log_qs = callLog.objects.filter(callSID='1243')
		if (log_qs.exists()):
			log = log_qs.get()
			self.assertEqual(log.call_duration, 30)

	def test_getQuickRecording_6(self, twilio, say, play):
		"""
		get quick recording - action (with recording url)
		"""
		session = self.client.session
		session['practice_id'] = self.practice.id
		session['answering_service'] = 'yes'
		session['ivr2_state'] = 'PracticeIVR_LeaveRegularMsg_New'
		session['ivr2_sub_state'] = 'PracticeIVR_LeaveRegularMsg_GetMsg'
		# or PracticeIVR_LeaveUrgentMsg_GetMsg
		session['ivr2_Record_prompt_str'] = 'Please leave your message'
		session['authenticated'] = True
		session.save()
		url = '/IVR/GetQuickRecordingV2/1/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085551234',
			'To': '+18004664411',
			'CallStatus': 'inprogress',
			'CallSid': '1244',
			'RecordingUrl': 'http://api.twilio.com/2010-04-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/RE8e3dfb46277add8bb0b381d087d9424d'
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		calls = [
			mock.call.Response(),
			mock.call.Redirect('/IVR/PracticeV2/LeaveTextMsg/'),
			mock.call.Response().append(twilio.Redirect()),
			]
		twilio.assert_has_calls(calls)
		assert self.client.session['ivr2_state'] == 'PracticeIVR_LeaveRegularMsg_New'
		assert self.client.session['ivr2_sub_state'] == 'PracticeIVR_LeaveRegularMsg_GetMsg'
		assert self.client.session['ivr2_Record_recording'] == 'http://api.twilio.com/2010-04-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/RE8e3dfb46277add8bb0b381d087d9424d'
		assert self.client.session['ivr2_only_callbacknumber'] == False

	def test_getQuickRecording_7(self, twilio, say, play):
		"""
		get quick recording - action (with no recording url)
		"""
		session = self.client.session
		session['practice_id'] = self.practice.id
		session['answering_service'] = 'yes'
		session['ivr2_state'] = 'PracticeIVR_LeaveRegularMsg_New'
		session['ivr2_sub_state'] = 'PracticeIVR_LeaveRegularMsg_GetMsg'
		# or PracticeIVR_LeaveUrgentMsg_GetMsg
		session['ivr2_Record_prompt_str'] = 'Please leave your message'
		session['getQuickRecording_subsequentExcecution'] = True
		session['authenticated'] = True
		session.save()
		url = '/IVR/GetQuickRecordingV2/1/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085551234',
			'To': '+18004664411',
			'CallStatus': 'inprogress',
			'CallSid': '1245',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		calls = [
			mock.call.Response(),
			mock.call.Response().append(say('sorry didn\'t get that')),
			mock.call.Pause(length=1),
			mock.call.Response().append(twilio.Pause()),
			mock.call.Response().append(say('Please leave your message')),
			mock.call.Record(finishOnKey='1234567890*#',
				action='/IVR/GetQuickRecordingV2/1/',
				timeout=6, playBeep=True, maxLength=5),
			mock.call.Response().append(twilio.Record()),
			mock.call.Redirect('/IVR/GetQuickRecordingV2/'),
			mock.call.Response().append(twilio.Redirect()),
			]
		twilio.assert_has_calls(calls)
		assert self.client.session['ivr2_state'] == 'PracticeIVR_LeaveRegularMsg_New'
		assert self.client.session['ivr2_sub_state'] == 'PracticeIVR_LeaveRegularMsg_GetMsg'

	def test_getQuickRecording_8(self, twilio, say, play):
		"""
		get quick recording - action - hangup
		"""
		session = self.client.session
		provider = self.providers[0]
		session['provider_id'] = provider.id
		session['ivr2_state'] = 'ProviderIVR_LeaveMsg_New'
		# or PracticeIVR_LeaveUrgentMsg_GetMsg
		session['ivr2_Record_prompt_str'] = 'Please leave your message'
		session['getQuickRecording_subsequentExcecution'] = True
		session['ivr2_returnOnHangup'] = 'MHLogin.DoctorCom.IVR.views_provider_v2.ProviderIVR_LeaveMsg_Action'
		session['authenticated'] = True
		session['ivr2_Record_callbacknumber'] = '4085551234'
		#caller_mhluser = _getMHLUser('4085551234')
		log = callLog(callSID='1246', caller_number='4085551234', called_number='8004664411',
			call_source='OC')
		log.save()
		session.save()
		url = '/IVR/GetQuickRecordingV2/1/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085551234',
			'To': '+18004664411',
			'CallStatus': 'completed',
			'CallSid': '1246',
			'CallDuration': '45'
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		calls = [
			mock.call.Response(),
			]
		twilio.assert_has_calls(calls)
		assert self.client.session['ivr2_state'] == 'ProviderIVR_LeaveMsg_New'
		log_qs = callLog.objects.filter(callSID='1246')
		if (log_qs.exists()):
			log = log_qs.get()
			self.assertEqual(log.call_duration, 45)

	# 
	# test getRecording
	#
	def test_getRecording_0(self, twilio, say, play):
		"""
		get recording - no prompt, raise exception
		"""
		session = self.client.session
		provider = self.providers[0]
		session['provider_id'] = provider.id
		session['ivr2_state'] = 'ProviderIVR_LeaveMsg_New'
		# or PracticeIVR_LeaveUrgentMsg_GetMsg
		session['ivr2_returnOnHangup'] = 'MHLogin.DoctorCom.IVR.views_provider_v2.ProviderIVR_LeaveMsg_Action'
		session['authenticated'] = True
		session.save()
		url = '/IVR/GetRecordingV2/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085551234',
			'To': '+18004664411',
			'CallStatus': 'inprogress',
			'CallSid': '1246',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		with self.assertRaises(Exception):
			response = self.client.post(url, post_vars,
				**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
#		self.assertRaises(Exception, 'Error. Required session key \'ivr2_Record_prompt\' undefined')

	def test_getRecording_1(self, twilio, say, play):
		"""
		get recording - via provider leave message (regular message)
		"""
		session = self.client.session
		provider = self.providers[0]
		session['provider_id'] = provider.id
		session['ivr2_state'] = 'ProviderIVR_LeaveMsg_New'
		# or PracticeIVR_LeaveUrgentMsg_GetMsg
		session['ivr2_Record_prompt_str'] = 'Please leave your message for this provider'
		session['ivr2_returnOnHangup'] = 'MHLogin.DoctorCom.IVR.views_provider_v2.ProviderIVR_LeaveMsg_Action'
		session['authenticated'] = True
		session.save()
		url = '/IVR/GetRecordingV2/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085551234',
			'To': '+18004664411',
			'CallStatus': 'inprogress',
			'CallSid': '1260',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		calls = [
			mock.call.Response(),
			mock.call.Response().append(say('Please leave a message for provider')),
			mock.call.Record(finishOnKey='1234567890*#', transcribe=False,
				playBeep=True, timeout=5, maxLength=180,
				action='/IVR/GetRecordingV2/1/'),
			mock.call.Response().append(twilio.Record()),
			mock.call.Redirect('/IVR/GetRecordingV2/'),
			mock.call.Response().append(twilio.Redirect()),
			]
		twilio.assert_has_calls(calls)
		assert self.client.session['ivr2_state'] == 'ProviderIVR_LeaveMsg_New'

	def test_getRecording_2a(self, twilio, say, play):
		"""
		get recording - prompt once is set - first time around
		"""
		session = self.client.session
		provider = self.providers[0]
		session['provider_id'] = provider.id
		session['ivr2_state'] = 'ProviderIVR_LeaveMsg_New'
		# or PracticeIVR_LeaveUrgentMsg_GetMsg
		session['ivr2_returnOnHangup'] = 'MHLogin.DoctorCom.IVR.views_provider_v2.ProviderIVR_LeaveMsg_Action'
		session['ivr2_Record_prompt_str'] = 'Please leave your message'
		session['ivr2_Record_promptOnce'] = True
		session['authenticated'] = True
		session.save()
		url = '/IVR/GetRecordingV2/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085551234',
			'To': '+18004664411',
			'CallStatus': 'inprogress',
			'CallSid': '1261',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		calls = [
			mock.call.Response(),
			mock.call.Response().append(say('Please leave your message')),
			mock.call.Record(finishOnKey='1234567890*#', transcribe=False,
				playBeep=True, timeout=5, maxLength=180,
				action='/IVR/GetRecordingV2/1/'),
			mock.call.Response().append(twilio.Record()),
			mock.call.Redirect('/IVR/GetRecordingV2/'),
			mock.call.Response().append(twilio.Redirect()),
			]
		twilio.assert_has_calls(calls)
		assert self.client.session['ivr2_state'] == 'ProviderIVR_LeaveMsg_New'
		assert self.client.session['ivr2_Record_promptOnce_played'] == True

	def test_getRecording_2b(self, twilio, say, play):
		"""
		get recording - prompt once is set; already played set, no say/prompt
		"""
		session = self.client.session
		provider = self.providers[0]
		session['provider_id'] = provider.id
		session['ivr2_state'] = 'ProviderIVR_LeaveMsg_New'
		# or PracticeIVR_LeaveUrgentMsg_GetMsg
		session['ivr2_returnOnHangup'] = 'MHLogin.DoctorCom.IVR.views_provider_v2.ProviderIVR_LeaveMsg_Action'
		session['ivr2_Record_prompt_str'] = 'Please leave your message'
		session['ivr2_Record_promptOnce'] = True
		session['ivr2_Record_promptOnce_played'] = True
		session['authenticated'] = True
		session.save()
		url = '/IVR/GetRecordingV2/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085551234',
			'To': '+18004664411',
			'CallStatus': 'inprogress',
			'CallSid': '1261',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		calls = [
			mock.call.Response(),
			mock.call.Record(finishOnKey='1234567890*#', transcribe=False,
				playBeep=True, timeout=5, maxLength=180,
				action='/IVR/GetRecordingV2/1/'),
			mock.call.Response().append(twilio.Record()),
			mock.call.Redirect('/IVR/GetRecordingV2/'),
			mock.call.Response().append(twilio.Redirect())
			]
		twilio.assert_has_calls(calls)
		assert self.client.session['ivr2_state'] == 'ProviderIVR_LeaveMsg_New'
		assert self.client.session['ivr2_Record_promptOnce_played'] == True

	def test_getRecording_3(self, twilio, say, play):
		"""
		get recording - via provider leave message (regular or urgent)
		caller hang up
		"""
		session = self.client.session
		provider = self.providers[0]
		session['provider_id'] = provider.id
		session['ivr2_state'] = 'ProviderIVR_LeaveMsg_New'
		# or PracticeIVR_LeaveUrgentMsg_GetMsg
		session['ivr2_Record_prompt_str'] = 'Please leave your message'
		session['authenticated'] = True
		session.save()
		url = '/IVR/GetRecordingV2/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085551234',
			'To': '+18004664411',
			'CallStatus': 'completed',
			'CallSid': '1262',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		calls = [
			mock.call.Response(),
			]
		twilio.assert_has_calls(calls)
		assert self.client.session['ivr2_state'] == 'ProviderIVR_LeaveMsg_New'

	def test_getRecording_4(self, twilio, say, play):
		"""
		get recording - action with recording url - to confirmation
		"""
		session = self.client.session
		provider = self.providers[0]
		session['provider_id'] = provider.id
		session['ivr2_state'] = 'ProviderIVR_LeaveMsg_New'
		# or PracticeIVR_LeaveUrgentMsg_GetMsg
		session['ivr2_Record_prompt_str'] = 'Please leave your message'
		session['authenticated'] = True
		session.save()
		url = '/IVR/GetRecordingV2/1/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085551234',
			'To': '+18004664411',
			'CallStatus': 'inprogress',
			'CallSid': '1263',
			'RecordingUrl': 'http://api.twilio.com/2010-04-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/RE8e3dfb46277add8bb0b381d087d9424d'
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		calls = [
			mock.call.Response(),
			mock.call.Gather(action='/IVR/GetRecordingV2/2/',
				finishOnKey='', numDigits=1),
			mock.call.Gather().append(say('You said')),
			mock.call.Play(u'http://api.twilio.com/2010-04-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/RE8e3dfb46277add8bb0b381d087d9424d'),
			mock.call.Gather().append(twilio.Play('http://api.twilio.com/')),
			mock.call.Gather().append(say('to rerecord press 3. Press 1 to continue, press any other key to replay')),
			mock.call.Response().append(twilio.Gather()),
			mock.call.Redirect('/IVR/GetRecordingV2/2/'),
			mock.call.Response().append(twilio.Redirect()),
			]
		twilio.assert_has_calls(calls)
		assert self.client.session['ivr2_state'] == 'ProviderIVR_LeaveMsg_New'
		assert self.client.session['ivr2_Record_recording'] == 'http://api.twilio.com/2010-04-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/RE8e3dfb46277add8bb0b381d087d9424d'

	def test_getRecording_5(self, twilio, say, play):
		"""
		get recording - action with no recording url - repeat
		"""
		session = self.client.session
		provider = self.providers[0]
		session['provider_id'] = provider.id
		session['ivr2_state'] = 'ProviderIVR_LeaveMsg_New'
		# or PracticeIVR_LeaveUrgentMsg_GetMsg
		session['ivr2_Record_prompt_str'] = 'Please leave your message'
		session['authenticated'] = True
		session.save()
		url = '/IVR/GetRecordingV2/1/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085551234',
			'To': '+18004664411',
			'CallStatus': 'inprogress',
			'CallSid': '1264',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		calls = [
			mock.call.Response(),
			mock.call.Response().append(say('please leave your message')),
			mock.call.Record(finishOnKey='1234567890*#', transcribe=False,
				playBeep=True, timeout=5, maxLength=180,
				action='/IVR/GetRecordingV2/1/'),
			mock.call.Response().append(twilio.Record()),
			mock.call.Redirect('/IVR/GetRecordingV2/'),
			mock.call.Response().append(twilio.Redirect()),
			]
		twilio.assert_has_calls(calls)
		assert self.client.session['ivr2_state'] == 'ProviderIVR_LeaveMsg_New'

	def test_getRecording_6(self, twilio, say, play):
		"""
		get recording - action - hangup
		"""
		session = self.client.session
		provider = self.providers[0]
		session['provider_id'] = provider.id
		session['ivr2_state'] = 'ProviderIVR_LeaveMsg_New'
		# or PracticeIVR_LeaveUrgentMsg_GetMsg
		session['ivr2_Record_prompt_str'] = 'Please leave your message'
		session['ivr2_returnOnHangup'] = 'MHLogin.DoctorCom.IVR.views_provider_v2.ProviderIVR_LeaveMsg_Action'
		session['authenticated'] = True
		session.save()
		url = '/IVR/GetRecordingV2/1/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085551234',
			'To': '+18004664411',
			'CallStatus': 'completed',
			'CallSid': '1265',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		calls = [
			mock.call.Response()
			]
		twilio.assert_has_calls(calls)
		assert self.client.session['ivr2_state'] == 'ProviderIVR_LeaveMsg_New'

	def test_getRecording_7(self, twilio, say, play):
		"""
		get Recording confirm to confirm recording; normal flow
		-- go to saveRecordingReturn to save the recording and continue
		we need to do this as part of change options -> change name for provider
		"""
		session = self.client.session
		provider = self.providers[0]
		config = _getProviderVMConfig(provider)
		config.save()
		session['provider_id'] = provider.id
		session['ivr2_state'] = 'ProviderIVR_Options_New'
		session['ivr2_sub_state'] = 'ProviderIVR_Options_1'
		session['config_id'] = config.id
		# or PracticeIVR_LeaveUrgentMsg_GetMsg
		session['ivr2_Record_prompt_str'] = 'Please say your name'
		session['ivr2_Record_recording'] = 'http://api.twilio.com/2010-04-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/RE8e3dfb46277add8bb0b381d087d9424d'
		session['authenticated'] = True
		session.save()
		url = '/IVR/GetRecordingV2/2/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085551234',
			'To': '+18004664411',
			'CallStatus': 'inprogress',
			'CallSid': '1266',
			'Digits': '1',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		calls = [
			mock.call.Response(),
			mock.call.Redirect('/IVR/ProviderV2/Options/'),
			mock.call.Response().append(twilio.Redirect()),
 			]
		twilio.assert_has_calls(calls)
		assert self.client.session['ivr2_state'] == 'ProviderIVR_Options_New'
		assert self.client.session['ivr2_sub_state'] == 'ProviderIVR_Options_1'
		config = VMBox_Config.objects.get(id=self.client.session['config_id'])
		assert config.name == 'http://api.twilio.com/2010-04-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/RE8e3dfb46277add8bb0b381d087d9424d'

	def test_getRecording_8(self, twilio, say, play):
		"""
		get Recording confirm: option to rerecord
		"""
		session = self.client.session
		provider = self.providers[0]
		config = _getProviderVMConfig(provider)
		config.save()
		session['provider_id'] = provider.id
		session['ivr2_state'] = 'ProviderIVR_Options_New'
		session['ivr2_sub_state'] = 'ProviderIVR_Options_1'
		session['config_id'] = config.id
		# or PracticeIVR_LeaveUrgentMsg_GetMsg
		session['ivr2_Record_prompt_str'] = 'Please say your name'
		session['ivr2_Record_recording'] = 'http://api.twilio.com/2010-04-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/RE8e3dfb46277add8bb0b381d087d9424d'
		session['authenticated'] = True
		session.save()
		url = '/IVR/GetRecordingV2/2/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085551234',
			'To': '+18004664411',
			'CallStatus': 'inprogress',
			'CallSid': '1267',
			'Digits': '3',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		calls = [
			mock.call.Response(),
			mock.call.Response().append(say('please say your name')),
			mock.call.Record(finishOnKey='1234567890*#', transcribe=False,
				playBeep=True, timeout=5, maxLength=180,
				action='/IVR/GetRecordingV2/1/'),
			mock.call.Response().append(twilio.Record()),
			mock.call.Redirect('/IVR/GetRecordingV2/'),
			mock.call.Response().append(twilio.Redirect()),
			]
		twilio.assert_has_calls(calls)
		assert self.client.session['ivr2_state'] == 'ProviderIVR_Options_New'
		assert self.client.session['ivr2_sub_state'] == 'ProviderIVR_Options_1'

	def test_getRecording_9(self, twilio, say, play):
		"""
		get Recording confirm: other digits instead of confirm or rerecord
		"""
		session = self.client.session
		provider = self.providers[0]
		config = _getProviderVMConfig(provider)
		config.save()
		session['provider_id'] = provider.id
		session['ivr2_state'] = 'ProviderIVR_Options_New'
		session['ivr2_sub_state'] = 'ProviderIVR_Options_1'
		session['config_id'] = config.id
		# or PracticeIVR_LeaveUrgentMsg_GetMsg
		session['ivr2_Record_prompt_str'] = 'Please say your name'
		session['ivr2_Record_recording'] = 'http://api.twilio.com/2010-04-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/RE8e3dfb46277add8bb0b381d087d9424d'
		session['authenticated'] = True
		session.save()
		url = '/IVR/GetRecordingV2/2/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085551234',
			'To': '+18004664411',
			'CallStatus': 'inprogress',
			'CallSid': '1268',
			'Digits': '9',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		calls = [
			mock.call.Response(),
			mock.call.Gather(action='/IVR/GetRecordingV2/2/',
				finishOnKey='', numDigits=1),
			mock.call.Gather().append(say('You said')),
			mock.call.Play(u'http://api.twilio.com/2010-04-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/RE8e3dfb46277add8bb0b381d087d9424d'),
			mock.call.Gather().append(twilio.Play('http://api.twilio.com/')),
			mock.call.Gather().append(say('to rerecord press 3. Press 1 to continue, press any other key to replay')),
			mock.call.Response().append(twilio.Gather()),
			mock.call.Redirect('/IVR/GetRecordingV2/2/'),
			mock.call.Response().append(twilio.Redirect()),
			]
		twilio.assert_has_calls(calls)
		assert self.client.session['ivr2_state'] == 'ProviderIVR_Options_New'
		assert self.client.session['ivr2_sub_state'] == 'ProviderIVR_Options_1'

	def test_getRecording_10(self, twilio, say, play):
		"""
		get Recording confirm - with no recording -> restart getRecording
		"""
		session = self.client.session
		provider = self.providers[0]
		config = _getProviderVMConfig(provider)
		config.save()
		session['provider_id'] = provider.id
		session['ivr2_state'] = 'ProviderIVR_Options_New'
		session['ivr2_sub_state'] = 'ProviderIVR_Options_1'
		session['config_id'] = config.id
		# or PracticeIVR_LeaveUrgentMsg_GetMsg
		session['ivr2_Record_prompt_str'] = 'Please say your name'
		session['authenticated'] = True
		session.save()
		url = '/IVR/GetRecordingV2/2/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085551234',
			'To': '+18004664411',
			'CallStatus': 'inprogress',
			'CallSid': '1269',
			'Digits': '1',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		calls = [
			mock.call.Response(),
			mock.call.Response().append(say('Please leave your message')),
			mock.call.Record(finishOnKey='1234567890*#', transcribe=False,
				playBeep=True, timeout=5, maxLength=180,
				action='/IVR/GetRecordingV2/1/'),
			mock.call.Response().append(twilio.Record()),
			mock.call.Redirect('/IVR/GetRecordingV2/'),
			mock.call.Response().append(twilio.Redirect()),
			]
		twilio.assert_has_calls(calls)
		assert self.client.session['ivr2_state'] == 'ProviderIVR_Options_New'
		assert self.client.session['ivr2_sub_state'] == 'ProviderIVR_Options_1'

	def test_getRecording_11(self, twilio, say, play):
		"""
		get recording - no prompt, raise exception
		"""
		session = self.client.session
		provider = self.providers[0]
		session['provider_id'] = provider.id
		session['ivr2_state'] = 'ProviderIVR_LeaveMsg_New'
		# or PracticeIVR_LeaveUrgentMsg_GetMsg
		session['ivr2_returnOnHangup'] = 'MHLogin.DoctorCom.IVR.views_provider_v2.ProviderIVR_LeaveMsg_Action'
		session['authenticated'] = True
		session.save()
		url = '/IVR/GetRecordingV2/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085551234',
			'To': '+18004664411',
			'CallStatus': 'inprogress',
			'CallSid': '1266',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		with self.assertRaises(Exception):
			response = self.client.post(url, post_vars,
				**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})

	#
	# test getCallBackNumber
	#
	def test_getCallBackNumber_New(self, twilio, say, play):
		"""
		practice get callback number initial start
		"""
		session = self.client.session
		session['practice_id'] = self.practice.id
		session['answering_service'] = 'yes'
		session['ivr2_state'] = 'PracticeIVR_CallerResponse_New'
		session['ivr2_returnOnHangup'] = 'MHLogin.DoctorCom.IVR.views_provider_v2.PracticeIVR_LeaveUrgentMsg_New'
		session['authenticated'] = True
		session.save()
		url = '/IVR/GetCallBackNumberV2/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085551234',
			'To': '+18004664411',
			'CallStatus': 'inprogress',
			'CallSid': '1300',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		calls = [
			mock.call.Response(),
			mock.call.Gather(
				action='/IVR/GetCallBackNumberV2/1/',
				finishOnKey='#',
				timeout=30,
				numDigits=12),
			mock.call.Gather().append(say(
				u'On the keypad, please enter your call back number including area code now. Then press pound.')),
			mock.call.Response().append(twilio.Gather()),
			mock.call.Redirect('/IVR/GetCallBackNumberV2/1/'),
			mock.call.Response().append(twilio.Redirect('/IVR/GetCallBackNumberV2/1/')),
			]
		twilio.assert_has_calls(calls)

	def test_getCallBackNumber_action1_goodnumber(self, twilio, say, play):
		"""
		practice get callback number action:
		callback step 1: got number; repeat the number and request confirmation
		"""
		digits = '4081239999'
		url = '/IVR/GetCallBackNumberV2/1/'
		path = 'http://testserver' + url
		post_vars = {
			'CallStatus': 'inprogress',
			'CallSid': '1310',
			'Digits': digits,
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)

		session = self.client.session
		session['ivr2_returnOnHangup'] = 'MHLogin.DoctorCom.IVR.views_practice_v2.PracticeIVR_LeaveRegularMsg_New'
		session['ivr2_state'] = 'PracticeIVR_LeaveRegularMsg_New'
		session['ivr2_callback_step'] = 1
		session.save()
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		calls = [
			mock.call.Response(),
			mock.call.Gather(action='/IVR/GetCallBackNumberV2/1/',
				finishOnKey='', numDigits=1),
			mock.call.Gather().append(say(
				u'Eye got ' + ' '.join(digits) + '. If this correct, '
				u'press one. Or press three to enter eh different number')),
			mock.call.Response().append(twilio.Gather()),
			mock.call.Redirect('/IVR/GetCallBackNumberV2/1/'),
			mock.call.Response().append(twilio.Redirect('/IVR/GetCallBackNumberV2/1/')),
			]
		twilio.assert_has_calls(calls)
		assert self.client.session['ivr2_callback_step'] == 2
		assert self.client.session['ivr2_state'] == 'PracticeIVR_LeaveRegularMsg_New'

	def test_getCallBackNumber_action1_noareacode(self, twilio, say, play):
		"""
		practice get callback number action:
		callback step 1: got number without areacode
		"""
		digits = '1239999'
		url = '/IVR/GetCallBackNumberV2/1/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085551234',
			'To': '+18004664411',
			'CallStatus': 'inprogress',
			'CallSid': '1311',
			'Digits': digits,
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		session = self.client.session
		session['ivr2_returnOnHangup'] = 'MHLogin.DoctorCom.IVR.views_practice_v2.PracticeIVR_LeaveRegularMsg_New'
		session['ivr2_callback_step'] = 1
		session['ivr2_state'] = 'PracticeIVR_CallerResponse_New'
		session.save()
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		# check number entered, check areacode variable
		calls = [
			mock.call.Response(),
			mock.call.Gather(action='/IVR/GetCallBackNumberV2/1/',
				finishOnKey='', numDigits=1),
			mock.call.Gather().append(say(
				u'Eye got ' + ' '.join(digits) + '. If this correct, '
				u'press one. Or press three to enter eh different number')),
			mock.call.Response().append(twilio.Gather()),
			mock.call.Redirect('/IVR/GetCallBackNumberV2/1/'),
			mock.call.Response().append(twilio.Redirect()),
			]
		twilio.assert_has_calls(calls)
		assert self.client.session['ivr2_callback_step'] == 2
		assert self.client.session['ivr2_state'] == 'PracticeIVR_CallerResponse_New'

	def test_getCallBackNumber_action1_5digits(self, twilio, say, play):
		"""
		practice get callback number action:
		callback step 1: got number 5 digits (not valid phone #)
		"""
		digits = '12345'
		url = '/IVR/GetCallBackNumberV2/1/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085551234',
			'To': '+18004664411',
			'CallSid': '1323',
			'CallStatus': 'inprogress',
			'Digits': digits
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		session = self.client.session
		session['ivr_urgent_flag'] = True
		session['ivr2_state'] = 'PracticeIVR_LeaveUrgentMsg_New'
		session['ivr2_callback_step'] = 1
		session.save()
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		calls = [
			mock.call.Response(),
			mock.call.Gather(
				action='/IVR/GetCallBackNumberV2/1/',
				finishOnKey='',
				numDigits=1,
				),
			mock.call.Gather().append(say(
				u'Eye got ' + ' '.join(digits) + ' . If this correct '
				u'press one. Or press three to enter eh different number')),
			mock.call.Response().append(twilio.Gather()),
			mock.call.Redirect('/IVR/GetCallBackNumberV2/1/'),
			mock.call.Response().append(twilio.Redirect()),
			]
		twilio.assert_has_calls(calls)
		assert self.client.session['ivr2_callback_step'] == 2
		assert self.client.session['ivr2_state'] == 'PracticeIVR_LeaveUrgentMsg_New'

	def test_getCallBackNumber_action1_badnumber(self, twilio, say, play):
		"""
		practice get callback number action:
		callback step 1: 13 digit number?
		"""
		digits = '1234567890123'
		url = '/IVR/GetCallBackNumberV2/1/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085551234',
			'To': '+18004664411',
			'CallStatus': 'inprogress',
			'CallSid': '1312',
			'Digits': digits,
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)

		session = self.client.session
		session['ivr2_returnOnHangup'] = 'MHLogin.DoctorCom.IVR.views_practice_v2.PracticeIVR_LeaveRegularMsg_New'
		session['ivr2_state'] = 'PracticeIVR_CallerResponse_New'
		session['ivr2_callback_step'] = 1
		session.save()
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		calls = [
			mock.call.Response(),
			mock.call.Gather(
				action='/IVR/GetCallBackNumberV2/1/',
				finishOnKey='',
				numDigits=1,
				),
			mock.call.Gather().append(say(
				u'Eye got ' + ' '.join(digits) + ' . If this correct '
				u'press one. Or press three to enter eh different number')),
			mock.call.Response().append(twilio.Gather()),
			mock.call.Redirect('/IVR/GetCallBackNumberV2/1/'),
			mock.call.Response().append(twilio.Redirect('/IVR/GetCallBackNumberV2/1/')),
			]
		twilio.assert_has_calls(calls)
		assert self.client.session['ivr2_callback_step'] == 2
		assert self.client.session['ivr2_state'] == 'PracticeIVR_CallerResponse_New'

	def test_getCallBackNumber_action1_badinput(self, twilio, say, play):
		"""
		practice get callback number action:
		callback step 1: bad digit, not a number
		"""
		url = '/IVR/GetCallBackNumberV2/1/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085551234',
			'To': '+18004664411',
			'CallStatus': 'inprogress',
			'CallSid': '1313',
			'Digits': '*',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)

		session = self.client.session
		session['ivr2_returnOnHangup'] = 'MHLogin.DoctorCom.IVR.views_practice_v2.PracticeIVR_LeaveRegularMsg_New'
		session['ivr2_state'] = 'PracticeIVR_CallerResponse_New'
		session['ivr2_callback_step'] = 1
		session.save()
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		calls = [
			mock.call.Response(),
			mock.call.Response().append(say('I am sorry, I did not get that')),
			mock.call.Gather(
				action='/IVR/GetCallBackNumberV2/1/',
				finishOnKey='#',
				timeout=30,
				numDigits=12,
				),
			mock.call.Gather().append(say(
				u'On the keypad, please enter your call back number including '
				u'area code now. Then press pound.')),
			mock.call.Response().append(twilio.Gather()),
			mock.call.Redirect('/IVR/GetCallBackNumberV2/1/'),
			mock.call.Response().append(twilio.Redirect()),
			]
		twilio.assert_has_calls(calls)
		assert self.client.session['ivr2_callback_step'] == 1
		assert self.client.session['ivr2_state'] == 'PracticeIVR_CallerResponse_New'

	def test_getCallBackNumber_action2_1(self, twilio, say, play):
		"""
		practice get callback number action:
		callback step 2: get user acceptance of correct callback number
		"""
		url = '/IVR/GetCallBackNumberV2/1/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085551234',
			'To': '+18004664411',
			'CallStatus': 'inprogress',
			'Digits': '1',
			'CallSid': '1320',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)

		session = self.client.session
		session['ivr2_urgent_flag'] = True
		session['ivr2_state'] = 'PracticeIVR_LeaveUrgentMsg_New'
		session['ivr2_sub_state'] = 'PracticeIVR_LeaveUrgentMsg_GetCallback'
		session['ivr2_Record_callbacknumber'] = '18005551234'
		session['ivr2_caller_id_area_code'] = '800'
		session['ivr2_callback_step'] = 2
		session.save()
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		calls = [
			mock.call.Response(),
			mock.call.Redirect('/IVR/PracticeV2/LeaveMsg/'),
			mock.call.Response().append(twilio.Redirect('/IVR/PracticeV2/LeaveMsg/')),
			]
		twilio.assert_has_calls(calls)
		assert self.client.session['ivr2_callback_step'] == 3
		assert self.client.session['ivr2_state'] == 'PracticeIVR_LeaveUrgentMsg_New'
		assert self.client.session['ivr2_sub_state'] == 'PracticeIVR_LeaveUrgentMsg_GetCallback'

	def test_getCallBackNumber_action2_3(self, twilio, say, play):
		"""
		practice get callback number action:
		callback step 2: get user rejection of number; repeat getting callback number
		"""
		url = '/IVR/GetCallBackNumberV2/1/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085551234',
			'To': '+18004664411',
			'CallStatus': 'inprogress',
			'Digits': '3',
			'CallSid': '1321',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)

		session = self.client.session
		session['ivr_urgent_flag'] = True
		session['ivr2_state'] = 'PracticeIVR_LeaveUrgentMsg_New'
		session['ivr2_callback_step'] = 2
		session['ivr2_Record_callbacknumber'] = '18005551234'
		session['ivr2_caller_id_area_code'] = '800'
		session.save()
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		calls = [
			mock.call.Response(),
			mock.call.Redirect('/IVR/GetCallBackNumberV2/1/'),
			mock.call.Response().append(twilio.Redirect('/IVR/GetCallBackNumberV2/1/')),
#			mock.call.Response().__str__()
			]
		twilio.assert_has_calls(calls)
		assert self.client.session['ivr2_callback_step'] == 1
		assert self.client.session['ivr2_state'] == 'PracticeIVR_LeaveUrgentMsg_New'

	def test_getCallBackNumber_action2_nodigits(self, twilio, say, play):
		"""
		practice get callback number action:
		callback step 2: user enter unexpected value (not 1 confirm or 3 reject)
		"""
		url = '/IVR/GetCallBackNumberV2/1/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085551234',
			'To': '+18004664411',
			'CallStatus': 'inprogress',
			'Digits': '#',
			'CallSid': '1322',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)

		session = self.client.session
		session['ivr_urgent_flag'] = True
		session['ivr2_state'] = 'PracticeIVR_LeaveUrgentMsg_New'
		session['ivr2_callback_step'] = 2
		session['ivr2_Record_callbacknumber'] = '18005551234'
		session['ivr2_caller_id_area_code'] = '800'
		session.save()
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		calls = [
			mock.call.Response(),
			mock.call.Response().append(say(u'I\'m sorry, I didn\'t understand that.')),
			mock.call.Gather(action='/IVR/GetCallBackNumberV2/1/',
				finishOnKey='#', timeout=30, numDigits=12),
			mock.call.Gather().append(say(
				u'On the keypad, please enter your call back number including area code now. Then press pound.')),
			mock.call.Response().append(twilio.Gather()),
			mock.call.Redirect('/IVR/GetCallBackNumberV2/1/'),
			mock.call.Response().append(twilio.Redirect()),
			]
		twilio.assert_has_calls(calls)
		assert self.client.session['ivr2_callback_step'] == 1
		assert self.client.session['ivr2_state'] == 'PracticeIVR_LeaveUrgentMsg_New'

