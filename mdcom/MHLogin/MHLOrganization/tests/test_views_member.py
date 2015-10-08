'''
Created on 2013-5-8

@author: pyang
'''
import mock

from django.test.testcases import TestCase
from MHLogin.utils.tests.tests import clean_db_datas, create_user
from MHLogin.MHLPractices.models import PracticeLocation,\
	OrganizationRelationship, Pending_Association, OrganizationSetting,\
	OrganizationType
from django.core.urlresolvers import reverse
import time
from MHLogin.MHLUsers.models import OfficeStaff, Office_Manager, Provider,\
	Administrator, MHLUser
import json
import datetime
from MHLogin.api.v1.tests.utils import get_random_username
from MHLogin.Invites.models import Invitation
from MHLogin.MHLCallGroups.models import CallGroup
from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from MHLogin.MHLCallGroups.Scheduler.models import EventEntry
from MHLogin.DoctorCom.IVR.models import VMBox_Config
from django.contrib.auth import authenticate
from MHLogin.DoctorCom.Messaging.models import Message, MessageRecipient
from MHLogin.DoctorCom.Messaging.tests import DevNull
from MHLogin.KMS.utils import generate_keys_for_users

class CurrentProvidersTest(TestCase):
	@classmethod
	def setUpClass(cls):
		clean_db_datas()
		cls.user = create_user('practicemgr1', 'lin', 'xing', 'demo')

		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice.save()
		practice1 = PracticeLocation(practice_name='test1',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice1.save()
		
		OrganizationRelationship.objects.create(organization=practice,\
				parent=practice1,create_time=int(time.time()),billing_flag=True)
		cls.practice = practice
		staff = OfficeStaff()
		staff.user = cls.user
		staff.office_lat = 0.0
		staff.office_longit = 0.0
		staff.current_practice = practice
		staff.save()
		staff.practices.add(practice)
		
		mgr = Office_Manager(user=staff, practice=practice, manager_role=2)
		mgr.save()
	@classmethod
	def tearDownClass(cls):
		clean_db_datas()

	def setUp(self):
		self.client.post('/login/', {'username': self.user.username, 'password': 'demo'})

	def tearDown(self):
		self.client.logout()
		
	def testCurrentProviders(self):
		response = self.client.get(reverse('MHLogin.MHLOrganization.views_member.currentProviders'),\
					data={'org_id': self.practice.id})
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'MHLOrganization/Member/member_provider_list.html')

class CurrentOfficeStaffTest(TestCase):
	@classmethod
	def setUpClass(cls):
		clean_db_datas()
		cls.user = create_user('practicemgr1', 'lin', 'xing', 'demo')
		cls.admin = create_user("sduper", "super", "duper", "demo", 
							"Ocean Avenue", "Carmel", "CA", "93921", uklass=Administrator)
		cls.admin.save()
		org_setting = OrganizationSetting(can_have_manager=True,\
						can_have_nurse=True,can_have_dietician=True)
		org_setting.save()
		org_type = OrganizationType(name="Test Org Type", \
						organization_setting=org_setting, is_public=True)
		org_type.save()
		cls.org_type = org_type
		cls.org_setting = org_setting
		
		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',
								organization_setting =org_setting,
								organization_type = org_type)
		practice.save()
		practice1 = PracticeLocation(practice_name='test1',
								practice_longit='0.1',
								practice_lat='0.0',
								organization_setting =org_setting,
								organization_type = org_type)
		practice1.save()
		cls.practice = practice
		cls.practice1 = practice1
		
		staff = OfficeStaff()
		staff.user = cls.user
		staff.office_lat = 0.0
		staff.office_longit = 0.0
		staff.current_practice = practice
		staff.save()
		staff.practices.add(practice)
		cls.staff = staff
		
		mgr = Office_Manager(user=staff, practice=practice, manager_role=2)
		mgr.save()
	@classmethod
	def tearDownClass(cls):
		clean_db_datas()

	def setUp(self):
		self.client.post('/login/', {'username': self.user.username, 'password': 'demo'})

	def tearDown(self):
		self.client.logout()
		
	def testCurrentOfficeStaff(self):
		response = self.client.get(reverse('MHLogin.MHLOrganization.views_member.currentOfficeStaff'),\
					data={'org_id': self.practice.id})
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'MHLOrganization/Member/member_staff_list.html')
		
		response = self.client.get(reverse('MHLogin.MHLOrganization.views_member.currentOfficeStaff'),\
					data={'org_id': self.practice.id,'lastName':'peng'})
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'MHLOrganization/Member/member_staff_list.html')
		
