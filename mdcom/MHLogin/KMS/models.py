
from base64 import b64decode, b64encode
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
from functools import wraps

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.db import models

"""
Feature 2074: KMS updated models but keeping old until after rollout, generic pub/priv
keys supports non-user entities such as practices, keys static on reset, oauth support
w/optional key expiration dates, pycrypto 2.6 upgrade, password recovery, no more pickle,
aes helpers w/cbc, pad/unpad helpers, upgraded reset key for admins, more uts.
TESTING_KMS_INTEGRATION - flag to grep for to search changes made outside kms app
"""
RSA_PRIMARY, RSA_IVR = 0, 1  # key types - users have different rsa keys for IVR
RSA_TYPES = {RSA_PRIMARY: 'Primary', RSA_IVR: 'IVR'}
CRED_WEBAPP, CRED_IVRPIN, CRED_OAUTH = 0, 1, 2
CRED_TYPES = {CRED_WEBAPP: 'Web/App', CRED_IVRPIN: 'IVR Pin', CRED_OAUTH: 'OAuth'}


def update_owner_type(func):
	"""
	Decorator to update owner to MHLUser if instanceof User.  TODO: to make this
	go away w/Django 1.5 change default request.user type from User to MHLUser.
	Old KMS did not use generic relations or ContentTypes for public key owner.
	"""
	@wraps(func)
	def decorator(*args, **kwargs):
		from MHLogin.MHLUsers.models import MHLUser
		owner = kwargs.get('owner')
		if isinstance(owner, User) and owner.__class__ != MHLUser:
			kwargs['owner'] = MHLUser.objects.get(id=owner.id)
		return func(*args, **kwargs)
	return decorator


class PublicKeyManager(models.Manager):
	""" Table level helpers for OwnerPublicKey """
	def get_query_set(self):
		return super(PublicKeyManager, self).get_query_set().filter(active=True)

	@update_owner_type
	def filter_pubkey(self, **kwargs):
		owner = kwargs.pop('owner', None)
		owner and kwargs.update({'owner_id': owner.id,
			'owner_type': ContentType.objects.get_for_model(owner)})
		return self.filter(**kwargs)

	@update_owner_type
	def get_pubkey(self, keytype=RSA_PRIMARY, **kwargs):
		owner = kwargs.pop('owner', None)
		owner and kwargs.update({'owner_id': owner.id,
			'owner_type': ContentType.objects.get_for_model(owner)})
		return self.get(keytype=keytype, **kwargs)


class PrivateKeyManager(models.Manager):
	""" Table level helpers for UserPrivateKey. """
	def get_privkey(self, user, opub, credtype=CRED_WEBAPP, **kwargs):
		""" Helper to get most common private key associated with user """
		return self.get(user=user, opub=opub, credtype=credtype, **kwargs)


class EncryptedObjectManager(models.Manager):
	""" Table level helpers for EncryptedObject """
	def create_object(self, obj, opub, clearkey):
		""" create an EncryptedObject given the obj reference (eg. Message,
			Attachment, etc.), pubkey, and the clearkey to encrypt """
		pubkey = import_rsa(opub.publickey)
		return self.create(**{
			'object_type': ContentType.objects.get_for_model(obj),
			'object_id': obj.id,
			'opub': opub,
			'cipherkey': b64encode(PKCS1_OAEP.new(pubkey).encrypt(clearkey)),
			})

	def get_object(self, obj, opub):
		""" Strict helper to get an EncryptedObject """
		return self.get(**{
			'object_type': ContentType.objects.get_for_model(obj),
			'object_id': obj.id,
			'opub': opub,
			})


