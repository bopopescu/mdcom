#-*- coding: utf-8 -*-

import datetime
import json
import time
import mock

from django.core.urlresolvers import reverse
from django.test.testcases import TestCase

from MHLogin.MHLOrganization.forms import OrganizationProfileSimpleForm, \
	OrgTypeForm
from MHLogin.MHLOrganization.tests.utils import create_multiple_organization_types
from MHLogin.MHLPractices.forms import HolidaysForm, PracticeProfileForm
from MHLogin.MHLPractices.forms_org import OrganizationSettingForm
from MHLogin.MHLPractices.models import PracticeLocation, \
	OrganizationRelationship, OrganizationSetting, OrganizationType, PracticeHours, \
	PracticeHolidays, Pending_Org_Association, OrganizationMemberOrgs,\
	Log_Org_Association, AccessNumber
from MHLogin.MHLUsers.forms import CreateProviderForm,\
	CreateMHLUserForm, CreateOfficeStaffForm
from MHLogin.MHLUsers.models import OfficeStaff, Office_Manager, Administrator,\
	Provider, Broker
from MHLogin.api.v1.tests.utils import get_random_username
from MHLogin.utils.tests.tests import clean_db_datas, create_user
from MHLogin.MHLOrganization.tests.test_org import MHLOrgTest


class OrgListTest(MHLOrgTest):
	def test_org_list(self):
		response = self.client.get(reverse('MHLogin.MHLOrganization.views.org_list'))
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'MHLOrganization/includes/organization_template.html')


class OrgTreeTest(MHLOrgTest):
	def test_org_tree(self):
		OrganizationRelationship.objects.filter(parent=None,organization=self.old_parent_practice)
		response = self.client.post(reverse('MHLogin.MHLOrganization.views.org_tree'),\
				data={'root_node':self.old_parent_practice.id,'show_parent':True})
		self.assertEqual(response.status_code, 200)
		OrganizationRelationship.objects.filter(parent=None,organization=self.old_parent_practice)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 1)


class OrgSettingEditTest(MHLOrgTest):
	def test_org_setting_edit(self):
		response = self.client.post(reverse('MHLogin.MHLOrganization.views.org_setting_edit'),\
				data={'org_id': self.practice.id})
		self.assertEqual(self.practice.organization_setting.delete_flag, False)
		self.assertEqual(response.status_code, 200)
		self.failUnless(isinstance(response.context['form'], OrganizationSettingForm))
		self.assertTemplateUsed(response, 'MHLOrganization/Settings/org_setting.html')

		count = OrganizationSetting.objects.filter(delete_flag=True).count()
		response = self.client.post(reverse('MHLogin.MHLOrganization.views.org_setting_edit'),\
				data={'org_id': self.practice.id,'inherit_org_type':'true'})
		count_org_org_setting = OrganizationSetting.objects.filter(delete_flag=True).count()
		self.assertEqual(1, count_org_org_setting-count)
		self.assertEqual(response.status_code, 200)
		self.failUnless(isinstance(response.context['form'], OrganizationSettingForm))
		self.assertTemplateUsed(response, 'MHLOrganization/Settings/org_setting.html')

		response = self.client.get(reverse('MHLogin.MHLOrganization.views.org_setting_edit'),\
				data={'org_id': self.practice.id})
		self.assertEqual(response.status_code, 200)
		self.failUnless(isinstance(response.context['form'], OrganizationSettingForm))
		self.failIf(response.context['form'].is_valid())
		self.assertTemplateUsed(response, 'MHLOrganization/Settings/org_setting.html')

		self.practice.organization_setting = None
		self.practice.save()
		count_no_setting = OrganizationSetting.objects.all().count()
		response = self.client.post(reverse('MHLogin.MHLOrganization.views.org_setting_edit'),\
				data={'org_id': self.practice.id})
		count_org_setting = OrganizationSetting.objects.all().count()
		self.assertEqual(response.status_code, 200)
		self.assertEqual(1, count_org_setting-count_no_setting)
		self.assertTemplateUsed(response, 'MHLOrganization/Settings/org_setting.html')