class AddAssociationTest(TestCase):
	@classmethod
	def setUpClass(cls):
		clean_db_datas()
		cls.user = create_user('practicemgr1', 'lin', 'xing', 'demo')
		cls.user1 = create_user('practicemgr2', 'lin', 'xing', 'demo')

		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice.save()
		practice1 = PracticeLocation(practice_name='test1',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice1.save()
		
		OrganizationRelationship.objects.create(organization=practice,\
				parent=practice1,create_time=int(time.time()),billing_flag=True)
		cls.practice = practice
		cls.practice1 = practice1
		staff = OfficeStaff()
		staff.user = cls.user
		staff.office_lat = 0.0
		staff.office_longit = 0.0
		staff.current_practice = practice
		staff.save()
		staff.practices.add(practice)
		cls.staff = staff

		provider = create_user('Provoder1', 'pro1', 'pro1', 'demo', uklass=Provider)
		provider.practices.add(practice1)
		cls.provider = provider

		mgr = Office_Manager(user=staff, practice=practice, manager_role=2)
		mgr.save()
	@classmethod
	def tearDownClass(cls):
		clean_db_datas()

	def setUp(self):
		self.client.post('/login/', {'username': self.user.username, 'password': 'demo'})

	def tearDown(self):
		self.client.logout()
		
	def testAddAssociation(self):
		response = self.client.post(reverse('MHLogin.MHLOrganization.views_member.addAssociation'),\
					data={'org_id': self.practice.id,'prov_id':self.provider.user.id,\
						'userType':1})
		self.assertEqual(response.status_code, 200)
		try:
			association = Pending_Association.objects.get(from_user=self.user)
			self.assertEqual(association.to_user_id, self.provider.user.id)
		except:
			with self.assertRaises(Pending_Association.DoesNotExist): \
					Pending_Association.objects.get(from_user=self.user)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 1)
		
		response = self.client.post(reverse('MHLogin.MHLOrganization.views_member.addAssociation'),\
					data={'org_id': self.practice.id,'prov_id':self.staff.user.id,\
						'userType':0})
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 1)
		
		response = self.client.get(reverse('MHLogin.MHLOrganization.views_member.addAssociation'),\
					data={'org_id': self.practice.id,'prov_id':self.provider.user.id,\
						'userType':1})
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 1)
		
		response = self.client.get(reverse('MHLogin.MHLOrganization.views_member.addAssociation'),\
					data={'org_id': self.practice.id,'prov_id':self.staff.user.id,\
						'userType':0})
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 1)

class RemoveAssociationTest(TestCase):
	@classmethod
	def setUpClass(cls):
		clean_db_datas()
		cls.user = create_user(get_random_username(), 'lin', 'xing', 'demo')
		cls.user1 = create_user(get_random_username(), 'y', 'p', 'demo')
		cls.user2 = create_user(get_random_username(), 'y', 'p', 'demo')
		cls.to_user = create_user(get_random_username(), "tian", "thj", "demo", "555 Bryant St.",
								"Palo Alto", "CA", "")

		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice.save()
		practice1 = PracticeLocation(practice_name='test1',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice1.save()
		
		OrganizationRelationship.objects.create(organization=practice,\
				parent=practice1,create_time=int(time.time()),billing_flag=True)
		cls.practice = practice
		cls.practice1 = practice1
		
		assoc = Pending_Association()
		assoc.from_user = cls.user1
		assoc.to_user = cls.to_user
		assoc.practice_location = practice
		assoc.created_time = datetime.datetime(2013, 5, 14, 12, 30)
		assoc.resent_time = datetime.datetime(2013, 5, 14, 13, 30)
		assoc.save()
		cls.assoc = assoc
		
		provider = Provider(user=cls.to_user, office_lat=0.0, office_longit=0.0, current_practice = practice)
		provider.save()
		cls.provider = provider
		
		staff = OfficeStaff()
		staff.user = cls.user
		staff.office_lat = 0.0
		staff.office_longit = 0.0
		staff.current_practice = practice
		staff.save()
		staff.practices.add(practice)
		
		mgr = Office_Manager(user=staff, practice=practice, manager_role=2)
		mgr.save()
	@classmethod
	def tearDownClass(cls):
		clean_db_datas()

	def setUp(self):
		self.client.post('/login/', {'username': self.user.username, 'password': 'demo'})

	def tearDown(self):
		self.client.logout()
		
	def testRemoveAssociation(self):
		response = self.client.get(reverse('MHLogin.MHLOrganization.views_member.removeAssociation'),\
					data={'org_id': self.practice.id})
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 1)
		response = self.client.post(reverse('MHLogin.MHLOrganization.views_member.removeAssociation'),\
					data={'org_id': self.practice.id,'assoc_id':self.assoc.id})
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 2)
		

		
class AddProviderToPracticeTest(TestCase):
	@classmethod
	def setUpClass(cls):
		clean_db_datas()
		cls.user = create_user('practicemgr1', 'lin', 'xing', 'demo')
		cls.user1 = create_user('practicemgr2', 'lin', 'xing', 'demo')
		cls.from_user = create_user(get_random_username(), "tian", "thj", "demo", "555 Bryant St.",
								"Palo Alto", "CA", "")

		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice.save()
		practice1 = PracticeLocation(practice_name='test1',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice1.save()
		
		OrganizationRelationship.objects.create(organization=practice,\
				parent=practice1,create_time=int(time.time()),billing_flag=True)
		cls.practice = practice
		staff = OfficeStaff()
		staff.user = cls.user
		staff.office_lat = 0.0
		staff.office_longit = 0.0
		staff.current_practice = practice
		staff.save()
		staff.practices.add(practice)
		
		assoc = Pending_Association()
		assoc.from_user = cls.from_user
		assoc.to_user = cls.user1
		assoc.practice_location = practice
		assoc.created_time = datetime.datetime(2013, 5, 14, 12, 30)
		assoc.resent_time = datetime.datetime(2013, 5, 14, 13, 30)
		assoc.save()
		cls.assoc = assoc
		
		provider = Provider(user=cls.from_user, office_lat=0.0, office_longit=0.0, current_practice = practice)
		provider.save()
		cls.provider = provider
		
		mgr = Office_Manager(user=staff, practice=practice, manager_role=2)
		mgr.save()
	@classmethod
	def tearDownClass(cls):
		clean_db_datas()

	def setUp(self):
		self.client.post('/login/', {'username': self.user.username, 'password': 'demo'})

	def tearDown(self):
		self.client.logout()

	@mock.patch('MHLogin.apps.smartphone.v1.views_account.thread.start_new_thread', autospec=True)
	def testAddProviderToPractice(self, start_thrad):
		response = self.client.post(reverse('MHLogin.MHLOrganization.views_member.addProviderToPractice'),\
					data={'org_id': self.practice.id})
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 1)
		response = self.client.get(reverse('MHLogin.MHLOrganization.views_member.addProviderToPractice'),\
					data={'org_id': self.practice.id,'assoc_id':self.assoc.id})
		self.assertEqual(response.status_code, 200)
		with self.assertRaises(Pending_Association.DoesNotExist): \
				Pending_Association.objects.get(pk=self.assoc.id)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 2)
		
