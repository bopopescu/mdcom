# -*- coding: utf-8 -*-
'''
Created on 2013-5-8

@author: pyang
'''
from MHLogin.api.v1.tests.utils import APITest
from django.core.urlresolvers import reverse
from MHLogin.api.v1.errlib import err_GE002
from MHLogin.MHLSites.models import Site


class SiteTest(APITest):
	def testSiteSearch(self):
		response = self.client.post(reverse(
			'MHLogin.api.v1.views_sites.siteSearch'), **self.extra)
		self.assertEqual(response.status_code, 200, response.status_code)

		response = self.client.get(reverse(
			'MHLogin.api.v1.views_sites.siteSearch'), **self.extra)
		self.assertEqual(response.content, err_GE002().content, response.status_code)

	def testSiteInfo(self):
		site = Site(name="pyang", address1="Palo Alto", lat="0.0", longit="0.0")
		site.save()

		response = self.client.post(reverse\
				('MHLogin.api.v1.views_sites.siteInfo', \
				args=(site.id,)), **self.extra)
		self.assertEqual(response.status_code, 200, response.status_code)

	def testSiteProviders(self):
		site = Site(name="pyang", address1="Palo Alto",lat="0.0",longit="0.0")
		site.save()
		
		response = self.client.post(reverse\
				('MHLogin.api.v1.views_sites.siteProviders', \
				args=(site.id,)), **self.extra)
		self.assertEqual(response.status_code, 200, response.status_code)
	
	def testSiteStaff(self):
		site = Site(name="pyang", address1="Palo Alto",lat="0.0",longit="0.0")
		site.save()
		
		response = self.client.post(reverse\
				('MHLogin.api.v1.views_sites.siteStaff', \
				args=(site.id,)), **self.extra)
		self.assertEqual(response.status_code, 200, response.status_code)

class MysiteTest(APITest):
	def testMySiteProviders(self):
		site = Site(name="pyang", address1="Palo Alto",lat="0.0",longit="0.0")
		site.save()
		
		data = {
			'id': site.id
		}
		response = self.client.post(reverse\
				('MHLogin.api.v1.views_sites.mySiteProviders'), data, **self.extra)
		self.assertEqual(response.status_code, 200, response.status_code)
		
	def testMySiteMedStudents(self):
		site = Site(name="pyang", address1="Palo Alto",lat="0.0",longit="0.0")
		site.save()
		data = {
			'id': site.id
		}
		response = self.client.post(reverse\
				('MHLogin.api.v1.views_sites.mySiteMedStudents'), data, **self.extra)
		self.assertEqual(response.status_code, 200, response.status_code)
		
	def testMySiteStaff(self):
		site = Site(name="pyang", address1="Palo Alto",lat="0.0",longit="0.0")
		site.save()
		data = {
			'id': site.id
		}
		response = self.client.post(reverse\
				('MHLogin.api.v1.views_sites.mySiteStaff'), data, **self.extra)
		self.assertEqual(response.status_code, 200, response.status_code)
		