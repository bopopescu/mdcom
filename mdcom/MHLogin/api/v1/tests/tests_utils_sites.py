# -*- coding: utf-8 -*-
'''
Created on 2013-5-15

@author: pyang
'''
from django.test.testcases import TestCase
from MHLogin.api.v1.utils_sites import getSiteInfo,\
	getSiteProviders, getSiteStudents, getSiteStaff, getSiteList
from django.http import Http404
from MHLogin.MHLSites.models import Site
from django.forms.models import model_to_dict
from MHLogin.MHLUsers.utils import get_all_site_providers
from MHLogin.api.v1.utils_users import setSubProviderResultList
from MHLogin.api.v1.tests.utils import create_site

class UtilsSitesTest(TestCase):
	def testGetSiteInfo(self):
		site = create_site()
		self.assertEqual(model_to_dict(site, exclude=('lat', 'longit')), getSiteInfo(site.id))
		with self.assertRaises(Http404): getSiteInfo('')
		site_ids = Site.objects.filter().values_list('id', flat=True)
		not_exist_id = 1
		while not_exist_id in site_ids:
			not_exist_id += 1
		with self.assertRaises(Http404): getSiteInfo(not_exist_id)
	
	def testGetSiteProviders(self):
		site = create_site()
		rs = get_all_site_providers(site)
		data = {}
		data['users'] = setSubProviderResultList(rs)
		self.assertEqual(data, getSiteProviders(site.id))
		with self.assertRaises(Http404): getSiteProviders('')
		site_ids = Site.objects.filter().values_list('id', flat=True)
		not_exist_id = 1
		while not_exist_id in site_ids:
			not_exist_id += 1
		with self.assertRaises(Http404): getSiteProviders(not_exist_id)
	
	def testGetSiteStudents(self):
		site = create_site()
		rs = get_all_site_providers(site)
		data = {}
		data['users'] = setSubProviderResultList(rs)
		self.assertEqual(data, getSiteStudents(site.id))
		with self.assertRaises(Http404): getSiteStudents('')
		site_ids = Site.objects.filter().values_list('id', flat=True)
		not_exist_id = 1
		while not_exist_id in site_ids:
			not_exist_id += 1
		with self.assertRaises(Http404): getSiteStudents(not_exist_id)

	def testGetSiteStaff(self):
		site = create_site()
		rs = get_all_site_providers(site)
		data = {}
		data['users'] = setSubProviderResultList(rs)
		self.assertEqual(data, getSiteStaff(site.id))
		with self.assertRaises(Http404): getSiteStaff('')
		site_ids = Site.objects.filter().values_list('id', flat=True)
		not_exist_id = 1
		while not_exist_id in site_ids:
			not_exist_id += 1
		with self.assertRaises(Http404): getSiteStaff(not_exist_id)
		
	def testGetSiteList(self):

		site1 = Site(
				name = 'mysite site',
				address1='555 Pleasant Pioneer Grove',
				address2='Trailer Q615',
				city='Mountain View',
				state='CA',
				zip='94040-4104',
				lat=37.36876,
				longit=-122.081864,
				short_name = 'MSite'
			)
		site1.save()
		
		site2 = Site(
				name = 'doctorcom site',
				address1='555 Pleasant Pioneer Grove',
				address2='Trailer Q615 Bryant',
				city='Mountain View Palo',
				state='CA',
				zip='94040-4104',
				lat=37.36876,
				longit=-122.081864,
				short_name = 'MSite'
			)
		site2.save()
#	
		condition_dicts = [
					{'name':u'site','result':2,'result_failed':'name failed'},
					{'name':u'mysite','result':1,'result_failed':'name failed'},
					{'name':u'abc','result':0,'result_failed':'name failed'},
					{'address':u'Bryant','result':1,'result_failed':'address failed'},
					{'address':u'555 Pleasant Pioneer Grove','result':2,'result_failed':'address failed'},
					{'address':u'abc','result':0,'result_failed':'address failed'},
					{'city':u'Palo','result':1,'result_failed':'city failed'},
					{'city':u'Mountain View','result':2,'result_failed':'city failed'},
					{'city':u'abc','result':0,'result_failed':'city failed'},
					{'state':u'CA','result':2,'result_failed':'state failed1'},
					{'state':u'abc','result':0,'result_failed':'state failed3'},
					{'zip':'94040-4104','result':2,'result_failed':'zip failed1'},
					{'zip':u'22222','result':0,'result_failed':'zip failed2'},
					{'limit':0,'result':2, 'result_total':2, 'result_failed':'limit failed1'},
					{'limit':1,'result':1, 'result_total':2, 'result_failed':'limit failed2'},
					{'limit':2,'result':2, 'result_total':2, 'result_failed':'limit failed3'},
			]
		for dict in condition_dicts:
			result = getSiteList(dict)
			if 'result_total' not in dict:
				dict['result_total'] = dict['result']
			self.assertEqual(dict['result_total'], result['total_count'], dict['result_failed'])
		
	