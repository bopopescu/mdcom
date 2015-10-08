import json

from django.test import TestCase

from MHLogin.DoctorCom.Messaging.models import MessageBodyUserStatus, \
	MessageBody, Message
from MHLogin.apps.smartphone.v1.tests.utils import generateHttpRequest
from MHLogin.apps.smartphone.v1.views_messaging import rx_message_list, \
	tx_message_list, delete_message, get_message


#add by xlin in 130109 to test rx_message_list
class rx_message_listTest(TestCase):
	def test_rx_message_list(self):
		request = generateHttpRequest()

		#get method
		request.method = 'GET'
		result = rx_message_list(request)
		self.assertEqual(result.status_code, 400)
		msg = json.loads(result.content)
		self.assertEqual(msg['errno'], 'GE002')

		#post method
		request.method = 'POST'

		#invliad form data
		request.POST['from_timestamp'] = 'wzs'
		result = rx_message_list(request)
		self.assertEqual(result.status_code, 400)
		msg = json.loads(result.content)
		self.assertEqual(msg['errno'], 'GE031')

		#from_timestamp
		request.POST['from_timestamp'] = 1356668292
		result = rx_message_list(request)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		self.assertEqual(msg['warnings'], {})

		#to_timestamp
		request.POST['to_timestamp'] = 1356668292
		result = rx_message_list(request)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		self.assertEqual(msg['warnings'], {})

		#count
		request.POST['count'] = 10
		result = rx_message_list(request)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		self.assertEqual(msg['warnings'], {})

		#resolved
		request.POST['resolved'] = True
		result = rx_message_list(request)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		self.assertEqual(msg['warnings'], {})

		#read
		request.POST['read'] = True
		result = rx_message_list(request)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		self.assertEqual(msg['warnings'], {})

		#exclude_id
		request.POST['exclude_id'] = None
		result = rx_message_list(request)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		self.assertEqual(msg['warnings'], {})

		#is_threading
		request.POST['is_threading'] = True
		result = rx_message_list(request)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		self.assertEqual(msg['warnings'], {})

		#thread_uuid
		request.POST['thread_uuid'] = '1'
		result = rx_message_list(request)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		self.assertEqual(msg['warnings'], {})

		#use_time_setting
		request.POST['use_time_setting'] = True
		result = rx_message_list(request)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		self.assertEqual(msg['warnings'], {})

		#return_python is true
		result = rx_message_list(request, True)
		self.assertEqual(result['warnings'], {})


#add by xlin in 130109 to test tx_message_list
class tx_message_listTest(TestCase):
	def test_tx_message_list(self):
		request = generateHttpRequest()

		#get method
		request.method = 'GET'
		result = tx_message_list(request)
		self.assertEqual(result.status_code, 400)
		msg = json.loads(result.content)
		self.assertEqual(msg['errno'], 'GE002')

		#post method
		request.method = 'POST'

		#invliad form data
		request.POST['from_timestamp'] = 'wzs'
		result = tx_message_list(request)
		self.assertEqual(result.status_code, 400)
		msg = json.loads(result.content)
		self.assertEqual(msg['errno'], 'GE031')

		#from_timestamp
		request.POST['from_timestamp'] = 1356668292
		result = tx_message_list(request)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		self.assertEqual(msg['warnings'], {})

		#to_timestamp
		request.POST['to_timestamp'] = 1356668292
		result = tx_message_list(request)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		self.assertEqual(msg['warnings'], {})

		#count
		request.POST['count'] = 10
		result = tx_message_list(request)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		self.assertEqual(msg['warnings'], {})

		#resolved
		request.POST['resolved'] = True
		result = tx_message_list(request)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		self.assertEqual(msg['warnings'], {})

		#read
		request.POST['read'] = True
		result = tx_message_list(request)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		self.assertEqual(msg['warnings'], {})

		#exclude_id
		request.POST['exclude_id'] = None
		result = tx_message_list(request)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		self.assertEqual(msg['warnings'], {})

		#is_threading
		request.POST['is_threading'] = True
		result = tx_message_list (request)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		self.assertEqual(msg['warnings'], {})

		#thread_uuid
		request.POST['thread_uuid'] = '1'
		result = tx_message_list(request)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		self.assertEqual(msg['warnings'], {})

		#use_time_setting
		request.POST['use_time_setting'] = True
		result = tx_message_list(request)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		self.assertEqual(msg['warnings'], {})

		#return_python is true
		result = tx_message_list(request, True)
		self.assertEqual(result['warnings'], {})

#add by xlin in 130109 to test delete_message
class DeleteMessageTest(TestCase):
	def test_delete_message(self):
		request = generateHttpRequest()

		#not find message
		result = delete_message(request, '20fc43b89e97484aba6fc1870f026a2e')
		self.assertEqual(result.status_code, 400)
		msg = json.loads(result.content)
		self.assertEqual(msg['errno'], 'IN003')

		#find message
		msg = Message(sender=request.user, sender_site=None, subject="pandas")
		msg.urgent = False
		msg.message_type = 'NM'
		msg.callback_number = '2561234561'
		msg.save()
		body = "i am indeed a talking panda. how are you?"
		msg_body = MessageBody(message=msg, body=body)
		msg_body.save()
		mbu = MessageBodyUserStatus(msg_body=msg_body, user=request.user)
		mbu.save()

		result = delete_message(request, msg.uuid)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		self.assertEqual(msg['data'], {})


#add by xlin in 130109 to test get_message
class GetMessageTest(TestCase):
	def test_get_message(self):
		request = generateHttpRequest()

		#get method
		request.method = 'GET'
		result = get_message(request, '20fc43b89e97484aba6fc1870f026a2e')
		self.assertEqual(result.status_code, 400)
		msg = json.loads(result.content)
		self.assertEqual(msg['errno'], 'GE002')

		#post method
		request.method = 'POST'

		#invalid form data
		request.POST['secret'] = '123'
		result = get_message(request, '20fc43b89e97484aba6fc1870f026a2e')
		self.assertEqual(result.status_code, 400)
		msg = json.loads(result.content)
		self.assertEqual(msg['errno'], 'GE031')

#		#valid form data but find 0 message
#		request.POST['secret'] = '20fc43b89e97484aba6fc1870f026a2e'
#		try:
#			result = get_message(request, '20fc43b89e97484aba6fc1870f026a2e')
#		except:
#			self.assertEqual(result.status_code, 200)
#			msg = json.loads(result.content)
#			self.assertEqual(msg['errno'], 'GE031')
#		
#		#valid form data and find 1 message
#		provider = Provider(user=request.user, office_lat=0.0, office_longit=0.0)
#		provider.save()
#		
#		msg = Message(sender=request.user, sender_site=None, subject="pandas")
#		msg.urgent = False
#		msg.message_type = 'NM'
#		msg.callback_number = '2561234561'
#		msg.save()
#		body = "i am indeed a talking panda. how are you?"
#		msg_body = MessageBody(message=msg, body=body)
#		msg_body.save()
#		mbu = MessageBodyUserStatus(msg_body=msg_body, user=request.user)
#		mbu.save()
#		
#		request.POST['secret'] = msg.uuid
#		result = get_message(request, msg.uuid)


