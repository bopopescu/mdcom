
import hmac
import mock

from hashlib import sha1
from base64 import encodestring
from django.conf import settings
from .base import TestIVRBase
#from django.contrib.auth.models import UserManager
from MHLogin.MHLUsers.models import Provider

# helper to generate signature for twilio validation
generate_sig = lambda path: encodestring(hmac.new(
	settings.TWILIO_ACCOUNT_TOKEN, path, sha1).digest()).strip()


@mock.patch('MHLogin.DoctorCom.speech.utils.Play', autospec=True)
@mock.patch('MHLogin.DoctorCom.speech.utils.Say', autospec=True)
@mock.patch('MHLogin.DoctorCom.IVR.views_provider.twilio', autospec=True)
class TestIVRProvider(TestIVRBase):
	def setUp(self):
		super(TestIVRProvider, self).setUp()

	def tearDown(self):
		super(TestIVRProvider, self).tearDown()

	def test_getProviderIVR_Main_completed(self, twilio, say, play):
		pq = Provider.objects.all()
		if pq:
			provider = pq[0]
			#print u"Provider: %d %s" % (provider.id, provider.user.username)
		else:
			provider = None
			#print u"Provider not found "

		session = self.client.session
		session['ivr_call_stack'] = []
		session['provider_id'] = provider.id
		session.save()
		url = '/IVR/Provider/'
		path = 'http://testserver' + url  # TODO: figure out better way to do this
		post_vars = {
			'CallStatus': 'completed',
			'Duration': '0.01',
			'CallSid': '123'
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
#		import pdb; pdb.set_trace()
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		calls = [
			mock.call.Response(),
			]
		twilio.assert_has_calls(calls)

	def test_getProviderIVR_Main_VM(self, twilio, say, play):
		provider = self.providers[0]
		#print u"Provider: %d %s" % (provider.id, provider.user.username)
		session = self.client.session
		session['ivr_call_stack'] = ['ProviderIVR_Main']
		session['provider_id'] = provider.id
		session.save()
		url = '/IVR/Provider/'
		path = 'http://testserver' + url  # TODO: figure out better way to do this
		post_vars = {
			'Caller': '4085551234',
			'Called': '8004664411',
			'CallSid': '123',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
#		import pdb; pdb.set_trace()
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		calls = [
			mock.call.Response(),
			]
		twilio.assert_has_calls(calls)

	def test_getProviderIVR_Main(self, twilio, say, play):
		provider = self.providers[0]
		#print u"Provider: %d %s" % (provider.id, provider.user.username)
		session = self.client.session
		session['ivr_call_stack'] = ['ProviderIVR_Main']
		session['provider_id'] = provider.id
		session.save()
		url = '/IVR/Provider/'
		path = 'http://testserver' + url  # TODO: figure out better way to do this
		post_vars = {
			'Caller': '4085551111',
			'Called': '8004664411',
			'CallSid': '123',
			}
		for k, v in sorted(post_vars.items()):
			path += (k + v)
#		import pdb; pdb.set_trace()
		response = self.client.post(url, post_vars,
			**{'HTTP_X_TWILIO_SIGNATURE': generate_sig(path)})
		self.assertEqual(response.status_code, 200)
		calls = [
			mock.call.Response(),
			]
		twilio.assert_has_calls(calls)

