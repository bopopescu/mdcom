
import base64
import cPickle
from Crypto.Cipher import AES
import datetime
import time

from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.contrib.contenttypes.models import ContentType
from django.db.utils import IntegrityError
from django.db import models
from django.http import HttpResponse
from django.utils.translation import ugettext_lazy as _

from MHLogin.KMS.exceptions import KeyInvalidException
from MHLogin.KMS.shortcuts import encrypt_object, gen_keys_for_users, \
	regen_invalid_keys_for_users, check_keys_exist_for_users, decrypt_cipherkey
from MHLogin.KMS.models import OwnerPublicKey
from MHLogin.MHLUsers.models import Provider, MHLUser, GENDER_CHOICES, OfficeStaff
from MHLogin.MHLSites.models import Site
from MHLogin.DoctorCom.views import send_page
from MHLogin.DoctorCom.IVR.models import VMBox_Config
from MHLogin.DoctorCom.SMS.views import sendSMS_Twilio_newMessage
from MHLogin.apps.smartphone.models import SmartPhoneAssn
from MHLogin.apps.smartphone.v1.utils import notify
from exceptions import InvalidRecipientException
from MHLogin.MHLPractices.models import PracticeLocation

from MHLogin.utils.admin_utils import mail_admins
from MHLogin.utils.fields import UUIDField, MHLPhoneNumberField
from MHLogin.utils.mh_logging import get_standard_logger
from MHLogin.utils.storage import get_file, create_file

from smtplib import SMTPException

# Setting up logging
logger = get_standard_logger('%s/DoctorCom/Messaging/models.log' % (settings.LOGGING_ROOT), 
							'DoctorCom.Messaging.models', settings.LOGGING_LEVEL)


MESSAGE_RELATION_CHOICES = (
	('RE', _('Reply')),
	('FW', _('Forward')),
)

MESSAGE_TYPES = (
	("ANS", _("Answering Service")),
	("NM", _("Normal")),
	("SMS", _("Text Message")),
	("VM", _("Voice Mail")),
	("RF", _("Referral")),
)

VMSTATUS_CHOICES = (
	('U', _('Unconfirmed')),
	('C', _('Confirmed')),
	('R', _('Recording Saved')),
)


class Message(models.Model):
	"""
	The standard message object that users send to each other. Note that this is 
	a *secure* message object in that the bodies of the messages are encrypted.

	Usage:
	1. Instantiate it normally, populating the sender, sender_site, and subject, at a minimum.
	2. Save the message object.
	3. Call message_object.save_body() to create the sender's copy.
	4. Set the recipients of the message. (must come after #2 due to the way many-to-many 
		relations work in Django)
	5. Call message.send().

	At this point, you can stop if you want to keep the message as a draft. To send the message
	"""	

	# id = models.AutoField(primary_key=True)
	uuid = UUIDField(auto=True, primary_key=False)
	thread_uuid = UUIDField(auto=True, primary_key=False, null=True)

	sender = models.ForeignKey(User, null=True, related_name="message_sender", db_index=True)
	recipients = models.ManyToManyField(User, through='MessageRecipient', 
								related_name="message_recipients")
	ccs = models.ManyToManyField(User, through='MessageCC', 
								related_name="message_ccs")

	urgent = models.BooleanField(default=False)
	_resolved_by = models.ForeignKey(User, null=True, related_name="message__resolved_by")
	resolution_timestamp = models.PositiveIntegerField(default=0)

	# Bookkeeping
	draft = models.BooleanField(default=True)
	send_timestamp = models.PositiveIntegerField(default=0, db_index=True)  # GMT
	sender_site = models.ForeignKey(Site, null=True)

	subject = models.CharField(max_length=1024, blank=True)

	related_message = models.ForeignKey('Message', null=True)
	related_message_relation = models.CharField(max_length=2, choices=MESSAGE_RELATION_CHOICES)

	message_type = models.CharField(max_length=3, choices=MESSAGE_TYPES, default="NM")
	callback_number = MHLPhoneNumberField()

	vmstatus = models.CharField(choices=VMSTATUS_CHOICES, default='U', max_length=1)

	objects = models.Manager()

	def save_body(self, body):
		if (not self.uuid):
			raise Exception(_('Body cannot be saved until the message has been saved. '
							'This is because the body has a ForeignKey back to the '
							'Message, which must be saved to be defined.'))
		body_obj = encrypt_object(
			MessageBody,
			{
				'user': self.sender,
				'message': self
			},
			cleartext=body,
			opub=self.sender and OwnerPublicKey.objects.get_pubkey(owner=self.sender))
		return body_obj

	def send(self, request, body_obj, attachment_objs=[], refer_objs=[]):
		"""
		Send this message. Note that this also saves the message automatically! Do NOT call 
		save on this object afterward!

		Requirements:
			1. You have to have run the save_body method to create a MessageBody object for the sender.

		Arguments:
			request: The standard Django HttpRequest object. This is required for decryption 
			of the body, if the optional body argument is omitted.
		"""
		# Disallow send of messages that have already been sent
		if (not self.draft):
			raise Exception(_('Trying to send a message that\'s already been sent.'))		
		# Generate a list of recipients, merging CCs and whatnot.
		all_recipients = list(self.recipients.all())
		all_recipients.extend(list(self.ccs.all()))
		recipients = list(self.recipients.all())
		if(not recipients):
			raise InvalidRecipientException(_("At least one recipient is required"))
		non_sender_recipients = [user for user in all_recipients if user.pk != 
								(self.sender.pk if self.sender else None)] 
		# remove the sender from the list of recipients to generate keys for

		# First, generate copies of the private key for the body of this message, except for the sender.
		ivr = self.message_type in ('VM', 'ANS')
		gen_keys_for_users(body_obj, non_sender_recipients, body_obj._key, request, ivr)

