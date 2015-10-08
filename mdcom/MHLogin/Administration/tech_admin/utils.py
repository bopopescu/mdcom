
"""
 Tech Admin utility functions
"""

from functools import wraps

from django.contrib.auth.models import Permission

from MHLogin.Administration.tech_admin.management.commands.\
		create_admin_groups import TECH_ADMIN_GROUP, READONLY_ADMIN_GROUP


def check_permission(perm):
	""" Check if current user has permission """
	def f(user, perm):
		return user.has_perm(perm)
	return f


def check_usertype(usertype):
	""" Check if usertype is in our register usertypes dictionary """
	def f(user, usertypes):
		return usertype in usertypes
	return f


# helper to check if user belongs to tech admin group
def is_techadmin(user):
	"""" Check if user is tech-admin.  By definition tech-admin is not superuser.
	If user has super-user access but for some reason is part of the tech-admin
	group superuser flag takes precedence.

	:returns: True if user has staff non-superuser access and member of tech-admin group
	"""
	rc = False
	if not user.is_superuser and user.groups.filter(name=TECH_ADMIN_GROUP):
		rc = True

	return rc


# helper to check if user belongs to read-only admin group
def is_readonly_admin(user):
	"""" Check if user is read-only admin, they should have staff access and
	belong to the READONLY_ADMIN_GROUP group.

	:returns: True if user has staff non-superuser access 
		and member of read-only admin group
	"""
	rc = False
	if not user.is_superuser and user.groups.filter(name=READONLY_ADMIN_GROUP):
		rc = True

	return rc


def get_user_permissions(user):
	""" :returns: QuerySet of all user permissions including groups """ 
	ids = list(user.user_permissions.all().values_list('id', flat=True))
	ids.extend(Permission.objects.filter(group__user=user).values_list('id', flat=True))
	return Permission.objects.filter(id__in=set(ids))


# monkey patch a method in a class
def monkeypatch_method(cls):
	""" Monkey patch a method in a class.  It will replace or add depending on name.
	Example:
		@monkeypatch_method(RelatedFieldWidgetWrapper)
		def render(self, name, value, *args, **kwargs):
			return "bingo"
	"""
	@wraps(cls)
	def decorator(func):
		setattr(cls, func.__name__, func)
		return func
	return decorator


# monkey patch a class with another class
def monkeypatch_class(name, bases, namespace):
	assert len(bases) == 1, "Exactly one base class required"
	base = bases[0]
	for name, value in namespace.iteritems():
		if name != "__metaclass__":
			setattr(base, name, value)
	return base

