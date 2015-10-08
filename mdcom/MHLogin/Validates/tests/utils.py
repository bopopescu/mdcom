'''
Created on 2013-6-7

@author: pyang
'''

import random
import string
from django.conf import settings
from django.test.testcases import TestCase

from MHLogin.utils.tests.tests import clean_db_datas
from MHLogin.api.v1.tests.utils import create_user, get_random_username
from MHLogin.MHLOrganization.tests.utils import create_organization
from MHLogin.MHLUsers.models import OfficeStaff, Broker, Provider

class ValidTest(TestCase):
	def setUp(self):
		clean_db_datas()
		self.temp_CALL_ENABLE = settings.CALL_ENABLE
		self.temp_SEND_MAXIMUM_PER_DAY = settings.SEND_MAXIMUM_PER_DAY
		self.temp_SEND_CODE_WAITING_TIME = settings.SEND_CODE_WAITING_TIME
		self.temp_FAIL_VALIDATE_MAXIMUM_PER_HOUR = settings.FAIL_VALIDATE_MAXIMUM_PER_HOUR
		self.temp_VALIDATE_LOCK_TIMEE = settings.VALIDATE_LOCK_TIME

		settings.SEND_MAXIMUM_PER_DAY = 5
		settings.SEND_CODE_WAITING_TIME = 2
		settings.FAIL_VALIDATE_MAXIMUM_PER_HOUR = 3
		settings.VALIDATE_LOCK_TIME = 2

		self.provider = create_user(get_random_username(), "yang", "peng", "demo",uklass=Provider)
		self.provider.mobile_phone = '9563322588'
		self.provider.mobile_confirmed = True
		self.provider.email = 'dasdasdasd@sdasd.com'
		self.provider.email_confirmed =True
		self.provider.save()
		
		self.organization = create_organization()
		self.user = create_user(get_random_username(), "yang", "peng", "demo")
		staff = OfficeStaff()
		staff.user = self.user
		staff.pager = '9985622456'
		staff.office_lat = 0.0
		staff.office_longit = 0.0
		staff.current_practice = self.organization
		staff.save()
		self.staff = staff
		
		self.user_bro = create_user(get_random_username(), "yang", "peng", "demo")
		self.broker = Broker()
		self.broker.pager = '9985622456'
		self.broker.user = self.user_bro
		self.broker.office_lat = 0.0
		self.broker.office_longit = 0.0
		self.broker.save()
		
		self.user = create_user(get_random_username(), "yang", "peng", "demo")
		self.user.mobile_phone = '9563322488'
		self.user.mobile_confirmed = True
		self.user.email_confirmed =True
		self.user.save()
	def tearDown(self):
		clean_db_datas()
		settings.CALL_ENABLE = self.temp_CALL_ENABLE
		settings.SEND_MAXIMUM_PER_DAY = self.temp_SEND_MAXIMUM_PER_DAY
		settings.SEND_CODE_WAITING_TIME = self.temp_SEND_CODE_WAITING_TIME
		settings.FAIL_VALIDATE_MAXIMUM_PER_HOUR = self.temp_FAIL_VALIDATE_MAXIMUM_PER_HOUR
		settings.VALIDATE_LOCK_TIME = self.temp_VALIDATE_LOCK_TIMEE

	@classmethod
	def setUpClass(cls):
		clean_db_datas()
		
	@classmethod
	def tearDownClass(cls):
		clean_db_datas()
	
def randomCode():
	char_set = string.ascii_uppercase + \
							string.ascii_lowercase + string.digits
	salt = ''.join(random.sample(char_set, 4))
	return salt
