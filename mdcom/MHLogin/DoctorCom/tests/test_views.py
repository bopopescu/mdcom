
import json
import mock
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.conf import settings
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from MHLogin.DoctorCom.models import Click2Call_Log
from MHLogin.DoctorCom.IVR.utils import TYPE_CALLED, TYPE_CALLER
from MHLogin.DoctorCom.IVR.utils import get_active_call
from MHLogin.MHLCallGroups.models import CallGroup
from MHLogin.MHLPractices.models import PracticeLocation
from MHLogin.MHLUsers.models import OfficeStaff, Office_Manager, \
	MHLUser, Provider, Physician, NP_PA
from MHLogin.utils.tests import create_user


class PraticeInfoTest(TestCase):
	@classmethod
	def setUpClass(cls):
		cls.user = create_user('practicemgr5', 'lin', 'xing', 'demo', '', '', '', '',)

		call_group = CallGroup(description='test', team='team')
		call_group.save()
		cls.call_group = call_group

		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',
								call_group=call_group,)
		practice.save()
		practice.call_groups.add(call_group)
		cls.practice = practice

	@classmethod
	def tearDownClass(cls):
		OfficeStaff.objects.all().delete()
		Office_Manager.objects.all().delete()
		PracticeLocation.objects.all().delete()
		CallGroup.objects.all().delete()
		MHLUser.objects.all().delete()

	def test_pratice_info(self):
		self.client.post('/login/', {'username': self.user.username,
			'password': 'demo'})
		staff = OfficeStaff(user=self.user)
		staff.save()
		staff.practices.add(self.practice)
		staff.current_practice = self.practice
		staff.save()
		manager = Office_Manager(user=staff, practice=self.practice, manager_role=1)
		manager.save()

		response = self.client.get(reverse('MHLogin.DoctorCom.views.practice_info'))
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'MHLUsers/practice_info.html')
		self.client.logout()


