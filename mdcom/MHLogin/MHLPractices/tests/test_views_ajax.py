
import datetime
import json
import mock

from django.core.urlresolvers import reverse
from django.test.testcases import TestCase
from django.utils.translation import ugettext as _

from MHLogin.Invites.models import Invitation
from MHLogin.KMS.utils import generate_keys_for_users
from MHLogin.MHLCallGroups.Scheduler.models import EventEntry
from MHLogin.MHLCallGroups.models import CallGroup, CallGroupMember, \
	CallGroupMemberPending
from MHLogin.MHLPractices.models import PracticeLocation, Pending_Association, \
	Log_Association
from MHLogin.MHLUsers.models import OfficeStaff, Office_Manager, Provider
from MHLogin.utils.tests import create_user
from MHLogin.utils.tests.tests import clean_db_datas


class DevNull():
	write = lambda self, s: None
	flush = lambda self: None


class RemoveProviderCallGroupTest(TestCase):
	@classmethod
	def setUpClass(cls):
		clean_db_datas()
		cls.user = create_user('practicemgr1', 'lin', 'xing', 'demo', '', '', '', '',)

		call_group = CallGroup(description='test', team='team')
		call_group.save()
		cls.group = call_group

		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice.save()
		practice.call_groups.add(call_group)
		cls.practice = practice

	@classmethod
	def tearDownClass(cls):
		clean_db_datas()

	def setUp(self):
		self.client.post('/login/', {'username': self.user.username, 'password': 'demo'})

	def tearDown(self):
		self.client.logout()

	def test_removeProviderCallGroup(self):
		#user is a manager
		staff = OfficeStaff(user=self.user)
		staff.current_practice = self.practice
		staff.save()
		staff.practices.add(self.practice)
		manager = Office_Manager(user=staff, practice=self.practice, manager_role=2)
		manager.save()

		#invalid provider
		provider_invalid = {'prov_id': 'abc'}
		response = self.client.post(reverse('MHLogin.MHLPractices.views_ajax.removeProvider'), 
								data=provider_invalid)
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(msg['err'], _('The data is error. Please refresh page again.'))

		#init a provider in practices
		provider1 = Provider(username='provider', first_name='tes', last_name="meister", email='aa@ada.com',
					office_lat=0.0, office_longit=0.0)
		provider1.save()
		provider1.practices.add(self.practice)

		provider_data = {'prov_id': provider1.id}

		response = self.client.post(reverse('MHLogin.MHLPractices.views_ajax.removeProvider'), 
								data=provider_data)
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(msg, 'ok')
		self.assertNotEqual(provider1.practices, self.practice)

		#init a new provider in current practice and assign event
		user2 = create_user('practicemgr2', 'lin2', 'xing2', 'demo', '', '', '', '',)
		provider2 = Provider(username='provider2', first_name='tes', last_name="meister", email='a2a@ada.com',
					user=user2, office_lat=0.0, office_longit=0.0)
		provider2.save()
		provider2.practices.add(self.practice)
		startDate = datetime.datetime.now() + datetime.timedelta(-10)
		endDate = datetime.datetime.now() + datetime.timedelta(10)
		event = EventEntry(creator=user2,
						oncallPerson=user2,
						callGroup=self.group,
						startDate=startDate,
						endDate=endDate,
						title='test event',
						oncallLevel='0',
						eventStatus=1,
						checkString='abc'
						)
		event.save()
		provider_data = {'prov_id': provider2.id}
		#init key because send mail
		generate_keys_for_users(output=DevNull())
		response = self.client.post(reverse('MHLogin.MHLPractices.views_ajax.removeProvider'), 
					data=provider_data)
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(msg, 'ok')
		self.assertNotEqual(provider2.practices, self.practice)

		#init a provider in practices and current practice 
		provider3 = Provider(username='provider3', first_name='tes', last_name="meister", 
			email='aa3@ada.com', office_lat=0.0, office_longit=0.0)
		provider3.current_practice = self.practice
		provider3.save()
		provider3.practices.add(self.practice)
		provider_data = {'prov_id': provider3.id}

		response = self.client.post(reverse('MHLogin.MHLPractices.views_ajax.removeProvider'), 
			data=provider_data)
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(msg, 'ok')
		self.assertNotEqual(provider1.practices, self.practice)
		self.assertIsNone(provider1.current_practice)


