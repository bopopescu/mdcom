
import hmac
import mock
import os

from hashlib import sha1
from base64 import encodestring

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase, Client

from MHLogin.DoctorCom.IVR.models import VMBox_Config, callLog
from MHLogin.DoctorCom.models import Click2Call_Log
from MHLogin.MHLCallGroups.models import CallGroup
from MHLogin.MHLUsers.models import MHLUser, Provider, Administrator
from MHLogin.MHLPractices.models import PracticeLocation, OrganizationSetting
from MHLogin.KMS.models import OwnerPublicKey, UserPrivateKey
from MHLogin.KMS.utils import generate_keys_for_users
from MHLogin.utils.tests import create_user

# helper to generate signature for twilio validation
generate_sig = lambda path: encodestring(hmac.new(
	settings.TWILIO_ACCOUNT_TOKEN, path, sha1).digest()).strip()

devnull = open(os.devnull, 'w')


@mock.patch('MHLogin.DoctorCom.speech.utils.Play', autospec=True)
@mock.patch('MHLogin.DoctorCom.speech.utils.Say', autospec=True)
@mock.patch('MHLogin.DoctorCom.IVR.views_generic.twilio', autospec=True)
class TestIVRGeneric(TestCase):

	@classmethod
	def setUpClass(cls):
		# create a user to login creating a session needed by ivr tests
		cls.admin = create_user("ivrguy", "ivr", "guy", "demo", 
			"Ocean Avenue", "Carmel", "CA", "93921", uklass=Administrator)

	@classmethod
	def tearDownClass(cls):
		Administrator.objects.all().delete()
		MHLUser.objects.all().delete()
		OwnerPublicKey.objects.all().delete()
		UserPrivateKey.objects.all().delete()

	def setUp(self):
		# create a session
		self.client.post('/login/', {'username': self.admin.user.username, 
									'password': 'demo'})

	def tearDown(self):
		self.client.logout()

	def test_getCallBackNumber_completed(self, twilio, say, play):
		url = '/IVR/GetCallBackNumber/'
		path = 'http://testserver' + url  # TODO: figure out better way to do this
		post_vars = {
			'CallStatus': 'completed'
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)

		session = self.client.session
		session['ivr_has_number'] = True
		session['ivr_callback_returnOnHangup'] = '/all/done'
		session.save()
		response = self.client.post(url, post_vars, 
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)}) 
		self.assertEqual(response.status_code, 200)
		calls = [
			mock.call.Response(),
			]
		twilio.assert_has_calls(calls)

	def test_getCallBackNumber_make_recording(self, twilio, say, play):
		url = '/IVR/GetCallBackNumber/'
		path = 'http://testserver' + url  # TODO: figure out better way to do this
		post_vars = {
			'CallStatus': 'completed'
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)

		session = self.client.session
		session['ivr_has_number'] = True
		session['ivr_callback_returnOnHangup'] = \
			'MHLogin.DoctorCom.IVR.views_generic.UnaffiliatedNumber'
		session['ivr_makeRecording_callbacknumber'] = True
		session.save()
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		calls = [
			mock.call.Response(),
			mock.call.Response(),
			mock.call.Pause(),
			mock.call.Response().append(twilio.Pause()),
			mock.call.Response().append(say(
				u'You have called an inactive phone number affiliated with '
				u'doctorcom. Please visit us online at w w w dot m d com dot '
				u'com. Good bye.')),
			mock.call.Hangup(),
			mock.call.Response().append(twilio.Hangup()),
			]
		twilio.assert_has_calls(calls)

	def test_getCallBackNumber_urgent_1(self, twilio, say, play):
		url = '/IVR/GetCallBackNumber/'
		path = 'http://testserver' + url  # TODO: figure out better way to do this
		post_vars = {
			'CallStatus': 'in-progress',
			'Digits': '1'
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v) 

		session = self.client.session
		session['ivr_urgent_second_time'] = True
		session['ivr_call_stack'] = ['MHLogin.MHLogin_Main.views.main']
		session['ivr_makeRecording_callbacknumber'] = '18005551234'
		session['ivr_caller_id_area_code'] = '800'
		session.save()
		response = self.client.post(url, post_vars, 
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		calls = [
			mock.call.Response(),
			mock.call.Gather(
				action='/IVR/GetCallBackNumber/',
				finishOnKey='#',
				timeout=30,
				numDigits=12,
				),
			mock.call.Gather().append(say(
				u'On the keypad, please enter your call back number including '
				u'area code now. Then press pound.')),
			mock.call.Response().append(twilio.Gather()),
			mock.call.Redirect('/IVR/GetCallBackNumber/'),
			mock.call.Response().append(twilio.Redirect()),
			]
		twilio.assert_has_calls(calls)

	def test_getCallBackNumber_urgent_2(self, twilio, say, play):
		url = '/IVR/GetCallBackNumber/'
		path = 'http://testserver' + url  # TODO: figure out better way to do this
		post_vars = {
			'CallStatus': 'in-progress',
			'Digits': '1'
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v) 

		session = self.client.session
		session['ivr_urgent_second_time'] = True
		session['ivr_call_stack'] = ['MHLogin.MHLogin_Main.views.main']
		session.save()
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		calls = [
			mock.call.Response(),
			mock.call.Gather(
				action='/IVR/GetCallBackNumber/',
				finishOnKey='#',
				timeout=30,
				numDigits=12,
				),
			mock.call.Gather().append(say(
				u'On the keypad, please enter your call back number including '
				u'area code now. Then press pound.')),
			mock.call.Response().append(twilio.Gather()),
			mock.call.Redirect('/IVR/GetCallBackNumber/'),
			mock.call.Response().append(twilio.Redirect()),
			]
		twilio.assert_has_calls(calls)

	def test_getCallBackNumber_nodigits_1(self, twilio, say, play):
		url = '/IVR/GetCallBackNumber/'
		path = 'http://testserver' + url  # TODO: figure out better way to do this
		post_vars = {
			'CallStatus': 'in-progress',
			'Digits': '#'
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v) 

		session = self.client.session
		session['ivr_has_number'] = True
		session['ivr_makeRecording_callbacknumber'] = True
		session['ivr_call_stack'] = ['MHLogin.MHLogin_Main.views.main']
		session.save()
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		calls = [
			mock.call.Response(),
			mock.call.Response().append(say(u'I\'m sorry, I didn\'t understand that.')),
			mock.call.Redirect('/IVR/GetCallBackNumber/'),
			mock.call.Response().append(twilio.Redirect()),
			]
		twilio.assert_has_calls(calls)

	def test_getCallBackNumber_nodigits_2(self, twilio, say, play):
		url = '/IVR/GetCallBackNumber/'
		path = 'http://testserver' + url  # TODO: figure out better way to do this
		post_vars = {
			'CallStatus': 'in-progress',
			'Digits': '#'
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v) 

		session = self.client.session
		session['ivr_has_number'] = True
		session['ivr_makeRecording_callbacknumber'] = True
		session['ivr_call_stack'] = ['MHLogin.MHLogin_Main.views.main']
		session['ivr_caller_id_area_code'] = '800'
		session.save()
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		calls = [
			mock.call.Response(),
			mock.call.Response().append(say(u'I\'m sorry, I didn\'t understand that.')),
			mock.call.Redirect('/IVR/GetCallBackNumber/'),
			mock.call.Response().append(twilio.Redirect()),
			]
		twilio.assert_has_calls(calls)

	def test_getCallBackNumber_digit_1(self, twilio, say, play):
		url = '/IVR/GetCallBackNumber/'
		path = 'http://testserver' + url  # TODO: figure out better way to do this
		post_vars = {
			'CallStatus': 'in-progress',
			'Digits': '1'
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v) 

		session = self.client.session
		session['ivr_has_number'] = True
		session['ivr_makeRecording_callbacknumber'] = True
		session['ivr_call_stack'] = ['MHLogin.MHLogin_Main.views.main']
		session.save()
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		calls = [
			mock.call.Response(),
			mock.call.Redirect('/'),
			]
		twilio.assert_has_calls(calls)

	def test_getCallBackNumber_digit_3_1(self, twilio, say, play):
		url = '/IVR/GetCallBackNumber/'
		path = 'http://testserver' + url  # TODO: figure out better way to do this
		post_vars = {
			'CallStatus': 'in-progress',
			'Digits': '3'
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v) 

		session = self.client.session
		session['ivr_has_number'] = True
		session['ivr_makeRecording_callbacknumber'] = True
		session['ivr_call_stack'] = ['MHLogin.MHLogin_Main.views.main']
		session.save()
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		calls = [
			mock.call.Response(),
			mock.call.Redirect('/IVR/GetCallBackNumber/'),
			]
		twilio.assert_has_calls(calls)

	def test_getCallBackNumber_digit_3_2(self, twilio, say, play):
		url = '/IVR/GetCallBackNumber/'
		path = 'http://testserver' + url  # TODO: figure out better way to do this
		post_vars = {
			'CallStatus': 'in-progress',
			'Digits': '3'
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v) 

		session = self.client.session
		session['ivr_has_number'] = True
		session['ivr_makeRecording_callbacknumber'] = True
		session['ivr_call_stack'] = ['MHLogin.MHLogin_Main.views.main']
		session['ivr_caller_id_area_code'] = '800'
		session.save()
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		calls = [
			mock.call.Response(),
			mock.call.Redirect('/IVR/GetCallBackNumber/'),
			]
		twilio.assert_has_calls(calls)

	def test_getCallBackNumber_digit_9(self, twilio, say, play):
		url = '/IVR/GetCallBackNumber/'
		path = 'http://testserver' + url  # TODO: figure out better way to do this
		post_vars = {
			'CallStatus': 'in-progress',
			'Digits': '9'
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v) 

		digits = '12'
		session = self.client.session
		session['ivr_has_number'] = True
		session['ivr_makeRecording_callbacknumber'] = list(digits)
		session['ivr_call_stack'] = ['MHLogin.MHLogin_Main.views.main']
		session.save()
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		calls = [
			mock.call.Response(),
			mock.call.Response().append(say(u'I\'m sorry, I didn\'t understand that.')),
			mock.call.Gather(
				action='/IVR/GetCallBackNumber/',
				finishOnKey='',
				numDigits=1,
				),
			mock.call.Gather().append(say(
				u'Eye got ' + ' '.join(digits) + '. If this is correct, '
				u'press one. Or press three to enter eh different number')),
			mock.call.Response().append(twilio.Gather()),
			]
		twilio.assert_has_calls(calls)

	def test_getCallBackNumber_inprogress(self, twilio, say, play):
		digits = '12345'
		url = '/IVR/GetCallBackNumber/'
		path = 'http://testserver' + url  # TODO: figure out better way to do this
		post_vars = {
			'CallStatus': 'in-progress',
			'Digits': digits
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v) 

		session = self.client.session
		session['ivr_has_number'] = True
		session['ivr_call_stack'] = ['MHLogin.MHLogin_Main.views.main']
		session.save()
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		calls = [
			mock.call.Response(),
			mock.call.Gather(
				action='/IVR/GetCallBackNumber/',
				finishOnKey='',
				numDigits=1,
				),
			mock.call.Gather().append(say(
				u'Eye got ' + ' '.join(digits) + ' . If this is correct, '
				u'press one. Or press three to enter eh different number')),
			mock.call.Response().append(twilio.Gather()),
			mock.call.Redirect('/IVR/GetCallBackNumber/'),
			mock.call.Response().append(twilio.Redirect()),
			]
		twilio.assert_has_calls(calls)

	def test_unaffiliatedNumber(self, twilio, say, play):
		session = self.client.session
		session['ivr_call_stack'] = ['ProviderIVR_TreeRoot']
		session.save()
		url = "/IVR/Unaffiliated/"
		path = 'http://testserver' + url  # TODO: figure out better way to do this
		post_vars = {
			'CallStatus': 'connecting',
			'CallSid': '1234',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v) 
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		calls = [
			mock.call.Response(),
			mock.call.Pause(),
			mock.call.Response().append(twilio.Pause()),
			mock.call.Response().append(say(u'You have called an inactive phone number affiliated with ')),
			mock.call.Hangup(),
			mock.call.Response().append(twilio.Hangup()),
			]
		twilio.assert_has_calls(calls)

	def test_GetQuickRecording_1(self, twilio, say, play):
		session = self.client.session
		session['ivr_call_stack'] = ['ProviderIVR_TreeRoot']
		session['ivr_makeRecording_prompt'] = 'Please leave your message'
		session.save()
		url = '/IVR/GetQuickRecording/'
		path = 'http://testserver' + url  # TODO: figure out better way to do this
		post_vars = {
			'Caller': '+14085551234',
			'Called': '+18004664411',
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
			mock.call.Pause(length=1),
			mock.call.Response().append(twilio.Pause()),
			mock.call.Response().append('Please leave your message'),
			mock.call.Record(finishOnKey='1234567890*#',
				action='/IVR/GetQuickRecording/', timeout=6,
				playBeep=True, maxLength=5),
			mock.call.Response().append(twilio.Record()),
			mock.call.Redirect('/IVR/GetQuickRecording/'),
			mock.call.Response().append(twilio.Redirect()),
			]
		twilio.assert_has_calls(calls)

	def test_GetRecording_1(self, twilio, say, play):
		session = self.client.session
		session['ivr_call_stack'] = ['ProviderIVR_TreeRoot']
		session['ivr_makeRecording_prompt'] = 'Please leave your message'
		session['ivr2_Record_returnOnHangup'] = 'MHLogin.DoctorCom.IVR.views_provider.ProviderIVR_LeaveMsg'
		session['authenticated'] = True
		session.save()
		url = '/IVR/GetRecording/'
		path = 'http://testserver' + url  # TODO: figure out better way to do this
		post_vars = {
			'Caller': '+14085551234',
			'Called': '+18004664411',
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
			mock.call.Response().append('Please leave your message'),
			mock.call.Record(finishOnKey='1234567890*#', transcribe=False, 
				playBeep=True, timeout=5, maxLength=180, action='/IVR/GetRecording/'),
			mock.call.Response().append(twilio.Record()),
			mock.call.Redirect('/IVR/GetRecording/'),
			mock.call.Response().append(twilio.Redirect()),
			]
		twilio.assert_has_calls(calls)


class IVRProviderSetup(TestCase):
	@classmethod
	def setUpClass(cls):
		cls.provider = Provider.objects.create(username='healmeister', first_name='heal',
			last_name='meister', address1="555 Bryant St.", city="Palo Alto", state="CA", 
			lat=0.0, longit=0.0, office_lat=0.0, office_longit=0.0, is_active=True, 
			tos_accepted=True, mobile_confirmed=True, mdcom_phone='123', mobile_phone='456')
		cls.provider.set_password('demo')
		cls.provider.user = cls.provider  # for our unique prov-user reln
		cls.provider.save()
		# TESTING_KMS_INTEGRATION create keys
		generate_keys_for_users(output=devnull)

	@classmethod
	def tearDownClass(cls):
		Click2Call_Log.objects.all().delete()
		VMBox_Config.objects.all().delete()								
		MHLUser.objects.all().delete()
		Provider.objects.all().delete()
		OwnerPublicKey.objects.all().delete()
		UserPrivateKey.objects.all().delete()

	def test_setup_authenticate_and_starttreeroot(self):
		url = '/IVR/Provider/'
		path = 'http://testserver' + url  # TODO: figure out better way to do this
		post_vars = {
			'CallStatus': 'in-progress',
			'Caller': self.provider.mobile_phone,  # caller is calling his mdcom #
			'Called': self.provider.mdcom_phone,
			'CallSid': 'abc',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v) 
		c = self.client

		#### STEP 1 start clean slate, no vmbox config, no pin
		c.post(url, post_vars, **{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		# 'authenticated' not set to False in session, just not there
		self.assertTrue('authenticated' not in c.session)
		#### STEP 2 set PIN  (not authenticated)
		post_vars['Digits'] = '1234'
		url = '/IVR/ChangePin/'
		path = 'http://testserver' + url
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		c.post(url, post_vars, **{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertTrue('authenticated' not in c.session)
		#### STEP 3 VERIFY PIN (still not authenticated)
		c.post(url, post_vars, **{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertTrue('authenticated' not in c.session)
		#### STEP 4 Login with incorrect PIN (pin set, but login with incorrect)
		post_vars['Digits'] = '1235'
		url = '/IVR/Provider/'
		path = 'http://testserver' + url
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		c.post(url, post_vars, **{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertTrue('authenticated' not in c.session)
		#### STEP 5 Login with correct PIN and verify start of setup
		post_vars['Digits'] = '1234'
		path = 'http://testserver' + url
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		c.post(url, post_vars, **{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertTrue(c.session['ivr_setup_stage'] == 1) 
		#### STEP 6 configuration step - record name
		c.post(url, post_vars, **{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertTrue(c.session['ivr_setup_stage'] == 2) 
		#### STEP 7 configuration step - record greeting
		c.post(url, post_vars, **{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertTrue(c.session['ivr_setup_stage'] == 3) 
		#### STEP 8 complete configuration - verify we are authenticated and complete!
		c.post(url, post_vars, **{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertTrue('authenticated' in c.session) 
		self.assertTrue(c.session['authenticated'] == True)
		config = VMBox_Config.objects.get(id=c.session['config_id'])
		self.assertTrue(config.config_complete == True)
		#### STEP 9 start the tree root (say summary)
		post_vars.pop('Digits', None)
		path = 'http://testserver' + url
		for k, v in sorted(post_vars.items()):
			path += (k + v) 
		c.post(url, post_vars, **{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertTrue(config.config_complete == True)
		#### STEP 10 tree root (change setup)
		post_vars['Digits'] = '4'  # ProviderIVR_Options
		path = 'http://testserver' + url
		for k, v in sorted(post_vars.items()):
			path += (k + v) 
		c.post(url, post_vars, **{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertTrue(config.config_complete == True)

		#### TBI: Below is not real world as we directly post back to views 
		#### STEP 11 options 
		post_vars['Digits'] = '1'  # change name
		url = reverse('ProviderIVR_Options')
		path = 'http://testserver' + url
		for k, v in sorted(post_vars.items()):
			path += (k + v) 
		resp = c.post(url, post_vars, **{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertTrue('changeName' in resp.client.session['ivr_call_stack'])
		#### STEP 12 options 
		post_vars['Digits'] = '3'  # change greeting
		path = 'http://testserver' + url
		for k, v in sorted(post_vars.items()):
			path += (k + v) 
		resp = c.post(url, post_vars, **{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertTrue('changeGreeting' in resp.client.session['ivr_call_stack'])
		#### STEP 13 options 
		post_vars['Digits'] = '5'  # change pin
		path = 'http://testserver' + url
		for k, v in sorted(post_vars.items()):
			path += (k + v) 
		resp = c.post(url, post_vars, **{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		post_vars['Digits'] = '1234'  # change pin part2
		url = reverse('changePin')
		path = 'http://testserver' + url
		for k, v in sorted(post_vars.items()):
			path += (k + v) 
		resp = c.post(url, post_vars, **{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertTrue('ivr_changePin_hash' in resp.client.session)
		#### STEP 14 options 
		url = reverse('ProviderIVR_Options')
		post_vars['Digits'] = '9'  # main menu
		path = 'http://testserver' + url
		for k, v in sorted(post_vars.items()):
			path += (k + v) 
		resp = c.post(url, post_vars, **{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		#### STEP 15 play messages (when no messages verifies redmine 2048) 
		self.assertTrue('ivr_playMessages_newMessages' not in resp.client.session)		
		self.assertTrue('ivr_playMessages_oldMessages' not in resp.client.session)		
		for digit in ['1', '2', '*']:
			post_vars['Digits'] = digit
			url = '/IVR/Provider/'
			path = 'http://testserver' + url
			for k, v in sorted(post_vars.items()):
				path += (k + v)
			c.post(url, post_vars, **{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
			self.assertTrue('ivr_playMessages_newMessages' in resp.client.session)		
			self.assertTrue('ivr_playMessages_oldMessages' in resp.client.session)		


class IVRProviderAndPracticeCalls(TestCase):
	@classmethod
	def setUpClass(cls):
		cls.provider1 = Provider.objects.create(username='healmeister', first_name='heal',
			last_name='meister', address1="555 Bryant St.", city="Palo Alto", state="CA", 
			lat=0.0, longit=0.0, office_lat=0.0, office_longit=0.0, is_active=True, 
			tos_accepted=True, mobile_confirmed=True, mdcom_phone='777', mobile_phone='666')
		cls.provider1.set_password('demo')
		cls.provider1.user = cls.provider1  # for our unique prov-user reln
		cls.provider1.save()
		cls.provider2 = Provider.objects.create(username='docholiday', first_name='doc',
			last_name='holiday', address1="123 Main St.", city="Tombstone", state="AZ", 
			lat=0.0, longit=0.0, office_lat=0.0, office_longit=0.0, is_active=True, 
			tos_accepted=True, mobile_confirmed=True, mdcom_phone='999', mobile_phone='888')
		cls.provider2.set_password('demo')
		cls.provider2.user = cls.provider2  # for our unique prov-user reln
		cls.provider2.save()
		cls.call_group = CallGroup.objects.create(description='test', team='team')
		org_setting = OrganizationSetting(can_have_answering_service=True)
		org_setting.save()
		cls.practice = PracticeLocation.objects.create(practice_name='The MRC Gang',
			practice_phone='765', mdcom_phone='909', pin='1234', name_greeting='hello',
			greeting_closed='we are closed', greeting_lunch='its lunch time', 
			config_complete=False, practice_lat=0.0, practice_longit=0.0, 
			time_zone='UTC', call_group=cls.call_group, organization_setting=org_setting)
		# TESTING_KMS_INTEGRATION create keys
		generate_keys_for_users(output=devnull)
		# setup to get us going
		cls.setup_IVR_for_providers()
		cls.setup_IVR_for_practice()

	@classmethod
	def tearDownClass(cls):
		Click2Call_Log.objects.all().delete()
		VMBox_Config.objects.all().delete()								
		MHLUser.objects.all().delete()
		Provider.objects.all().delete()
		callLog.objects.all().delete()
		PracticeLocation.objects.all().delete()
		OrganizationSetting.objects.all().delete()
		OwnerPublicKey.objects.all().delete()
		UserPrivateKey.objects.all().delete()

	@classmethod
	def setup_IVR_for_providers(cls):
		""" Helper to get us going with 2 providers """
		provs = ((cls.provider1, '3333', '6666'), (cls.provider2, '4444', '7777'))
		for (prov, pin, sid) in provs:
			c = prov.client = Client()
			url = '/IVR/Provider/'
			path = 'http://testserver' + url
			post_vars = {
				'CallStatus': 'in-progress',
				'Caller': prov.mobile_phone,  # caller is calling his mdcom #
				'Called': prov.mdcom_phone,   # to setup first time (part of test)
				'CallSid': sid,
				}
			for k, v in sorted(post_vars.items()):
				path += (k + v) 
			#### STEP 1 start clean slate, no vmbox config, no pin
			resp = c.post(url, post_vars, **{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
			# 'authenticated' not set to False in session, just not there
			assert('authenticated' not in resp.client.session)  # no class assert
			#### STEP 2 set PIN  (not authenticated)
			post_vars['Digits'] = pin
			url = '/IVR/ChangePin/'
			path = 'http://testserver' + url
			for k, v in sorted(post_vars.items()):
				path += (k + v)
			resp = c.post(url, post_vars, **{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
			assert('authenticated' not in resp.client.session)
			#### STEP 3 VERIFY PIN (still not authenticated)
			resp = c.post(url, post_vars, **{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
			assert('authenticated' not in resp.client.session)
			#### STEP 4 Login with correct PIN and verify start of setup
			url = '/IVR/Provider/'
			path = 'http://testserver' + url
			for k, v in sorted(post_vars.items()):
				path += (k + v)
			resp = c.post(url, post_vars, **{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
			assert(resp.client.session['ivr_setup_stage'] == 1) 
			#### STEP 5 configuration step - record name
			resp = c.post(url, post_vars, **{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
			assert(resp.client.session['ivr_setup_stage'] == 2) 
			#### STEP 6 configuration step - record greeting
			resp = c.post(url, post_vars, **{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
			assert(resp.client.session['ivr_setup_stage'] == 3) 
			#### STEP 7 complete configuration - verify we are authenticated and complete!
			resp = c.post(url, post_vars, **{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
			assert(resp.client.session['authenticated'] == True)
			config = VMBox_Config.objects.get(id=resp.client.session['config_id'])
			# TODO: ProviderIVR_ForwardCall() requires name or key error ivr_makeRecording_recording
			config.name, config.greeting = prov.first_name, 'http://greeting'
			config.save()
			assert(config.config_complete == True)

	@classmethod
	def setup_IVR_for_practice(cls):
		c = Client()
		#### start practice setup
		url = '/IVR/Practice/'
		path = 'http://testserver' + url
		post_vars = {
			'CallStatus': 'in-progress',
			'Caller': cls.practice.practice_phone,
			'Called': cls.practice.mdcom_phone,
			'CallSid': 'abcdef',
			'Digits': cls.practice.pin,
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		assert(cls.practice.config_complete == False)
		#### STEP 1 configuration step - change pin
		resp = c.post(url, post_vars, **{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		assert(resp.client.session['ivr_setup_stage'] == 1)
		#### STEP 2 configuration step - record name
		resp = c.post(url, post_vars, **{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		assert(resp.client.session['ivr_setup_stage'] == 2)
		#### STEP 3 configuration step - change greeting
		resp = c.post(url, post_vars, **{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		assert(resp.client.session['ivr_setup_stage'] == 3)
		#### STEP 4 configuration step - change greeting part2
		resp = c.post(url, post_vars, **{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		assert(resp.client.session['ivr_setup_stage'] == 4)
		#### STEP 5 configuration step - finish up
		resp = c.post(url, post_vars, **{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		assert(PracticeLocation.objects.get(id=cls.practice.id).config_complete == True)

	def test_provider2_call_provider1_mobile(self):
		c = self.provider2.client
		url = '/IVR/Provider/'
		path = 'http://testserver' + url
		post_vars = {
			'CallStatus': 'in-progress',
			'Caller': self.provider2.mobile_phone,  # mobile caller provider2 calling 
			'Called': self.provider1.mdcom_phone,   # calling provider1 mdcom phone
			'CallSid': '12345678',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v) 
		#### provider2 call provider1 forwards to mobile
		self.provider1.forward_voicemail = 'MO'
		self.provider1.save()
		resp = c.post(url, post_vars, **{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		#### verify session in 'Dialed' state
		self.assertTrue(resp.client.session['ProviderIVR_ForwardCall_state'] == 'Dialed')
		#### provider1 picks up phone 
		url = reverse('ProviderIVR_ForwardCall_VetAnswer')
		path = 'http://testserver' + url
		for k, v in sorted(post_vars.items()):
			path += (k + v) 
		resp = c.post(url, post_vars, **{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		#### provider1 presses a key  
		post_vars['Digits'] = '1'  # provider1 presses 1 key
		url = reverse('ProviderIVR_ForwardCall_VetAnswer')
		path = 'http://testserver' + url
		for k, v in sorted(post_vars.items()):
			path += (k + v) 
		resp = c.post(url, post_vars, **{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		log = callLog.objects.get(callSID=post_vars['CallSid'])
		#### verify we connected caller <--> callee  
		self.assertTrue(log.call_connected == True)

	def test_provider2_call_provider1_vm(self):
		c = self.provider2.client
		url = '/IVR/Provider/'
		path = 'http://testserver' + url
		post_vars = {
			'CallStatus': 'in-progress',
			'Caller': self.provider2.mobile_phone,  # mobile caller provider2 calling 
			'Called': self.provider1.mdcom_phone,   # calling provider1 mdcom phone
			'CallSid': '12345678',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v) 
		#### provider2 call provider1 forwards to voice mailbox
		self.provider1.forward_voicemail = 'VM'
		self.provider1.save()
		resp = c.post(url, post_vars, **{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		#### verify provider2 leaving provider1 a voicemail
		self.assertTrue('ivr_makeRecording_prompt' in resp.client.session)
		self.assertTrue('ProviderIVR_LeaveMsg' in resp.client.session['ivr_call_stack'])

	def test_stranger_call_provider1_vm(self):
		c = self.provider2.client
		url = '/IVR/Provider/'
		path = 'http://testserver' + url
		post_vars = {
			'CallStatus': 'in-progress',
			'Caller': '5551212',  # random mobile caller provider2 calling 
			'Called': self.provider1.mdcom_phone,  # calling provider1 mdcom phone
			'CallSid': '82345671',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v) 
		#### stranger calling provider1 forwards to mobile
		self.provider1.forward_voicemail = 'MO'
		self.provider1.save()
		resp = c.post(url, post_vars, **{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		#### verify stranger getting quickrecording
		self.assertTrue(resp.client.session['getQuickRecording_subsequentExcecution'] == True)

	def test_provider1_call_practice(self):
		c = self.provider2.client
		url = '/IVR/Practice/'
		path = 'http://testserver' + url
		post_vars = {
			'CallStatus': 'in-progress',
			'Caller': self.provider1.mobile_phone,  # mobile caller provider2 calling 
			'Called': self.practice.mdcom_phone,    # calling practice mdcom phone
			'CallSid': '98765',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v) 
		#### provider1 call practice forwards to voice mailbox
		resp = c.post(url, post_vars, **{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		#### verify provider1 leaving practice a voicemail
		self.assertTrue(resp.client.session['practice_id'] == self.practice.id)
		self.assertTrue(resp.client.session['practice_phone'] == self.practice.practice_phone)
		#### verify provider1 call practice enters digits
		post_vars['Digits'] = '1'
		path = 'http://testserver' + url
		for k, v in sorted(post_vars.items()):
			path += (k + v) 
		resp = c.post(url, post_vars, **{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		#### verify provider1 leaving practice a voicemail
		self.assertTrue(resp.client.session['practice_id'] == self.practice.id)
		self.assertTrue(resp.client.session['practice_phone'] == self.practice.practice_phone)
		#### verify call status complete
		post_vars['CallStatus'] = 'completed'
		post_vars['Duration'] = '5'
		path = 'http://testserver' + url
		for k, v in sorted(post_vars.items()):
			path += (k + v) 
		resp = c.post(url, post_vars, **{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		# TODO: bug in PracticeIVR_Main setting attribute duration instead of call_duration
#		self.assertTrue(callLog.objects.get(callSID=post_vars['CallSid']).\
#					call_duration == post_vars['Duration'])