class OrgAddTest(TestCase):
	@classmethod
	def setUpClass(cls):
		clean_db_datas()
		cls.user = create_user('practicemgr1', 'lin', 'xing', 'demo')

		org_setting = OrganizationSetting()
		org_setting.save()
		org_type = OrganizationType(name="Test Org Type", 
			organization_setting=org_setting, is_public=True)
		org_type.save()
		cls.org_type = org_type
		sub_types = create_multiple_organization_types(org_type)
		cls.sub_types = sub_types

		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',
								organization_type = org_type)
		practice.save()
		practice1 = PracticeLocation(practice_name='test1',
								practice_longit='0.1',
								practice_lat='0.0',
								organization_type = org_type)
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

	def test_org_add_no_permission(self):
		response = self.client.get(reverse('MHLogin.MHLOrganization.views.org_add'), \
				data={'org_id': self.practice.id, 'parent_org_ids': self.sub_types[9].id, \
				'user_id':self.practice.id,'organization_type':self.sub_types[0]})
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'MHLOrganization/Information/org_no_permission.html')

	def test_org_add(self):
		response = self.client.get(reverse('MHLogin.MHLOrganization.views.org_add'), \
				data={'org_id': self.practice.id, 'parent_org_ids': self.practice.id, \
				'user_id':self.practice.id,'organization_type':self.sub_types[0]})
		self.assertEqual(response.status_code, 200)
		self.failIf(response.context['form'].is_valid())
		self.failUnless(isinstance(response.context['form'], OrganizationProfileSimpleForm))
		self.assertTemplateUsed(response, 'MHLOrganization/Information/org_add.html')


class OrgSaveTest(TestCase):
	@classmethod
	def setUpClass(cls):
		clean_db_datas()
		cls.user = create_user('practicemgr1', 'lin', 'xing', 'demo')
		org_setting = OrganizationSetting()
		org_setting.save()
		org_type = OrganizationType(name="Test Org Type", 
			organization_setting=org_setting, is_public=True)
		org_type.save()
		cls.org_type = org_type
		sub_types = create_multiple_organization_types(org_type)
		cls.sub_types = sub_types

		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',
								organization_type=org_type,)
		practice.save()
		practice1 = PracticeLocation(practice_name='test1',
								practice_longit='0.1',
								practice_lat='0.0',
								organization_type=org_type,)
		practice1.save()
		OrganizationRelationship.objects.create(organization=practice,
			parent=practice1, create_time=int(time.time()), billing_flag=True)
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

	def test_org_save(self):
		organization_type = self.sub_types[0].id
		data = [{'parent_org_ids': self.practice.id, 'org_id': self.practice.id,\
					'practice_name':'new practice', 'user_id':self.user.id, \
					'organization_type': organization_type},
			{'parent_org_ids': self.practice.id, 'org_id': self.practice.id,\
					'practice_name':'new practice', 'user_id':self.user.id},
			{'parent_org_ids': self.practice.id, 'org_id': self.practice.id,\
					'practice_name':'new practice', 'user_id':self.user.id,\
					'organization_type':self.sub_types[9].id},
			{'org_id': self.practice.id}]
		response = self.client.post(reverse('MHLogin.MHLOrganization.views.org_save'),\
				data=data[0])
		self.assertEqual(response.status_code, 200)
		practice = PracticeLocation.objects.get(pk=organization_type)
		self.assertEqual(practice.practice_name,'test')
		org_rs = OrganizationRelationship.objects.filter(organization=\
						self.practice,parent=self.practice1)
		self.assertEqual(len(org_rs), 1)

		response = self.client.post(reverse('MHLogin.MHLOrganization.views.org_save'),\
				data=data[1])
		self.failIf(response.context['form'].is_valid())
		self.failUnless(isinstance(response.context['form'], OrganizationProfileSimpleForm))
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'MHLOrganization/Information/org_save.html')

		response = self.client.post(reverse('MHLogin.MHLOrganization.views.org_save'),\
				data=data[2])
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'MHLOrganization/Information/org_save.html')

		response = self.client.get(reverse('MHLogin.MHLOrganization.views.org_save'),\
				data=data[3])
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 1)


class OrgViewTest(MHLOrgTest):
	def test_org_view(self):
		practiceHours = PracticeHours()
		practiceHours.practice_location = self.practice
		practiceHours.day_of_week = 1
		practiceHours.open = datetime.time(9)
		practiceHours.close = datetime.time(18)
		practiceHours.lunch_start = datetime.time(12)
		practiceHours.lunch_duration = 60
		practiceHours.save()
		practiceHoursList = [practiceHours]
		self.practiceHoursList = practiceHoursList
		self.practiceHours = practiceHours
		response = self.client.get(reverse('MHLogin.MHLOrganization.views.org_view'),\
				data={'org_id': self.practice.id})
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'MHLOrganization/Information/org_view.html')