class OwnerPublicKey(models.Model):
	# FK to owner object, can support non-user entities
	owner_type = models.ForeignKey(ContentType, null=False,
		limit_choices_to={'model__in': ('mhluser', 'practicelocation')})
	owner_id = models.IntegerField()
	# Currently supported: User, PracticeLocation
	owner = generic.GenericForeignKey('owner_type', 'owner_id')
	# owner's RSA public part of key in 'PEM' (RFC1421) format
	publickey = models.TextField(editable=False)
	# key to decrypt adminscopy, enc'd with admin public reset key
	admincipher = models.TextField(editable=False)
	# RSA key encrypted via admin's decrypted cipher
	adminscopy = models.TextField(editable=False)
	# public key type: web, ivr, etc.
	keytype = models.IntegerField(default=RSA_PRIMARY,
		choices=((k, v) for k, v in RSA_TYPES.items()))
	# True when all EncryptedObjects with this pubkey are valid and active
	active = models.BooleanField(default=True)
	# datetime of OwnerPublicKey creation
	create_date = models.DateTimeField(auto_now_add=True, editable=False)

	__unicode__ = lambda self: "%s, key type: %s" % (self.owner if self.owner else
		'/'.join([str(self.owner_type), str(self.owner_id)]), RSA_TYPES[self.keytype])

	# custom managers for this table
	objects = PublicKeyManager()
	inactive = models.Manager()

#	class Meta:  # TODO: once rm #2115 in we can enforce and remove active field
#		unique_together = (('owner_type', 'owner_id', 'keytype'),)


class UserPrivateKey(models.Model):
	# user who's credentials are used to encrypt privatekey field
	user = models.ForeignKey('MHLUsers.MHLUser', related_name='userprivatekey')
	# Owner Public Key associated with this private key
	opub = models.ForeignKey(OwnerPublicKey, related_name='userprivatekey')
	# RSA encrypted with user credentials or secret_key if g'fathered
	privatekey = models.TextField(editable=False)
	# how rsa encrypted: webapp (password), oauth (token), ivr (pin), etc.
	credtype = models.IntegerField(default=CRED_WEBAPP,
		choices=((k, v) for k, v in CRED_TYPES.items()))
	# flag True when privatekey encrypted with secret_key
	gfather = models.BooleanField(default=True, editable=False)
	# recovery blob stores encrypted rsa key, credentials emailed to user
	recovery = models.TextField(null=True, editable=False)
	# datetime of UserPrivateKey creation
	create_date = models.DateTimeField(auto_now_add=True, editable=False)
	# datetime of expiration - None for no expiration
	expire_date = models.DateTimeField(default=None, null=True, editable=False)

	__unicode__ = lambda self: "%s, key type: %s, cred type: %s" % \
		(self.user, RSA_TYPES[self.opub.keytype], CRED_TYPES[self.credtype])

	# custom manager for this table
	objects = PrivateKeyManager()

	class Meta:
		unique_together = (('user', 'opub', 'credtype'),)


class EncryptedObject(models.Model):
	# object reference who's data is encrypted, e.g. MessageBody, MessageAttachment, etc.
	object_type = models.ForeignKey(ContentType)
	object_id = models.PositiveIntegerField()
	object = generic.GenericForeignKey('object_type', 'object_id')
	# public key who encrypted me
	opub = models.ForeignKey(OwnerPublicKey, related_name='encryptedobject')
	# RSA encrypted via owner public key, decrypted via user private key
	cipherkey = models.TextField(editable=False)
	# datetime of encrypted object creation
	create_date = models.DateTimeField(auto_now_add=True, editable=False)

	__unicode__ = lambda self: "%s %s" % (self.object, self.opub)

	def decrypt_cipherkey(self, upriv, creds):
		""" Helper returning decrypted cipherkey, i.e. clearkey """
		rsa = import_rsa(upriv.privatekey, creds)
		clearkey = PKCS1_OAEP.new(rsa).decrypt(b64decode(self.cipherkey))
		return clearkey

	def change_cipherkey(self, opub, new_clearkey):
		""" Change cipher key, assumes object is or will be re-encrypted with this key """
		pubkey = import_rsa(opub.publickey)
		self.cipherkey = b64encode(PKCS1_OAEP.new(pubkey).encrypt(new_clearkey))
		self.save()

	# custom manager for this table
	objects = EncryptedObjectManager()

	class Meta:
		unique_together = (('object_type', 'object_id', 'opub'),)


