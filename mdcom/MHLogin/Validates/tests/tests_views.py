'''
Created on 2013-6-6

@author: pyang
'''
import json

from django.core.urlresolvers import reverse
from django.test.testcases import TestCase

from MHLogin.utils.tests.tests import clean_db_datas
from MHLogin.api.v1.tests.utils import get_random_username, create_user
from MHLogin.MHLUsers.models import Provider
from MHLogin.Validates.tests.utils import ValidTest
class ValidationPageTest(TestCase):
	def setUp(self):
		clean_db_datas()
		self.user = create_user(get_random_username(), "yang", "peng", "demo")
		self.user.mobile_phone = 9563322588
		self.user.mobile_confirmed = True
		self.user.email_confirmed =True
		self.user.save()
		
		self.provider = Provider(user=self.user, office_lat=0.0, office_longit=0.0,pager='8001234567')
		self.provider.save()
	def tearDown(self):
		clean_db_datas()
		
	def testValidationPage(self):
		self.client.post('/login/', {'username': self.provider.user.username, 'password': 'demo'})
		response = self.client.post(reverse('MHLogin.Validates.views.validationPage'))
		self.assertEqual(response.status_code, 302)
		self.client.logout()
		
		self.client.post('/login/', {'username': self.provider.user.username, 'password': 'demo'})
		response = self.client.get(reverse('MHLogin.Validates.views.validationPage'))
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'Validates/validation.html')
		self.client.logout()
		
class ContactInfoTest(ValidTest):
	def testContactInfo(self):
		loginUser = [{'username':self.provider.user.username,'password': 'demo'},
					{'username': self.staff.user.username,'password': 'demo'},
					{'username': self.broker.user.username,'password': 'demo'}]
		self.client.post('/login/', loginUser[0])
		response = self.client.get(reverse('MHLogin.Validates.views.contactInfo'), \
				data={'mobile_phone':self.provider.mobile_phone})
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 1)
		self.client.logout()
		
		for i in range(2):
			self.client.post('/login/', loginUser[i+1])
			response = self.client.get(reverse('MHLogin.Validates.views.contactInfo'), \
					data={'pager':self.staff.pager})
			self.assertEqual(response.status_code, 200)
			msg = json.loads(response.content)
			self.assertEqual(len(msg), 1)
			self.client.logout()
			
class SendCodeTest(ValidTest):
	def testSendCode(self):
		self.client.post('/login/', {'username': self.provider.user.username, 'password': 'demo'})
		response = self.client.post(reverse('MHLogin.Validates.views.sendCode'),\
				data={'type':1,'recipient':'yangpeng'})
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 4)
		self.client.logout()
		
class ValidateTest(ValidTest):
	def testValidate(self):
		loginUser = [{'username':self.provider.user.username,'password': 'demo'},
					{'username': self.staff.user.username,'password': 'demo'},
					{'username': self.broker.user.username,'password': 'demo'}]
		for i in range(3):
			self.client.post('/login/', loginUser[i])
			response = self.client.post(reverse('MHLogin.Validates.views.validate'))
			self.assertEqual(response.status_code, 200)
			msg = json.loads(response.content)
			self.assertEqual(len(msg), 1)
			self.client.logout()