class OrgRemoveTest(MHLOrgTest):
	@mock.patch('MHLogin.Administration.views_org_type.thread.start_new_thread', autospec=True)
	def test_org_remove(self, start_thread):
		admin = create_user("admin", "aaa", "ddd", "demo", 
							"Ocean Avenue", "Carmel", "CA", "93921", uklass=Administrator)
		self.client.post('/login/', {'username': self.user.username, 'password': 'demo'})
		response = self.client.get(reverse('MHLogin.MHLOrganization.views.org_remove'),\
				data={'org_id': self.practice.id})
		self.assertEqual(response.status_code, 403)
		pra = PracticeLocation.objects.get(id=self.practice.id)
		self.assertFalse(pra.delete_flag)
		self.client.logout()

		self.client.post('/login/', {'username': admin.user.username, 'password': 'demo'})
		response = self.client.get(reverse('MHLogin.MHLOrganization.views.org_remove'),\
				data={'org_id': self.practice.id})
		self.assertEqual(response.status_code, 200)
		with self.assertRaises(PracticeLocation.DoesNotExist):\
						PracticeLocation.objects.get(id=self.practice.id)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 1)
		self.client.logout()


class OrgDragMoveTest(MHLOrgTest):
	@mock.patch('MHLogin.Administration.views_org_type.thread.start_new_thread', autospec=True)
	def test_drag_move(self, start_thread):
		re_org_rs_old = OrganizationRelationship.objects.filter(organization=\
						self.practice,parent=self.old_parent_practice)
		re_org_rs_new = OrganizationRelationship.objects.filter(organization=\
						self.practice,parent=self.new_parent_practice)
		self.assertEqual(len(re_org_rs_old), 1)
		self.assertEqual(len(re_org_rs_new), 0)
		response = self.client.post(reverse('MHLogin.MHLOrganization.views.org_drag_move'),\
				data={'org_id': self.practice.id,'org_parent_id':self.new_parent_practice.id})
		self.assertEqual(response.status_code, 200)
		org_rs_old = OrganizationRelationship.objects.filter(organization=\
						self.practice,parent=self.old_parent_practice)
		org_rs_new = OrganizationRelationship.objects.filter(organization=\
						self.practice,parent=self.new_parent_practice)
		self.assertEqual(len(org_rs_old), 0)
		self.assertEqual(len(org_rs_new), 1)
		msg = json.loads(response.content)
		self.assertEqual(msg['status'], 'OK')

		response = self.client.post(reverse('MHLogin.MHLOrganization.views.org_drag_move'),\
				data={'org_id': self.practice.id})
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 2)


class OrgMoveTest(MHLOrgTest):
	@mock.patch('MHLogin.Administration.views_org_type.thread.start_new_thread', autospec=True)
	def test_org_move_manager(self, start_thread):
		Office_Manager.objects.create(user=self.staff, 
			practice=self.old_parent_practice, manager_role=2)
		Office_Manager.objects.create(user=self.staff, 
			practice=self.new_parent_practice, manager_role=2)
		response = self.client.get(reverse('MHLogin.MHLOrganization.views.org_move'),\
				data={'org_id': self.practice.id})
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'MHLOrganization/Information/org_move.html')

		re_org_rs_old = OrganizationRelationship.objects.filter(organization=\
			self.practice, parent=self.old_parent_practice)
		re_org_rs_new = OrganizationRelationship.objects.filter(organization=\
			self.practice, parent=self.new_parent_practice)
		self.assertEqual(len(re_org_rs_old), 1)
		self.assertEqual(len(re_org_rs_new), 0)
		organization_type = self.sub_types[1].id
		response = self.client.post(reverse('MHLogin.MHLOrganization.views.org_move'), \
				data={'org_id': self.practice.id, 'parent_org_ids': self.new_parent_practice.id, \
				'organization_type':organization_type, 'user_id':self.user.id})
		self.assertEqual(response.status_code, 200)
		org_rs_old = OrganizationRelationship.objects.filter(organization=\
						self.practice,parent=self.old_parent_practice)
		org_rs_new = OrganizationRelationship.objects.filter(organization=\
						self.practice,parent=self.new_parent_practice)
		self.assertEqual(len(org_rs_new), 1)
		self.assertEqual(len(org_rs_old), 0)
		try:
			practice = PracticeLocation.objects.get(pk=self.practice.id)
			self.assertEqual(practice.practice_name, "test org")
		except:
			with self.assertRaises(PracticeLocation.DoesNotExist):\
					PracticeLocation.objects.get(pk=self.practice.id)
		msg = json.loads(response.content)
		self.assertEqual(msg["status"], "ok")

	def test_org_move_no_permission(self):
		response = self.client.get(reverse('MHLogin.MHLOrganization.views.org_move'),\
				data={'org_id': self.practice.id, 'parent_org_ids': self.new_parent_practice.id})
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'MHLOrganization/Information/org_no_permission.html')


