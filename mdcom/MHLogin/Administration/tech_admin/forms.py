
"""
All admin forms can be used by either admin or tech-admin.  The major difference
between these forms and django admin forms is the ability to access the request object.
Django makes it difficult but possible by overriding the get_form method in the admin
interface before form creation.  Note the assertions in base class form constructors.
"""
import itertools
import datetime

from django import forms
from django.contrib.auth.forms import UserCreationForm, \
		UserChangeForm, AdminPasswordChangeForm
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _

from MHLogin.Administration.tech_admin.utils import is_techadmin, get_user_permissions
from MHLogin.Administration.tech_admin.management.commands.\
		create_admin_groups import TECH_ADMIN_GROUP


class TechAdminForm(forms.ModelForm):
	""" Base class tech admin form for non-user related forms """
	def __init__(self, *args, **kwargs):
		assert (self.request != None)  # set by admin get_form()
		super(TechAdminForm, self).__init__(*args, **kwargs)


class TechAdminUserForm(UserChangeForm):
	""" Base class tech admin user form, diverges from TechAdminForm different parent """
	def __init__(self, *args, **kwargs):
		assert (self.request != None)  # set by admin get_form()
		if is_techadmin(self.request.user):
			# Set available group/permissions based on tech-admins permissions
			self.base_fields['groups']._queryset = self.request.user.groups.all()
			self.base_fields['user_permissions']._queryset = get_user_permissions(self.request.user)
		super(TechAdminUserForm, self).__init__(*args, **kwargs)
		# after init save user's personal groups not part of tech-admins if any
		self.personal_grps = self.instance.groups.exclude(
							id__in=(g.id for g in self.request.user.groups.all()))
		self.personal_perms = self.instance.user_permissions.exclude(
							id__in=(p.id for p in get_user_permissions(self.request.user)))

		for locfield in ['lat', 'longit', 'office_lat', 'office_longit']:
			if locfield in self.fields:
				self.fields[locfield].widget.attrs['disabled'] = 'disabled'

	def clean_groups(self):
		if is_techadmin(self.request.user):
			if not self.cleaned_data['groups'] or (self.cleaned_data['groups'] and
				not self.cleaned_data['groups'].exclude(name=TECH_ADMIN_GROUP)):
				raise ValidationError(_("%s must belong to at least "
					"one non tech-admin group." % self.instance.username))
			# add back personal groups if user belongs to other groups
			# besides the ones this tech-admin is administering
			self.cleaned_data['groups'] = [g for g in itertools.chain(
							self.cleaned_data['groups'], self.personal_grps)]
		return self.cleaned_data['groups']

	def clean_user_permissions(self):
		if is_techadmin(self.request.user):
			# add back personal permissions if user belongs to ones not part of tech-admin
			self.cleaned_data['user_permissions'] = [p for p in itertools.chain(
							self.cleaned_data['user_permissions'], self.personal_perms)]
		return self.cleaned_data['user_permissions']

	def clean(self):
		""" ValidationError raised here will not be associated with a particular field. """
		if 'groups' in self.changed_data and self.request.user.id == self.instance.id:
			raise ValidationError(_("Changing your permissions is not supported."))
		if 'user_permissions' in self.changed_data and self.request.user.id == self.instance.id:
			raise ValidationError(_("Changing your permissions is not supported."))
		if 'is_superuser' in self.changed_data and self.request.user.id == self.instance.id:
			raise ValidationError(_("Changing your permissions is not supported."))
		if 'is_staff' in self.changed_data and self.request.user.id == self.instance.id:
			raise ValidationError(_("Changing your permissions is not supported."))
		if 'is_active' in self.changed_data and self.request.user.id == self.instance.id:
			raise ValidationError(_("Changing your permissions is not supported."))
		return super(TechAdminUserForm, self).clean()


class TechAdminUserCreationForm(UserCreationForm):
	""" For creation of users, inheritance model diverges again """
	def __init__(self, *args, **kwargs):
		assert (self.request != None)  # set by admin get_form()
		super(TechAdminUserCreationForm, self).__init__(*args, **kwargs)

	def save(self, commit=True):
		""" For tech-admins default new user's groups to non tech-admin's """
		user = super(TechAdminUserCreationForm, self).save(commit)
		if is_techadmin(self.request.user):
			# before assigning default groups need to save model
			user.save()
			user.groups = self.request.user.groups.exclude(name=TECH_ADMIN_GROUP)

		return user

	def clean(self):
		""" ValidationError raised here will not be associated with a particular field. """
		if is_techadmin(self.request.user):
			if not self.request.user.groups.exclude(name=TECH_ADMIN_GROUP):
				raise ValidationError(_("You must belong to at least one "
					"non tech-admin group to add users."))
			# TODO: TEMPORARY
