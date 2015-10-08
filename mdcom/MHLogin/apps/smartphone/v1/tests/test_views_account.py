
import json
import mock

from django.conf import settings
from django.test import TestCase

from MHLogin.MHLSites.models import Site
from MHLogin.MHLUsers.models import OfficeStaff, MHLUser
from MHLogin.apps.smartphone.models import SmartPhoneAssn
from MHLogin.apps.smartphone.v1.tests.utils import generateHttpRequest,\
	create_org_type, ct_practice
from MHLogin.apps.smartphone.v1.views_account import get_key, practice_mgmt, \
	site_mgmt, call_fwd_prefs, get_dcom_number, get_mobile_phone, \
	update_mobile_phone, anssvc_forwarding, preference, getForwardChoicesKeyByValue, \
	_err_AM010
from MHLogin.utils.tests.tests import clean_db_datas


#add by xlin in 130107 to test get_key
class GetKeyTest(TestCase):
	def test_get_key(self):
		request = generateHttpRequest()
		#get method
		request.method = 'GET'
		result = get_key(request)
		self.assertEqual(result.status_code, 400)
		msg = json.loads(result.content)
		self.assertEqual(msg['errno'], 'GE002')

		#post method and form data is invalid
		request.method = 'POST'
		request.POST['secret'] = 'error'
		result = get_key(request)
		self.assertEqual(result.status_code, 400)
		msg = json.loads(result.content)
		self.assertEqual(msg['errno'], 'GE031')

		#miss valid data


#add by xlin in 130107 to test practice_mgmt
class practice_mgmtTest(TestCase):
	def setUp(self):
		clean_db_datas()

	@mock.patch('MHLogin.apps.smartphone.v1.views_account.thread.start_new_thread', autospec=True)
	def test_practice_mgmt(self, start_thread):
		request = generateHttpRequest()

		#get method and provider
		request.method = 'GET'
		result = practice_mgmt(request)
		self.assertEqual(result.status_code, 200)

		#get method and staff
		staff = OfficeStaff(user=request.user)
		staff.save()
		assn = SmartPhoneAssn.all_objects.get(device_id=request.REQUEST['DCOM_DEVICE_ID'])
		assn.user_type = 100
		assn.save(request)
		result = practice_mgmt(request)
		self.assertEqual(result.status_code, 200)

		#post method and no practice
		request.method = 'POST'
		result = practice_mgmt(request)
		self.assertEqual(result.status_code, 400)

		#post method and have practice but not manager
		organization_type = create_org_type()
		practice = ct_practice('name', organization_type)
		request.POST['current_practice'] = practice.id
		result = practice_mgmt(request)
		self.assertEqual(result.status_code, 200)

		#post method and staff can not change current practice
		assn = SmartPhoneAssn.all_objects.get(device_id=request.REQUEST['DCOM_DEVICE_ID'])
		assn.user_type = 101
		assn.save(request)
		result = practice_mgmt(request)
		self.assertEqual(result.status_code, 403)

		#post method and can change current practice
		assn = SmartPhoneAssn.all_objects.get(device_id=request.REQUEST['DCOM_DEVICE_ID'])
		assn.user_type = 1
		assn.save(request)
		request.provider.practices.add(practice)
		result = practice_mgmt(request)
		self.assertEqual(result.status_code, 200)


#add by xlin 130107 to test site_mgmt
class SiteMgmtTest(TestCase):
	def setUp(self):
		clean_db_datas()

	def test_site_mgmt(self):
		request = generateHttpRequest()
		#get method and provider
		request.method = 'GET'
		result = site_mgmt(request)
		self.assertEqual(result.status_code, 200)

		#post method and site is none
		request.method = 'POST'
		result = site_mgmt(request)
		self.assertEqual(result.status_code, 200)

		#post method and new site is user site
		site = Site(name='test site', address1='test address', lat=0.0, longit=0.1)
		site.save()
		request.POST['current_site'] = site.id
		request.provider.sites.add(site)
		result = site_mgmt(request)
		self.assertEqual(result.status_code, 200)


