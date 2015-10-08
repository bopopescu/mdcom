import json

from django.test import TestCase

from MHLogin.apps.smartphone.v1.tests.utils import generateHttpRequest
from MHLogin.apps.smartphone.v1.views_validates import sendCode, validate


#add by xlin in 130125 to test sendCode
class SendCodeTest(TestCase):
	def test_sendCode(self):
		request = generateHttpRequest()

		#get method
		request.method = 'GET'
		result = sendCode(request)
		self.assertEqual(result.status_code, 400)
		msg = json.loads(result.content)
		self.assertEqual(msg['errno'], 'GE002')

		#post method
		request.method = 'POST'
		request.POST['recipient'] = ''
		request.POST['type'] = ''
		request.POST['init'] = ''
		result = sendCode(request)
		self.assertEqual(result.status_code, 400)
		msg = json.loads(result.content)
		self.assertEqual(msg['errno'], 'GE031')

		#user type is 1
		request.POST['recipient'] = 'a@a.cn'
		request.POST['type'] = '1'
		request.POST['init'] = True
		request.user.mobile_phone = '800123456'
		request.user.mobile_confirmed = True
		result = sendCode(request)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		self.assertEqual(len(msg), 3)

		#user type is 2
#		request.POST['recipient'] = 'testP@suzhoukada.com'
#		request.POST['type'] = '2'
#		request.POST['init'] = True
#		request.user.mobile_phone = '800123456'
#		request.user.mobile_confirmed = True
#		result = sendCode(request)
#		self.assertEqual(result.status_code, 200)
#		msg = json.loads(result.content)
#		self.assertEqual(len(msg), 3)

#add by xlin in 130128 to test validate
class ValidateTest(TestCase):
	def test_validate(self):
		request = generateHttpRequest()

		#get method
		request.method = 'GET'
		result = validate(request)
		self.assertEqual(result.status_code, 400)
		msg = json.loads(result.content)
		self.assertEqual(msg['errno'], 'GE002')

		#post method
		request.method = 'POST'
		request.POST['recipient'] = ''
		request.POST['type'] = ''
		request.POST['init'] = ''
		result = validate(request)
		self.assertEqual(result.status_code, 400)
		msg = json.loads(result.content)
		self.assertEqual(msg['errno'], 'GE031')

		request.method = 'POST'
		request.POST['recipient'] = 'testP@suzhoukada.com'
		request.POST['type'] = '1'
		request.POST['init'] = True
		request.POST['code'] = 'test'
		result = validate(request)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		self.assertEqual(len(msg), 3)