class OrgEditTest(MHLOrgTest):
	def test_org_edit(self):
		data=[{'org_id': self.practice.id,'organization_type':self.new_parent_practice.id},
			{'org_id': self.practice.id,'organization_type':self.new_parent_practice.id,\
					'practice_name':'practiceName','time_zone':'America/Los_Angeles'},
			{'org_id': self.practice.id,'organization_type':self.new_parent_practice.id,\
					'practice_name':'practiceName'},
			{'org_id': self.practice.id,'practice_name':'practiceName'}]
		response = self.client.get(reverse('MHLogin.MHLOrganization.views.org_edit'),\
				data=data[0])
		self.failUnless(isinstance(response.context['pareorg_form'], OrgTypeForm))
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'MHLOrganization/Information/org_edit.html')
		for i in range(3):
			response = self.client.post(reverse('MHLogin.MHLOrganization.views.org_edit'),\
					data=data[i+1])
			self.assertEqual(response.status_code, 200)
			self.failUnless(isinstance(response.context['form'], PracticeProfileForm))
			self.assertTemplateUsed(response, 'MHLOrganization/Information/org_edit.html')


class MemberOrgViewTest(MHLOrgTest):
	def test_member_org_view(self):
		response = self.client.get(reverse('MHLogin.MHLOrganization.views.member_org_view'),\
				data={'org_id': self.practice.id})
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'MHLOrganization/MemberOrg/member_org_view.html')


class MemberOrgShowOrgTest(MHLOrgTest):
	def test_member_org_show_org(self):
		response = self.client.get(reverse('MHLogin.MHLOrganization.views.member_org_show_org'),\
				data={'org_id': self.practice.id,'organization_type':self.org_type})
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'MHLOrganization/MemberOrg/member_org_list.html')
		response = self.client.post(reverse('MHLogin.MHLOrganization.views.member_org_show_org'),\
				data={'org_id': self.practice.id,'organization_type':self.org_type})
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'MHLOrganization/MemberOrg/member_org_list.html')
		response = self.client.post(reverse('MHLogin.MHLOrganization.views.member_org_show_org'),\
				data={'org_id': self.practice.id,'organization_type':self.org_type,'search_input':'true'})
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'MHLOrganization/MemberOrg/member_org_list.html')


class MemberOrgShowInviteTest(MHLOrgTest):
	def test_member_org_show_invite(self):
		response = self.client.get(reverse('MHLogin.MHLOrganization.views.member_org_show_invite'),\
				data={'org_id': self.practice.id,'organization_type':self.org_type})
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'MHLOrganization/MemberOrg/member_org_invite_list.html')
		response = self.client.post(reverse('MHLogin.MHLOrganization.views.member_org_show_invite'),\
				data={'org_id': self.practice.id,'organization_type':self.org_type})
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'MHLOrganization/MemberOrg/member_org_invite_list.html')


class MemberOrgInviteIncomingTest(MHLOrgTest):
	def test_member_org_invite_incoming(self):
		response = self.client.get(reverse('MHLogin.MHLOrganization.views.member_org_invite_incoming'))
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 0)


class MemberOrgRemoveTest(MHLOrgTest):
	@mock.patch('MHLogin.Administration.views_org_type.thread.start_new_thread', autospec=True)
	def test_member_org_remove(self, start_thread):
		org_rs = OrganizationMemberOrgs()
		org_rs.from_practicelocation = self.practice
		org_rs.to_practicelocation = self.new_parent_practice
		org_rs.save()
		response = self.client.get(reverse('MHLogin.MHLOrganization.views.member_org_remove'),\
				data={'org_id': self.practice.id})
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 1)
		response = self.client.post(reverse('MHLogin.MHLOrganization.views.member_org_remove'),\
				data={'org_id': self.practice.id})
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 1)
		response = self.client.post(reverse('MHLogin.MHLOrganization.views.member_org_remove'),\
				data={'org_id': self.practice.id,'org_rs_id':org_rs.id})
		self.assertEqual(response.status_code, 200)
		with self.assertRaises(OrganizationMemberOrgs.DoesNotExist):
				OrganizationMemberOrgs.objects.get(pk=org_rs.id)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 1)


