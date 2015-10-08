#-*- coding: utf-8 -*-
from datetime import datetime

from django.test.testcases import TestCase

from MHLogin.MHLOrganization.utils import get_member_orgs, save_member_org,\
	can_user_manage_this_org, can_user_manage_org_module, which_orgs_contain_this_user, get_org_members,\
	get_org_staff, is_user_in_this_org, has_sent_org_invitation_to_this_user, get_all_parent_org_ids,\
	get_all_child_org_ids, get_other_organizations, can_we_remove_this_org,\
	get_org_all_providers, get_org_providers, get_orgs_I_can_manage,\
	format_tree_data, notify_org_users_tab_chanaged
from MHLogin.MHLPractices.models import OrganizationSetting, OrganizationType, \
	 Pending_Association, OrganizationRelationship
from MHLogin.MHLUsers.models import Administrator, OfficeStaff, Office_Manager, Provider
from MHLogin.utils.tests.tests import clean_db_datas
from MHLogin.MHLOrganization.tests.utils import create_multiple_organizations,\
	create_organization_not_member, create_organization, create_parent_organization
from MHLogin.MHLOrganization.tests.test_org import MHLOrgTest
from MHLogin.api.v1.tests.utils import create_user, get_random_username


class OrganizationSettingTest(TestCase):
	organization = None
	org_setting = None
	org_type = None
	org_type_setting = None

	def setUp(self):
		clean_db_datas()
		self.organization = create_organization(auto_type=False)

		self.org_setting = OrganizationSetting()
		self.org_setting.save()

		self.org_type_setting = OrganizationSetting()
		self.org_type_setting.save()
		self.org_type = OrganizationType(name="Test Org Type", organization_setting=self.org_type_setting)
		self.org_type.save()

	def testOrganizationSetting_None(self):
		self.assertIsNone(self.organization.get_setting())

		self.organization.organization_setting = self.org_setting
		self.organization.save()
		self.org_setting.delete_flag = True
		self.org_setting.save()
		self.assertIsNone(self.organization.get_setting())

	def testOrganizationSetting_FromOrganization(self):
		self.organization.organization_setting = self.org_setting
		self.organization.save()
		self.org_setting.delete_flag = False
		self.org_setting.save()
		self.assertEqual(self.org_setting, self.organization.get_setting())

		self.organization.organization_type = self.org_type
		self.organization.save()
		setting = self.organization.get_setting()
		self.assertEqual(self.org_setting, setting)
		self.assertNotEqual(self.org_type_setting, setting)

	def testOrganizationSetting_FromOrganizationType(self):
		self.organization.organization_type = self.org_type
		self.organization.organization_setting = None
		self.organization.save()
		self.assertEqual(self.org_type_setting, self.organization.get_setting())

		self.org_setting.delete_flag = True
		self.org_setting.save()
		self.organization.organization_type = self.org_type
		self.organization.organization_setting = self.org_setting
		self.organization.save()
		setting = self.organization.get_setting()
		self.assertEqual(self.org_type_setting, setting)
		self.assertNotEqual(self.org_setting, setting)

	def tearDown(self):
		clean_db_datas()

class GetMemberOrgTest(TestCase):
	organization = None
	parent_organization = None
	org_members = []
	organization_not_member = None

	def setUp(self):
		clean_db_datas()

		self.parent_organization = create_parent_organization()

		self.organization = create_organization()
		self.organization.save_parent_org(parent_org=self.parent_organization)

		self.org_members = []
		self.org_members = create_multiple_organizations(10)

		self.organization_not_member = create_organization_not_member()

	def test_get_member_orgs(self):
		org_member_ids = []
		for _organization in self.org_members:
			save_member_org(self.organization.id, _organization, billing_flag=0)
			org_member_ids.append(_organization.id)

		org_members = get_member_orgs(self.organization.id)
		self.assertEqual(len(org_member_ids), len(org_members))
		for org in org_members:
			self.assertIn(org.id, org_member_ids)
		self.assertNotIn(self.organization_not_member.id, org_member_ids)

	def test_get_member_orgs_distinct(self):
		org_member_ids = []
		for _organization in self.org_members:
			save_member_org(self.organization.id, _organization, billing_flag=0)
			save_member_org(self.parent_organization.id, _organization, billing_flag=0)
			org_member_ids.append(_organization.id)

		org_members = get_member_orgs(self.organization.id)
		self.assertEqual(len(org_member_ids), len(org_members))
		for org in org_members:
			self.assertIn(org.id, org_member_ids)
		self.assertNotIn(self.organization_not_member.id, org_member_ids)

	def tearDown(self):
		clean_db_datas()