#			raise ValidationError("Creation of users is temporarily "
#				"disabled for Tech Admins.")
		return super(TechAdminUserCreationForm, self).clean()


class TechAdminPasswordForm(AdminPasswordChangeForm):

	def save(self, commit=True):
		# TESTING_KMS_INTEGRATION
		from MHLogin.KMS.utils import generate_new_user_keys
		from MHLogin.MHLUsers.models import PasswordResetLog, MHLUser
		PasswordResetLog.objects.create(user=self.user,
			reset=True, requestor=self.request.user,
			reset_timestamp=datetime.datetime.now())
		user = self.user if self.user.__class__ == MHLUser else MHLUser.objects.get(id=self.user.id)
		# TODO: update when rm #2115 goes in
		generate_new_user_keys(user, self.cleaned_data["password1"])
		return super(TechAdminPasswordForm, self).save()


class PracticeLocationForm(TechAdminForm):
	""" Custom Practice Location change form to show members belonging to practice.
	Since we have manytomany and foreign key relationships for this to work we
	must include any MHLUser types that have relationships into PracticeLocation.
	Currently OfficeStaff and Providers have this relationship.
	"""
	# form only fields, make sure names don't collide with model field names
	members = forms.MultipleChoiceField(required=False)

	def __init__(self, *args, **kwargs):
		super(PracticeLocationForm, self).__init__(*args, **kwargs)

		if 'instance' in kwargs:
			users = kwargs['instance'].get_members()
			# Set the form fields based on the model object
			self.fields['members'].choices = [(u.id, u) for u in users]
		self.fields['members'].widget.attrs['disabled'] = 'disabled'

	def clean(self):
		""" ValidationError raised here will not be associated with a particular field. """
		# Allow tech admin to change practice if all users belong to the same group(s)
		# he does minus his tech-admin. And allow edits on empty practices but no deletes.
		if is_techadmin(self.request.user):
			outcasts = []
			grps = self.request.user.groups.exclude(name=TECH_ADMIN_GROUP)
			# now check every user belongs to at least one of the groups tech admin does
			for _, user in self.fields['members'].choices:
				if not user.groups.filter(id__in=(g.id for g in grps)):
					outcasts.append(user)

			if outcasts:
				raise ValidationError(_("Cannot modify practice, one or more practice "
					"members do not belong to your group: %s" %
						', '.join(str(o) for o in outcasts)))
		return super(PracticeLocationForm, self).clean()


class TechAdminGroupForm(TechAdminForm):
	""" Show auth.users belonging to groups.  If any other models have FK into
	groups add the query to the init function here.
	"""
	# form only fields, make sure names don't collide with model field names
	members = forms.MultipleChoiceField(required=False)

	def __init__(self, *args, **kwargs):
		if is_techadmin(self.request.user):
			# Set available group/permissions based on tech-admins permissions
			self.base_fields['permissions']._queryset = get_user_permissions(self.request.user)
		super(TechAdminGroupForm, self).__init__(*args, **kwargs)

		users = self.orig_perms = []
		if 'instance' in kwargs:
			# helper to show users belonging to this group if any
			users = kwargs['instance'].user_set.all()
			# save orig perms not in tech admin's perm list
			self.orig_perms = kwargs['instance'].permissions.exclude(id__in=(p.id
								for p in get_user_permissions(self.request.user)))
		# Set the form fields based on the model object
		self.fields['members'].choices = [(u.id, ' '.join([u.first_name, u.last_name]))
										for u in users]
		self.fields['members'].widget.attrs['disabled'] = 'disabled'

	def clean(self):
		""" ValidationError raised here if tech-admin doing something they ain't supposed to.... """
		if is_techadmin(self.request.user):
			if Group.objects.filter(id=self.instance.id).exists():
				raise ValidationError(_("Tech admin not allowed to modify groups."))
		return super(TechAdminGroupForm, self).clean()

	def clean_permissions(self):
		if is_techadmin(self.request.user):
			self.cleaned_data['permissions'] = [p for p in itertools.chain(
							self.cleaned_data['permissions'], self.orig_perms)]
		return self.cleaned_data['permissions']

	def save(self, commit=True):
		""" For tech-admins assign new group to this tech-admin """
		group = super(TechAdminGroupForm, self).save(commit)
		if is_techadmin(self.request.user):
			group.save()
			self.request.user.groups.add(group)

		return group