class RejectAssociationTest(TestCase):
	@classmethod
	def setUpClass(cls):
		clean_db_datas()
		cls.user = create_user('practicemgr1', 'lin', 'xing', 'demo')
		cls.user1 = create_user('practicemgr2', 'lin', 'xing', 'demo')
		cls.from_user = create_user(get_random_username(), "tian", "thj", "demo", "555 Bryant St.",
								"Palo Alto", "CA", "")

		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice.save()
		practice1 = PracticeLocation(practice_name='test1',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice1.save()
		
		OrganizationRelationship.objects.create(organization=practice,\
				parent=practice1,create_time=int(time.time()),billing_flag=True)
		cls.practice = practice
		staff = OfficeStaff()
		staff.user = cls.user
		staff.office_lat = 0.0
		staff.office_longit = 0.0
		staff.current_practice = practice
		staff.save()
		staff.practices.add(practice)
		
		assoc = Pending_Association()
		assoc.from_user = cls.from_user
		assoc.to_user = cls.user1
		assoc.practice_location = practice
		assoc.created_time = datetime.datetime(2013, 5, 14, 12, 30)
		assoc.resent_time = datetime.datetime(2013, 5, 14, 13, 30)
		assoc.save()
		cls.assoc = assoc
		
		provider = Provider(user=cls.from_user, office_lat=0.0, office_longit=0.0, current_practice = practice)
		provider.save()
		cls.provider = provider
		
		mgr = Office_Manager(user=staff, practice=practice, manager_role=2)
		mgr.save()
	@classmethod
	def tearDownClass(cls):
		clean_db_datas()

	def setUp(self):
		self.client.post('/login/', {'username': self.user.username, 'password': 'demo'})

	def tearDown(self):
		self.client.logout()
		
	def testRejectAssociation(self):
		response = self.client.post(reverse('MHLogin.MHLOrganization.views_member.rejectAssociation'),\
					data={'org_id': self.practice.id})
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 1)
		
		re_pen_assoc_len = len(Pending_Association.objects.filter(pk=self.assoc.id))
		response = self.client.get(reverse('MHLogin.MHLOrganization.views_member.rejectAssociation'),\
					data={'org_id': self.practice.id,'assoc_id':self.assoc.id})
		self.assertEqual(response.status_code, 200)
		pen_assoc_len = len(Pending_Association.objects.filter(pk=self.assoc.id))
		self.assertEqual(re_pen_assoc_len-pen_assoc_len, 1, 'Delete association')
		with self.assertRaises(Pending_Association.DoesNotExist): \
				Pending_Association.objects.get(pk=self.assoc.id)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 2)

class RemoveProviderTest(TestCase):
	@classmethod
	def setUpClass(cls):
		clean_db_datas()
		cls.call_group = CallGroup.objects.create(description='test', team='team')
		cls.user = create_user('practicemgr1', 'lin', 'xing', 'demo')
		cls.user1 = create_user('practicemgr2', 'yang', 'peng', 'demo')
		cls.user2 = create_user('practicemgr234', 'yang1', 'peng1', 'demo')

		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',
								call_group = cls.call_group,)
		practice.save()
		practice1 = PracticeLocation(practice_name='test1',
								practice_longit='0.1',
								practice_lat='0.0',
								call_group = cls.call_group,)
		practice1.save()
		
		OrganizationRelationship.objects.create(organization=practice,\
				parent=practice1,create_time=int(time.time()),billing_flag=True)
		cls.practice = practice
		cls.practice1 = practice1
		
		provider = Provider(user=cls.user1, office_lat=0.0, office_longit=0.0, current_practice = practice)
		provider.save()
		provider.practices.add(practice)
		provider.practices.add(practice1)
		cls.provider = provider
		
		cls.provider2 = Provider(username="docholiday", first_name="doc", 
								last_name="holiday", office_lat=0.0, office_longit=0.0)
		cls.provider2.set_password("holiday")
		cls.provider2.save()
		VMBox_Config(owner=cls.provider2).save()
		
		staff = OfficeStaff()
		staff.user = cls.user
		staff.office_lat = 0.0
		staff.office_longit = 0.0
		staff.current_practice = practice
		staff.save()
		staff.practices.add(practice)
		
		cls.event = EventEntry(creator=cls.user,
						oncallPerson=cls.user1,
						callGroup=cls.call_group,
						startDate=datetime.datetime(2012, 12, 1),
						endDate=datetime.datetime.now()+datetime.timedelta(days = 2),
						title='test event',
						oncallLevel='0',
						eventStatus=1,
						checkString='abc'
						)
		cls.event.save()
		mgr = Office_Manager(user=staff, practice=practice, manager_role=2)
		mgr.save()
		generate_keys_for_users(output=DevNull())
	@classmethod
	def tearDownClass(cls):
		clean_db_datas()

	def setUp(self):
		self.client.post('/login/', {'username': self.user.username, 'password': 'demo'})

	def tearDown(self):
		self.client.logout()
		
	@mock.patch('MHLogin.apps.smartphone.v1.views_account.thread.start_new_thread', autospec=True)
	def testRemoveProvider(self, start_thread):
		response = self.client.post(reverse('MHLogin.MHLOrganization.views_member.removeProvider'),\
					data={'org_id': self.practice.id,'prov_id':1})
		self.assertEqual(response.status_code, 404)
		
		sender = authenticate(username=self.user.username, password='demo')
		msg = Message(sender=sender, sender_site=None, subject="pandas")
		recipient = User.objects.get(id=self.provider2.id)		
		msg.urgent = False
		msg.message_type = 'NM'
		self.assertRaises(Exception, msg.save_body, '')
		msg.save()
		MessageRecipient(message=msg, user=recipient).save()
		response = self.client.post(reverse('MHLogin.MHLOrganization.views_member.removeProvider'),\
					data={'org_id': self.practice.id,'prov_id':self.provider.id})
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 2)
		
		response = self.client.get(reverse('MHLogin.MHLOrganization.views_member.removeProvider'),\
					data={'org_id': self.practice.id,'prov_id':self.provider.id})
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 2)
		