class GetOrgSubUserTypesTest(TestCase):
	organization = None
	org_setting = None
	org_type = None
	org_type_setting = None

	def setUp(self):
		clean_db_datas()

		self.org_setting = OrganizationSetting(
				can_have_physician = True,
				can_have_nppa = True,
				can_have_medical_student = True,
				can_have_staff = True,
				can_have_manager = True,
				can_have_nurse = True,
				can_have_tech_admin = True,
			)
		self.org_setting.save()

		self.organization = create_organization()
		self.organization.organization_setting = self.org_setting

	def test_get_org_sub_user_types(self):
		self.assertListEqual([1,2,10,100,101,3,-1], self.organization.get_org_sub_user_types())

	def tearDown(self):
		clean_db_datas()

class CanUserManageThisOrgTest(TestCase):
	organization = None

	def setUp(self):
		clean_db_datas()

		self.organization = create_organization()

	def test_can_user_manage_this_org(self):
		user = create_user(get_random_username(),'yang','peng','demo')
		admin = Administrator(user=user)
		admin.save()
		self.assertTrue(can_user_manage_this_org(self.organization.id, admin.user.id)["can_manage_org"])
		
		self.user = create_user(get_random_username(),'yang','peng','demo')
		staff = OfficeStaff()
		staff.user = self.user
		staff.office_lat = 0.0
		staff.office_longit = 0.0
		staff.current_practice = self.organization
		staff.save()
		staff.practices.add(self.organization)
		self.assertFalse(can_user_manage_this_org(self.organization.id, staff.user.id)["can_manage_org"])

		Office_Manager.objects.create(user=staff, practice=self.organization, manager_role=1)
		self.assertTrue(can_user_manage_this_org(self.organization.id, staff.user.id)["can_manage_org"])

	def tearDown(self):
		clean_db_datas()

class CanUserManageOrgModuleTest(TestCase):
	organization = None
	def setUp(self):
		clean_db_datas()
		self.organization = create_organization()
		
	def test_can_user_manage_org_module(self):
		user = create_user(get_random_username(),'yang','peng','demo')
		admin = Administrator(user=user)
		self.assertTrue(can_user_manage_org_module(admin.user.id))

		user1 = create_user(get_random_username(),'yang','peng','demo')
		staff = OfficeStaff()
		staff.user = user1
		staff.office_lat = 0.0
		staff.office_longit = 0.0
		staff.current_practice = self.organization
		staff.save()
		staff.practices.add(self.organization)
		self.assertFalse(can_user_manage_org_module(staff.user.id)["can_manage_org"])

		Office_Manager.objects.create(user=staff, practice=self.organization, manager_role=1)
		self.assertTrue(can_user_manage_org_module(staff.user.id)["can_manage_org"])

	def tearDown(self):
		clean_db_datas()

class WhichOrgsContainThisUserByIdTest(TestCase):
	orgs = []
	org = None
	org_type = None
	staff = None
	def setUp(self):
		clean_db_datas()
		self.user = create_user(get_random_username(),'yang','peng','demo')
		org_setting = OrganizationSetting(display_in_contact_list_tab=True)
		org_setting.save()
		self.org_type = OrganizationType(name="Test Org Type", organization_setting=org_setting, is_public=True)
		self.org_type.save()
		self.org = create_organization()
		staff = OfficeStaff()
		staff.user = self.user
		staff.office_lat = 0.0
		staff.office_longit = 0.0
		staff.save()
		self.staff = staff

		self.org_members = []
		self.org_members = create_multiple_organizations(10)

	def test_which_orgs_contain_this_user(self):
		org_ids = []
		for p in self.orgs:
			self.staff.practices.add(p)
			org_ids.append(p.id)
		self.staff.save()

		orgs_contain = which_orgs_contain_this_user(self.staff.user.id, in_tab=False)
		orgs_contain_ids = [p.id for p in orgs_contain]
		self.assertEqual(len(org_ids), len(orgs_contain_ids))
		self.assertListEqual(org_ids, orgs_contain_ids)
		self.assertNotIn(self.org.id, orgs_contain_ids)

	def test_which_orgs_contain_this_user_in_tab(self):
		org_ids = []
		for p in self.orgs:
			org_setting = OrganizationSetting(display_in_contact_list_tab=True)
			org_setting.save()
			p.organization_setting = org_setting
			p.save()
			self.staff.practices.add(p)
			org_ids.append(p.id)
		self.staff.save()

		orgs_contain = which_orgs_contain_this_user(self.staff.user.id, in_tab=True)
		orgs_contain_ids = [p.id for p in orgs_contain]
		self.assertEqual(len(org_ids), len(orgs_contain_ids))
		self.assertListEqual(org_ids, orgs_contain_ids)
		self.assertNotIn(self.org.id, orgs_contain_ids)

	def test_which_orgs_contain_this_user_in_tab_from_org_type(self):
		org_ids = []
		for p in self.orgs:
			p.organization_type = self.org_type
			p.save()
			self.staff.practices.add(p)
			org_ids.append(p.id)
		self.staff.save()

		orgs_contain = which_orgs_contain_this_user(self.staff.user.id, in_tab=True)
		orgs_contain_ids = [p.id for p in orgs_contain]
		self.assertEqual(len(org_ids), len(orgs_contain_ids))
		self.assertListEqual(org_ids, orgs_contain_ids)
		self.assertNotIn(self.org.id, orgs_contain_ids)

	def tearDown(self):
		clean_db_datas()

