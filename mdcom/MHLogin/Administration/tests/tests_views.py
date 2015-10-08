'''
Created on 2013-5-30

@author: pyang
'''
from django.test.testcases import TestCase
from django.core.urlresolvers import reverse
from MHLogin.MHLUsers.models import Administrator
from MHLogin.utils.tests.tests import create_user, clean_db_datas
from MHLogin.Administration.forms import GetAssignPracticeForm
from MHLogin.MHLPractices.models import PracticeLocation, OrganizationSetting,\
	OrganizationType


class GetAssignPracticeTest(TestCase):
	def setUp(self):
		clean_db_datas()
		org_setting = OrganizationSetting(can_have_physician=True)
		org_setting.save()
		self.org_setting = org_setting
		org_type = OrganizationType(name="Test Org Type", 
			organization_setting=org_setting, is_public=True)
		org_type.save()
		self.org_type = org_type

		practice = PracticeLocation(practice_name='test',
						practice_longit='0.1',
						practice_lat='0.0',
						organization_type=org_type,
						organization_setting=org_setting,)
		practice.save()
		self.practice = practice

		user = create_user('admin', 'Morris', 'Kelly', 'demo', uklass=Administrator)
		user.save()
		self.client.post('/login/', {'username': user.user.username, 'password': 'demo'})

	def tearDown(self):
		self.client.logout()

	def testGetAssignPractice(self):
		response = self.client.get(reverse('MHLogin.Administration.views.getAssignPractice'),\
			data={'userType': 1, 'assignPractice': self.practice})
		self.assertEqual(response.status_code, 200)
		self.failIf(response.context['form'].is_valid())
		self.failUnless(isinstance(response.context['form'], GetAssignPracticeForm))
		self.assertTemplateUsed(response, 'get_assign_practice.html')

		response = self.client.get(reverse('MHLogin.Administration.views.getAssignPractice'),\
						data={'userType': 2, 'assignPractice': self.practice})
		self.assertEqual(response.status_code, 200)
		self.failIf(response.context['form'].is_valid())
		self.failUnless(isinstance(response.context['form'], GetAssignPracticeForm))
		self.assertTemplateUsed(response, 'get_assign_practice.html')

		response = self.client.get(reverse('MHLogin.Administration.views.getAssignPractice'),\
			data={'userType': 10, 'assignPractice': self.practice})
		self.assertEqual(response.status_code, 200)
		self.failIf(response.context['form'].is_valid())
		self.failUnless(isinstance(response.context['form'], GetAssignPracticeForm))
		self.assertTemplateUsed(response, 'get_assign_practice.html')

		response = self.client.get(reverse('MHLogin.Administration.views.getAssignPractice'),\
			data={'userType': 100, 'assignPractice': self.practice})
		self.assertEqual(response.status_code, 200)
		self.failIf(response.context['form'].is_valid())
		self.failUnless(isinstance(response.context['form'], GetAssignPracticeForm))
		self.assertTemplateUsed(response, 'get_assign_practice.html')

		response = self.client.get(reverse('MHLogin.Administration.views.getAssignPractice'),\
			data={'userType': 101, 'assignPractice': self.practice})
		self.assertEqual(response.status_code, 200)
		self.failIf(response.context['form'].is_valid())
		self.failUnless(isinstance(response.context['form'], GetAssignPracticeForm))
		self.assertTemplateUsed(response, 'get_assign_practice.html')

		response = self.client.get(reverse('MHLogin.Administration.views.getAssignPractice'),\
			data={'userType': 300, 'assignPractice': self.practice})
		self.assertEqual(response.status_code, 200)
		self.failIf(response.context['form'].is_valid())
		self.failUnless(isinstance(response.context['form'], GetAssignPracticeForm))
		self.assertTemplateUsed(response, 'get_assign_practice.html')

		response = self.client.post(reverse('MHLogin.Administration.views.getAssignPractice'))
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'get_assign_practice.html')