class RemoveStaffTest(TestCase):
	@classmethod
	def setUpClass(cls):
		clean_db_datas()
		cls.user = create_user('practicemgr1', 'lin', 'xing', 'demo')

		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice.save()
		practice1 = PracticeLocation(practice_name='test1',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice1.save()
		
		OrganizationRelationship.objects.create(organization=practice,\
				parent=practice1,create_time=int(time.time()),billing_flag=True)
		cls.practice = practice
		cls.practice1 = practice1
		staff = OfficeStaff()
		staff.user = cls.user
		staff.office_lat = 0.0
		staff.office_longit = 0.0
		staff.current_practice = practice
		staff.save()
		staff.practices.add(practice)
		cls.staff = staff
		
		mgr = Office_Manager(user=staff, practice=practice, manager_role=2)
		mgr.save()
	@classmethod
	def tearDownClass(cls):
		clean_db_datas()

	def setUp(self):
		self.client.post('/login/', {'username': self.user.username, 'password': 'demo'})

	def tearDown(self):
		self.client.logout()

	@mock.patch('MHLogin.apps.smartphone.v1.views_account.thread.start_new_thread', autospec=True)
	def testRemoveStaff(self, start_thread):
		response = self.client.post(reverse('MHLogin.MHLOrganization.views_member.removeStaff'),\
					data={'org_id': self.practice.id,'staff_id':1})
		self.assertEqual(response.status_code, 200)
		with self.assertRaises(Office_Manager.DoesNotExist):\
				Office_Manager.objects.get(user=self.staff, practice=self.practice)
		with self.assertRaises(OfficeStaff.DoesNotExist):\
				OfficeStaff.objects.get(practices=self.practice)
		staff = OfficeStaff.objects.get(user = self.user)
		self.assertEqual(staff.current_practice, None, 'current_practice=None')
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 2)
		
		response = self.client.get(reverse('MHLogin.MHLOrganization.views_member.removeStaff'),\
					data={'org_id': self.practice.id})
		self.assertEqual(response.status_code, 302)
		
class ChangeRoleTest(TestCase):
	@classmethod
	def setUpClass(cls):
		clean_db_datas()
		cls.user = create_user('practicemgr1', 'lin', 'xing', 'demo')
		cls.user1 = create_user('practicemgr11', 'aaa', 'bbbb', 'demo')

		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice.save()
		practice1 = PracticeLocation(practice_name='test1',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice1.save()
		
		OrganizationRelationship.objects.create(organization=practice,\
				parent=practice1,create_time=int(time.time()),billing_flag=True)
		cls.practice = practice
		cls.practice1 = practice1
		
		staff = OfficeStaff()
		staff.user = cls.user
		staff.office_lat = 0.0
		staff.office_longit = 0.0
		staff.current_practice = practice
		staff.save()
		staff.practices.add(practice)
		cls.staff = staff
		
		staff1 = OfficeStaff()
		staff1.user = cls.user1
		staff1.office_lat = 0.0
		staff1.office_longit = 0.0
		staff1.current_practice = practice1
		staff1.save()
		staff1.practices.add(practice1)
		cls.staff1 = staff1
		
		mgr = Office_Manager(user=staff, practice=practice, manager_role=2)
		mgr.save()
	@classmethod
	def tearDownClass(cls):
		clean_db_datas()

	def setUp(self):
		self.client.post('/login/', {'username': self.user.username, 'password': 'demo'})

	def tearDown(self):
		self.client.logout()
		
	def testChangeRole(self):
		response = self.client.post(reverse('MHLogin.MHLOrganization.views_member.changeRole'),\
					data={'org_id': self.practice.id,'pk':1,'newRole':1})
		self.assertEqual(response.status_code, 200)
		om = Office_Manager.objects.get(user=self.staff, practice=self.practice)
		self.assertEqual(om.manager_role, 1)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 2)

		response = self.client.post(reverse('MHLogin.MHLOrganization.views_member.changeRole'),\
					data={'org_id': self.practice.id,'pk':2,'newRole':4})
		self.assertEqual(response.status_code, 200)
		obm = Office_Manager.objects.get(user=self.staff1)
		self.assertEqual(obm.manager_role, 4)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 2)
		
		response = self.client.post(reverse('MHLogin.MHLOrganization.views_member.changeRole'),\
					data={'org_id': self.practice.id,'pk':1,'newRole':0})
		self.assertEqual(response.status_code, 200)
		with self.assertRaises(Office_Manager.DoesNotExist):\
				Office_Manager.objects.get(user=self.staff, practice=self.practice)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 2)
		
		
