
import os
import sys

import Crypto.PublicKey.RSA as RSA
from Crypto.Cipher import PKCS1_OAEP
from base64 import b64encode, b64decode

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.core.urlresolvers import reverse
from django.db import models
from django.http import HttpResponse, HttpRequest
from django.utils import unittest
from django.test import TestCase

from MHLogin.MHLUsers.models import Administrator, MHLUser, Provider

from MHLogin.KMS.exceptions import KeyInvalidException
from MHLogin.KMS.models import PrivateKey, RSAPubKey, RSAKeyPair, \
	AdminPrivateKey, IVR_RSAKeyPair, IVR_RSAPubKey, IVR_PrivateKey, \
	CRED_WEBAPP, CRED_IVRPIN, RSA_IVR, OwnerPublicKey, UserPrivateKey, \
	EncryptedObject, RSA_TYPES, export_rsa, import_rsa
from MHLogin.KMS.shortcuts import encrypt_object, decrypt_object, gen_keys_for_users, \
	check_keys_exist_for_users, recrypt_ivr_key_via_web_creds, admin_decrypt_cipherkey, \
	decrypt_cipherkey
from MHLogin.KMS.utils import store_user_key, strengthen_key, create_default_keys, \
	generate_recovery, reset_keys, generate_new_user_keys, reset_user_invalid_keys, \
	aes_decrypt, aes_encrypt, get_user_key, generate_keys_for_users, recrypt_keys

# If import error need to run: python manage.py create_resetkeys.py <admin pw>
try:
	from MHLogin._admin_reset import ADMIN_RESET_ENCD_RSA
except ImportError:
	sys.stderr.write('To generate _admin_reset.py please run management command:\n'
					'python manage.py create_resetkeys demo\n')
	raise

# Admin password is "demo"
ADMIN_PASSWORD = 'demo'


def test_create_provider(username, email, firstname, lastname, password, mobile):
	""" helper to create a provider """
	prov = Provider.objects.create(username=username, email=email,
		office_lat=0.0, office_longit=0.0, first_name=firstname,
		last_name=lastname, mobile_phone=mobile, mdcom_phone='123',
		tos_accepted=True, mobile_confirmed=True, email_confirmed=True, is_active=True)
	prov.set_password(password)
	prov.user = prov  # setup our unique relationship FK/inheritance to mhluser
	prov.save()
	return prov

devnull = open(os.devnull, 'w')


class SecureTestMessage(models.Model):
	owner = models.ForeignKey(User, null=True)
	ciphertext = models.TextField()

	def decrypt(self, request, clearkey):
		return aes_decrypt(clearkey, b64decode(self.ciphertext))

	def encrypt(self, cleartext, clearkey):
		self.ciphertext = b64encode(aes_encrypt(clearkey, cleartext))


class ShortcutTests(unittest.TestCase):

	# Configuration
	password = 'foobazbar'
	ivr_pin = '1234'
	webcreds = password
	ivrcreds = ivr_pin
	clear_text = 'This is my message'
	initial_creds = settings.SECRET_KEY

	@classmethod
	def setUpClass(self):
		""" Create a User to link the private key to. """
		u = MHLUser.objects.create(username="ShortcutTests")
		create_default_keys(u)
		uprivs = UserPrivateKey.objects.filter(user=u, credtype=CRED_WEBAPP, gfather=True)
		recrypt_keys(uprivs, self.initial_creds, self.webcreds)
		uprivs = UserPrivateKey.objects.filter(user=u, credtype=CRED_IVRPIN, gfather=True)
		recrypt_keys(uprivs, self.initial_creds, self.ivrcreds)

	@classmethod
	def tearDownClass(cls):
		User.objects.all().delete()
		MHLUser.objects.all().delete()
		Provider.objects.all().delete()
		Administrator.objects.all().delete()
		OwnerPublicKey.objects.all().delete()
		UserPrivateKey.objects.all().delete()
		EncryptedObject.objects.all().delete()

	def test_encrypt_object_noIVR(self):
		u = MHLUser.objects.get(username="ShortcutTests")
		opub = OwnerPublicKey.objects.get_pubkey(owner=u)
		m = encrypt_object(SecureTestMessage, {}, self.clear_text, opub)

		# Set up a fake request object.
		request = HttpRequest()
		request.session = dict()
		response = HttpResponse()
		request.user = u
		store_user_key(request, response, self.password)
		request.COOKIES['ss'] = response.cookies['ss'].value

		m_get = SecureTestMessage.objects.get(pk=m.pk)
		m_body = decrypt_object(request, m_get)

		self.assertEqual(m_body, self.clear_text)

	def test_encrypt_object_withIVR(self):
		u = User.objects.get(username="ShortcutTests")
		opub = OwnerPublicKey.objects.get_pubkey(owner=u, keytype=RSA_IVR)
		m = encrypt_object(SecureTestMessage, {}, self.clear_text, opub)

		# Set up a fake request object.
		request = HttpRequest()
		request.session = dict()
		response = HttpResponse()
		request.user = u
		store_user_key(request, response, self.ivr_pin)
		request.COOKIES['ss'] = response.cookies['ss'].value

		m_get = SecureTestMessage.objects.get(pk=m.pk)
		m_body = decrypt_object(request, m_get, ivr=True)

		self.assertEqual(m_body, self.clear_text)

		# Set up a fake IVR request object.
		ivr_request = HttpRequest()
		ivr_request.session = dict()
		ivr_response = HttpResponse()
		ivr_request.user = u
		store_user_key(ivr_request, ivr_response, self.ivr_pin)
		ivr_request.COOKIES['ss'] = ivr_response.cookies['ss'].value

		ivr_m_get = SecureTestMessage.objects.get(pk=m.pk)
		ivr_m_body = decrypt_object(ivr_request, ivr_m_get, ivr=True)

		self.assertEqual(ivr_m_body, self.clear_text)


