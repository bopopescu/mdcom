
#-*- coding: utf-8 -*-
from datetime import datetime
import random
import traceback

from django.contrib.contenttypes import generic
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.conf import settings
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Q
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _

from MHLogin.DoctorCom.IVR.models import VMBox_Config, VMMessage
from MHLogin.MHLSites.models import Site
from MHLogin.MHLPractices.models import PracticeLocation
from MHLogin.MHLUsers.validators import validate_phone
from MHLogin.utils.fields import UUIDField, MHLPhoneNumberField
from MHLogin.utils.constants import NATION_CHOICES, STATE_CHOICES, CARE_TYPE_CHOICES, \
	FORWARD_CHOICES, STAFF_TYPE_CHOICES, SPECIALTY_CHOICES, ROLE_TYPE, \
	STAFF_TYPE_CHOICES_EXTRA, YESNO_CHOICE, GENDER_CHOICES, SETTING_TIME_CHOICES, \
	CALLER_ANSSVC_CHOICES, TIME_ZONES_CHOICES, REFER_FORWARD_CHOICES, REFER_FORWARD_CHOICES_BOTH

from MHLogin.utils.mh_logging import get_standard_logger 

# Setting up logging
logger = get_standard_logger('%s/MHLUsers/models.log' % (settings.LOGGING_ROOT),
							'MHLUsers.models', settings.LOGGING_LEVEL)

VALIDATION_ERROR_MOBILE_EXISTS = _('A user with this mobile phone number already exists.')
VALIDATION_ERROR_EMAIL_EXISTS = _('A user with this email already exists.')
PHONE_NUMBER_HELP_TEXT = _("Please enter only digits. (e.g., 8005555555)")


class States(models.Model):
	nation = models.CharField(max_length=2, choices=NATION_CHOICES)
	state = models.CharField(max_length=2, choices=STATE_CHOICES)

	def __unicode__(self):
		return self.get_state_display()

	class Meta:
		unique_together = (('nation', 'state'),)
		verbose_name_plural = "States"


class ActiveManagedUser(models.Manager):
	def get_query_set(self):
		return super(ActiveManagedUser, self).get_query_set().filter(user__is_active=True)


class ActiveOfficeUser(models.Manager):
	def get_query_set(self):
		return super(ActiveOfficeUser, self).get_query_set().filter(user__user__is_active=True)


#add by xlin 120914
class SearchProviders(models.Manager):
	def get_query_set(self, first_name, last_name, email, hosp, prac):
		filt = getProviderFilterByOptions(first_name, last_name, email, hosp, prac)
		providers = Provider.active_objects.filter(filt).distinct()
		return providers


#add by xlin 120914
class SearchOfficeStaff(models.Manager):
	def get_query_set(self, first_name, last_name, email, hosp, prac):
		filt = getStafferFilterByOptions(first_name, last_name, email, hosp, prac)
		staffers = OfficeStaff.active_objects.filter(filt).distinct()
		return staffers

#horrible hack to make these not optional, since we can't modify django.contrib.auth.user
User._meta.get_field('first_name').blank = False
User._meta.get_field('last_name').blank = False
User._meta.get_field('email').blank = False


