'''
Created on 2013-5-16

@author: pyang
'''
from django.test.testcases import TestCase
# -*- coding: utf-8 -*-
from MHLogin.api.v1.tests.utils import create_user, get_random_username,\
	create_practice
from MHLogin.MHLUsers.models import Provider, Physician, NP_PA
from MHLogin.MHLSites.models import Site
from MHLogin.MHLPractices.models import PracticeLocation
from MHLogin.api.v1.utils_practices import getPracticeList, setPracticeResult,\
	getPracticeInfo, getPracticeProviders, getPracticeStaff
from django.http import Http404
from MHLogin.api.v1.utils_users import setSubProviderResultList
from MHLogin.MHLUsers.utils import get_all_practice_providers,\
	get_all_practice_staff
class UtilsPracticeTest(TestCase):
	def testGetPracticeList(self):
		practice1 = PracticeLocation(
			practice_name='USA practice',
			practice_address1='555 Pleasant Pioneer Grove',
			practice_address2='Trailer Q615 beijing',
			practice_city='Mountain View suzhou',
			practice_state='CA',
			practice_zip='94040-4104',
			practice_lat=37.36876,
			practice_longit=-122.081864)
		practice1.save()
		
		practice2 = PracticeLocation(
			practice_name='China practice',
			practice_address1='jiangsu',
			practice_address2='beijing',
			practice_city='suzhou',
			practice_state='JS',
			practice_zip='94040-4104',
			practice_lat=37.36876,
			practice_longit=-122.081864)
		practice2.save()

		condition_dicts = [
					{'practice_name':u'practice','result':2,'result_failed':'name failed'},
					{'practice_name':u'USA','result':1,'result_failed':'name failed'},
					{'practice_name':u'abc','result':0,'result_failed':'name failed'},
					{'practice_address':u'jiangsu','result':1,'result_failed':'address failed'},
					{'practice_address':u'beijing','result':2,'result_failed':'address failed'},
					{'practice_address':u'abc','result':0,'result_failed':'address failed'},
					{'practice_city':u'Mountain','result':1,'result_failed':'city failed1'},
					{'practice_city':u'suzhou','result':2,'result_failed':'city failed2'},
					{'practice_city':u'abc','result':0,'result_failed':'city failed3'},
					{'practice_state':u'CA','result':1,'result_failed':'state failed'},
					{'practice_state':u'JS','result':1,'result_failed':'state failed'},
					{'practice_state':u'abc','result':0,'result_failed':'state failed'},
					{'practice_zip':'94040-4104','result':2,'result_failed':'zip failed'},
					{'practice_zip':u'22222','result':0,'result_failed':'zip failed'},
					{'limit':0,'result':2, 'result_total':2, 'result_failed':'limit failed'},
					{'limit':1,'result':1, 'result_total':2, 'result_failed':'limit failed'},
					{'limit':2,'result':2, 'result_total':2, 'result_failed':'limit failed'},
					{
						'practice_name':u'practice','address':u'suzhou china','city':u'suzhou','state':u'AB',
						'limit':2,'result':2, 'result_total':2, 'result_failed':'all failed1'
					},
					{
						'practice_name':u'abc','address':u'suzhou china','city':u'suzhou','state':u'AB',
						'limit':1,'result':0, 'result_total':0, 'result_failed':'all failed2'
					},
			]
		for dict in condition_dicts:
			result = getPracticeList(dict)
			if 'result_total' not in dict:
				dict['result_total'] = dict['result']
			self.assertEqual(dict['result_total'], result['total_count'], dict['result_failed'])
			self.assertEqual(dict['result'], len(result['results']), dict['result_failed'])

	def testGetPracticeInfo(self):
		practice = create_practice()
		data = setPracticeResult(practice, "Middle")
		self.assertEqual(data, getPracticeInfo(practice.id))
		with self.assertRaises(Http404): getPracticeInfo('')
		practice_ids = PracticeLocation.objects.filter().values_list('id', flat=True)
		not_exist_id = 1
		while not_exist_id in practice_ids:
			not_exist_id += 1
		with self.assertRaises(Http404): getPracticeInfo(not_exist_id)
		
	def testGetPracticeProviders(self):
		practice = create_practice()
		rs = get_all_practice_providers(practice, False)
		data = {}
		data['users'] = setSubProviderResultList(rs)
		self.assertEqual(data, getPracticeProviders(practice.id))
		with self.assertRaises(Http404): getPracticeProviders('')
		practice_ids = PracticeLocation.objects.filter().values_list('id', flat=True)
		not_exist_id = 1
		while not_exist_id in practice_ids:
			not_exist_id += 1
		with self.assertRaises(Http404): getPracticeProviders(not_exist_id)
		
	def testGetPracticeStaff(self):
		practice = create_practice()
		rs = get_all_practice_staff(practice)
		data = {}
		data['users'] = setSubProviderResultList(rs)
		self.assertEqual(data, getPracticeStaff(practice.id))
		with self.assertRaises(Http404): getPracticeStaff('')
		practice_ids = PracticeLocation.objects.filter().values_list('id', flat=True)
		not_exist_id = 1
		while not_exist_id in practice_ids:
			not_exist_id += 1
		with self.assertRaises(Http404): getPracticeStaff(not_exist_id)
	
	def testSetPracticeResult(self):
		practice = create_practice()
		logo_size = 'Small'
		
		self.assertEqual(setPracticeResult(practice, logo_size), getPracticeInfo(practice.id))
		self.assertEqual(setPracticeResult(practice, ""), getPracticeInfo(practice.id))
		self.assertEqual(setPracticeResult(practice, 11), getPracticeInfo(practice.id))
		self.assertEqual(setPracticeResult(practice, None), getPracticeInfo(practice.id))
		