'''
Created on 2013-6-26

@author: pyang
'''
from django.test.testcases import TestCase
from MHLogin.api.v1.utils_messaging import get_refer, _get_attachment_filename
from MHLogin.DoctorCom.Messaging.models import MessageRefer, Message,\
	MessageAttachment, MessageContent
from MHLogin.api.v1.tests.utils import create_user
from MHLogin.apps.smartphone.v1.tests.utils import generateHttpRequest
class GetReferTest(TestCase):
	def testGetRefer(self):
		user = create_user('practicemgr','yang','peng','demo')
		msg = Message(sender=user, sender_site = None, subject="pandas")
		msg.urgent = False
		msg.callback_number = 2561234561
		msg.save()
		refer = MessageRefer()
		refer.message = msg
		refer.gender = 'M'
		refer.status = 'AC'
		refer.phone_number = 8529631475
		refer.alternative_phone_number = 1472583695
		refer.home_phone_number = 8472583695
		refer.save()
		refer_list=[refer]
		self.assertEqual(get_refer(refer_list),refer.status)
		with self.assertRaises(TypeError):get_refer(refer)

#class Get_attachment_filenameTest(TestCase):
#	def test_get_attachment_filename(self):
#		user = create_user('practicemgr','yang','peng','demo')
#		msg = Message(sender=user, sender_site = None, subject="pandas")
#		msg.urgent = False
#		msg.callback_number = 2561234561
#		msg.save()
#		request = generateHttpRequest()
#		msgCon = MessageContent()
#		msgCon.message=msg
#		msgCon.save()
#		attachment = MessageAttachment(msgCon)
#		attachment.size = '12'
#		attachment.save()
#		
#		_get_attachment_filename(request,msg)