import json

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase

from MHLogin.MHLPractices.models import PracticeLocation
from MHLogin.MHLUsers.models import OfficeStaff, Provider, \
	Office_Manager
from MHLogin.apps.smartphone.v1.tests.utils import generateHttpRequest,\
	create_org_type, ct_practice
from MHLogin.apps.smartphone.v1.views_device import check_in, dissociate, \
	app_version_update, register_push_token, re_key
from MHLogin.utils.tests import create_user
from MHLogin.utils.tests.tests import clean_db_datas


#add by xlin 130106 to test associate
class AssociateTest(TestCase):
	@classmethod
	def setUpClass(cls):
		clean_db_datas()
		organization_type = create_org_type()
		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',
								mdcom_phone='8005550085',
								organization_type=organization_type)
		practice.save()
		cls.practice = practice

		user = create_user('practicemgr1', 'lin', 'xing', 'demo')
		cls.user = user

	@classmethod
	def tearDownClass(cls):
		clean_db_datas()

	def setUp(self):
		pass

	def tearDown(self):
		self.client.logout()

	def test_associate_get(self):
		#get method
		data = {}
		response = self.client.get(reverse('MHLogin.apps.smartphone.v1.views_device.associate'), data=data)
		self.assertEqual(response.status_code, 400)
		msg = json.loads(response.content)
		self.assertEqual(msg['errno'], 'GE002')

	def test_associate_formvalid(self):
		#error user
		data = {'username': '',
			'password':'demo',
			'device_id':'e2c73b2b28f7466da855005ef48cdeaa',
			'app_version':'1.00.22',
			'platform':'iPad', }
		response = self.client.post(reverse('MHLogin.apps.smartphone.v1.views_device.associate'), data=data)
		self.assertEqual(response.status_code, 400)
		msg = json.loads(response.content)
		self.assertEqual(msg['errno'], 'GE031')

	def test_associate_allow_staff(self):
		provider = Provider(office_lat=0.0, office_longit=0.0, user=self.user)
		provider.save()
		self.user = provider
		self.user.save()

		providerData = {'username': self.user.user.username,
			'password': 'demo',
			'device_id': 'e2c73b2b28f7466da855005ef48cdeaa',
			'app_version': '1.00.22',
			'allow_staff_login': 1,
			'platform': 'iPad', }
		response = self.client.post(reverse('MHLogin.apps.smartphone.v1.views_device.associate'), 
								data=providerData)
		self.assertEqual(response.status_code, 200)

	def test_associate_err_user(self):
		data = {'username': 'abc',
			'password': 'demo',
			'device_id': 'e2c73b2b28f7466da855005ef48cdeaa',
			'app_version': '1.00.22',
			'allow_staff_login': 1,
			'platform': 'iPad', }
		response = self.client.post(reverse('MHLogin.apps.smartphone.v1.views_device.associate'), data=data)
		self.assertEqual(response.status_code, 400)
		msg = json.loads(response.content)
		self.assertEqual(msg['errno'], 'DM001')

	def test_associate_provider(self):
		provider = Provider(office_lat=0.0, office_longit=0.0, user=self.user)
		provider.save()
		self.user = provider
		self.user.save()

		providerData = {'username': self.user.user.username,
			'password': 'demo',
			'device_id': 'e2c73b2b28f7466da855005ef48cdeaa',
			'app_version': '1.00.22',
			'platform': 'iPad', }
		response = self.client.post(reverse('MHLogin.apps.smartphone.v1.views_device.associate'), 
								data=providerData)
		self.assertEqual(response.status_code, 200)

	def test_associate_staff(self):
		staff = OfficeStaff(user=self.user)
		staff.save()
		self.user = staff
		self.user.save()
		staffData = {'username': self.user.user.username,
			'password': 'demo',
			'device_id': 'e2c73b2b28f7466da855005ef48cdeaa',
			'app_version': '1.00.22',
			'platform': 'iPad', }
		response = self.client.post(reverse('MHLogin.apps.smartphone.v1.views_device.associate'), 
								data=staffData)
		self.assertEqual(response.status_code, 400)
		msg = json.loads(response.content)
		self.assertEqual(msg['errno'], 'DM002')

	def test_associate_manager(self):
		staff2 = OfficeStaff(user=self.user, current_practice=self.practice)
		staff2.save()
		manager = Office_Manager(user=staff2, practice=self.practice, manager_role=2)
		manager.save()
		self.user = manager
		self.user.save()
		staff2Data = {'username': self.user.user.user.username,
			'password': 'demo',
			'device_id': 'e2c73b2b28f7466da855005ef48cdeaa',
			'app_version': '1.00.22',
			'platform': 'iPad', }
		response = self.client.post(reverse('MHLogin.apps.smartphone.v1.views_device.associate'), 
								data=staff2Data)
		self.assertEqual(response.status_code, 200)