class MHLUser(User):
	uuid = UUIDField(auto=True, primary_key=False)
	gender = models.CharField(max_length=1, choices=GENDER_CHOICES, 
					verbose_name=_("Gender"), default='M')
	title=models.CharField(max_length=30,blank=True,null=True)
	mobile_phone = MHLPhoneNumberField(blank=True, verbose_name=_("Mobile Phone"), 
					validators=[validate_phone])
	phone = MHLPhoneNumberField(blank=True, verbose_name=_("Other Phone"), 
					help_text=PHONE_NUMBER_HELP_TEXT, validators=[validate_phone])

	address1 = models.CharField(max_length=200, blank=True, verbose_name=_("Address1"))
	address2 = models.CharField(max_length=200, blank=True, verbose_name=_("Address2"))
	city = models.CharField(max_length=200, blank=True, verbose_name=_("City"))
	state = models.CharField(max_length=2, choices=STATE_CHOICES, blank=True, verbose_name=_("State"))
	zip = models.CharField(max_length=10, blank=True, verbose_name=_("Zip"))  # 10 for zip and zip+4
	lat = models.FloatField(blank=True, null=True)
	longit = models.FloatField(blank=True, null=True)

	photo = models.ImageField(upload_to="images/userBioPics/%Y/%m/%d", blank=True, 
					verbose_name=_("Photo"), help_text=_("Recommended size 100*130"))

	email_confirmed = models.BooleanField(default=False)
	mobile_confirmed = models.BooleanField(default=False)
	tos_accepted = models.BooleanField(default=False, 
					help_text=_("Has the user accepted the terms of service?"))
	billing_account_accepted = models.BooleanField(default=False, 
					help_text=_("Has the user created a billing account?"))

	force_pass_change = models.BooleanField(default=False)
	password_change_time = models.DateTimeField(auto_now_add=True)

	#add by xlin 20120924 to add user skill
	skill = models.CharField(max_length=200, null=True, 
		blank=True, verbose_name=_("Special Skill"))
	public_notes = models.TextField(blank=True, 
		help_text="Special notes, contact preferences, etc..")
	#add by xlin 121017 for todo1045 that add setting time field False is 24h;True is 12h
	time_setting = models.IntegerField(choices=SETTING_TIME_CHOICES, 
		default=0, verbose_name=_('Time Setting'))

	refer_to_manager = models.BooleanField(default=True,
		verbose_name=_('CC refer to manager'))

	refer_forward = models.IntegerField(choices=REFER_FORWARD_CHOICES, 
		default=REFER_FORWARD_CHOICES_BOTH, verbose_name=_('Refer Forward Setting'))

	#time zone where practice is located, matches values in pytz
	time_zone = models.CharField(max_length=64, blank=True, null=True,
					choices=TIME_ZONES_CHOICES, verbose_name=_('Time Zone'))

	def __unicode__(self):
		return "%s %s" % (self.first_name, self.last_name)

	def clean(self):
		if (self.pk):
			# This user already exists
			if (self.mobile_phone and MHLUser.objects.filter(
						mobile_phone=self.mobile_phone).exclude(pk=self.pk).exists()):
				raise ValidationError(VALIDATION_ERROR_MOBILE_EXISTS)
		else:
			# This user doesn't exist yet. This would be for new accounts.
			if (self.mobile_phone and MHLUser.objects.filter(mobile_phone=self.mobile_phone).exists()):
				raise ValidationError(VALIDATION_ERROR_MOBILE_EXISTS)

		if (self.email):
			query_set = MHLUser.objects.filter(email=self.email)
			if (self.pk):
				query_set = query_set.exclude(pk=self.pk)
			if (query_set.exists()):
				raise ValidationError(VALIDATION_ERROR_EMAIL_EXISTS)

	def save(self, *args, **kwargs):
		# Check to ensure that no other user exists with the same mobile phone
		# number.

		if (self.mobile_phone and MHLUser.objects.filter(
						mobile_phone=self.mobile_phone).exclude(pk=self.pk).exists()):
			raise Exception(VALIDATION_ERROR_MOBILE_EXISTS)
		if (self.email):
			query_set = MHLUser.objects.filter(email=self.email)
			if (self.pk):
				query_set = query_set.exclude(pk=self.pk)
			if (query_set.exists()):
				raise ValidationError(VALIDATION_ERROR_EMAIL_EXISTS)
		super(MHLUser, self).save(*args, **kwargs)

	def set_password(self, newpass):
		super(MHLUser, self).set_password(newpass)
		self.password_change_time = datetime.now()

	def change_smartphone_perm(self, is_enable=True):
		perm, is_created = Permission.objects.get_or_create(codename='access_smartphone',
				name='Can use smartphone app', 
				content_type=ContentType.objects.get_for_model(MHLUser))
		if is_enable and not self.has_perm('MHLUsers.access_smartphone'):
			self.user_permissions.add(perm)
			self.save()

		if not is_enable and self.has_perm('MHLUsers.access_smartphone'):
			self.user_permissions.remove(perm)
			self.save()

	class Meta:
		ordering = ['last_name', 'first_name']
		permissions = (
			("access_smartphone", "Can use smartphone app"),
			("can_call_transfer", "Can transfer incoming calls"),
		)

MHLUSER_FIELDS = [f.name for f in MHLUser._meta.fields 
				if (f.model == MHLUser or f.model == User and f.name != "id")]


