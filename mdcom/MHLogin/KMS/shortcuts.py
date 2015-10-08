
import os
from base64 import b64decode
from Crypto.Cipher import PKCS1_OAEP

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.utils.translation import ugettext as _

from MHLogin.KMS.models import EncryptedObject, OwnerPublicKey, UserPrivateKey, \
	RSA_PRIMARY, RSA_IVR, CRED_IVRPIN, CRED_WEBAPP, export_rsa, import_rsa
from MHLogin.KMS.exceptions import KeyInvalidException
from MHLogin.KMS.utils import get_user_key, strengthen_key


def encrypt_object(klass, init_kwargs, cleartext=None, opub=None):
	""" Top level helper to encrypt data for storage.

	:param klass: db class type to be created and encrypted cleartext to be stored in.
		This class MUST implement def encrypt(self, cleartext, clearkey).
	:param init_kwargs: Dictionary keyword arguments passed to the klass c'tor.
	:param cleartext: Data to encrypt and store in klass instance.  Must be of data
		type klass understands.  If None klass instance created with no encrypted data
	:param opub: publickey to encrypt klass' clearkey or None if just creating klass.
	:raises: AttributeError if klass does not have proper encrypt() method
	"""
	clearkey = os.urandom(32)  # decryption key for AES
	obj = klass(**init_kwargs)
	cleartext and obj.encrypt(cleartext, clearkey)
	obj.save()
	obj._key = clearkey  # cache clearkey
	# if opub None we are just creating obj and encrypting if cleartext non-None
	opub and EncryptedObject.objects.create_object(obj, opub, clearkey)

	return obj


def decrypt_object(request, obj, ivr=False, ss=None, opub=None):
	""" Top level helper to decrypt obj contents.

	:param request: Django request, depends on request.user and request.session['key]
	:param obj: the target, obj's class MUST implement def decrypt(self, request, clearkey)
	:param ivr: for IVR requests query user's IVR public key
	:param ss: secret session key, if None pickup from remote request.COOKIES['ss']
	:param opub: when opub owner is non-user entity (e.g. PracticeLocation)
	:raises: AttributeError if obj does not have proper decrypt() method
	"""
	clearkey = decrypt_cipherkey(request, obj, ivr, ss, opub)
	cleartext = obj.decrypt(request, clearkey)
	return cleartext


def decrypt_cipherkey(request, obj, ivr=False, ss=None, opub=None):
	""" Helper to get EncryptedObject's decrypted cipherkey, i.e. clearkey

	:param request: Django request, depends on request.user and request.session['key]
	:param obj: the target database object
	:param ivr: for IVR requests query user's IVR public key, arg change to credtype in #2281
	:param ss: secure secret, if None pickup remotely i.e. request.COOKIES['ss']
	:param opub: when opub owner is non-user entity, e.g. PracticeLocation
	:raises: KeyInvalidException if wrong creds or no private key exists
	"""
	try:
		keytype = RSA_PRIMARY if not ivr else RSA_IVR
		credtype = CRED_WEBAPP if not ivr else CRED_IVRPIN
		opub = opub or OwnerPublicKey.objects.get_pubkey(owner=request.user, keytype=keytype)
		upriv = UserPrivateKey.objects.get_privkey(request.user, opub, credtype)
		encobj = EncryptedObject.objects.get_object(obj, opub)
		# import upriv.privatekey with credentials and decrypt cipherkey 
		clearkey = encobj.decrypt_cipherkey(upriv, get_user_key(request, ss=ss))
		return clearkey
	except (ValueError, ObjectDoesNotExist, MultipleObjectsReturned):  # normalize
		raise KeyInvalidException("Wrong credentials or no user private key exists.")


