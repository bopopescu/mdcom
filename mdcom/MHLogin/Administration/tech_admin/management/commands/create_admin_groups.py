
"""
 Helper command to create admin related groups.  Currently creates a tech admin
 group for use with the tech-amdin feature and a read-only admin group.  See
 comments in tech_admin/options.py for for details on how this is done.
 """
import sys

from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q


TECH_ADMIN_GROUP = 'Tech Admin'
READONLY_ADMIN_GROUP = 'Readonly Admin'


@transaction.commit_manually
class Command(BaseCommand):
	""" Command to create two groups: 'Tech Admin' and 'Readonly Admin'
	"""

	def handle(self, *args, **kwargs):
		# allow for explicity setting additional permissions
		create_admin_groups(**kwargs)


def create_admin_groups(**kwargs):
	""" Helper function to create two groups: 'Tech Admin' and 'Readonly Admin'
	"""
	verb = int(kwargs['verbosity']) if 'verbosity' in kwargs else 0

	if verb > 1:
		sys.stderr.write("Creating MHLogin user/group permission(s)\n")

	create_admin_group(READONLY_ADMIN_GROUP, Q(codename__startswith="change_"))
	create_admin_group(TECH_ADMIN_GROUP, build_tech_admin_permission_query())

	if (verb > 1):
		sys.stderr.write("\n%s DONE\n" % sys.argv[1])


# helper to create readonly admin
def create_admin_group(name, query=None):
	"""
	Since Django 1.3 has interesting behavior with 'change' and 'add' we can use that for
	our definition of read only.  Specifically if a user has 'change' permission on a model
	but no 'add' or 'delete' we define that as read only on that model for that user. For our
	application we don't have the case where a user has 'change' access but no 'add' or
	'delete' on a model.
	"""

	users = None
	try:
		agroup = Group.objects.get(name=name)
		# if exists gather all users associated with group before deleting
		users = User.objects.filter(Q(groups__name=agroup.name))
		[u.groups.remove(agroup) for u in users]
		agroup.delete()
		# if exists remove all existing possibly stale permissions and re-add
	except ObjectDoesNotExist:
		# does not exist create it
		pass
	agroup = Group(name=name)
	agroup.save()  # creates primary key needed by many-to-many

	if query != None:
		perms = Permission.objects.filter(query)
	else:  # grab everything
		perms = Permission.objects.all()
	for p in perms:
		agroup.permissions.add(p)

	if users:
		# if users were in previous group add them back
		[u.groups.add(agroup) for u in users]

	return agroup


# helper to build tech admin permissions
def build_tech_admin_permission_query():
	models = ['Group', 'PracticeLocation', 'PracticeHours',
			'PracticeHolidays', 'Organization', 'Organization_Member', 'Pending_Organization']
	user_models = ['Broker', 'Dietician', 'MHLUser', 'NP_PA', 'Nurse', 'Office_Manager',
			'OfficeStaff', 'Physician', 'Provider', 'Regional_Manager', 'Salesperson']

	# we may customize this as time goes on but currently tech admins are allowed
	# to modify users and practice locations based on the group(s) they belong to

	models.extend(user_models)

	content_types = ContentType.objects.filter(model__in=models)

	return Q(content_type__in=content_types)


#def add_view_permissions(sender, **kwargs):
#	""" This syncdb hooks takes care of adding a view
#	permission too all our content types.
#	"""
#	verb = int(kwargs['verbosity']) if kwargs.has_key('verbosity') else 0
#
#	if verb > 1:
#		sys.stderr.write("Adding view permissions\n")
#
#	# for each of our content types
#	for content_type in ContentType.objects.all():
#		# build our permission slug
#		codename = "view_%s" % content_type.model
#
#		# if it doesn't exist..
#		if not Permission.objects.filter(content_type=content_type, codename=codename):
#			# add it
#			Permission.objects.create(content_type=content_type,
#									codename=codename,
#									name="Can view %s" % content_type.name)
#
#			if verb > 1:
#				sys.stderr.write("Added view permission for %s\n" % content_type.name)