class DoctorComViews(TestCase):
	@classmethod
	def setUpClass(cls):
		cls.provider = Provider.objects.create(username='healmeister', first_name='heal',
			last_name='meister', address1="555 Bryant St.", city="Palo Alto", state="CA", 
			lat=0.0, longit=0.0, office_lat=0.0, office_longit=0.0, is_active=True, 
			tos_accepted=True, mobile_confirmed=True, mdcom_phone='123', mobile_phone='456')
		cls.provider.set_password('demo')
		cls.provider.user = cls.provider  # for our unique prov-user reln
		cls.provider.user_permissions.add(Permission.objects.get(codename='can_call_transfer', 
			content_type=ContentType.objects.get_for_model(MHLUser)))
		cls.provider.save()

		cls.docprov = Provider.objects.create(username='docholiday', first_name='doc',
			last_name='holiday', address1="555 Bryant St.", city="Palo Alto", state="CA", 
			lat=0.0, longit=0.0, office_lat=0.0, office_longit=0.0, is_active=True, 
			tos_accepted=True, mobile_confirmed=True, mdcom_phone='101', mobile_phone='202')
		cls.docprov.set_password('demo')
		cls.docprov.user = cls.docprov  # for our unique prov-user reln
		cls.docprov.save()
		Physician.objects.create(user=cls.docprov)
		NP_PA.objects.create(user=cls.docprov)

	@classmethod
	def tearDownClass(cls):
		Click2Call_Log.objects.all().delete()
		OfficeStaff.objects.all().delete()
		MHLUser.objects.all().delete()
		Provider.objects.all().delete()
		Physician.objects.all().delete()

	def test_provider_view(self):
		c = self.client
		# after successful login should get re-direct to /
		response = c.post('/login/', {'username': self.provider.username,
									'password': 'demo'})
		self.assertEqual(response.status_code, 302)
		# get main provider info page before click2call
		response = c.get(reverse('MHLogin.DoctorCom.views.provider_info') +
						'?provider=' + str(self.provider.id))
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'MHLUsers/tab_provider_info.html')
		# now logout, we can alternatively call c.post('/logout/')
		response = c.logout()

		# after successful login should get re-direct to /
		response = c.post('/login/', {'username': self.docprov.username,
									'password': 'demo'})
		self.assertEqual(response.status_code, 302)
		# get main provider view page before click2call
		response = c.get(reverse('MHLogin.DoctorCom.views.provider_view') +
						'?provider=' + str(self.docprov.id))
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'MHLUsers/provider_info.html')
		# get main provider info page before click2call
		response = c.get(reverse('MHLogin.DoctorCom.views.provider_info') +
						'?provider=' + str(self.docprov.id))
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'MHLUsers/tab_provider_info.html')
		# get office_staff_info
		response = c.get(reverse('MHLogin.DoctorCom.views.office_staff_info') +
						'?provider=' + str(self.docprov.id))
		self.assertTemplateUsed(response, 'MHLUsers/tab_officeuser_info.html')
		# now logout, we can alternatively call c.post('/logout/')
		response = c.logout()

	class TwilioResp(object):
		if (settings.TWILIO_PHASE == 2):
			content = json.dumps(
					{'sid': 'CAfabc0000000000000000000000000000',
					'to': '+16505551212', 'from': '+16505550000'}
				)
		else:
			content = json.dumps({"TwilioResponse":
				{'Call':
					{'Sid': 'CAfabc0000000000000000000000000000',
					'Called': '6505551212', 'Caller': '6505550000',
					'Flags': 2, 'Annotation': None}, 
					}
				})

	@mock.patch('MHLogin.DoctorCom.IVR.utils.get_active_call', return_value=None)
	@mock.patch('MHLogin.DoctorCom.views.make_twilio_request', return_value=TwilioResp())
	def test_provider_click2call_view(self, resp, call):
		c = self.client
		# after successful login should get re-direct to /
		response = c.post('/login/', {'username': self.provider.username,
									'password': 'demo'})
		self.assertEqual(response.status_code, 302)	
		response = c.get(reverse('MHLogin.DoctorCom.views.click2call_initiate') +
					'?called_number=678')
		# should get 200, 403's if CALL_ENABLE False in settings
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'DoctorCom/call_in_progress.html')
		# now logout, we can alternatively call c.post('/logout/')
		response = c.logout()
		self.assertTrue(Click2Call_Log.objects.filter(called_number='678').exists(), 
					"CallLog missing")

	def mock_get_active_call(self):
		def fn(mhphone, ctype=TYPE_CALLED, status=1):
			call = None
			if ctype == TYPE_CALLED:
				if (settings.TWILIO_PHASE == 2):
					call = {'from': 'not_a_mobile', 'sid': 'CA00000000000000000000000000000000'}
				else:
					call = {'Caller': 'not_a_mobile', 'Sid': 'CA00000000000000000000000000000000'}
			return call
		return fn

	@mock.patch('MHLogin.DoctorCom.IVR.utils.get_active_call', 
		new_callable=mock_get_active_call, self=None)
	@mock.patch('MHLogin.DoctorCom.views.make_twilio_request', return_value=TwilioResp())
	def test_provider_click2xfer_view(self, resp, call):
		c = self.client
		# after successful login should get re-direct to /
		response = c.post('/login/', {'username': self.provider.username,
									'password': 'demo'})
		self.assertEqual(response.status_code, 302)
		response = c.get(reverse('MHLogin.DoctorCom.views.click2call_initiate') +
					'?called_number=9999')
		# should get 200, 403's if CALL_ENABLE False in settings
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'DoctorCom/call_in_progress.html')
		# now logout, we can alternatively call c.post('/logout/')
		response = c.logout()
		self.assertTrue(Click2Call_Log.objects.filter(called_number='9999').exists(), 
					"CallLog missing")

	class TwilioResps(object):
		if (settings.TWILIO_PHASE == 2):
			content = json.dumps({'calls': [
				{'sid': 'CAfabc0000000000000000000000000000',
				'to': '+16505551212', 'from': '+16505550000'},
				]})
		else:
			content = json.dumps({'TwilioResponse':
				{'Calls': [
					{'Call':
						{'Sid': 'CAfabc0000000000000000000000000000',
						'Called': '6505551212', 'Caller': '6505550000'},
					}, ]
				}})		

	def mock_make_twilio_request(self):
		return lambda method, uri, **kwargs: self.TwilioResps()

	def test_get_active_call(self):
		# TODO: move to IVR/tests.py
		with mock.patch('MHLogin.DoctorCom.IVR.utils.make_twilio_request', 
					new_callable=self.mock_make_twilio_request):
			call1 = get_active_call('6505551212', ctype=TYPE_CALLED)
			call2 = get_active_call('6505550000', ctype=TYPE_CALLER)
		if (settings.TWILIO_PHASE == 2):
			self.assertTrue(call1['to'] == '+16505551212', call1['to'])
			self.assertTrue(call2['from'] == '+16505550000', call2['from'])
		else:	
			self.assertTrue(call1['Called'] == '6505551212', call1['Called'])
			self.assertTrue(call2['Caller'] == '6505550000', call2['Caller'])

