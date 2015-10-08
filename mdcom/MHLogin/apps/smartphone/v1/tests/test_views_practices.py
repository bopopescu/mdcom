import json

from django.test import TestCase

from MHLogin.MHLUsers.models import OfficeStaff, Office_Manager
from MHLogin.apps.smartphone.models import SmartPhoneAssn
from MHLogin.apps.smartphone.v1.tests.utils import generateHttpRequest,\
	create_org_type, ct_practice
from MHLogin.apps.smartphone.v1.views_practices import local_office, \
	practice_info
from MHLogin.utils.tests.tests import clean_db_datas


#add by xlin in 130109 to test local_office
class LocalOfficeTest(TestCase):
	def setUp(self):
		clean_db_datas()

	def test_local_office(self):
		request = generateHttpRequest()

		#a provider call this method
		result = local_office(request)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		
		self.assertEqual(len(msg['data']['practices']), 0)

		#a office manager login but has not current practice
		organization_type = create_org_type()
		practice = ct_practice('name', organization_type)
		staff = OfficeStaff(user=request.user)
		staff.save()
		manager = Office_Manager(user=staff, practice=practice, manager_role=2)
		manager.save()

		assn = SmartPhoneAssn.all_objects.get(device_id=request.REQUEST['DCOM_DEVICE_ID'])
		assn.user_type = 100
		assn.save(request)

		result = local_office(request)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		self.assertEqual(len(msg['data']['practices']), 0)

		#a office manager login and has current practice
		staff.current_practice = practice
		result = local_office(request)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		self.assertEqual(len(msg['data']['practices']), 0)


#add by xlin in 130109 to test practice_info
class PracticeInfoTest(TestCase):
	def setUp(self):
		clean_db_datas()

	def test_practice_info(self):
		organization_type = create_org_type()
		practice = ct_practice('name', organization_type)

		request = generateHttpRequest()

		#a provider login
		result = practice_info(request, practice.id)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		self.assertEqual(msg['data']['id'], practice.id)

		#a staff login
		staff = OfficeStaff(user=request.user)
		staff.save()
		manager = Office_Manager(user=staff, practice=practice, manager_role=2)
		manager.save()

		assn = SmartPhoneAssn.all_objects.get(device_id=request.REQUEST['DCOM_DEVICE_ID'])
		assn.user_type = 100
		assn.save(request)

		#invalid practice
		result = practice_info(request, 0)
		self.assertEqual(result.status_code, 400)
		msg = json.loads(result.content)
		self.assertEqual(msg['errno'], 'PF003')

		#valid practice
		result = practice_info(request, practice.id)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		self.assertEqual(msg['data']['id'], practice.id)