class GetOrgMembersUtilsTest(TestCase):
	org_staff = []
	org_providers = []
	org = None
	staff = None
	provider = None

	def setUp(self):
		clean_db_datas()

		org_setting = OrganizationSetting()
		org_setting.save()
		org_type = OrganizationType(name="Test Org Type", organization_setting=org_setting, is_public=True)
		org_type.save()
		self.org = create_organization()

		for i in range(10):
			user_name = "".join(["Staff1_", str(i)])
			first_name = "".join(["Test1_", str(i)])
			user = create_user(user_name, first_name, 'S', 'demo')
			self.staff = OfficeStaff()
			self.staff.user = user
			self.staff.office_lat = 0.0
			self.staff.office_longit = 0.0
			self.staff.save()
			self.org_staff.append(self.staff)

			# IntegrityError: column username is not unique
#			provider_name = "".join(["Pravider1_", str(i)])
#			pro = create_user(provider_name, 'Provider', 'P', 'demo', uklass=Provider)
#			self.org_providers.append(pro)
		self.user = create_user(get_random_username(), 'staff', 'S', 'demo')
		staff = OfficeStaff()
		staff.user = self.user
		staff.office_lat = 0.0
		staff.office_longit = 0.0
		staff.save()
		self.staff = staff
		self.provider = create_user("Pravider2", 'Provider', 'P', 'demo', uklass=Provider)
		self.provider.save()

	def test_get_org_members(self):
		user_ids = []
		staff_user_ids = []
		provider_user_ids = []
		for usr in self.org_staff:
			usr.practices.add(self.org)
			usr.save()
			user_ids.append(usr.user.id)
			staff_user_ids.append(usr.user.id)

		for usr in self.org_providers:
			usr.practices.add(self.org)
			usr.save()
			user_ids.append(usr.user.id)
			provider_user_ids.append(usr.user.id)

		members = get_org_members(self.org.id)
		member_ids = [p.user.id for p in members]
		self.assertListEqual(user_ids, member_ids)

		self.assertNotIn(self.provider.user.id, member_ids)
		self.assertNotIn(self.staff.user.id, member_ids)

		self.assertEqual(0, len(get_org_staff(self.org.id, user_name="Staff2")))
		self.assertEqual(10, len(get_org_staff(self.org.id)))

		for id in user_ids:
			self.assertTrue(is_user_in_this_org(self.org.id, user_id=id))
		self.assertFalse(is_user_in_this_org(self.org.id, user_id=self.staff.user.id))
		self.assertFalse(is_user_in_this_org(self.org.id, user_name="Staff2"))
		self.assertFalse(is_user_in_this_org(self.org.id, user_name="Provider2"))

	def tearDown(self):
		clean_db_datas()

