
import os
import sys
import hashlib

from base64 import b16encode, b64encode, b64decode
from Crypto.Cipher import AES, XOR, PKCS1_OAEP
from Crypto.PublicKey import RSA

from django.conf import settings
from django.contrib.contenttypes.models import ContentType

from MHLogin.utils.admin_utils import mail_admins
from MHLogin.KMS import logger
from MHLogin.KMS.models import UserPrivateKey, OwnerPublicKey, EncryptedObject, \
	CRED_WEBAPP, RSA_PRIMARY, CRED_IVRPIN, RSA_IVR, export_rsa, import_rsa


def generate_keys_for_users(output=sys.stderr, users=None):
	"""
	Generates RSA keypairs for all users without them, default state is
	grandfathered until user with new key(s) logs in.  This function REQUIRES
	settings.DEBUG to be set to a non-false value.
	"""
# 	if not settings.DEBUG:
# 		raise Exception('This code is only allowed to be run with DEBUG set to true. '
# 			'Do NOT run this in a production environment!')
	from MHLogin.MHLUsers.models import MHLUser
	users = users or MHLUser.objects.all()
	count = users.count()
	output.write("User count: %d\n" % count)
	for user in users:
		if not OwnerPublicKey.objects.filter_pubkey(owner=user).exists():
			output.write("Generating key for user %s..." % (user))
			create_default_keys(user)
			output.write("Done!...%d remaining\n" % count)  # show we're alive
		else:
			output.write("OwnerPublicKey exists for user %s, skipping.\n" % user)
		count -= 1
	output.write("Done.\n")


def split_user_key(password):
	""" Helper to crypto split a password """
	remote = os.urandom(32)
	local = XOR.new(remote).encrypt(strengthen_key(password))
	return b64encode(remote), b64encode(local)


def store_user_key(request, response, password):
	""" Crypto split user password storing half in cookie other half in session """
	remote, local = split_user_key(password)
	# by this point cookie acceptance should be verified
	response.set_cookie('ss',
			value=remote,
			max_age=settings.SESSION_COOKIE_AGE,
			domain=settings.SESSION_COOKIE_DOMAIN,
			secure=settings.SESSION_COOKIE_SECURE,
			path=settings.SESSION_COOKIE_PATH)
	request.session['key'] = local


def get_user_key(request, ss=None):
	""" Crypto join local 'key' and remote cookie or 'ss' to form strengthened password """
	remote = b64decode(ss or request.COOKIES['ss'])
	local = b64decode(request.session['key'])
	return XOR.new(remote).decrypt(local)


def strengthen_key(key):
	"""
	Takes the user's password (user key) and returns a pseudorandom 32-character binary
	hash of the user's password. This allows us to gain better user password security
	through both storage of obfuscated user passwords and less guessable crypto keys.
	"""
	salt = settings.KMS_STRENGTHENKEY_SALT \
		if 'KMS_STRENGTHENKEY_SALT' in dir(settings) else 'Ieth1avu'
	rounds = settings.KMS_STRENGTHENKEY_ROUNDS \
		if 'KMS_STRENGTHENKEY_ROUNDS' in dir(settings) else 4
	# SHA1 hashes aren't long enough, nor are MD5 hashes. We need to concatenate
	# the two, then truncate in order to get our 32-character length.
	sha_lib = hashlib.sha1()
	md5_lib = hashlib.md5()
	for i in range(rounds):
		key = ''.join([key, salt])
		sha_lib.update(key)
		md5_lib.update(key)
		key = ''.join([sha_lib.digest(), md5_lib.digest()[:12]])
	return key


