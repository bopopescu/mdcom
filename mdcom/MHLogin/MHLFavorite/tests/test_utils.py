#-*- coding: utf-8 -*-

'''
Created on 2013-5-28

@author: wxin
'''
from django.utils.unittest.case import TestCase

from MHLogin.MHLOrganization.tests.utils import create_multiple_organizations
from MHLogin.utils.tests.tests import clean_db_datas, create_user
from MHLogin.MHLUsers.models import OfficeStaff
from MHLogin.MHLFavorite.utils import do_toggle_favorite, get_my_favorite,\
	get_my_favorite_ids, OBJECT_TYPE_FLAG_MHLUSER, OBJECT_TYPE_FLAG_ORG

class GetMyFavorite(TestCase):
	
	@classmethod
	def setUpClass(cls):
		clean_db_datas()

		cls.owner = create_user('TestProvider', "Li", 'Wen', 'demo')
		staffs = []
		for i in range(10):
			user_name = "".join(["Staff1_", str(i)])
			first_name = "".join(["Test1_", str(i)])
			user = create_user(user_name, first_name, 'S', 'demo', uklass=OfficeStaff)
			staffs.append(user)
		cls.staffs = staffs
		cls.organizations = create_multiple_organizations()

	def test_get_my_favorite(self):

		for ele in self.staffs:
			do_toggle_favorite(self.owner, 1, ele.user.id)
			# repeat add same object, 
			# the function 'do_toggle_favorite' shouldn't raise error  
			do_toggle_favorite(self.owner, 1, ele.user.id)
		for ele in self.organizations:
			do_toggle_favorite(self.owner, 2, ele.id)
		favs = get_my_favorite(self.owner, object_type_flag=OBJECT_TYPE_FLAG_MHLUSER)
		self.assertEqual(len(self.staffs), len(favs))
		favs = get_my_favorite(self.owner, object_type_flag=OBJECT_TYPE_FLAG_ORG)
		self.assertEqual(len(self.organizations), len(favs))
		favs = get_my_favorite(self.owner)
		self.assertEqual(len(self.staffs)+len(self.organizations), len(favs))

		for ele in self.staffs:
			do_toggle_favorite(self.owner, 1, ele.user.id, is_favorite=False)
		for ele in self.organizations:
			do_toggle_favorite(self.owner, 2, ele.id, is_favorite=False)
		favs = get_my_favorite(self.owner)
		self.assertEqual(0, len(favs))


	@classmethod
	def tearDownClass(cls):
		clean_db_datas()

class GetMyFavoriteIds(TestCase):
	
	@classmethod
	def setUpClass(cls):
		clean_db_datas()

		cls.owner = create_user('TestProvider', "Li", 'Wen', 'demo')
		staffs = []
		for i in range(10):
			user_name = "".join(["Staff1_", str(i)])
			first_name = "".join(["Test1_", str(i)])
			user = create_user(user_name, first_name, 'S', 'demo', uklass=OfficeStaff)
			staffs.append(user)
		cls.staffs = staffs
		cls.organizations = create_multiple_organizations()

	def test_get_my_favorite_ids(self):

		for ele in self.staffs:
			do_toggle_favorite(self.owner, 1, ele.user.id)
			# repeat add same object, 
			# the function 'do_toggle_favorite' shouldn't raise error  
			do_toggle_favorite(self.owner, 1, ele.user.id)
		for ele in self.organizations:
			do_toggle_favorite(self.owner, 2, ele.id)

		favs = get_my_favorite_ids(self.owner, object_type_flag=OBJECT_TYPE_FLAG_MHLUSER)
		self.assertEqual(len(self.staffs), len(favs))
		favs = get_my_favorite_ids(self.owner, object_type_flag=OBJECT_TYPE_FLAG_ORG)
		self.assertEqual(len(self.organizations), len(favs))
		favs = get_my_favorite_ids(self.owner)
		self.assertEqual(len(self.staffs)+len(self.organizations), len(favs))


		for ele in self.staffs:
			do_toggle_favorite(self.owner, 1, ele.user.id, is_favorite=False)
		for ele in self.organizations:
			do_toggle_favorite(self.owner, 2, ele.id, is_favorite=False)
		favs = get_my_favorite_ids(self.owner)
		self.assertEqual(0, len(favs))


	@classmethod
	def tearDownClass(cls):
		clean_db_datas()