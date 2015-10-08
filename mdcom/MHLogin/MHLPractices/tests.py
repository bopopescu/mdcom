#-*- coding: utf-8 -*-
'''
Created on 2012-9-21

@author: mwang
'''

from MHLogin.MHLPractices.models import PracticeLocation
from MHLogin.MHLPractices.utils import changeCurrentPracticeForStaff
from MHLogin.MHLUsers.models import OfficeStaff, MHLUser
from MHLogin.utils.tests import create_user
from django.test import TestCase

class ChangeCurrentPracticeForStaffTest(TestCase):
	staff = None
	practice = None
	def setUp(self):
		self.staff = create_user("bblazejowsky", "bill", "blazejowsky", "demo", 
							"Ocean Avenue", "Carmel", "CA", "93921", uklass=OfficeStaff)
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

	def tearDown(self):
		OfficeStaff.objects.filter(id=self.staff.id).delete()
		MHLUser.objects.filter(id=self.staff.user.id).delete()
		PracticeLocation.objects.all().delete()

	def testChangeCurrentPracticeForStaff(self):
		with self.assertRaises(PracticeLocation.DoesNotExist):
			changeCurrentPracticeForStaff(None, self.staff.user.id)
		with self.assertRaises(MHLUser.DoesNotExist):
			changeCurrentPracticeForStaff(self.practice.id, None)
		with self.assertRaises(PracticeLocation.DoesNotExist):
			changeCurrentPracticeForStaff(self.practice.id+1, self.staff.user.id)

		changeCurrentPracticeForStaff(self.practice.id, self.staff.user.id)
		staff = OfficeStaff.objects.filter(id=self.staff.id)
		if staff:
			staff = staff[0]
			self.assertEqual(staff.current_practice.id, self.practice.id)

		mhluser = MHLUser.objects.filter(id=self.staff.user.id)
		if mhluser:
			mhluser = mhluser[0]
			practice = self.practice
			self.assertEqual(practice.practice_address1, mhluser.address1)
			self.assertEqual(practice.practice_address2, mhluser.address2)
			self.assertEqual(practice.practice_city, mhluser.city)
			self.assertEqual(practice.practice_state, mhluser.state)
			self.assertEqual(practice.practice_zip, mhluser.zip)
			self.assertEqual(practice.practice_lat, mhluser.lat)
			self.assertEqual(practice.practice_longit, mhluser.longit)
