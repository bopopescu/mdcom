#-*- coding: utf-8 -*-
'''
Created on 2013-3-26

@author: wxin
'''
from MHLogin.MHLPractices.models import OrganizationType, OrganizationSetting, \
	OrganizationTypeSubs, PracticeLocation
from MHLogin.utils.constants import RESERVED_ORGANIZATION_TYPE_ID_PRACTICE


def create_multiple_organization_types(parent_type, num=10, is_public=True):
	sub_types = []
	OrganizationType.objects.all().delete()
	org_setting = OrganizationSetting()
	org_setting.save()
	for i in xrange(num):
		type_name = "".join(["Test Org Type2_", str(i)])
		_org_type = OrganizationType(name=type_name, 
			organization_setting=org_setting, is_public=is_public)
		_org_type.id = i + 1
		# TODO: issue 2030, reserved id's is a hazardous approach, the UT's 
		# were working with SQLlite but not with MySQL, DB engines recycle
		# id's differently and we should not rely on reserved id fields.  This 
		# should be addressed in a separate Redmine as model changes may occur.
		_org_type.save()
		sub_types.append(_org_type)
		OrganizationTypeSubs.objects.create(from_organizationtype=parent_type, 
			to_organizationtype=_org_type)
	return sub_types


def create_multiple_organizations(num=10, org_type=None):
	orgs = []
	if not org_type:
		org_setting = OrganizationSetting()
		org_setting.save()
		org_type = OrganizationType(name="Test Org Type2", 
			organization_setting=org_setting, is_public=True)
		org_type.save()

	for i in xrange(num):
		practice_name = "".join(["Test1_", str(i)])
		_organization = PracticeLocation(
			practice_name=practice_name,
			practice_address1='555 Pleasant Pioneer Grove',
			practice_address2='Trailer Q615',
			practice_city='Mountain View',
			practice_state='CA',
			practice_zip='94040-4104',
			practice_lat=37.36876,
			practice_longit=-122.081864,
			organization_type=org_type)
		_organization.save()
		orgs.append(_organization)
	return orgs


def create_organization_not_member(org_type=None):
	org_setting = OrganizationSetting()
	org_setting.save()
	org_type = OrganizationType(name="Test Org Type", 
		organization_setting=org_setting, is_public=True)
	organization_not_member = PracticeLocation(
		practice_name="Test2",
		practice_address1='555 Pleasant Pioneer Grove',
		practice_address2='Trailer Q615',
		practice_city='Mountain View',
		practice_state='CA',
		practice_zip='94040-4104',
		practice_lat=37.36876,
		practice_longit=-122.081864)
	if org_type:
			organization_not_member.organization_type = org_type
	organization_not_member.save()
	return organization_not_member


def create_organization(auto_type=True, org_type=None, org_type_id=None, org_name="Test Org"):
	if not org_type:
		if auto_type:
			org_setting = OrganizationSetting(can_have_luxury_logo=True,
											display_in_contact_list_tab=True)
			org_setting.save()
			type_name = "Test Org Type1"
			if org_type_id:
				org_type = OrganizationType(id=org_type_id, 
					name=type_name, organization_setting=org_setting)
				org_type.save()
			else:
				org_type = OrganizationType(name=type_name, organization_setting=org_setting)
				# force id for test - MySQL UT's don't re-use ids after cleanup 
				org_type.id = RESERVED_ORGANIZATION_TYPE_ID_PRACTICE
				# TODO: issue 2030, reserved id's is a hazardous approach, the UT's 
				# were working with SQLlite but not with MySQL, DB engines recycle
				# id's differently and we should not rely on reserved id fields.  This 
				# should be addressed in a separate Redmine as model changes may occur.
				org_type.save()

	_organization = PracticeLocation(
		practice_name="Test Org",
		practice_address1='555 Pleasant Pioneer Grove',
		practice_address2='Trailer Q615',
		practice_city='Mountain View',
		practice_state='CA',
		practice_zip='94040-4104',
		practice_lat=37.36876,
		practice_longit=-122.081864,
		organization_type=org_type)
	_organization.save()
	return _organization


def create_parent_organization(org_type=None):
	if not org_type:
		org_setting = OrganizationSetting()
		org_setting.save()
		org_type = OrganizationType(name="Test Org Type", 
			organization_setting=org_setting, is_public=True)
	parent_organization = PracticeLocation(
			practice_name="TestP",
			practice_address1='555 Pleasant Pioneer Grove',
			practice_address2='Trailer Q615',
			practice_city='Mountain View',
			practice_state='CA',
			practice_zip='94040-4104',
			practice_lat=37.36876,
			practice_longit=-122.081864)
	parent_organization.organization_type = org_type
	parent_organization.save()
	return parent_organization