#add by xlin 121218 to test addAssociation method
class AddAssociationTest(TestCase):
	@classmethod
	def setUpClass(cls):
		clean_db_datas()
		cls.user = create_user('practicemgr1', 'lin', 'xing', 'demo', '', '', '', '',)

		call_group = CallGroup(description='test', team='team')
		call_group.save()
		cls.group = call_group

		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice.save()
		practice.call_groups.add(call_group)
		cls.practice = practice

	@classmethod
	def tearDownClass(cls):
		clean_db_datas()

	def setUp(self):
		self.client.post('/login/', {'username': self.user.username, 'password': 'demo'})

	def tearDown(self):
		self.client.logout()

	def test_addAssociation(self):
		#user is a manager
		staff = OfficeStaff(user=self.user)
		staff.current_practice = self.practice
		staff.save()
		staff.practices.add(self.practice)
		manager = Office_Manager(user=staff, practice=self.practice, manager_role=2)
		manager.save()

		#provider id
		user = create_user('p', 'lin2', 'xing2', 'demo', '', '', '', '',)
		provider = Provider(username='provider', first_name='first', last_name="last", email='p@a.com',
					user=user, office_lat=0.0, office_longit=0.0)
		provider.save()

		data = {'prov_id': provider.user.id, 'userType': 1}
		response = self.client.post(reverse('MHLogin.MHLPractices.views_ajax.addAssociation'), data)
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(msg[0], 'ok')
		self.assertEqual(Pending_Association.objects.count(), 1)
		self.assertEqual(Pending_Association.objects.get(to_user=provider.user).from_user, self.user)
		self.assertEqual(Log_Association.objects.count(), 1)


#add by xlin 121219 to test method resendAssociation
class ResendAssociationTest(TestCase):
	@classmethod
	def setUpClass(cls):
		clean_db_datas()
		cls.user = create_user('practicemgr1', 'lin', 'xing', 'demo', '', '', '', '',)

		call_group = CallGroup(description='test', team='team')
		call_group.save()
		cls.group = call_group

		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice.save()
		practice.call_groups.add(call_group)
		cls.practice = practice

	@classmethod
	def tearDownClass(cls):
		clean_db_datas()

	def setUp(self):
		self.client.post('/login/', {'username': self.user.username, 'password': 'demo'})

	def tearDown(self):
		self.client.logout()

	def test_resendAssociation(self):
		#user is a manager
		staff = OfficeStaff(user=self.user)
		staff.current_practice = self.practice
		staff.save()
		staff.practices.add(self.practice)
		manager = Office_Manager(user=staff, practice=self.practice, manager_role=2)
		manager.save()

		#invalid assoc id
		assocID = {'assoc_id': 'a'}
		response = self.client.post(reverse('MHLogin.MHLPractices.views_ajax.resendAssociation'), data=assocID)
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(msg['err'], _('The data is error. Please refresh the page again.'))

		#valid assoc id
		to_user = create_user('p2', 'lin2', 'xing2', 'demo', '', '', '', '',)
		provider = Provider(username='provider', first_name='first', last_name="last", email='p@a.com',
					user=to_user, office_lat=0.0, office_longit=0.0)
		provider.save()
		pend = Pending_Association(from_user=self.user, to_user=to_user, 
			practice_location=self.practice, created_time=datetime.datetime.now())
		pend.save()
		assocID = {'assoc_id': pend.id}
		response = self.client.post(reverse('MHLogin.MHLPractices.views_ajax.resendAssociation'), data=assocID)
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(msg, 'OK')
		self.assertEqual(Log_Association.objects.get(association_id=pend.id).action, 'RES')


#add by xlin 121219 to test removeAssociation method
class RemoveAssociationTest(TestCase):
	@classmethod
	def setUpClass(cls):
		clean_db_datas()
		cls.user = create_user('practicemgr1', 'lin', 'xing', 'demo', '', '', '', '',)

		call_group = CallGroup(description='test', team='team')
		call_group.save()
		cls.group = call_group

		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice.save()
		practice.call_groups.add(call_group)
		cls.practice = practice

	@classmethod
	def tearDownClass(cls):
		clean_db_datas()

	def setUp(self):
		self.client.post('/login/', {'username': self.user.username, 'password': 'demo'})

	def tearDown(self):
		self.client.logout()

	def test_removeAssociation(self):
		#user is a manager
		staff = OfficeStaff(user=self.user)
		staff.current_practice = self.practice
		staff.save()
		staff.practices.add(self.practice)
		manager = Office_Manager(user=staff, practice=self.practice, manager_role=2)
		manager.save()

		#invalid assoc id
		assocID = {'assoc_id': 'a'}
		response = self.client.post(reverse('MHLogin.MHLPractices.views_ajax.removeAssociation'), data=assocID)
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(msg['err'], _('The data is error. Please refresh the page again.'))

		#valid assoc id
		to_user = create_user('p2', 'lin2', 'xing2', 'demo', '', '', '', '',)
		provider = Provider(username='provider', first_name='first', last_name="last", email='p@a.com',
					user=to_user, office_lat=0.0, office_longit=0.0)
		provider.save()
		pend = Pending_Association(from_user=self.user, to_user=to_user, 
			practice_location=self.practice, created_time=datetime.datetime.now())
		pend.save()
		assocID = {'assoc_id': pend.id}
		response = self.client.post(reverse('MHLogin.MHLPractices.views_ajax.removeAssociation'), data=assocID)
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(msg, 'OK')
		self.assertEqual(Log_Association.objects.get(association_id=pend.id).action, 'CAN')
		self.assertEqual(Pending_Association.objects.count(), 0)


