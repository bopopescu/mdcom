import time
import datetime
from pytz import timezone

from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.test import TestCase, Client
from django.conf import settings

from MHLogin.MHLUsers.models import Provider, MHLUser, OfficeStaff, Administrator
from MHLogin.DoctorCom.Messaging.models import Message, MessageBody, MessageRecipient, MessageAttachment,\
	MessageActionHistory, ACTION_TYPE_OPTION_OPEN, ACTION_TYPE_OPTION_RESOLVE,\
	ACTION_TYPE_OPTION_UNRESOLVE
from MHLogin.DoctorCom.Messaging import models
from MHLogin.KMS.exceptions import KeyInvalidException
from MHLogin.KMS.utils import store_user_key, generate_keys_for_users
from MHLogin.KMS.shortcuts import encrypt_object
from MHLogin.KMS.models import OwnerPublicKey, UserPrivateKey, EncryptedObject
from MHLogin.DoctorCom.IVR.models import VMBox_Config
from MHLogin.MHLPractices.models import PracticeLocation
from MHLogin.DoctorCom.Messaging.views_ajax import _get_system_time_as_tz
from pytz.exceptions import UnknownTimeZoneError
from MHLogin.DoctorCom.Messaging.utils_new_message import createNewMessage
from MHLogin.DoctorCom.Messaging.exceptions import InvalidRecipientException


class DevNull():
	write = lambda self, s: None
	flush = lambda self: None


class CalledTest(object):
	def __init__(self):
		self.was_called = False

	def __call__(self, *args, **kwargs):
		self.kwargs = kwargs
		self.args = args
		self.was_called = True