def export_rsa(internKey, passphrase=None):
	""" Helper hook to export key with default protection scheme. """
	# With pycrypto 2.6: passphrase hashed w/PBKDF1, key enc'd w/DES-EDE3-CBC
	return internKey.exportKey(passphrase=passphrase)
	# TODO: when pycrypto >= 2.7 available
	# return internKey.exportKey(passphrase=passphrase, pkcs=8,
	#	protection='PBKDF2WithHMAC-SHA1AndAES256-CBC')  # , or bcrypt/scrypt
	#		#iteration_count=10000, salt_size=8)


def import_rsa(externKey, passphrase=None, model=None, fieldname=None):
	""" Helper hook to import key, passphrase None for public key import """
	if passphrase:
		# TODO: for key encryption upgrade, parse header to determine if upgrade needed
		# if upgradeable import key, re-export strengthened and save to model if exists.
		rsa = RSA.importKey(externKey, passphrase)
	else:  # public key
		rsa = RSA.importKey(externKey)
	return rsa


##########################################################################################
################# Previous KMS: To be removed once integration complete ##################
##########################################################################################

import base64
import cPickle
import os
import ssl
import urllib2

from django.utils.translation import ugettext as _

from MHLogin.utils.fields import UUIDField
from MHLogin.utils.admin_utils import mail_admins

from MHLogin.KMS.exceptions import KeyInvalidException


class PrivateKeyBase(models.Model):
	uuid = UUIDField(auto=True, primary_key=True)

	# Don't forget to define the following fields. (See PrivateKey for an example):
	#object_type = models.ForeignKey(ContentType, related_name='The encrypted object type (non-IVR).')
	#object_id = models.IntegerField()
	#object = generic.GenericForeignKey('object_type', 'object_id')

	owner = models.ForeignKey(User)

	# Encrypted, pickled, base64encoded key -- encrypted using the owner's public key!
	key = models.TextField()

	# Reset Password Flag
	# This flag shall indicate that this privatekey is encrypted using a user's
	# old keypair, in the event that the user's password is reset or their
	# keypair has to be changed for some reason.
	invalid_key = models.BooleanField(default=False)

	# Clear (unencrypted) key. This shouldn't be stored in the database.
	_key_clear = None

#	Encryption shouldn't be needed. We're going to generate the key, then
#	encrypt the data in one step, really. In other words, this object is really
#	only ever being used for key storage and decryption.
#	def encrypt(self, string, key):
#		pass

	def decrypt(self, request, key=None, keypair=None, ciphertext=None, obj=None):
		"""Decrypt the ciphertext and return the string data back.

		:param key: The key to decrypt the owner's RSAKeyPair, so that we can get at this private key.
		:param ciphertext: The ciphertext to decrypt using this key. The ciphertext should 
			be encrypted, pickled, then base64encoded (in that order).
		"""
		if (not keypair and not key):
			raise Exception(_('Either key or keypair (or both) MUST be defined. '
				'Note that if key is omitted, keypair MUST contain a decrypted, '
				'cached copy of the keypair.'))

		if (not key and not keypair._keypair):
			raise Exception(_('If key is omitted, keypair MUST contain a '
					'decrypted, cached copy of the keypair.'))

		private_key = self.decrypt_private_key(key, key_pair=keypair)
		if (len(private_key) != 32):
			# TODO:
			# Consider mailing admins at this point. This is an erroneous condition.
			print private_key
			raise KeyInvalidException('key length is %i' % len(private_key))

		if (ciphertext):
			ciphertext = base64.b64decode(ciphertext)
			ciphertext = cPickle.loads(ciphertext)

			aes = AES.new(private_key)
			clear_text = aes.decrypt(ciphertext)
			return clear_text.rstrip()  # strip trailing spaces

		if (obj):
			return obj.decrypt(request, private_key)

		return self.object.decrypt(request, private_key)

	def decrypt_private_key(self, key, key_pair):
		private_key = base64.b64decode(self.key)
		private_key = cPickle.loads(private_key)
		private_key = key_pair.decrypt(private_key, key)
		if (len(private_key) > 32):
			# TODO:
			# Consider mailing admins at this point. This is an erroneous condition.
			print private_key
			raise KeyInvalidException('key length is %i' % len(private_key))
		if (len(private_key) < 32):
			# pycrypto will disregard leading null characters when applying the
			# public key encryption. As a result, we're going to add them back
			# here.
			padding = ['\x00' for i in range((32 - (len(private_key) % 32)) % 32)]
			padding.append(private_key)
			private_key = ''.join(padding)
		return private_key

	class Meta:
		unique_together = (('object_type', 'object_id', 'owner',),)
		abstract = True