class OwnerKeyTests(TestCase):
	""" OwnerKeyTests unittester for creating a user's RSA key, decrypting it and
	using public key to encrypt/decrypt aes random key for aes message decryption.
	"""
	def setUp(self):
		# create users
		self.provider = test_create_provider('healmeister', 'hmesiter@doc.com',
			'heal', 'meister', 'healme', '4085551212')
		self.adminguy = test_create_provider('docholiday', 'doc@holiday.com',
			'doc', 'holiday', 'demo', '4085551213')
		self.adminguy.is_staff = self.adminguy.is_superuser = True
		self.adminguy.save()
		self.drbob = test_create_provider('drbob', 'drbob@doc.com',
			'doctor', 'bob', 'bobman', '4085551214')
		Administrator.objects.create(user=self.adminguy)
		generate_keys_for_users(output=devnull)
		generate_keys_for_users(output=devnull)  # again for coverage and behavior

	def tearDown(self):
		User.objects.all().delete()
		Provider.objects.all().delete()
		Administrator.objects.all().delete()
		OwnerPublicKey.objects.all().delete()
		UserPrivateKey.objects.all().delete()
		EncryptedObject.objects.all().delete()

	def test_key_pair_fetch(self):
		""" Just for fun, normally using RSA for AES key en/decryption. """
		cleartext = 'Something fishy...'
		user = MHLUser.objects.get(username=self.provider.user.username)

		opub = OwnerPublicKey.objects.get_pubkey(owner=user)
		upriv = UserPrivateKey.objects.get_privkey(user=user, opub=opub)
		# we store keys in PEM format so import
		pubkey = import_rsa(upriv.opub.publickey)
		rsa = import_rsa(upriv.privatekey, strengthen_key(settings.SECRET_KEY if
			upriv.gfather else 'healme'))
		# pubkey enc/dec low level, PKCS1_OAEP w/RSA in production
		ciphertext = pubkey.encrypt(cleartext, os.urandom)[0]
		decrypted_text = rsa.decrypt(ciphertext)
		self.assertEqual(cleartext, decrypted_text)

	def test_login_and_rsa_key_import_export(self):
		c = self.client
		response = c.post('/login/', {'username': 'healmeister', 'password': 'healme'})
		self.assertEqual(response.status_code, 302)
		# just extra verification we can get user from django auth
		user = authenticate(username='healmeister', password='healme')
		user = MHLUser.objects.get(id=user.id)
		# verify we are logged in
		self.assertEqual(c.session['_auth_user_id'], user.id)
		# These should match:
		self.assertEqual(get_user_key(c, response.cookies['ss'].value),
				strengthen_key('healme'))
		# query our KeyPair we created in setup
		opub = OwnerPublicKey.objects.get_pubkey(owner=user)
		upriv = UserPrivateKey.objects.get_privkey(user=user, opub=opub)
		devnull.write(unicode(upriv))  # simulate __unicode__
		# grab pubkey from db its in RSA export format but double test import/export
		pub_key_from_db = export_rsa(import_rsa(upriv.opub.publickey).publickey())
		# grab our binary user credential
		creds = get_user_key(c, response.cookies['ss'].value)
		# properly import
		rsa_key = import_rsa(upriv.privatekey, creds)
		# verify we can properly create RSA objs by importing
		pub_key_from_key = export_rsa(rsa_key.publickey())
		# verify match
		self.assertEqual(pub_key_from_db, pub_key_from_key)
		# now test decryption of key with admin credentials
		creds = strengthen_key(ADMIN_PASSWORD)
		admin_rsa = import_rsa(ADMIN_RESET_ENCD_RSA, creds)
		adminclear = PKCS1_OAEP.new(admin_rsa).decrypt(b64decode(upriv.opub.admincipher))
		rsa_key = import_rsa(upriv.opub.adminscopy, adminclear)
		# verify match
		self.assertEqual(pub_key_from_db, export_rsa(rsa_key.publickey()))
		# now logout, we can alternatively call c.post('/logout/')
		response = c.logout()
		self.assertTrue('_auth_user_id' not in c.session)

	def test_secure_message(self):
		cleartext = "I drive a Dodge Stratus, don't tell anyone."
		c = self.client
		response = c.post('/login/', {'username': 'healmeister', 'password': 'healme'})
		c.COOKIES = {'ss': response.cookies['ss'].value}
		self.assertEqual(response.status_code, 302)
		# just extra verification we can get user from django auth
		c.user = authenticate(username='healmeister', password='healme')
		c.user = MHLUser.objects.get(id=c.user.id)
		# verify we are logged in
		self.assertEqual(c.session['_auth_user_id'], c.user.id)
		# These should match:
		self.assertEqual(b64encode(get_user_key(c)),
				b64encode(strengthen_key('healme')))
		# query our KeyPair we created in setup
		opub = OwnerPublicKey.objects.get_pubkey(owner=c.user)
		with self.assertRaises(AttributeError):
			encrypt_object(str, {}, "boo")
		# NOTE: encrypt_object leaks m._key but using that fact to test this for now
		msg = encrypt_object(SecureTestMessage, {}, cleartext)
		# verify keys don't exist:
		exists = check_keys_exist_for_users(msg, [c.user])
		self.assertEqual(exists, False)
		with self.assertRaises(Exception):
			gen_keys_for_users(msg, [c.user], None, None)
		gen_keys_for_users(msg, [c.user], None, c, ivr=True)  # does both default & ivr
		# test with cache
		gen_keys_for_users(msg, [self.drbob], msg._key, c)
		msg._key = None  # uncache, test with diff user
		gen_keys_for_users(msg, [self.adminguy], None, c)
		# verify keys do exist:
		exists = check_keys_exist_for_users(msg, [c.user])
		self.assertEqual(exists, True)
		exists = check_keys_exist_for_users(msg, [c.user, self.adminguy])
		self.assertEqual(exists, True)
		# time passes by .... now decrypt it
		encobj = EncryptedObject.objects.get_object(msg, opub)
		# do step by step instead of helper decrypt_object
		opub = OwnerPublicKey.objects.get_pubkey(owner=c.user)
		upriv = UserPrivateKey.objects.get(user=c.user, opub=opub)
		creds = get_user_key(c, response.cookies['ss'].value)
		clearkey = encobj.decrypt_cipherkey(upriv, creds)
		self.assertEqual(clearkey, decrypt_cipherkey(c, msg))
		# now call the object's decrypt method
		decrypted_cleartext = msg.decrypt(c, clearkey)
		# verify they do match after decryption
		self.assertTrue(decrypted_cleartext == cleartext)
		# now try calling top level helper decrypt_object and verify
		decrypted_cleartext = decrypt_object(c, msg)
		# verify they do match after decryption
		self.assertTrue(decrypted_cleartext == cleartext)
		# try calling encobj's decrypt with invalid creds
		with self.assertRaises(KeyInvalidException):
			decrypt_object(c, msg, ss="malarkey")
		# create encrypted object without encrypting
		msg2 = encrypt_object(SecureTestMessage, {})
		self.assertTrue(len(msg2.ciphertext) == 0)
		# now logout, we can alternatively call c.post('/logout/')
		response = c.logout()
		self.assertTrue('_auth_user_id' not in c.session)
		# test str rep of opub
		self.assertEqual(unicode(opub), u"%s, key type: %s" %
			(c.user, RSA_TYPES[opub.keytype]), opub)
		### tickle the admin interface with all the objs created in this UT ###
		response = c.post('/login/', {'username': 'docholiday', 'password': 'demo'})
		user = authenticate(username='docholiday', password='demo')
		opub = OwnerPublicKey.objects.get_pubkey(owner=user)
		url = reverse("admin:%s_%s_change" %
			(opub._meta.app_label, opub._meta.module_name), args=[opub.id])
		response = c.get(url)
		upriv = opub.userprivatekey.get()
		url = reverse("admin:%s_%s_change" %
			(upriv._meta.app_label, upriv._meta.module_name), args=[upriv.id])
		response = c.get(url)
		encobj = EncryptedObject.objects.all()[0]
		url = reverse("admin:%s_%s_change" %
			(encobj._meta.app_label, encobj._meta.module_name), args=[encobj.id])
		response = c.get(url)
		response = c.logout()

	def test_rekey_reset(self):
		cleartext = "Who is the best super hero of all time?"
		c = self.client
		response = c.post('/login/', {'username': 'healmeister', 'password': 'healme'})
		self.assertEqual(response.status_code, 302)
		# just extra verification we can get user from django auth
		user = authenticate(username='healmeister', password='healme')
		user = MHLUser.objects.get(id=user.id)
		# verify we are logged in
		self.assertEqual(c.session['_auth_user_id'], user.id)
		# get users' public key
		opub = OwnerPublicKey.objects.get_pubkey(owner=user)
		# encrypt_object encrypts w/user pub key
		msg = encrypt_object(SecureTestMessage, {}, cleartext, opub)
		# encrypt_object() creates EncryptedObject
		encobj = EncryptedObject.objects.get_object(msg, opub)
		# test decryption of keys with user's credentials when not grandfathered
		upriv = UserPrivateKey.objects.get(user=user, opub=opub)
		clearkey = encobj.decrypt_cipherkey(upriv, strengthen_key('healme'))
		# now call the object's decrypt method
		decrypted_cleartext = msg.decrypt(c, clearkey)
		# verify they do match after decryption
		self.assertTrue(decrypted_cleartext == cleartext)
		# get admin reset key
		creds = strengthen_key(ADMIN_PASSWORD)
		admin_rsa = import_rsa(ADMIN_RESET_ENCD_RSA, creds)
		privs = UserPrivateKey.objects.filter(user=user, credtype=CRED_WEBAPP)
		reset_keys(privs, admin_rsa)
		# fetch the encrypted object again but decrypt with initial settings
		encobj = EncryptedObject.objects.get_object(msg, opub)
		# test decryption with initial credentials when grandfathered
		upriv = UserPrivateKey.objects.get(user=user, opub=opub)
		clearkey = encobj.decrypt_cipherkey(upriv, strengthen_key(settings.SECRET_KEY))
		# now call the object's decrypt method
		decrypted_cleartext = msg.decrypt(c, clearkey)
		# verify they do match after decryption
		self.assertTrue(decrypted_cleartext == cleartext)
		# now logout, we can alternatively call c.post('/logout/')
		response = c.logout()
		self.assertTrue('_auth_user_id' not in c.session)
		# try resetting admins keys
		privs = UserPrivateKey.objects.filter(user=self.adminguy, credtype=CRED_WEBAPP)
		reset_keys(privs, admin_rsa)
		# test str rep of encobj
		self.assertEqual(unicode(encobj), u"SecureTestMessage object %s, key type: %s"
			% (user, RSA_TYPES[encobj.opub.keytype]), encobj)

	def test_regen_invalid_keys(self):
		from MHLogin.KMS.shortcuts import regen_invalid_keys_for_users
		c = self.client
		cleartext = "I enjoy going to tax seminars."
		response = c.post('/login/', {'username': 'healmeister', 'password': 'healme'})
		self.assertEqual(response.status_code, 302)
		# just extra verification we can get user from django auth
		user = authenticate(username='healmeister', password='healme')
		# verify we are logged in
		self.assertEqual(c.session['_auth_user_id'], user.id)
		opub = OwnerPublicKey.objects.get_pubkey(owner=user)
		# NOTE: encrypt_object leaks m._key but using that fact to test this for now
		msg = encrypt_object(SecureTestMessage, {}, cleartext, opub)
		# regen key (just regen don't re-encrypt object, for another test)
		regen_invalid_keys_for_users(msg, [user])
		msg_type = ContentType.objects.get_for_model(msg)
		EncryptedObject.objects.filter(object_type=msg_type, object_id=msg.id).delete()
		# simulate re-creation of encrypted objects and singleton cast to array
		regen_invalid_keys_for_users(msg, [user])
		# logout. cleanup
		response = c.logout()
		self.assertTrue('_auth_user_id' not in c.session)

	def test_recovery_key_generation(self):
		c = self.client
		recovery = generate_recovery(self.adminguy, None)
		self.assertTrue(recovery != None)  # all keys still g'fathered so true
		response = c.post('/login/', {'username': 'docholiday', 'password': 'demo'})
		self.assertEqual(response.status_code, 302)
		# just extra verification we can get user from django auth
		user = authenticate(username='docholiday', password='demo')
		# verify we are logged in
		self.assertEqual(c.session['_auth_user_id'], user.id)
		# get admin reset private key
		creds = strengthen_key(ADMIN_PASSWORD)
		admin_rsa = import_rsa(ADMIN_RESET_ENCD_RSA, creds)
		recovery = generate_recovery(self.adminguy, admin_rsa)
		self.assertTrue(recovery != None)
		recovery = generate_recovery(self.adminguy, None)
		self.assertTrue(recovery == None)  # not all keys g'fathered now
		# test recovery on regular user
		recovery = generate_recovery(self.provider, admin_rsa)
		self.assertTrue(recovery != None)
		# logout. cleanup
		response = c.logout()
		self.assertTrue('_auth_user_id' not in c.session)

	def test_change_IVR_pin_via_web_creds(self):
		c = self.client
		# after successful login should get re-direct to /
		response = c.post('/login/', {'username': 'healmeister', 'password': 'healme'})
		self.assertEqual(response.status_code, 302)
		# just extra verification we can get user from django auth
		user = authenticate(username='healmeister', password='healme')
		user = MHLUser.objects.get(id=user.id)
		# verify we are logged in
		self.assertEqual(c.session['_auth_user_id'], user.id)
		# set cookies first for request object then change pin via web
		c.COOKIES = {'ss': response.cookies['ss'].value}
		recrypt_ivr_key_via_web_creds(user, c, '5678')
		# logout. cleanup
		response = c.logout()
		self.assertTrue('_auth_user_id' not in c.session)

	def test_gen_new_keys(self):
		cleartext = "A sql query walks in to a bar, approaches two tables and asks 'may I join you?'"
		c = self.client
		# after successful login should get re-direct to /
		response = c.post('/login/', {'username': 'healmeister', 'password': 'healme'})
		c.COOKIES = {'ss': response.cookies['ss'].value}
		self.assertEqual(response.status_code, 302)
		# just extra verification we can get user from django auth
		c.user = authenticate(username='healmeister', password='healme')
		c.user = MHLUser.objects.get(id=c.user.id)
		msg = encrypt_object(SecureTestMessage, {}, cleartext)
		gen_keys_for_users(msg, [c.user], None, c, ivr=True)
		generate_new_user_keys(c.user, 'monkey')
		c.user.set_password('monkey')
		c.user.save()
		# logout. cleanup
		response = c.logout()
		# simulate admin update invalid keys
		creds = strengthen_key(ADMIN_PASSWORD)
		admin_rsa = import_rsa(ADMIN_RESET_ENCD_RSA, creds)
		reset_user_invalid_keys(MHLUser.objects.get(id=c.user.id), admin_rsa)
		# login with new password and verify we can decrypt message
		response = c.post('/login/', {'username': 'healmeister', 'password': 'monkey'})
		c.COOKIES = {'ss': response.cookies['ss'].value}
		self.assertEqual(response.status_code, 302)
		# just extra verification we can get user from django auth
		c.user = authenticate(username='healmeister', password='monkey')
		# verify we are logged in
		self.assertEqual(c.session['_auth_user_id'], c.user.id)
		decrypted_cleartext = decrypt_object(c, msg)
		self.assertEqual(decrypted_cleartext, cleartext)
		response = c.logout()

	def test_static_reset(self):
		# new way will obsolete test_gen_new_keys when rm #2115 in
		cleartext = "We never really grow up, we only learn how to act in public."
		c = self.client
		# after successful login should get re-direct to /
		response = c.post('/login/', {'username': 'healmeister', 'password': 'healme'})
		c.COOKIES = {'ss': response.cookies['ss'].value}
		c.user = authenticate(username='healmeister', password='healme')
		c.user = MHLUser.objects.get(id=c.user.id)
		opub = OwnerPublicKey.objects.get_pubkey(owner=c.user)
		msg = encrypt_object(SecureTestMessage, {}, cleartext, opub)
		c.user.set_password('gorilla')
		c.user.save()
		creds = strengthen_key(ADMIN_PASSWORD)
		admin_rsa = import_rsa(ADMIN_RESET_ENCD_RSA, creds)
		privs = UserPrivateKey.objects.filter(user=c.user, credtype=CRED_WEBAPP)
		reset_keys(privs, admin_rsa, 'gorilla')
		c.logout()
		response = c.post('/login/', {'username': 'healmeister', 'password': 'gorilla'})
		c.COOKIES = {'ss': response.cookies['ss'].value}
		decrypted_cleartext = decrypt_object(c, msg)
		self.assertEqual(decrypted_cleartext, cleartext)
		msg.id += 1
		with self.assertRaises(KeyInvalidException):
			decrypt_object(c, msg)
		response = c.logout()

	def test_admin_API_shortcuts(self):
		# TODO: functions in this test to use common api from utils or shortcuts
		cleartext = "42: the answer to life the universe and everything."
		c = self.client
		response = c.post('/login/', {'username': 'healmeister', 'password': 'healme'})
		c.COOKIES = {'ss': response.cookies['ss'].value}
		self.assertEqual(response.status_code, 302)
		# just extra verification we can get user from django auth
		c.user = authenticate(username='healmeister', password='healme')
		c.user = MHLUser.objects.get(id=c.user.id)
		opub = OwnerPublicKey.objects.get_pubkey(owner=c.user)
		msg = encrypt_object(SecureTestMessage, {}, cleartext, opub)
		upriv = UserPrivateKey.objects.get_privkey(c.user, opub)
		# fetch something that shouldn't exist as encrypted data
		notthere = admin_decrypt_cipherkey(ADMIN_PASSWORD, c.user)
		self.assertTrue(notthere == None)
		clearkey1 = admin_decrypt_cipherkey(ADMIN_PASSWORD, msg)
		encobj = EncryptedObject.objects.get_object(msg, opub)
		# import upriv.privatekey with credentials and decrypt cipherkey
		clearkey2 = encobj.decrypt_cipherkey(upriv, get_user_key(c))
		self.assertTrue(clearkey1 == clearkey2)
		clearkey = admin_decrypt_cipherkey(ADMIN_PASSWORD, msg)
		cleartext2 = msg.decrypt(None, clearkey)
		self.assertTrue(cleartext == cleartext2)

	def test_rsa_encryption_decryption(self):
		from base64 import b16encode
		from Crypto.Util.number import bytes_to_long, long_to_bytes

		output = devnull  # sys.stderr
		rsa = RSA.generate(2048, os.urandom)
		pubkey = rsa.publickey()
		# OK CASE:
		clearkey = str(bytearray.fromhex(
			'6162303132333435363738393031323334353637383930313233343536373839'))
		cipherkey = pubkey.encrypt(clearkey, os.urandom)[0]
		output.write("\nHexdump of clearkey input:\n%s\nHexdump of cipher output(len):\n%s (%d)" % \
			(b16encode(clearkey), b16encode(cipherkey), len(b16encode(cipherkey)) / 2))
		clearkey = rsa.decrypt(cipherkey)
		output.write("\nHexdump of cipherkey after decryption (OK):\n%s" % \
			(b16encode(clearkey)))
		# FAIL CASE:
		clearkey = str(bytearray.fromhex(
			'0000303132333435363738393031323334353637383930313233343536373839'))
		cipherkey = pubkey.encrypt(clearkey, os.urandom)[0]
		output.write("\n\n\nHexdump of clearkey input (with leading null bytes):\n%s\nHexdump "
			"of cipherkey(len):\n%s (%d)" % (b16encode(clearkey), b16encode(cipherkey),
				len(b16encode(cipherkey)) / 2))
		clearkey = rsa.decrypt(cipherkey)
		output.write("\nHexdump of clearinput after decryption (FAIL):\n%s" % \
			(b16encode(clearkey)))
		# NEW CASE: (OK with leading 0's when we pass long to encrypt instead of str)
		clearkey = str(bytearray.fromhex(
			'0000303132333435363738393031323334353637383930313233343536373839'))
		# need to convert to str for database storage - and back to long during decrypt
		cipherkey = str(pubkey.encrypt(bytes_to_long(clearkey), os.urandom)[0])
		output.write("\n\n\nHexdump of clearkey input (with leading null bytes):\n%s\nHexdump "
			"of cipherkey(len):\n%s (%d)" % (b16encode(clearkey), b16encode(long_to_bytes(cipherkey)),
				len(b16encode(str(long_to_bytes(cipherkey)))) / 2))
		clearkey = long_to_bytes(rsa.decrypt(long(cipherkey)), 32)  # and blocksize 32
		output.write("\nHexdump of clearinput after decryption (OK, no padding!!):\n%s" % \
			(b16encode(clearkey)))

		setup = \