class MemberOrgInviteStep1Test(MHLOrgTest):
	def test_member_org_invite_step1(self):
		response = self.client.get(reverse('MHLogin.MHLOrganization.views.member_org_invite_step1'),\
				data={'org_id': self.practice.id})
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'MHLOrganization/MemberOrg/invite_step1.html')


class MemberOrgInviteStep2Test(MHLOrgTest):
	def test_member_org_invite_step2(self):
		response = self.client.get(reverse('MHLogin.MHLOrganization.views.member_org_invite_step2'),\
				data={'org_id': self.practice.id,'org_name':self.practice.practice_name})
		self.assertEqual(response.status_code, 200)
		self.assertEqual(0, len(response.context["org_list"]))
		self.assertTemplateUsed(response, 'MHLOrganization/MemberOrg/invite_step2.html')

		response = self.client.post(reverse('MHLogin.MHLOrganization.views.member_org_invite_step2'),\
				data={'org_id': self.practice.id,'org_name':self.practice.practice_name})
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'MHLOrganization/MemberOrg/invite_step2.html')


class MemberOrgInviteStep3Test(MHLOrgTest):
	def test_member_org_invite_step3(self):
		response = self.client.post(reverse('MHLogin.MHLOrganization.views.member_org_invite_step3'),\
				data={'org_id': self.practice.id,'sel_org_id':self.practice.id})
		self.assertEqual(response.status_code, 200)
		pending = Pending_Org_Association.objects.get(from_practicelocation=self.practice,\
					to_practicelocation=self.practice)
		self.assertEqual(pending.sender.first_name, 'lin')
		pending_log = Log_Org_Association.objects.get(
			association_id = pending.id,
			from_practicelocation = self.practice,
			to_practicelocation=self.practice,
			sender=self.user,
		)
		self.assertEqual(pending_log.sender.first_name, 'lin')
		self.assertTemplateUsed(response, 'MHLOrganization/MemberOrg/invite_step3.html')


class MemberOrgResendInvite(MHLOrgTest):
	def test_member_org_resend_invite(self):
		pending = Pending_Org_Association()
		pending.from_practicelocation = self.practice
		pending.to_practicelocation = self.new_parent_practice
		pending.sender = self.user
		pending.save()
		response = self.client.post(reverse('MHLogin.MHLOrganization.views.member_org_resend_invite',args=(pending.id,)),\
				data={'org_id': self.practice.id})
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 1)


class MemberOrgCancelInvite(MHLOrgTest):
	def test_member_org_cancel_invite(self):
		pending = Pending_Org_Association()
		pending.from_practicelocation = self.practice
		pending.to_practicelocation = self.new_parent_practice
		pending.sender = self.user
		pending.save()
		response = self.client.get(reverse('MHLogin.MHLOrganization.views.member_org_cancel_invite',args=(pending.id,)),\
				data={'org_id': self.practice.id})
		with self.assertRaises(Pending_Org_Association.DoesNotExist):\
				Pending_Org_Association.objects.get(from_practicelocation = self.practice)
		self.assertEqual(response.status_code, 302)


class MemberViewTest(MHLOrgTest):
	def test_member_view(self):
		response = self.client.get(reverse('MHLogin.MHLOrganization.views.member_view'),\
				data={'org_id': self.practice.id})
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'MHLOrganization/Member/member_view.html')


