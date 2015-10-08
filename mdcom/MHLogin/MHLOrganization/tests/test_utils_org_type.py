#-*- coding: utf-8 -*-
from MHLogin.MHLOrganization.tests.utils import create_multiple_organization_types, create_multiple_organizations,\
	create_organization
from MHLogin.MHLOrganization.utils_org_type import get_sub_types_by_typeid, can_we_remove_this_org_type, \
	can_we_create_this_type_under_that_type, how_many_instances,\
	get_parent_types_by_typeid
from MHLogin.MHLPractices.models import OrganizationType, OrganizationSetting, \
	OrganizationTypeSubs, PracticeLocation
from MHLogin.MHLUsers.models import Administrator, Office_Manager, OfficeStaff
from MHLogin.utils.constants import RESERVED_ORGANIZATION_TYPES_RESERVED
from django.test.testcases import TestCase
from MHLogin.utils.tests.tests import create_user, clean_db_datas
from MHLogin.utils.constants import RESERVED_ORGANIZATION_TYPE_ID_PRACTICE
from MHLogin.api.v1.tests.utils import get_random_username


class GetSubTypesICanUseTest(TestCase):
	org_type = None
	admin = None
	manager = None
	organization = None

	def setUp(self):
		clean_db_datas()

		OrganizationType.objects.all().delete()
		org_setting = OrganizationSetting()
		org_setting.save()
		self.org_type = OrganizationType(name="Test Org Type1", 
			organization_setting=org_setting, is_public=True)
		# TODO: issue 2030, reserved id's is a hazardous approach, the UT's 
		# were working with SQLlite but not with MySQL, DB engines recycle
		# id's differently and we should not rely on reserved id fields.  This 
		# should be addressed in a separate Redmine as model changes may occur.
		self.org_type.id = RESERVED_ORGANIZATION_TYPE_ID_PRACTICE
		self.org_type.save()

		self.organization = create_organization()
		self.organization = PracticeLocation(
			practice_name=get_random_username(),
			practice_address1='555 Pleasant Pioneer Grove',
			practice_address2='Trailer Q615',
			practice_city='Mountain View',
			practice_state='CA',
			practice_zip='94040-4104',
			practice_lat=37.36876,
			practice_longit=-122.081864)
		self.organization.save()

		self.admin = create_user('admin', 'Morris', 'Kelly', 'demo', uklass=Administrator)
		staff = create_user('practicemgr1', 'Practice', 'Mgr', 'demo', uklass=OfficeStaff)
		staff.practices.add(self.organization)
		staff.save()

		self.manager = Office_Manager(user=staff, practice=self.organization, manager_role=1)
		self.manager.save()

	def test_get_sub_types_I_can_use_empty(self):
		self.assertEqual(0, len(get_sub_types_by_typeid(self.org_type.id)))

	def test_get_sub_types_I_can_use(self):
		create_multiple_organization_types(self.org_type, num=10)
		self.assertEqual(10, len(get_sub_types_by_typeid(self.org_type.id)))

		create_multiple_organization_types(self.org_type, num=10, is_public=False)
		self.assertEqual(10, len(get_sub_types_by_typeid(self.org_type.id)))
		self.assertEqual(0, len(get_sub_types_by_typeid(self.org_type.id, is_public=True)))

	def tearDown(self):
		pass


class CanWeRemoveThisOrgTypeTest(TestCase):

	def setUp(self):
		pass

	def test_can_we_remove_this_org_type(self):
		# TODO
		for org_type_id in RESERVED_ORGANIZATION_TYPES_RESERVED:
			self.assertFalse(can_we_remove_this_org_type(org_type_id))
		self.assertTrue(can_we_remove_this_org_type(5))

	def tearDown(self):
		pass


class CanWeCreateThisTypeUnderThatTypeTest(TestCase):
	org_type = None
	sub_type = None

	def setUp(self):
		clean_db_datas()
		org_setting = OrganizationSetting()
		org_setting.save()
		self.org_type = OrganizationType(name="Test Org Type1", 
			organization_setting=org_setting, is_public=True)
		self.org_type.save()
		self.sub_type = OrganizationType(name="Test Org Type2", 
			organization_setting=org_setting, is_public=True)
		self.sub_type.save()

	def test_can_we_create_this_type_under_that_type_cant(self):
		self.assertFalse(can_we_create_this_type_under_that_type(-1, None))
		self.assertFalse(can_we_create_this_type_under_that_type(self.sub_type.id, self.org_type.id))

	def test_can_we_create_this_type_under_that_type_can(self):
		OrganizationTypeSubs.objects.create(from_organizationtype=self.org_type, 
			to_organizationtype=self.sub_type)
		self.assertTrue(can_we_create_this_type_under_that_type(self.sub_type.id, self.org_type.id))

	def tearDown(self):
		pass


class HowManyInstancesTest(TestCase):
	org_type = None

	def setUp(self):
		clean_db_datas()
		org_setting = OrganizationSetting()
		org_setting.save()
		self.org_type = OrganizationType(name="Test Org Type1", 
			organization_setting=org_setting, is_public=True)
		self.org_type.save()

	def test_how_many_instances_empty(self):
		create_multiple_organizations()
		self.assertEqual(0, len(how_many_instances(self.org_type.id)))

	def test_how_many_instances(self):
		create_multiple_organizations(num=10, org_type=self.org_type)
		self.assertEqual(10, len(how_many_instances(self.org_type.id)))

	def tearDown(self):
		pass

class GetParentTypesByTypeidTest(TestCase):
	org_type = None
	admin = None
	manager = None
	organization = None

	def setUp(self):
		clean_db_datas()

		OrganizationType.objects.all().delete()
		org_setting = OrganizationSetting()
		org_setting.save()
		self.org_type = OrganizationType(name="Test Org Type1", organization_setting=org_setting, is_public=True)
		self.org_type.save()

		self.organization = create_organization()

		self.admin = create_user('admin', 'Morris', 'Kelly', 'demo', uklass=Administrator)
		staff = create_user('practicemgr1', 'Practice', 'Mgr', 'demo', uklass=OfficeStaff)
		staff.practices.add(self.organization)
		staff.save()

		self.manager = Office_Manager(user=staff, practice=self.organization, manager_role=1)
		self.manager.save()

	def test_get_parent_types_by_typeid(self):
		create_multiple_organization_types(self.org_type, num=10)
		self.assertEqual(1, len(get_parent_types_by_typeid(self.org_type.id)))
		with self.assertRaises(Exception):get_parent_types_by_typeid('2sadfa')
		with self.assertRaises(Exception):get_parent_types_by_typeid('')

		create_multiple_organization_types(self.org_type, num=10, is_public=False)
		self.assertEqual(1, len(get_parent_types_by_typeid(self.org_type.id)))
		self.assertEqual(0, len(get_parent_types_by_typeid(self.org_type.id, is_public=True)))
		self.assertEqual(0, len(get_parent_types_by_typeid(None)))

	def tearDown(self):
		pass
