'''
Created on 2013-5-13

@author: pyang
'''
from MHLogin.api.v1.tests.utils import APITest
from django.core.urlresolvers import reverse
from MHLogin.api.v1.errlib import err_GE002
from MHLogin.MHLPractices.models import PracticeLocation

class PracticeTest(APITest):
	def testPracticeSearch(self):
		response = self.client.post(reverse\
				('MHLogin.api.v1.views_practices.practiceSearch'), **self.extra)
		self.assertEqual(response.status_code, 200, response.status_code)

		response = self.client.get\
				(reverse('MHLogin.api.v1.views_practices.practiceSearch'), **self.extra)
		self.assertEqual(response.content, err_GE002().content, response.status_code)

	def testPracticeInfo(self):
		practice = PracticeLocation(practice_name = "pyang",practice_address1="Palo Alto",\
				practice_longit = 0.0,practice_lat = 0.0)
		practice.save()
		
		response = self.client.get\
				(reverse('MHLogin.api.v1.views_practices.practiceInfo',\
				args=(practice.id,)), **self.extra)
		self.assertEqual(response.status_code, 200, response.status_code)
		
	def testPracticeProviders(self):
		practice = PracticeLocation(practice_name = "pyang",practice_address1="Palo Alto",\
				practice_longit = 0.0,practice_lat = 0.0)
		practice.save()
		
		response = self.client.get\
				(reverse('MHLogin.api.v1.views_practices.practiceProviders',\
				args=(practice.id,)), **self.extra)
		self.assertEqual(response.status_code, 200, response.status_code)
		
	def testPracticeStaff(self):
		practice = PracticeLocation(practice_name = "pyang",practice_address1="Palo Alto",\
				practice_longit = 0.0,practice_lat = 0.0)
		practice.save()
		
		response = self.client.get\
				(reverse('MHLogin.api.v1.views_practices.practiceStaff',\
				args=(practice.id,)), **self.extra)
		self.assertEqual(response.status_code, 200, response.status_code)

class MyPracticeTest(APITest):
	def testMyPracticeProviders(self):
		practice = PracticeLocation(practice_name = "pyang",practice_address1="Palo Alto",\
				practice_longit = 0.0,practice_lat = 0.0)
		practice.save()
		data = {
			'id': practice.id
		}
		response = self.client.post(reverse\
				('MHLogin.api.v1.views_practices.myPracticeProviders'), data, **self.extra)
		self.assertEqual(response.status_code, 200, response.status_code)
		
	def testMyPracticeStaff(self):
		practice = PracticeLocation(practice_name = "pyang",practice_address1="Palo Alto",\
				practice_longit = 0.0,practice_lat = 0.0)
		practice.save()
		data = {
			'id': practice.id
		}
		response = self.client.post(reverse\
				('MHLogin.api.v1.views_practices.myPracticeStaff'), data, **self.extra)
		self.assertEqual(response.status_code, 200, response.status_code)
		
	def testLocalOffice(self):
		practice = PracticeLocation(practice_name = "pyang",practice_address1="Palo Alto",\
				practice_longit = 0.0,practice_lat = 0.0)
		practice.save()
		data = {
			'id': practice.id
		}
		response = self.client.post(reverse\
				('MHLogin.api.v1.views_practices.localOffice'), data, **self.extra)
		self.assertEqual(response.status_code, 200, response.status_code)
		