class ChangeSmartphonePermissionTest(TestCase):
	@classmethod
	def setUpClass(cls):
		clean_db_datas()
		cls.user = create_user('practicemgr1', 'lin', 'xing', 'demo')
		cls.user1 = create_user('practicemgr2', 'yang', 'peng', 'demo')

		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice.save()
		practice1 = PracticeLocation(practice_name='test1',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice1.save()
		
		OrganizationRelationship.objects.create(organization=practice,\
				parent=practice1,create_time=int(time.time()),billing_flag=True)
		cls.practice = practice
		cls.practice1 = practice1
		staff = OfficeStaff()
		staff.user = cls.user
		staff.office_lat = 0.0
		staff.office_longit = 0.0
		staff.current_practice = practice
		staff.save()
		staff.practices.add(practice)
		cls.staff = staff
		
		cls.content_type=ContentType.objects.get_for_model(cls.user1)
		try:
			perm = Permission.objects.get(codename='access_smartphone',\
					name='Can use smartphone app', \
					content_type=ContentType.objects.get_for_model(MHLUser))
			staff.user.user_permissions.remove(perm)
			staff.save()
		except:
			with cls.assertRaises(Permission.DoesNotExist):\
					Permission.objects.get(codename='access_smartphone',\
					name='Can use smartphone app', \
					content_type=ContentType.objects.get_for_model(MHLUser))
		mgr = Office_Manager(user=staff, practice=practice, manager_role=2)
		mgr.save()
	@classmethod
	def tearDownClass(cls):
		clean_db_datas()

	def setUp(self):
		self.client.post('/login/', {'username': self.user.username, 'password': 'demo'})

	def tearDown(self):
		self.client.logout()
		clean_db_datas()
		
	def testChangeSmartphonePermission(self):
		response = self.client.post(reverse('MHLogin.MHLOrganization.views_member.changeSmartphonePermission'),\
					data={'org_id': self.practice.id,'pk':self.staff.id,'newSmart':'True'})
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 2)
		response = self.client.post(reverse('MHLogin.MHLOrganization.views_member.changeSmartphonePermission'),\
					data={'org_id': self.practice.id,'pk':self.staff.id,'newSmart':'False'})
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 2)
		response = self.client.post(reverse('MHLogin.MHLOrganization.views_member.changeSmartphonePermission'),\
					data={'org_id': self.practice.id,'pk':self.staff.id,'newSmart':'false'})
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 2)
		response = self.client.post(reverse('MHLogin.MHLOrganization.views_member.changeSmartphonePermission'),\
					data={'org_id': self.practice.id})
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 2)
		response = self.client.post(reverse('MHLogin.MHLOrganization.views_member.changeSmartphonePermission'),\
					data={'org_id': self.practice.id,'pk':self.user.id,'newSmart':'True'})
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 2)
		
class CheckProviderScheduleTest(TestCase):
	@classmethod
	def setUpClass(cls):
		clean_db_datas()
		cls.user = create_user('practicemgr1', 'lin', 'xing', 'demo')

		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',
								)
		practice.save()
		practice1 = PracticeLocation(practice_name='test1',
								practice_longit='0.1',
								practice_lat='0.0',
								)
		practice1.save()
		
		OrganizationRelationship.objects.create(organization=practice,\
				parent=practice1,create_time=int(time.time()),billing_flag=True)
		cls.practice = practice
		cls.practice1 = practice1
		staff = OfficeStaff()
		staff.user = cls.user
		staff.office_lat = 0.0
		staff.office_longit = 0.0
		staff.current_practice = practice
		staff.save()
		staff.practices.add(practice)

		user1 = create_user('Provoder1', 'pro1', 'pro1', 'demo')
		provider = Provider(user=user1)
		provider.office_lat = 0.0
		provider.office_longit = 0.0
		provider.current_practice = practice1
		provider.save()
		provider.practices.add(practice1)
		cls.provider = provider

		mgr = Office_Manager(user=staff, practice=practice, manager_role=2)
		mgr.save()
	@classmethod
	def tearDownClass(cls):
		clean_db_datas()

	def setUp(self):
		self.client.post('/login/', {'username': self.user.username, 'password': 'demo'})

	def tearDown(self):
		self.client.logout()
		
	def testCheckProviderSchedule(self):
		response = self.client.get(reverse('MHLogin.MHLOrganization.views_member.checkProviderSchedule'),\
					data={'org_id': self.practice.id,'prov_id':self.provider.user.id})
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 1)
		self.call_group = CallGroup.objects.create(description='test', team='team')
		organization = PracticeLocation(practice_name='testcallgroup',
								practice_longit='0.1',
								practice_lat='0.0',
								call_group = self.call_group,)
		organization.save()
		self.organization = organization
		response = self.client.get(reverse('MHLogin.MHLOrganization.views_member.checkProviderSchedule'),\
					data={'org_id': self.practice.id})
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 2)
		response = self.client.get(reverse('MHLogin.MHLOrganization.views_member.checkProviderSchedule'),\
					data={'org_id': self.practice.id,'prov_id':self.provider.user.id})
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 1)
		response = self.client.post(reverse('MHLogin.MHLOrganization.views_member.checkProviderSchedule'),\
					data={'org_id': self.practice.id,'prov_id':self.provider.user.id})
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 1)

class GetInvitationsTest(TestCase):
	@classmethod
	def setUpClass(cls):
		clean_db_datas()
		cls.user = create_user('practicemgr1', 'lin', 'xing', 'demo')

		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice.save()
		practice1 = PracticeLocation(practice_name='test1',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice1.save()
		
		OrganizationRelationship.objects.create(organization=practice,\
				parent=practice1,create_time=int(time.time()),billing_flag=True)
		cls.practice = practice
		cls.practice1 = practice1
		staff = OfficeStaff()
		staff.user = cls.user
		staff.office_lat = 0.0
		staff.office_longit = 0.0
		staff.current_practice = practice
		staff.save()
		staff.practices.add(practice)
		
		mgr = Office_Manager(user=staff, practice=practice, manager_role=2)
		mgr.save()
	@classmethod
	def tearDownClass(cls):
		clean_db_datas()

	def setUp(self):
		self.client.post('/login/', {'username': self.user.username, 'password': 'demo'})

	def tearDown(self):
		self.client.logout()
		
	def testGetInvitations(self):
		response = self.client.get(reverse('MHLogin.MHLOrganization.views_member.getInvitations'),\
					data={'org_id': self.practice.id})
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 4)
		