# DEPRECATION WARNING:
# We are gradually working on breaking this inheritance relation. Please do NOT
# write new code relying on it, if possible. Rather, use the provided /user/
# field to refer to the parent object.
#
# Additionally, if you run into code or templates that relies on this
# inheritance relation, please fix it. This will help us to spread out the work
# to break the relation over time.
#
# If you MUST write code that relies on this inheritance relation, please
# document your usage of the inheritance relation thoroughly so that it is clear
# where it's relied upon, and what needs to be done when this relation is
# actually broken. Additionally, please tag the location with the 'TODO_PROVINH'
# string in your comment (e.g., #TODO_PROVINH: comment here). Thanks!
class Provider(MHLUser):  # TODO_KCV new provider this will inherit from models.Model
	"""
		Provider objects which allow us to declare MHLUsers to be providers, and
		to allow us to collect additional data on these users.

		Changing model to not inherit from MHLUser and just use foreign key into MHLUser
		grep for TODO_PROVINH tags in code for places where we assume inheritance
	"""
	# Be aware that if you're creating a Provider, you need to manually populate
	# this field with the correct User object!
	user = models.ForeignKey(MHLUser, null=True, blank=True, related_name='user_provider')

	office_address1 = models.CharField(max_length=200, blank=True, verbose_name=_("Office address1"))
	office_address2 = models.CharField(max_length=200, blank=True, verbose_name=_("Office address2"))
	office_phone = MHLPhoneNumberField(verbose_name=_("Office Phone"), blank=True, 
					help_text=PHONE_NUMBER_HELP_TEXT, validators=[validate_phone])

	office_city = models.CharField(max_length=200, blank=True, verbose_name=_("Office city"))
	office_state = models.CharField(max_length=2, choices=STATE_CHOICES, blank=True, 
					verbose_name=_("Office state"))
	office_zip = models.CharField(max_length=10, blank=True, 
					verbose_name=_("Office zip"))  # 10 for zip and zip+4
	office_lat = models.FloatField(blank=True)
	office_longit = models.FloatField(blank=True)
	# Django IntegerField too small for US phone number with area code.
	pager = MHLPhoneNumberField(blank=True, verbose_name=_("Pager"), help_text=PHONE_NUMBER_HELP_TEXT)
	pager_extension = models.CharField(max_length=100, blank=True, verbose_name=_("Pager extension"))
	pager_confirmed = models.BooleanField(default=False)

	#DoctorCom Provisioned Phone Number and confirmation flag
	mdcom_phone = MHLPhoneNumberField(blank=True)
	mdcom_phone_sid = models.CharField(max_length=34, blank=True)

	forward_mobile = models.BooleanField(default=True)
	forward_office = models.BooleanField(default=False)
	forward_other = models.BooleanField(default=False)
	forward_vmail = models.BooleanField(default=False)

	forward_voicemail = models.CharField(max_length=2, choices=FORWARD_CHOICES, default='MO')
	forward_anssvc = models.CharField(max_length=2, choices=FORWARD_CHOICES, default='VM')
	# Voicemail
	vm_config = generic.GenericRelation(VMBox_Config,
					content_type_field='owner_type', object_id_field='owner_id')
	vm_msgs = generic.GenericRelation(VMMessage,
					content_type_field='owner_type', object_id_field='owner_id')

	sites = models.ManyToManyField(Site, null=True, blank=True, 
					related_name='site_provider')
	current_site = models.ForeignKey(Site, null=True, blank=True, 
					related_name='site_provider_current')

	practices = models.ManyToManyField(PracticeLocation, null=True, blank=True, 
					related_name='practice_provider')
	current_practice = models.ForeignKey(PracticeLocation, null=True, blank=True, 
					related_name='practice_provider_current')

	licensure_states = models.ManyToManyField(States, null=True, blank=True, 
					verbose_name=_("States of Licensure"))

	#Flag to set provider as a medical student
	clinical_clerk = models.BooleanField(default=False)

	status_verified = models.BooleanField(default=False)
	status_verifier = models.ForeignKey(MHLUser, null=True, blank=True, 
					related_name='verifier_provider')

	certification = models.TextField(null=True, blank=True,
					verbose_name=_("certification"))

	objects = models.Manager()
	active_objects = ActiveManagedUser()

	#add by xlin 120914
	search_objects = SearchProviders()

	def __unicode__(self):
		return "%s %s" % (self.first_name, self.last_name)

	def __getattribute__(self, name):
		if settings.DEBUG_PROVIDER == True and name in MHLUSER_FIELDS:
			# array of sets (file, line#, function, expr)
			tracebuf = traceback.extract_stack()
			buf = ""
			for t in tracebuf:
				buf = buf + "File: ..." + t[0][-30:] + " line: " + str(t[1]) + \
					" func: " + t[2] + " expr: " + t[3] + "\n"
			logger.warn("Provider will soon no longer inherit from MHLUser,"\
					"use foreign key 'user' to get to field '%s', stacktrace:"\
					"\n%s\n" % (name, buf)) 
		return super(Provider, self).__getattribute__(name)

	def clean(self):
		if (self.pk):
			# This user already exists
			if (self.mobile_phone and MHLUser.objects.filter(
					mobile_phone=self.mobile_phone).exclude(pk=self.pk).exists()):
				raise ValidationError(VALIDATION_ERROR_MOBILE_EXISTS)
		else:
			# This user doesn't exist yet. This would be for new accounts.
			if (self.mobile_phone and MHLUser.objects.filter(
					mobile_phone=self.mobile_phone).exists()):
				raise ValidationError(VALIDATION_ERROR_MOBILE_EXISTS)

		if (self.email):
			query_set = MHLUser.objects.filter(email=self.email)
			if (self.pk):
				query_set = query_set.exclude(pk=self.pk)
			if (query_set.exists()):
				raise ValidationError(VALIDATION_ERROR_EMAIL_EXISTS)

	def save(self, *args, **kwargs):
		# Check to ensure that no other user exists with the same mobile phone number.
		if (self.mobile_phone and MHLUser.objects.filter(
					mobile_phone=self.mobile_phone).exclude(pk=self.pk).exists()):
			raise Exception(VALIDATION_ERROR_MOBILE_EXISTS)

		if (self.email):
			query_set = MHLUser.objects.filter(email=self.email)
			if (self.pk):
				query_set = query_set.exclude(pk=self.pk)
			if (query_set.exists()):
				raise ValidationError(VALIDATION_ERROR_EMAIL_EXISTS)

		super(MHLUser, self).save(*args, **kwargs)

	class Meta:
		ordering = ['user']