'''
import os
import Crypto.PublicKey.RSA as RSA

from base64 import b64encode, b64decode, b16encode
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Util.number import bytes_to_long, long_to_bytes

rsa = RSA.generate(2048, os.urandom)
pubkey = rsa.publickey()
clearkey = bytearray.fromhex(
	'0000303132333435363738393031323334353637383930313233343536373839')
clearkey = str(clearkey)
'''
		stmt1 = \
'''  # match as close as possible when we do read/writes to db
cipherkey = b64encode(pubkey.encrypt(clearkey, os.urandom)[0])
clearkey = rsa.decrypt(b64decode(cipherkey))
if len(clearkey) < 32:  # simulate checking < 32 bytes
	pass
'''
		stmt2 = \
'''  # match as close as possible when we do read/writes to db
cipherkey = pubkey.encrypt(bytes_to_long(clearkey), os.urandom)[0]
clearkey = long_to_bytes(rsa.decrypt(long(cipherkey)), 32)  # and blocksize 32
'''
		stmt3 = \
'''  # match as close as possible when we do read/writes to db
cipherkey = b64encode(PKCS1_OAEP.new(pubkey).encrypt(clearkey))
clearkey = PKCS1_OAEP.new(rsa).decrypt(b64decode(cipherkey))
'''
		import timeit
		output = devnull  # sys.stderr
		repeat = 1  # 5000
		output.write("\n\nTiming: 1st what we did:\n")
		result = timeit.timeit(stmt=stmt1, setup=setup, number=repeat)
		output.write("\nSeconds: %s\n" % str(result))
		output.write("\n\nTiming: 2nd using long_to_bytes:\n")
		result = timeit.timeit(stmt=stmt2, setup=setup, number=repeat)
		output.write("\nSeconds: %s\n" % str(result))
		output.write("\n\nTiming: 3rd with PKCS1:\n")
		result = timeit.timeit(stmt=stmt3, setup=setup, number=repeat)
		output.write("\nSeconds: %s\n" % str(result))

	def test_new_strengthen(self):
		setup = \