#		smartphones = SmartPhoneAssn.objects.filter(user__in=all_recipients)
		smartphones = SmartPhoneAssn.objects.filter(user__in=all_recipients, is_active=True).\
			exclude(push_token=None).exclude(push_token='')
		# Secondly, for each recipient, generate a new message user status object so that 
		# the message status (read, deleted, etc.) can be stored for that user.
		for recipient in non_sender_recipients:
			s = MessageBodyUserStatus(msg_body=body_obj, user=recipient)
			s.save()
#		notified_recipients = non_sender_recipients
#		
#		#sender is messeging himself, send a notification
#		if(not notified_recipients):
#			notified_recipients = [self.sender]
#		notified_recipients = MHLUser.objects.filter(id__in=[u.id for u in notified_recipients])
		notified_recipients = MHLUser.objects.filter(id__in=[u.id for u in all_recipients])
		for recipient in notified_recipients:
			if (self.message_type in ('ANS', 'VM', 'NM', 'SMS')):
				qs = smartphones.filter(user=recipient)
				if(qs):
					from utils import get_message_count
					if(self.sender):
						text = _("You have a new DoctorCom message from %(sender)s: %(subject)s") \
								% {'sender': self.sender, 'subject': self.subject}
					else:
						text = _("You have a new DoctorCom message: %s") % (self.subject,)
					try:
						notify(qs,
							text=text,
							additional_data={"message_id": self.uuid},
							count=get_message_count(recipient, None,
									read_flag=False, direction='received'))
					except Exception as e:
						err_email_body = '\n'.join([
								('notify mobile has errors!'),
								''.join(['Server: ', settings.SERVER_ADDRESS]),
								''.join(['Session: ', str(request.session.session_key)]),
								''.join(['Message: ', ('Notify mobile has errors.')]),
								''.join(['Exception: ', str(e)]),
								''.join(['Exception data: ', str(e.args)]),
							])
						mail_admins('notify mobile has errors', err_email_body)
				if(settings.CALL_ENABLE):
					config_type = ContentType.objects.get(app_label="MHLUsers", model="provider")
					config = VMBox_Config.objects.filter(
								owner_type__pk=config_type.id, owner_id=recipient.id)
					#always send a notification to providers (the query above only matches providers)
					#send a notification if we didn't send a push notification (not qs) or if the
					#user has explicitly asked for sms notifications
					if(config and (not qs or config[0].notification_sms)):
						sendSMS_Twilio_newMessage(request, body_obj.clear_data, 
										attachment_objs, self, recipient)

					if not config:
						config_type = ContentType.objects.get(app_label="MHLUsers", model="officestaff")
						staff = OfficeStaff.objects.filter(user=recipient)
						if staff and staff[0].id:
							config = VMBox_Config.objects.filter(
								owner_type__pk=config_type.id, owner_id=staff[0].id)
					if (config and config[0].notification_email):
						try:
							subject = "New DoctorCom System Message"
							body = "You've received a DoctorCom system message."
							if (self.sender):
								#sender_name = ' '.join(['New DoctorCom Message from', 
								#	self.sender.first_name, self.sender.last_name,])
								body = ' '.join(['You received a DoctorCom message from', 
									self.sender.first_name, self.sender.last_name])
							send_mail(
									subject,
									body,
									settings.SERVER_EMAIL,
									[user.email],
									fail_silently=False
								)
						except SMTPException as e:
							import inspect
							mail_admins('Mail Send Error', '%s\n%s' % (e, inspect.trace(),))

			if (self.message_type == 'ANS' and self.urgent and settings.CALL_ENABLE):

				config_type = ContentType.objects.get(app_label="MHLUsers", model="Provider")
				config = VMBox_Config.objects.filter(owner_id=recipient.id, owner_type=config_type)

				if(config and config[0].notification_page):
					paged = Provider.objects.get(user=recipient)
					if (paged.pager):
						send_page(self.sender, paged, self.callback_number)

		# Thirdly, generate keys for all attachments.
		for attach in attachment_objs:
			gen_keys_for_users(attach, non_sender_recipients, attach._key, request, ivr)

		for refer in refer_objs:
			gen_keys_for_users(refer, non_sender_recipients, refer._key, request, ivr)

		# Book keeping
		self.draft = False
		self.send_timestamp = time.time()
		# DEBUG: Temporarily disabled the following lines.
		#if ('Provider' in request.session['MHL_Users']):
		#	self.sender_site = request.session['MHL_Users']['Provider'].current_site

		# Save book keeping changes. Note that we don't use self.save since that
		# will choke on self.draft == False.
		super(Message, self).save()

		# Site Analytics
		from ..models import SiteAnalytics
		try:
			siteStat = SiteAnalytics.objects.get(dateoflog=datetime.date.today(), 
						site=self.sender_site)
		except SiteAnalytics.DoesNotExist:
			siteStat = SiteAnalytics(dateoflog=datetime.date.today(), 
				site=self.sender_site, countPage=0, countMessage=0, countClick2Call=0)
			siteStat.save()
		siteStat.countMessage = models.F('countMessage') + 1
		siteStat.save()