def generate_new_user_keys(user, password):
	""" 
	Legacy helper to generate new rsa keys for user, keeping existing.  This will
	no longer be needed when #2115 in, but may be kept for prosperity.  Note: This 
	function will deny a user access to his/her *old* messages until the Administrator 
	logs in and enters the Administrator key.

	:param user: Base class MHLUser type.
	:param password: The user's new password.
	"""
	mail_admins('Password Force Change Notice (%s)' % settings.SERVER_ADDRESS,
		'%s %s (%s) force changed their password. Please go and reset their old keys.' %
			(user.first_name, user.last_name, user.username,))
	ipubs = OwnerPublicKey.objects.filter_pubkey(owner=user)
	UserPrivateKey.objects.filter(opub__in=ipubs).delete()
	ipubs.update(active=False)
	create_default_keys(user, password)


def reset_user_invalid_keys(user, admin_rsa):
	""" Legacy, recrypts all encrypted objects with user's new pubkey(s) """
	otype, oid = ContentType.objects.get_for_model(user), user.id
	ipubs = OwnerPublicKey.inactive.filter(owner_type=otype, owner_id=oid, active=False)
	for ipub in ipubs:
		adminclearkey = PKCS1_OAEP.new(admin_rsa).decrypt(b64decode(ipub.admincipher))
		# import inactive key
		irsa = import_rsa(ipub.adminscopy, adminclearkey)
		# get matching active public key for user
		apub = OwnerPublicKey.objects.get(owner_type=otype, owner_id=oid,
							keytype=ipub.keytype, active=True)
		# import new active publickey
		apublickey = import_rsa(apub.publickey)
		# update encrypted objects encrypting via new active public key
		for encobj in EncryptedObject.objects.filter(opub=ipub):
			clearkey = PKCS1_OAEP.new(irsa).decrypt(b64decode(encobj.cipherkey))
			encobj.cipherkey = b64encode(PKCS1_OAEP.new(apublickey).encrypt(clearkey))
			encobj.opub = apub  # point encobj's opub to new pubkey
			encobj.save()
	apubs = OwnerPublicKey.objects.filter_pubkey(owner=user)
	# reset user's private keys outside their own pubkeys if any, eg. practice locations
	privs = UserPrivateKey.objects.filter(
			user=user, credtype=CRED_WEBAPP).exclude(opub__in=apubs)
	reset_keys(privs, admin_rsa)
	# and remove inactive public keys
	ipubs.delete()


def reset_keys(uprivs_qry, admin_rsa, creds=None):
	""" For rm #450, static reset user keys.  Obsoletes reset_user_invalid_keys()
		and generate_new_user_keys() when black box in office and rm #2115 done. """
	for priv in uprivs_qry:
		clearkey = PKCS1_OAEP.new(admin_rsa).decrypt(b64decode(priv.opub.admincipher))
		rsa = import_rsa(priv.opub.adminscopy, clearkey)
		priv.privatekey = export_rsa(rsa, strengthen_key(creds or settings.SECRET_KEY))
		priv.gfather = False if creds else True
		priv.save()


def recrypt_keys(uprivs_qry, old_creds, new_creds, strengthd=False):
	""" Recrypt keys when user changes password/pin or un-grandfathered.

	:param strengthd: Handle annoying corner case, IVR does not ask for old
		pin when user wants to change pin via IVR, we have only userkey, i.e.
		strengthen_key(pin). TODO: Redmine so behavior is same as web/app.
	:raises: ValueError if old_creds incorrect
	"""
	old_creds = old_creds if strengthd else strengthen_key(old_creds)
	new_creds = new_creds if strengthd else strengthen_key(new_creds)
	for priv in uprivs_qry:
		rsa = import_rsa(priv.privatekey, old_creds)
		priv.privatekey = export_rsa(rsa, new_creds)
		priv.gfather = False
		priv.save()