class PrivateKey(PrivateKeyBase):
	# /object/ shall point to a Django model with a method named "decrypt".
	# This method shall accept the private key as an argument and return the
	# decrypted output, be it a file or text.
	# Note that in the event of any output other than string, the object coder
	# will be expected to provide a valid Django HttpResponse object as
	# appropriate (e.g., with correct MIME data).
	object_type = models.ForeignKey(ContentType, related_name=('The encrypted '
									'object type (non-IVR).'))
	object_id = models.IntegerField()
	object = generic.GenericForeignKey('object_type', 'object_id')

	def __init__(self, *args, **kwargs):
		# First, grab our kwargs, if they exist. This way, the parent init function won't complain.
		key_arg = 'key' in kwargs
		if (key_arg):
			key_arg = kwargs['key']
			if (len(key_arg) != 32):
				raise Exception(_('Keyword \'key\' of the wrong length. It MUST '
								'have length of 32 characters.'))
			del kwargs['key']
		public_key = None
		if('public_key' in kwargs):
			public_key = kwargs['public_key']
			del kwargs['public_key']

		super(PrivateKey, self).__init__(*args, **kwargs)

		if (not self.key and key_arg):
			# We need to initialize this object
			if (not key_arg):
				raise Exception(_('Keyword \'key\' is required.'))
			if(not public_key):
				public_key = RSAPubKey.objects.get(owner=self.owner)
			self.key = public_key.encrypt(key_arg)
			self.key = cPickle.dumps(self.key)
			self.key = base64.b64encode(self.key)

	def decrypt_private_key(self, key, key_pair=None):
		if (not key_pair):
			key_pair = RSAKeyPair.objects.get(owner=self.owner)
		return super(PrivateKey, self).decrypt_private_key(key, key_pair)


class IVR_PrivateKey(PrivateKeyBase):
	# /object/ shall point to a Django model with a method named "decrypt".
	# This method shall accept the private key as an argument and return the
	# decrypted output, be it a file or text.
	# Note that in the event of any output other than string, the object coder
	# will be expected to provide a valid Django HttpResponse object as
	# appropriate (e.g., with correct MIME data).
	object_type = models.ForeignKey(ContentType, related_name='The encrypted object type (IVR).')
	object_id = models.IntegerField()
	object = generic.GenericForeignKey('object_type', 'object_id')

	def __init__(self, *args, **kwargs):
		# First, grab our kwargs, if they exist. This way, the parent init function won't complain.
		key_arg = 'key' in kwargs
		if (key_arg):
			key_arg = kwargs['key']
			if (len(key_arg) != 32):
				raise Exception(_('Keyword \'key\' of the wrong length. It MUST have '
								'length of 32 characters.'))
			del kwargs['key']
		public_key = None
		if('public_key' in kwargs):
			public_key = kwargs['public_key']
			del kwargs['public_key']

		super(IVR_PrivateKey, self).__init__(*args, **kwargs)

		if (not self.key and key_arg):
			# We need to initialize this object
			if (not key_arg):
				raise Exception(_('Keyword \'key\' is required.'))
			if(not public_key):
				public_key = IVR_RSAPubKey.objects.get(owner=self.owner)
			self.key = public_key.encrypt(key_arg)
			self.key = cPickle.dumps(self.key)
			self.key = base64.b64encode(self.key)

	def decrypt_private_key(self, key, key_pair=None):
		if (not key_pair):
			key_pair = IVR_RSAKeyPair.objects.get(owner=self.owner)
		return super(IVR_PrivateKey, self).decrypt_private_key(key, key_pair)