#			for user in all_recipients:
#				
#				config_type = ContentType.objects.get(app_label="MHLUsers", model="provider")
#				config = VMBox_Config.objects.get(owner_type__pk=config_type.id,  owner_id=user.id)
#				# Notify the user about messages
#				if (config.notification_email):
#					try:
#						subject = "New DoctorCom System Message"
#						body = "You've received a DoctorCom system message."
#						if (self.sender):
#							sender_name = ' '.join(['New DoctorCom Message from', 
#								self.sender.first_name, self.sender.last_name,])
#							body = ' '.join(['You received a DoctorCom message from', 
#								self.sender.first_name, self.sender.last_name,])
#						send_mail(
#								subject,
#								body,
#								settings.SERVER_EMAIL,
#								[user.email],
#								fail_silently=False
#							)
#					except SMTPException as e:
#						mail_admins('Mail Send Error', '%s\n%s'%(e, inspect.trace(),))
#				if (config.notification_sms):
#					sendSMS_Twilio_newMessage(request, form.cleaned_data['body'], attachments, msg)

	def delete(self, request):
		raise Exception(_('Deletion of message objects is disallowed. If you wish to '
				'hide these objects, make sure you delete the correct MessageBody objects.'))

		#bodies = MessageBody.objects.filter(message=self, owner=request.user)
		#bodies.delete()
		#attachments = MessageAttachment.objects.filter(message=self, owner=request.user)
		#attachments.delete()

	def save(self, *args, **kwargs):
		if (not self.draft):
			raise Exception(_('Trying to save a message that\'s already been sent.'))
		super(Message, self).save(*args, **kwargs)

	def __unicode__(self):
		return "Message from %s to %s" % \
				(self.sender, ', '.join([str(i) for i in self.recipients.all()]))

	def set_resolved_by(self, user):
		self._resolved_by = user
		self.resolution_timestamp = int(time.time())
		super(Message, self).save()
		return self._resolved_by

	def get_resolved_by(self):
		return self._resolved_by

	resolved_by = property(get_resolved_by, set_resolved_by)

	class Meta:
		ordering = ['-send_timestamp']


class MessageRecipient(models.Model):
	message = models.ForeignKey(Message)
	user = models.ForeignKey(User)

	class Meta():
		# The below is necessary because this many-to-many relationship was
		# defined as a generic Django many-to-many relationship, which was then
		# broken out into this class in order to speed SQL queries involving
		# this many-to-many relation.
		db_table = 'Messaging_message_recipients'


class MessageCC(models.Model):
	message = models.ForeignKey(Message)
	user = models.ForeignKey(User)

	class Meta():
		# The below is necessary because this many-to-many relationship was
		# defined as a generic Django many-to-many relationship, which was then
		# broken out into this class in order to speed SQL queries involving
		# this many-to-many relation.
		db_table = 'Messaging_message_ccs'


class MessageContent(models.Model):
	"""
	Abstract class for content (textual body/attachments for now) for a Message.

	Usage:
		Initialization:
			Typical for a Django object. However, a django.contrib.auth.models
			User object is REQUIRED as the first argument.
		Read/Delete Flags:

	"""

	message = models.ForeignKey(Message)

	# Don't forget to implement the below methods in your child class of this
	# class. The KMS codebase expects them.
	# def encrypt(self, data, key):
	# def decrypt(self, key):
	# def __unicode__(self):

	# Runtime variables:
	# The below _key instance variable should cache the private key for this
	# object. It's desirable because we can access the secured contents of this
	# object multiple times in a view, and we don't want to have to keep getting
	# the private key every time. This value should NEVER be a Django models.*
	# field type so that it never gets placed into the database.
	_key = None

	def save(self, *args, **kwargs):
		if (not self.message.draft):
			raise Exception(_('Trying to save a message that\s already been sent.'))
		super(MessageContent, self).save(*args, **kwargs)

	class Meta:
		abstract = True
		ordering = ['-message__send_timestamp']


class MessageBodyUserStatus(models.Model):
	user = models.ForeignKey(User)
	msg_body = models.ForeignKey('MessageBody')

	read_flag = models.BooleanField(default=False)
	read_timestamp = models.PositiveIntegerField(default=0)

	delete_flag = models.BooleanField(default=False)
	delete_timestamp = models.PositiveIntegerField(default=0)

	resolution_flag = models.BooleanField(default=False)
	resolution_timestamp = models.PositiveIntegerField(default=0)

	def decrypt(self, request, key=None, ivr=False):
		self.msg_body._set_status_obj(self)
		return self.msg_body.decrypt(request, key, ivr)

	def delete(self):
		self.delete_flag = True
		self.delete_timestamp = time.time()
		self.save()

	def __unicode__(self):
		return 'User Status for user %s %s for message %s' % (
				self.user.first_name, self.user.last_name, self.msg_body.message.uuid)

	class Meta():
		unique_together = (('user', 'msg_body',),)
		verbose_name_plural = "Message Body Users Status"


