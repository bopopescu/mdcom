import datetime
import json

from django.core.urlresolvers import reverse
from django.test.testcases import TestCase

from MHLogin.MHLPractices.models import PracticeLocation, Pending_Association, \
	AccountActiveCode
from MHLogin.MHLPractices.views import checkActiveCode
from MHLogin.MHLSites.models import Site
from MHLogin.MHLUsers.models import OfficeStaff, Office_Manager
from MHLogin.utils.tests import create_user
from boto.provider import Provider
from MHLogin.utils.tests.tests import clean_db_datas


#add by xlin 121226 to test getPenddings MHLogin.MHLPractices.views.getPenddings
class getPenddingsTest(TestCase):
	@classmethod
	def setUpClass(cls):
		clean_db_datas()
		cls.user = create_user('practicemgr1', 'lin', 'xing', 'demo')

		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice.save()
		cls.practice = practice

	@classmethod
	def tearDownClass(cls):
		clean_db_datas()

	def setUp(self):
		self.client.post('/login/', {'username': self.user.username, 'password': 'demo'})

	def tearDown(self):
		self.client.logout()

	def test_getPenddings(self):
		staff = OfficeStaff(user=self.user)
		staff.current_practice = self.practice
		staff.save()
		staff.practices.add(self.practice)
		manager = Office_Manager(user=staff, practice=self.practice, manager_role=2)
		manager.save()

		response = self.client.post(reverse('MHLogin.MHLPractices.views.getPenddings'))
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 0)

		pend = Pending_Association(from_user=self.user, to_user=self.user, practice_location=self.practice, created_time=datetime.datetime.now())
		pend.save()

		response = self.client.post(reverse('MHLogin.MHLPractices.views.getPenddings'))
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 1)


#add by xlin 121226 to test sucessActive
class SucessActiveTest(TestCase):
	@classmethod
	def setUpClass(cls):
		clean_db_datas()
		cls.user = create_user('practicemgr1', 'lin', 'xing', 'demo')

		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice.save()
		cls.practice = practice

	@classmethod
	def tearDownClass(cls):
		clean_db_datas()

	def setUp(self):
		self.client.post('/login/', {'username': self.user.username, 'password': 'demo'})

	def tearDown(self):
		self.client.logout()

	def test_sucessActive(self):
		staff = OfficeStaff(user=self.user)
		staff.current_practice = self.practice
		staff.save()
		staff.practices.add(self.practice)
		manager = Office_Manager(user=staff, practice=self.practice, manager_role=2)
		manager.save()

		response = self.client.post(reverse('MHLogin.MHLPractices.views.sucessActive'))
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'Staff/sucessActive.html')


#add by xlin 121226 to test staffHome
class StaffHomeTest(TestCase):
	@classmethod
	def setUpClass(cls):
		clean_db_datas()
		cls.user = create_user('practicemgr1', 'lin', 'xing', 'demo')

		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice.save()
		cls.practice = practice

	@classmethod
	def tearDownClass(cls):
		clean_db_datas()

	def setUp(self):
		self.client.post('/login/', {'username': self.user.username, 'password': 'demo'})

	def tearDown(self):
		self.client.logout()

	def test_staffHome(self):
		staff = OfficeStaff(user=self.user)
		staff.current_practice = self.practice
		staff.save()
		staff.practices.add(self.practice)
		manager = Office_Manager(user=staff, practice=self.practice, manager_role=2)
		manager.save()

		response = self.client.post(reverse('MHLogin.MHLPractices.views.staffHome'))
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'Staff/staffHome.html')


#add by xlin to test checkActiveCode
class checkActiveCodeTest(TestCase):
	def test_checkActiveCode(self):
		code = ''
		email = ''
		result = checkActiveCode(code, email)
		self.assertEqual(result[2], False)

		acc = AccountActiveCode(code='abc', recipient='a@a.cn', sender=1, userType=1)
		acc.save()
		result = checkActiveCode(code, email)
		self.assertEqual(result[2], False)