class AdminPrivateKey(models.Model):
	"""
	This is the administrative "back-door" key for all objects. This will allow us 
	access to protected data, should users need to perform actions such as password resets.
	"""
	uuid = UUIDField(auto=True, primary_key=True)

	# /object/ shall point to a Django model with a TextField named
	# "ciphertext". This field shall contain data encrypted by the private key,
	# pickled, then base64-encoded.
	object_type = models.ForeignKey(ContentType, related_name='The object for which '
					'this Admin Key exists')
	object_id = models.PositiveIntegerField()
	object = generic.GenericForeignKey('object_type', 'object_id')

	# Encrypted, pickled, base64encoded key -- encrypted using the owner's public key!
	key = models.TextField()

	# Clear key. This shouldn't be stored in the database
	_key_clear = None

	def __init__(self, *args, **kwargs):
		# First, grab our kwargs, if they exist. This way, the parent init function won't complain.
		key_arg = 'key' in kwargs
		if (key_arg):
			key_arg = kwargs['key']
			if (len(key_arg) != 32):
				raise Exception(_('Keyword \'key\' of the wrong length. It MUST '
								'have length of 32 characters.'))
			del kwargs['key']

		super(AdminPrivateKey, self).__init__(*args, **kwargs)

		if (not self.key and key_arg):
			# We need to initialize this object
			if (not key_arg):
				raise Exception(_('Keyword \'key\' is required.'))

			public_key = base64.b64decode(settings.CRYPTO_ADMIN_PUBLIC_KEY)
			public_key = cPickle.loads(public_key)
			public_key._randfunc = os.urandom  # rm #2113, pickled diffs pycrypto 2.3<-->2.6
			self.key = public_key.encrypt(key_arg, os.urandom)
			self.key = cPickle.dumps(self.key)
			self.key = base64.b64encode(self.key)

#	Encryption shouldn't be needed. We're going to generate the key, then
#	encrypt the data in one step, really. In other words, this object is really
#	only ever being used for key storage and decryption.
#	def encrypt(self, string, key):
#		pass

	def decrypt(self, request, key, ciphertext=None):
		"""Decrypt the ciphertext and return the string data back.

		:param key: The key to decrypt the owner's RSAKeyPair, so that we 
			can get at this private key.
		:param ciphertext: The ciphertext to decrypt using this key. The ciphertext 
			should be encrypted, pickled, then base64encoded (in that order).
		"""
		if (len(key) > 32):
			raise KeyInvalidException('Argument \'key\' is too long. It has a '
									'maximum length of 32 characters.')

		private_key = self.decrypt_private_key(key)

		if (ciphertext):
			ciphertext = base64.b64decode(ciphertext)
			ciphertext = cPickle.loads(ciphertext)

			aes = AES.new(private_key)
			clear_text = aes.decrypt(ciphertext)
			return clear_text.rstrip()  # strip trailing spaces

		return self.object.decrypt(request, private_key)

	def decrypt_private_key(self, key):
		key_pair = base64.b64decode(settings.CRYPTO_ADMIN_KEYPAIR)
		padded_key = [' ' for i in range((32-(len(key)%32))%32)]
		padded_key.insert(0, key)
		key = ''.join(padded_key)
		a = AES.new(key)
		key_pair = a.decrypt(key_pair)

		try:
			key_pair = cPickle.loads(key_pair)
			key_pair._randfunc = os.urandom  # rm #2113 pickled diffs pycrypto 2.3<-->2.6  
		except Exception:
			raise KeyInvalidException()

		private_key = base64.b64decode(self.key)
		private_key = cPickle.loads(private_key)
		return key_pair.decrypt(private_key)


class RSAPubKey_Base(models.Model):
	uuid = UUIDField(auto=True, primary_key=True)

	owner = models.ForeignKey(User)

	public_key = models.TextField(blank=True)

	# If you implement this abstract object, make sure you define the following 
	# field as a models.ForeignKey out to the keypair!
	key_pair = None

	# Cache the binary/unpacked key in the interest of reducing computational overhead
	_pkey_obj = None

	def __init__(self, *args, **kwargs):
		pub_key = 'public_key' in kwargs
		if (pub_key):
			pub_key = kwargs['public_key']
			del(kwargs['public_key'])
		super(RSAPubKey_Base, self).__init__(*args, **kwargs)
		if (pub_key and not self.public_key):
			self._populate_key(pub_key)

	def _populate_key(self, pub_key_obj):
		key_temp = cPickle.dumps(pub_key_obj)
		self.public_key = base64.b64encode(key_temp)

	def encrypt(self, text):
		if (not self._pkey_obj):
			pkey = base64.b64decode(self.public_key)
			#raise Exception(repr(pkey))
			self._pkey_obj = cPickle.loads(pkey)
		self._pkey_obj._randfunc = os.urandom  # rm #2113, pickled diffs pycrypto 2.3<-->2.6
		return self._pkey_obj.encrypt(text, os.urandom)

	class Meta:
		abstract = True