#add by xlin 121219 to test rejectAssociation
class RejectAssociationTest(TestCase):
	@classmethod
	def setUpClass(cls):
		clean_db_datas()
		cls.user = create_user('practicemgr1', 'lin', 'xing', 'demo', '', '', '', '',)

		call_group = CallGroup(description='test', team='team')
		call_group.save()
		cls.group = call_group

		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice.save()
		practice.call_groups.add(call_group)
		cls.practice = practice

	@classmethod
	def tearDownClass(cls):
		clean_db_datas()

	def setUp(self):
		self.client.post('/login/', {'username': self.user.username, 'password': 'demo'})

	def tearDown(self):
		self.client.logout()

	def test_rejectAssociation(self):
		#user is a manager
		staff = OfficeStaff(user=self.user)
		staff.current_practice = self.practice
		staff.save()
		staff.practices.add(self.practice)
		manager = Office_Manager(user=staff, practice=self.practice, manager_role=2)
		manager.save()

		#invalid assoc id
		assocID = {'assoc_id': 'a'}
		response = self.client.post(reverse('MHLogin.MHLPractices.views_ajax.rejectAssociation'), data=assocID)
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(msg['err'], _('The data is error. Please refresh the page again.'))

		#valid assoc id
		to_user = create_user('p2', 'lin2', 'xing2', 'demo', '', '', '', '',)
		provider = Provider(username='provider', first_name='first', last_name="last", email='p@a.com',
					user=self.user, office_lat=0.0, office_longit=0.0)
		provider.save()
		pend = Pending_Association(from_user=self.user, to_user=to_user, 
			practice_location=self.practice, created_time=datetime.datetime.now())
		pend.save()
		assocID = {'assoc_id': pend.id}
		response = self.client.post(reverse('MHLogin.MHLPractices.views_ajax.rejectAssociation'), data=assocID)
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(msg, 'OK')
		self.assertEqual(Log_Association.objects.get(association_id=pend.id).action, 'REJ')
		self.assertEqual(Pending_Association.objects.count(), 0)


#add by xlin 121219 to test addProviderToPractice method
class AddProviderToPracticeTest(TestCase):
	@classmethod
	def setUpClass(cls):
		clean_db_datas()
		cls.user = create_user('practicemgr1', 'lin', 'xing', 'demo', '', '', '', '',)

		call_group = CallGroup(description='test', team='team')
		call_group.save()
		cls.call_group = call_group

		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',
								call_group=call_group)
		practice.save()
		practice.call_groups.add(call_group)
		cls.practice = practice

	@classmethod
	def tearDownClass(cls):
		clean_db_datas()

	def setUp(self):
		self.client.post('/login/', {'username': self.user.username, 'password': 'demo'})

	def tearDown(self):
		self.client.logout()

	@mock.patch('MHLogin.apps.smartphone.v1.views_account.thread.start_new_thread', autospec=True)
	def test_addProviderToPractice(self, start_thread):
		#user is a manager
		staff = OfficeStaff(user=self.user)
		staff.current_practice = self.practice
		staff.save()
		staff.practices.add(self.practice)
		manager = Office_Manager(user=staff, practice=self.practice, manager_role=2)
		manager.save()

		#invalid assoc id
		assocID = {'assoc_id': 'a'}
		response = self.client.post(reverse('MHLogin.MHLPractices.views_ajax.addProviderToPractice'), data=assocID)
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(msg['err'], _('A server error has occurred.'))

		#valid assoc id
		to_user = create_user('p2', 'lin2', 'xing2', 'demo', '', '', '', '',)
		provider = Provider(username='provider', first_name='first', last_name="last", email='p@a.com',
					user=self.user, office_lat=0.0, office_longit=0.0)
		provider.save()
		pend = Pending_Association(from_user=self.user, to_user=to_user, 
			practice_location=self.practice, created_time=datetime.datetime.now())
		pend.save()
		assocID = {'assoc_id': pend.id}
		response = self.client.post(reverse('MHLogin.MHLPractices.views_ajax.addProviderToPractice'), data=assocID)
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(msg, 'ok')
		self.assertEqual(Log_Association.objects.get(association_id=pend.id).action, 'ACC')
		self.assertEqual(Pending_Association.objects.count(), 0)
		self.assertEqual(self.practice in Provider.objects.get(pk=provider.pk).practices.all(), True)
		mems = CallGroupMember.objects.filter(call_group=self.call_group)
		self.assertEqual(len(mems), 1)