'''
import hashlib
import sys
from time import mktime
from datetime import datetime
from django.utils.crypto import pbkdf2
now = datetime.now()
id = 22
password = 'monkey'
'''

		stmt1 = \
'''
salt = 'Ieth1avu'
salt = ''.join([str(mktime(now.timetuple())), str(id), salt])
pbkdf2(password, salt, iterations=10000)
'''
		stmt2 = \
'''
salt = 'Ieth1avu'
rounds = 4
sha_lib = hashlib.sha1()
md5_lib = hashlib.md5()
for i in range(rounds):
	key = ''.join([password, salt])
	sha_lib.update(password)
	md5_lib.update(password)
	password = ''.join([sha_lib.digest(), md5_lib.digest()[:12]])
'''
		import timeit
		output = devnull  # sys.stderr
		repeat = 10  # 5000
		output.write("\n\nTiming: new pbkdf2:\n")
		result = timeit.timeit(stmt=stmt1, setup=setup, number=repeat)
		output.write("\nSeconds: %s\n" % str(result))

		output.write("\n\nTiming: old sha/md5:\n")
		result = timeit.timeit(stmt=stmt2, setup=setup, number=repeat)
		output.write("\nSeconds: %s\n" % str(result))

	def test_alters(self):
		# add this to alters when we enable unique_together for OwnerPublickKey
		''' TODO:
		ALTER TABLE KMS_ownerpublickey
			ADD CONSTRAINT owner_type_id UNIQUE (owner_type_id, owner_id, keytype);
		'''