#add by xlin 130107 to test call_fwd_prefs
class CallFwdPrefsTest(TestCase):
	def setUp(self):
		clean_db_datas()

	def test_call_fwd_prefs(self):
		request = generateHttpRequest()
		staff = OfficeStaff(user=request.user)
		staff.save()
		assn = SmartPhoneAssn.all_objects.get(device_id=request.REQUEST['DCOM_DEVICE_ID'])
		assn.user_type = 101
		assn.save(request)

		#error user type
		result = call_fwd_prefs(request)
		self.assertEqual(result.status_code, 400)
		msg = json.loads(result.content)
		self.assertEqual(msg['errno'], 'DM020')

		#correct user type, and have no phone number
		assn = SmartPhoneAssn.all_objects.get(device_id=request.REQUEST['DCOM_DEVICE_ID'])
		assn.user_type = 1
		assn.save(request)

		request.method = 'GET'
		result = call_fwd_prefs(request)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		self.assertEqual(len(msg['data']['choices']), 1)
		self.assertEqual(msg['data']['choices'][0], 'Voicemail')

		#user have mobile phone
		mhluser = MHLUser.objects.get(id=request.user.id)
		mhluser.mobile_phone = '8005550011'
		mhluser.save()
		result = call_fwd_prefs(request)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		self.assertEqual(len(msg['data']['choices']), 2)
		self.assertEqual(msg['data']['choices'][1], 'Mobile')

		#pravider has office phone
		request.provider.office_phone = '8005550015'
		request.provider.save()
		result = call_fwd_prefs(request)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		self.assertEqual(len(msg['data']['choices']), 3)
		self.assertEqual(msg['data']['choices'][2], 'Office')

		#user has phone
		mhluser.phone = '8005550032'
		mhluser.save()
		result = call_fwd_prefs(request)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		self.assertEqual(len(msg['data']['choices']), 4)
		self.assertEqual(msg['data']['choices'][3], 'Other')

		#post method
		request.method = 'POST'
		request.POST['forward'] = 'abc'
		result = call_fwd_prefs(request)
		self.assertEqual(result.status_code, 400)
		msg = json.loads(result.content)
		self.assertEqual(msg['errno'], 'GE031')

		#invalid data
		request.POST['forward'] = 'Mobile'
		result = call_fwd_prefs(request)
		self.assertEqual(result.status_code, 200)

		request.POST['forward'] = 'Office'
		result = call_fwd_prefs(request)
		self.assertEqual(result.status_code, 200)

		request.POST['forward'] = 'Other'
		result = call_fwd_prefs(request)
		self.assertEqual(result.status_code, 200)


#add by xlin in 130107 to test get_dcom_number
class GetDcomNumberTest(TestCase):
	def setUp(self):
		clean_db_datas()

	def test_get_dcom_number(self):
		request = generateHttpRequest()
		staff = OfficeStaff(user=request.user)
		staff.save()

		#a provider call this method
		result = get_dcom_number(request)
		self.assertEqual(result.status_code, 200)

		#a staff or manager call this method
		assn = SmartPhoneAssn.all_objects.get(device_id=request.REQUEST['DCOM_DEVICE_ID'])
		assn.user_type = 101
		assn.save(request)

		result = get_dcom_number(request)
		self.assertEqual(result.status_code, 200)

		#has current_practice
		organization_type = create_org_type()
		practice = ct_practice('name', organization_type)
		staff.current_practice = practice
		staff.save()
		result = get_dcom_number(request)
		self.assertEqual(result.status_code, 200)


#add by xlin in 130107 to test get_mobile_phone
class GetMobilePhoneTest(TestCase):
	def test_get_mobile_phone(self):
		request = generateHttpRequest()
		result = get_mobile_phone(request)
		self.assertEqual(result.status_code, 200)


#add by xlin in 130107 to test update_mobile_phone
class update_mobile_phoneTest(TestCase):
	def test_update_mobile_phone(self):
		request = generateHttpRequest()
		staff = OfficeStaff(user=request.user)
		staff.save()

		#get method
		request.method = 'GET'
		result = update_mobile_phone(request)
		self.assertEqual(result.status_code, 400)
		msg = json.loads(result.content)
		self.assertEqual(msg['errno'], 'GE002')

		#post method
		request.method = 'POST'

		#invalid mobile phone number
		request.POST['mobile_phone'] = '1236'
		result = update_mobile_phone(request)
		self.assertEqual(result.status_code, 400)
		msg = json.loads(result.content)
		self.assertEqual(msg['errno'], 'GE031')

		#valid mobile phone number but someone has been used
		temp = settings.CALL_ENABLE
		settings.CALL_ENABLE = False
		mobile_phone = '8005550094'
		user = MHLUser(mobile_phone=mobile_phone, username='samenumber', 
			first_name='sa', last_name='as', password='demo')
		user.save()
		request.POST['mobile_phone'] = mobile_phone
		result = update_mobile_phone(request)
		self.assertEqual(result.status_code, 400)
		msg = json.loads(result.content)
		self.assertEqual(msg['errno'], 'AM020')

		#valid mobile phone number and nobody use it
		mobile_phone2 = '8007750094'
		request.POST['mobile_phone'] = mobile_phone2
		result = update_mobile_phone(request)
		self.assertEqual(result.status_code, 200)
		settings.CALL_ENABLE = temp