class MessageBody(MessageContent):
	body = models.TextField()

	# The _status variable is used to cache the MessageContentUserStatus object
	# for this instance, so that we only ever need to grab it once per request.
	_status = None

	# To use the following instance variables, use the self.read_flag or 
	# self.delete_flag accessors. For example:
	#      m = MessageBody.objects.get(id=1)
	#      if (not m.read_flag):
	#          m.read_flag = True
	# Usage of the delete flag is similar. Note that use of the accessors is
	# dependent upon:
	#    1. Definition of the self.user instance variable, to the user for
	#       which this request is being processed.
	#    2. The MessageContent record *must* be saved before these values are
	#       accessed. This is because the read_flag and delete_flag values are
	#       actually kept in the MessageContentUserStatus object, which requires
	#       the MessageContent object to have a valid id.
	#    3. The self.user value *must* be defined to be the user for whom we are
	#       servicing this request. You may define this either on object init,
	#       or by defining it manually before accessing the read/delete flags.
	# Additionally, you cannot use these values in QuerySet filter calls. If you
	# need to filter on read/delete flags, you need to run something akin to:
	#    MessageBody.objects.filter(messagebodyuserstatus__deleted=False)
	# See http://docs.djangoproject.com/en/1.1/topics/db/queries/#lookups-that-span-relationships
	# for more details
	__read_flag = None
	__delete_flag = None
	__resolution_flag = None

	# The user field should keep track of which user this instance is handling a 
	# response for. When you initialize this object, this will generally be the
	# message sender.
	user = None

	# The decrypted contents of this object
	clear_data = None

	def __init__(self, *args, **kwargs):
		"""
		Initialization has additional required kwarg /user/ IFF this is a new
		object that's being instantiated. The user object should be the user
		for which we're handling the response.
		"""
		user_temp = 'user' in kwargs
		if (user_temp):
			user_temp = kwargs['user']
			del kwargs['user']

		super(MessageBody, self).__init__(*args, **kwargs)

		if (self.id == None):
			#if (not user_temp):
			#	raise Exception('Keyword argument user is required. See documentation' 
			#      'for self.user for which user to assign.')
			self.user = user_temp

	def save(self, *args, **kwargs):
		super(MessageBody, self).save(*args, **kwargs)
		if (self._status):
			self._status.save()
		elif (self.user):
			try:
				self._status = MessageBodyUserStatus.objects.get(msg_body=self, user=self.user)
			except models.ObjectDoesNotExist:
				self._status = MessageBodyUserStatus(msg_body=self, user=self.user)
				self._status.save()

	def encrypt(self, data, key):
		data = data.encode('utf-8')
		self.clear_data = data

		padded_data = [' ' for i in range((16 - (len(data) % 16)) % 16)]
		padded_data.insert(0, data)
		padded_data = ''.join(padded_data)

		a = AES.new(key)
		self.body = a.encrypt(padded_data)
		self.body = cPickle.dumps(self.body)
		self.body = base64.b64encode(self.body)

	def decrypt(self, request, key=None, ivr=False):
		if (self.clear_data):
			return self.clear_data

		key = key or decrypt_cipherkey(request, self, ivr)
		if (not self.user):
			self.user = request.user

		# TODO, make this function have single responsibility, move the
		# following two lines to read_message
		if (self.read_flag == False):
			self.read_flag = True

		a = AES.new(key)
		body = base64.b64decode(self.body)
		try:
			body = cPickle.loads(body)
		except Exception:
			raise KeyInvalidException()
		self.clear_data = a.decrypt(body).rstrip().decode('utf-8')  # strip trailing spaces
		return self.clear_data

	def delete(self):
		self.set_delete_flag(True)

	def get_read_flag(self):
		if (self.__read_flag != None):
			return self.__read_flag
		if (not self.id):
			raise Exception(_('Access to the read_flag requires the MessageContent '
							'object to be saved first.'))
		if (not self.user):
			raise Exception(_('MessageBody objects MUST have a user defined in order '
							'to have a valid read_flag value.'))

		if (not self._status):
			self._status = MessageBodyUserStatus.objects.get(msg_body=self, user=self.user)
		self.__read_flag = self._status.read_flag
		return self.__read_flag

	def set_read_flag(self, value):
		if (not self.id):
			raise Exception(_('Access to the read_flag requires the MessageContent '
							'object to be saved first.'))
		if (not self.user):
			raise Exception(_('MessageBody objects MUST have a user defined in order to '
							'have a valid read_flag value.'))
		if (value != True and value != False):
			raise Exception(_('The read_flag may only be set to True or False.'))

		if (not self._status):
			self._status = MessageBodyUserStatus.objects.get(message_content=self, user=self.user)

		if (not self._status.read_flag):
			self._status.read_flag = value
			if (not self._status.read_timestamp):
				self._status.read_timestamp = int(time.time())
			self.__read_flag = True
			self._status.save()

	read_flag = property(get_read_flag, set_read_flag)

	def get_delete_flag(self):
		if (self.__delete_flag != None):
			return self.__delete_flag
		if (not self.id):
			raise Exception(_('Access to the delete_flag requires the '
							'MessageContent object to be saved first.'))
		if (not self.user):
			raise Exception(_('MessageBody objects MUST have a user defined '
							'in order to have a valid delete_flag value.'))

		if (not self._status):
			self._status = MessageBodyUserStatus.objects.get(message_content=self, user=self.user)
		self.__delete_flag = self._status.delete_flag
		return self.__delete_flag

	def set_delete_flag(self, value):
		if (not self.id):
			raise Exception(_('Access to the delete_flag requires the '
							'MessageContent object to be saved first.'))
		if (not self.user):
			raise Exception(_('MessageBody objects MUST have a user defined in '
							'order to have a valid delete_flag value.'))
		if (value != True and value != False):
			raise Exception(_('The delete_flag may only be set to True or False.'))

		if (not self._status):
			self._status = MessageBodyUserStatus.objects.get(message_content=self, user=self.user)

		if (not self._status.delete_flag):
			self._status.delete_flag = value
			if (not self._status.delete_timestamp):
				self._status.delete_timestamp = int(time.time())
			self.__delete_flag = True
			self._status.save()

	delete_flag = property(get_delete_flag, set_delete_flag)

	def get_resolution_flag(self):
		if (self.__resolution_flag != None):
			return self.__resolution_flag
		if (not self.id):
			raise Exception(_('Access to the resolution_flag requires the '
							'MessageContent object to be saved first.'))
		if (not self.user):
			raise Exception(_('MessageBody objects MUST have a user defined in '
							'order to have a valid resolution_flag value.'))

		if (not self._status):
			self._status = MessageBodyUserStatus.objects.get(message_content=self, user=self.user)
		self.__resolution_flag = self._status.resolution_flag
		return self.__resolution_flag

	def set_resolution_flag(self, value):
		if (not self.id):
			raise Exception(_('Access to the resolution_flag requires the '
							'MessageContent object to be saved first.'))
		if (not self.user):
			raise Exception(_('MessageBody objects MUST have a user defined '
							'in order to have a valid resolution_flag value.'))
		if (value != True or value != False):
			raise Exception(_('The resolution_flag may only be set to True or False.'))

		if (not self._status):
			self._status = MessageBodyUserStatus.objects.get(message_content=self, user=self.user)

		if (not self._status.resolution_flag):
			self._status.resolution_flag = value
			if (not self._status.resolution_timestamp):
				self._status.resolution_timestamp = int(time.time())
			self.__resolution_flag = True

	resolution_flag = property(get_resolution_flag, set_resolution_flag)

	def _set_status_obj(self, status_obj):
		self._status = status_obj

	def __unicode__(self):
		return "Message body for msg id %s" % (str(self.message.pk),)

	class Meta:
		verbose_name_plural = "Message Body"