#add by xlin 130106 to test check_user
class CheckUserTest(TestCase):
	@classmethod
	def setUpClass(cls):
		clean_db_datas()

		organization_type = create_org_type()
		practice = ct_practice('name', organization_type)
		cls.practice = practice

		user = create_user('practicemgr1', 'lin', 'xing', 'demo')
		cls.user = user

	@classmethod
	def tearDownClass(cls):
		clean_db_datas()

	def setUp(self):
		pass

	def tearDown(self):
		self.client.logout()

	def test_check_user(self):
		#get
		response = self.client.get(reverse('MHLogin.apps.smartphone.v1.views_device.check_user'))
		self.assertEqual(response.status_code, 400)
		msg = json.loads(response.content)
		self.assertEqual(msg['errno'], 'GE002')

		#post invliad user name
		invalidData = {'username': 'xlin'}
		response = self.client.post(reverse('MHLogin.apps.smartphone.v1.views_device.check_user'), 
								data=invalidData)
		self.assertEqual(response.status_code, 400)
		msg = json.loads(response.content)
		self.assertEqual(msg['errno'], 'PF001')

		#post valid user name
		username = 'linxing'
		user = User(username=username)
		user.save()
		validData = {'username': username}
		response = self.client.post(reverse('MHLogin.apps.smartphone.v1.views_device.check_user'), 
								data=validData)
		self.assertEqual(response.status_code, 200)


#add by xlin 130106 to test dissociate
class DissociateTest(TestCase):
	def test_dissociate(self):
		request = generateHttpRequest()
		result = dissociate(request)
		self.assertEqual(result.status_code, 200)


#add by xlin 130106 to test check_in
class CheckInTest(TestCase):
	def test_check_in(self):
		request = generateHttpRequest()

		request.method = 'GET'
		result = check_in(request)
		msg = json.loads(result.content)
		self.assertEqual(msg['errno'], 'GE002')

		request.method = 'POST'
		result = check_in(request)
		self.assertEqual(result.status_code, 200)

		request.POST['key'] = 'abc'
		request.POST['rx_timestamp'] = '123'
		request.POST['tx_timestamp'] = 'adf'
		result = check_in(request)
		self.assertEqual(result.status_code, 400)
		msg = json.loads(result.content)
		self.assertEqual(msg['errno'], 'GE031')


#add by xlin 130107 to test app_version_update
class AppVersionUpdateTest(TestCase):
	def test_app_version_update(self):
		request = generateHttpRequest()

		request.method = 'GET'
		result = app_version_update(request)
		msg = json.loads(result.content)
		self.assertEqual(msg['errno'], 'GE002')

		request.method = 'POST'
		request.POST['app_version'] = '1.22'
		result = app_version_update(request)
		self.assertEqual(result.status_code, 200)


#add by xlin 130107 to test register_push_token
class RegisterPushTokenTest(TestCase):
	def test_register_push_token(self):
		request = generateHttpRequest()

		request.method = 'GET'
		result = register_push_token(request)
		msg = json.loads(result.content)
		self.assertEqual(msg['errno'], 'GE002')

		request.method = 'POST'
		request.POST['token'] = 'abc'
		result = register_push_token(request)
		msg = json.loads(result.content)
		self.assertEqual(msg['errno'], 'GE031')

		request.POST['token'] = 'abcdefetyuabcdefetyuabcdefetyuabcdefetyuabcdefetyuabcdefetyuacsw'
		result = register_push_token(request)
		self.assertEqual(result.status_code, 200)


#add by xlin 130107 to test re_key
class ReKeyTest(TestCase):
	def test_re_key(self):
		request = generateHttpRequest()

		result = re_key(request)
		self.assertEqual(result.status_code, 400)
		msg = json.loads(result.content)
		self.assertEqual(msg['errno'], 'GE100')