class MessageTests(TestCase):
	@classmethod
	def setUpClass(cls):
		cls.request = Client()
		pl = PracticeLocation.objects.create(practice_lat=0.0, practice_longit=0.0)
		cls.provider = Provider(username="tmeister", first_name="tester", 
								last_name="meister", office_lat=0.0, office_longit=0.0)
		cls.provider.set_password("maestro")
		cls.provider.save()
		cls.provider2 = Provider(username="docholiday", first_name="doc", 
								last_name="holiday", office_lat=0.0, office_longit=0.0)
		cls.provider2.set_password("holiday")
		cls.provider2.save()
		cls.userm = MHLUser(username="imanager", first_name="important", 
							last_name="manager", is_active=True)
		cls.userm.set_password("monkey")
		cls.userm.save()

		cls.userstaff = OfficeStaff(current_practice=pl)
		cls.userstaff.user = cls.userm
		cls.userstaff.save()
		adminguy = MHLUser(username="superduper", first_name="super", 
							last_name="duper", is_active=True)
		adminguy.set_password("crackerjax")
		adminguy.save()
		cls.adminguy = Administrator.objects.create(user=adminguy)
		generate_keys_for_users(output=DevNull())
		# needed by our login

		VMBox_Config(owner=cls.provider).save()
		VMBox_Config(owner=cls.provider2).save()
		VMBox_Config(owner=cls.userstaff).save()

	@classmethod
	def tearDownClass(cls):
		try:
			cls.provider.delete()
			cls.provider2.delete()
			cls.userm.delete()
			cls.adminguy.user.delete()
			cls.adminguy.delete()
			cls.userstaff.delete()
			PracticeLocation.objects.all().delete()
			OwnerPublicKey.objects.all().delete()
			UserPrivateKey.objects.all().delete()
			EncryptedObject.objects.all().delete()
		except AssertionError:
			# due to the nature of our unittests we should use setup/teardown 
			# and not the class setup/teardown
			pass

	def test_normal_message(self):
		self.request.post('/login/', {'username': self.provider.username, 'password': 'maestro'})
		sender = authenticate(username=self.provider.username, password='maestro')
		msg = Message(sender=sender, sender_site=None, subject="pandas")
		recipient = User.objects.get(id=self.provider2.id)		
		msg.urgent = False
		msg.message_type = 'NM'
		self.assertRaises(Exception, msg.save_body, '')
		msg.save()
		body = "i am indeed a talking panda. how are you?"
		msg_body = msg.save_body(body)
		MessageRecipient(message=msg, user=recipient).save()

		test = CalledTest()
		models.sendSMS_Twilio_newMessage = test
		msg.send(self.request, msg_body, [])
		self.assertTrue(test.was_called)

		self.assertTrue(Message.objects.filter(sender=sender, subject="pandas").exists())
		self.assertTrue(MessageRecipient.objects.filter(message=msg, user=recipient).exists())
		msg_body.delete()
		clean_msg_body = MessageBody.objects.get(pk=msg_body.pk)
		self.request.logout()

		self.assertEqual(msg_body.decrypt(self.request), body)
		response = self.request.post('/login/', {'username': self.provider2.username, 'password': 'holiday'})
		self.request.user = authenticate(username=self.provider2.username, password='holiday')
		self.request.COOKIES = {'ss': response.cookies['ss'].value}
		try:
			self.assertEqual(clean_msg_body.decrypt(self.request), body)
		except KeyInvalidException:
			raise self.failureException("message body decryption failed")

		self.assertRaises(Exception, msg.save)

		self.assertRaises(Exception, msg.delete, self.request)
		self.assertRaises(Exception, msg.send, self.request, msg_body, [])
		self.request.logout()

	def test_bad_password(self):
		self.request.post('/login/', {'username': self.provider.username, 'password': 'maestro'})
		sender = authenticate(username=self.provider.username, password='maestro')
		msg = Message(sender=sender, sender_site=None, subject="pandas")
		recipient = User.objects.get(id=self.provider2.id)
		msg.urgent = False
		msg.message_type = 'NM'
		msg.save()
		body = "i am indeed a talking panda. how are you?"
		msg_body = msg.save_body(body)
		MessageRecipient(message=msg, user=recipient).save()
		self.request.logout()

		test = CalledTest()
		models.sendSMS_Twilio_newMessage = test
		msg.send(self.request, msg_body, [])
		self.assertTrue(test.was_called)

		response = self.request.post('/login/', {'username': self.provider2.username, 'password': 'holiday'})
		clean_msg_body = MessageBody.objects.get(message=msg)
		self.request.user = recipient
		store_user_key(self.request, response, 'wrongpassword')
		self.request.COOKIES = {'ss': response.cookies['ss'].value}
		self.assertRaises(KeyInvalidException, clean_msg_body.decrypt, self.request)
		self.request.logout()

	def test_system_message(self):
		self.request.post('/login/', {'username': self.provider.username, 'password': 'maestro'})
		provider = authenticate(username=self.provider.username, password='maestro')

		msg = Message(sender=None, sender_site=None, subject="I'm in space!", message_type='ANS')
		msg.save()
		recipient = User.objects.get(id=self.provider2.id)		
		MessageRecipient(user=recipient, message=msg).save()
		body = 'SPACE!'
		msg_body = msg.save_body(body)
		path = ''.join([settings.MEDIA_ROOT, 'audio/fetch_error.wav'])
		wav_data = open(path, "r").read()
		attachment = encrypt_object(
			MessageAttachment,
			{
				'message': msg,
				'size': len(wav_data),
				'encrypted': True,
			})

		self.request.user = provider
		attachment.encrypt_url(self.request, ''.join(['file://', attachment.uuid]))
		attachment.encrypt_filename(self.request, "i'm in space")
		attachment.encrypt_file(self.request, [wav_data])
		attachment.suffix = 'wav'
		attachment.content_type = 'audio/wav'
		attachment.save()

		test = CalledTest()
		models.sendSMS_Twilio_newMessage = test
		msg.send(self.request, msg_body, [attachment])
		self.assertTrue(test.was_called)
		self.request.logout()

		response = self.request.post('/login/', {'username': 
					self.provider2.username, 'password': 'holiday'})
		recipient = authenticate(username=self.provider2.username, password='holiday')

		self.request.user = recipient
		self.request.COOKIES = {'ss': response.cookies['ss'].value}

		clean_attachment = MessageAttachment.objects.get(pk=attachment.pk)
		clean_attachment.get_file(self.request, response)

		self.assertEqual(response.content, wav_data) 
		self.assertTrue(clean_attachment.decrypt_url(self.request))
		self.assertRaises(Exception, clean_attachment.delete, self.request)
		self.request.logout()

	def test_self_message(self):
		self.request.post('/login/', {'username': self.provider.username, 'password': 'maestro'})
		sender = authenticate(username=self.provider.username, password='maestro')
		msg = Message(sender=sender, sender_site=None, subject="this was a triumph")
		recipient = sender
		msg.urgent = False
		msg.message_type = 'NM'
		msg.save()
		body = "i'm making a note here: huge success"
		msg_body = msg.save_body(body)
		MessageRecipient(message=msg, user=recipient).save()

		self.request.user = recipient
		test = CalledTest()
		models.sendSMS_Twilio_newMessage = test
		msg.send(self.request, msg_body, [])
		self.assertTrue(test.was_called)
		self.request.logout()

	def test_invalid_recipient(self):
		self.request.post('/login/', {'username': self.provider.username, 'password': 'maestro'})
		sender = authenticate(username=self.provider.username, password='maestro')
		msg = Message(sender=sender, sender_site=None, subject="this was a triumph")
		recipient = None
		msg.urgent = False
		msg.message_type = 'NM'
		msg.save()
		body = "i'm making a note here: huge success"
		msg_body = msg.save_body(body)
		self.assertRaises(ValueError, MessageRecipient, message=msg, user=recipient)
		self.assertRaises(InvalidRecipientException, msg.send, self.request, msg_body, [])
		self.request.logout()


