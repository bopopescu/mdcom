from django.utils.unittest.case import TestCase

from MHLogin.MHLCallGroups.models import CallGroup, Specialty, CallGroupMember
from MHLogin.MHLCallGroups.utils import checkMultiCallGroupId, \
	isMultiCallGroupManager, canAccessMultiCallGroup, canAccessCallGroup, \
	isCallGroupManager, isCallGroupStaff, isCallGroupMember
from MHLogin.MHLPractices.models import PracticeLocation
from MHLogin.MHLUsers.models import OfficeStaff, Office_Manager, Administrator, \
	Provider
from MHLogin.utils.tests import create_user
from MHLogin.utils.tests.tests import clean_db_datas

#add by xlin 121213
#test checkMultiCallGroupId method
class CheckMultiCallGroupIdTest(TestCase):
	def setUp(self):
		clean_db_datas()

	def test_checkMultiCallGroupId(self):
		#init practice and call group
		call_group = CallGroup(description='test', team='team')
		call_group.save()
		
		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice.save()
		practice.call_groups.add(call_group)
		
		#pass a valid parameter
		result = checkMultiCallGroupId(practice.id, call_group.id)
		self.assertEqual(call_group.id, result)
		
		#practice not exist
#		result = checkMultiCallGroupId(117, 0)
#		self.assertRaises(PracticeLocation.DoesNotExist, result)
		
		#pass a invalid call group parameter
		result = checkMultiCallGroupId(practice.id, 0)
		self.assertEqual(call_group.id, result)
		
		#ther is a specialty
		practice2 = PracticeLocation(practice_name='test2',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice2.save()
		
		specialty_name = 'Specialty A'
		specialty1 = Specialty()
		specialty1.name = specialty_name
		specialty1.practice_location = practice2
		specialty1.number_selection = 3
		specialty1.save()
		specialty1.call_groups.add(call_group)
		
		result = checkMultiCallGroupId(practice2.id, 0)
		self.assertEqual(call_group.id, result)
	
#add by xlin 121213 to test isMultiCallGroupManager method
class IsMultiCallGroupManagerTest(TestCase):
	def setUp(self):
		clean_db_datas()

	def test_isMultiCallGroupManager(self):
		#init practice and call group
		call_group = CallGroup(description='test', team='team')
		call_group.save()
		
		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice.save()
		practice.call_groups.add(call_group)
		
		user = create_user('user1', 'us', 'er', 'demo')
		
		#only mhluser call method
		result = isMultiCallGroupManager(user, practice.id, call_group.id)
		self.assertEqual(result, False)
		
		#staff call method
		staff = OfficeStaff(user=user)
		staff.save()
		result = isMultiCallGroupManager(user, call_group.id, practice.id)
		self.assertEqual(result, False)
		
		practice2 = PracticeLocation(practice_name='test2',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice2.save()
		practice2.call_groups.add(call_group)
		
		#manager call method
		staff.practices.add(practice)
		staff.save()
		manager = Office_Manager(user=staff, practice=practice, manager_role=1)
		manager.save()
		result = isMultiCallGroupManager(user, call_group.id, practice.id)
		self.assertEqual(result, True)
		
		#manager with specialty call method
		specialty_name = 'Specialty A'
		specialty1 = Specialty()
		specialty1.name = specialty_name
		specialty1.practice_location = practice
		specialty1.number_selection = 3
		specialty1.save()
		specialty1.call_groups.add(call_group)
		
		manager2 = Office_Manager(user=staff, practice=practice2, manager_role=1)
		manager2.save()
		
		result = isMultiCallGroupManager(user, call_group.id, practice.id)
		self.assertEqual(result, True)

#add by xlin 121213 to test canAccessMultiCallGroup method
class CanAccessMultiCallGroupTest(TestCase):
	def setUp(self):
		clean_db_datas()

	def test_canAccessMultiCallGroup(self):
		#init practice and call group
		call_group = CallGroup(description='test', team='team')
		call_group.save()
		
		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice.save()
		practice.call_groups.add(call_group)
		
		#admin call this method
		admin = create_user('user-access-group2', 'us', 'er', 'demo', '', '', '', '', Administrator)
		result = canAccessMultiCallGroup(admin.user, call_group, practice.id)
		self.assertEqual(result, True)
		
		#not admin call this method
		user = create_user('user-access-group', 'us', 'er', 'demo')
		result = canAccessMultiCallGroup(user, call_group, practice.id)
		self.assertEqual(result, False)
		
#add by xlin 121214 to test canAccessCallGroup method in utils.py
class CanAccessCallGroupTest(TestCase):
	def setUp(self):
		clean_db_datas()

	def test_canAccessCallGroup(self):
		call_group = CallGroup(description='test', team='team')
		call_group.save()
		
		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',
								call_group=call_group)
		practice.save()
		practice.call_groups.add(call_group)
		
		user = create_user('user-CallGroup2', 'us', 'er', 'demo')
		staff = OfficeStaff(user=user)
		staff.save()
		staff.practices.add(practice)
		
		#a staff call this method
		result = canAccessCallGroup(staff, long(call_group.pk))
		self.assertEqual(result, False)
		
		#a manager call this method
#		manager = Office_Manager(user=staff, practice=practice, manager_role=1)
#		manager.save()
#		
#		result = canAccessCallGroup(manager, long(call_group.pk))
#		self.assertEqual(result, True)
		
		#admin call this method
		admin = create_user('user-CallGroup', 'us', 'er', 'demo', '', '', '', '', Administrator)
		result = canAccessCallGroup(admin.user, call_group)
		self.assertEqual(result, True)
		
		Administrator.objects.all().delete()

#add by xlin 121214 to test isCallGroupManager method in utils.py
class IsCallGroupManagerTest(TestCase):
	def setUp(self):
		clean_db_datas()

	def test_isCallGroupManager(self):
		call_group = CallGroup(description='test', team='team')
		call_group.save()
		
		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice.call_group = call_group
		practice.save()
		
		
		user = create_user('user4', 'us', 'er', 'demo')
		
		#a mhluser call this method
		result = isCallGroupManager(user, call_group.pk)
		self.assertEqual(result, False)
		
		staff = OfficeStaff(user=user)
		staff.save()
		staff.practices.add(practice)
		
		#a staff call this method
		result = isCallGroupManager(user, call_group.pk)
		self.assertEqual(result, False)
		
		#a manager call this method
		manager = Office_Manager(user=staff, practice=practice, manager_role=1)
		manager.save()
		
		result = isCallGroupManager(user, call_group.pk)
		self.assertEqual(result, True)

#add by xlin 121214 to test isCallGroupStaff method in utils.py
class IsCallGroupStaffTest(TestCase):
	def setUp(self):
		clean_db_datas()

	def test_isCallGroupStaff(self):
		call_group = CallGroup(description='test', team='team')
		call_group.save()
		
		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice.call_group = call_group
		practice.save()
		
		
		user = create_user('user5', 'us', 'er', 'demo')
		
		#a mhluser call this method
		result = isCallGroupStaff(user, call_group.pk)
		self.assertEqual(result, False)
		
		staff = OfficeStaff(user=user)
		staff.save()
		staff.practices.add(practice)
		
		#a staff call this method
		result = isCallGroupStaff(user, call_group.pk)
		self.assertEqual(result, True)
		
		#a manager call this method
		manager = Office_Manager(user=staff, practice=practice, manager_role=1)
		manager.save()
		
		result = isCallGroupStaff(user, call_group.pk)
		self.assertEqual(result, True)

#add by xlin 121214 to test isCallGroupMember method in utls.py
class IsCallGroupMemberTest(TestCase):
	def setUp(self):
		clean_db_datas()

	def test_isCallGroupMember(self):
		call_group = CallGroup(description='test', team='team')
		call_group.save()
		user = create_user('user6', 'us', 'er', 'demo')
		
		result = isCallGroupMember(user, call_group.id)
		self.assertEqual(result, False)
		
		provider = Provider(username='provider', first_name='tes', last_name="meister", email='aa@ada.com',
					user=user, office_lat=0.0, office_longit=0.0)
		provider.save()
		call_groupm = CallGroupMember(call_group=call_group, member=provider, alt_provider=1)
		call_groupm.save()
		
		result = isCallGroupMember(provider, call_group.id)
		self.assertEqual(result, True)