class MessageAttachment(MessageContent):
	# id = models.AutoField(primary_key=True)
	uuid = UUIDField(auto=True, primary_key=False, db_index=True)

	filename = models.TextField()
	url = models.TextField()

	encrypted = models.BooleanField(default=False)

	content_type = models.CharField(max_length=255, null=True)  # mime type
	encoding = models.CharField(max_length=255, null=True)
	charset = models.CharField(max_length=255, null=True)
	suffix = models.CharField(max_length=255, null=True)

	size = models.PositiveIntegerField()  # Size in bytes
	metadata = models.CharField(max_length=255, blank=True)

	# The below values should cache the decrypted contents for this object. We
	# want to cache decrypted data if it exists since we may need to access the
	# data multiple times in a single response. This value should NEVER be a 
	# Django models.* field type so that it never gets placed into the database.
	_filename = None
	_url = None

	def encrypt(self, data, key):
		# Don't do anything -- encryption for these objects happens after the
		# object is created and saved.
		return

	def decrypt(self, request, key, ivr=False):
		"""
		Decrypts and returns the url of the object. To get the URL, you
		need to use KMS.utils.decrypt_cipherkey.
		"""
		if (self._url):
			return self._url
		if (not self._key):
			if (not key and not request):
				raise Exception(_("Decryption requires either a key or the HttpRequest object!"))

			self._key = key or decrypt_cipherkey(request, self, ivr)

		# Mark the message as read.
		if (self.read_flag == False):
			self.read_flag = True
			self.read_timestamp = int(time.time())
			self.save()

		a = AES.new(self._key)
		url = base64.b64decode(self.url)
		try:
			url = cPickle.loads(url)
		except Exception:
			raise KeyInvalidException()
		self._url = a.decrypt(url)
		return self._url

	def encrypt_filename(self, request, filename, key=None):
		if (not self._key):
			self._key = key or decrypt_cipherkey(request, self)

		filename = filename.encode('utf-8')
		padded_filename = [' ' for i in range((16 - (len(filename) % 16)) % 16)]
		padded_filename.insert(0, filename)
		padded_filename = ''.join(padded_filename)

		a = AES.new(self._key)
		self._filename = a.encrypt(padded_filename)
		self._filename = cPickle.dumps(self._filename)
		self.filename = base64.b64encode(self._filename)

	def decrypt_filename(self, request, key=None, ivr=False):
		if (self._filename):
			return self._filename

		if (not self._key):
			self._key = key or decrypt_cipherkey(request, self, ivr)

		a = AES.new(self._key)
		filename = base64.b64decode(self.filename)
		try:
			filename = cPickle.loads(filename)
		except Exception:
			raise KeyInvalidException()
		self._filename = a.decrypt(filename).rstrip().decode('utf-8')
		return self._filename

	def encrypt_url(self, request, url, key=None):
		if (not self._key):
			self._key = key or decrypt_cipherkey(request, self)

		padded_url = [' ' for i in range((16 - (len(url) % 16)) % 16)]
		padded_url.insert(0, url)
		padded_url = ''.join(padded_url)

		a = AES.new(self._key)
		self._url = a.encrypt(padded_url)
		self._url = cPickle.dumps(self._url)
		self.url = base64.b64encode(self._url)

	def decrypt_url(self, request, key=None, ivr=False):
		if (self._url):
			return self._url

		if (not self._key):
			self._key = key or decrypt_cipherkey(request, self, ivr)

		a = AES.new(self._key)
		url = base64.b64decode(self.url)
		try:
			url = cPickle.loads(url)
		except Exception:
			raise KeyInvalidException()
		self._url = a.decrypt(url).rstrip()
		return self._url

	def encrypt_file(self, request, file_chunks, key=None):
		if (not self._key):
			self._key = key or decrypt_cipherkey(request, self)

		padded_file = file_chunks
		if isinstance(file_chunks, str):
			padded_file = file_chunks + ' ' * ((16 - (len(file_chunks) % 16)) % 16)
		else:
			assembled_file = ''.join(file_chunks)
			padded_file = [' ' for i in range((16 - (len(assembled_file) % 16)) % 16)]
			padded_file.insert(0, assembled_file)
			padded_file = ''.join(padded_file)

		a = AES.new(self._key)
		encrypted_data = a.encrypt(padded_file)
		"""
		name = '.'.join([settings.CONTAINER_PREFIX, "attachments"])
		container = settings.CLOUDCONNECTION.create_container(name)
		file = container.create_object(self.uuid)
		retries = 2
		while retries > 0:
			try:
				file.write(encrypted_data)
				retries = 0
			except SSLError as e:
				retries -= 1
				if(retries <= 0):
					raise e
		"""

		f = create_file('attachments/%s' % (self.uuid,))
		if not f:
			raise IOError
		f.set_contents(encrypted_data)
		f.close()

	def get_file(self, request, response, key=None, ivr=False):
		"""
		Gets the attachment and properly stuffs it into the passed response,
		decrypting if appropriate.
		"""
		if (not self._key):
			self._key = key or decrypt_cipherkey(request, self, ivr)

		response['Cache-Control'] = 'no-cache'
		response['Content-Disposition'] = 'attachment; filename="%s"' % \
			(self.decrypt_filename(request))
		response['Content-Length'] = self.size

		"""
		name = '.'.join([settings.CONTAINER_PREFIX, "attachments"])
		container = settings.CLOUDCONNECTION.create_container(name)
		file = container[self.uuid]
		"""
		f = get_file('attachments/%s' % (self.uuid,))
		if not f:
			raise IOError
		data = f.read()
		f.close()

		if (self.encrypted):
			a = AES.new(self._key)
			data = a.decrypt(data).rstrip()
		response['Cache-Control'] = 'no-cache'
		response['Content-Disposition'] = 'attachment; filename="%s"' % \
				(self.decrypt_filename(request))
		response['Content-Length'] = len(data)
		response.write(data)

	def get_content_file(self, request, key=None, ivr=False):
		if (not self._key):
			self._key = key or decrypt_cipherkey(request, self, ivr)

		f = get_file('attachments/%s' % (self.uuid,))
		if not f:
			raise IOError
		data = f.read()
		f.close()

		if (self.encrypted):
			a = AES.new(self._key)
			data = a.decrypt(data).rstrip()
		return data

	def delete(self, request):
		raise Exception(_('Deletion of MessageAttachment objects is disallowed. '
				'To delete a MessageAttachment, delete the body '
				'and the attachment will follow.'))

	def __unicode__(self):
		return "Message attachment for msg id %s" % (str(self.message.pk),)


