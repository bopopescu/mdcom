
import sys

from Crypto.Util.number import long_to_bytes as l_2_b, bytes_to_long as b_2_l

from datetime import datetime
from math import ceil
from base64 import b64decode
from cPickle import loads
from optparse import make_option

from django import db
from django.contrib.sessions.models import Session
from django.core.management.base import BaseCommand

from MHLogin.apps.smartphone.models import SmartPhoneAssn
from MHLogin.KMS import logger
from MHLogin.KMS.models import OwnerPublicKey, AdminPrivateKey, RSA_IVR, RSA_PRIMARY, \
	EncryptedObject, PrivateKey, IVR_PrivateKey, import_rsa
from MHLogin.KMS.utils import strengthen_key


class Command(BaseCommand):
	BaseCommand.option_list += (
		make_option('--force', action='store_true', dest='force',
			default=False, help='Forcibly re-create EncryptedObjects.'),
		make_option('--logoff', action='store_true', dest='logoff',
			default=False, help='Clear active user sessions requiring users '
				'to re-authenticate.  Do when migration completely done.'),)

	def __init__(self):
		super(Command, self).__init__()
		self.help = 'Help: Migrate private and admin key tables to EncryptedObject.\n'
		self.args = 'password'

	def handle(self, *args, **options):
		if (len(args) != 1):
			sys.stderr.write("Admin password required.\n")
			self.print_help(sys.argv[1], "")
		else:
			from MHLogin._admin_reset import ADMIN_RESET_ENCD_RSA

			try:
				force = options.pop('force', False)
				logoff = options.pop('logoff', False)

				admin_rsa = import_rsa(ADMIN_RESET_ENCD_RSA, strengthen_key(args[0]))
				migrate_admin_objectkeys(admin_rsa, force)
				# Remove active sessions, users need to log in. During initial migration
				# rsa keys are grandfathered since we do not know users's password.
				# And we don't want specialized code in KMS checking for this single
				# use-case where keys are grandfathered while user logged in.
				if logoff:
					Session.objects.filter(expire_date__gte=datetime.now()).delete()
					SmartPhoneAssn.objects.filter(is_active=True).update(is_active=False)
			except ValueError:
				sys.stderr.write("Invalid password.\n")


def migrate_admin_objectkeys(admin_rsa, force, output=sys.stderr):
	"""
	NOTE: python manage.py create_userkeys must be run before this.  migrate old 
	style AdminPrivate encrypted objects to new EncryptedObjects.  Some old databases 
	had invalid random key lengths of 256 and should be 32, warn when we skip over. 
	"""
	if force:
		EncryptedObject.objects.all().delete()
		output.write("Forcibly recreating all EncryptedObjects...\n")

	db.reset_queries()
	admin_keys = {}
	privs = PrivateKey.objects.all().values_list('object_type', 'object_id', 'owner')
	count, diglen = len(privs), len(str(len(privs)))
	update_tick = int(ceil(count * 0.10))  # tick every 10% done
	output.write("\nPrivate key count: %d\n" % count)

	encs = EncryptedObject.objects.filter(opub__keytype=RSA_PRIMARY).\
		values_list('object_type', 'object_id', 'opub__owner_id')
	for tup in filter(lambda priv: priv not in encs, privs):
		pkey = PrivateKey.objects.get(object_type=tup[0], object_id=tup[1], owner=tup[2])
		if pkey.object != None:  # if None obj apparently deleted...not much we can do
			# create new EncryptedObject
			opub = OwnerPublicKey.objects.get_pubkey(owner=pkey.owner)
			clearkey = get_clear_key(admin_rsa, tup, admin_keys, output)
			if clearkey:
				EncryptedObject.objects.create_object(pkey.object, opub, clearkey)
		# show we're alive
		(count % update_tick == 0) and output.write("\r%0*d." % (diglen, count))
		count -= 1

	privs = IVR_PrivateKey.objects.all().values_list('object_type', 'object_id', 'owner')
	count, diglen = len(privs), len(str(len(privs)))
	update_tick = int(ceil(count * 0.10))  # tick every 10% done
	output.write("\nIVR Private key count: %d\n" % count)

	encs = EncryptedObject.objects.filter(opub__keytype=RSA_IVR).\
		values_list('object_type', 'object_id', 'opub__owner_id')
	for tup in filter(lambda priv: priv not in encs, privs):
		pkey = IVR_PrivateKey.objects.get(object_type=tup[0], object_id=tup[1], owner=tup[2])
		if pkey.object != None:  # if None obj apparently deleted...not much we can do
			# create new EncryptedObject
			opub = OwnerPublicKey.objects.get_pubkey(owner=pkey.owner, keytype=RSA_IVR)
			clearkey = get_clear_key(admin_rsa, tup, admin_keys, output)
			if clearkey:
				EncryptedObject.objects.create_object(pkey.object, opub, clearkey)
		# show we're alive
		(count % update_tick == 0) and output.write("\r%0*d." % (diglen, count))
		count -= 1

	output.write("\nQuery count: " + str(len(db.connection.queries))) 
	output.write("\nDone migrating keys.\n")


def get_clear_key(admin_rsa, tup, admin_keys, output):
	if (tup[0], tup[1]) in admin_keys:
		clearkey = admin_keys[(tup[0], tup[1])]
	else:
		akey = AdminPrivateKey.objects.filter(object_type=tup[0], object_id=tup[1])[0]

		clearkey = None
		try:  # decrypt the legacy key, was pickled and not rsa padded so no PKCS1_OAEP
			cipherkey = loads(b64decode(akey.key))[0]
			clearkey = l_2_b(admin_rsa.decrypt(b_2_l(cipherkey)), 32)
		except ValueError as ve:
			clearkey = ''
			logger.critical("Invalid message size: %s for admin key: %s" % (str(ve), akey))
			output.write("\r????")  # show we're alive
		keylen = len(clearkey)
		if keylen != 32:
			clearkey = None
			logger.critical("Invalid length: %d for admin key: %s" % (keylen, akey))
			output.write("\r!!!!")  # show we're alive
		else:
			admin_keys[(tup[0], tup[1])] = clearkey

	return clearkey


def test_decrypt(akey, clearkey):
	"""
	Unfortunately our models who do encr/decr decrypt things differently enough:
	order, args, dependencies, etc. this method is here... only testing MessageBody
	for now.
	"""
	import cPickle
	from Crypto.Cipher import AES
	from MHLogin.DoctorCom.Messaging.models import MessageBody

	clearkey = bytearray(clearkey)  # convert to byte array to play with it
	if isinstance(akey.object, MessageBody):
		#passphrase[0] = '\xaa'
		a = AES.new(str(clearkey))
		body = b64decode(akey.object.body)
		try:
			body = cPickle.loads(body)
		except Exception:
			logger.critical("Unable to depickle: %s" % (akey.object))
		cleartext = a.decrypt(body).rstrip()  # strip trailing spaces
		if not isprintable(cleartext):
			logger.critical("Possible MessageBody decryption failure for: %s" % (akey))
	else:
		logger.critical("TODO: Not running test_decrypt for: %s" % (akey))


def isprintable(s, codec='utf8'):
	""" One of several ways to determine if string is printable, good enough to test """
	is_printable = True
	try:
		s.decode(codec)
	except UnicodeDecodeError:
		is_printable = False
	return is_printable