# DEPRECATION WARNING:
# We are gradually working on breaking this inheritance relation. Please do NOT
# write new code relying on it, if possible. Rather, use the provided /user/
# field to refer to the parent object.
#
# Additionally, if you run into code or templates that relies on this
# inheritance relation, please fix it. This will help us to spread out the work
# to break the relation over time.
#
# If you MUST write code that relies on this inheritance relation, please
# document your usage of the inheritance relation thoroughly so that it is clear
# where it's relied upon, and what needs to be done when this relation is
# actually broken. Additionally, please tag the location with the 'TODO_PROVINH'
# string in your comment (e.g., #TODO_OFFSTFINH: comment here). Thanks!
#class OfficeStaff(models.Model):
class OfficeStaff(models.Model):
	# Be aware that if you're creating a OfficeStaff user, you need to manually
	# populate this field with the correct User object!
	user = models.ForeignKey(MHLUser, null=True, blank=True, related_name='user_officestaff')

	office_phone = MHLPhoneNumberField(blank=True, help_text=PHONE_NUMBER_HELP_TEXT)
	office_address1 = models.CharField(max_length=200, blank=True)
	office_address2 = models.CharField(max_length=200, blank=True)
	office_city = models.CharField(max_length=200, blank=True)
	office_state = models.CharField(max_length=2, choices=STATE_CHOICES, blank=True)
	office_zip = models.CharField(max_length=10, blank=True)  # 10 for zip and zip+4

	# Django IntegerField too small for US phone number with area code.
	pager = MHLPhoneNumberField(blank=True, verbose_name=_('pager'), help_text=PHONE_NUMBER_HELP_TEXT)
	pager_extension = models.CharField(max_length=100, blank=True, verbose_name=_('pager extension'))
	pager_confirmed = models.BooleanField(default=False)

	sites = models.ManyToManyField(Site, null=True, blank=True, 
					related_name='site_officestaff')
	current_site = models.ForeignKey(Site, null=True, blank=True, 
					related_name='site_officestaff_current')

	practices = models.ManyToManyField(PracticeLocation, null=True, blank=True, 
					related_name='practice_officestaff')
	current_practice = models.ForeignKey(PracticeLocation, null=True, blank=True, 
					related_name='practice_officestaff_current')
	vm_config = generic.GenericRelation(VMBox_Config,
					content_type_field='owner_type', object_id_field='owner_id')
	caller_anssvc = models.CharField(max_length=2, choices=CALLER_ANSSVC_CHOICES, default='')
	objects = models.Manager()
	active_objects = ActiveManagedUser()

	#add by xlin 120914
	search_objects = SearchOfficeStaff()

	class Meta:
		verbose_name = _("Office Staff")
		verbose_name_plural = _("Office Staff")
		ordering = ['user']

	def __unicode__(self):
		return "%s %s" % (self.user.first_name, self.user.last_name)