#add by xlin 121219 to test removeProvider
class RemoveProviderTest(TestCase):
	@classmethod
	def setUpClass(cls):
		clean_db_datas()
		cls.user = create_user('practicemgr1', 'lin', 'xing', 'demo', '', '', '', '',)

		call_group = CallGroup(description='test', team='team')
		call_group.save()
		cls.call_group = call_group

		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice.save()
		practice.call_groups.add(call_group)
		cls.practice = practice

	@classmethod
	def tearDownClass(cls):
		clean_db_datas()

	def setUp(self):
		self.client.post('/login/', {'username': self.user.username, 'password': 'demo'})

	def tearDown(self):
		self.client.logout()

	def test_removeProvider(self):
		#user is a manager
		staff = OfficeStaff(user=self.user)
		staff.current_practice = self.practice
		staff.save()
		staff.practices.add(self.practice)
		manager = Office_Manager(user=staff, practice=self.practice, manager_role=2)
		manager.save()

		#practice has no call group
		response = self.client.post(reverse('MHLogin.MHLPractices.views_ajax.removeProvider'))
		self.assertEqual(response.status_code, 200)

		#practice has call group
		self.practice.call_group = self.call_group
		self.practice.save()
		response = self.client.post(reverse('MHLogin.MHLPractices.views_ajax.removeProvider'))
		self.assertEqual(response.status_code, 200)


#add by xlin 121220 to test cancelInvitation method
class CancelInvitationTest(TestCase):
	@classmethod
	def setUpClass(cls):
		clean_db_datas()
		cls.user = create_user('practicemgr1', 'lin', 'xing', 'demo', '', '', '', '',)

		call_group = CallGroup(description='test', team='team')
		call_group.save()
		cls.call_group = call_group

		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice.save()
		practice.call_groups.add(call_group)
		cls.practice = practice

	@classmethod
	def tearDownClass(cls):
		clean_db_datas()

	def setUp(self):
		self.client.post('/login/', {'username': self.user.username, 'password': 'demo'})

	def tearDown(self):
		self.client.logout()

	def test_cancelInvitation(self):
		#user is a manager
		staff = OfficeStaff(user=self.user)
		staff.current_practice = self.practice
		staff.save()
		staff.practices.add(self.practice)
		manager = Office_Manager(user=staff, practice=self.practice, manager_role=2)
		manager.save()

		#get method
		response = self.client.get(reverse('MHLogin.MHLPractices.views_ajax.cancelInvitation'))
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(msg[1], _('A server error has occured.'))

		#post method
		email = 'a1@aa.cn'
		user_type = 1
		invite = Invitation(sender=self.user, recipient=email, assignPractice=self.practice, userType=user_type)
		invite.save()

		#there is no invite find
		data = {'email': 'cc@aa.cn', 'type': '0'}
		response = self.client.post(reverse('MHLogin.MHLPractices.views_ajax.cancelInvitation'), data=data)
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(msg[1], _('A server error has occured.'))

		#there is 1 invite find
		data = {'email': email, 'type': user_type}
		response = self.client.post(reverse('MHLogin.MHLPractices.views_ajax.cancelInvitation'), data=data)
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(msg[0], 'ok')
		self.assertEqual(Invitation.objects.count(), 0)

		#a new invite
		email2 = 't@t.cn'
		invite2 = Invitation(sender=self.user, recipient=email2, assignPractice=self.practice, userType=user_type)
		invite2.save()

		data = {'email': email2, 'type': user_type}
		response = self.client.post(reverse('MHLogin.MHLPractices.views_ajax.cancelInvitation'), data=data)
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(msg[0], 'ok')