class ResendInvitationTest(TestCase):
	@classmethod
	def setUpClass(cls):
		clean_db_datas()
		cls.user = create_user('practicemgr1', 'lin', 'xing', 'demo')
		cls.user1 = create_user('practicemgr2', 'lin', 'xing', 'demo')

		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice.save()
		practice1 = PracticeLocation(practice_name='test1',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice1.save()
		
		OrganizationRelationship.objects.create(organization=practice,\
				parent=practice1,create_time=int(time.time()),billing_flag=True)
		cls.practice = practice
		cls.practice1 = practice1
		staff = OfficeStaff()
		staff.user = cls.user
		staff.office_lat = 0.0
		staff.office_longit = 0.0
		staff.current_practice = practice
		staff.save()
		staff.practices.add(practice)
		
		usertype = 1
		code = '12345'
		email = 'test2@suzhoukada.com'
		invite = Invitation(code=code, sender=cls.user1, recipient=email, 
			userType=usertype, assignPractice=practice)
		invite.save()
		cls.invite = invite
		
		mgr = Office_Manager(user=staff, practice=practice, manager_role=2)
		mgr.save()
	@classmethod
	def tearDownClass(cls):
		clean_db_datas()

	def setUp(self):
		self.client.post('/login/', {'username': self.user.username, 'password': 'demo'})

	def tearDown(self):
		self.client.logout()
		
	def testResendInvitation(self):
		response = self.client.get(reverse('MHLogin.MHLOrganization.views_member.resendInvitation'),\
					data={'org_id': self.practice.id})
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 2)
		response = self.client.post(reverse('MHLogin.MHLOrganization.views_member.resendInvitation'),\
					data={'org_id': self.practice.id,'id':self.invite.id})
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 1)

class CancelInvitationTest(TestCase):
	@classmethod
	def setUpClass(cls):
		clean_db_datas()
		cls.user = create_user('practicemgr1', 'lin', 'xing', 'demo')
		cls.user1 = create_user('practicemgr123', 'lin', 'xing', 'demo')

		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice.save()
		practice1 = PracticeLocation(practice_name='test1',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice1.save()
		
		OrganizationRelationship.objects.create(organization=practice,\
				parent=practice1,create_time=int(time.time()),billing_flag=True)
		cls.practice = practice
		cls.practice1 = practice1
		staff = OfficeStaff()
		staff.user = cls.user
		staff.office_lat = 0.0
		staff.office_longit = 0.0
		staff.current_practice = practice
		staff.save()
		staff.practices.add(practice)
		
		usertype = 1
		cls.usertype = usertype
		code = '12345'
		email = 'test2@suzhoukada.com'
		cls.invite = Invitation(code=code, sender=cls.user1, recipient=email, 
			userType=usertype, assignPractice=cls.practice)
		cls.invite.save()
		
		mgr = Office_Manager(user=staff, practice=practice, manager_role=2)
		mgr.save()
	@classmethod
	def tearDownClass(cls):
		clean_db_datas()

	def setUp(self):
		self.client.post('/login/', {'username': self.user.username, 'password': 'demo'})

	def tearDown(self):
		self.client.logout()
		
	def testCancelInvitation(self):
		response = self.client.get(reverse('MHLogin.MHLOrganization.views_member.cancelInvitation'),\
					data={'org_id': self.practice.id})
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 2)
		
		response = self.client.post(reverse('MHLogin.MHLOrganization.views_member.cancelInvitation'),\
					data={'org_id': self.practice.id,'email':'testp@suzhoukada.com',\
						'type':self.usertype})
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 2)
		
		response = self.client.post(reverse('MHLogin.MHLOrganization.views_member.cancelInvitation'),\
					data={'org_id': self.practice.id,'email':self.invite.recipient,\
						'type':self.usertype})
		self.assertEqual(response.status_code, 200)
		with self.assertRaises(Invitation.DoesNotExist):\
				Invitation.objects.get(pk=self.invite.id)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 1)

class CancelExistInvitationTest(TestCase):
	@classmethod
	def setUpClass(cls):
		clean_db_datas()
		cls.user = create_user('practicemgr1', 'lin', 'xing', 'demo')
		cls.user1 = create_user('practicemgr11', 'lin', 'xing', 'demo')

		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice.save()
		practice1 = PracticeLocation(practice_name='test1',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice1.save()
		
		OrganizationRelationship.objects.create(organization=practice,\
				parent=practice1,create_time=int(time.time()),billing_flag=True)
		cls.practice = practice
		cls.practice1 = practice1
		staff = OfficeStaff()
		staff.user = cls.user
		staff.office_lat = 0.0
		staff.office_longit = 0.0
		staff.current_practice = practice
		staff.save()
		staff.practices.add(practice)
		
		usertype = 1
		cls.usertype = usertype
		code = '12345'
		email = 'test2@suzhoukada.com'
		cls.invite = Invitation(code=code, sender=cls.user1, recipient=email, 
			userType=usertype, assignPractice=cls.practice)
		cls.invite.save()
		
		mgr = Office_Manager(user=staff, practice=practice, manager_role=2)
		mgr.save()
	@classmethod
	def tearDownClass(cls):
		clean_db_datas()

	def setUp(self):
		self.client.post('/login/', {'username': self.user.username, 'password': 'demo'})

	def tearDown(self):
		self.client.logout()
		
	def testCancelExistInvitation(self):
		response = self.client.get(reverse('MHLogin.MHLOrganization.views_member.cancelExistInvitation'),\
					data={'org_id': self.practice.id})
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 2)
		response = self.client.post(reverse('MHLogin.MHLOrganization.views_member.cancelExistInvitation'),\
					data={'org_id': self.practice.id,'email':'test@suzhoukada.com','type':self.usertype})
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 2)
		
		response = self.client.post(reverse('MHLogin.MHLOrganization.views_member.cancelExistInvitation'),\
					data={'org_id': self.practice.id,'email':self.invite.recipient,'type':self.usertype})
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		with self.assertRaises(Invitation.DoesNotExist):\
				Invitation.objects.get(pk=self.invite.id)
		self.assertEqual(len(msg), 1)
		
