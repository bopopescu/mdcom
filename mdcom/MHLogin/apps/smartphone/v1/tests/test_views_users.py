import json

from django.conf import settings
from django.test import TestCase

from MHLogin.MHLPractices.models import PracticeLocation
from MHLogin.MHLSites.models import Site
from MHLogin.MHLUsers.models import Provider, OfficeStaff, Physician, \
	Office_Manager, NP_PA, MHLUser, Nurse
from MHLogin.apps.smartphone.models import SmartPhoneAssn
from MHLogin.apps.smartphone.v1.tests.utils import generateHttpRequest,\
	create_org_type, ct_practice
from MHLogin.apps.smartphone.v1.views_users import site_providers, site_staff, \
	site_students, practice_providers, practice_staff, community_providers, \
	get_all_providers_and_staffs, user_info, user_search, user_update_photo
from MHLogin.utils.tests import create_user
from MHLogin.utils.tests.tests import clean_db_datas


#add by xlin in 130107 to test site_providers
class SiteProvidersTest(TestCase):
	def setUp(self):
		clean_db_datas()

	def test_site_providers(self):
		request = generateHttpRequest()

		#provider has not current site
		result = site_providers(request)
		self.assertEqual(result.status_code, 200)

		current_site = Site(name='test site', address1='test address', lat=0.0, longit=0.1)
		current_site.save()

		request.provider.current_site = current_site
		request.provider.save()

		#provider has current site
		result = site_providers(request)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		self.assertEqual(len(msg['data']['users']), 0)

		#return_python == true
		result = site_providers(request, True)
		msg = result['data']['users']
		self.assertEqual(len(msg), 0)


#add by xlin 130108 to test site_staff
class SiteStaffTest(TestCase):
	def setUp(self):
		clean_db_datas()

	def test_site_staff(self):
		request = generateHttpRequest()
		staff = OfficeStaff(user=request.user)
		staff.save()

		assn = SmartPhoneAssn.all_objects.get(device_id=request.REQUEST['DCOM_DEVICE_ID'])
		assn.user_type = 101
		assn.save(request)

		#staff has not current site
		result = site_staff(request)
		self.assertEqual(result.status_code, 200)

		current_site = Site(name='test site', address1='test address', lat=0.0, longit=0.1)
		current_site.save()

		staff.current_site = current_site
		staff.save()

		#staff has current site
		result = site_staff(request)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		self.assertEqual(len(msg['data']['users']), 0)

		#return_python == true
		result = site_staff(request, True)
		msg = result['data']['users']
		self.assertEqual(len(msg), 0)


#add by xlin in 130108 to test site_students
class SiteStudentsTest(TestCase):
	def setUp(self):
		clean_db_datas()

	def test_site_students(self):
		request = generateHttpRequest()
		staff = OfficeStaff(user=request.user)
		staff.save()

		#provider not staff
		assn = SmartPhoneAssn.all_objects.get(device_id=request.REQUEST['DCOM_DEVICE_ID'])
		assn.user_type = 101
		assn.save(request)
		result = site_students(request)
		self.assertEqual(result.status_code, 400)
		msg = json.loads(result.content)
		self.assertEqual(msg['errno'], 'DM020')

		#get back provider and has no current site
		assn = SmartPhoneAssn.all_objects.get(device_id=request.REQUEST['DCOM_DEVICE_ID'])
		assn.user_type = 1
		assn.save(request)
		result = site_students(request)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		self.assertEqual(len(msg['data']['users']), 0)

		#provider has current site
		site = Site(name='test site', address1='test address', lat=0.0, longit=0.1)
		site.save()
		request.provider.current_site = site
		request.provider.save()
		result = site_students(request)
		self.assertEqual(result.status_code, 200)
		self.assertEqual(len(msg['data']['users']), 0)

		#Physician has current site
		request.provider.sites.add(site)
		request.provider.clinical_clerk = True
		request.provider.save()
		phy = Physician(user=request.provider)
		phy.save()
		result = site_students(request)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		self.assertEqual(len(msg['data']['users']), 1)


#add by xlin in 130108 to test practice_providers
class PracticeProvidersTest(TestCase):
	def setUp(self):
		clean_db_datas()

	def test_practice_providers(self):
		request = generateHttpRequest()

		#provider has no current practice
		result = practice_providers(request)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		self.assertEqual(len(msg['data']['users']), 0)

		organization_type = create_org_type()
		practice = ct_practice('name', organization_type)
		request.provider.current_practice = practice

		#provider has current practice but find 0
		result = practice_providers(request)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		self.assertEqual(len(msg['data']['users']), 0)

		#provider has current practice and find 1
		request.provider.practices.add(practice)
		request.provider.clinical_clerk = True
		request.provider.save()
		phy = Physician(user=request.provider)
		phy.save()
		result = practice_providers(request)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		self.assertEqual(len(msg['data']['users']), 1)


