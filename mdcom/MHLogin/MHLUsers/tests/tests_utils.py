#-*- coding: utf-8 -*-
'''
Created on 2012-9-24

@author: mwang
'''
from MHLogin.MHLPractices.models import PracticeLocation
from MHLogin.MHLUsers.models import OfficeStaff, Provider, Broker, MHLUser
from MHLogin.MHLUsers.utils import update_staff_address_info_by_practice
from MHLogin.utils.tests import create_user
from django.test import TestCase

class UpdateStaffAddressInfoByPracticeTest(TestCase):
	practice = None
	user_datas = []
	def setUp(self):
		PracticeLocation.objects.all().delete()
		self.practice = PracticeLocation(
			practice_address1='555 Pleasant Pioneer Grove',
			practice_address2='Trailer Q615',
			practice_city='Mountain View',
			practice_state='CA',
			practice_zip='94040-4104',
			practice_lat=37.36876,
			practice_longit=-122.081864)
		self.practice.save()

		self.user_datas = [
				{"username":"bblazejowsky", "first_name":"bill", "last_name":"blazejowsky", "password":"demo", 
					"addr":"Ocean Avenue","addr2":"Ocean Avenue", "city":"Carmel", "state":"CA", "zipcode":"93921", "uklass":OfficeStaff},
				{"username":"bblazejowsky1", "first_name":"bill1", "last_name":"blazejowsky1", "password":"demo", 
					"addr":"Ocean Avenue","addr2":"Ocean Avenue", "city":"Carmel", "state":"CA", "zipcode":"93921", "uklass":Provider},
				{"username":"bblazejowsky2", "first_name":"bill2", "last_name":"blazejowsky2", "password":"demo", 
					"addr":"Ocean Avenue","addr2":"Ocean Avenue", "city":"Carmel", "state":"CA", "zipcode":"93921", "uklass":Broker},
			]

		for user in self.user_datas:
			persistent_user = create_user(user['username'], user['first_name'], user['last_name'], user['password'], 
							user['addr'], user['city'], user['state'], user['zipcode'], uklass=user['uklass'])
			persistent_user.current_practice = self.practice
			persistent_user.save()

			user['id'] = persistent_user.user.id
			user['lat'] = persistent_user.user.lat
			user['longit'] = persistent_user.user.longit

	def tearDown(self):
		user_ids = [user['id'] for user in self.user_datas]
		OfficeStaff.objects.filter(user__id__in=user_ids).delete()
		Broker.objects.filter(user__id__in=user_ids).delete()
		Provider.objects.filter(user__id__in=user_ids).delete()
		MHLUser.objects.filter(id__in=user_ids).delete()
		PracticeLocation.objects.all().delete()

	def testUpdateStaffAddressInfoByPractice(self):
		practice = self.practice
		update_staff_address_info_by_practice(practice)
		for user in self.user_datas:
			mhluser = MHLUser.objects.filter(id=user['id'])
			if mhluser:
				mhluser = mhluser[0]
				if user['uklass'] != OfficeStaff:
					self.assertEqual(user['addr'], mhluser.address1)
					self.assertEqual(user['city'], mhluser.city)
					self.assertEqual(user['state'], mhluser.state)
					self.assertEqual(user['zipcode'], mhluser.zip)
					self.assertEqual(user['lat'], mhluser.lat)
					self.assertEqual(user['longit'], mhluser.longit)
				else:
					self.assertEqual(practice.practice_address1, mhluser.address1)
					self.assertEqual(practice.practice_address2, mhluser.address2)
					self.assertEqual(practice.practice_city, mhluser.city)
					self.assertEqual(practice.practice_state, mhluser.state)
					self.assertEqual(practice.practice_zip, mhluser.zip)
					self.assertEqual(practice.practice_lat, mhluser.lat)
					self.assertEqual(practice.practice_longit, mhluser.longit)

