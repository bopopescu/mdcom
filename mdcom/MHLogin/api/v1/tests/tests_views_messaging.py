'''
Created on 2013-5-13

@author: pyang
'''
import json

from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse

from MHLogin.DoctorCom.IVR.models import VMBox_Config
from MHLogin.DoctorCom.Messaging.models import MessageBodyUserStatus, Message, \
	MessageBody, MessageRefer, MessageRecipient
from MHLogin.DoctorCom.Messaging.tests import DevNull
from MHLogin.KMS.utils import generate_keys_for_users
from MHLogin.MHLUsers.models import Provider
from MHLogin.api.v1.errlib import err_GE002
from MHLogin.api.v1.tests.utils import APITest, create_user, get_random_username


class GetMessagesTest(APITest):
	def testGetReceivedMessages(self):
		response = self.client.get(reverse(
			'MHLogin.api.v1.views_messaging.getReceivedMessages'), **self.extra)
		self.assertEqual(response.content, err_GE002().content, response.status_code)

		response = self.client.post(reverse(
			'MHLogin.api.v1.views_messaging.getReceivedMessages'), **self.extra)
		self.assertEqual(response.status_code, 200, response.status_code)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 2)

	def testGetSentMessages(self):
		response = self.client.get(reverse(
			'MHLogin.api.v1.views_messaging.getReceivedMessages'), **self.extra)
		self.assertEqual(response.content, err_GE002().content, response.status_code)

		response = self.client.post(reverse(
			'MHLogin.api.v1.views_messaging.getSentMessages'), **self.extra)
		self.assertEqual(response.status_code, 200, response.status_code)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 2)


class DeleteMessagesTest(APITest):
	def testDeleteMessages(self):
		response = self.client.get(reverse('MHLogin.api.v1.views_messaging.deleteMessages'), **self.extra)
		self.assertEqual(response.content, err_GE002().content, response.status_code)

		response = self.client.post(reverse('MHLogin.api.v1.views_messaging.deleteMessages'), **self.extra)
		self.assertEqual(response.status_code, 400, response.status_code)

		self.user = create_user(get_random_username(), "mhluser", "thj", "demo", 
						"555 Bryant St.", "Palo Alto", "CA", "")
		self.user.mdcom_phone = '9002000001'
		self.user.save()
		sender = self.user
		msg = Message(sender=sender, sender_site=None, subject="pandas")
		msg.urgent = False
		msg.message_type = 'NM'
		msg.callback_number = '2561234561'
		msg.save()
		message_id = msg.uuid
		data = {'message_ids': [message_id]}
		response = self.client.post(reverse('MHLogin.api.v1.views_messaging.deleteMessages'), 
			data, **self.extra)
		self.assertEqual(response.status_code, 200, response.status_code)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 2)


class DeleteMessageTest(APITest):
	def testDeleteMessage(self):
		self.user = create_user(get_random_username(), "mhluser", "thj", "demo", 
						"555 Bryant St.", "Palo Alto", "CA", "")
		self.user.mdcom_phone = '9002000001'
		self.user.save()
		sender = self.user
		msg = Message(sender=sender, sender_site=None, subject="pandas")
		msg.urgent = False
		msg.message_type = 'NM'
		msg.callback_number = '2561234561'
		msg.save()
		body = "i am indeed a talking panda. how are you?"
		msg_body = MessageBody(message=msg, body=body)
		msg_body.save()

		msgbus = MessageBodyUserStatus()
		msgbus.user = self.user
		msgbus.msg_body = msg_body
		msgbus.save()
		self.msgbus = msgbus

		self.extra['HTTP_MDCOM_USER_UUID'] = self.user.uuid

		message_id = msg.uuid
		response = self.client.get(reverse(
			'MHLogin.api.v1.views_messaging.deleteMessage', 
				args=(message_id,)), **self.extra)
		self.assertEqual(response.status_code, 200, response.status_code)


class ComposeMessageTest(APITest):

	def testComposeMessage(self):
		response = self.client.get(reverse(
			'MHLogin.api.v1.views_messaging.composeMessage'), **self.extra)
		self.assertEqual(response.content, err_GE002().content, response.status_code)

		response = self.client.post(reverse(
			'MHLogin.api.v1.views_messaging.composeMessage'), **self.extra)
		self.assertEqual(response.status_code, 400, response.status_code)

#		provider = create_user("upretest", "upre", "test", "maestro",
#				"555 Bryant St.", "Palo Alto", "CA", "", uklass=Provider)
#
#		provider2 = create_user("doc holiday", "doc", "holiday", "holiday",
#				"555 Bryant St.", "Palo Alto", "CA", "", uklass=Provider)
#
#		data={'body':'i am indeed a talking panda. how are you?',
#			'recipients': ",".join([str(provider.id), str(provider2.id)])}
#		response = self.client.post(reverse('MHLogin.api.v1.views_messaging.composeMessage'), 
#			data, **self.extra)
#		self.assertEqual(response.status_code, 200, response.status_code)