class CallbackLog(models.Model):
	message = models.ForeignKey(Message)
	time = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['time']


REFER_STATUS = (
	('NO', ''),
	('AC', _('Accepted')),
	('RE', _('Declined')),
)


class MessageRefer(models.Model):
	uuid = UUIDField(auto=True, primary_key=False)
	message = models.ForeignKey(Message)
	first_name = models.CharField(max_length=30, blank=True)
	middle_name = models.CharField(max_length=30, blank=True, null=True)
	last_name = models.CharField(max_length=30, blank=True)
	gender = models.CharField(max_length=1, choices=GENDER_CHOICES, \
			blank=True, null=True)
	date_of_birth = models.DateField(null=True)
	phone_number = MHLPhoneNumberField(blank=True, null=True)
	alternative_phone_number = MHLPhoneNumberField(blank=True, null=True)
	insurance_id = models.CharField(max_length=30, blank=True, null=True)
	insurance_name = models.CharField(max_length=30, blank=True, null=True)
	secondary_insurance_id = models.CharField(max_length=30, blank=True)
	secondary_insurance_name = models.CharField(max_length=30, blank=True)
	tertiary_insurance_id = models.CharField(max_length=30, blank=True)
	tertiary_insurance_name = models.CharField(max_length=30, blank=True)
	is_sendfax = models.BooleanField()
	status = models.CharField(max_length=2, choices=REFER_STATUS)
	refer_pdf = models.FilePathField(blank=True)
	refer_jpg = models.FilePathField(blank=True)
	refuse_reason = models.CharField(max_length=255, blank=True, null=True)
	practice = models.ForeignKey(PracticeLocation, null=True, 
				blank=True, related_name="messagerefer_practice")

	previous_name = models.CharField(max_length=30, blank=True, null=True)
	email = models.EmailField(_('email address'), blank=True, null=True)
	notes = models.TextField(blank=True, null=True)
	home_phone_number = MHLPhoneNumberField(blank=True, null=True)
	mrn = models.CharField(max_length=30, verbose_name="MRN")
	ssn = models.CharField(max_length=30, verbose_name="SSN", blank=True, null=True)
	prior_authorization_number = models.CharField(max_length=30, blank=True, null=True)
	other_authorization = models.CharField(max_length=200, blank=True, null=True)
	internal_tracking_number = models.CharField(max_length=30, blank=True, null=True)
	address = models.CharField(max_length=200, blank=True, null=True)
	medication_list = models.CharField(max_length=255, blank=True, null=True)
	ops_code = models.CharField(max_length=255, blank=True, null=True)
	icd_code = models.CharField(max_length=255, blank=True, null=True)

	def __unicode__(self):
		return self.first_name

	_filename = None

	def encrypt(self, data, key):
		pass

	def encrypt_file(self, request, file_chunks, key=None):
		if (not self._key):
			self._key = key or decrypt_cipherkey(request, self)

		padded_file = file_chunks + ' ' * ((16 - (len(file_chunks) % 16)) % 16)
		a = AES.new(self._key)
		return a.encrypt(padded_file)

	def decrypt_file(self, request, key=None, ivr=False):
		key = key or decrypt_cipherkey(request, self, ivr)
		f = get_file('refer/pdf/%s' % (self.uuid,))
		if f:
			data = f.read()
			f.close()
			a = AES.new(key)
			return a.decrypt(data).rstrip()
		return ''

	def get_file(self, request, key=None, ivr=False):
		"""
		Gets the refer and properly stuffs it into the passed response,
		decrypting if appropriate.
		"""
		refer_pdf_stream = self.decrypt_file(request, key, ivr=ivr)
		response = HttpResponse(mimetype="application/pdf")
		response["Cache-Control"] = "no-cache"
		response["Accept-Ranges"] = "none"
		response["Content-Disposition"] = "attachment; filename=Refer.pdf"
		response['Content-Length'] = len(refer_pdf_stream)
		response.write(refer_pdf_stream)
		return response


