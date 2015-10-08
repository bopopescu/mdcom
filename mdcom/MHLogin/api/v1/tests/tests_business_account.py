'''
Created on 2013-6-27

@author: pyang
'''
from django.test.testcases import TestCase
from MHLogin.api.v1.business_account import officeStaffProfileLogic,\
	brokerEditProfileLogic
from MHLogin.apps.smartphone.v1.tests.utils import generateHttpRequest

class TestOfficeStaffProfileLogic(TestCase):
	def testOfficeStaffProfileLogic(self):
		request = generateHttpRequest()
		request.method = "get"
		self.assertEqual(officeStaffProfileLogic(request).status_code,200)
		request.method = "POST"
		self.assertEqual(officeStaffProfileLogic(request).status_code,400)
		request.POST = {'first_name':'yang',
					'email':'asdasd@asdafasdf.com',
					'last_name':'peng',
					'gender':'M',
					'email_confirmed':True
					}
		self.assertEqual(officeStaffProfileLogic(request).status_code,200)

class TestBrokerEditProfileLogic(TestCase):
	def testBrokerEditProfileLogic(self):
		request = generateHttpRequest()
		request.method = "get"
		self.assertEqual(brokerEditProfileLogic(request).status_code,400)
		request.method = "POST"
		request.POST = {'first_name':'yang',
					'email':'asdasd@asdafasdf.com',
					'last_name':'peng',
					'gender':'M',
					'email_confirmed':True
					}
		self.assertEqual(brokerEditProfileLogic(request).status_code,200)