#add by xlin 130104 to test practice_main_view
class PracticeMainViewTest(TestCase):
	@classmethod
	def setUpClass(cls):
		clean_db_datas()
		cls.user = create_user('practicemgr1', 'lin', 'xing', 'demo')

		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice.save()
		cls.practice = practice

	@classmethod
	def tearDownClass(cls):
		clean_db_datas()

	def setUp(self):
		self.client.post('/login/', {'username': self.user.username, 'password': 'demo'})

	def tearDown(self):
		self.client.logout()

	def test_practice_main_view(self):
		#403
#		response = self.client.post(reverse('MHLogin.MHLPractices.views.practice_main_view'))
#		self.assertEqual(response.status_code, 403)

		staff = OfficeStaff(user=self.user)
		staff.save()
		staff.practices.add(self.practice)

		#staff no current practice
		response = self.client.post(reverse('MHLogin.MHLPractices.views.practice_main_view'))
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'dashboard_office_staff.html')

		#staff and current practice
		staff.current_practice = self.practice
		staff.save()
		response = self.client.post(reverse('MHLogin.MHLPractices.views.practice_main_view'))
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'dashboard_office_staff.html')

		#manger
		manager = Office_Manager(user=staff, practice=self.practice, manager_role=2)
		manager.save()

		response = self.client.post(reverse('MHLogin.MHLPractices.views.practice_main_view'))
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'dashboard_office_manager.html')

		#manager and current site
		site = Site(name='test site', address1='test address', lat='0.4', longit='4.1')
		staff.current_site = site
		staff.save()
		response = self.client.post(reverse('MHLogin.MHLPractices.views.practice_main_view'))
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'dashboard_office_manager.html')


#add xlin 130104 to test practice_profile_view
class PracticeProfileViewTest(TestCase):
	@classmethod
	def setUpClass(cls):
		clean_db_datas()
		cls.user = create_user('practicemgr1', 'lin', 'xing', 'demo')

		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice.save()
		cls.practice = practice

	@classmethod
	def tearDownClass(cls):
		clean_db_datas()

	def setUp(self):
		self.client.post('/login/', {'username': self.user.username, 'password': 'demo'})

	def tearDown(self):
		self.client.logout()

	def test_practice_profile_view_manager(self):
		staff = OfficeStaff(user=self.user)
		staff.current_practice = self.practice
		staff.save()
		staff.practices.add(self.practice)

		manager = Office_Manager(user=staff, practice=self.practice, manager_role=1)
		manager.save()

		response = self.client.post(reverse('MHLogin.MHLPractices.views.practice_profile_view'))
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'Profile/practice_profile_view.html')

		manager.manager_role = 2
		manager.save()
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'Profile/practice_profile_view.html')

	def test_practice_profile_view_staff(self):
		#403
		staff = OfficeStaff(user=self.user)
		staff.current_practice = self.practice
		staff.save()
		staff.practices.add(self.practice)

		response = self.client.post(reverse('MHLogin.MHLPractices.views.practice_profile_view'))
		self.assertEqual(response.status_code, 403)


#add by xlin 130104 to test practice_profile_edit
class PracticeProfileEditTest(TestCase):
	@classmethod
	def setUpClass(cls):
		clean_db_datas()
		cls.user = create_user('practicemgr1', 'lin', 'xing', 'demo')

		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice.save()
		cls.practice = practice

	@classmethod
	def tearDownClass(cls):
		clean_db_datas()

	def setUp(self):
		self.client.post('/login/', {'username': self.user.username, 'password': 'demo'})

	def tearDown(self):
		self.client.logout()

	def test_practice_profile_edit_staff(self):
		staff = OfficeStaff(user=self.user)
		staff.current_practice = self.practice
		staff.save()
		staff.practices.add(self.practice)
		staff.save()

		response = self.client.post(reverse('MHLogin.MHLPractices.views.practice_profile_edit'))
		self.assertEqual(response.status_code, 403)

	def test_practice_profile_edit_manager(self):
		staff = OfficeStaff(user=self.user)
		staff.current_practice = self.practice
		staff.save()
		staff.practices.add(self.practice)

		manager = Office_Manager(user=staff, practice=self.practice, manager_role=1)
		manager.save()

		response = self.client.get(reverse('MHLogin.MHLPractices.views.practice_profile_edit'))
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'Profile/practice_profile_edit.html')
