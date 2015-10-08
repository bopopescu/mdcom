'''
Created on 2013-6-28

@author: pyang
'''
from django.test.testcases import TestCase
from django.test.client import Client
from django.http.request import HttpRequest

from MHLogin.apps.smartphone.v1.utils import push_notification, get_associations,\
	render_android_notification, render_iphone_notification, ASSOCIATIONS_KEY_IOS,\
	ASSOCIATIONS_KEY_ANDROID, TAB_CHANGE_SUPPORT_VERSION
from MHLogin.utils.tests.tests import clean_db_datas
from MHLogin.apps.smartphone.models import SmartPhoneAssn
from MHLogin.apps.smartphone.v1.tests.utils import generateHttpRequest
from MHLogin.apps.smartphone.v1 import utils

class NotifyTest(object):
	def __init__(self):
		self.was_notify = False

	def __call__(self, *args, **kwargs):
		self.kwargs = kwargs
		self.args = args
		self.was_notify = True


class PushNotificationTest(TestCase):
	def setUp(self):
		clean_db_datas()
		self.request = generateHttpRequest()
		self.assn = SmartPhoneAssn.all_objects.get(device_id=self.request.REQUEST['DCOM_DEVICE_ID'])
		self.assn.user_type = 101
		self.assn.push_token = 'test smartPhoneAssn'
		self.assn.save(self.request)
		
	def tearDown(self):
		clean_db_datas()
		
	def test_push_notification(self):
		#ipad,iphone
		user_ids = [self.request.user.id]
		additional_data = {
			'user': {
				'tab_changed': True
			}
		}
		test_notify = NotifyTest()
		utils.notify_iphones = test_notify
		self.assertTrue(push_notification(user_ids,additional_data))
		self.assertTrue(test_notify.was_notify)
		#Android
		self.assn.platform = 'Android'
		self.assn.save(self.request)
		utils.notify_androids = test_notify
		self.assertTrue(push_notification(user_ids,additional_data))
		self.assertTrue(test_notify.was_notify)

class GetAssociationsTest(TestCase):
	def setUp(self):
		clean_db_datas()
		self.request = generateHttpRequest()
		self.assn = SmartPhoneAssn.all_objects.get(device_id=self.request.REQUEST['DCOM_DEVICE_ID'])
		self.assn.user_type = 101
		self.assn.push_token = 'test smartPhoneAssn'
		self.assn.save(self.request)
		
		env = Client()._base_environ()
		request = HttpRequest()
		request.META['REMOTE_ADDR'] = env['REMOTE_ADDR']
		self.assn1_request = request
		self.assn1 = SmartPhoneAssn()
		self.assn1.user = self.request.user
		self.assn1.user_type = 2
		self.assn1.platform = 'iPhone'
		self.assn1.push_token = 'test smartPhoneAssn1'
		self.assn1.save(request)
		
	def tearDown(self):
		clean_db_datas()
		
	def test_get_associations(self):
		#ipad,iphone
		user_ids = self.request.user.id
		self.assertEqual(len(get_associations(user_ids)[self.request.user.id][ASSOCIATIONS_KEY_IOS]),2)
		#Android
		self.assn.platform = 'Android'
		self.assn.save(self.request)
		self.assertEqual(len(get_associations(user_ids)[self.request.user.id][ASSOCIATIONS_KEY_ANDROID]),1)

	def test_get_associations2(self):
		#ipad,iphone
		user_ids = self.request.user.id
		associates = get_associations(user_ids, 
			support_version=TAB_CHANGE_SUPPORT_VERSION)[self.request.user.id]
		self.assertNotIn(ASSOCIATIONS_KEY_IOS, associates)
		#Android
		self.assn.platform = 'Android'
		self.assn.save(self.request)
		associates = get_associations(user_ids, 
			support_version=TAB_CHANGE_SUPPORT_VERSION)[self.request.user.id]
		self.assertNotIn(ASSOCIATIONS_KEY_ANDROID, associates)

	def test_get_associations3(self):
		#ipad,iphone
		user_ids = self.request.user.id
		#Android
		self.assn.version = '1.42.00'
		self.assn.save(self.request)

		self.assn1.version = '1.42.00'
		self.assn1.save(self.assn1_request)
		associates = get_associations(user_ids, 
			support_version=TAB_CHANGE_SUPPORT_VERSION)[self.request.user.id]

		self.assertIn(ASSOCIATIONS_KEY_IOS, associates)
		self.assertEqual(len(associates[ASSOCIATIONS_KEY_IOS]),2)

		#Android
		self.assn.platform = 'Android'
		self.assn.version = '1.57.00'
		self.assn.save(self.request)
		associates = get_associations(user_ids, 
			support_version=TAB_CHANGE_SUPPORT_VERSION)[self.request.user.id]
		self.assertIn(ASSOCIATIONS_KEY_ANDROID, associates)
		self.assertEqual(len(associates[ASSOCIATIONS_KEY_ANDROID]),1)

	def test_get_associations4(self):
		#ipad,iphone
		user_ids = self.request.user.id
		#Android
		self.assn.version = '1.41.02'
		self.assn.save(self.request)

		self.assn1.version = '1.41.02'
		self.assn1.save(self.assn1_request)
		associates = get_associations(user_ids, 
			support_version=TAB_CHANGE_SUPPORT_VERSION)[self.request.user.id]

		self.assertNotIn(ASSOCIATIONS_KEY_IOS, associates)

		#Android
		self.assn.platform = 'Android'
		self.assn.version = '1.56.00'
		self.assn.save(self.request)
		associates = get_associations(user_ids, 
			support_version=TAB_CHANGE_SUPPORT_VERSION)[self.request.user.id]
		self.assertNotIn(ASSOCIATIONS_KEY_ANDROID, associates)

	def test_get_associations5(self):
		#ipad,iphone
		user_ids = self.request.user.id
		#Android
		self.assn.version = '1.42.01'
		self.assn.save(self.request)

		self.assn1.version = '1.42.02'
		self.assn1.save(self.assn1_request)
		associates = get_associations(user_ids, 
			support_version=TAB_CHANGE_SUPPORT_VERSION)[self.request.user.id]

		self.assertIn(ASSOCIATIONS_KEY_IOS, associates)
		self.assertEqual(len(associates[ASSOCIATIONS_KEY_IOS]),2)

		#Android
		self.assn.platform = 'Android'
		self.assn.version = '1.57.01'
		self.assn.save(self.request)
		associates = get_associations(user_ids, 
			support_version=TAB_CHANGE_SUPPORT_VERSION)[self.request.user.id]
		self.assertIn(ASSOCIATIONS_KEY_ANDROID, associates)
		self.assertEqual(len(associates[ASSOCIATIONS_KEY_ANDROID]),1)

class RenderAndroidNotificationTest(TestCase):
	def setUp(self):
		clean_db_datas()
		
	def tearDown(self):
		clean_db_datas()
		
	def test_render_android_notification(self):
		additional_data = {
			'user': {
				'tab_changed': True
			}
		}
		self.assertEqual(render_android_notification(additional_data)['badge'],0)
		self.assertTrue(render_android_notification(additional_data)['user']['tab_changed'])

class RenderIphoneNotificationTest(TestCase):
	def setUp(self):
		clean_db_datas()
		
	def tearDown(self):
		clean_db_datas()
		
	def test_render_iphone_notification(self):
		additional_data = {
			'user': {
				'tab_changed': True
			}
		}
		count = 1
		self.assertEqual(len(render_iphone_notification(additional_data)['aps']['alert']),0)
		self.assertEqual(render_iphone_notification(additional_data,count)['aps']['badge'],count)
