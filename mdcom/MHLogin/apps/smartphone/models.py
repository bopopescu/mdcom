
import datetime
import hashlib
import random
import string

from django.db import models

from MHLogin.MHLUsers.models import MHLUser
from MHLogin.utils.constants import USER_TYPE_CHOICES
from MHLogin.utils.fields import UUIDField


class ActiveAssnManager(models.Manager):
	def get_query_set(self):
		return super(ActiveAssnManager, self).get_query_set().filter(is_active=True)

PLATFORM_CHOICES = (
	('Android', 'Android'),
	('iPhone', 'iPhone'),
	('iPad', 'iPad'),
)


class SmartPhoneAssn(models.Model):
	device_id = UUIDField(max_length=255, auto=True, db_index=True, unique=True, editable=True)
	device_serial = models.CharField(max_length=255)
	user = models.ForeignKey(MHLUser, db_index=True)
	# The human-readable description for this device.
	name = models.CharField(max_length=255, default='', blank=True)

	user_type = models.IntegerField(choices=USER_TYPE_CHOICES)

	# If the version field is None or '', it's version 1.0.
	version = models.CharField(max_length=32, default='1.00.000', blank=True, null=True)
	platform = models.CharField(choices=PLATFORM_CHOICES, max_length=64)

	secret = models.CharField(max_length=255, blank=False)
	# A hash of the user's encryption key. This is used to verify that we have
	# the correct value.
	secret_hash = models.CharField(max_length=255, blank=False)

	is_active = models.BooleanField(default=True, db_index=True)

	password_reset = models.BooleanField(default=False)

	db_secret = models.TextField(blank=True, null=True)
	# A hash of the app db's encryption key. This is used to verify that we have
	# the correct value.
	db_hash = models.CharField(max_length=255, blank=False)

	push_token = models.CharField(max_length=255, blank=True)

	def save(self, request, *args, **kwargs):
		created = not bool(self.pk)
		super(SmartPhoneAssn, self).save(*args, **kwargs)
		if (created):
			log_entry = SmartPhoneAssnLog(
								device_id=self.device_id,
								serial=self.device_serial,
								requesting_ip=request.META['REMOTE_ADDR'],
								timestamp=datetime.datetime.now(),
								action='ASC'
							)
			log_entry.save()

	def dissociate(self, request, remote_request=False, administrative_request=False):
		"""
		arguments:
			request - the standard Django HttpRequest object that views get.
			remote_request - Whether or not the request was initiated remotely. 
			This argument is typecast as a boolean to determine truth value.
		"""
		dissoc_code = 'WDS'
		if (remote_request):
			dissoc_code = 'RDS'
		log_entry = SmartPhoneAssnLog(
							device_id=self.device_id,
							serial=self.device_serial,
							requesting_ip=request.META['REMOTE_ADDR'],
							timestamp=datetime.datetime.now(),
							action=dissoc_code
						)
		log_entry.save()

		self.is_active = False
		if (self.pk):
			super(SmartPhoneAssn, self).save()

	def reassociate(self, request, name=''):
		"""
		Re-associates this device if it was dissociated at some point.
		"""
		log_entry = SmartPhoneAssnLog(
							device_id=self.device_id,
							serial=self.device_serial,
							requesting_ip=request.META['REMOTE_ADDR'],
							timestamp=datetime.datetime.now(),
							action='ASC'
						)
		log_entry.save()

		self.is_active = True
		if (name):
			self.name = name

		if (self.pk):
			super(SmartPhoneAssn, self).save()

	def delete(self):
		raise Exception('Deletion of this object is disallowed.')

	def verify_key(self, key):
		"""
		Verifies that the passed key is valid for the user.

		Note that key is expected to be base64-encoded.
		"""
		(salt, sep, hash) = self.secret_hash.partition('$')

		m = hashlib.md5()
		m.update(salt)
		m.update(key)

		if (m.hexdigest() == hash):
			return True
		return False

	def verify_db_key(self, key):
		"""
		Verifies that the passed key is valid for the user's smartphone db.

		Note that key is expected to be base64-encoded.
		"""

		(salt, sep, hash) = self.db_hash.partition('$')

		m = hashlib.md5()
		m.update(salt)
		m.update(key)

		if (m.hexdigest() == hash):
			return True
		return False

	def update_secret(self, secret, key):
		"""
		Sets the secret value for this object, and appropriately updates the
		hash for the user's encryption key, so that we can ensure we have a
		good encryption key when the device requests it.

		Note that key and secret are expected to be base64-encoded.
		"""
		char_set = string.ascii_uppercase + \
							string.ascii_lowercase + string.digits
		salt = ''.join(random.sample(char_set, 6))

		self.secret = secret

		m = hashlib.md5()
		m.update(salt)
		m.update(key)

		hash = m.hexdigest()
		self.secret_hash = ''.join([salt, '$', hash])

		if (self.pk):
			super(SmartPhoneAssn, self).save()

	def update_db_secret(self, secret, key):
		"""
		Sets the secret value for this object, and appropriately updates the
		hash for the user's encryption key, so that we can ensure we have a
		good encryption key when the device requests it.

		Note that key and secret are expected to be base64-encoded.
		"""
		char_set = string.ascii_uppercase + \
							string.ascii_lowercase + string.digits
		salt = ''.join(random.sample(char_set, 6))

		self.db_secret = secret

		m = hashlib.md5()
		m.update(salt)
		m.update(key)

		hash = m.hexdigest()
		self.db_hash = ''.join([salt, '$', hash])

		if (self.pk):
			super(SmartPhoneAssn, self).save()

	def usr_password_reset(self, request):
		"""
		Sets the password_reset flag to True.
		"""
		log_entry = SmartPhoneAssnLog(
							device_id=self.device_id,
							serial=self.device_serial,
							requesting_ip=request.META['REMOTE_ADDR'],
							timestamp=datetime.datetime.now(),
							action='PCG'
						)
		log_entry.save()

		self.password_reset = True
		if (self.pk):
			super(SmartPhoneAssn, self).save()

	def usr_password_reset_complete(self, request):
		"""
		Sets the password_reset flag to False.
		"""
		log_entry = SmartPhoneAssnLog(
							device_id=self.device_id,
							serial=self.device_serial,
							requesting_ip=request.META['REMOTE_ADDR'],
							timestamp=datetime.datetime.now(),
							action='PCC'
						)
		log_entry.save()

		self.password_reset = False
		if (self.pk):
			super(SmartPhoneAssn, self).save()

	all_objects = models.Manager()
	objects = ActiveAssnManager()

	class Meta:
		verbose_name_plural = "Smart Phone Assn"


SMARTPHONE_LOG_ACTIONS = (
	('ASC', 'Association'),
	('RDS', 'Remote Dissociation'),
	('WDS', 'Web Dissociation'),
	('ADS', 'Administrative Dissociation'),
	('NOT', 'Device Notification'),  # Notification of the device to wipe.

	('PCG', 'Password Change'),
	('PCC', 'Password Change Complete'), 
)


class SmartPhoneAssnLog(models.Model):
	device_id = models.CharField(max_length=32, db_index=True)
	serial = models.CharField(max_length=255, db_index=True)

	requesting_ip = models.IPAddressField()
	timestamp = models.DateTimeField()
	action = models.CharField(max_length=3, choices=SMARTPHONE_LOG_ACTIONS)

	def save(self, **kwargs):
		if (not self.pk):
			super(SmartPhoneAssnLog, self).save(**kwargs)
		else:
			raise Exception('Updating existing records is disallowed.')

	def delete(self):
		raise Exception('Deletion of this object is disallowed.')