#add by xlin 121220 to test cancelExistInvitation
class CancelExistInvitationTest(TestCase):
	@classmethod
	def setUpClass(cls):
		clean_db_datas()
		cls.user = create_user('practicemgr1', 'lin', 'xing', 'demo', '', '', '', '',)

		call_group = CallGroup(description='test', team='team')
		call_group.save()
		cls.call_group = call_group

		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice.save()
		practice.call_groups.add(call_group)
		cls.practice = practice

	@classmethod
	def tearDownClass(cls):
		clean_db_datas()

	def setUp(self):
		self.client.post('/login/', {'username': self.user.username, 'password': 'demo'})

	def tearDown(self):
		self.client.logout()

	def test_cancelExistInvitation(self):
		#user is a manager
		staff = OfficeStaff(user=self.user)
		staff.current_practice = self.practice
		staff.save()
		staff.practices.add(self.practice)
		manager = Office_Manager(user=staff, practice=self.practice, manager_role=2)
		manager.save()

		#get method
		response = self.client.get(reverse('MHLogin.MHLPractices.views_ajax.cancelExistInvitation'))
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(msg[1], _('A server error has occured.'))

		email = 'a1@aa.cn'
		user_type = 1
		invite = Invitation(sender=self.user, recipient=email, assignPractice=self.practice, userType=user_type)
		invite.save()

		#there is no invite find
		data = {'email': 'cc@aa.cn', 'type': '0'}
		response = self.client.post(reverse('MHLogin.MHLPractices.views_ajax.cancelExistInvitation'), data=data)
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(msg[1], _('A server error has occured.'))

		data = {'email': email, 'type': user_type}
		response = self.client.post(reverse('MHLogin.MHLPractices.views_ajax.cancelExistInvitation'), data=data)
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(msg[0], 'ok')
		self.assertEqual(Invitation.objects.count(), 0)


#add by xlin 121220 to test sendNewProviderEmail method
class SendNewProviderEmailTest(TestCase):
	@classmethod
	def setUpClass(cls):
		clean_db_datas()
		cls.user = create_user('practicemgr1', 'lin', 'xing', 'demo', '', '', '', '',)

		call_group = CallGroup(description='test', team='team')
		call_group.save()
		cls.call_group = call_group

		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice.save()
		practice.call_groups.add(call_group)
		cls.practice = practice

	@classmethod
	def tearDownClass(cls):
		clean_db_datas()

	def setUp(self):
		self.client.post('/login/', {'username': self.user.username, 'password': 'demo'})

	def tearDown(self):
		self.client.logout()

	def test_sendNewProviderEmail(self):
		#user is a manager
		staff = OfficeStaff(user=self.user)
		staff.current_practice = self.practice
		staff.save()
		staff.practices.add(self.practice)

		#office staff call this method
		#get method
		response = self.client.get(reverse('MHLogin.MHLPractices.views_ajax.sendNewProviderEmail'))
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(msg['err'], _('A server error has occurred when you send a email. '
			'Please refresh page again.'))

		#invalid data
		data = {'userType': '33', 'msg': 'abc', 'recipient': 'ab@aa.cn'}
		response = self.client.post(reverse('MHLogin.MHLPractices.views_ajax.sendNewProviderEmail'), 
			data=data)
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(msg['err']['userType'][0], 'Select a valid choice. 33 is not one '
			'of the available choices.')

		email = 'test@aa.cn'
		provider1 = Provider(username='provider', first_name='tes', last_name="meister", email=email,
					office_lat=0.0, office_longit=0.0)
		provider1.save()

		#invalid email
		data = {'userType': 1, 'msg': 'abc', 'recipient': email}
		response = self.client.post(reverse('MHLogin.MHLPractices.views_ajax.sendNewProviderEmail'), data=data)
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(msg['err'], _('This email address is already associated with a DoctorCom account.'))

		#valid email and send a mail
		email = 'taaC@at.cn'
		data = {'userType': 2, 'msg': 'abc', 'recipient': email}
		response = self.client.post(reverse('MHLogin.MHLPractices.views_ajax.sendNewProviderEmail'), data=data)
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(msg, 'ok')
		self.assertEqual(Invitation.objects.count(), 1)
		self.assertEqual(Invitation.objects.get(recipient=email).userType, 1)

		manager = Office_Manager(user=staff, practice=self.practice, manager_role=2)
		manager.save()

		#valid email and send a mail manager login
		email = 'taaC2@at.cn'
		data = {'userType': 2, 'msg': 'abc', 'recipient': email}
		response = self.client.post(reverse('MHLogin.MHLPractices.views_ajax.sendNewProviderEmail'), data=data)
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(msg, 'ok')
		self.assertEqual(Invitation.objects.count(), 2)
		self.assertEqual(Invitation.objects.get(recipient=email).userType, 1)


