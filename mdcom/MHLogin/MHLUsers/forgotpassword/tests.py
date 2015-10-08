
import os
import mock
import datetime
from django.contrib.auth import authenticate
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.core.serializers.json import DjangoJSONEncoder

from MHLogin.MHLUsers.models import MHLUser, Provider, Physician

from MHLogin.KMS.utils import generate_keys_for_users
from MHLogin.KMS.models import OwnerPublicKey, UserPrivateKey


# keep microseconds, works w/sqlite and compat w/mysql because it's stripped		
class MockDjangoJSONEncoder(DjangoJSONEncoder):
	def default(self, o):
		return o.isoformat() if isinstance(o, datetime.datetime) \
			else super(MockDjangoJSONEncoder, self).default(o)


class ForgotPassword(TestCase):
	def setUp(self):
		self.provider = Provider.objects.create(username='healmeister', first_name='heal',
			last_name='meister', address1="555 Bryant St.", city="Palo Alto", state="CA", 
			lat=0.0, longit=0.0, office_lat=0.0, office_longit=0.0, is_active=True, 
			tos_accepted=True, mobile_confirmed=True, mdcom_phone='123', 
			email_confirmed=True, mobile_phone='4085551212')
		self.provider.set_password('demo')
		self.provider.user = self.provider  # for our unique prov-user reln
		self.provider.save()

		self.docprov = Provider.objects.create(username='docholiday', first_name='doc',
			last_name='holiday', address1="555 Bryant St.", city="Palo Alto", state="CA", 
			lat=0.0, longit=0.0, office_lat=0.0, office_longit=0.0, is_active=True, 
			tos_accepted=True, mobile_confirmed=True, mdcom_phone='101', mobile_phone='202',
			email_confirmed=True, email='docholiday@tombstone.az.edu')
		self.docprov.set_password('demo')
		self.docprov.user = self.docprov  # for our unique prov-user reln
		self.docprov.save()
		Physician.objects.create(user=self.docprov)
		generate_keys_for_users(open(os.devnull, 'w'))

	def tearDown(self):
		MHLUser.objects.all().delete()
		Provider.objects.all().delete()
		Physician.objects.all().delete()
		OwnerPublicKey.objects.all().delete()
		UserPrivateKey.objects.all().delete()

	@mock.patch('MHLogin.MHLUsers.forgotpassword.views.DjangoJSONEncoder',
			new_callable=lambda: MockDjangoJSONEncoder) 
	@mock.patch('MHLogin.utils.decorators.cache.get',
			new_callable=lambda: lambda *args, **kwargs: 0)
	def test_forgot_password(self, mockcache, mockjson):
		# mockcache never returns hit, instead of mocking decorator which is a pita
		c = self.client
		# first try invalid user
		resp = c.get(reverse('forgot_password'))
		self.assertTemplateUsed(resp, 'forgotpassword.html')
		resp = c.post(reverse('forgot_password'), 
			{'username': 'buddy', 'email': 'buddy@nowhere.com'})
		self.assertTemplateUsed(resp, 'forgotpassword.html')
		# next try valid user with not enough data
		resp = c.get(reverse('forgot_password'))
		self.assertTemplateUsed(resp, 'forgotpassword.html')
		resp = c.post(reverse('forgot_password'), 
			{'username': 'docholiday'})
		self.assertTemplateUsed(resp, 'forgotpassword.html')

		# now try 1st valid user
		resp = c.get(reverse('forgot_password'))
		self.assertTemplateUsed(resp, 'forgotpassword.html')
		resp = c.post(reverse('forgot_password'), 
			{'username': 'healmeister', 'mobile_phone': '4085551212'})
		# for post success we get redirected to email sent url 
		self.assertTemplateNotUsed(resp, 'forgotpassword.html')
		# we should get a redirect on success to email 
		self.assertEqual(resp.status_code, 302, resp.status_code)

		# now try 2nd valid user and change their password
		resp = c.get(reverse('forgot_password'))
		self.assertTemplateUsed(resp, 'forgotpassword.html')
		with mock.patch('MHLogin.MHLUsers.forgotpassword.views.loader.render_to_string', 
				new_callable=lambda: self.mock_render2string):
			resp = c.post(reverse('forgot_password'), 
				{'username': 'docholiday', 'email': 'docholiday@tombstone.az.edu'})
		# for post success we get redirected to email sent url 
		self.assertTemplateNotUsed(resp, 'forgotpassword.html')
		# we should get a redirect on success to email 
		self.assertEqual(resp.status_code, 302, resp.status_code)
		# simulate email sent
		resp = c.get(reverse('email_sent'))
		self.assertTemplateUsed(resp, 'email_sent.html')
		# first try invalid token
		resp = c.get(reverse('password_change', kwargs={
			'token': 'foo', 'tempcode': 'bar'}))
		self.assertTemplateUsed(resp, 'newpassword.html')
		# second try valid token
		resp = c.get(reverse('password_change', kwargs={
			'token': self.mock_ctx['token'], 'tempcode': self.mock_ctx['tempcode']}))
		self.assertTemplateUsed(resp, 'newpassword.html')
		# only 1, still at form no re-direct
		resp = c.post(reverse('password_change', kwargs={
			'token': self.mock_ctx['token'], 'tempcode': self.mock_ctx['tempcode']}), 
				{'password1': '1231'})
		self.assertNotEqual(resp.status_code, 302, resp.status_code)
		# mismatch, still at form no re-direct
		resp = c.post(reverse('password_change', kwargs={
			'token': self.mock_ctx['token'], 'tempcode': self.mock_ctx['tempcode']}), 
				{'password1': '1231', 'password2': '1234'})
		self.assertNotEqual(resp.status_code, 302, resp.status_code)
		# same existing old pw, still at form no re-direct
		resp = c.post(reverse('password_change', kwargs={
			'token': self.mock_ctx['token'], 'tempcode': self.mock_ctx['tempcode']}), 
				{'password1': 'demo', 'password2': 'demo'})
		self.assertNotEqual(resp.status_code, 302, resp.status_code)
		# match, things look good, re-direct
		resp = c.post(reverse('password_change', kwargs={
			'token': self.mock_ctx['token'], 'tempcode': self.mock_ctx['tempcode']}), 
				{'password1': '1234', 'password2': '1234'})
		self.assertEqual(resp.status_code, 302, resp.status_code)
		# simulate password change complete!!
		resp = c.get(reverse('password_complete'))
		self.assertTemplateUsed(resp, 'complete.html')
		# verify they can login with new password!!  first try invalid (old)
		resp = c.post('/login/', {'username': 'docholiday', 'password': 'demo'})
		self.assertEqual(resp.status_code, 200)
		# now try valid
		resp = c.post('/login/', {'username': 'docholiday', 'password': '1234'})
		self.assertEqual(resp.status_code, 302)
		# verify we are logged in
		user = authenticate(username='docholiday', password='1234')
		self.assertEqual(c.session['_auth_user_id'], user.pk)
		self.assertEqual(user.username, 'docholiday')
		# all done, logout
		resp = c.logout()
		self.assertTrue('_auth_user_id' not in c.session)

	@mock.patch('MHLogin.MHLUsers.forgotpassword.views.DjangoJSONEncoder',
			new_callable=lambda: MockDjangoJSONEncoder) 
	@mock.patch('MHLogin.utils.decorators.cache.get',
			new_callable=lambda: lambda *args, **kwargs: 0)
	def test_forgot_password_while_logged_in(self, mockcache, mockjson):
		# mockcache never returns hit, instead of mocking decorator which is a pita
		c = self.client
		# test while logged in 
		c.post('/login/', {'username': 'docholiday', 'password': 'demo'})
		# valid user and change their password
		resp = c.get(reverse('forgot_password'))
		self.assertTemplateUsed(resp, 'forgotpassword.html')
		with mock.patch('MHLogin.MHLUsers.forgotpassword.views.loader.render_to_string', 
				new_callable=lambda: self.mock_render2string):
			resp = c.post(reverse('forgot_password'), 
				{'username': 'docholiday', 'email': 'docholiday@tombstone.az.edu'})
		# for post success we get redirected to email sent url 
		self.assertTemplateNotUsed(resp, 'forgotpassword.html')
		# we should get a redirect on success to email 
		self.assertEqual(resp.status_code, 302, resp.status_code)
		# simulate email sent
		resp = c.get(reverse('email_sent'))
		self.assertTemplateUsed(resp, 'email_sent.html')
		# valid token
		resp = c.get(reverse('password_change', kwargs={
			'token': self.mock_ctx['token'], 'tempcode': self.mock_ctx['tempcode']}))
		self.assertTemplateUsed(resp, 'newpassword.html')
		# match, things look good, re-direct
		resp = c.post(reverse('password_change', kwargs={
			'token': self.mock_ctx['token'], 'tempcode': self.mock_ctx['tempcode']}), 
				{'password1': '1234', 'password2': '1234'})
		self.assertEqual(resp.status_code, 302, resp.status_code)
		# simulate password change complete!!
		resp = c.get(reverse('password_complete'))
		self.assertTemplateUsed(resp, 'complete.html')
		# all done, logout
		resp = c.logout()
		self.assertTrue('_auth_user_id' not in c.session)

	def mock_render2string(self, template_name, dictionary=None, context_instance=None):
		self.mock_ctx = dictionary
		return "Unit testing, email body..."