class MemberProviderCreateTest(TestCase):
	@classmethod
	def setUpClass(cls):
		clean_db_datas()
		cls.user = create_user('practicemgr1', 'lin', 'xing', 'demo')
		cls.provider = create_user("dholiday", "doc", "holiday", "demo", uklass=Provider)

		org_setting = OrganizationSetting(can_have_physician=True, can_have_nppa=True,
				can_have_medical_student=True)
		org_setting.save()
		cls.org_setting = org_setting
		org_type = OrganizationType(name="Test Org Type", 
				organization_setting=org_setting, is_public=True)
		org_type.save()
		cls.org_type = org_type

		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',
								organization_type=org_type,
								organization_setting=org_setting,)
		practice.save()
		practice1 = PracticeLocation(practice_name='test1',
								practice_longit='0.1',
								practice_lat='0.0',
								organization_type=org_type,
								organization_setting=org_setting,)
		practice1.save()

		OrganizationRelationship.objects.create(organization=practice,
			parent=practice1, create_time=int(time.time()), billing_flag=True)

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
		datadict = {
			'user_type':1,
			'org_id': cls.practice.id,
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

	def test_member_provider_create(self):
		response = self.client.post(reverse('MHLogin.MHLOrganization.views.member_provider_create'),\
				data=self.datadict)
		self.assertEqual(response.status_code, 200)
		self.failIf(response.context['user_form'].is_valid())
		self.failUnless(isinstance(response.context['user_form'], CreateProviderForm))
		self.assertTemplateUsed(response, 'MHLOrganization/Member/member_provider_create.html')

		response = self.client.get(reverse('MHLogin.MHLOrganization.views.member_provider_create'),\
				data={'org_id': self.practice.id})
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'MHLOrganization/Member/member_provider_create.html')

	def test_member_provider_create_NPPA(self):
		self.datadict['user_type'] = 2
		response = self.client.post(reverse('MHLogin.MHLOrganization.views.member_provider_create'),\
				data=self.datadict)
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'MHLOrganization/Member/member_provider_create.html')

	def test_member_provider_create_STUDENT(self):
		self.datadict['user_type'] = 10
		response = self.client.post(reverse('MHLogin.MHLOrganization.views.member_provider_create'),\
				data=self.datadict)
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'MHLOrganization/Member/member_provider_create.html')

	def test_member_provider_create_novalid(self):
		self.datadict['user_type'] = 0
		response = self.client.post(reverse('MHLogin.MHLOrganization.views.member_provider_create'),\
				data=self.datadict)
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'MHLOrganization/Member/member_provider_create.html')


class MemberStaffCreateTest(MHLOrgTest):
	def test_member_staff_create(self):
		del self.datadict['user_type']
		self.datadict['staff_type']=101
		response = self.client.post(reverse('MHLogin.MHLOrganization.views.member_staff_create'),\
				data=self.datadict)
		self.assertEqual(response.status_code, 200)
		self.failIf(response.context['user_form'].is_valid())
		self.failUnless(isinstance(response.context['staff_form'], CreateOfficeStaffForm))
		self.failIf(response.context['user_form'].is_valid())
		self.failUnless(isinstance(response.context['user_form'], CreateMHLUserForm))
		self.assertTemplateUsed(response, 'MHLOrganization/Member/member_staff_create.html')

	def test_member_staff_create_manager(self):
		self.datadict['staff_type']=100
		response = self.client.post(reverse('MHLogin.MHLOrganization.views.member_staff_create'),\
				data=self.datadict)
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'MHLOrganization/Member/member_staff_create.html')

	def test_member_staff_create_nurse(self):
		self.datadict['staff_type']=3
		response = self.client.post(reverse('MHLogin.MHLOrganization.views.member_staff_create'),\
				data=self.datadict)
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'MHLOrganization/Member/member_staff_create.html')

	def test_member_staff_create_dietician(self):
		self.datadict['staff_type']=4
		response = self.client.post(reverse('MHLogin.MHLOrganization.views.member_staff_create'),\
				data=self.datadict)
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'MHLOrganization/Member/member_staff_create.html')

	def test_member_staff_create_novalid(self):	
		self.datadict['staff_type']='0'
		response = self.client.post(reverse('MHLogin.MHLOrganization.views.member_staff_create'),\
				data=self.datadict)
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'MHLOrganization/Member/member_staff_create.html')


class InviteViewTest(MHLOrgTest):
	def test_invite_view(self):
		response = self.client.get(reverse('MHLogin.MHLOrganization.views.invite_view'),\
				data={'org_id': self.practice.id})
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'MHLOrganization/Invite/invite_view.html')


class InviteProviderTest(MHLOrgTest):
	def test_provider_view(self):
		response = self.client.get(reverse('MHLogin.MHLOrganization.views.invite_provider'),\
				data={'org_id': self.practice.id,'step':1})
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 1)

		response = self.client.post(reverse('MHLogin.MHLOrganization.views.invite_provider'),\
				data={'org_id': self.practice.id,'step':2,'index':1})
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 3)

		response = self.client.post(reverse('MHLogin.MHLOrganization.views.invite_provider'),\
				data={'org_id': self.practice.id,'step':3,'index':1})
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 2)

		response = self.client.post(reverse('MHLogin.MHLOrganization.views.invite_provider'),\
				data={'org_id': self.practice.id,'step':3,'step_type':'email',\
					'email':'ss@suzhoukada.com','type':1,'msg':'msg is here'})
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 1)