##########################################################################################
############ Previous KMS Unittests: To be removed once integration complete #############
##########################################################################################


class RSAKeyPairTests(unittest.TestCase):
	# Configuration
	rsa_key = strengthen_key('foobazbar')
	clear_text = 'This is my message'

	@classmethod
	def setUpClass(cls):
		""" Create a User to link the keypair to. """
		cls.u = u = User(username="RSAKeyPairTestsUser")
		u.save()

		cls.key_pair = key_pair = RSAKeyPair(key=cls.rsa_key)
		u = User.objects.get(username="RSAKeyPairTestsUser")
		key_pair.owner = u
		key_pair.save()

	@classmethod
	def tearDownClass(self):
		User.objects.all().delete()
		Provider.objects.all().delete()
		Administrator.objects.all().delete()
		OwnerPublicKey.objects.all().delete()
		UserPrivateKey.objects.all().delete()
		EncryptedObject.objects.all().delete()

	def test_key_pair_fetch(self):
		u = User.objects.get(username="RSAKeyPairTestsUser")

		key_pair = RSAKeyPair.objects.get(owner=u)
		pub_key = RSAPubKey.objects.get(owner=u)

		cipher_text = pub_key.encrypt(self.clear_text)
		decrypted_text = key_pair.decrypt(cipher_text, key=self.rsa_key)
		self.assertEqual(self.clear_text, decrypted_text)

	def test_wrong_key(self):
		u = User.objects.get(username="RSAKeyPairTestsUser")

		key_pair = RSAKeyPair.objects.get(owner=u)
		pub_key = RSAPubKey.objects.get(owner=u)

		cipher_text = pub_key.encrypt(self.clear_text)
		self.assertRaises(KeyInvalidException, key_pair.decrypt, cipher_text,
					key=strengthen_key('thisisanincorrectpassword'))

	def test_invalid_key_lengths(self):
		self.assertRaises(KeyInvalidException, RSAKeyPair,
					key='thisisareallyobnoxiouslylongpasswordthatreallyoughttobetoolong!')
		self.assertRaises(KeyInvalidException, RSAKeyPair, key='')


