
import os
import sys

from base64 import b64encode
from optparse import make_option

from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.utils.translation import ugettext

from MHLogin.KMS.utils import strengthen_key
from MHLogin.KMS.models import OwnerPublicKey, UserPrivateKey, RSA_PRIMARY, RSA_IVR, \
	CRED_WEBAPP, CRED_IVRPIN, export_rsa, import_rsa


class Command(BaseCommand):
	""" Django management command to create user OwnerKey pairs for existing
		users.  Support for PracticeLocation is deferred as they will be created
		by their owner on creation, or by an admin manually for existing practices. """
	BaseCommand.option_list += (
		make_option('--rsa-local', action='store_true', dest='rsalocal',
				default=False, help='Generate RSA keys locally.'),
		make_option('--force', action='store_true', dest='force',
				default=False, help='Forcibly re-create UserKeys.'),)

	def __init__(self):
		super(Command, self).__init__()
		self.help = ugettext("Help: Create user pairs for all users that don't have one.\n")
		self.args = None

	def handle(self, *args, **options):
		rsalocal = options.pop('rsalocal', False)
		force = options.pop('force', False)

		create_userkeys(local=rsalocal, force=force)


# NOTE: syncdb must be called before this method on a DB
def create_userkeys(local=False, force=False, output=sys.stderr):
	""" Helper to create new style KMS KeyPairs """
	from MHLogin.MHLUsers.models import MHLUser
	output.write("Generating RSA keys locally...\n") if local else \
		output.write("Fetching RSA keys remotely...\n")
	if force:  # clear out existing if exists
		ct = ContentType.objects.get_for_model(MHLUser)
		opubs = OwnerPublicKey.objects.filter(owner_type=ct)
		uprivs = UserPrivateKey.objects.filter(opub__owner_type=ct)
		opubs.delete()
		uprivs.delete()
		output.write("Forcibly recreating all user keys...\n")

	users = MHLUser.objects.all()
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
