import json

from django.core.urlresolvers import reverse
from django.test.testcases import TestCase

from MHLogin.MHLCallGroups.models import CallGroup, CallGroupMember
from MHLogin.MHLPractices.models import PracticeLocation
from MHLogin.MHLUsers.models import OfficeStaff, Office_Manager, Provider
from MHLogin.utils.tests import create_user
from MHLogin.utils.tests.tests import clean_db_datas


#add by xlin 121224 to test getMembers
class MCGetMembersTest(TestCase):
	@classmethod
	def setUpClass(cls):
		clean_db_datas()

		cls.user = create_user('practicemgr5', 'lin', 'xing', 'demo', '', '', '', '',)

		call_group = CallGroup(description='test', team='team')
		call_group.save()
		cls.call_group = call_group

		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice.save()
		practice.call_groups.add(call_group)
		cls.practice = practice

	def setUp(self):
		self.client.post('/login/', {'username': self.user.username, 'password': 'demo'})

	@classmethod
	def tearDownClass(cls):
		clean_db_datas()

	def test_getMembers(self):
		staff = OfficeStaff(user=self.user)
		staff.save()
		staff.practices.add(self.practice)
		staff.current_practice = self.practice
		staff.save()
		manager = Office_Manager(user=staff, practice=self.practice, manager_role=1)
		manager.save()

		#0 member found
		response = self.client.post(reverse('MHLogin.MHLCallGroups.views_multicallgroup.getMembers', 
			args=(self.practice.id, self.call_group.id,)))
		self.assertEqual(response.status_code, 200)

		#1 member found
		provider = Provider(username='provider', first_name='tes', last_name="meister", 
			email='aa@ada.com', office_lat=0.0, office_longit=0.0)
		provider.save()
		member = CallGroupMember(call_group=self.call_group, member=provider, alt_provider=1)
		member.save()
		response = self.client.post(reverse('MHLogin.MHLCallGroups.views_multicallgroup.getMembers', 
			args=(self.practice.id, self.call_group.id,)))
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 1)
		self.assertEqual(msg[0][0], provider.id)

		#403
		call_group2 = CallGroup(description='test2', team='team')
		call_group2.save()

		response = self.client.post(reverse('MHLogin.MHLCallGroups.views_multicallgroup.getMembers', 
			args=(self.practice.id, call_group2.id,)))
		self.assertEqual(response.status_code, 403)
