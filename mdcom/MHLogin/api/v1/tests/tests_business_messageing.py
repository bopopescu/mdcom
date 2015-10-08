'''
Created on 2013-5-17

@author: pyang
'''
import json

from django.http import Http404

from MHLogin.api.v1.business_messaging import getReceivedMessagesLogic,\
	getSentMessagesLogic, getMessageLogic
from MHLogin.apps.smartphone.v1.tests.utils import generateHttpRequest
from MHLogin.DoctorCom.Messaging.models import Message
from MHLogin.api.v1.tests.utils import create_user, APITest


class GetMessageLogicTest(APITest):
	def testGetReceivedMessagesLogic(self):
		request = generateHttpRequest()
		request.method = "get"
		response = getReceivedMessagesLogic(request, return_python=False)
		self.assertEqual(json.loads(response.content)['errno'], 'GE002')
		request.method = "POST"
		response = getReceivedMessagesLogic(request, return_python=True)
		for dresp in response:
			self.assertEqual(dresp[1], 'a')

	def testGetSentMessagesLogic(self):
		request = generateHttpRequest()
		request.method = "get"
		response = getSentMessagesLogic(request, return_python=False)
		self.assertEqual(json.loads(response.content)['errno'], 'GE002')
		request.method = "POST"
		response = getSentMessagesLogic(request, return_python=True)
		for dresp in response:
			self.assertEqual(dresp[1], 'a')

	def testGetMessageLogic(self):
		request = generateHttpRequest()
		user = create_user('yangpeng', 'yang', 'peng', 'demo')
		msg = Message(sender=user, sender_site=None, subject="pandas")
		msg.urgent = False
		msg.message_type = 'NM'
		msg.callback_number = '2561234561'
		msg.save()
		message_id = msg.uuid
		request.method = "get"
		response = getMessageLogic(request, message_id)
		self.assertEqual(json.loads(response.content)['errno'], 'GE002')
		request.method = "POST"
		with self.assertRaises(Http404):
			getMessageLogic(request, message_id)