#add by xlin 130107 to test anssvc_forwarding
class AnssvcForwardingTest(TestCase):
	def test_anssvc_forwarding(self):
		request = generateHttpRequest()
		staff = OfficeStaff(user=request.user)
		staff.save()
		assn = SmartPhoneAssn.all_objects.get(device_id=request.REQUEST['DCOM_DEVICE_ID'])
		assn.user_type = 101
		assn.save(request)

		#not provider call this method
		result = anssvc_forwarding(request)
		self.assertEqual(result.status_code, 400)
		msg = json.loads(result.content)
		self.assertEqual(msg['errno'], 'DM020')

		#change back to provider
		assn = SmartPhoneAssn.all_objects.get(device_id=request.REQUEST['DCOM_DEVICE_ID'])
		assn.user_type = 1
		assn.save(request)

		request.method = 'GET'

		#get method and have no phone number
		result = anssvc_forwarding(request)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		self.assertEqual(len(msg['data']['choices']), 1)
		self.assertEqual(msg['data']['choices'][0], 'Voicemail')

		#get method and user have mobile phone
		mhluser = MHLUser.objects.get(id=request.user.id)
		mhluser.mobile_phone = '8005550011'
		mhluser.save()
		result = anssvc_forwarding(request)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		self.assertEqual(len(msg['data']['choices']), 2)
		self.assertEqual(msg['data']['choices'][1], 'Mobile')

		#get method and provider has office phone
		request.provider.office_phone = '8005550015'
		request.provider.save()
		result = anssvc_forwarding(request)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		self.assertEqual(len(msg['data']['choices']), 3)
		self.assertEqual(msg['data']['choices'][2], 'Office')

		#get method and user have other phone number
		mhluser.phone = '8005550032'
		mhluser.save()
		result = anssvc_forwarding(request)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		self.assertEqual(len(msg['data']['choices']), 4)
		self.assertEqual(msg['data']['choices'][3], 'Other')

		request.method = 'POST'

		#post method and invliad forward
		request.POST['forward'] = '123'
		result = anssvc_forwarding(request)
		self.assertEqual(result.status_code, 400)
		msg = json.loads(result.content)
		self.assertEqual(msg['errno'], 'GE031')

		#post method and valid forward
		request.POST['forward'] = 'Mobile'
		result = anssvc_forwarding(request)
		self.assertEqual(result.status_code, 200)


#add by xlin in 130107 to test preference
class PreferenceTest(TestCase):
	def test_preference(self):
		request = generateHttpRequest()
		#get method
		request.method = 'GET'
		result = preference(request)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
#		self.assertEqual(msg['data']['time_zone'], settings.TIME_ZONE)
		self.assertEqual(msg['data']['time_setting'], request.user.time_setting)

		request.method = 'POST'
		#post method and invalid time_setting
		request.POST['time_setting'] = 3
		result = preference(request)
		self.assertEqual(result.status_code, 400)
		msg = json.loads(result.content)
		self.assertEqual(msg['errno'], 'GE031')

		#post methdo and valid time_setting
		request.POST['time_setting'] = 1
		result = preference(request)
		self.assertEqual(result.status_code, 200)


#add by xlin in 130107 to test getForwardChoicesKeyByValue
class GetForwardChoicesKeyByValueTest(TestCase):
	def test_getForwardChoicesKeyByValue(self):
		val = ''
		result = getForwardChoicesKeyByValue(val)
		self.assertIsNone(result)

		val = 'Mobile'
		result = getForwardChoicesKeyByValue(val)
		self.assertEqual(result, 'MO')

		val = 'Office'
		result = getForwardChoicesKeyByValue(val)
		self.assertEqual(result, 'OF')

		val = 'Other'
		result = getForwardChoicesKeyByValue(val)
		self.assertEqual(result, 'OT')

		val = 'Voicemail'
		result = getForwardChoicesKeyByValue(val)
		self.assertEqual(result, 'VM')


#add by xlin in 130107 to test _err_AM010
class ErrAM010Test(TestCase):
	def test_err_AM010(self):
		result = _err_AM010()
		self.assertEqual(result.status_code, 400)
		msg = json.loads(result.content)
		self.assertEqual(msg['errno'], 'AM010')
