#-*- coding: utf-8 -*-
'''
Created on 2013-3-26

@author: wxin
'''
from MHLogin.MHLPractices.models import OrganizationType, OrganizationSetting, \
	PracticeLocation, OrganizationRelationship
from django.test.testcases import TestCase
from MHLogin.utils.tests.tests import clean_db_datas, create_user
from MHLogin.api.v1.tests.utils import get_random_username
from MHLogin.MHLUsers.models import OfficeStaff, Office_Manager
import time


class MHLOrgTest(TestCase):
	@classmethod
	def setUpClass(cls):
		from MHLogin.MHLOrganization.tests.utils import create_multiple_organization_types
		clean_db_datas()
		cls.user = create_user('practicemgr1', 'lin', 'xing', 'demo')
		org_setting = OrganizationSetting(can_have_staff=True, 
			can_have_nurse=True, can_have_dietician=True)
		org_setting.save()

		org_type = OrganizationType(name="Test Org Type - old type", 
				organization_setting=org_setting, is_public=True)
		org_type.save()
		cls.org_type = org_type

		parent_org_type = OrganizationType(name="Test Org Type - parent type", organization_setting=org_setting, is_public=True)
		parent_org_type.save()
		cls.parent_org_type = parent_org_type

		sub_types = create_multiple_organization_types(parent_org_type)
		cls.sub_types = sub_types

		old_parent_practice = PracticeLocation(practice_name='old org parent',
								practice_longit='0.1',
								practice_lat='0.0',
								organization_setting=org_setting,
								organization_type=parent_org_type,)
		old_parent_practice.save()
		OrganizationRelationship.objects.create(organization=old_parent_practice,
			parent=None, create_time=int(time.time()), billing_flag=True)
		cls.old_parent_practice = old_parent_practice

		practice = PracticeLocation(practice_name='test org',
								practice_longit='0.1',
								practice_lat='0.0',
								organization_setting=org_setting,
								organization_type=org_type,)
		practice.save()

		OrganizationRelationship.objects.create(organization=practice,\
			parent=old_parent_practice, create_time=int(time.time()), billing_flag=True)

		new_parent_practice = PracticeLocation(practice_name='new org parent',
								practice_longit='0.1',
								practice_lat='0.0',
								organization_setting=org_setting,
								organization_type=parent_org_type,)
		new_parent_practice.save()
		OrganizationRelationship.objects.create(organization=new_parent_practice,
			parent=None, create_time=int(time.time()), billing_flag=True)

		cls.new_parent_practice = new_parent_practice
		cls.practice = practice

		staff = OfficeStaff()
		staff.user = cls.user
		staff.office_lat = 0.0
		staff.office_longit = 0.0
		staff.current_practice = practice
		staff.save()
		staff.practices.add(practice)
		staff.practices.add(old_parent_practice)
		staff.practices.add(new_parent_practice)
		cls.staff = staff
		Office_Manager.objects.create(user=staff, practice=practice, manager_role=2)

		datadict = {
			'user_type':1,
			'org_id': practice.id,
			'username':get_random_username(),
			'first_name':'yang',
			'last_name':'peng',
			'mobile_phone':9001111111,
			'gender':'M',
			'email':'cprovider1@suzhoukada.com',
			'lat':0.0, 
			'longit':0.0, 
			'address1':'address1', 
			'address2':'address2', 
			'city':'Chicago', 
			'state':'IL', 
			'zip':60601,
			'user_type':1,
			'office_lat':41.885805,
			'office_longit':-87.6229106,
		}
		cls.datadict = datadict

	@classmethod
	def tearDownClass(cls):
		clean_db_datas()

	def setUp(self):
		self.client.post('/login/', {'username': self.user.username, 'password': 'demo'})

	def tearDown(self):
		self.client.logout()	