"""
	It's used for encrypting JPG and XML files. 
"""


class MessageAttachmentDicom(models.Model):
	# id = models.AutoField(primary_key=True)
	attachment = models.ForeignKey(MessageAttachment, unique=True)
	jpg_count = models.PositiveIntegerField()  # jpg file count
	xml_count = models.PositiveIntegerField()  # xml file count

	_key = None

	def encrypt(self, data, key):
		# Don't do anything -- encryption for these objects happens after the
		# object is created and saved.
		return

	def encrypt_files(self, request, src_files, suffix, key=None):
		if src_files:
			if (not self._key):
				self._key = key or decrypt_cipherkey(request, self)

			if not isinstance(src_files, list):
				src_files = [src_files]
			for index in xrange(len(src_files)):
				src_file = src_files[index]
				content = src_file.read()
				assembled_file = ''.join(content)
				padded_file = [' ' for i in range((16 - (len(assembled_file) % 16)) % 16)]
				padded_file.insert(0, assembled_file)
				padded_file = ''.join(padded_file)
				a = AES.new(self._key)
				encrypted_data = a.encrypt(padded_file)

				saved_file = create_file('attachments/%s_dicom/%s_%d.%s' % (
						self.attachment.uuid, self.attachment.uuid, index, suffix))
				if not saved_file:
					raise IOError
				saved_file.set_contents(encrypted_data)
				saved_file.close()

	def encrypt_jpgs(self, request, jpg_files, key=None):
		self.encrypt_files(request, jpg_files, 'jpg', key=key)

	def encrypt_xmls(self, request, xml_files, key=None):
		self.encrypt_files(request, xml_files, 'xml', key=key)

	def get_file_content(self, request, suffix, index, key=None, ivr=False):
		if (not self._key):
			self._key = key or decrypt_cipherkey(request, self, ivr)

		f = get_file('attachments/%s_dicom/%s_%d.%s' % (
				self.attachment.uuid, self.attachment.uuid, index, suffix))
		if not f:
			raise IOError
		data = f.read()
		f.close()

		a = AES.new(self._key)
		data = a.decrypt(data).rstrip()
		return data

	def get_jpg_content(self, request, index, key=None, ivr=False):
		return self.get_file_content(request, 'jpg', index, key=key, ivr=False)

	def get_xml_content(self, request, index, key=None, ivr=False):
		return self.get_file_content(request, 'xml', index, key=key, ivr=False)

	def get_dicom_jpg_to_response(self, request, index, key=None, ivr=False):
		data = self.get_jpg_content(request, index, key=key, ivr=False)
		response = HttpResponse(mimetype="image/jpg")
		response["Cache-Control"] = "no-cache"
		response["Accept-Ranges"] = "none"
		response["Content-Disposition"] = "attachment; filename=dicom.jpg"
		response['Content-Length'] = len(data)
		response.write(data)
		return response

	def get_dicom_xml_to_response(self, request, index, key=None, ivr=False):
		data = self.get_xml_content(request, index, key=key, ivr=False)
		response = HttpResponse(mimetype="application/xml")
		response["Cache-Control"] = "no-cache"
		response["Accept-Ranges"] = "none"
		response["Content-Disposition"] = "attachment; filename=dicom.xml"
		response['Content-Length'] = len(data)
		response.write(data)
		return response

	def check_files(self):
		return self.check_type_files(self.jpg_count, 'jpg') and \
				self.check_type_files(self.xml_count, 'xml')

	def check_type_files(self, file_count, suffix):
		exist = True
		for index in xrange(file_count):
			f = get_file('attachments/%s_dicom/%s_%d.%s' % \
						(self.attachment.uuid, self.attachment.uuid, index, suffix))
			if not f:
				exist = False
				break
		return exist

	def gen_keys_for_users(self, request):
		"""
			This method should exclude sender, because sender's key has been generated 
			when invoke function encrypt_object
		"""
		all_recipients = self.get_distinct_related_users(include_sender=False)
		gen_keys_for_users(self, all_recipients, self._key, request)

	def regen_keys_for_users(self, request=None):
		"""
			This method include sender.
		"""
		all_related_users = self.get_distinct_related_users()
		regen_invalid_keys_for_users(self, all_related_users)

	def check_keys_for_users(self, request=None):
		"""
			This method include sender.
		"""
		all_related_users = self.get_distinct_related_users()
		return check_keys_exist_for_users(self, all_related_users)

	def get_distinct_related_users(self, include_sender=True):
		msg = self.attachment.message
		all_related_users = list(msg.recipients.all())
		all_related_users.extend(list(msg.ccs.all()))
		if include_sender:
			all_related_users.extend([msg.sender])
		else:
			non_sender_recipients = [user for user in all_related_users 
					if user.pk != (msg.sender.pk if msg.sender else None)] 
			# remove the sender from the list of recipients to generate keys for
			all_related_users = non_sender_recipients
		all_related_users = set(all_related_users)
		return all_related_users