class ComposeADSTest(APITest):
	def testComposeADS(self):
		response = self.client.get(reverse(
			'MHLogin.api.v1.views_messaging.composeADS'), **self.extra)
		self.assertEqual(response.content, err_GE002().content, response.status_code)

		response = self.client.post(reverse(
			'MHLogin.api.v1.views_messaging.composeADS'), **self.extra)
		self.assertEqual(response.status_code, 400, response.status_code)

#		provider = create_user("upretest", "upre", "test", "maestro",
#				"555 Bryant St.", "Palo Alto", "CA", "", uklass=Provider)
#		provider2 = create_user("doc holiday", "doc", "holiday", "holiday",
#				"555 Bryant St.", "Palo Alto", "CA", "", uklass=Provider)
#
#		data={'body':'i am indeed a talking panda. how are you?',
#			'recipients': ",".join([str(provider.id), str(provider2.id)])}
#		response = self.client.post(reverse('MHLogin.api.v1.views_messaging.composeADS'), 
#			data, **self.extra)
#		self.assertEqual(response.status_code, 200, response.status_code)


class ComposeReferTest(APITest):
	def testComposeRefer(self):
		response = self.client.get(reverse(
			'MHLogin.api.v1.views_messaging.composeRefer'), **self.extra)
		self.assertEqual(response.content, err_GE002().content, response.status_code)

		response = self.client.post(reverse(
			'MHLogin.api.v1.views_messaging.composeRefer'), **self.extra)
		self.assertEqual(response.status_code, 400, response.status_code)

#		provider = create_user("upretest", "upre", "test", "maestro",
#				"555 Bryant St.", "Palo Alto", "CA", "", uklass=Provider)
#
#		data = {'date_of_birth':'05/20/2000',
#			'first_name':'yang',
#			'gender':'M',
#			'last_name':'peng',
#			'phone_number':9000555624,
#			'reason_of_refer':'test it',
#			'user_recipients':str(provider.id),}
#		response = self.client.post(reverse('MHLogin.api.v1.views_messaging.composeRefer'), 
#			data, **self.extra)
#		self.assertEqual(response.status_code, 200, response.status_code)


class MessageTest(APITest):
	def testGetMessage(self):
		sender = self.user
		msg = Message(sender=sender, sender_site=None, subject="pandas")
		msg.urgent = False
		msg.message_type = 'NM'
		msg.callback_number = '2561234561'
		msg.save()
		body = "i am indeed a talking panda. how are you?"
		msg_body = MessageBody(message=msg, body=body)
		msg_body.save()

		msgbus = MessageBodyUserStatus()
		msgbus.user = self.user
		msgbus.msg_body = msg_body
		msgbus.save()
		self.msgbus = msgbus

		self.object_type = ContentType.objects.get_for_model(msg_body)
		self.extra['HTTP_MDCOM_USER_UUID'] = self.user.uuid

		response = self.client.get(reverse(
			'MHLogin.api.v1.views_messaging.getMessage', args=(msg.uuid,)), **self.extra)
		self.assertEqual(response.content, err_GE002().content, response.status_code)
#		response = self.client.post(reverse\
#				('MHLogin.api.v1.views_messaging.getMessage', args=(msg.uuid,)), **self.extra)

	def testGetReferPDF(self):
		sender = self.user
		msg = Message(sender=sender, sender_site=None, subject="pandas")
		msg.urgent = False
		msg.message_type = 'NM'
		msg.callback_number = '2561234561'
		msg.save()

		refer = MessageRefer()
		refer.message = msg
		refer.gender = 'M'
		refer.status = 'AC'
		refer.phone_number = 8529631475
		refer.alternative_phone_number = 1472583695
		refer.home_phone_number = 8472583695
		refer.save()
		response = self.client.get(reverse('MHLogin.api.v1.views_messaging.getReferPDF', \
				args=(refer.uuid,)), **self.extra)
		self.assertEqual(response.content, err_GE002().content, response.status_code)

		response = self.client.post(reverse('MHLogin.api.v1.views_messaging.getReferPDF', \
				args=(refer.uuid,)), **self.extra)
		self.assertEqual(response.status_code, 400, response.status_code)

		with self.assertRaises(Exception):
			self.client.post(reverse(
				'MHLogin.api.v1.views_messaging.getReferPDF', args=(refer.uuid,)), \
				data={'secret': 'ABeohIU4Sy48bQ/w07cLKBJ6gv49ptEF0YY48VXSMr4='}, **self.extra)