#add by xlin 121221 to test getProviderByEmailOrNameInCallGroup
class GetProviderByEmailOrNameInCallGroupTest(TestCase):
	@classmethod
	def setUpClass(cls):
		clean_db_datas()
		cls.user = create_user('practicemgr1', 'lin', 'xing', 'demo', '', '', '', '',)

		call_group = CallGroup(description='test', team='team')
		call_group.save()
		cls.call_group = call_group

		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice.save()
		practice.call_groups.add(call_group)
		cls.practice = practice

	@classmethod
	def tearDownClass(cls):
		clean_db_datas()

	def setUp(self):
		self.client.post('/login/', {'username': self.user.username, 'password': 'demo'})

	def tearDown(self):
		self.client.logout()

	def test_getProviderByEmailOrNameInCallGroup(self):
		#user is a manager
		staff = OfficeStaff(user=self.user)
		staff.current_practice = self.practice
		staff.save()
		staff.practices.add(self.practice)

		#get method
		response = self.client.get(reverse('MHLogin.MHLPractices.views_ajax.getProviderByEmailOrNameInCallGroup'))
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(msg['err'], _('A server error has occurred.'))

		#post method
		searchOptions = {'email': '', 'fullname': '', 'firstName': '', 'lastName': '', 
			'username': '', 'call_group': self.call_group.id}
		response = self.client.post(reverse('MHLogin.MHLPractices.views_ajax.getProviderByEmailOrNameInCallGroup'), 
			data=searchOptions)
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 0)

		#find 1 provider
		user = create_user('provider1', 'lin', 'xing', 'demo', '', '', '', '',)
		provider1 = Provider(username='provider', first_name='tes', last_name="meister", email='p1@provider.com',
					user=user, office_lat=0.0, office_longit=0.0)
		provider1.save()

		#input option first name
		searchFirstName = {'email': '', 'fullname': 'tes', 'firstName': 'tes', 
			'lastName': '', 'username': '', 'call_group': self.call_group.id}
		response = self.client.post(reverse('MHLogin.MHLPractices.views_ajax.getProviderByEmailOrNameInCallGroup'), 
			data=searchFirstName)
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 1)

		#input option last name
		searchLastName = {'email': '', 'fullname': '', 'firstName': '', 'lastName': 'meister', 
			'username': '', 'call_group': self.call_group.id}
		response = self.client.post(reverse('MHLogin.MHLPractices.views_ajax.getProviderByEmailOrNameInCallGroup'), 
			data=searchLastName)
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 1)

		#input option user name
		searchUsername = {'email': '', 'fullname': '', 'firstName': '', 'lastName': '', 
			'username': 'provider', 'call_group': self.call_group.id}
		response = self.client.post(reverse('MHLogin.MHLPractices.views_ajax.getProviderByEmailOrNameInCallGroup'), 
			data=searchUsername)
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 1)

		#input option email
		searchEmail = {'email': 'p1@provider.com', 'fullname': '', 'firstName': 'tes', 
			'lastName': '', 'username': '', 'call_group': self.call_group.id}
		response = self.client.post(reverse('MHLogin.MHLPractices.views_ajax.getProviderByEmailOrNameInCallGroup'), 
			data=searchEmail)
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 1)

		pend = CallGroupMemberPending(from_user=self.user, to_user=provider1,
			practice=self.practice, call_group=self.call_group, created_time=datetime.datetime.now())
		pend.save()

		searchLastName = {'email': '', 'fullname': '', 'firstName': '', 
			'lastName': 'meister', 'username': '', 'call_group': self.call_group.id}
		response = self.client.post(reverse('MHLogin.MHLPractices.views_ajax.getProviderByEmailOrNameInCallGroup'), 
			data=searchLastName)
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 1)

		searchLastName = {'email': '', 'fullname': '', 'firstName': '', 
			'lastName': '', 'username': '', 'call_group': self.call_group.id}
		response = self.client.post(reverse('MHLogin.MHLPractices.views_ajax.getProviderByEmailOrNameInCallGroup'), 
			data=searchLastName)
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 1)
