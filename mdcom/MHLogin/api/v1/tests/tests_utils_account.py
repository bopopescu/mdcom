'''
Created on 2013-6-13

@author: pyang
'''
from django.test.testcases import TestCase
from MHLogin.MHLUsers.models import OfficeStaff, Broker, Nurse
from MHLogin.api.v1.tests.utils import create_user
from MHLogin.api.v1.utils_account import officeStaffProfileView,\
	brokerProfileView

class OfficeStaffProfileViewTest(TestCase):
	def testOfficeStaffProfileView(self):
		user = create_user('practicemgr1', 'lin', 'xing', 'demo')
		staff = OfficeStaff()
		staff.user = user
		staff.office_lat = 0.0
		staff.office_longit = 0.0
		staff.save()
		self.assertEqual(officeStaffProfileView(staff)['photo'],'/media/images/photos/staff_icon.jpg')
		nurse = Nurse(user = staff)
		nurse.save()
		self.assertEqual(officeStaffProfileView(nurse.user)['photo'],'/media/images/photos/nurse.jpg')
		
class BrokerProfileViewTest(TestCase):
	def testBrokerProfileView(self):
		user = create_user('practicemgr1', 'lin', 'xing', 'demo')
		broker = Broker()
		broker.user = user
		broker.office_lat = 0.0
		broker.office_longit = 0.0
		broker.save()
		self.assertEqual(brokerProfileView(broker)['username'],user.username)