class GetSystemTimeAsTzTest(TestCase):

	def setUp(self):
		self.TIMEZOME = settings.TIME_ZONE
		settings.TIME_ZONE = "America/Los_Angeles"

	def test_get_system_time_as_tz(self):
		t = datetime.datetime.now()
		origin = t
		expert = t - datetime.timedelta(hours=2)
		tz = timezone('Pacific/Honolulu')
		self.assertEqual(expert.strftime('%m/%d/%y %I:%M %p'),
						_get_system_time_as_tz(origin, tz).\
						strftime('%m/%d/%y %I:%M %p'))
		origin = t
		expert = t - datetime.timedelta(hours=2)
		tz = 'Pacific/Honolulu'
		self.assertEqual(expert.strftime('%m/%d/%y %I:%M %p'),
						_get_system_time_as_tz(origin, tz). \
						strftime('%m/%d/%y %I:%M %p'))
		origin = None
		expert = t - datetime.timedelta(hours=2)
		tz = 'Pacific/Honolulu'
		self.assertIsNone(_get_system_time_as_tz(origin, tz))
		origin = t
		expert = t - datetime.timedelta(hours=2)
		tz = 'Pacific/1234'
		with self.assertRaises(UnknownTimeZoneError): 
			_get_system_time_as_tz(origin, tz)

	def tearDown(self):	
		settings.TIME_ZONE = self.TIMEZOME