def generate_recovery(user, admin_rsa=None):
	""" Generate recovery key: must provide admin creds or all keys g'fathered """
	recovery_key, recovery = os.urandom(32), None
	if admin_rsa:
		# generate recovery regardless of g'fathered state when given admin_rsa
		for priv in UserPrivateKey.objects.filter(user=user):
			clearkey = PKCS1_OAEP.new(admin_rsa).decrypt(b64decode(priv.opub.admincipher))
			rsa = import_rsa(priv.opub.adminscopy, clearkey)
			priv.recovery = export_rsa(rsa, recovery_key)
			priv.save()
		recovery = b16encode(recovery_key)
	elif not UserPrivateKey.objects.filter(user=user, gfather=False).exists():
		# no admin (e.g. user signup) but all keys must be g'fathered
		initial_creds = strengthen_key(settings.SECRET_KEY)
		for priv in UserPrivateKey.objects.filter(user=user):
			rsa = import_rsa(priv.privatekey, initial_creds)
			priv.recovery = export_rsa(rsa, recovery_key)
			priv.save()
		recovery = b16encode(recovery_key)
	if not recovery:
		logger.critical("Recovery key not created for user: %s" % user)

	return recovery  # send to user, don't store anywhere


def create_default_keys(user, webcreds=None, ivrcreds=None):
	""" Helper to create standard user setup:
			1. Web/App RSA key encrypted w/web credentials (password)
			2. IVR RSA key encrypted w/ivr credentials (pin)
			3. Same IVR RSA key encrypted w/web credentials
	"""
	# 1. Web/App RSA key encrypted w/web credentials
	create_rsakeypair(user, RSA_PRIMARY, CRED_WEBAPP, webcreds)
	# 2. IVR RSA key encrypted w/IVR PIN credentials
	ipub, ipriv = create_rsakeypair(user, RSA_IVR, CRED_IVRPIN, ivrcreds)
	# 3. Same IVR key, this is so users can change a forgotten pin via web
	rsa = import_rsa(ipriv.privatekey, strengthen_key(ivrcreds or settings.SECRET_KEY))
	UserPrivateKey.objects.create(user=user, opub=ipub, credtype=CRED_WEBAPP,
		privatekey=export_rsa(rsa, strengthen_key(webcreds or settings.SECRET_KEY)),
			gfather=False if webcreds else True)


def create_rsakeypair(user, keytype=RSA_PRIMARY, credtype=CRED_WEBAPP, creds=None):
	""" Create rsa key pair - public and private, grandfathered if no credentials """
	assert(user.__class__.__name__ == 'MHLUser'), user.__class__.__name__
	from MHLogin._admin_reset import ADMIN_RESET_PUBLIC_RSA
	# create RSA public and private key instances
	rsa = RSA.generate(2048, os.urandom)
	# encrypt a copy of rsa key with admin reset pubkey
	adminclearkey = os.urandom(32)
	adminpub = import_rsa(ADMIN_RESET_PUBLIC_RSA)
	admincipher = b64encode(PKCS1_OAEP.new(adminpub).encrypt(adminclearkey))
	adminscopy = export_rsa(rsa, adminclearkey)
	# now create pub/priv pair, encrypting with creds (password, pin, etc.)
	opub = OwnerPublicKey.objects.create(owner_id=user.id,
		owner_type=ContentType.objects.get_for_model(user), adminscopy=adminscopy,
			admincipher=admincipher, publickey=export_rsa(rsa.publickey()), keytype=keytype)
	upriv = UserPrivateKey.objects.create(user=user, opub=opub, credtype=credtype,
		privatekey=export_rsa(rsa, strengthen_key(creds or settings.SECRET_KEY)),
			gfather=False if creds else True)
	return opub, upriv


def aes_encrypt(creds, cleartext):
	""" AES encrypt helper using CBC mode """
	iv = os.urandom(16)
	return iv + AES.new(creds, mode=AES.MODE_CBC, IV=iv).encrypt(padn(cleartext))


def aes_decrypt(creds, ciphertext):
	""" AES decrypt helper using CBC mode, assuming aes_encrypt() used for encryption """
	return unpad(AES.new(creds, mode=AES.MODE_CBC, IV=ciphertext[:16]).decrypt(ciphertext[16:]))

# helper to pad inclusively multiple of 16 (default), max 255
padn = lambda s, n=16: s + (n - len(s) % n) * chr(n - len(s) % n)
# helper to unpad assumes padn was used, pad value(s) are number of bytes padded
unpad = lambda s: s[0:-ord(s[-1])]