#add by xlin in 130108 to test practice_staff
class PracticeStaffTest(TestCase):
	def setUp(self):
		clean_db_datas()

	def test_practice_staff(self):
		request = generateHttpRequest()
		staff = OfficeStaff(user=request.user)
		staff.save()
		assn = SmartPhoneAssn.all_objects.get(device_id=request.REQUEST['DCOM_DEVICE_ID'])
		assn.user_type = 101
		assn.save(request)

		#staff and has no current practice
		result = practice_staff(request)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		self.assertEqual(len(msg['data']['users']), 0)

		organization_type = create_org_type()
		practice = ct_practice('test', organization_type)
		staff.current_practice = practice

		#staff has current practice but has 0 staff find
		result = practice_staff(request)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		self.assertEqual(len(msg['data']['users']), 0)

		#staff has current practice but has 1 staff find
		staff.current_practice = practice
		staff.save()
		staff.practices.add(practice)
		manager = Office_Manager(user=staff, practice=practice, manager_role=2)
		manager.save()
		result = practice_staff(request)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		self.assertEqual(len(msg['data']['users']), 1)

		#return_python == True
		result = practice_staff(request, True)
		msg = result['data']['users']
		self.assertEqual(len(msg), 1)


#add by xlin 130108 to test community_providers
class CommunityProvidersTest(TestCase):
	def setUp(self):
		clean_db_datas()

	def test_community_providers(self):
		request = generateHttpRequest()

		#find 0 provider
		result = community_providers(request)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		self.assertEqual(len(msg['data']['users']), 0)

		#find 1 provider
		phy = Physician(user=request.provider)
		phy.save()
		result = community_providers(request)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		self.assertEqual(len(msg['data']['users']), 1)

		organization_type = create_org_type()
		practice = ct_practice('name', organization_type)
		assn = SmartPhoneAssn.all_objects.get(device_id=request.REQUEST['DCOM_DEVICE_ID'])
		assn.user_type = 100
		assn.save(request)
		staff = OfficeStaff(user=request.user, current_practice=practice)
		staff.save()
		result = community_providers(request)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		self.assertEqual(len(msg['data']['users']), 1)


#add by xlin in 130108 to test get_all_providers_and_staffs
class GetAllProvidersAndStaffsTest(TestCase):
	def setUp(self):
		clean_db_datas()

	def test_get_all_providers_and_staffs(self):
		request = generateHttpRequest()

		#get method
		request.method = 'GET'
		result = get_all_providers_and_staffs(request)
		self.assertEqual(result.status_code, 400)
		msg = json.loads(result.content)
		self.assertEqual(msg['errno'], 'GE002')

		#post method
		request.method = 'POST'
		#find 0 any type user
		result = get_all_providers_and_staffs(request)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		self.assertEqual(len(msg['users']), 0)

		#has 1 nppa
		user = create_user('np1', 'abc', '', 'demo')
		provider = Provider(user=user, username='p1', first_name='abc', last_name='', 
			office_lat=0.0, office_longit=0.0)
		provider.save()
		nppa = NP_PA(user=provider)
		nppa.save()

		request.POST['name'] = unicode('abc')
		result = get_all_providers_and_staffs(request)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		self.assertEqual(len(msg['users']), 1)
		self.assertEqual(msg['users'][0]['first_name'], 'abc')

		phy = Physician(user=provider)
		phy.save()
		result = get_all_providers_and_staffs(request)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		self.assertEqual(len(msg['users']), 2)
		self.assertEqual(msg['users'][0]['first_name'], 'abc')

		#staff 
		organization_type = create_org_type()
		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',
								mdcom_phone='8005550085',
								organization_type=organization_type)
		practice.save()
		staff = OfficeStaff(user=request.user, current_practice=practice)
		staff.save()
		staff.practices.add(practice)

		request.POST['name'] = unicode(request.user.first_name)
		result = get_all_providers_and_staffs(request)
		self.assertEqual(result.status_code, 200)
		self.assertEqual(len(msg['users']), 2)
		self.assertEqual(msg['users'][0]['first_name'], 'abc')