class MarkMessageTest(APITest):
	def testMarkMessageRead(self):

		response = self.client.get(reverse(
			'MHLogin.api.v1.views_messaging.markMessageRead'), **self.extra)
		self.assertEqual(response.content, err_GE002().content, response.status_code)

		self.user = create_user(get_random_username(), "mhluser", "thj", "demo", 
						"555 Bryant St.", "Palo Alto", "CA", "")
		self.user.mdcom_phone = '9002000001'
		self.user.save()
		sender = self.user
		msg = Message(sender=sender, sender_site=None, subject="pandas")
		msg.urgent = False
		msg.message_type = 'NM'
		msg.callback_number = '2561234561'
		msg.save()
		message_id = msg.uuid
		data = {'message_ids': [message_id]}
		response = self.client.post(reverse(
			'MHLogin.api.v1.views_messaging.markMessageRead'), data, **self.extra)
		self.assertEqual(response.status_code, 200, response.status_code)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 2)

	def testMarkMessageUnread(self):
		response = self.client.get(reverse(
			'MHLogin.api.v1.views_messaging.markMessageUnread'), **self.extra)
		self.assertEqual(response.content, err_GE002().content, response.status_code)

		sender = self.user
		msg = Message(sender=sender, sender_site=None, subject="pandas")
		msg.urgent = False
		msg.message_type = 'NM'
		msg.callback_number = '2561234561'
		msg.save()
		message_id = msg.uuid
		data = {'message_ids': [message_id]}
		response = self.client.post(reverse(
			'MHLogin.api.v1.views_messaging.markMessageUnread'), data, **self.extra)
		self.assertEqual(response.status_code, 200, response.status_code)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 2)


class GetAttachmentTest(APITest):
	def testGetAttachment(self):
		sender = self.user
		msg = Message(sender=sender, sender_site=None, subject="pandas")
		msg.urgent = False
		msg.draft = True
		msg.message_type = 'NM'
		msg.callback_number = '2561234561'
		msg.save()
#		attachment = MessageAttachment()
#		attachment.size = '12'
#		attachment.save()
#		attachment.uuid
#		
		response = self.client.get(reverse('MHLogin.api.v1.views_messaging.getAttachment', 
			args=(msg.uuid, msg.uuid)), **self.extra)
		self.assertEqual(response.content, err_GE002().content, response.status_code)

#		response = self.client.post(reverse('MHLogin.api.v1.views_messaging.getAttachment', 
#			args=(msg.uuid, msg.uuid)), **self.extra)
#		self.assertEqual(response.status_code, 200, response.status_code)
#		msg = json.loads(response.content)
#		self.assertEqual(len(msg), 2)


class UpdateReferTest(APITest):
	def testUpdateRefer(self):
		provider = Provider(username="upretest", first_name="upre", 
								last_name="test", office_lat=0.0, office_longit=0.0)
		provider.set_password("maestro")
		provider.save()
		provider2 = Provider(username="doc holiday", first_name="doc", 
								last_name="holiday", office_lat=0.0, office_longit=0.0)
		provider2.set_password("holiday")
		provider2.save()
		sender = provider
		msg = Message(sender=sender, sender_site=None, subject="pandas")
		msg.urgent = False
		msg.message_type = 'NM'
		msg.callback_number = '2561234561'
		msg.save()
		body = "i am indeed a talking panda. how are you?"
		msg_body = MessageBody(message=msg, body=body)
		msg_body.save()
		refer = MessageRefer()
		refer.message = msg
		refer.first_name = 'msg'
		refer.middle_name = 'refer'
		refer.last_name = 'again'
		refer.gender = 'M'
		refer.status = 'NO'
		refer.phone_number = 8529631475
		refer.alternative_phone_number = 1472583695
		refer.save()
		msgRe = MessageRecipient()
		msgRe.message = msg
		msgRe.user = provider2
		msgRe.save()

		generate_keys_for_users(output=DevNull())

		VMBox_Config(owner=provider).save()
		VMBox_Config(owner=provider2).save()

		response = self.client.get(reverse(
				'MHLogin.api.v1.views_messaging.updateRefer', args=(refer.uuid,)), **self.extra)
		self.assertEqual(response.content, err_GE002().content, response.status_code)

		response = self.client.post(reverse(
				'MHLogin.api.v1.views_messaging.updateRefer', args=(refer.uuid,)), \
				data={'status': 'NO'}, **self.extra)
		self.assertEqual(response.status_code, 200, response.status_code)
		m = json.loads(response.content)
		self.assertEqual(len(m), 2)

