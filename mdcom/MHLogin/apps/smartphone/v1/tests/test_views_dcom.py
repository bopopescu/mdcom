import json

from django.test import TestCase

from MHLogin.DoctorCom.Messaging.models import Message, MessageBodyUserStatus, \
	MessageBody
from MHLogin.MHLUsers.models import Provider, OfficeStaff, MHLUser
from MHLogin.apps.smartphone.models import SmartPhoneAssn
from MHLogin.apps.smartphone.v1.tests.utils import generateHttpRequest,\
	create_org_type, ct_practice, create_mhluser
from MHLogin.apps.smartphone.v1.views_dcom import page_user, call, \
	message_callback
from MHLogin.utils.tests import create_user
from MHLogin.utils.tests.tests import clean_db_datas


#add by xlin in 130130 to test page_user
class page_userTest(TestCase):
	def setUp(self):
		clean_db_datas()

	def test_page_user(self):
		request = generateHttpRequest()
		user_id = 0

		#get method
		request.method = 'GET'
		result = page_user(request, user_id)
		self.assertEqual(result.status_code, 400)
		msg = json.loads(result.content)
		self.assertEqual(msg['errno'], 'GE002')

		#post method
		request.method = 'POST'

		#invlid form data
		request.POST['number'] = ''
		result = page_user(request, user_id)
		self.assertEqual(result.status_code, 400)
		msg = json.loads(result.content)
		self.assertEqual(msg['errno'], 'GE031')

		#valid form data
		request.POST['number'] = '12345'

		#not found user
		result = page_user(request, user_id)
		self.assertEqual(result.status_code, 400)
		msg = json.loads(result.content)
		self.assertEqual(msg['errno'], 'GE010')

		#user not a provider or an office staff
		user_id = create_mhluser()
		result = page_user(request, user_id)
		self.assertEqual(result.status_code, 400)
		msg = json.loads(result.content)
		self.assertEqual(msg['errno'], 'GE010')

		#a provider and has no pager
		Provider.objects.all().delete()
		provider = Provider(user=request.user, office_lat=0.0, office_longit=0.0)
		provider.save()
		result = page_user(request, provider.user.id)
		self.assertEqual(result.status_code, 400)
		msg = json.loads(result.content)
		self.assertEqual(msg['errno'], 'TE002')

		#a provider and has pager
		Provider.objects.all().delete()
		provider = Provider(user=request.user, office_lat=0.0, office_longit=0.0, pager='8001234567')
		provider.save()
		result = page_user(request, provider.user.id)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		self.assertEqual(msg['data'], {})

		#an office staff and has no pager
		staff = OfficeStaff(user=create_mhluser())
		staff.save()
		result = page_user(request, staff.user.id)
		self.assertEqual(result.status_code, 400)
		msg = json.loads(result.content)
		self.assertEqual(msg['errno'], 'TE002')

		#an office staff and has pager
		staff = OfficeStaff(user=create_mhluser(), pager='8001234567')
		staff.save()
		result = page_user(request, staff.user.id)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		self.assertEqual(msg['data'], {})


#add by xlin in 130130 to test call
class CallTest(TestCase):
	def setUp(self):
		clean_db_datas()

	def test_call(self):
		phone = '80012312321'
		request = generateHttpRequest()

		#user has no mobile phone
		result = call(request)
		self.assertEqual(result.status_code, 400)
		msg = json.loads(result.content)
		self.assertEqual(msg['errno'], 'TE005')

		#user has mobile phone
		user = MHLUser.objects.get(pk=request.user.pk)
		user.mobile_phone = phone
		user.save()

		#invlid form data
		request.POST['number'] = ''
		request.POST['caller_number'] = ''
		result = call(request)
		self.assertEqual(result.status_code, 400)
		msg = json.loads(result.content)
		self.assertEqual(msg['errno'], 'GE031')

		#valid form data
		assn = SmartPhoneAssn.all_objects.get(device_id=request.REQUEST['DCOM_DEVICE_ID'])
		assn.user_type = 1
		assn.save(request)

		request.POST['number'] = '8005550056'
		request.POST['caller_number'] = '8005550056'
		result = call(request)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		self.assertEqual(msg['warnings'], {})

		#user id and is 0
		user_id = 0
		result = call(request, user_id=user_id)
		self.assertEqual(result.status_code, 400)
		msg = json.loads(result.content)
		self.assertEqual(msg['errno'], 'GE010')

		#user_id and is not 0
		username = 'test1'
		user = create_user(username, 'abc', 'def', 'demo')
		user_id = user.pk
		result = call(request, user_id=user_id)
		self.assertEqual(result.status_code, 400)
		msg = json.loads(result.content)
		self.assertEqual(msg['errno'], 'TE005')

		#user id and user hase mobile phone
		user = MHLUser.objects.get(username=username)
		user.mobile_phone = '8569854741'
		user.save()
		result = call(request, user_id=user_id)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		self.assertEqual(msg['warnings'], {})

		#practice_id is 0
		practice_id = 0
		result = call(request, practice_id=practice_id)
		self.assertEqual(result.status_code, 400)
		msg = json.loads(result.content)
		self.assertEqual(msg['errno'], 'GE010')

		#practice id is not 0
		organization_type = create_org_type()
		practice = ct_practice('name', organization_type)
		result = call(request, practice_id=practice.pk)
		self.assertEqual(result.status_code, 400)
		msg = json.loads(result.content)
		self.assertEqual(msg['errno'], 'TE006')

		#number is in kwargs
		number = '8001247841'
		result = call(request, number=number)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		self.assertEqual(msg['warnings'], {})


#add by xlin in 130131 to test message_callback
class MessageCallbackTest(TestCase):
	def setUp(self):
		clean_db_datas()

	def test_message_callback(self):
		phone = '8005550056'
		request = generateHttpRequest()

		#message not found 404
		message_id = 0
		try:
			result = message_callback(request, message_id)
		except:
			self.assertEqual(result.status_code, 404)

		#message found
		user = MHLUser.objects.get(pk=request.user.pk)
		user.mobile_phone = phone
		user.save()
		message = Message(callback_number=phone)
		message.save()
		msg_body = MessageBody(message=message)
		msg_body.save()
		request.POST['caller_number'] = phone
		status = MessageBodyUserStatus(user=request.user, msg_body=msg_body)
		status.save()
		result = message_callback(request, message.uuid)
		self.assertEqual(result.status_code, 200)

##add by xlin in 130131 to test connect_call
#class ConnectCallTest(TestCase):
#	def test_connect_call(self):
#		phone = '8005550012'
#		request = generateHttpRequest()
#		
#		#find 0 log
#		sid = 1
#		request.POST['CallSid'] = sid
#		request.POST['Caller'] = phone
#		result = connect_call(request)
#		self.assertEqual(result.status_code, 200)
#		msg = result.content
#		self.assertGreater(string.find(msg, 'Sorry, this number is a DoctorCOM public number.'), 0)
#		
#		#find 1 log
#		log = Click2Call_Log(caller=request.user, called_number=phone, caller_number=phone, connected=False)
#		log.save()
#		result = connect_call(request)
#		self.assertEqual(result.status_code, 200)
#		
#		#find 1 provider
#		result = connect_call(request)
#		self.assertEqual(result.status_code, 200)
		
