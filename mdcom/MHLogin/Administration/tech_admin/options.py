
"""
Base class MHLogin admin models for admins and tech-admins.  Our admin model allows
more flexibility tailoring what the admin can do based on his/her permissions.  For
superusers the same functionality is available just as the regular Django Admin
provides.  Tech admins may only administer other members belonging to the same group(s)
they belong to.

In addition we support view-only admin access on a per user basis also using groups and
permissions.  DJango 1.3 Admin has model instanced support for viewing or read only features.
This is intended, however they have interesting behavior with add and change permissions.
If a user has 'add' permission but no 'change' permission for a particular model they
cannot add a row to a model.  Here is the error from Django's admin app:

"In order to add users, Django requires that your user account have both
the "Add user" and "Change user" permissions set.

And to view an Admin page we cannot simply modify an AdminModel and set fields to read
only based on user because to get to that point a user must have 'change' permission.
Adding a 'view' permission requires considerable work and hopefully future versions
of Django will listen to their user base and change their definition of permissions.

Since Django 1.3 has this interesting definition of 'change', 'add', and 'delete' we
can use that for our definition of read only.  Specifically if a user has 'change'
permission on a model but no 'add' or 'delete' we define that as read only on that model
for that user. For our application we don't have the case where a user has 'change'
access but no 'add' or 'delete' on a model.  Also note the case where an admin with no
change permission could delete and add back a row in a model - but to prevent that
they have the special check needing add *and* change to add a user.

Django if you're listening to your community we should have two (3) permissions:
	# Modify
	# View (read-only)
	# Implicitly a third, none of the two meaning no permission.
This makes the design cleaner and matches the English language as what the
these permissions do. Also takes care of the strange case mentioned above with
having 'add' but no 'change'.

Current limitation:  Tech-admins can only administer users who belong to the same
group(s) they belong to.  So if a regular user belongs to two or more groups the
tech-admin also needs to belong to those groups.  Currently a superuser would have
to grant the tech admin access to the other group so they could manage that user.
"""
from django.contrib import admin
from django.contrib.auth import admin as auth_admin
from django.forms.models import fields_for_model
from django.shortcuts import get_object_or_404

from MHLogin.Administration.tech_admin.utils import is_techadmin
from MHLogin.Administration.tech_admin.forms import \
		TechAdminUserForm, TechAdminUserCreationForm, TechAdminPasswordForm


class TechAdmin(admin.ModelAdmin):
	""" Base class for tech admin models """

	def get_readonly_fields(self, request, obj=None):
		return readonly_fields(TechAdmin, self, request, obj)

	def get_form(self, request, obj=None, **kwargs):
		""" Override, set request on form """
		form = super(TechAdmin, self).get_form(request, obj, **kwargs)
		form.request = request
		return form

	def queryset(self, request):
		"""
		:returns: QuerySet used by changelist_view.
		"""
		qs = super(TechAdmin, self).queryset(request)
		if is_techadmin(request.user):
			qs = self.techadmin_queryset(request, qs)
		return qs

	def techadmin_queryset(self, request, qs):
		""" filter down query set more if tech admin, override in child
			classes as needed.  Don't call base class if overridden."""
		return qs  # should be implemented in child classes but not mandatory

	def has_delete_permission(self, request, obj=None):
		""" Temporary, disable delete in view for tech-admin """
		# TEMPORARY
		return False if is_techadmin(request.user) else \
			super(TechAdmin, self).has_delete_permission(request, obj)


class TechMHLUserAdmin(auth_admin.UserAdmin):
	""" Inherit from UserAdmin because it has more builtin support for users. Another
		issue in Django UserAdmin base class they organize fieldsets into groups
		which is nice.  However when we want to exclude a field like 'is_superuser' it is
		not in fieldsets as key. Deep in the bowels of Django Admin code they search for
		key in list so 'is_superuser' is not there but 'Permissions' is.  Refer to base
		class to see implementation details.  In this case we get KeyError exception
		when we want to exclude 'is_superuser', keeping the list flat prevents this.
	"""
	add_form_template = 'tech_admin/add_form.html'
	filter_horizontal = ['groups', 'user_permissions']
	# override UserAdmin, set to None to get all fields in model as flat list
	fieldsets = None  # is built up when form is ready to render and is kept flat
	# Tech Admin forms can be used for regular admins as well
	form = TechAdminUserForm
	add_form = TechAdminUserCreationForm
	change_password_form = TechAdminPasswordForm

	def get_form(self, request, obj=None, **kwargs):
		""" Override, set request on form and for tech-admin exclude superuser, staff """
		form = super(TechMHLUserAdmin, self).get_form(request, obj, **kwargs)
		form.request = request
		if is_techadmin(request.user):
			form.base_fields.pop('is_superuser', None)
			form.base_fields.pop('is_staff', None)
		return form

	def get_readonly_fields(self, request, obj=None):
		""" Calls helper to get readonly fields may also call super """
		# when we move to practice groups or organization we will need to do this instead:
		# return fields + ('practice_group',) if is_techadmin(request.user) else fields
		return readonly_fields(TechMHLUserAdmin, self, request, obj)

	def has_delete_permission(self, request, obj=None):
		""" Temporary, disable delete in view for tech-admin """
		# TEMPORARY
		return False if is_techadmin(request.user) else \
			super(TechMHLUserAdmin, self).has_delete_permission(request, obj)

	def queryset(self, request):
		"""
		:returns: QuerySet used by changelist_view.
		"""
		qs = super(TechMHLUserAdmin, self).queryset(request)
		if is_techadmin(request.user):
			qs = self.techadmin_queryset(request, qs)
		return qs

	def techadmin_queryset(self, request, qs):
		""" filter down query set more if tech admin, override in child
			classes as needed.  Don't call base class if overridden."""
		raise NotImplementedError("Child classes must override.")

	def user_change_password(self, request, idx):
		""" Override, set request on form """
		self.change_password_form.request = request
		if request.user.id == get_object_or_404(self.model, pk=idx).id:
			# check if we are changing our password
			from MHLogin.MHLUsers.views import change_password
			from django.core.urlresolvers import resolve
			view = resolve(request.path).namespace + ':password_change_done'
			resp = change_password(request, redirect_view=view)
		else:
			resp = super(TechMHLUserAdmin, self).user_change_password(request, idx)
		return resp


def readonly_fields(klass, adm, request, obj):
	""" Helper to get readonly fields for TechMHLUserAdmin and TechAdmin.
	Here we apply our definition of readonly: when a user does not have add or
	delete on a model.  Again Django should have only two permissions: 'modify'
	and 'view', and implicitly a third which is none of the two signifying no
	permission.
	"""
	u = request.user
	perm_add = ''.join([adm.opts.app_label, '.', adm.opts.get_add_permission()])
	perm_del = ''.join([adm.opts.app_label, '.', adm.opts.get_delete_permission()])
	# Mess with the fields here we can't call get_field_sets() because it calls this
	# function too - I hope django changes the way they do permissions for admin.
	# There should be two: modify, view, and implicitly none for no permissions.
	if not u.is_superuser and not u.has_perm(perm_add) and not u.has_perm(perm_del):
		fields = fields_for_model(adm.model)  # grab all fields from the model
	else:
		fields = super(klass, adm).get_readonly_fields(request, obj)

	return fields

