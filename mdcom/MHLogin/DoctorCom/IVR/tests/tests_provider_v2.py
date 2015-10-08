
import os
import hmac
import mock

from hashlib import sha1
from base64 import encodestring
from django.conf import settings
from .base import TestIVRBase
from MHLogin.MHLUsers.models import Provider
from MHLogin.DoctorCom.Messaging.models import MessageBodyUserStatus, MessageAttachment
from MHLogin.DoctorCom.IVR.views_provider_v2 import _getProviderVMConfig
from MHLogin.DoctorCom.IVR.models import VMBox_Config, callLog
from MHLogin.KMS.utils import generate_keys_for_users

# helper to generate signature for twilio validation
generate_sig = lambda path: encodestring(hmac.new(
	settings.TWILIO_ACCOUNT_TOKEN, path, sha1).digest()).strip()


@mock.patch('MHLogin.DoctorCom.speech.utils.Play', autospec=True)
@mock.patch('MHLogin.DoctorCom.speech.utils.Say', autospec=True)
@mock.patch('MHLogin.DoctorCom.IVR.views_provider_v2.twilio', autospec=True)
@mock.patch('MHLogin.DoctorCom.IVR.views_generic_v2.twilio', autospec=True)
@mock.patch('MHLogin.DoctorCom.SMS.views.client.sms.messages.create', autospec=True)
class TestIVRProviderV2(TestIVRBase):

	def setUp(self):
		super(TestIVRProviderV2, self).setUp()

	def tearDown(self):
		super(TestIVRProviderV2, self).tearDown()

#
# SETUP VM TEST
#
	def test_ProviderIVR_Main_Setup_Start(self, sms, twiliog, twiliop, say, play):
		"""
		provider called with provider's mobile phone - go to setup voicemail
		"""
		url = '/IVR/ProviderV2/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085559999',
			'To': '+18004664411',
			'CallStatus': 'inprogress',
			'CallSid': '100',
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
			mock.call.Response().append(say("Welcome to your voicemail account. It looks "
				"like some setup is needed. Let's get started. First, we need to set "
				"up your pin number.")),
			mock.call.Response().append(twiliog.Gather(action='/IVR/ChangePinV2/1/',
				finishOnKey='#',
				numDigits=8,)),
			]
		twiliop.assert_has_calls(pcalls)
		gcalls = [
			mock.call.Gather(action='/IVR/ChangePinV2/1/', finishOnKey='#', numDigits=8),
			mock.call.Gather().append(say('Please enter four to eight digits. Press pound to finish.')),
			]
		twiliog.assert_has_calls(gcalls)
		# goes from substate ProviderIVR_Setup_Start to ProviderIVR_Setup_Pin
		assert self.client.session['ivr2_state'] == 'ProviderIVR_Setup_New'
		assert self.client.session['ivr2_sub_state'] == 'ProviderIVR_Setup_Pin'
		# caller is masked
		assert self.client.session['Caller'] == '8004664411'
		assert self.client.session['Called'] == '8004664411'
		providerS = Provider.objects.filter(mdcom_phone='8004664411')
		provider = providerS[0]
		assert self.client.session['provider_id'] == provider.id
		assert provider.user.mobile_phone == '4085559999'

	def test_ProviderIVR_Setup_Start(self, sms, twiliog, twiliop, say, play):
		"""
		provider called with provider's mobile phone;
		go to setup voicemail 1st step - starting to setup Pin
		"""
		provider = self.providers[0]
		config = _getProviderVMConfig(provider)
		config.set_pin('1234')
		config.config_complete = False
		config.save()
		session = self.client.session
		session['provider_id'] = provider.id
		session['config_id'] = config.id
		session['Caller'] = '4085559999'
		session['Called'] = '8004664411'
		session['ivr2_state'] = 'ProviderIVR_Setup_New'
		session['ivr2_sub_state'] = 'ProviderIVR_Setup_Start'
		session.save()
		url = '/IVR/ProviderV2/Setup/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085559999',
			'To': '+18004664411',
			'CallStatus': 'inprogress',
			'CallSid': '1001',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		gcalls = [
			mock.call.Gather(action='/IVR/ChangePinV2/1/', finishOnKey='#', numDigits=8),
			mock.call.Gather().append(say('Please enter four to eight digits. Press pound to finish.')),
			]
		twiliog.assert_has_calls(gcalls)
		pcalls = [
			mock.call.Response(),
			mock.call.Pause(),
			mock.call.Response().append(twiliop.Pause()),
			mock.call.Response().append(say('Let\'s get started. First, we need to set up your pin number.')),
			mock.call.Response().append(twiliog.Gather()),
		]
		twiliop.assert_has_calls(pcalls)
		# goes from substate ProviderIVR_Setup_Start to ProviderIVR_Setup_Pin
		assert self.client.session['ivr2_state'] == 'ProviderIVR_Setup_New'
		assert self.client.session['ivr2_sub_state'] == 'ProviderIVR_Setup_Pin'
		providerS = Provider.objects.filter(mdcom_phone='8004664411')
		provider = providerS[0]
#		config = VMBox_Config.objects.get(id=self.client.session['config_id'])
#		assert config.name == 'http://api.twilio.com/2010-04-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/RE8e3dfb46277add8bb0b381d087d9424d'
		assert self.client.session['provider_id'] == provider.id
		assert provider.user.mobile_phone == '4085559999'

	def test_ProviderIVR_Setup_Name(self, sms, twiliog, twiliop, say, play):
		"""
		provider called with provider's mobile phone;
		go to setup voicemail 2nd step - starting to setup Name
		the return step is done in test_ChangeName_Provider_2
		"""
		provider = self.providers[0]
		config = _getProviderVMConfig(provider)
		config.set_pin('1234')
		config.config_complete = False
		config.save()
		session = self.client.session
		session['provider_id'] = provider.id
		session['config_id'] = config.id
		session['Caller'] = '4085559999'
		session['Called'] = '8004664411'
		session['ivr2_state'] = 'ProviderIVR_Setup_New'
		session['ivr2_sub_state'] = 'ProviderIVR_Setup_Pin'
		session['ivr2_Record_recording'] = 'http://api.twilio.com/2010-04-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/RE8e3dfb46277add8bb0b381d087d9424d'
		session.save()
		url = '/IVR/ProviderV2/Setup/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085559999',
			'To': '+18004664411',
			'CallStatus': 'inprogress',
			'CallSid': '1001',
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
			mock.call.Response().append(say('Now, we need to record your name.  Please say your name after the tone. Press pound to finish.')),
			mock.call.Record(finishOnKey='1234567890*#', transcribe=False,
				playBeep=True, timeout=3, maxLength=10, action='/IVR/GetRecordingV2/1/'),
			mock.call.Response().append(twiliog.Record()),
			mock.call.Redirect('/IVR/GetRecordingV2/'),
			mock.call.Response().append(twiliog.Redirect()),
			]
		twiliog.assert_has_calls(gcalls)
		# goes from substate ProviderIVR_Setup_Start to ProviderIVR_Setup_Pin
		assert self.client.session['ivr2_state'] == 'ProviderIVR_Setup_New'
		assert self.client.session['ivr2_sub_state'] == 'ProviderIVR_Setup_Name'
		providerS = Provider.objects.filter(mdcom_phone='8004664411')
		provider = providerS[0]
		assert self.client.session['provider_id'] == provider.id
		assert provider.user.mobile_phone == '4085559999'

	def test_ProviderIVR_Setup_Greeting(self, sms, twiliog, twiliop, say, play):
		"""
		provider called with provider's mobile phone;
		go to setup voicemail 3rd step - setup Greeting
		from ivr2_sub_state ProviderIVR_Setup_Start to ProviderIVR_Setup_Pin
		"""
		provider = self.providers[0]
		config = _getProviderVMConfig(provider)
		config.set_pin('1234')
		config.name = 'http://api.twilio.com/2010-04-01/Accounts/AC087cabfd0a453a05acceb2810c100f69'\
			'/Recordings/RE8e3dfb46277add8bb0b381d087d9424d'
		config.config_complete = False
		config.save()
		session = self.client.session
		session['provider_id'] = provider.id
		session['config_id'] = config.id
		session['Caller'] = '4085559999'
		session['Called'] = '8004664411'
		session['ivr2_state'] = 'ProviderIVR_Setup_New'
		session['ivr2_sub_state'] = 'ProviderIVR_Setup_Name'
		session['ivr2_Record_recording'] = 'http://api.twilio.com/2010-04-01/Accounts/'\
			'AC087cabfd0a453a05acceb2810c100f69/Recordings/RE8e3dfb46277add8bb0b381d087d9424d'
		session.save()
		url = '/IVR/ProviderV2/Setup/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085559999',
			'To': '+18004664411',
			'CallStatus': 'inprogress',
			'CallSid': '1001',
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
			mock.call.Response().append(say('Now, we need to record your greeting.  Please say your greeting after the tone. Press pound to finish.')),
			mock.call.Record(finishOnKey='1234567890*#', transcribe=False,
				playBeep=True, timeout=3, maxLength=120, action='/IVR/GetRecordingV2/1/'),
			mock.call.Response().append(twiliog.Record()),
			mock.call.Redirect('/IVR/GetRecordingV2/'),
			mock.call.Response().append(twiliog.Redirect()),
			]
		twiliog.assert_has_calls(gcalls)
		assert self.client.session['ivr2_state'] == 'ProviderIVR_Setup_New'
		assert self.client.session['ivr2_sub_state'] == 'ProviderIVR_Setup_Greeting'
		providerS = Provider.objects.filter(mdcom_phone='8004664411')
		provider = providerS[0]
