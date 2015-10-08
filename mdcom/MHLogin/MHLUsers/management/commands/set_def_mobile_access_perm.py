
import sys
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
#from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand
from django.utils.translation import ugettext

from MHLogin.MHLUsers.models import MHLUser, logger


class Command(BaseCommand):
	"""
	Set default mobile access permissions on all users to True.  Syncdb must be run
	once before this command is run.  Once in the db this command can run without
	syncdb. 
	"""
	def __init__(self):
		super(Command, self).__init__()
		self.help = ugettext('Help: Set/Reset all user permissions, no arguments.\n')
		self.args = None

	def handle(self, *args, **options):
		set_def_mobile_access_perm(None)


# NOTE: syncdb must be called before this method on a DB without mobile permission. 
def set_def_mobile_access_perm(sender, **kwargs):
	""" Helper to set default mobile access permission to users to true.
	"""
	mobile_perm = Permission.objects.get_or_create(codename='access_smartphone',
		name='Can use smartphone app', 
			content_type=ContentType.objects.get_for_model(MHLUser))
	if mobile_perm[1] == True:
		msg = "Created %s. We should run syncdb so all permissions "\
				"are rebuilt...\n" % mobile_perm[0].codename
		sys.stderr.write(msg)
		logger.critical(msg)

	for u in User.objects.all():
		try:
			u.user_permissions.add(mobile_perm[0])
			u.save()
			# When checking using shortcut has_perm() pass in string like this:
			# u.has_perm('MHLUsers.access_smartphone'): or
			# u.has_perm('.'.join([mobile_perm[0].content_type.app_label, 
									#mobile_perm[0].codename])):
			# or access via get/filter (although above is recommended)
			#try:
			#	u.user_permissions.get(id=mobile_perm[0].id)
			#except ObjectDoesNotExist, odne:
			#	pass
		except Exception, e:
			logger.critical('Cannot add permission: access_smartphone, '
				'for user: %s, details: %s' % (u.username, str(e)))
	inactive_users = "The following users are inactive: %s\n" % ', '.join(
		i.username for i in MHLUser.objects.filter(is_active=False))
	logger.warn(inactive_users)
	sys.stderr.write("Done.\n")