class HasSentOrgInvitationToThisUserTest(TestCase):
	org = None
	staff = None
	provider = None
	manager = None

	def setUp(self):
		clean_db_datas()

		org_setting = OrganizationSetting()
		org_setting.save()
		org_type = OrganizationType(name="Test Org Type", organization_setting=org_setting, is_public=True)
		org_type.save()
		self.org = create_organization()

		user1 = create_user(get_random_username(), 'Test1', 'S', 'demo')
		staff1 = OfficeStaff()
		staff1.user = user1
		staff1.office_lat = 0.0
		staff1.office_longit = 0.0
		staff1.current_practice = self.org
		staff1.save()
		staff1.practices.add(self.org)
		self.manager = Office_Manager(user=staff1, practice=self.org, manager_role=1)

		user = create_user(get_random_username(), 'Test1', 'S', 'demo')
		staff = OfficeStaff()
		staff.user = user
		staff.office_lat = 0.0
		staff.office_longit = 0.0
		staff.save()
		self.staff = staff
		
		self.provider = create_user("Pravider2", 'Provider', 'P', 'demo', uklass=Provider)
		self.provider.save()

	def test_has_sent_org_invitation_to_this_user_notsent(self):
		self.assertFalse(has_sent_org_invitation_to_this_user(self.org.id, self.staff.user.id))
		self.assertFalse(has_sent_org_invitation_to_this_user(self.org.id, self.provider.user.id))

	def test_has_sent_org_invitation_to_this_user_sent(self):
		Pending_Association.objects.create(
				from_user = self.manager.user.user,
				to_user = self.staff.user,
				practice_location = self.org,
				created_time=datetime.now()
			)
		Pending_Association.objects.create(
				from_user =self.manager.user.user,
				to_user = self.provider.user,
				practice_location = self.org,
				created_time=datetime.now()
			)
		self.assertTrue(has_sent_org_invitation_to_this_user(self.org.id, self.staff.user.id))
		self.assertTrue(has_sent_org_invitation_to_this_user(self.org.id, self.provider.user.id))

	def tearDown(self):
		clean_db_datas()


class SaveMemberOrgTest(TestCase):
	organization = None
	parent_organization = None
	org_members = []
	organization_not_member = None

	def setUp(self):
		clean_db_datas()

		self.parent_organization = create_parent_organization()

		self.organization = create_organization()
		self.organization.save_parent_org(parent_org=self.parent_organization)

		self.org_members = []
		self.org_members = create_multiple_organizations(10)

		self.organization_not_member = create_organization_not_member()


	def test_save_member_org(self):
		for _organization in self.org_members:
			save_member_org(self.organization.id, _organization, billing_flag=0)
			
		self.assertEqual(save_member_org(self.organization.id, _organization),None)
		
	def tearDown(self):
		clean_db_datas()

class GetAllParentOrgIdsTest(TestCase):
	organization = None
	parent_organization = None
	org_members = []
	organization_not_member = None

	def setUp(self):
		clean_db_datas()

		self.parent_organization = create_parent_organization()

		self.organization = create_organization()
		self.organization.save_parent_org(parent_org=self.parent_organization)

		self.org_members = []
		self.org_members = create_multiple_organizations(10)

		self.organization_not_member = create_organization_not_member()


	def test_get_all_parent_org_ids(self):
		org_member_ids = []
		self.assertEqual(len(get_all_parent_org_ids([])),0)
		for _organization in self.org_members:
			org_member_ids.append(_organization.id)
		self.assertEqual(len(get_all_parent_org_ids(org_member_ids)),10)
		org_member_ids = 5
		with self.assertRaises(Exception):get_all_parent_org_ids(org_member_ids)
		org_member_ids = "5"
		self.assertEqual(len(get_all_parent_org_ids(org_member_ids)),1)
		
	def tearDown(self):
		clean_db_datas()

class GetAllChildOrgIdsTest(TestCase):
	organization = None
	parent_organization = None
	org_members = []
	organization_not_member = None

	def setUp(self):
		clean_db_datas()

		self.parent_organization = create_parent_organization()

		self.organization = create_organization()
		self.organization.save_parent_org(parent_org=self.parent_organization)

		self.org_members = []
		self.org_members = create_multiple_organizations(10)

		self.organization_not_member = create_organization_not_member()

	def test_get_all_child_org_ids(self):
		org_member_ids = []
		self.assertEqual(len(get_all_child_org_ids([])),0)
		for _organization in self.org_members:
			org_member_ids.append(_organization.id)
		self.assertEqual(len(get_all_child_org_ids(org_member_ids)),10)
		org_member_ids = 5
		with self.assertRaises(Exception):get_all_child_org_ids(org_member_ids)
		org_member_ids = "5"
		self.assertEqual(len(get_all_child_org_ids(org_member_ids)),1)
		
	def tearDown(self):
		clean_db_datas()

class GetOtherOrganizationsTest(TestCase):
	organization = None
	parent_organization = None
	org_members = []
	organization_not_member = None

	def setUp(self):
		clean_db_datas()

		self.parent_organization = create_parent_organization()

		self.organization = create_organization()
		self.organization.save_parent_org(parent_org=self.parent_organization)

		self.org_members = []
		self.org_members = create_multiple_organizations(10)

		self.organization_not_member = create_organization_not_member()


	def test_get_other_organizations(self):
		
		for _organization in self.org_members:
			self.assertEqual(get_other_organizations(_organization.id),[])
		self.assertEqual(get_other_organizations(''),[])
		
	def tearDown(self):
		clean_db_datas()
	