#add by xlin in 130108 to test user_info
class UserInfoTest(TestCase):
	def setUp(self):
		clean_db_datas()

	def test_user_info(self):
		request = generateHttpRequest()

		#not find any provider match
		result = user_info(request, -123)
		self.assertEqual(result.status_code, 400)
		msg = json.loads(result.content)
		self.assertEqual(msg['errno'], 'PF001')

		#provider call this method
		result = user_info(request, request.user.id)
		self.assertEqual(result.status_code, 200)

		#physician call this method
		phy = Physician(user=request.provider)
		phy.save()
		result = user_info(request, request.user.id)
		self.assertEqual(result.status_code, 200)

		#staff call this method
		assn = SmartPhoneAssn.all_objects.get(device_id=request.REQUEST['DCOM_DEVICE_ID'])
		assn.user_type = 101
		assn.save(request)

		staff = OfficeStaff(user=request.user)
		staff.save()
		result = user_info(request, request.user.id)
		self.assertEqual(result.status_code, 200)

		#staff with current practice
		organization_type = create_org_type()
		practice = ct_practice('name', organization_type)
		staff.current_practice = practice
		staff.save()
		result = user_info(request, request.user.id)
		self.assertEqual(result.status_code, 200)

		#manager call this method
		manager = Office_Manager(user=staff, practice=practice, manager_role=2)
		manager.save()
		result = user_info(request, request.user.id)
		self.assertEqual(result.status_code, 200)


#add by xlin in 130108 to test user_search
class UserSearchTest(TestCase):
	def setUp(self):
		clean_db_datas()

	def test_user_search(self):
		request = generateHttpRequest()

		#get method
		request.method = 'GET'
		result = user_search(request)
		self.assertEqual(result.status_code, 400)
		msg = json.loads(result.content)
		self.assertEqual(msg['errno'], 'GE002')

		request.method = 'POST'

		#invalid form data
		request.POST['name'] = 'abc'
		request.POST['limit'] = 'limit'

		result = user_search(request)
		self.assertEqual(result.status_code, 400)
		msg = json.loads(result.content)
		self.assertEqual(msg['errno'], 'GE031')

		#valid form data
		request.POST['limit'] = 10

		#find 0 provider
		result = user_search(request)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		self.assertEqual(msg['data']['count'], 0)

		#find 1 provider
		mhluser = MHLUser.objects.get(id=request.user.id)
		mhluser.first_name = 'abc'
		mhluser.save()
		result = user_search(request)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		self.assertEqual(msg['data']['count'], 1)

		#1 physician find
		phy = Physician(user=request.provider)
		phy.save()
		result = user_search(request)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		self.assertEqual(msg['data']['count'], 1)

		#1 medical student find
		request.provider.clinical_clerk = True
		request.provider.save()
		result = user_search(request)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		self.assertEqual(msg['data']['count'], 1)


#add by xlin in 130109 to test user_update_photo
class UserUpdatePhotoTest(TestCase):
	def setUp(self):
		clean_db_datas()

	def test_user_update_photo(self):
		request = generateHttpRequest()

		#get method
		request.method = 'GET'
		result = user_update_photo(request)
		self.assertEqual(result.status_code, 400)
		msg = json.loads(result.content)
		self.assertEqual(msg['errno'], 'GE002')

		#post method
		request.method = 'POST'

		#provider login and has no photo
		result = user_update_photo(request)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		self.assertEqual(msg['photo'], ''.join([settings.MEDIA_URL, 'images/photos/avatar2.png']))

		#staff login and has no photo
		staff = OfficeStaff(user=request.user)
		staff.save()
		assn = SmartPhoneAssn.all_objects.get(device_id=request.REQUEST['DCOM_DEVICE_ID'])
		assn.user_type = 101
		assn.save(request)
		result = user_update_photo(request)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		self.assertEqual(msg['photo'], ''.join([settings.MEDIA_URL, 'images/photos/staff_icon.jpg']))

		#nurse login and has no photo
		nurse = Nurse(user=staff)
		nurse.save()
		result = user_update_photo(request)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		self.assertEqual(msg['photo'], ''.join([settings.MEDIA_URL, 'images/photos/nurse.jpg']))

		#user has photo, and new photo == old photo
		mhluser = MHLUser.objects.get(id=request.user.id)
		mhluser.photo = 'a.png'
		mhluser.save()
		result = user_update_photo(request)
		self.assertEqual(result.status_code, 200)