ACTION_TYPE_OPTION_OPEN = 'OP'
ACTION_TYPE_OPTION_RESOLVE = 'RS'
ACTION_TYPE_OPTION_UNRESOLVE = 'UR'

ACTION_TYPE_OPTIONS = (
	(ACTION_TYPE_OPTION_OPEN, _('Opened')),
	(ACTION_TYPE_OPTION_RESOLVE, _('Resolved')),
	(ACTION_TYPE_OPTION_UNRESOLVE, _('Unresolved')),
)

""" used for recording message opration history """


class MessageActionHistory(models.Model):
	message = models.ForeignKey(Message)
	user = models.ForeignKey(User)
	type = models.CharField(max_length=2, choices=ACTION_TYPE_OPTIONS)
	timestamp = models.PositiveIntegerField(default=0)  # Unix timestamp

	def __unicode__(self):
		return 'Message action history: %s %s, %s for message %s at %s' % (
				self.user.first_name, self.user.last_name, self.type,\
				self.message.uuid, str(self.timestamp))

	class Meta:
		ordering = ["message", "timestamp"]
		unique_together = (('message', 'user', 'type'),)
		verbose_name_plural = "Message Action History"

	@staticmethod
	def create_read_history(message, user, timestamp=None):
		"""Create message action history,
		:param message: is an instance of Message.
		:param user: is an instance of User/MHLUser.
		:param timestamp: unix time stamp
		:raise: ValueError
		"""
		if not message or not user:
			raise ValueError

		if timestamp is None:
			timestamp = time.time()

		history = MessageActionHistory.get_action_history(message, user,\
							ACTION_TYPE_OPTION_OPEN)
		if history:
			return history

		try:
			history = MessageActionHistory(message=message, user=user, 
				type=ACTION_TYPE_OPTION_OPEN, timestamp=timestamp)
			history.save()
			return history
		except IntegrityError:
			return MessageActionHistory.get_action_history(message, user,\
							ACTION_TYPE_OPTION_OPEN)

	@staticmethod
	def create_resolve_history(message, user, resolve=True, timestamp=None):
		"""Create message action history,
		:param message: is an instance of Message.
		:param user: is an instance of User/MHLUser.
		:param resolve: is a bool value.
		:param timestamp: unix time stamp
		:raise: ValueError
		"""
		if not message or not user:
			raise ValueError

		if timestamp is None:
			timestamp = time.time()

		type = ACTION_TYPE_OPTION_RESOLVE if resolve else ACTION_TYPE_OPTION_UNRESOLVE
		history = list(MessageActionHistory.objects.filter(message=message,\
			type__in=[ACTION_TYPE_OPTION_RESOLVE, ACTION_TYPE_OPTION_UNRESOLVE]))
		if history and len(history) > 0:
			history = history[0]
			history.user = user
			history.type = type
			history.timestamp = timestamp
			history.save()
			return history
		else:
			try:
				history = MessageActionHistory(message=message, user=user, 
						type=type, timestamp=timestamp)
				history.save()
				return history
			except IntegrityError:
				return MessageActionHistory.get_action_history(message, user, type)

	@staticmethod
	def get_action_history(message, user, type):
		"""get message action history,
		:param message: is an instance of Message.
		:param user: is an instance of User/MHLUser.
		:param type: message action type ACTION_TYPE_OPTIONS
		:raise: ValueError
		"""
		if not message or not user or not type:
			raise ValueError

		history = list(MessageActionHistory.objects.filter(message=message,\
					user=user, type=type))
		if history and len(history) > 0:
			return history[0]
		else:
			return None


#SMS_STATUS_CHOICES = (
#	('QD','Queued'),
#	('TX','Sending'),
#	
#	('SE','Sent'),
#	('FA','Failed'),
#)
#class MessageSMSLog(models.Model):
#	msg = models.ForeignKey(MessageBody)
#	recipient = models.ForeignKey(User)
#	
#	sms_id = models.CharField(max_length=34)
#	status = models.CharField(max_length=2, choices=SMS_STATUS_CHOICES)
#	
#	request_timestamp = models.DateTimeField(auto_now_add=True)
#	status_timestamp = models.DateTimeField()