class Physician(models.Model):
	user = models.ForeignKey(Provider, unique=True)

	specialty = models.CharField(max_length=2, choices=SPECIALTY_CHOICES, 
					blank=True, verbose_name=_("Specialty"))
	accepting_new_patients = models.BooleanField(default=True, 
					blank=True, verbose_name=_("Accepting new patients"))
	staff_type = models.CharField(max_length=2, choices=STAFF_TYPE_CHOICES, 
					blank=True, verbose_name=_("Staff type"))

	objects = models.Manager()
	active_objects = ActiveOfficeUser()

	def __unicode__(self):
		return "%s %s" % (self.user.user.first_name, self.user.user.last_name)

	class Meta:
		ordering = ['user']


class NP_PA(models.Model):
	user = models.ForeignKey(Provider, unique=True)

	objects = models.Manager()
	active_objects = ActiveOfficeUser()

	def __unicode__(self):
		return "%s %s" % (self.user.user.first_name, self.user.user.last_name)

	class Meta:
		verbose_name = "NP/PA/Midwife"
		ordering = ['user']


class Nurse(models.Model):
	user = models.ForeignKey(OfficeStaff, unique=True)

	objects = models.Manager()
	active_objects = ActiveOfficeUser()

	def __unicode__(self):
		return "%s %s" % (self.user.user.first_name, self.user.user.last_name)

	class Meta:
		ordering = ['user']


class Office_Manager(models.Model):
	#user = models.ForeignKey(OfficeStaff, unique=True)
	user = models.ForeignKey(OfficeStaff)
	practice = models.ForeignKey(PracticeLocation, related_name='practice_office_manager')
	manager_role = models.IntegerField(choices=ROLE_TYPE, default=1)

	objects = models.Manager()
	active_objects = ActiveOfficeUser()

	def __unicode__(self):
		return "%s %s" % (self.user.user.first_name, self.user.user.last_name)

	class Meta:
		verbose_name = _("Office Manager")
		ordering = ['user']
		unique_together = (("user", "practice"),)


class Dietician(models.Model):
	user = models.ForeignKey(OfficeStaff, unique=True)

	objects = models.Manager()
	active_objects = ActiveOfficeUser()

	def __unicode__(self):
		return "%s %s" % (self.user.user.first_name, self.user.user.last_name)

	class Meta:
		ordering = ['user']


# Staff Roles
class Administrator(models.Model):
	user = models.ForeignKey(MHLUser, unique=True)

	objects = models.Manager()
	active_objects = ActiveManagedUser()

	def __unicode__(self):
		return "%s %s" % (self.user.first_name, self.user.last_name)

	class Meta:
		verbose_name = _("System Administrator")
		ordering = ['user__last_name']


class Salesperson(models.Model):
	user = models.ForeignKey(MHLUser, unique=True, related_name='user_salesperson')

	def __unicode__(self):
		return "%s %s" % (self.user.first_name, self.user.last_name)

	class Meta:
		db_table = 'Sales_salesperson'  # existing in production as this name
		verbose_name = "Salesperson"
		verbose_name_plural = "Salespeople"
		ordering = ['user__last_name']
		permissions = (
			("sales_executive", "Sales/Leads executive"),
)


class Patient(models.Model):
	user = models.ForeignKey(User, related_name='user_patient', unique=True)
	room_number = models.CharField(max_length=10, blank=True)
	care_type = models.CharField(max_length=1, choices=CARE_TYPE_CHOICES)

	def __unicode__(self):
		return "%s %s" % (self.user.first_name, self.user.last_name)