class RSAPubKey(RSAPubKey_Base):
	# Keeps track of whether or not the owner of this key has an IVR key as well
	ivr_key = models.ForeignKey('IVR_RSAPubKey', null=True, default=None)
	key_pair = models.ForeignKey('RSAKeyPair', null=True)


class IVR_RSAPubKey(RSAPubKey_Base):
	key_pair = models.ForeignKey('IVR_RSAKeyPair', null=True)


class RSAKeyPair_Base(models.Model):
	"""A secured RSA keypair object.
	Note that when you implement this, you'll want to implement an over-written
	save method. See RSAKeyPair/IVR_RSAKeyPair for implementation specifics.
	"""

	uuid = UUIDField(auto=True, primary_key=True)
	owner = models.ForeignKey(User)

	keypair = models.TextField(blank=True)

	# The grandfathered flag will be True on all users for whom the user's key
	# is grounded in settings.SECRET_KEY, rather than in the user's password.
	# This only is the case until the user logs in with their password (or is
	# nagged to update their key).
	grandfathered = models.BooleanField(default=False)

	# The following is a strictly internal value. It's only used on initialization 
	# of a new RSAKeyPair to store the pycrypto public key object. This object is 
	# created and assigned on keypair generation, and is used to generate the 
	# RSAPubKey object on initial save.
	_public_key = None

	# The following is a strictly internal value. It's the cached copy of this
	# object's decrypted, deserialized key pair.
	_keypair = None

	def __init__(self, *args, **kwargs):
		key = 'key' in kwargs
		if (key):
			key = kwargs['key']

			if (len(key) != 32):
				raise KeyInvalidException(_('The given key is of the incorrect '
					'length (%i). Keys have MUST have a length of 32 characters.'))
			del(kwargs['key'])
		super(RSAKeyPair_Base, self).__init__(*args, **kwargs)
		if (not self.keypair and key):
			self._generate_key(key)
		elif (key):
			raise Exception(_('Unexpected kwarg \'key\' encountered.'))

	def _generate_key(self, key):
		url = ''.join(['https://files.mdcom.com/KMS/Key/New/', settings.SERVER_PLATFORM, '/'])
		try:
			# make sure this is defined for the default/catch-all Exception handler
			keypair_response_raw = ''
			keypair_response = urllib2.urlopen(url, timeout=5)
			keypair_response_raw = keypair_response.read()
			if (keypair_response.getcode() == 200):
				keypair = base64.b64decode(keypair_response_raw)
				keypair = cPickle.loads(keypair)
			else:
				keypair = self._generate_keypair_manually()
		except (urllib2.HTTPError, urllib2.URLError, ssl.SSLError) as e:
			# The fetch failed
			#print "The fetch failed!"
			mail_admins(_('KMS KeyGen Error: Failed Fetch'), """
KMS.models.%s._generate_key exception: %s
Host: %s
URL: %s
""" %
				(self.__class__.__name__, repr(e), settings.SERVER_ADDRESS, url))
			keypair = self._generate_keypair_manually()
		except (ValueError,) as e:
			# The base64 decode failed
			#print "The base64 decode failed!"
			mail_admins(_('KMS KeyGen Error: base64 Decode Failed'), """
KMS.models.%s._generate_key exception: %s
Host: %s
URL: %s
Value: %s
""" %
				(self.__class__.__name__, repr(e), settings.SERVER_ADDRESS, url, keypair_response_raw))
			keypair = self._generate_keypair_manually()
		except (cPickle.PickleError, AttributeError, EOFError, ImportError, IndexError) as e:
			# The unpickle failed
			#print "The unpickle failed!"
			mail_admins(_('KMS KeyGen Error: Unpickle Failed'), """
KMS.models.%s._generate_key exception: %s
Host: %s
Value: %s
URL: %s
""" %
				(self.__class__.__name__, repr(e), settings.SERVER_ADDRESS, url, keypair_response_raw))
			keypair = self._generate_keypair_manually()
		except Exception as e:
			# Generic error handler! An unknown exception was raised.
			mail_admins(_('KMS KeyGen Error: UNKNOWN EXCEPTION'), """
KMS.models.%s._generate_key exception: %s
Host: %s
Value: %s
URL: %s
""" %
				(self.__class__.__name__, repr(e), settings.SERVER_ADDRESS, url, keypair_response_raw))
			keypair = self._generate_keypair_manually()

		self._public_key = keypair.publickey()

		# Prepare the keypair for storage, then assign it.
		keypair = cPickle.dumps(keypair)
		padding = [' ' for i in range(16 - (len(keypair) % 16))]
		padding.insert(0, keypair)
		keypair = ''.join(padding)
		aes = AES.new(key)
		keypair = aes.encrypt(keypair)
		self.keypair = base64.b64encode(keypair)

	def _generate_keypair_manually(self):
		# Generate keys if _generate_key has an issue
		return RSA.generate(2048, os.urandom)

	def decrypt_self(self, key):
		if (len(key) != 32):
			raise KeyInvalidException(_('Argument \'key\' is of the wrong length. '
									'It MUST be 32 characters long.'))
		aes = AES.new(key)

		self._keypair = self.keypair
		self._keypair = base64.b64decode(self._keypair)
		self._keypair = aes.decrypt(self._keypair)
		try:
			self._keypair = cPickle.loads(self._keypair)
			self._keypair._randfunc = os.urandom  # pickled diffs pycrypto 2.3<-->2.6
		except Exception:
			raise KeyInvalidException()

	def decrypt(self, ciphertext, key=None):
		if (not self._keypair and key):
			self.decrypt_self(key)

		try:
			return self._keypair.decrypt(ciphertext)
		except ValueError:
			raise KeyInvalidException()

	def change_key(self, old_key, new_key):
		if (len(old_key) != 32):
			raise KeyInvalidException(_('Argument \'old_key\' is of the wrong length. '
					'It MUST be 32 characters long.'))
		if (len(new_key) != 32):
			raise KeyInvalidException(_('Argument \'new_key\' is of the wrong length. '
					'It MUST be 32 characters long.'))

		old_aes = AES.new(old_key)
		new_aes = AES.new(new_key)

		keypair = base64.b64decode(self.keypair)
		keypair = old_aes.decrypt(keypair)

		keypair = new_aes.encrypt(keypair)
		self.keypair = base64.b64encode(keypair)

	class Meta:
		abstract = True


class RSAKeyPair(RSAKeyPair_Base):
	# Keeps track of whether or not the owner of this key has an IVR key as well
	ivr_key = models.ForeignKey('IVR_RSAKeyPair', null=True, default=None)

	def save(self, *args, **kwargs):
		create_public_key = not self.uuid
		super(RSAKeyPair, self).save(*args, **kwargs)
		if (create_public_key):
			# Generate the public key object for this object.
			pub_key = RSAPubKey(public_key=self._public_key)
			pub_key.owner = self.owner
			pub_key.key_pair = self
			if(self.ivr_key):
				pub_key.ivr_key = IVR_RSAPubKey.objects.get(key_pair=self.ivr_key)
			pub_key.save()


class IVR_RSAKeyPair(RSAKeyPair_Base):
	def save(self, *args, **kwargs):
		create_public_key = not self.uuid
		super(IVR_RSAKeyPair, self).save(*args, **kwargs)
		if (create_public_key):
			# Generate the public key object for this object.
			pub_key = IVR_RSAPubKey(public_key=self._public_key)
			pub_key.owner = self.owner
			pub_key.key_pair = self
			pub_key.save()