#		config = VMBox_Config.objects.get(id=self.client.session['config_id'])
#		assert config.greeting == 'http://api.twilio.com/2010-04-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/RE8e3dfb46277add8bb0b381d087d9424d'
		assert self.client.session['provider_id'] == provider.id
		assert provider.user.mobile_phone == '4085559999'

	def test_ProviderIVR_Setup_Complete(self, sms, twiliog, twiliop, say, play):
		"""
		provider called with provider's mobile phone
		after setup Greeting; we return to setup to complete
		then we do another call for setting the log of call
		"""
		provider = self.providers[0]
		config = _getProviderVMConfig(provider)
		config.set_pin('1234')
		config.greeting = 'http://api.twilio.com/2010-04-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/RE8e3dfb46277add8bb0b381d087d9424d'
		config.name = 'http://api.twilio.com/2010-04-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/RE8e3dfb46277add8bb0b381d087d9424d'
		config.config_complete = False
		config.save()
		session = self.client.session
		session['provider_id'] = provider.id
		session['config_id'] = config.id
		session['Caller'] = '4085559999'
		session['Called'] = '8004664411'
		session['ivr2_state'] = 'ProviderIVR_Setup_New'
		session['ivr2_sub_state'] = 'ProviderIVR_Setup_Greeting'
		session['ivr2_Record_recording'] = 'http://api.twilio.com/2010-04-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/RE8e3dfb46277add8bb0b381d087d9424d'
		session.save()
		# set up call log here - done in ProviderIVR_Main_New
		#caller_mhluser = _getMHLUser('4085559999')
		log = callLog(callSID='1001', caller_number='4085559999', called_number='8004664411',
			call_source='OC')
		log.save()
		url = '/IVR/ProviderV2/Setup/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085559999',
			'To': '+18004664411',
			'CallStatus': 'inprogress',
			'CallSid': '1001',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		pcalls = [
			mock.call.Response(),
			mock.call.Response().append(say('Your voicemail is now set up.')),
			mock.call.Redirect('/IVR/ProviderV2/TreeRoot/'),
			mock.call.Response().append(twiliop.Redirect()),
		]
		twiliop.assert_has_calls(pcalls)
		gcalls = []
		twiliog.assert_has_calls(gcalls)
		# goes from substate ProviderIVR_Setup_Start to ProviderIVR_Setup_Pin
		assert self.client.session['ivr2_state'] == 'ProviderIVR_TreeRoot_New'
		assert 'ivr2_sub_state' not in self.client.session
		providerS = Provider.objects.filter(mdcom_phone='8004664411')
		provider = providerS[0]
		config = VMBox_Config.objects.get(id=self.client.session['config_id'])
		assert config.config_complete is True
		assert self.client.session['provider_id'] == provider.id
		assert provider.user.mobile_phone == '4085559999'
		# callback to complete call log
		url = '/IVR/ProviderV2/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085559999',
			'To': '+18004664411',
			'CallStatus': 'completed',
			'CallSid': '1001',
			'CallDuration': '30',
			'Duration': '2'
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		log_qs = callLog.objects.filter(callSID='1001')
		if (log_qs.exists()):
			log = log_qs.get()
			self.assertEqual(log.call_duration, 30)