class IVR_RSAKeyPairTests(unittest.TestCase):

	# Configuration
	rsa_key = strengthen_key('foobazbar')
	clear_text = 'This is my message'

	@classmethod
	def setUpClass(cls):
		""" Create a User to link the keypair to. """
		cls.u = u = User(username="IVR_RSAKeyPairTestsUser")
		u.save()

		key_pair = IVR_RSAKeyPair(key=cls.rsa_key)
		u = User.objects.get(username="IVR_RSAKeyPairTestsUser")
		key_pair.owner = u
		key_pair.save()
		cls.key_pair = key_pair

	@classmethod
	def tearDownClass(self):
		User.objects.all().delete()
		Provider.objects.all().delete()
		Administrator.objects.all().delete()
		OwnerPublicKey.objects.all().delete()
		UserPrivateKey.objects.all().delete()
		EncryptedObject.objects.all().delete()

	def setUp(self):
		# Check to ensure that the RSA Public Key is automatically stored.
		self.assertTrue(IVR_RSAPubKey.objects.filter(key_pair=self.key_pair).exists())

	def test_key_pair_fetch(self):
		u = User.objects.get(username="IVR_RSAKeyPairTestsUser")

		key_pair = IVR_RSAKeyPair.objects.get(owner=u)
		pub_key = IVR_RSAPubKey.objects.get(owner=u)

		cipher_text = pub_key.encrypt(self.clear_text)
		decrypted_text = key_pair.decrypt(cipher_text, key=self.rsa_key)
		self.assertEqual(self.clear_text, decrypted_text)

	def test_wrong_key(self):
		u = User.objects.get(username="IVR_RSAKeyPairTestsUser")

		key_pair = IVR_RSAKeyPair.objects.get(owner=u)
		pub_key = IVR_RSAPubKey.objects.get(owner=u)

		cipher_text = pub_key.encrypt(self.clear_text)
		self.assertRaises(KeyInvalidException, key_pair.decrypt, cipher_text,
					key=strengthen_key('thisisanincorrectpassword'))

	def test_invalid_key_lengths(self):
		self.assertRaises(KeyInvalidException, IVR_RSAKeyPair,
					key='thisisareallyobnoxiouslylongpasswordthatreallyoughttobetoolong!')
		self.assertRaises(KeyInvalidException, IVR_RSAKeyPair, key='')