class SendNewProviderEmailTest(TestCase):
	@classmethod
	def setUpClass(cls):
		clean_db_datas()
		cls.user = create_user('practicemgr1', 'lin', 'xing', 'demo')
		org_setting = OrganizationSetting(can_have_manager=True)
		org_setting.save()
		org_type = OrganizationType(name="Test Org Type", organization_setting=org_setting, is_public=True)
		org_type.save()
		cls.org_type = org_type
		cls.org_setting = org_setting
		
		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',
								organization_setting =org_setting,
								organization_type = org_type)
		practice.save()
		practice1 = PracticeLocation(practice_name='test1',
								practice_longit='0.1',
								practice_lat='0.0',
								organization_setting =org_setting,
								organization_type = org_type)
		practice1.save()
		OrganizationRelationship.objects.create(organization=practice,\
				parent=practice1,create_time=int(time.time()),billing_flag=True)
		cls.practice = practice
		cls.practice1 = practice1
		staff = OfficeStaff()
		staff.user = cls.user
		staff.office_lat = 0.0
		staff.office_longit = 0.0
		staff.current_practice = practice
		staff.save()
		staff.practices.add(practice)
		
		mgr = Office_Manager(user=staff, practice=practice, manager_role=2)
		mgr.save()
	@classmethod
	def tearDownClass(cls):
		clean_db_datas()

	def setUp(self):
		self.client.post('/login/', {'username': self.user.username, 'password': 'demo'})

	def tearDown(self):
		self.client.logout()
		
	def testSendNewProviderEmail(self):
		response = self.client.get(reverse('MHLogin.MHLOrganization.views_member.sendNewProviderEmail'),\
					data={'org_id': self.practice.id})
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 1)
		response = self.client.post(reverse('MHLogin.MHLOrganization.views_member.sendNewProviderEmail'),\
					data={'org_id': self.practice.id,'recipient':'testY@suzhoukada.com','userType':1})
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 2)

		response = self.client.post(reverse('MHLogin.MHLOrganization.views_member.sendNewProviderEmail'),\
					data={'org_id': self.practice.id,'recipient':'testY@suzhoukada.com'})
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 1)

class CheckPenddingExistTest(TestCase):
	@classmethod
	def setUpClass(cls):
		clean_db_datas()
		cls.user = create_user('practicemgr1', 'lin', 'xing', 'demo')

		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice.save()
		practice1 = PracticeLocation(practice_name='test1',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice1.save()
		
		OrganizationRelationship.objects.create(organization=practice,\
				parent=practice1,create_time=int(time.time()),billing_flag=True)
		cls.practice = practice
		cls.practice1 = practice1
		staff = OfficeStaff()
		staff.user = cls.user
		staff.office_lat = 0.0
		staff.office_longit = 0.0
		staff.current_practice = practice
		staff.save()
		staff.practices.add(practice)
		
		mgr = Office_Manager(user=staff, practice=practice, manager_role=2)
		mgr.save()
	@classmethod
	def tearDownClass(cls):
		clean_db_datas()

	def setUp(self):
		self.client.post('/login/', {'username': self.user.username, 'password': 'demo'})

	def tearDown(self):
		self.client.logout()
		
	def testCheckPenddingExist(self):
		response = self.client.post(reverse('MHLogin.MHLOrganization.views_member.checkPenddingExist'),\
					data={'org_id': self.practice.id,'id':self.user.id})
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 2)