class InviteStaffTest(MHLOrgTest):
	def test_provider_view(self):
		response = self.client.get(reverse('MHLogin.MHLOrganization.views.invite_staff'),\
				data={'org_id': self.practice.id,'step':1})
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 2)

		response = self.client.post(reverse('MHLogin.MHLOrganization.views.invite_staff'),\
				data={'org_id': self.practice.id,'step':2})
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 2)


class InformationSubIvrViewTest(MHLOrgTest):
	def test_information_sub_ivr_view(self):
		data = [{'org_id': self.practice.id},
			{'org_id': self.practice.id,'newnumber':'true','delnumber':'true','number':1},
			{'org_id': self.practice.id,'newnumber':'true','delnumber':'true',\
				'remove':[1]
				},]
		response = self.client.get(reverse('MHLogin.MHLOrganization.views.information_sub_ivr_view'),\
				data=data[0])
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'MHLOrganization/InformationSub/information_sub_ivr_view.html')

		response = self.client.post(reverse('MHLogin.MHLOrganization.views.information_sub_ivr_view'),\
				data=data[1])
		acc_num = AccessNumber.objects.get(number=1)
		self.assertEqual(acc_num.practice.practice_name, 'test org')
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'MHLOrganization/InformationSub/information_sub_ivr_view.html')

		response = self.client.post(reverse('MHLogin.MHLOrganization.views.information_sub_ivr_view'),\
				data=data[2])
		self.assertEqual(response.status_code, 200)
		with self.assertRaises(AccessNumber.DoesNotExist):AccessNumber.objects.get(number=1)
		self.assertTemplateUsed(response, 'MHLOrganization/InformationSub/information_sub_ivr_view.html')

		response = self.client.post(reverse('MHLogin.MHLOrganization.views.information_sub_ivr_view'),\
				data=data[0])
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'MHLOrganization/InformationSub/information_sub_ivr_view.html')


class InformationSubPinChangeTest(TestCase):
	@classmethod
	def setUpClass(cls):
		clean_db_datas()
		cls.user = create_user('practicemgr1', 'lin', 'xing', 'demo')
		cls.user1 = create_user('practicemgr11', 'y', 'p', 'demo')

		cls.broker = create_user("broker1", "bro", "1", "demo", 
							"123 Main St.", "Phoenix", "AZ", uklass=Broker)

		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice.save()
		practice1 = PracticeLocation(practice_name='test1',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice1.save()

		OrganizationRelationship.objects.create(organization=practice,\
			parent=practice1, create_time=int(time.time()), billing_flag=True)

		cls.practice = practice
		staff = OfficeStaff()
		staff.user = cls.user
		staff.office_lat = 0.0
		staff.office_longit = 0.0
		staff.current_practice = practice
		staff.save()
		staff.practices.add(practice)

		cls.provider = Provider(user=cls.user1, office_lat=0.0, office_longit=0.0, current_practice = practice)
		cls.provider.mdcom_phone = '5948949899' 
		cls.provider.save()
#		
		mgr = Office_Manager(user=staff, practice=practice, manager_role=2)
		mgr.save()

	@classmethod
	def tearDownClass(cls):
		clean_db_datas()

	def setUp(self):
		pass

	def tearDown(self):
		pass

	def test_information_sub_pin_change(self):
		data=[{'org_id': self.practice.id,'password':'demo','pin1':12345,'pin2':12345},
			{'org_id': self.practice.id},
			{'org_id': self.practice.id,'password':'demo','pin1':12345,'pin2':12345}
			]
		self.client.post('/login/', {'username': self.user.username, 'password': 'demo'})
		staff_no_pin = OfficeStaff.objects.get(current_practice = self.practice)
		has_no_pin = True if  staff_no_pin.current_practice.pin else False
		self.assertEqual(has_no_pin, False, "The practice do not has pin.")
		response = self.client.post(reverse('MHLogin.MHLOrganization.views.information_sub_pin_change'),\
				data=data[0])
		staff_has_pin = OfficeStaff.objects.get(current_practice = self.practice)
		has_pin = True if staff_has_pin.current_practice.pin else False
		self.assertEqual(has_pin, True, "The practice do not has pin.")
		self.assertEqual(response.status_code, 302)
		self.client.logout()

		self.client.post('/login/', {'username': self.user.username, 'password': 'demo'})
		response = self.client.get(reverse('MHLogin.MHLOrganization.views.information_sub_pin_change'),\
				data=data[1])
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'MHLOrganization/InformationSub/information_sub_pin_change.html')
		self.client.logout()

		self.client.post('/login/', {'username': self.provider.user.username, 'password': 'demo'})
		response = self.client.post(reverse('MHLogin.MHLOrganization.views.information_sub_pin_change'),\
				data=data[2])
		self.assertEqual(response.status_code, 403)
		self.client.logout()


