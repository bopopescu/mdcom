#-*- coding: utf-8 -*-
'''
Created on 2013-5-10

@author: pyang
'''
from django.test.testcases import TestCase
from MHLogin.utils.tests.tests import clean_db_datas
from MHLogin.api.v1.tests.utils import create_user
from MHLogin.MHLCallGroups.models import CallGroup
from MHLogin.MHLPractices.models import PracticeLocation
from django.core.urlresolvers import reverse
from MHLogin.MHLUsers.models import Provider

class AddPracticeToProviderTest(TestCase):
	@classmethod
	def setUpClass(cls):
		clean_db_datas()
		user = create_user('practicemgr1', 'lin', 'xing', 'demo', '', '', '', '',)
		cls.user =user
		call_group = CallGroup(description='test', team='team')
		call_group.save()
		cls.group = call_group

		practice = PracticeLocation(practice_name='Test Org',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice.save()
		cls.practice = practice
		provider = Provider()
		provider.user = cls.user
		provider.office_lat = 0.0
		provider.office_longit = 0.0
		provider.current_practice = practice
		provider.save()
		provider.practices.add(practice)
		cls.provider = provider
		
		practice.call_groups.add(call_group)
		cls.practice = practice


	@classmethod
	def tearDownClass(cls):
		clean_db_datas()

	def setUp(self):
		self.client.post('/login/', {'username': self.user.username, 'password': 'demo'})

	def tearDown(self):
		self.client.logout()

	def testAddPracticeToProvider(self):
		response = self.client.get(reverse('MHLogin.MHLUsers.views_ajax.addPracticeToProvider'))
		self.assertEqual(response.status_code, 302)
		self.assertEqual(len(self.provider.practices.all()), 1)
		
	def testAddPracticeToProviderNoPractice(self):
		response = self.client.get(reverse('MHLogin.MHLUsers.views_ajax.addPracticeToProvider'))
		self.assertEqual(response.status_code, 302)
		self.assertEqual(len(self.provider.practices.all()), 1)
		
		