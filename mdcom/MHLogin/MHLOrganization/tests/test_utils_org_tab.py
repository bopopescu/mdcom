#-*- coding: utf-8 -*-
'''
Created on 2013-5-10

@author: pyang
'''
from django.test.testcases import TestCase
from MHLogin.utils.tests.tests import clean_db_datas, create_user
from MHLogin.MHLPractices.models import PracticeLocation, OrganizationSetting,\
	OrganizationType
from MHLogin.MHLOrganization.utils import save_member_org, get_member_orgs,\
	get_org_staff, is_user_in_this_org
from MHLogin.MHLOrganization.utils_org_tab import getOrganizationsOfUser,\
	getOrgMembers
from MHLogin.MHLOrganization.tests.utils import create_multiple_organizations,\
	create_organization, create_parent_organization, create_organization_not_member
from MHLogin.MHLUsers.models import OfficeStaff, Provider


class GetOrganizationsOfUserTest(TestCase):
	org_type = None
	admin = None
	manager = None
	organization = None

	def setUp(self):
		clean_db_datas()

		self.parent_organization = create_parent_organization()
		self.organization = create_organization()
		self.organization.save_parent_org(parent_org=self.parent_organization)

		self.org_members = []
		self.org_members = create_multiple_organizations(10)

		self.organization_not_member = create_organization_not_member()

	def testGetOrganizationsOfUser(self):
		org_member_ids = []
		for _organization in self.org_members:
			save_member_org(self.organization.id, _organization, billing_flag=0)
			org_member_ids.append(_organization.id)

		org_members = get_member_orgs(self.organization.id)
		self.assertEqual(len(org_member_ids), len(org_members))
		for org in org_members:
			self.assertEqual([],getOrganizationsOfUser(org,current_practice=_organization))
		with self.assertRaises(Exception):getOrganizationsOfUser('')
		self.assertIsNotNone(org,"None is not valid type")

	def tearDown(self):
		pass


class GetOrgMembersTest(TestCase):
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
		self.org = PracticeLocation(
			practice_name="Test1",
			practice_address1='555 Pleasant Pioneer Grove',
			practice_address2='Trailer Q615',
			practice_city='Mountain View',
			practice_state='CA',
			practice_zip='94040-4104',
			practice_lat=37.36876,
			practice_longit= -122.081864)
		self.org.organization_type = org_type
		self.org.save()

		for i in range(10):
			user_name = "".join(["Staff1_", str(i)])
			first_name = "".join(["Test1_", str(i)])
			user = create_user(user_name, first_name, 'S', 'demo', uklass=OfficeStaff)
			self.org_staff.append(user)

			# IntegrityError: column username is not unique
#			provider_name = "".join(["Pravider1_", str(i)])
#			pro = create_user(provider_name, 'Provider', 'P', 'demo', uklass=Provider)
#			self.org_providers.append(pro)

		self.staff = create_user("Staff2", 'Test2', 'S', 'demo', uklass=OfficeStaff)
		self.staff.save()
		self.provider = create_user("Pravider2", 'Provider', 'P', 'demo', uklass=Provider)
		self.provider.save()

	def testGetOrgMembers(self):
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

		members = getOrgMembers(self.org.id)
		member_ids = [p.user.id for p in members]
		self.assertListEqual(user_ids, member_ids)

		self.assertNotIn(self.provider.user.id, member_ids)
		self.assertNotIn(self.staff.user.id, member_ids)

		self.assertEqual(0, len(get_org_staff(self.org.id, user_name="Staff2")))
		self.assertEqual(1, len(get_org_staff(self.org.id, user_name="Test1_1")))

		for id in user_ids:
			self.assertTrue(is_user_in_this_org(self.org.id, user_id=id))
		self.assertFalse(is_user_in_this_org(self.org.id, user_id=self.staff.user.id))
		self.assertFalse(is_user_in_this_org(self.org.id, user_name="Staff2"))
		self.assertFalse(is_user_in_this_org(self.org.id, user_name="Provider2"))

	def tearDown(self):
		pass