class MessageActionHistoryTest(TestCase):
	@classmethod
	def setUpClass(cls):
		cls.request = Client()
		pl = PracticeLocation.objects.create(practice_lat=0.0, practice_longit=0.0)
		cls.provider = Provider(username="tmeister", first_name="tester", 
								last_name="meister", office_lat=0.0, office_longit=0.0)
		cls.provider.set_password("maestro")
		cls.provider.save()
		cls.provider2 = Provider(username="docholiday", first_name="doc", 
								last_name="holiday", office_lat=0.0, office_longit=0.0)
		cls.provider2.set_password("holiday")
		cls.provider2.save()
		cls.userm = MHLUser(username="imanager", first_name="important", 
							last_name="manager", is_active=True)
		cls.userm.set_password("monkey")
		cls.userm.save()

		cls.userstaff = OfficeStaff(current_practice=pl)
		cls.userstaff.user = cls.userm
		cls.userstaff.save()
		generate_keys_for_users(output=DevNull())
		# needed by our login

		VMBox_Config(owner=cls.provider).save()
		VMBox_Config(owner=cls.provider2).save()
		VMBox_Config(owner=cls.userstaff).save()

	@classmethod
	def tearDownClass(cls):
		try:
			cls.provider.delete()
			cls.provider2.delete()
			cls.userm.delete()
			cls.userstaff.delete()
			PracticeLocation.objects.all().delete()
			OwnerPublicKey.objects.all().delete()
			UserPrivateKey.objects.all().delete()
			EncryptedObject.objects.all().delete()
		except AssertionError:
			# due to the nature of our unittests we should use setup/teardown 
			# and not the class setup/teardown
			pass

	def test_history(self):
		self.request.post('/login/', {'username': self.provider.username, 'password': 'maestro'})
		sender = authenticate(username=self.provider.username, password='maestro')

		test = CalledTest()
		models.sendSMS_Twilio_newMessage = test
		msg = createNewMessage(self.request, sender, self.provider,\
						[self.provider2.id], "i am indeed a talking panda. how are you?",\
						subject="pandas")
		self.assertTrue(test.was_called)

		# test read history
		new_history = MessageActionHistory.get_action_history(msg, sender,\
							ACTION_TYPE_OPTION_OPEN)
		self.assertIsNone(new_history)
		timestamp1 = int(time.time())
		timestamp2 = int(time.time())
		history1 = MessageActionHistory.create_read_history(msg, sender,\
							timestamp=timestamp1)
		history2 = MessageActionHistory.create_read_history(msg, sender,\
							timestamp=timestamp2)
		new_history = MessageActionHistory.get_action_history(msg, sender,\
							ACTION_TYPE_OPTION_OPEN)
		self.assertIsNotNone(new_history)
		self.assertEqual(new_history, history1)
		self.assertEqual(new_history, history2)
		self.assertEqual(new_history.timestamp, timestamp1)
		self.assertEqual(new_history.type, ACTION_TYPE_OPTION_OPEN)

		# test resolve history
		new_re_history = MessageActionHistory.get_action_history(msg, sender,\
							ACTION_TYPE_OPTION_RESOLVE)
		new_ur_history = MessageActionHistory.get_action_history(msg, sender,\
							ACTION_TYPE_OPTION_UNRESOLVE)
		self.assertIsNone(new_re_history)
		self.assertIsNone(new_ur_history)

		history1 = MessageActionHistory.create_resolve_history(msg, sender,\
					timestamp=timestamp1)
		history2 = MessageActionHistory.create_resolve_history(msg, sender,\
					timestamp=timestamp2)
		new_re_history = MessageActionHistory.get_action_history(msg, sender,\
							ACTION_TYPE_OPTION_RESOLVE)
		new_ur_history = MessageActionHistory.get_action_history(msg, sender,\
							ACTION_TYPE_OPTION_UNRESOLVE)
		self.assertIsNotNone(new_re_history)
		self.assertIsNone(new_ur_history)
		self.assertEqual(new_re_history, history1)
		self.assertEqual(new_re_history, history2)
		self.assertEqual(new_re_history.timestamp, timestamp2)
		self.assertEqual(new_re_history.type, ACTION_TYPE_OPTION_RESOLVE)

		# test unresolve history
		history1 = MessageActionHistory.create_resolve_history(msg, sender,\
						resolve=False, timestamp=timestamp1)
		history2 = MessageActionHistory.create_resolve_history(msg, sender,\
						resolve=False, timestamp=timestamp2)
		new_re_history = MessageActionHistory.get_action_history(msg, sender,\
							ACTION_TYPE_OPTION_RESOLVE)
		new_ur_history = MessageActionHistory.get_action_history(msg, sender,\
							ACTION_TYPE_OPTION_UNRESOLVE)
		self.assertIsNone(new_re_history)
		self.assertIsNotNone(new_ur_history)
		self.assertEqual(new_ur_history, history1)
		self.assertEqual(new_ur_history, history2)
		self.assertEqual(new_ur_history.timestamp, timestamp2)
		self.assertEqual(new_ur_history.type, ACTION_TYPE_OPTION_UNRESOLVE)

		self.request.logout()