class CombinedRSAKeyPairTests(unittest.TestCase):
	"""
	Tests to ensure that both non-IVR and IVR keys work together.
	"""
	# Configuration
	rsa_key = strengthen_key('foobazbar')
	ivr_rsa_key = strengthen_key('123456')
	clear_text = 'This is my message'

	@classmethod
	def setUpClass(cls):
		""" Create a User to link the keypair to. """
		cls.u = u = User(username="CombinedKeyPairTestsUser")
		u.save()

		u = User.objects.get(username="CombinedKeyPairTestsUser")

		ivr_key_pair = IVR_RSAKeyPair(key=cls.ivr_rsa_key)
		ivr_key_pair.owner = u
		ivr_key_pair.save()

		key_pair = RSAKeyPair(key=cls.rsa_key)
		key_pair.owner = u
		key_pair.save()

	@classmethod
	def tearDownClass(self):
		User.objects.all().delete()
		Provider.objects.all().delete()
		Administrator.objects.all().delete()
		OwnerPublicKey.objects.all().delete()
		UserPrivateKey.objects.all().delete()
		EncryptedObject.objects.all().delete()

	def test_key_pair_fetch(self):
		u = User.objects.get(username="CombinedKeyPairTestsUser")

		key_pair = IVR_RSAKeyPair.objects.get(owner=u)
		pub_key = IVR_RSAPubKey.objects.get(owner=u)

		cipher_text = pub_key.encrypt(self.clear_text)
		decrypted_text = key_pair.decrypt(cipher_text, key=self.ivr_rsa_key)
		self.assertEqual(self.clear_text, decrypted_text)

		key_pair = RSAKeyPair.objects.get(owner=u)
		pub_key = RSAPubKey.objects.get(owner=u)

		cipher_text = pub_key.encrypt(self.clear_text)
		decrypted_text = key_pair.decrypt(cipher_text, key=self.rsa_key)
		self.assertEqual(self.clear_text, decrypted_text)

	def test_wrong_key(self):
		u = User.objects.get(username="CombinedKeyPairTestsUser")

		key_pair = IVR_RSAKeyPair.objects.get(owner=u)
		pub_key = IVR_RSAPubKey.objects.get(owner=u)

		cipher_text = pub_key.encrypt(self.clear_text)
		self.assertRaises(KeyInvalidException, key_pair.decrypt, cipher_text,
					key=strengthen_key('thisisanincorrectpassword'))
		key_pair = RSAKeyPair.objects.get(owner=u)
		pub_key = RSAPubKey.objects.get(owner=u)

		cipher_text = pub_key.encrypt(self.clear_text)
		self.assertRaises(KeyInvalidException, key_pair.decrypt, cipher_text,
					key=strengthen_key('thisisanincorrectpassword'))

	def test_invalid_key_lengths(self):
		self.assertRaises(KeyInvalidException, IVR_RSAKeyPair,
			key='thisisareallyobnoxiouslylongpasswordthatreallyoughttobetoolong!')
		self.assertRaises(KeyInvalidException, IVR_RSAKeyPair, key='')
		self.assertRaises(KeyInvalidException, RSAKeyPair,
			key='thisisareallyobnoxiouslylongpasswordthatreallyoughttobetoolong!')
		self.assertRaises(KeyInvalidException, RSAKeyPair, key='')

	def test_shortcut_encrypt(self):
		pass

	def test_shortcut_decrypt(self):
		pass