def gen_keys_for_users(obj, users, clearkey=None, request=None, ivr=False):
	""" Create EncryptedObject(s) to reference given object and associated user(s).

	:param obj: object the created encrypted object will reference.
	:param users: MHLUser(s) for each an EncryptedObject is created for obj.
	:param clearkey: The clearkey used to decrypt obj contents.  Note: if None
		clearkey must be cached in obj or encrypted object already created.
	:param request: The HttpRequest of a user with access to the encrypted object
		for the object. Note that either this value or clearkey is required.
	:param ivr: If True will create encrypted object with user's IVR public key as well.
	"""
	if not clearkey and not request:
		raise Exception(_('Either clearkey or request arguments are *required*'))
	# if no clearkey check cache or fetch from db
	if not clearkey:
		if '_key' in dir(obj) and obj._key:
			clearkey = obj._key
		else:
			clearkey = decrypt_cipherkey(request, obj, ivr)
			obj._key = clearkey
	# Object already encrypted, generate new EncryptedObjects for users
	for user in users:
		opub = OwnerPublicKey.objects.get_pubkey(owner=user)
		EncryptedObject.objects.create_object(obj, opub, clearkey)

		if ivr:
			opub = OwnerPublicKey.objects.get_pubkey(owner=user, keytype=RSA_IVR)
			EncryptedObject.objects.create_object(obj, opub, clearkey)


def regen_invalid_keys_for_users(obj, users, new_clearkey=None):
	""" Shortcut to re-generate private keys for the given object, for the given users.

	:param obj: The object for which EncryptedObjects should be re-generated
	:param users: List of MHLUser objects for which EncryptedObjects have new clearkey
	:param new_clearkey: The new clear-text private key for this object.
	"""
	new_clearkey = new_clearkey or os.urandom(32)
	ct = ContentType.objects.get_for_model(obj)
	# TESTING_KMS_INTEGRATION - note: old kms did not do for ivr
	for user in users:
		opub = OwnerPublicKey.objects.get_pubkey(owner=user)
		encs = EncryptedObject.objects.filter(object_type=ct, object_id=obj.id, opub=opub)
		if encs.exists():
			[enc.change_cipherkey(opub, new_clearkey) for enc in encs]
		else:
			EncryptedObject.objects.create_object(obj, opub, new_clearkey)

	obj._key = new_clearkey


def check_keys_exist_for_users(obj, users):
	""" Shortcut to check private keys exist or not, for the given users.

	:param obj: The object we are verifying EncryptdObjects exists for users
	:param users: List of MHLUser objects to check, fail on first missing
	"""
	exist = True
	ct = ContentType.objects.get_for_model(obj)
	# TESTING_KMS_INTEGRATION: note: old kms did not do for ivr
	for user in users:
		opub = OwnerPublicKey.objects.get_pubkey(owner=user)
		if not EncryptedObject.objects.filter(opub=opub,
				object_type=ct.id, object_id=obj.id).exists():
			exist = False
			break
	return exist


def recrypt_ivr_key_via_web_creds(user, request, new_pin):
	""" decrypt special web enc'd ivr key then recrypt pin enc'd ivr key with new pin """ 
	opub = OwnerPublicKey.objects.get_pubkey(owner=user, keytype=RSA_IVR)
	uprivw = UserPrivateKey.objects.get_privkey(user, opub, CRED_WEBAPP, gfather=False)
	rsa = import_rsa(uprivw.privatekey, get_user_key(request))
	# ivr pin may still be g'fathered
	uprivi = UserPrivateKey.objects.get_privkey(user, opub, CRED_IVRPIN)
	uprivi.privatekey = export_rsa(rsa, strengthen_key(new_pin))
	uprivi.gfather = False
	uprivi.save()


def admin_decrypt_cipherkey(admin_creds, obj):
	""" ADMIN UTILITY, TODO: move this to black box, rm #2115 """
	clearkey = None
	ct = ContentType.objects.get_for_model(obj)
	encobj = EncryptedObject.objects.filter(object_type=ct, object_id=obj.pk)
	if encobj.exists():
		from MHLogin._admin_reset import ADMIN_RESET_ENCD_RSA
		admin_rsa = import_rsa(ADMIN_RESET_ENCD_RSA, strengthen_key(admin_creds))
		# get first match since we are decrypting admincipher
		opub = encobj[0].opub
		# decrypt adminscopy rsa key for this encd object
		adminclearkey = PKCS1_OAEP.new(admin_rsa).decrypt(b64decode(opub.admincipher))
		rsa = import_rsa(opub.adminscopy, adminclearkey)
		# finally, decrypt encobj's cipherkey with decrypted admins rsa copy
		clearkey = PKCS1_OAEP.new(rsa).decrypt(b64decode(encobj[0].cipherkey))

	return clearkey