class InformationSubHourEditTest(MHLOrgTest):
	def test_information_sub_hour_edit(self):
		hoursdicts = [
				{'open': ['11:11']*7, 'close': ['1:1']*7, 'lunch_start':['0:12']*7, 'lunch_duration':[20]*7},
		]
		response = self.client.get(reverse('MHLogin.MHLOrganization.views.information_sub_hour_edit'),\
				data={'org_id': self.practice.id})
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'MHLOrganization/InformationSub/information_sub_hour_edit.html')
		for i in range(len(hoursdicts)):
			hoursdicts[i]['org_id'] = self.practice.id
			response = self.client.post(reverse('MHLogin.MHLOrganization.views.information_sub_hour_edit'),\
					data=hoursdicts[i])
			self.assertEqual(response.status_code, 302)


class InformationSubHolidayAddTest(MHLOrgTest):
	def test_information_sub_holiday_add(self):
		practiceHoliday = PracticeHolidays()
		practiceHoliday.practice_location = self.practice
		practiceHoliday.name = get_random_username()
		practiceHoliday.designated_day = datetime.date(2013,5,20)
		practiceHoliday.save()
		holiday_id = practiceHoliday.id
		response = self.client.get(reverse('MHLogin.MHLOrganization.views.information_sub_holiday_add',args=(holiday_id,)),\
				data={'org_id': self.practice.id})
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'MHLOrganization/InformationSub/information_sub_holiday_add.html')

		response = self.client.post(reverse('MHLogin.MHLOrganization.views.information_sub_holiday_add',args=(holiday_id,)),\
				data={'org_id': self.practice.id})
		self.assertEqual(response.status_code, 200)
		self.failUnless(isinstance(response.context['form'], HolidaysForm))
		self.assertTemplateUsed(response, 'MHLOrganization/InformationSub/information_sub_holiday_add.html')

		response = self.client.post(reverse('MHLogin.MHLOrganization.views.information_sub_holiday_add',args=(holiday_id,)),\
				data={'org_id': self.practice.id,'designated_day':practiceHoliday.designated_day})
		self.assertEqual(response.status_code, 302)


class MemberOrgAcceptInviteTest(MHLOrgTest):
	@mock.patch('MHLogin.Administration.views_org_type.thread.start_new_thread', autospec=True)
	def test_member_org_accept_invite(self, start_thread):
		pending = Pending_Org_Association()
		pending.from_practicelocation = self.practice
		pending.to_practicelocation = self.new_parent_practice
		pending.sender = self.user
		pending.save()
		response = self.client.get(reverse('MHLogin.MHLOrganization.views.member_org_accept_invite',args=(pending.id,)))
		self.assertEqual(response.status_code, 200)


class MemberOrgRejectedInviteTest(MHLOrgTest):
	def test_member_org_rejected_invite(self):
		pending = Pending_Org_Association()
		pending.from_practicelocation = self.practice
		pending.to_practicelocation = self.new_parent_practice
		pending.sender = self.user
		pending.save()
		response = self.client.get(reverse('MHLogin.MHLOrganization.views.member_org_rejected_invite',args=(pending.id,)))
		self.assertEqual(response.status_code, 200)


class InformationSubHolidayViewTest(MHLOrgTest):
	def test_information_sub_holiday_view(self):
		practiceHoliday = PracticeHolidays()
		practiceHoliday.practice_location = self.practice
		practiceHoliday.name = get_random_username()
		practiceHoliday.designated_day = datetime.date(2013,5,20)
		practiceHoliday.save()
		response = self.client.get(reverse('MHLogin.MHLOrganization.views.information_sub_holiday_view'), \
				data={'org_id': self.practice.id})
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'MHLOrganization/InformationSub/information_sub_holiday_view.html')

		ids = [1]
		response = self.client.post(reverse('MHLogin.MHLOrganization.views.information_sub_holiday_view'), \
				data={'org_id': self.practice.id,'remove':ids})
		with self.assertRaises(PracticeHolidays.DoesNotExist): \
				PracticeHolidays.objects.get(id__in=ids)
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'MHLOrganization/InformationSub/information_sub_holiday_view.html')
	