class StaffSearchTest(TestCase):
	@classmethod
	def setUpClass(cls):
		clean_db_datas()
		cls.user = create_user('practicemgr1', 'lin', 'xing', 'demo')

		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice.save()
		practice1 = PracticeLocation(practice_name='test1',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice1.save()
		
		OrganizationRelationship.objects.create(organization=practice,\
				parent=practice1,create_time=int(time.time()),billing_flag=True)
		cls.practice = practice
		cls.practice1 = practice1
		staff = OfficeStaff()
		staff.user = cls.user
		staff.office_lat = 0.0
		staff.office_longit = 0.0
		staff.current_practice = practice
		staff.save()
		staff.practices.add(practice)
		
		mgr = Office_Manager(user=staff, practice=practice, manager_role=2)
		mgr.save()
	@classmethod
	def tearDownClass(cls):
		clean_db_datas()

	def setUp(self):
		self.client.post('/login/', {'username': self.user.username, 'password': 'demo'})

	def tearDown(self):
		self.client.logout()
	def testStaffSearch(self):
		response = self.client.get(reverse('MHLogin.MHLOrganization.views_member.staffSearch'),\
					data={'org_id': self.practice.id,'search_name':self.practice.practice_name})
		self.assertEqual(response.status_code, 200)
		response = self.client.post(reverse('MHLogin.MHLOrganization.views_member.staffSearch'),\
					data={'org_id': self.practice.id,'search_name':self.practice.practice_name})
		self.assertEqual(response.status_code, 200)
		response = self.client.post(reverse('MHLogin.MHLOrganization.views_member.staffSearch'),\
					data={'org_id': self.practice.id})
		self.assertEqual(response.status_code, 200)

class ResendAssociationTest(TestCase):
	@classmethod
	def setUpClass(cls):
		clean_db_datas()
		cls.user = create_user('practicemgr1', 'lin', 'xing', 'demo')
		cls.user1 = create_user('practicemgr2', 'y', 'p', 'demo')
		cls.to_user = create_user(get_random_username(), "tian", "thj", "demo", "555 Bryant St.",
								"Palo Alto", "CA", "")
		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice.save()
		practice1 = PracticeLocation(practice_name='test1',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice1.save()
		
		OrganizationRelationship.objects.create(organization=practice,\
				parent=practice1,create_time=int(time.time()),billing_flag=True)
		cls.practice = practice
		cls.practice1 = practice1
		
		provider = Provider(user=cls.to_user, office_lat=0.0, office_longit=0.0, current_practice = practice1)
		provider.save()
		provider.practices.add(practice1)
		cls.provider = provider
		
		assoc = Pending_Association()
		assoc.from_user = cls.user1
		assoc.to_user = cls.to_user
		assoc.practice_location = practice
		assoc.created_time = datetime.datetime(2013, 5, 14, 12, 30)
		assoc.resent_time = datetime.datetime(2013, 5, 14, 13, 30)
		assoc.save()
		cls.assoc = assoc

		staff = OfficeStaff()
		staff.user = cls.user
		staff.office_lat = 0.0
		staff.office_longit = 0.0
		staff.current_practice = practice
		staff.save()
		staff.practices.add(practice)
		
		mgr = Office_Manager(user=staff, practice=practice, manager_role=2)
		mgr.save()
	@classmethod
	def tearDownClass(cls):
		clean_db_datas()

	def setUp(self):
		self.client.post('/login/', {'username': self.user.username, 'password': 'demo'})

	def tearDown(self):
		self.client.logout()
	def testResendAssociation(self):
		response = self.client.get(reverse('MHLogin.MHLOrganization.views_member.resendAssociation'),\
					data={'org_id': self.practice.id})
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 1)
		
		response = self.client.post(reverse('MHLogin.MHLOrganization.views_member.resendAssociation'),\
					data={'org_id': self.practice.id,'assoc_id':self.assoc.id})
		self.assertEqual(response.status_code, 200)

		msg = json.loads(response.content)
		self.assertEqual(len(msg), 2)

class GetInvitePending(TestCase):
	@classmethod
	def setUpClass(cls):
		clean_db_datas()
		cls.user = create_user('practicemgr1', 'lin', 'xing', 'demo')
		cls.user1 = create_user('practicemgr2', 'y', 'p', 'demo')
		cls.to_user = create_user(get_random_username(), "tian", "thj", "demo", "555 Bryant St.",
								"Palo Alto", "CA", "", uklass=Provider)

		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice.save()
		practice1 = PracticeLocation(practice_name='test1',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice1.save()
		
		OrganizationRelationship.objects.create(organization=practice,\
				parent=practice1,create_time=int(time.time()),billing_flag=True)
		cls.practice = practice
		cls.practice1 = practice1
		
		assoc = Pending_Association()
		assoc.from_user = cls.user1
		assoc.to_user = cls.to_user
		assoc.practice_location = practice
		assoc.created_time = datetime.datetime(2013, 5, 14, 12, 30)
		assoc.resent_time = datetime.datetime(2013, 5, 14, 13, 30)
		assoc.save()
		cls.assoc = assoc

		staff = OfficeStaff()
		staff.user = cls.user
		staff.office_lat = 0.0
		staff.office_longit = 0.0
		staff.current_practice = practice
		staff.save()
		staff.practices.add(practice)
		
		mgr = Office_Manager(user=staff, practice=practice, manager_role=2)
		mgr.save()
	@classmethod
	def tearDownClass(cls):
		clean_db_datas()

	def setUp(self):
		self.client.post('/login/', {'username': self.user.username, 'password': 'demo'})

	def tearDown(self):
		self.client.logout()
	
	def test_get_invite_pending(self):
		response = self.client.post(reverse('MHLogin.MHLOrganization.views_member.get_invite_pending'),\
					data={'org_id': self.practice.id,'index':1})
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'MHLOrganization/Invite/invite_pending_list_view.html')
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 4)

class ValideInvitationTest(TestCase):
	@classmethod
	def setUpClass(cls):
		clean_db_datas()
		cls.user = create_user('practicemgr1', 'lin', 'xing', 'demo')
		cls.user1 = create_user('practicemgr2', 'y', 'p', 'demo')
		cls.to_user = create_user(get_random_username(), "tian", "thj", "demo", "555 Bryant St.",
								"Palo Alto", "CA", "", uklass=Provider)

		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice.save()
		practice1 = PracticeLocation(practice_name='test1',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice1.save()
		
		OrganizationRelationship.objects.create(organization=practice,\
				parent=practice1,create_time=int(time.time()),billing_flag=True)
		cls.practice = practice
		cls.practice1 = practice1
		
		assoc = Pending_Association()
		assoc.from_user = cls.user1
		assoc.to_user = cls.to_user
		assoc.practice_location = practice
		assoc.created_time = datetime.datetime(2013, 5, 14, 12, 30)
		assoc.resent_time = datetime.datetime(2013, 5, 14, 13, 30)
		assoc.save()
		cls.assoc = assoc

		staff = OfficeStaff()
		staff.user = cls.user
		staff.office_lat = 0.0
		staff.office_longit = 0.0
		staff.current_practice = practice
		staff.save()
		staff.practices.add(practice)
		
		mgr = Office_Manager(user=staff, practice=practice, manager_role=2)
		mgr.save()
	@classmethod
	def tearDownClass(cls):
		clean_db_datas()

	def setUp(self):
		self.client.post('/login/', {'username': self.user.username, 'password': 'demo'})

	def tearDown(self):
		self.client.logout()
	
	def testValideInvitation(self):
		response = self.client.post(reverse('MHLogin.MHLOrganization.views_member.valideInvitation'),\
					data={'org_id': self.practice.id})
		self.assertEqual(response.status_code, 200)