class Broker(models.Model):
	"""
		Broker objects which allow us to declare MHLUsers to be broker, and
		to allow us to collect additional data on these users.

		DEPRECATION WARNING:
		Please read the deprecation warning in the code before using this object.
	"""
	user = models.ForeignKey(MHLUser, null=True, blank=True, related_name='user_broker')

	office_address1 = models.CharField(max_length=200, blank=True)
	office_address2 = models.CharField(max_length=200, blank=True)
	office_phone = MHLPhoneNumberField(verbose_name=_("Office Phone"), blank=True, 
					help_text=PHONE_NUMBER_HELP_TEXT, validators=[validate_phone])
	office_city = models.CharField(max_length=200, blank=True)
	office_state = models.CharField(max_length=2, choices=STATE_CHOICES, blank=True)

	office_zip = models.CharField(max_length=10, blank=True)  # 10 for zip and zip+4
	office_lat = models.FloatField(blank=True)
	office_longit = models.FloatField(blank=True)

	# Django IntegerField too small for US phone number with area code.
	pager = MHLPhoneNumberField(blank=True, help_text=PHONE_NUMBER_HELP_TEXT)
	pager_extension = models.CharField(max_length=100, blank=True)
	pager_confirmed = models.BooleanField(default=False)

	# DoctorCom Provisioned Phone Number and confirmation flag
	mdcom_phone = MHLPhoneNumberField(blank=True)
	mdcom_phone_sid = models.CharField(max_length=34, blank=True)

	forward_mobile = models.BooleanField(default=True)
	forward_office = models.BooleanField(default=False)
	forward_other = models.BooleanField(default=False)
	forward_vmail = models.BooleanField(default=False)

	forward_voicemail = models.CharField(max_length=2, choices=FORWARD_CHOICES, default='MO')
	forward_anssvc = models.CharField(max_length=2, choices=FORWARD_CHOICES, default='VM')
	# Voicemail
	vm_config = generic.GenericRelation(VMBox_Config,
					content_type_field='owner_type', object_id_field='owner_id')
	vm_msgs = generic.GenericRelation(VMMessage,
					content_type_field='owner_type', object_id_field='owner_id')

	licensure_states = models.ManyToManyField(States, null=True, 
					blank=True, verbose_name=_("States of Licensure"))

	#Flag to set provider as a medical student
	clinical_clerk = models.BooleanField(default=False)

	status_verified = models.BooleanField(default=False)
	status_verifier = models.ForeignKey(MHLUser, null=True, blank=True, 
					related_name='verifier_broker')

	objects = models.Manager()
	active_objects = ActiveManagedUser()

	def __unicode__(self):
		return self.user.username

	def clean(self):
		pass

	class Meta:
		ordering = ['user']


class Regional_Manager(models.Model):
	"""
	This is a placeholder class for Regional Managers that will have special access
	to the system in particular analytics.  Analytics will need to differentiate 
	on admin/regional manager and regular users and allow access accordingly.  
	"""
	office_mgr = models.ForeignKey(Office_Manager)

	def __unicode__(self):
		return "%s %s" % (self.office_mgr.user.user.first_name, self.office_mgr.user.user.last_name)

	class Meta:
		verbose_name = _("Regional Manager")


#add by xlin 120917
def getProviderFilterByOptions(first_name, last_name, email, hosp, prac):
	# NOTE: using 'filt' instead of reserved word 'filter', pep8 warning 
	filt = Q()
	if first_name or last_name:
		if last_name == '':
			filt = Q(first_name__icontains=first_name) | \
				Q(last_name__icontains=first_name)
		else:
			filt = Q(first_name__icontains=first_name) & \
				Q(last_name__icontains=last_name) | \
				Q(first_name__icontains=last_name) & \
				Q(last_name__icontains=first_name)
	if email:
		filt = filt & Q(email__icontains=email)
	if prac:
		filt = filt & Q(practices__practice_name__icontains=prac)
	if hosp:
		filt = filt & Q(sites__name__icontains=hosp)
	return filt


#add by xlin 120917
def getStafferFilterByOptions(first_name, last_name, email, hosp, prac):
	# NOTE: using 'filt' instead of reserved word 'filter', pep8 warning 
	filt = Q()
	if first_name or last_name:
		if last_name == '':
			filt = Q(user__first_name__icontains=first_name) | \
				Q(user__last_name__icontains=first_name)
		else:
			filt = Q(user__first_name__icontains=first_name) & \
				Q(user__last_name__icontains=last_name) | \
				Q(user__first_name__icontains=last_name) & \
				Q(user__last_name__icontains=first_name)
	if email:
		filt = filt & Q(user__email__icontains=email)
	if prac:
		filt = filt & Q(practices__practice_name__icontains=prac)
	if hosp:
		filt = filt & Q(sites__name__icontains=hosp)
	return filt


