
import os
import sys
import Crypto.Cipher.AES as AES

from os.path import join, normpath

from base64 import b64decode
from cPickle import loads, UnpicklingError

from django.conf import settings
from django.core.management.base import BaseCommand

from MHLogin.KMS.utils import strengthen_key
from MHLogin.KMS.models import export_rsa, import_rsa

ADMIN_RESET_PY = \
'''
# for qa/devl default password to decrypt is 'demo'

ADMIN_RESET_PUBLIC_RSA = \\\n"""%(admin_public_rsa)s"""

ADMIN_RESET_ENCD_RSA = \\\n"""%(admin_rsa)s"""

'''


class Command(BaseCommand):
	def __init__(self):
		super(Command, self).__init__()
		self.help = '''
			Create/Upgrade primary reset key storing in:
			%s/_admin_reset.py.
			Also create keys for admins to access via their web credentials.
			''' % normpath(settings.INSTALLATION_PATH)
		self.args = 'password'

	def handle(self, *args, **options):
		if (len(args) != 1):
			sys.stderr.write("Admin password required.\n")
			self.print_help(sys.argv[1], "")
		else:
			upgrade_admin_reset_key(args[0])


def upgrade_admin_reset_key(creds):
	""" Upgrade admin reset rsa keypair storing in _admin_reset.py. Upgraded
	public rsa keypart is stored in standard PEM format, encrypted private
	rsa keypart stored AES encrypted using CBC mode in base64 with no pickle.
	"""
	aes = AES.new(strengthen_key(creds))
	admin_kp = aes.decrypt(b64decode(settings.CRYPTO_ADMIN_KEYPAIR))
	try:
		admin_rsa = loads(admin_kp)
		admin_rsa._randfunc = os.urandom  # pickled diffs pycrypto 2.3<-->2.6
		# public key exported PEM format
		pub = export_rsa(admin_rsa.publickey())
		priv = export_rsa(admin_rsa, strengthen_key(creds))
		# put file in parent MHLogin directory
		fname = join(settings.INSTALLATION_PATH, '_admin_reset.py')
		f = open(fname, 'wb')
		f.write(ADMIN_RESET_PY % {'admin_public_rsa': pub, 'admin_rsa': priv, })
		f.close()
		# sanity check upgrade:
		from MHLogin._admin_reset import ADMIN_RESET_PUBLIC_RSA, ADMIN_RESET_ENCD_RSA
		upgrade_rsa_pub = import_rsa(ADMIN_RESET_PUBLIC_RSA)
		assert upgrade_rsa_pub.publickey() == admin_rsa.publickey(), "public key mismatch"
		upgrade_rsa = import_rsa(ADMIN_RESET_ENCD_RSA, strengthen_key(creds))
		assert upgrade_rsa == admin_rsa, "rsa key mismatch"
		sys.stderr.write("Admin RSA reset keys upgraded in: %s\n" % fname)
	except UnpicklingError:
		sys.stderr.write("Invalid password.\n")