class PrivateKeyTests(unittest.TestCase):
	# Configuration
	rsa_key = strengthen_key('foobazbar')
	aes_key = strengthen_key('this is my secure passphrase')
	clear_text = 'This is my message. There are many others like it, but this one is mine.'

	@classmethod
	def setUpClass(cls):
		""" Create a User to link the private key to. """
		u = User(username="PrivateKeyTests")
		u.save()

		key_pair = RSAKeyPair(key=cls.rsa_key)
		key_pair.owner = u
		key_pair.save()

		key_pair = IVR_RSAKeyPair(key=cls.rsa_key)
		key_pair.owner = u
		key_pair.save()

	@classmethod
	def tearDownClass(cls):
		User.objects.all().delete()
		Provider.objects.all().delete()
		Administrator.objects.all().delete()
		OwnerPublicKey.objects.all().delete()
		UserPrivateKey.objects.all().delete()
		EncryptedObject.objects.all().delete()

	def test_PrivateKey(self):
		u = User.objects.get(username="PrivateKeyTests")
		RSAKeyPair.objects.get(owner=u)
		RSAPubKey.objects.get(owner=u)

		msg = SecureTestMessage.objects.create(owner=u)
		msg.encrypt(self.clear_text, self.aes_key)
		msg.save()

		private_key = PrivateKey(owner=u, object=msg, key=self.aes_key)
		private_key.save()

		object_type = ContentType.objects.get_for_model(msg)

		private_key = PrivateKey.objects.get(owner=u, object_type=object_type, object_id=msg.id)

		decrypted_text = private_key.decrypt(None, key=self.rsa_key)
		self.assertEqual(decrypted_text, self.clear_text)

		# Admin private key tests
		aes_key = strengthen_key(ADMIN_PASSWORD)

		msg = SecureTestMessage.objects.create(owner=None)
		msg.encrypt(self.clear_text, aes_key)
		msg.save()

		private_key = AdminPrivateKey(key=strengthen_key(ADMIN_PASSWORD))
		private_key.object = msg
		private_key.save()

		decrypted_text = private_key.decrypt(None, strengthen_key(ADMIN_PASSWORD))
		self.assertEqual(decrypted_text, self.clear_text)

	def test_IVRPrivateKey(self):
		u = User.objects.get(username="PrivateKeyTests")
		IVR_RSAKeyPair.objects.get(owner=u)
		IVR_RSAPubKey.objects.get(owner=u)

		msg = SecureTestMessage.objects.create(owner=u)
		msg.encrypt(self.clear_text, self.aes_key)
		msg.save()

		private_key = IVR_PrivateKey(owner=u, object=msg, key=self.aes_key)
		private_key.save()

		object_type = ContentType.objects.get_for_model(msg)

		private_key = IVR_PrivateKey.objects.get(owner=u,
					object_type=object_type, object_id=msg.id)

		decrypted_text = private_key.decrypt(None, key=self.rsa_key)
		self.assertEqual(decrypted_text, self.clear_text)

		# Admin private key tests
		aes_key = strengthen_key(ADMIN_PASSWORD)

		msg = SecureTestMessage.objects.create(owner=None)
		msg.encrypt(self.clear_text, aes_key)
		msg.save()

		private_key = AdminPrivateKey(key=strengthen_key(ADMIN_PASSWORD))
		private_key.object = msg
		private_key.save()

		decrypted_text = private_key.decrypt(None, strengthen_key(ADMIN_PASSWORD))
		self.assertEqual(decrypted_text, self.clear_text)

	def test_ConcurrentPrivateKeys(self):
		u = User.objects.get(username="PrivateKeyTests")

		RSAKeyPair.objects.get(owner=u)
		RSAPubKey.objects.get(owner=u)
		IVR_RSAKeyPair.objects.get(owner=u)
		IVR_RSAPubKey.objects.get(owner=u)

		msg = SecureTestMessage.objects.create(owner=u)
		msg.encrypt(self.clear_text, self.aes_key)
		msg.save()

		object_type = ContentType.objects.get_for_model(msg)

		private_key = PrivateKey(owner=u, object=msg, key=self.aes_key)
		private_key.save()
		ivr_private_key = IVR_PrivateKey(owner=u, object=msg, key=self.aes_key)
		ivr_private_key.save()

		private_key = PrivateKey.objects.get(owner=u, object_type=object_type, object_id=msg.id)
		ivr_private_key = IVR_PrivateKey.objects.get(owner=u,
				object_type=object_type, object_id=msg.id)

		decrypted_text = private_key.decrypt(None, key=self.rsa_key)
		self.assertEqual(decrypted_text, self.clear_text)
		decrypted_text = ivr_private_key.decrypt(None, key=self.rsa_key)
		self.assertEqual(decrypted_text, self.clear_text)

		# Admin private key tests
		aes_key = strengthen_key(ADMIN_PASSWORD)

		msg = SecureTestMessage.objects.create(owner=None)
		msg.encrypt(self.clear_text, aes_key)
		msg.save()

		private_key = AdminPrivateKey(key=strengthen_key(ADMIN_PASSWORD))
		private_key.object = msg
		private_key.save()

		decrypted_text = private_key.decrypt(None, strengthen_key(ADMIN_PASSWORD))
		self.assertEqual(decrypted_text, self.clear_text)

	def test_IncorrectPassword(self):
		u = User.objects.get(username="PrivateKeyTests")
		RSAKeyPair.objects.get(owner=u)
		RSAPubKey.objects.get(owner=u)

		msg = SecureTestMessage.objects.create(owner=u)
		msg.encrypt(self.clear_text, self.aes_key)
		msg.save()

		private_key = PrivateKey(owner=u, object=msg, key=self.aes_key)
		private_key.save()

		self.assertRaises(KeyInvalidException, private_key.decrypt, None,
						key=strengthen_key('this is an incorrect password'))

		# Admin private key tests
		aes_key = strengthen_key(ADMIN_PASSWORD)

		msg = SecureTestMessage.objects.create(owner=None)
		msg.encrypt(self.clear_text, aes_key)
		msg.save()

		private_key = AdminPrivateKey(key=strengthen_key(ADMIN_PASSWORD))
		private_key.object = msg
		private_key.save()

		self.assertRaises(KeyInvalidException, private_key.decrypt, None,
						key=strengthen_key('this is an incorrect password'))