class CanWeRemoveThisOrgTest(TestCase):
	organization = None
	parent_organization = None
	org_members = []
	organization_not_member = None

	def setUp(self):
		clean_db_datas()

		self.parent_organization = create_parent_organization()

		self.organization = create_organization()
		self.organization.save_parent_org(parent_org=self.parent_organization)

		self.org_members = []
		self.org_members = create_multiple_organizations(10)

		self.organization_not_member = create_organization_not_member()

	def test_can_we_remove_this_org(self):
		user = create_user(get_random_username(),'yang','peng','demo')
		admin = Administrator(user=user)
		admin.save()
		self.assertTrue(can_we_remove_this_org(self.organization.id, admin.user.id))
		self.assertFalse(can_we_remove_this_org(admin.user.id, self.organization.id))
		
	def tearDown(self):
		clean_db_datas()
	
class GetOrgsICanManageTest(TestCase):
	organization = None
	parent_organization = None
	org_members = []
	organization_not_member = None
	
	def setUp(self):
		clean_db_datas()
		self.parent_organization = create_parent_organization()

		self.organization = create_organization()
		
		self.organization.save_parent_org(parent_org=self.parent_organization)

		self.org_members = []
		self.org_members = create_multiple_organizations(10)

		self.organization_not_member = create_organization_not_member()
		
	def test_get_orgs_I_can_manage(self):
		user = create_user(get_random_username(),'yang','peng','demo')
		admin = Administrator(user=user)
		admin.save()
		org_ids_excluded = self.organization.id
		self.assertEqual(len(get_orgs_I_can_manage(
						admin.id,org_id_excluded=org_ids_excluded)),0)
	def test_get_orgs_I_can_manage_user(self):
		user = create_user('yangpeng','yang','peng','demo')
		org_setting = OrganizationSetting()
		org_setting.save()
		org_type = OrganizationType(name="Test Org Type", \
				organization_setting=org_setting, is_public=True)
		org_type.save()
		staff = OfficeStaff()
		staff.user = user
		staff.office_lat = 0.0
		staff.office_longit = 0.0
		staff.current_practice = self.organization
		staff.save()
		staff.practices.add(self.organization)
		mgr = Office_Manager(user=staff, practice=self.organization, manager_role=2)
		mgr.save()
		get_orgs_I_can_manage(mgr.id,parent_id=self.parent_organization.id,\
				org_type_id=org_type.id,clear_no_type_org=True)
		
	def tearDown(self):
		clean_db_datas()

class GetOrgAllProviders(MHLOrgTest):
	organization = None
	parent_organization = None
	org_members = []
	organization_not_member = None
	def test_get_org_all_providers(self):
		user_name = self.practice.practice_name
		self.assertEqual(len(get_org_all_providers(self.practice.id)),0)
		self.assertEqual(len(get_org_providers(self.practice.id,user_name)),0)

	def tearDown(self):
		clean_db_datas()

class FormatTreeDataTest(MHLOrgTest):
	organization = None
	parent_organization = None
	org_members = []
	organization_not_member = None
	def test_format_tree_data(self):
		org_rs = OrganizationRelationship.objects.filter(organization=self.old_parent_practice,
						parent=None)
		result = format_tree_data(org_rs,is_flat=False)
		self.assertEqual(result[0]['attr']['name'], 'old org parent')

class NotifyOrgUsersTabChanagedTest(TestCase):
	def setUp(self):
		clean_db_datas()
		self.user = create_user(get_random_username(),'yang','peng','demo')
		self.organization = create_organization()
		self.parent_organization = create_parent_organization()
		self.organization.save_parent_org(parent_org=self.parent_organization)
		staff = OfficeStaff()
		staff.user = self.user
		staff.office_lat = 0.0
		staff.office_longit = 0.0
		staff.current_practice = self.organization
		staff.save()
		staff.practices.add(self.organization)

		mgr = Office_Manager(user=staff, practice=self.organization, manager_role=2)
		mgr.save()

		self.provider = create_user(get_random_username(), "doc", "holiday", "demo", uklass=Provider)
		self.provider.current_practice = self.parent_organization
		self.provider.save()
		self.provider.practices.add(self.parent_organization)

	def tearDown(self):
		pass

	def test_notify_org_users_tab_chanaged(self):
		self.assertTrue(notify_org_users_tab_chanaged(self.parent_organization.id))
		