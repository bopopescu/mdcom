#-*- coding: utf-8 -*-

'''
Created on 2013-6-8

@author: wxin
'''
from django.utils.unittest.case import TestCase

from MHLogin.MHLOrganization.tests.utils import create_multiple_organizations
from MHLogin.utils.tests.tests import clean_db_datas, create_user
from MHLogin.MHLUsers.models import OfficeStaff
from MHLogin.MHLFavorite.utils import do_toggle_favorite
from MHLogin.MHLFavorite.models import Favorite

class FavoriteTest(TestCase):
	
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

		for ele in cls.staffs:
			do_toggle_favorite(cls.owner, 1, ele.user.id)
			# repeat add same object, 
			# the function 'do_toggle_favorite' shouldn't raise error  
			do_toggle_favorite(cls.owner, 1, ele.user.id)
		for ele in cls.organizations:
			do_toggle_favorite(cls.owner, 2, ele.id)

	def test_favorite_to_str(self):
		favs = Favorite.objects.filter(owner=self.owner)
		for fav in favs:
			expect_str = "%s %s : %s - %d" % (fav.owner.first_name, fav.owner.last_name, 
					fav.object_type.model, fav.object_id)
			self.assertEqual(expect_str, str(fav))