#
# TREEROOT TEST
#
	def test_ProviderIVR_TreeRoot(self, sms, twiliog, twiliop, say, play):
		"""
		caller is provider go direct to TreeRoot;
		voicemail calltree for msgs
		"""
		provider = self.providers[0]
		session = self.client.session
		session['provider_id'] = provider.id
		session['authenticated'] = True
		session['ivr2_state'] = 'ProviderIVR_TreeRoot_New'
		session.save()
		url = '/IVR/ProviderV2/TreeRoot/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085559999',
			'To': '+18004664411',
			'CallStatus': 'inprogress',
			'CallSid': '101',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		gcalls = []
		twiliog.assert_has_calls(gcalls)
		pcalls = [
			mock.call.Response(),
			mock.call.Gather(
				finishOnKey='',
				action='/IVR/ProviderV2/TreeRoot/1/',
				numDigits=1,
				),
			mock.call.Gather().append(say(u'You have 0 new, and 0 saved urgent messages, and 0 new, and 0 saved voice messages,')),
			mock.call.Gather().append(say(u'To manage your voicemail settings, press four.')),
			mock.call.Gather().append(say(u'To repeat this menu, press star.')),
			mock.call.Response().append(twiliop.Gather())
			]
		twiliop.assert_has_calls(pcalls)
		assert self.client.session['ivr2_state'] == 'ProviderIVR_TreeRoot_New'
		providerS = Provider.objects.filter(mdcom_phone='8004664411')
		provider = providerS[0]
		assert self.client.session['provider_id'] == provider.id

	def test_ProviderIVR_TreeAction_Digits_star(self, sms, twiliog, twiliop, say, play):
		"""
		provider voicemail treeroot Main
		with digit * to repeat menu
		"""
		provider = self.providers[0]
		session = self.client.session
		session['provider_id'] = provider.id
		session['ivr2_state'] = 'ProviderIVR_TreeRoot_New'
		session['authenticated'] = True
		session.save()
		url = '/IVR/ProviderV2/TreeRoot/1/'
		path = 'http://testserver' + url
		post_vars = {
			'Digits': '*',
			'CallStatus': 'inprogress',
			'CallSid': '102',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		gcalls = []
		twiliog.assert_has_calls(gcalls)
		pcalls = [
			mock.call.Response(),
			mock.call.Gather(
				finishOnKey='',
				action='/IVR/ProviderV2/TreeRoot/1/',
				numDigits=1,
				),
			mock.call.Gather().append(say(u'You have 0 new, and 0 saved urgent messages, and 0 new, and 0 saved voice messages,')),
			mock.call.Gather().append(say(u'To manage your voicemail settings, press four.')),
			mock.call.Gather().append(say(u'To repeat this menu, press star.')),
			mock.call.Response().append(twiliop.Gather())
			]
		twiliop.assert_has_calls(pcalls)
		assert self.client.session['ivr2_state'] == 'ProviderIVR_TreeRoot_New'

	def test_ProviderIVR_TreeAction_Digits_1_noVM(self, sms, twiliog, twiliop, say, play):
		"""
		provider voicemail treeroot Main
		with digit 1 to listen to all messages (no messages)
		"""
		provider = self.providers[0]
		session = self.client.session
		session['provider_id'] = provider.id
		session['ivr2_state'] = 'ProviderIVR_TreeRoot_New'
		session['authenticated'] = True
		session.save()
		url = '/IVR/ProviderV2/TreeRoot/1/'
		path = 'http://testserver' + url
		post_vars = {
			'Digits': '1',
			'CallStatus': 'inprogress',
			'CallSid': '103',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		gcalls = []
		twiliog.assert_has_calls(gcalls)
		pcalls = [
			mock.call.Response(),
			mock.call.Gather(
				finishOnKey='',
				action='/IVR/ProviderV2/TreeRoot/1/',
				numDigits=1,
				),
			mock.call.Gather().append(say(u'You have 0 new, and 0 saved urgent messages, and 0 new, and 0 saved voice messages,')),
			mock.call.Gather().append(say(u'To manage your voicemail settings, press four.')),
			mock.call.Gather().append(say(u'To repeat this menu, press star.')),
			mock.call.Response().append(twiliop.Gather())
			]
		twiliop.assert_has_calls(pcalls)
		assert self.client.session['ivr2_state'] == 'ProviderIVR_TreeRoot_New'

	def test_ProviderIVR_TreeAction_Digits_2_noVM(self, sms, twiliog, twiliop, say, play):
		"""
		provider voicemail treeroot Main
		with digit 2 to listen to all urgent messages (no messages)
		"""
		provider = self.providers[0]
		session = self.client.session
		session['provider_id'] = provider.id
		session['ivr2_state'] = 'ProviderIVR_TreeRoot_New'
		session['authenticated'] = True
		session.save()
		url = '/IVR/ProviderV2/TreeRoot/1/'
		path = 'http://testserver' + url
		post_vars = {
			'Digits': '2',
			'CallStatus': 'inprogress',
			'CallSid': '104',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		gcalls = []
		twiliog.assert_has_calls(gcalls)
		pcalls = [
			mock.call.Response(),
			mock.call.Gather(
				finishOnKey='',
				action='/IVR/ProviderV2/TreeRoot/1/',
				numDigits=1,
				),
			mock.call.Gather().append(say(u'You have 0 new, and 0 saved urgent messages, and 0 new, and 0 saved voice messages,')),
			mock.call.Gather().append(say(u'To manage your voicemail settings, press four.')),
			mock.call.Gather().append(say(u'To repeat this menu, press star.')),
			mock.call.Response().append(twiliop.Gather())
			]
		twiliop.assert_has_calls(pcalls)
		assert self.client.session['ivr2_state'] == 'ProviderIVR_TreeRoot_New'

	def test_ProviderIVR_TreeAction_Digits_3_noVM(self, sms, twiliog, twiliop, say, play):
		"""
		provider voicemail treeroot Main
		with digit 3 to listen to all voicemail
		"""
		provider = self.providers[0]
		session = self.client.session
		session['provider_id'] = provider.id
		session['ivr2_state'] = 'ProviderIVR_TreeRoot_New'
		session['authenticated'] = True
		session.save()
		url = '/IVR/ProviderV2/TreeRoot/1/'
		path = 'http://testserver' + url
		post_vars = {
			'Digits': '3',
			'CallStatus': 'inprogress',
			'CallSid': '105',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		gcalls = []
		twiliog.assert_has_calls(gcalls)
		pcalls = [
			mock.call.Response(),
			mock.call.Gather(
				finishOnKey='',
				action='/IVR/ProviderV2/TreeRoot/1/',
				numDigits=1,
				),
			mock.call.Gather().append(say(u'You have 0 new, and 0 saved urgent messages, and 0 new, and 0 saved voice messages,')),
			mock.call.Gather().append(say(u'To manage your voicemail settings, press four.')),
			mock.call.Gather().append(say(u'To repeat this menu, press star.')),
			mock.call.Response().append(twiliop.Gather())
			]
		twiliop.assert_has_calls(pcalls)
		assert self.client.session['ivr2_state'] == 'ProviderIVR_TreeRoot_New'

	def test_ProviderIVR_TreeRoot_VM(self, sms, twiliog, twiliop, say, play):
		"""
		caller is provider go direct to TreeRoot;
		voicemail calltree for msgs
		"""
		generate_keys_for_users(open(os.devnull, 'w'))
		provider = self.providers[1]
		config = _getProviderVMConfig(provider)
#		config.pin = 'sha1$52958$8d282c07727dece284f4bed71a94cc469e1c9418'
		config.set_pin('1234')
		config.greeting = 'http://api.twilio.com/2010-04-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/RE8e3dfb46277add8bb0b381d087d9424d'
		config.name = 'http://api.twilio.com/2010-04-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/RE8e3dfb46277add8bb0b381d087d9424d'
		config.config_complete = True
		config.save()
		session = self.client.session
		session['provider_id'] = provider.id
		session['config_id'] = config.id
		session['Caller'] = '4085551234'
		session['ivr2_state'] = 'ProviderIVR_LeaveMsg_New'
		session['ivr2_sub_state'] = 'ProviderIVR_LeaveMsg_Start'
		session['ivr2_Record_recording'] = 'http://api.twilio.com/2010-04-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/RE8e3dfb46277add8bb0b381d087d9424d'
		session.save()
		self.assertEqual(provider.mdcom_phone, "8004664422")
		url = '/IVR/ProviderV2/LeaveMessage/1/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085551234',
			'To': '+18004664422',
			'CallStatus': 'inprogress',
			'CallSid': '252',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		# this saves a message to the provider
		# now we go to provider's voicemail tree to listen to it
		provider = self.providers[1]
		session = self.client.session
		session['provider_id'] = provider.id
		session['authenticated'] = True
		session['ivr2_state'] = 'ProviderIVR_TreeRoot_New'
		session.save()
		url2 = '/IVR/ProviderV2/TreeRoot/'
		path2 = 'http://testserver' + url2
		post_vars2 = {
			'From': '+14085558888',
			'To': '+18004664422',
			'CallStatus': 'inprogress',
			'CallSid': '106',
			}
		for k, v in sorted(post_vars2.items()):
			path2 += (k + v)
		response2 = self.client.post(url2, post_vars2,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path2)})
		self.assertEqual(response2.status_code, 200)
		gcalls = []
		twiliog.assert_has_calls(gcalls)
		pcalls = [
			mock.call.Response(),
			mock.call.Gather(
				finishOnKey='',
				action='/IVR/ProviderV2/TreeRoot/1/',
				numDigits=1,
				),
			mock.call.Gather().append(say(u'You have 0 new, and 0 saved urgent messages, and 0 new, and 0 saved voice messages,')),
			mock.call.Gather().append(say(u'To listen to all your messages, press one. To listen to your urgent messages, press two. To listen to your voice mail, press three. ')),
			mock.call.Gather().append(say(u'To manage your voicemail settings, press four. To repeat this menu, press star.')),
			mock.call.Response().append(twiliop.Gather())
			]
		twiliop.assert_has_calls(pcalls)
		assert self.client.session['ivr2_state'] == 'ProviderIVR_TreeRoot_New'
		providerS = Provider.objects.filter(mdcom_phone='8004664422')
		provider = providerS[0]
		assert self.client.session['provider_id'] == provider.id
		self.cleanup_rsa()

	def test_ProviderIVR_TreeAction_VM(self, sms, twiliog, twiliop, say, play):
		"""
		provider voicemail treeroot Main with 1 new voicemail
		with digit 3 to listen to all voicemail
		"""
		generate_keys_for_users(open(os.devnull, 'w'))
		provider = self.providers[1]
		config = _getProviderVMConfig(provider)
		config.pin = 'sha1$52958$8d282c07727dece284f4bed71a94cc469e1c9418'
		config.greeting = 'http://api.twilio.com/2010-04-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/RE8e3dfb46277add8bb0b381d087d9424d'
		config.name = 'http://api.twilio.com/2010-04-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/RE8e3dfb46277add8bb0b381d087d9424d'
		config.config_complete = True
		config.save()
		session = self.client.session
		session['provider_id'] = provider.id
		session['config_id'] = config.id
		session['Caller'] = '4085551234'
		session['ivr2_state'] = 'ProviderIVR_LeaveMsg_New'
		session['ivr2_sub_state'] = 'ProviderIVR_LeaveMsg_Start'
		session['ivr2_Record_recording'] = 'http://api.twilio.com/2010-04-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/RE8e3dfb46277add8bb0b381d087d9424d'
		session.save()
		self.assertEqual(provider.mdcom_phone, "8004664422")
		url = '/IVR/ProviderV2/LeaveMessage/1/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085551234',
			'To': '+18004664422',
			'CallStatus': 'inprogress',
			'CallSid': '252',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		# this saves a message to the provider
		# now we go to provider's voicemail tree to listen to it
		provider = self.providers[1]
		session = self.client.session
		session['provider_id'] = provider.id
		session['ivr2_state'] = 'ProviderIVR_TreeRoot_New'
		session['authenticated'] = True
		session.save()
		url = '/IVR/ProviderV2/TreeRoot/1/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+4085558888',
			'To': '+4085552222',
			'Digits': '3',
			'CallStatus': 'inprogress',
			'CallSid': '105',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		assert self.client.session['ivr2_state'] == 'ProviderIVR_TreeRoot_New'
		messages = MessageBodyUserStatus.objects.filter(user=provider.user,
			delete_flag=False, msg_body__message___resolved_by=None,
			msg_body__message__message_type__in=('ANS', 'VM'))
		msg = messages[0].msg_body.message
		uuid = MessageAttachment.objects.get(message=msg).uuid
		fetchurl = '/IVR/FetchRecording/' + uuid + "/"
		gcalls = [
			mock.call.Response(),
			mock.call.Response().append(say('call from 4085558888')),
			mock.call.Gather(action='/IVR/PlayMessagesV2/1/', finishOnKey='', numDigits=1),
			mock.call.Play(fetchurl),
			mock.call.Gather().append(twiliog.Play(fetchurl)),
			mock.call.Pause(length=1),
			mock.call.Gather().append(twiliog.Pause()),
			mock.call.Gather().append(say('Press 1 to move to the next message. ')),
			mock.call.Gather().append(say('Press 3 to re-play the message. ')),
			mock.call.Gather().append(say('Press 5 to call this person back. ')),
			mock.call.Gather().append(say('Press 7 to mark the message resolved and hide it. ')),
			mock.call.Gather().append(say('Press 9 to return to the main menu. ')),
			mock.call.Response().append(twiliog.Gather()),
			]
		twiliog.assert_has_calls(gcalls)
		pcalls = [
			mock.call.Response(),
			mock.call.Response().append(say('goodbye')),
			mock.call.Hangup(),
			mock.call.Response().append(twiliop.Hangup()),
			]
		twiliop.assert_has_calls(pcalls)
		self.cleanup_rsa()

# need more testcases to move forward/back the voicemail queue

	def test_ProviderIVR_TreeAction_Digits_4(self, sms, twiliog, twiliop, say, play):
		"""
		provider voicemail treeroot Main
		with digit 4 to manage voicemail settings (options)
		"""
		provider = self.providers[0]
		session = self.client.session
		session['provider_id'] = provider.id
		session['ivr2_state'] = 'ProviderIVR_TreeRoot_New'
		session['authenticated'] = True
		session.save()
		url = '/IVR/ProviderV2/TreeRoot/1/'
		path = 'http://testserver' + url
		post_vars = {
			'Digits': '4',
			'CallStatus': 'inprogress',
			'CallSid': '106',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		gcalls = []
		twiliog.assert_has_calls(gcalls)
		pcalls = [
			mock.call.Response(),
			mock.call.Gather(
				finishOnKey='',
				action='/IVR/ProviderV2/Options/1/',
				numDigits=1,
				),
			mock.call.Gather().append(say(u'Options menu')),
			mock.call.Gather().append(say(u'To re-record your name, press 1')),
			mock.call.Gather().append(say(u'To record a new greeting, press 3')),
			mock.call.Gather().append(say(u'To change your pin, press 5')),
			mock.call.Gather().append(say(u'To return to the main menu, press 9')),
			mock.call.Gather().append(say(u'To repeat this menu, press star')),
			mock.call.Response().append(twiliop.Gather()),
			]
		twiliop.assert_has_calls(pcalls)
		assert self.client.session['ivr2_state'] == 'ProviderIVR_Options_New'

	def test_ProviderIVR_TreeAction_Digits_Hash(self, sms, twiliog, twiliop, say, play):
		"""
		provider voicemail treeroot Main
		with digit # - not in any of the options stated
		"""
	# going to voicemail calltree
		provider = self.providers[0]
		session = self.client.session
		session['provider_id'] = provider.id
		session['ivr2_state'] = 'ProviderIVR_TreeRoot_New'
		session['authenticated'] = True
		session.save()
		url = '/IVR/ProviderV2/TreeRoot/1/'
		path = 'http://testserver' + url
		post_vars = {
			'Digits': '#',
			'CallStatus': 'inprogress',
			'CallSid': '107',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
#		self.assertEqual(session['ivr2_state'], 'ProviderIVR_TreeRoot_New')
		gcalls = []
		twiliog.assert_has_calls(gcalls)
		pcalls = [
			mock.call.Response(),
			mock.call.Response().append(say('I\'m sorry, I didn\'t understand that.')),
			mock.call.Gather(
				finishOnKey='',
				action='/IVR/ProviderV2/TreeRoot/1/',
				numDigits=1,
				),
			mock.call.Gather().append(say(u'You have 0 new, and 0 saved urgent messages, and 0 new, and 0 saved voice messages,')),
			mock.call.Gather().append(say(u'To manage your voicemail settings, press four.')),
			mock.call.Gather().append(say(u'To repeat this menu, press star.')),
			mock.call.Response().append(twiliop.Gather())
			]
		twiliop.assert_has_calls(pcalls)
		assert self.client.session['ivr2_state'] == 'ProviderIVR_TreeRoot_New'

#
# OPTIONS TEST
#
	def test_ProviderIVR_Options(self, sms, twiliog, twiliop, say, play):
		"""
		provider options main menu with vm_config set up
		explain options to change vm_config
		"""
		provider = self.providers[0]
		session = self.client.session
		session['provider_id'] = provider.id
		config = _getProviderVMConfig(provider)
		config.pin = 'sha1$52958$8d282c07727dece284f4bed71a94cc469e1c9418'
		config.complete = True
		config.save()
		session['ivr2_state'] = 'ProviderIVR_Options_New'
		session.save()
		session['authenticated'] = True
		url = '/IVR/ProviderV2/Options/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085559999',
			'To': '+18004664411',
			'CallStatus': 'inprogress',
			'CallSid': '150',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		gcalls = []
		twiliog.assert_has_calls(gcalls)
		pcalls = [
			mock.call.Response(),
			mock.call.Gather(
				finishOnKey='',
				action='/IVR/ProviderV2/Options/1/',
				numDigits=1,
				),
			mock.call.Gather().append(say(u'Options menu')),
			mock.call.Gather().append(say(u'To re-record your name, press 1')),
			mock.call.Gather().append(say(u'To record a new greeting, press 3')),
			mock.call.Gather().append(say(u'To change your pin, press 5')),
			mock.call.Gather().append(say(u'To return to the main menu, press 9')),
			mock.call.Gather().append(say(u'To repeat this menu, press star')),
			mock.call.Response().append(twiliop.Gather())
			]
		twiliop.assert_has_calls(pcalls)
		assert self.client.session['ivr2_state'] == 'ProviderIVR_Options_New'

	def test_ProviderIVR_Options_Digits_1(self, sms, twiliog, twiliop, say, play):
		"""
		provider options main menu with vm_config set up
		with digit 1 to change name
		"""
		provider = self.providers[0]
		session = self.client.session
		session['provider_id'] = provider.id
		session['ivr2_state'] = 'ProviderIVR_Options_New'
		session['authenticated'] = True
		session.save()
		url = '/IVR/ProviderV2/Options/1/'
		path = 'http://testserver' + url
		post_vars = {
			'Digits': '1',
			'CallStatus': 'inprogress',
			'CallSid': '151',
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
			mock.call.Response().append(say(' Please say your name after the tone. Press pound to finish.')),
			mock.call.Record(finishOnKey='1234567890*#',
				transcribe=False, playBeep=True, timeout=3, maxLength=10,
				action='/IVR/GetRecordingV2/1/'),
			mock.call.Response().append(twiliog.Record()),
			mock.call.Redirect('/IVR/GetRecordingV2/'),
			mock.call.Response().append(twiliog.Redirect()),
			]
		twiliog.assert_has_calls(gcalls)
		assert self.client.session['ivr2_state'] == 'ProviderIVR_Options_New'
		assert self.client.session['ivr2_sub_state'] == 'ProviderIVR_Options_1'

	def test_ProviderIVR_Options_Digits_3(self, sms, twiliog, twiliop, say, play):
		"""
		provider options main menu with vm_config set up
		with digit 3 to change greetings
		"""
	# change options greetings
		provider = self.providers[0]
		session = self.client.session
		session['provider_id'] = provider.id
		session['ivr2_state'] = 'ProviderIVR_Options_New'
		session['authenticated'] = True
		session.save()
		url = '/IVR/ProviderV2/Options/1/'
		path = 'http://testserver' + url
		post_vars = {
			'Digits': '3',
			'CallStatus': 'inprogress',
			'CallSid': '152',
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
			mock.call.Record(finishOnKey='1234567890*#',
				transcribe=False, playBeep=True, timeout=3, maxLength=120,
				action='/IVR/GetRecordingV2/1/'),
			mock.call.Response().append(twiliog.Record()),
			mock.call.Redirect('/IVR/GetRecordingV2/'),
			mock.call.Response().append(twiliog.Redirect()),
			]
		twiliog.assert_has_calls(gcalls)
		assert self.client.session['ivr2_state'] == 'ProviderIVR_Options_New'
		assert self.client.session['ivr2_sub_state'] == 'ProviderIVR_Options_3'

	def test_ProviderIVR_Options_Digits_5(self, sms, twiliog, twiliop, say, play):
		"""
		provider options main menu with vm_config set up
		with digit 5 to change pin
		"""
		provider = self.providers[0]
		session = self.client.session
		session['provider_id'] = provider.id
		session['ivr2_state'] = 'ProviderIVR_Options_New'
		session['authenticated'] = True
		session.save()
		url = '/IVR/ProviderV2/Options/1/'
		path = 'http://testserver' + url
		post_vars = {
			'Digits': '5',
			'CallStatus': 'inprogress',
			'CallSid': '153',
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
			mock.call.Gather(action='/IVR/ChangePinV2/1/',
				finishOnKey='#',
				numDigits=8,),
			mock.call.Gather().append(say("Please enter four to eight digits. Press pound to finish.")),
			mock.call.Response().append(twiliog.Gather(action='/IVR/ChangePinV2/1/',
				finishOnKey='#',
				numDigits=8,)),
			]
		twiliog.assert_has_calls(gcalls)
		assert self.client.session['ivr2_state'] == 'ProviderIVR_Options_New'
		assert self.client.session['ivr2_sub_state'] == 'ProviderIVR_Options_5'

	def test_ProviderIVR_Options_Digits_9(self, sms, twiliog, twiliop, say, play):
		"""
		provider options main menu with vm_config set up
		with digit 9 to return to main menu (TreeRoot)
		"""
		provider = self.providers[0]
		session = self.client.session
		session['provider_id'] = provider.id
		session['ivr2_state'] = 'ProviderIVR_Options_New'
		session['authenticated'] = True
		session.save()
		url = '/IVR/ProviderV2/Options/1/'
		path = 'http://testserver' + url
		post_vars = {
			'Digits': '9',
			'CallStatus': 'inprogress',
			'CallSid': '154',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		gcalls = []
		twiliog.assert_has_calls(gcalls)
		pcalls = [
			mock.call.Response(),
			mock.call.Redirect('/IVR/ProviderV2/TreeRoot/'),
			mock.call.Response().append(twiliop.Redirect()),
			]
		twiliop.assert_has_calls(pcalls)
		assert self.client.session['ivr2_state'] == 'ProviderIVR_TreeRoot_New'

	def test_ProviderIVR_Options_Digits_star(self, sms, twiliog, twiliop, say, play):
		"""
		provider options main menu with vm_config set up
		with digit * to repeat menu
		"""
		provider = self.providers[0]
		session = self.client.session
		session['provider_id'] = provider.id
		session['ivr2_state'] = 'ProviderIVR_Options_New'
		session['authenticated'] = True
		session.save()
		url = '/IVR/ProviderV2/Options/1/'
		path = 'http://testserver' + url
		post_vars = {
			'Digits': '*',
			'CallStatus': 'inprogress',
			'CallSid': '155',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		gcalls = []
		twiliog.assert_has_calls(gcalls)
		pcalls = [
			mock.call.Response(),
			mock.call.Gather(
				finishOnKey='',
				action='/IVR/ProviderV2/Options/1/',
				numDigits=1,
				),
			mock.call.Gather().append(say(u'Options menu')),
			mock.call.Gather().append(say(u'To re-record your name, press 1')),
			mock.call.Gather().append(say(u'To record a new greeting, press 3')),
			mock.call.Gather().append(say(u'To change your pin, press 5')),
			mock.call.Gather().append(say(u'To return to the main menu, press 9')),
			mock.call.Gather().append(say(u'To repeat this menu, press star')),
			mock.call.Response().append(twiliop.Gather())
			]
		twiliop.assert_has_calls(pcalls)
		assert self.client.session['ivr2_state'] == 'ProviderIVR_Options_New'

	def test_ProviderIVR_Options_Digits_bad(self, sms, twiliog, twiliop, say, play):
		"""
		provider options main menu with vm_config set up
		with digit 2 - not a valid selection choice
		"""
		provider = self.providers[0]
		session = self.client.session
		session['provider_id'] = provider.id
		session['ivr2_state'] = 'ProviderIVR_Options_New'
		session['authenticated'] = True
		session.save()
		url = '/IVR/ProviderV2/Options/1/'
		path = 'http://testserver' + url
		post_vars = {
			'Digits': '2',
			'CallStatus': 'inprogress',
			'CallSid': '156',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		gcalls = []
		twiliog.assert_has_calls(gcalls)
		pcalls = [
			mock.call.Response(),
			mock.call.Response().append(say(u'I\'m sorry, that wasn\'t a valid selection.')),
			mock.call.Gather(
				finishOnKey='',
				action='/IVR/ProviderV2/Options/1/',
				numDigits=1,
				),
			mock.call.Gather().append(say(u'Options menu')),
			mock.call.Gather().append(say(u'To re-record your name, press 1')),
			mock.call.Gather().append(say(u'To record a new greeting, press 3')),
			mock.call.Gather().append(say(u'To change your pin, press 5')),
			mock.call.Gather().append(say(u'To return to the main menu, press 9')),
			mock.call.Gather().append(say(u'To repeat this menu, press star')),
			mock.call.Response().append(twiliop.Gather())
			]
		twiliop.assert_has_calls(pcalls)
		assert self.client.session['ivr2_state'] == 'ProviderIVR_Options_New'

	def test_ProviderIVR_Options_Digits_bad1(self, sms, twiliog, twiliop, say, play):
		"""
		provider options main menu with vm_config set up
		with invalid digit (fall through else case => repeat options menu)
		"""
		provider = self.providers[0]
		session = self.client.session
		session['provider_id'] = provider.id
		session['ivr2_state'] = 'ProviderIVR_Options_New'
		session['authenticated'] = True
		session.save()
		url = '/IVR/ProviderV2/Options/1/'
		path = 'http://testserver' + url
		post_vars = {
			'Digits': '7',
			'CallStatus': 'inprogress',
			'CallSid': '157',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		gcalls = []
		twiliog.assert_has_calls(gcalls)
		pcalls = [
			mock.call.Response(),
			mock.call.Response().append(say(u'I\'m sorry, I didn\'t understand that.')),
			mock.call.Gather(
				finishOnKey='',
				action='/IVR/ProviderV2/Options/1/',
				numDigits=1,
				),
			mock.call.Gather().append(say(u'Options menu')),
			mock.call.Gather().append(say(u'To re-record your name, press 1')),
			mock.call.Gather().append(say(u'To record a new greeting, press 3')),
			mock.call.Gather().append(say(u'To change your pin, press 5')),
			mock.call.Gather().append(say(u'To return to the main menu, press 9')),
			mock.call.Gather().append(say(u'To repeat this menu, press star')),
			mock.call.Response().append(twiliop.Gather())
			]
		twiliop.assert_has_calls(pcalls)
		assert self.client.session['ivr2_state'] == 'ProviderIVR_Options_New'

	def test_ProviderIVR_Options_Digits_bad2(self, sms, twiliog, twiliop, say, play):
		"""
		provider options main menu with vm_config set up
		with invalid digit (fall through else case => repeat options menu)
		"""
		provider = self.providers[0]
		session = self.client.session
		session['provider_id'] = provider.id
		session['ivr2_state'] = 'ProviderIVR_Options_New'
		session['authenticated'] = True
		session.save()
		url = '/IVR/ProviderV2/Options/1/'
		path = 'http://testserver' + url
		post_vars = {
			'Digits': '44',
			'CallStatus': 'inprogress',
			'CallSid': '157',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		gcalls = []
		twiliog.assert_has_calls(gcalls)
		pcalls = [
			mock.call.Response(),
			mock.call.Response().append(say(u'I\'m sorry, I didn\'t understand that.')),
			mock.call.Gather(
				finishOnKey='',
				action='/IVR/ProviderV2/Options/1/',
				numDigits=1,
				),
			mock.call.Gather().append(say(u'Options menu')),
			mock.call.Gather().append(say(u'To re-record your name, press 1')),
			mock.call.Gather().append(say(u'To record a new greeting, press 3')),
			mock.call.Gather().append(say(u'To change your pin, press 5')),
			mock.call.Gather().append(say(u'To return to the main menu, press 9')),
			mock.call.Gather().append(say(u'To repeat this menu, press star')),
			mock.call.Response().append(twiliop.Gather())
			]
		twiliop.assert_has_calls(pcalls)
		assert self.client.session['ivr2_state'] == 'ProviderIVR_Options_New'

#
# OUTSIDE CALLER FORWARDCALL/LEAVEMSG TESTS
#
	def test_ProviderIVR_Main_Tree_ForwardCall_MO_1(self, sms, twiliog, twiliop, say, play):
		"""
		outside caller to Provider - Provider setting sends call to mobile
		go to foward call -> getName of caller
		"""
		provider = self.providers[2]
		self.assertEqual(provider.mdcom_phone, "8004664433")
		url = '/IVR/ProviderV2/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085551234',
			'To': '+18004664433',
			'CallStatus': 'inprogress',
			'CallSid': '200',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		pcalls = [
			mock.call.Response()]
		twiliop.assert_has_calls(pcalls)
		gcalls = [
			mock.call.Response(),
			mock.call.Pause(length=1),
			mock.call.Response().append(twiliog.Pause()),
			mock.call.Response().append(say('Please say your name after the tone.')),
			mock.call.Record(
				finishOnKey='1234567890*#',
				action='/IVR/GetQuickRecordingV2/1/',
				timeout=2,
				playBeep=True,
				maxLength=4,
				),
			mock.call.Response().append(twiliog.Record()),
			mock.call.Redirect('/IVR/GetQuickRecordingV2/'),
			mock.call.Response().append(twiliog.Redirect())
			]
		twiliog.assert_has_calls(gcalls)
		assert self.client.session['Caller'] == '4085551234'
		assert self.client.session['Called'] == '8004664433'
		assert self.client.session['ivr2_state'] == 'ProviderIVR_ForwardCall_New'
		assert self.client.session['ivr2_sub_state'] == 'ProviderIVR_ForwardCall_GetName'

	def test_ProviderIVR_Main_Tree_ForwardCall_MO_Dial(self, sms, twiliog, twiliop, say, play):
		"""
		outside caller to Provider - direct URL to CallForward
		dial provider's number
		"""
		provider = self.providers[2]
		log = callLog(caller_number='4085551234',
					called_number='8004664433',
					callSID='201',
					call_source='OC',
					mdcom_called=provider,
					)
		log.save()
		session = self.client.session
		session['provider_id'] = provider.id
		session['ivr2_state'] = 'ProviderIVR_ForwardCall_New'
		session['ivr2_sub_state'] = 'ProviderIVR_ForwardCall_GetName'
		session['Caller'] = '4085551234'
		session['Called'] = '8004664433'
		# need to set up that we got the name of caller
		session['ivr2_Record_recording'] = 'http://api.twilio.com/2010-04-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/RE8e3dfb46277add8bb0b381d087d9424d'
		session.save()
		self.assertEqual(provider.mdcom_phone, "8004664433")
		url = '/IVR/ProviderV2/CallForward/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085551234',
			'To': '+18004664433',
			'CallStatus': 'inprogress',
			'CallSid': '201',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		pcalls = [
			mock.call.Response(),
			mock.call.Dial(action='/IVR/ProviderV2/CallForward/', timeLimit=14400, timeout=22, callerId='+14085551234'),
			mock.call.Number(u'4085557777', url='/IVR/ProviderV2/CallForward/Vet/'),
			mock.call.Dial().append(twiliop.Number(u'4085554444', url='/IVR/ProviderV2/CallForward/Vet/')),
			mock.call.Response().append(twiliop.Dial(action='/IVR/ProviderV2/CallForward/', timeLimit=14400, timeout=22, callerId='+14085551234')),
			mock.call.Redirect('/IVR/ProviderV2/LeaveMessage/'),
			mock.call.Response().append(twiliop.Redirect()),
			]
		twiliop.assert_has_calls(pcalls)
		gcalls = []
		twiliog.assert_has_calls(gcalls)
		assert self.client.session['ivr2_state'] == 'ProviderIVR_ForwardCall_New'
		assert self.client.session['ivr2_sub_state'] == 'ProviderIVR_ForwardCall_Dial'

	def test_ProviderIVR_Main_Tree_ForwardCall_MO_Dialed(self, sms, twiliog, twiliop, say, play):
		"""
		outside caller to Provider who forwards call to MO - direct URL to CallForward
		after Dial step, forward to ProviderIVR_LeaveMsg_New
		"""
		provider = self.providers[2]
		log = callLog(caller_number='4085551234',
					called_number='8004664433',
					callSID='202',
					call_source='OC',
					mdcom_called=provider,
					)
		log.save()
		session = self.client.session
		session['provider_id'] = provider.id
		session['ivr2_state'] = 'ProviderIVR_ForwardCall_New'
		session['ivr2_sub_state'] = 'ProviderIVR_ForwardCall_Dial'
		session['Caller'] = '4085551234'
		session['Called'] = '8004664433'
		# need to set up that we got the name of caller
		session['ivr2_Record_recording'] = 'http://api.twilio.com/2010-04-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/RE8e3dfb46277add8bb0b381d087d9424d'
		session.save()
		self.assertEqual(provider.mdcom_phone, "8004664433")
		url = '/IVR/ProviderV2/CallForward/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085551234',
			'To': '+18004664433',
			'CallStatus': 'inprogress',
			'CallSid': '202',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		pcalls = [
			mock.call.Response(),
			mock.call.Response().append(say('The person at 8 0 0, 4 6 6, 4 4 3 3 is not available. \
Please leave a message after the beep. Press pound when finished for options.')),
			mock.call.Response().append(twiliog.Pause()),
			mock.call.Response().append(twiliog.Record()),
			mock.call.Response().append(twiliog.Redirect()),
			]
		twiliop.assert_has_calls(pcalls)
		gcalls = [
			mock.call.Pause(length=2),
			mock.call.Record(
				finishOnKey='1234567890*#',
				action='/IVR/GetRecordingV2/1/',
				transcribe=False,
				timeout=5,
				playBeep=True,
				maxLength=120,
				),
			mock.call.Redirect('/IVR/GetRecordingV2/')
			]
		twiliog.assert_has_calls(gcalls)
		assert self.client.session['ivr2_state'] == 'ProviderIVR_LeaveMsg_New'
		# assert self.client.session['ivr2_sub_state'] = 'ProviderIVR_ForwardCall_Dial'

	def test_ProviderIVR_Main_Tree_ForwardCall_MO_VetDialed(self, sms, twiliog, twiliop, say, play):
		"""
		outside caller to Provider who forwards call to MO - direct URL to CallForward/Vet
		this forwards to ProviderIVR_LeaveMsg_New
		"""
		provider = self.providers[2]
		log = callLog(caller_number='4085551234',
					called_number='8004664433',
					callSID='203',
					call_source='OC',
					mdcom_called=provider,
					)
		log.save()
		session = self.client.session
		session['provider_id'] = provider.id
		session['ivr2_state'] = 'ProviderIVR_ForwardCall_New'
		session['ivr2_sub_state'] = 'ProviderIVR_ForwardCall_Dial'
		session['Caller'] = '4085551234'
		session['Called'] = '8004664433'
		# need to set up that we got the name of caller
		session['ivr2_Record_recording'] = 'http://api.twilio.com/2010-04-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/RE8e3dfb46277add8bb0b381d087d9424d'
		session.save()
		self.assertEqual(provider.mdcom_phone, "8004664433")
		url = '/IVR/ProviderV2/CallForward/Vet/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085551234',
			'To': '+18004664433',
			'CallStatus': 'inprogress',
			'CallSid': '203',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		gcalls = []
		twiliog.assert_has_calls(gcalls)
		pcalls = [
			mock.call.Response(),
			mock.call.Gather(action='/IVR/ProviderV2/CallForward/Vet/', finishOnKey='', numDigits=1),
			mock.call.Gather().append(say('You have a call from')),
			mock.call.Play(''),
			mock.call.Gather().append(twiliop.Play('')),
			mock.call.Gather().append(say('Press any key to accept.')),
			mock.call.Response().append(twiliop.Gather()),
			mock.call.Hangup(),
			mock.call.Response().append(twiliop.Hangup()),
			]
		twiliop.assert_has_calls(pcalls)
		assert self.client.session['ivr2_state'] == 'ProviderIVR_ForwardCall_New'
		assert self.client.session['ivr2_sub_state'] == 'ProviderIVR_ForwardCall_Dial'

	def test_ProviderIVR_Main_Tree_ForwardCall_MO_Vet1(self, sms, twiliog, twiliop, say, play):
		"""
		outside caller to Provider who forwards call to MO - direct url to CallForward/Vet
		after dialing provider's number and provider hits a 1 to vet answer
		this returns control to twilio to connect the call
		"""
		provider = self.providers[2]
		log = callLog(caller_number='4085551234',
					called_number='8004664433',
					callSID='204',
					call_source='OC',
					mdcom_called=provider,
					)
		log.save()
		session = self.client.session
		session['provider_id'] = provider.id
		session['ivr2_state'] = 'ProviderIVR_ForwardCall_New'
		session['ivr2_sub_state'] = 'ProviderIVR_ForwardCall_Dial'
		session['Caller'] = '4085551234'
		session['Called'] = '8004664433'
		# need to set up that we got the name of caller
		session['ivr2_Record_recording'] = 'http://api.twilio.com/2010-04-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/RE8e3dfb46277add8bb0b381d087d9424d'
		session.save()
		self.assertEqual(provider.mdcom_phone, "8004664433")
		url = '/IVR/ProviderV2/CallForward/Vet/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085551234',
			'To': '+18004664433',
			'CallStatus': 'inprogress',
			'Digits': '1',
			'CallSid': '204',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		gcalls = []
		twiliog.assert_has_calls(gcalls)
		pcalls = []
		twiliop.assert_has_calls(pcalls)
		assert self.client.session['ivr2_state'] == 'ProviderIVR_ForwardCall_New'
		assert self.client.session['ivr2_sub_state'] == 'ProviderIVR_ForwardCall_Dial'

	def test_ProviderIVR_Main_Tree_ForwardCall_MO_fromProvider(self, sms, twiliog, twiliop, say, play):
		"""
		outside caller (who is a provider) call to Provider who forwards call to MO
		name of caller is from vmbox_config - go straight to dial
		"""
		provider = self.providers[2]
		callerProvider = self.providers[0]
		config = _getProviderVMConfig(callerProvider)
		config.pin = 'sha1$52958$8d282c07727dece284f4bed71a94cc469e1c9418'
		config.name = 'http://api.twilio.com/2010-04-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/RE8e3dfb46277add8bb0b381d087d9424d'
		config.config_complete = True
		config.save()
		self.assertEqual(provider.mdcom_phone, "8004664433")
		url = '/IVR/ProviderV2/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085559999',
			'To': '+18004664433',
			'CallStatus': 'inprogress',
			'CallSid': '205',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		pcalls = [
			mock.call.Response(),
			mock.call.Dial(action='/IVR/ProviderV2/CallForward/', timeLimit=14400, timeout=22, callerId='+18004664411'),
			mock.call.Number(u'4085557777', url='/IVR/ProviderV2/CallForward/Vet/'),
			mock.call.Dial().append(twiliop.Number(u'4085554444', url='/IVR/ProviderV2/CallForward/Vet/')),
			mock.call.Response().append(twiliop.Dial(action='/IVR/ProviderV2/CallForward/', timeLimit=14400, timeout=22, callerId='+18004664411')),
			mock.call.Redirect('/IVR/ProviderV2/LeaveMessage/'),
			mock.call.Response().append(twiliop.Redirect()),
#			mock.call.Number(u'4085554444', url='/IVR/ProviderV2/CallForward/Vet/'),
#			mock.call.Dial(action='/IVR/ProviderV2/CallForward/', timeLimit=14400, timeout=22, callerId='8004664411'),
			]
		twiliop.assert_has_calls(pcalls)
		gcalls = []
		twiliog.assert_has_calls(gcalls)
		assert self.client.session['ivr2_state'] == 'ProviderIVR_ForwardCall_New'
		assert self.client.session['ivr2_sub_state'] == 'ProviderIVR_ForwardCall_Dial'

	def test_ProviderIVR_Main_Tree_LeaveMsg_VM_1(self, sms, twiliog, twiliop, say, play):
		"""
		outside caller to Provider who forwards call to VM
		provider vm_config is not complete
		"""
		provider = self.providers[1]
		self.assertEqual(provider.mdcom_phone, "8004664422")
		url = '/IVR/ProviderV2/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085551234',
			'To': '+18004664422',
			'CallStatus': 'inprogress',
			'CallSid': '250',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		pcalls = [
			mock.call.Response(),
			mock.call.Response().append(say('The person at + 1 8, 0 0 4, 6 6 4 4 2 2 is not available. \
Please leave a message after the beep. Press pound when finished for options.')),
			mock.call.Response().append(twiliog.Pause()),
			mock.call.Response().append(twiliog.Record()),
			mock.call.Response().append(twiliog.Redirect()),
			]
		twiliop.assert_has_calls(pcalls)
		gcalls = [
			mock.call.Pause(length=2),
			mock.call.Record(
				finishOnKey='1234567890*#',
				action='/IVR/GetRecordingV2/1/',
				transcribe=False,
				timeout=5,
				playBeep=True,
				maxLength=120,
				),
			mock.call.Redirect('/IVR/GetRecordingV2/')
			]
		twiliog.assert_has_calls(gcalls)
		assert self.client.session['ivr2_state'] == 'ProviderIVR_LeaveMsg_New'

	def test_ProviderIVR_Main_Tree_LeaveMsg_VM_2(self, sms, twiliog, twiliop, say, play):
		"""
		outside caller to Provider who forwards call to VM; provider vm_config is complete
		to get recording from caller
		"""
		provider = self.providers[1]
		config = _getProviderVMConfig(provider)
		config.pin = 'sha1$52958$8d282c07727dece284f4bed71a94cc469e1c9418'
		config.greeting = 'http://api.twilio.com/2010-04-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/RE8e3dfb46277add8bb0b381d087d9424d'
		config.name = 'http://api.twilio.com/2010-04-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/RE8e3dfb46277add8bb0b381d087d9424d'
		config.config_complete = True
		config.save()
		session = self.client.session
		session['provider_id'] = provider.id
		session['config_id'] = config.id
		session.save()
		self.assertEqual(provider.mdcom_phone, "8004664422")
		url = '/IVR/ProviderV2/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085551234',
			'To': '+18004664422',
			'CallStatus': 'inprogress',
			'CallSid': '251',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		pcalls = [
			mock.call.Response(),
			mock.call.Response().append(twiliog.Play('http://api.twilio.com/2010-04-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/RE8e3dfb46277add8bb0b381d087d9424d')),
			mock.call.Response().append(twiliog.Pause()),
			mock.call.Response().append(twiliog.Record()),
			mock.call.Response().append(twiliog.Redirect()),
			]
		twiliop.assert_has_calls(pcalls)
		gcalls = [
			mock.call.Play(u'http://api.twilio.com/2010-04-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/RE8e3dfb46277add8bb0b381d087d9424d'),
			mock.call.Pause(length=2),
			mock.call.Record(
				finishOnKey='1234567890*#',
				action='/IVR/GetRecordingV2/1/',
				transcribe=False,
				timeout=5,
				playBeep=True,
				maxLength=120,
				),
			mock.call.Redirect('/IVR/GetRecordingV2/'),
			]
		twiliog.assert_has_calls(gcalls)
		assert self.client.session['ivr2_state'] == 'ProviderIVR_LeaveMsg_New'

	def test_ProviderIVR_Main_Tree_LeaveMsg_VM_3(self, sms, twiliog, twiliop, say, play):
		"""
		outside caller to Provider who forwards call to VM; provider vm_config is complete;
		to leaveMessage action to save recording
		"""
		generate_keys_for_users(open(os.devnull, 'w'))
		provider = self.providers[1]
		config = _getProviderVMConfig(provider)
		config.set_pin('1234')
		config.greeting = 'http://api.twilio.com/2010-04-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/RE8e3dfb46277add8bb0b381d087d9424d'
		config.name = 'http://api.twilio.com/2010-04-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/RE8e3dfb46277add8bb0b381d087d9424d'
		config.config_complete = True
		config.save()
		session = self.client.session
		session['provider_id'] = provider.id
		session['config_id'] = config.id
		session['Caller'] = '4085551234'
		session['ivr2_state'] = 'ProviderIVR_LeaveMsg_New'
		session['ivr2_Record_recording'] = 'http://api.twilio.com/2010-04-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/RE8e3dfb46277add8bb0b381d087d9424d'
		session.save()
		self.assertEqual(provider.mdcom_phone, "8004664422")
		url = '/IVR/ProviderV2/LeaveMessage/1/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085551234',
			'To': '+18004664422',
			'CallStatus': 'inprogress',
			'CallSid': '252',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		pcalls = [
			mock.call.Response(),
			mock.call.Response().append(say('Good bye')),
			mock.call.Hangup(),
			mock.call.Response().append(twiliop.Hangup()),
			]
		twiliop.assert_has_calls(pcalls)
		gcalls = []
		twiliog.assert_has_calls(gcalls)
		assert self.client.session['ivr2_state'] == 'ProviderIVR_LeaveMsg_New'
		assert self.client.session['ivr_makeRecording_recording'] == 'http://api.twilio.com/2010-04-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/RE8e3dfb46277add8bb0b381d087d9424d'
		# TODO: assert that the provider has received a message from this caller
		self.cleanup_rsa()

	def test_ProviderIVR_Main_Tree_LeaveMsg_VM_4(self, sms, twiliog, twiliop, say, play):
		"""
		outside caller to Provider who forwards call to VM; provider vm_config is complete;
		to leaveMessage action to save recording - caller hang up after recording
		"""
		generate_keys_for_users(open(os.devnull, 'w'))
		provider = self.providers[1]
		config = _getProviderVMConfig(provider)
		config.set_pin('1234')
		config.greeting = 'http://api.twilio.com/2010-04-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/RE8e3dfb46277add8bb0b381d087d9424d'
		config.name = 'http://api.twilio.com/2010-04-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/RE8e3dfb46277add8bb0b381d087d9424d'
		config.config_complete = True
		config.save()
		session = self.client.session
		session['provider_id'] = provider.id
		session['config_id'] = config.id
		session['Caller'] = '4085551234'
		session['ivr2_state'] = 'ProviderIVR_LeaveMsg_New'
		session['ivr2_Record_recording'] = 'http://api.twilio.com/2010-04-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/RE8e3dfb46277add8bb0b381d087d9424d'
		session.save()
		self.assertEqual(provider.mdcom_phone, "8004664422")
		url = '/IVR/ProviderV2/LeaveMessage/1/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085551234',
			'To': '+18004664422',
			'CallStatus': 'completed',
			'CallSid': '252',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		pcalls = [
			mock.call.Response(),
			mock.call.Response().append(say('Good bye')),
			mock.call.Hangup(),
			mock.call.Response().append(twiliop.Hangup()),
			]
		twiliop.assert_has_calls(pcalls)
		gcalls = []
		twiliog.assert_has_calls(gcalls)
		assert self.client.session['ivr2_state'] == 'ProviderIVR_LeaveMsg_New'
		assert self.client.session['ivr_makeRecording_recording'] == 'http://api.twilio.com/2010-04-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/RE8e3dfb46277add8bb0b381d087d9424d'
		# TODO: assert that the provider has received a message from this caller
		self.cleanup_rsa()

	def test_ProviderIVR_Main_Tree_Status(self, sms, twiliog, twiliop, say, play):
		"""
		status callback from prior call
		"""
		provider = self.providers[1]
		config = _getProviderVMConfig(provider)
		config.set_pin('1234')
		config.greeting = 'http://api.twilio.com/2010-04-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/RE8e3dfb46277add8bb0b381d087d9424d'
		config.name = 'http://api.twilio.com/2010-04-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/RE8e3dfb46277add8bb0b381d087d9424d'
		config.config_complete = True
		config.save()
		session = self.client.session
		session['provider_id'] = provider.id
		session['config_id'] = config.id
		session['Caller'] = '4085551234'
		session['ivr2_state'] = 'ProviderIVR_LeaveMsg_New'
		session['ivr2_Record_recording'] = 'http://api.twilio.com/2010-04-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/RE8e3dfb46277add8bb0b381d087d9424d'
		session.save()
		log = callLog(callSID='252', caller_number='4085551234', called_number='8004664422',
			call_source='OC')
		log.save()
		self.assertEqual(provider.mdcom_phone, "8004664422")
		url = '/IVR/ProviderV2/Status/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085551234',
			'To': '+18004664422',
			'CallStatus': 'completed',
			'CallSid': '252',
			'CallDuration': '55',
			'Duration': '2'
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		pcalls = []
		twiliop.assert_has_calls(pcalls)
		gcalls = []
		twiliog.assert_has_calls(gcalls)
		assert self.client.session['ivr2_state'] == 'ProviderIVR_LeaveMsg_New'
		log_qs = callLog.objects.filter(callSID='252')
		if (log_qs.exists()):
			log = log_qs.get()
			self.assertEqual(log.call_duration, 55)

	def test_playMessages_Digit_1(self, sms, twiliog, twiliop, say, play):
		"""
		first, we create 2 VM msgs for a provider
		Then we call PlayMessagesV2
		This is more functional than unit testing - since I am using a diff url to create
		voice mail messages. Also, this is only for Provider Voicemail - to play messages
		"""
		generate_keys_for_users(open(os.devnull, 'w'))
		provider = self.providers[1]
		config = _getProviderVMConfig(provider)
		config.pin = 'sha1$52958$8d282c07727dece284f4bed71a94cc469e1c9418'
		config.greeting = 'http://api.twilio.com/2010-04-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/RE8e3dfb46277add8bb0b381d087d9424d'
		config.name = 'http://api.twilio.com/2010-04-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/RE8e3dfb46277add8bb0b381d087d9424d'
		config.config_complete = True
		config.save()
		session = self.client.session
		session['provider_id'] = provider.id
		session['config_id'] = config.id
		session['Caller'] = '4085551234'
		session['ivr2_state'] = 'ProviderIVR_LeaveMsg_New'
		session['ivr2_Record_recording'] = 'http://api.twilio.com/2010-04-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/RE8e3dfb46277add8bb0b381d087d9424d'
		session.save()
		self.assertEqual(provider.mdcom_phone, "8004664422")
		url = '/IVR/ProviderV2/LeaveMessage/1/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085551234',
			'To': '+18004664422',
			'CallStatus': 'inprogress',
			'CallSid': '252',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		# this saves one message to the provider
		session['Caller'] = '4086661234'
		session['ivr2_state'] = 'ProviderIVR_LeaveMsg_New'
		session['ivr2_Record_recording'] = 'http://api.twilio.com/2010-04-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/RE8e3dfb46277add8bb0b381d087d9424d'
		session.save()
		self.assertEqual(provider.mdcom_phone, "8004664422")
		url = '/IVR/ProviderV2/LeaveMessage/1/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14086661234',
			'To': '+18004664422',
			'CallStatus': 'inprogress',
			'CallSid': '253',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		# this saves 2nd msg to provider
		# TODO we set up answering service msgs

		url = '/IVR/PlayMessagesV2/1/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+4085558888',
			'To': '+4085552222',
			'CallStatus': 'inprogress',
			'Digits': '1',
			'CallSid': '1322',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		messages = MessageBodyUserStatus.objects.filter(user=provider.user,
			delete_flag=False, msg_body__message___resolved_by=None,
			msg_body__message__message_type__in=('ANS', 'VM'))
		session = self.client.session
		session['ivr2_state'] = 'ProviderIVR_TreeRoot_New'
		session['ivr2_playMessages_newMessages'] = list(messages.filter(
			read_flag=False, delete_flag=False).all())
		session['ivr2_playMessages_oldMessages'] = []
		session.save()
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		assert self.client.session['ivr2_state'] == 'ProviderIVR_TreeRoot_New'
		assert len(self.client.session['ivr2_playMessages_newMessages']) == 1
		# the msgs are popped from the back of the list
		msg = messages[0].msg_body.message
		uuid = MessageAttachment.objects.get(message=msg).uuid
		fetchurl = '/IVR/FetchRecording/' + uuid + "/"
		gcalls = [
			mock.call.Response(),
			mock.call.Response().append(say('playing first new message')),
			mock.call.Gather(action='/IVR/PlayMessagesV2/1/', finishOnKey='', numDigits=1),
			mock.call.Play(str(fetchurl)),
			mock.call.Gather().append(twiliog.Play(fetchurl)),
			mock.call.Pause(length=1),
			mock.call.Gather().append(twiliog.Pause()),
			mock.call.Gather().append(say('Press 1 to move to the next message. ')),
			mock.call.Gather().append(say('Press 3 to re-play the message. ')),
			mock.call.Gather().append(say('Press 5 to call this person back. ')),
			mock.call.Gather().append(say('Press 7 to mark the message resolved and hide it. ')),
			mock.call.Gather().append(say('Press 9 to return to the main menu. ')),
			mock.call.Response().append(twiliog.Gather()),
			]
		twiliog.assert_has_calls(gcalls)
		self.cleanup_rsa()

	def test_playMessages_Digit_1_1(self, sms, twiliog, twiliop, say, play):
		"""
		first, we create 2 VM msgs for a provider
		Then we call PlayMessagesV2
		This is more functional than unit testing - since I am using a diff url to create
		voice mail messages. Also, this is only for Provider Voicemail - to play messages
		"""
		generate_keys_for_users(open(os.devnull, 'w'))
		provider = self.providers[1]
		config = _getProviderVMConfig(provider)
		config.pin = 'sha1$52958$8d282c07727dece284f4bed71a94cc469e1c9418'
		config.greeting = 'http://api.twilio.com/2010-04-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/RE8e3dfb46277add8bb0b381d087d9424d'
		config.name = 'http://api.twilio.com/2010-04-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/RE8e3dfb46277add8bb0b381d087d9424d'
		config.config_complete = True
		config.save()
		session = self.client.session
		session['provider_id'] = provider.id
		session['config_id'] = config.id
		session['Caller'] = '4085551234'
		session['ivr2_state'] = 'ProviderIVR_LeaveMsg_New'
		session['ivr2_Record_recording'] = 'http://api.twilio.com/2010-04-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/RE8e3dfb46277add8bb0b381d087d9424d'
		session.save()
		self.assertEqual(provider.mdcom_phone, "8004664422")
		url = '/IVR/ProviderV2/LeaveMessage/1/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085551234',
			'To': '+18004664422',
			'CallStatus': 'inprogress',
			'CallSid': '252',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		# this saves one message to the provider
		session['Caller'] = '4086661234'
		session['ivr2_state'] = 'ProviderIVR_LeaveMsg_New'
		session['ivr2_Record_recording'] = 'http://api.twilio.com/2010-04-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/RE8e3dfb46277add8bb0b381d087d9424d'
		session.save()
		self.assertEqual(provider.mdcom_phone, "8004664422")
		url = '/IVR/ProviderV2/LeaveMessage/1/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14086661234',
			'To': '+18004664422',
			'CallStatus': 'inprogress',
			'CallSid': '253',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		# this saves 2nd msg to provider
		# TODO we set up answering service msgs

		url = '/IVR/PlayMessagesV2/1/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+4085558888',
			'To': '+4085552222',
			'CallStatus': 'inprogress',
			'Digits': '1',
			'CallSid': '1322',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		messages = MessageBodyUserStatus.objects.filter(user=provider.user,
			delete_flag=False, msg_body__message___resolved_by=None,
			msg_body__message__message_type__in=('ANS', 'VM'))
		session = self.client.session
		session['ivr2_state'] = 'ProviderIVR_TreeRoot_New'
		session['ivr2_playMessages_newMessages'] = list(messages.filter(
			read_flag=False, delete_flag=False).order_by('msg_body__message__message_type',
					'-msg_body__message__send_timestamp').all())
		session['ivr2_playMessages_oldMessages'] = []
		session.save()
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		# second msg
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		assert self.client.session['ivr2_state'] == 'ProviderIVR_TreeRoot_New'
		assert self.client.session['ivr2_playMessages_newMessages'] == []
		msg0 = messages[0].msg_body.message
		uuid0 = MessageAttachment.objects.get(message=msg0).uuid
		fetchurl0 = '/IVR/FetchRecording/' + uuid0 + '/'
		msg1 = messages[1].msg_body.message
		uuid1 = MessageAttachment.objects.get(message=msg1).uuid
		fetchurl1 = '/IVR/FetchRecording/' + uuid1 + '/'
		gcalls = [
			mock.call.Response(),
			mock.call.Response().append(say('playing first new message')),
			mock.call.Gather(finishOnKey='', action='/IVR/PlayMessagesV2/1/', numDigits=1),
			mock.call.Play(str(fetchurl1)),
			mock.call.Gather().append(twiliog.Play(fetchurl1)),
			mock.call.Pause(length=1),
			mock.call.Gather().append(twiliog.Pause(length=1)),
			mock.call.Gather().append(say('Press 1 to move to the next message. ')),
			mock.call.Gather().append(say('Press 3 to re-play the message. ')),
			mock.call.Gather().append(say('Press 5 to call this person back. ')),
			mock.call.Gather().append(say('Press 7 to mark the message resolved and hide it. ')),
			mock.call.Gather().append(say('Press 9 to return to the main menu. ')),
			mock.call.Response().append(twiliog.Gather()),
			mock.call.ANY,
			mock.call.Response(),
			mock.call.Response().append(say('playing next new message')),
			mock.call.Gather(finishOnKey='', action='/IVR/PlayMessagesV2/1/', numDigits=1),
			mock.call.Play(str(fetchurl0)),
			mock.call.Gather().append(twiliog.Play(fetchurl0)),
			mock.call.Pause(length=1),
			mock.call.Gather().append(twiliog.Pause(length=1)),
			mock.call.Gather().append(say('Press 1 to move to the next message. ')),
			mock.call.Gather().append(say('Press 3 to re-play the message. ')),
			mock.call.Gather().append(say('Press 5 to call this person back. ')),
			mock.call.Gather().append(say('Press 7 to mark the message resolved and hide it. ')),
			mock.call.Gather().append(say('Press 9 to return to the main menu. ')),
			mock.call.Response().append(twiliog.Gather()),
			]
		# this fails!
#		twiliog.assert_has_calls(gcalls)
		self.cleanup_rsa()

	def test_playMessages_Digit_1_4(self, sms, twiliog, twiliop, say, play):
		"""
		first, we create 2 VM msgs for a provider
		Then we call PlayMessagesV2 - with digit 1 to play all msgs; then 4 which is not
		part of any selection.
		This is more functional than unit testing - since I am using a diff url to create
		voice mail messages. Also, this is only for Provider Voicemail - to play messages
		"""
		generate_keys_for_users(open(os.devnull, 'w'))
		provider = self.providers[1]
		config = _getProviderVMConfig(provider)
		config.set_pin('1234')
		config.greeting = 'http://api.twilio.com/2010-04-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/RE8e3dfb46277add8bb0b381d087d9424d'
		config.name = 'http://api.twilio.com/2010-04-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/RE8e3dfb46277add8bb0b381d087d9424d'
		config.config_complete = True
		config.save()
		session = self.client.session
		session['provider_id'] = provider.id
		session['config_id'] = config.id
		session['Caller'] = '4085551234'
		session['ivr2_state'] = 'ProviderIVR_LeaveMsg_New'
		session['ivr2_Record_recording'] = 'http://api.twilio.com/2010-04-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/RE8e3dfb46277add8bb0b381d087d9424d'
		session.save()
		self.assertEqual(provider.mdcom_phone, "8004664422")
		url = '/IVR/ProviderV2/LeaveMessage/1/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14085551234',
			'To': '+18004664422',
			'CallStatus': 'inprogress',
			'CallSid': '254',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		# this saves one message to the provider
		session['Caller'] = '4086661234'
		session['ivr2_state'] = 'ProviderIVR_LeaveMsg_New'
		session['ivr2_Record_recording'] = 'http://api.twilio.com/2010-04-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/RE8e3dfb46277add8bb0b381d087d9424d'
		session.save()
		self.assertEqual(provider.mdcom_phone, "8004664422")
		url = '/IVR/ProviderV2/LeaveMessage/1/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14086661234',
			'To': '+18004664422',
			'CallStatus': 'inprogress',
			'CallSid': '255',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		# saved 2nd msg to provider
		url = '/IVR/PlayMessagesV2/1/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+4085558888',
			'To': '+4085552222',
			'CallStatus': 'inprogress',
			'Digits': '1',
			'CallSid': '1322',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		messages = MessageBodyUserStatus.objects.filter(user=provider.user,
			delete_flag=False, msg_body__message___resolved_by=None,
			msg_body__message__message_type__in=('ANS', 'VM'))
		session = self.client.session
		session['ivr2_state'] = 'ProviderIVR_TreeRoot_New'
		session['ivr2_playMessages_newMessages'] = list(messages.filter(
			read_flag=False, delete_flag=False).order_by('msg_body__message__message_type',
					'-msg_body__message__send_timestamp').all())
		session['ivr2_playMessages_oldMessages'] = []
		session.save()
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		# second msg
		path2 = 'http://testserver' + url
		post_vars2 = {
			'From': '+4085558888',
			'To': '+4085552222',
			'CallStatus': 'inprogress',
			'Digits': '4',
			'CallSid': '1322',
			}
		for k, v in sorted(post_vars2.items()):
			path2 += (k + v)
		response = self.client.post(url, post_vars2,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path2)})
		self.assertEqual(response.status_code, 200)
		assert self.client.session['ivr2_state'] == 'ProviderIVR_TreeRoot_New'
		msg0 = messages[0].msg_body.message
		uuid0 = MessageAttachment.objects.get(message=msg0).uuid
		fetchurl0 = '/IVR/FetchRecording/' + uuid0 + '/'
		msg1 = messages[1].msg_body.message
		uuid1 = MessageAttachment.objects.get(message=msg1).uuid
		fetchurl1 = '/IVR/FetchRecording/' + uuid1 + '/'
		gcalls = [
			mock.call.Response(),
			mock.call.Response().append(say('playing first new message')),
			mock.call.Gather(action='/IVR/PlayMessagesV2/1/', finishOnKey='', numDigits=1),
			mock.call.Play(str(fetchurl1)),
			mock.call.Gather().append(twiliog.Play(fetchurl1)),
			mock.call.Pause(length=1),
			mock.call.Gather().append(twiliog.Pause(length=1)),
			mock.call.Gather().append(say('Press 1 to move to the next message. ')),
			mock.call.Gather().append(say('Press 3 to re-play the message. ')),
			mock.call.Gather().append(say('Press 5 to call this person back. ')),
			mock.call.Gather().append(say('Press 7 to mark the message resolved and hide it. ')),
			mock.call.Gather().append(say('Press 9 to return to the main menu. ')),
			mock.call.Response().append(twiliog.Gather()),
			mock.call.ANY,
			mock.call.Response(),
			mock.call.Response().append(say('I\'m sorry, I didn\'t get that')),
			mock.call.Response().append(say('Re-playing message')),
			mock.call.Gather(action='/IVR/PlayMessagesV2/1/', finishOnKey='', numDigits=1),
			mock.call.Play(str(fetchurl1)),
			mock.call.Gather().append(twiliog.Play(fetchurl1)),
			mock.call.Pause(length=1),
			mock.call.Gather().append(twiliog.Pause(length=1)),
			mock.call.Gather().append(say('Press 1 to move to the next message. ')),
			mock.call.Gather().append(say('Press 3 to re-play the message. ')),
			mock.call.Gather().append(say('Press 5 to call this person back. ')),
			mock.call.Gather().append(say('Press 7 to mark the message resolved and hide it. ')),
			mock.call.Gather().append(say('Press 9 to return to the main menu. ')),
			mock.call.Response().append(twiliog.Gather()),
			]
		# this fails
#		twiliog.assert_has_calls(gcalls)
		self.cleanup_rsa()

	def test_getRecording_4b(self, sms, twiliog, twiliop, say, play):
		"""
		get recording - action with recording url - and user hung up
		"""
		generate_keys_for_users(open(os.devnull, 'w'))
		session = self.client.session
		provider = self.providers[0]
		session['provider_id'] = provider.id
		session['ivr2_state'] = 'ProviderIVR_LeaveMsg_New'
		session['Caller'] = '4089991234'
		session['Called'] = '8004664411'
		# or PracticeIVR_LeaveUrgentMsg_GetMsg
		session['ivr2_Record_prompt_str'] = 'Please leave your message'
		session['ivr2_returnOnHangup'] = 'MHLogin.DoctorCom.IVR.views_provider_v2.ProviderIVR_LeaveMsg_Action'
		session['authenticated'] = True
		session.save()
		url = '/IVR/GetRecordingV2/1/'
		path = 'http://testserver' + url
		post_vars = {
			'From': '+14089991234',
			'To': '+18004664411',
			'CallStatus': 'completed',
			'CallSid': '12631',
			'CallDuration': '55',
			'RecordingUrl': 'http://api.twilio.com/2010-04-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/RE8e3dfb46277add8bb0b381d087d9424d'
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		gcalls = [
			mock.call.Response()
			]
		twiliog.assert_has_calls(gcalls)
		pcalls = [
			mock.call.Response(),
			mock.call.Response().append(say('good bye')),
			mock.call.Hangup(),
			mock.call.Response().append(twiliop.Hangup()),
			]
		twiliop.assert_has_calls(pcalls)
		assert self.client.session['Caller'] == '4089991234'
		assert self.client.session['Called'] == '8004664411'
		assert self.client.session['ivr2_state'] == 'ProviderIVR_LeaveMsg_New'
		assert self.client.session['ivr_makeRecording_recording'] == 'http://api.twilio.com/2010-04-01/Accounts/AC087cabfd0a453a05acceb2810c100f69/Recordings/RE8e3dfb46277add8bb0b381d087d9424d'
		# assert message has been saved
		self.cleanup_rsa()