#####################################################################################
###### The following classes are not MHLUser types but related to MHLUsers app ######
#####################################################################################


class PasswordResetLog(models.Model):
	user = models.ForeignKey(User, related_name='user_resetlog')
	# Keep track of whether or not the user reset their password using this code
	reset = models.BooleanField(default=False)
	# Keeps track of whether or not the administrator reset the user's old keys	
	resolved = models.BooleanField(default=False)

	requestor = models.ForeignKey(User, null=True, related_name='requestor_resetlog')
	requestor_ip = models.IPAddressField()
	request_timestamp = models.DateTimeField(auto_now_add=True)

	code = models.CharField(max_length=32)
	# The IP address of the machine from which this password was reset.
	reset_ip = models.IPAddressField(null=True, blank=True)
	reset_timestamp = models.DateTimeField(null=True, blank=True)

	servicer = models.ForeignKey(User, null=True, blank=True, related_name='servicer_resetlog')
	servicer_ip = models.IPAddressField(null=True, blank=True)
	resolution_timestamp = models.DateTimeField(null=True, blank=True)

	security_answers_count = models.CharField(max_length=32, default=0)

	def __init__(self, *args, **kwargs):
		super(PasswordResetLog, self).__init__(*args, **kwargs)

		if (not self.pk):
			# Set up the code
			self.code = self._gen_code()
			# Ensure that this code hasn't been generated for this user. Log
			# entries are expected to be unique between user and code for all
			# unused codes.
			while(PasswordResetLog.objects.filter(user=self.user, 
							code=self.code, reset=False).count()):
				self.code = self._gen_code()

	def _gen_code(self):
		chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ345789'
		return ''.join([random.choice(chars) for _ in range(16)])


class PhysicianGroup(models.Model):
	name = models.CharField(max_length=100, unique=True)

	def __unicode__(self):
		return self.name


class PhysicianGroupMembers(models.Model):
	physician = models.ForeignKey(Physician, related_name='physician_groupmem')
	physician_group = models.ForeignKey(PhysicianGroup)
	joined_date = models.DateTimeField(auto_now=True)

	def __unicode__(self):
		return "%s %s group: %s" % (self.physician.user.first_name, 
						self.physician.user.last_name, self.physician_group.name)

	class Meta:
		verbose_name_plural = "Doctor Group Members"


class EventLog(models.Model):
	user = models.ForeignKey(User, related_name='user_eventlog')
	event = models.CharField(max_length=2000)
	date = models.DateTimeField(auto_now=True)
	staff = models.CharField(max_length=1, choices=YESNO_CHOICE)
	staff_type = models.CharField(max_length=2, choices=STAFF_TYPE_CHOICES_EXTRA)
	sent_message = models.CharField(max_length=1, choices=YESNO_CHOICE)

	def __unicode__(self):
		return "Event Date: %s User: %s %s -- Event: %s" % (self.date, 
							self.user.first_name, self.user.last_name, self.event)


class SecurityQuestions(models.Model):
	#delete choice
	user = models.ForeignKey(User, unique=True)
	security_question1 = models.CharField(max_length=255, db_index=True)
	security_question2 = models.CharField(max_length=255, db_index=True)
	security_question3 = models.CharField(max_length=255, db_index=True)

	security_answer1 = models.CharField(max_length=255, db_index=True)
	security_answer2 = models.CharField(max_length=255, db_index=True)
	security_answer3 = models.CharField(max_length=255, db_index=True)

	def __unicode__(self):
		return '%s%s'(self.security_question1, self.security_answer1)

	class Meta:
		ordering = ['security_question1', 'security_question2', 'security_question3']
		verbose_name_plural = "Security Questions"


""" The following are signals used by MHLUsers app """


@receiver(post_save, sender=MHLUser)
@receiver(post_save, sender=Provider)
def post_save_set_def_user_perms(sender, **kwargs):
	""" After creation of user set default permissions """
	if ('created' and 'instance') in kwargs and kwargs['created'] == True:
		user = kwargs['instance']
		try:
			p = Permission.objects.get(codename='access_smartphone', 
				content_type=ContentType.objects.get_for_model(MHLUser))
			if not user.has_perm('MHLUsers.access_smartphone'):
				user.user_permissions.add(p)
		except ObjectDoesNotExist, odne:
			logger.critical("Problems setting default permission for user: %s, "
						"details: %s" % (user.username, str(odne)))

