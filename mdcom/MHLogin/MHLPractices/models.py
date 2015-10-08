
import time
from datetime import datetime
from django.db import models
from pytz import timezone, country_timezones
from django.utils.translation import ugettext_lazy as _

from MHLogin import settings
from MHLogin.DoctorCom.IVR.models import check_pin
from MHLogin.MHLSites.models import STATE_CHOICES
from MHLogin.utils.fields import UUIDField, MHLPhoneNumberField
from MHLogin.utils.validators import validate_unixDate
from MHLogin.utils.constants import ORG_POSITION_TYPE, ORG_SIZE_TYPE, USER_TYPE_DOCTOR, \
	USER_TYPE_NPPA, USER_TYPE_MEDICAL_STUDENT, USER_TYPE_OFFICE_STAFF, \
	USER_TYPE_OFFICE_MANAGER, USER_TYPE_NURSE, USER_TYPE_TECH_ADMIN, \
	USER_TYPE_DIETICIAN, RESERVED_ORGANIZATION_TYPE_ID_PRACTICE,\
	RESERVED_ORGANIZATION_ID_SYSTEM
from MHLogin.utils.constants import TIME_ZONES_CHOICES as tzchoices_fromcontants


country_type = 'us'
if 'de' in settings.FORCED_LANGUAGE_CODE:
	TIME_ZONES_CHOICES = (('Europe/Berlin', 'Europe/Berlin'),)
else:
	TIME_ZONES_CHOICES = tuple((tz, tz) for tz in country_timezones['us'])
# tz is used by line 141, --- [function is_open]timestamp = timestamp.astimezone(tz),
# so, I can't remove above codes.
# TODO, review this code

TIME_ZONES_CHOICES = tzchoices_fromcontants

#(
#('US/Alaska','US/Alaska'),
#('US/Aleutian','US/Aleutian'),
#('US/Arizona','US/Arizona'),
#('US/Central','US/Central'),
#('UUS/East-Indiana','US/East-Indiana'),
#('US/Eastern','US/Eastern'),
#('US/Hawaii','US/Hawaii'),
#('US/Indiana-Starke','US/Indiana-Starke'),
#('US/Michigan','US/Michigan'),
#('US/Mountain','US/Mountain'),
#('US/Pacific','US/Pacific'),
#('US/Samoa','US/Samoa'),
#)
HOURS_HELP_TEXT = _("in HH:MM 24 hour format")


class OfficeOpenStatus:
	Closed = 0
	Open = 1
	Lunch = 2


class ActiveOrganizationType(models.Manager):
	def get_query_set(self):
		return super(ActiveOrganizationType, self).get_query_set().filter(delete_flag=False)


class OrganizationType(models.Model):
	uuid = UUIDField(auto=True, primary_key=False)
	name = models.CharField(max_length=100, blank=False, unique=True, verbose_name=_('Name'),
				help_text=_('Organization Name'))
	is_public = models.BooleanField(default=False, verbose_name=_('Public'),
		help_text=_('If checked, office manager can create this type of organization. '
			'If unchecked only system admin can create this type of organization'))
	description = models.CharField(max_length=200, blank=True)

	subs = models.ManyToManyField('MHLPractices.OrganizationType', \
		through='MHLPractices.OrganizationTypeSubs', 
		related_name='sub_org_types', null=True, blank=True)
	organization_setting = models.ForeignKey('MHLPractices.OrganizationSetting')
	delete_flag = models.BooleanField(default=False)

	def save_sub_types(self, sub_types=None, *args, **kwargs):
		OrganizationTypeSubs.objects.filter(from_organizationtype=self).delete()
		if sub_types:
			if not isinstance(sub_types, list):
				sub_types = [sub_types]
			for sub_type in sub_types:
				if not OrganizationTypeSubs.objects.filter(from_organizationtype=self,\
								to_organizationtype=sub_type).exists():
					OrganizationTypeSubs.objects.create(from_organizationtype=self,\
								to_organizationtype=sub_type)
	__unicode__ = lambda self: "%s" % (self.name)

	objects = ActiveOrganizationType()
	full_objects = models.Manager()


class OrganizationSetting(models.Model):	
	can_have_answering_service = models.BooleanField(default=False,
			verbose_name=_('Can have answering service'),
			help_text=_('Allows organization to have answering service.'))
	can_be_billed = models.BooleanField(default=False,
			verbose_name=_('Can be billed'),
			help_text=_('Can organization be billed.'))
	display_in_contact_list_tab = models.BooleanField(default=False,
			verbose_name=_('Display in contact list tab'),
			help_text=_('If user is in this organization, we will display it in contact list tab.'))
	can_have_luxury_logo = models.BooleanField(default=False,
			verbose_name=_('Can have luxury logo'),
			help_text=_('Allows organization to have custom logo.'))
	can_have_member_organization = models.BooleanField(default=False,
			verbose_name=_('Can have member organization'),
			help_text=_('Allows organization to have member organization.'))

	can_have_physician = models.BooleanField(default=False,
			help_text=_('Allows organization to have physician.'))
	can_have_nppa = models.BooleanField(default=False,
			help_text=_('Allows organization to have nppa.'))
	can_have_medical_student = models.BooleanField(default=False,
			help_text=_('Allows organization to have medical student.'))

	can_have_staff = models.BooleanField(default=False,
			help_text=_('Allows organization to have staff.'))
	can_have_manager = models.BooleanField(default=False,
			help_text=_('Allows organization to have staff manager.'))
	can_have_nurse = models.BooleanField(default=False,
			help_text=_('Allows organization to have nurse.'))
	can_have_dietician = models.BooleanField(default=False,
			help_text=_('Allows organization to have dietician.'))
	can_have_tech_admin = models.BooleanField(default=False,
			help_text=_('Allows organization to have tech admin.'))

	delete_flag = models.BooleanField(default=False,
			help_text=_('Make the organization setting disabled.'))


class ActiveOrganization(models.Manager):
	def get_query_set(self):
		return super(ActiveOrganization, self).get_query_set().filter(delete_flag=False)


class ActivePractice(models.Manager):
	def get_query_set(self):
		return super(ActivePractice, self).get_query_set().filter(delete_flag=False, \
			organization_type__id=RESERVED_ORGANIZATION_TYPE_ID_PRACTICE)


class PracticeLocation(models.Model):
	"""
	Practice location object. Represents physical location of practice storing 
	address, doctor.com number, and members.  Members consist of professionals, 
	office staff, and office managers, of which office managers have change rights.
	"""
	practice_name = models.CharField(max_length=100, unique=True,\
		verbose_name=_('Name'))
	practice_address1 = models.CharField(max_length=200, blank=True,
						verbose_name=_("Address1"))
	practice_address2 = models.CharField(max_length=200, blank=True,
						verbose_name=_("Address2"))
	practice_phone = MHLPhoneNumberField(blank=True, verbose_name=_("Office Phone"))
	backline_phone = MHLPhoneNumberField(blank=True, verbose_name=_("Backline Phone"))
	practice_city = models.CharField(max_length=200, blank=True, verbose_name=_("City"))
	practice_state = models.CharField(max_length=2, choices=STATE_CHOICES, blank=True,
						verbose_name=_("State"))
	practice_zip = models.CharField(max_length=10, blank=True, verbose_name=_("Zip"))
	practice_lat = models.FloatField(blank=True)
	practice_longit = models.FloatField(blank=True)
	practice_photo = models.ImageField(upload_to="images/practicepics/%Y/%m/%d",
						blank=True, verbose_name=_("Logo"),
						help_text=_("Recommended size 100*30"))

	#DoctorCom Provisioned Phone Number and confirmation flag
	mdcom_phone = MHLPhoneNumberField(blank=True)
	mdcom_phone_sid = models.CharField(max_length=34, blank=True)

	#time zone where practice is located, matches values in pytz
	time_zone = models.CharField(max_length=64, blank=False,
						choices=TIME_ZONES_CHOICES, verbose_name=_('time zone'))

	#what call group is associated with this practice
	call_group = models.ForeignKey('MHLCallGroups.CallGroup', null=True, blank=True)
	#as we develop more functionality we will put products subscribed, billing, tos etc here

	#columns needed by answering service
	pin = models.CharField(max_length=120, blank=True)
	name_greeting = models.TextField(blank=True)
	greeting_closed = models.TextField(blank=True)
	greeting_lunch = models.TextField(blank=True)
	skip_to_rmsg = models.BooleanField(default=False,
				help_text=_('skip to taking a nonurgent message instead of '
						'asking during open hours'))
	config_complete = models.BooleanField(default=False)

	call_groups = models.ManyToManyField('MHLCallGroups.CallGroup', 
		null=True, blank=True, related_name="PracticeCallGroups", 
		verbose_name=("List of all of the call groups for this practice"))
	gen_msg = models.BooleanField(default=True, 
		help_text=('read out option for leaving nonurgent message for generic mailbox of practice'))

	# refactor organization added fields
	logo_position = models.IntegerField(choices=ORG_POSITION_TYPE, verbose_name=_("Logo Position"), default=0)
	logo_size = models.IntegerField(choices=ORG_SIZE_TYPE, verbose_name=_("Logo Size"), default=0)
	description = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Description"))
	create_date = models.DateTimeField(auto_now=True)
	status = models.IntegerField(default=1)
	short_name = models.CharField(max_length=30, blank=True)
	organization_type = models.ForeignKey(OrganizationType, null=True, blank=True)
	organization_setting = models.ForeignKey('MHLPractices.OrganizationSetting', 
			null=True, blank=True)

	member_orgs = models.ManyToManyField('MHLPractices.PracticeLocation', 
		through='MHLPractices.OrganizationMemberOrgs', 
		related_name='member org', null=True, blank=True)
	member_org_pending = models.ManyToManyField('MHLPractices.PracticeLocation', 
		through='MHLPractices.Pending_Org_Association',\
		related_name='member org pending', null=True, blank=True)

	delete_flag = models.BooleanField(default=False)

	objects = ActiveOrganization()
	full_objects = models.Manager()
	active_practice = ActivePractice()

	def __unicode__(self):
		return self.practice_name

	def uses_original_answering_serice(self):
		""" Will return True in case this practice was set up using one call group per location
		    version 2 requires NULL in practice.location call group and at least one entry in call_groups
			False in other case
		"""
		return self.call_group is not None

	__unicode__ = lambda self: self.practice_name

	def is_open(self, timestamp=None):
		"""
		:param timestamp: A timestamp (integer UNIX timestamp or a datetime object) 
			indicating the date and time you want to check. Alternatively, set it to 
			None to use the current time. Note that datetime objects *MUST* be timezone
			aware, or an exception will be raised.
		:returns: True if the practice is open, and False if the practice is closed, 
			given the passed time.
		"""
		# Munge the timestamp argument so that we always have a datetime object
		# representative of that time, in the practice's time zone.
		if (not timestamp):
			timestamp = datetime.now(timezone(self.time_zone))
		elif (timestamp.__class__.__name__ == 'datetime'):
			# If the timestamp is a datetime object
			if (timestamp.tzinfo == None):
				raise Exception(_('PracticeLocation.is_open() requires a '
					'timezone aware datetime object.'))
			timestamp = timestamp.astimezone(tz)
		else:
			# The timestamp is a UNIX timestamp.
			timestamp = datetime.fromtimestamp(timestamp, self.time_zone)

		if (PracticeHolidays.objects.filter(practice_location=self.id,
								designated_day=timestamp).exists()):
			return False

		# Shortcut to make access of the weekday easier.
		weekday = timestamp.isoweekday()

		today_hours = PracticeHours.objects.filter(
							practice_location=self.id, day_of_week=weekday)
		if (len(today_hours) == 0):
			# Days with no hours objects defined are considered closed.
			return False

		# Don't sweat len(today_hours) > 1 because the database schema forbids it.
		today_hours = today_hours[0] 

		# Heavy lifting! :)
		if (timestamp.time() > today_hours.open and timestamp.time() < today_hours.close):
			return True
		else:
			return False

	def set_pin(self, raw_pin):
		"""
		Based on Django 1.1.1's password hash generator.
		"""
		import random
		from MHLogin.DoctorCom.IVR.models import get_hexdigest
		algo = 'sha1'
		salt = get_hexdigest(algo, str(random.random()), str(random.random()))[:5]
		hashe = get_hexdigest(algo, salt, raw_pin)
		self.pin = '%s$%s$%s' % (algo, salt, hashe)

	def verify_pin(self, raw_pin):
		"""
		Based on Django 1.1.1's password hash generator.

		:returns: a boolean of whether the raw_password was correct. Handles
			encryption formats behind the scenes.
        """
		return check_pin(raw_pin, self.pin)

	def get_members(self):
		""" Return a queryset list of all MHLUsers belonging this practice """
		from MHLogin.MHLUsers.models import MHLUser
		users = list(self.practice_provider.all().
						values_list('user', flat=True))
		users.extend(list(self.practice_provider_current.all().
						values_list('user', flat=True)))
		users.extend(list(self.practice_officestaff.all().
						values_list('user', flat=True)))
		users.extend(list(self.practice_officestaff_current.all().
						values_list('user', flat=True)))
		users.extend(list(self.practice_office_manager.all().
						values_list('user__user', flat=True)))
		# unique'ify and return MHLUser list
		return MHLUser.objects.filter(id__in=set(users))

	def sanitize(self):
		"Sanitizes any personally identifying data from this object." 
		"NOTE THAT THIS DOES NOT SAVE THE OBJECT!"
		if (not settings.DEBUG):
			raise Exception(_('You must be in DEBUG mode to use this function.'))
		self.set_pin('1234')
		self.greeting = 'http://api.twilio.com/2008-08-01/Accounts/'\
			'AC087cabfd0a453a05acceb2810c100f69/Recordings/REf8afc497f43d8e1e9bc229a415ebe100'
		self.name = 'http://api.twilio.com/2008-08-01/Accounts/'\
			'AC087cabfd0a453a05acceb2810c100f69/Recordings/REf8afc497f43d8e1e9bc229a415ebe100'

	def multi_callgroup(self):
		return not bool(self.call_group)

	def save_parent_org(self, parent_org=None, billing_flag=None):
		""" Save organization parent relationship
		:param parent_org: is an instance of PracticeLocation
		:param billing_flag: billing_flag
		"""
		if parent_org:
			try:
				org_relation = OrganizationRelationship.active_objects.get(
						organization=self, parent=parent_org)
				org_relation.billing_flag = billing_flag
				org_relation.save()
			except OrganizationRelationship.DoesNotExist:
				org_relation = OrganizationRelationship.objects.create(organization=self, 
					parent=parent_org, create_time=time.time())
		else:
			OrganizationRelationship.active_objects.filter(
				organization=self, parent=parent_org).delete()

	def save_member_org(self, member_org=None, billing_flag=None):
		""" Save organization member relationship
		:param member_orgs: is an instance of PracticeLocation
		:param billing_flag: billing_flag
		"""
		if member_org:
			try: 
				member = OrganizationMemberOrgs.objects.get(from_practicelocation=self, 
						to_practicelocation=member_org)
				member.billing_flag = billing_flag
				member.save()
			except OrganizationMemberOrgs.DoesNotExist:
				OrganizationMemberOrgs.objects.create(from_practicelocation=self, 
					to_practicelocation=member_org, create_time=time.time(), 
						billing_flag=billing_flag)
		else:
			OrganizationMemberOrgs.objects.filter(from_practicelocation=self, 
					to_practicelocation=member_org).delete()

	def get_setting(self):
		""" Get org's setting object.
		:returns: an instance of OrganizationSetting
		"""
		if self.organization_setting and not self.organization_setting.delete_flag:
			return self.organization_setting
		else:
			org_type = self.organization_type
			if org_type and org_type.organization_setting and not \
					org_type.organization_setting.delete_flag:
				return org_type.organization_setting
			else:
				return None

	def get_setting_attr(self, key):
		""" Get org's setting's attribute value.
		:returns: setting's value
		"""
		setting = self.get_setting()
		if not setting:
			return False
		if not key or key not in dir(setting):
			return False
		return getattr(setting, key)

	def can_have_any_staff(self):
		setting = self.get_setting()
		if not setting:
			return None
		else:
			return setting.can_have_staff or setting.can_have_manager or \
				setting.can_have_nurse or setting.can_have_dietician

	def can_have_staff_member(self):
		setting = self.get_setting()
		if not setting:
			return None
		else:
			return setting.can_have_staff or setting.can_have_nurse or \
				setting.can_have_dietician

	def can_have_any_provider(self):
		setting = self.get_setting()
		if not setting:
			return None
		else:
			return setting.can_have_physician or setting.can_have_nppa or \
				setting.can_have_medical_student

	def get_org_sub_user_types_tuple(self, role_category=None, include_manager=True, 
						include_sub_staff_type=True):
		""" Get user's types that can save for this organization.

		:param role_category: int value if role_category is 1, return provider's 
			type tuple if role_category is 2, return staff's type tuple, 
			others(include None), return all user's type tuple
		:returns: tuple
		"""
		org_setting = self.get_setting()
		if org_setting is None:
			return ()
		provider_types = ()
		staff_types = ()
		if org_setting.can_have_physician:
			provider_types += ((USER_TYPE_DOCTOR, _('Doctor')),)
		if org_setting.can_have_nppa:
			provider_types += ((USER_TYPE_NPPA, _('NP/PA/Midwife')),)
		if org_setting.can_have_medical_student:
			provider_types += ((USER_TYPE_MEDICAL_STUDENT, _('Med/Dental Student')),)

		if include_manager and org_setting.can_have_manager:
			staff_types += ((USER_TYPE_OFFICE_MANAGER, _('Office Manager')),)

		if include_sub_staff_type:
			if org_setting.can_have_staff:
				staff_types += ((USER_TYPE_OFFICE_STAFF, _('Staff')),)
			if org_setting.can_have_nurse:
				staff_types += ((USER_TYPE_NURSE, _('Nurse')),)
			if org_setting.can_have_dietician:
				staff_types += ((USER_TYPE_DIETICIAN, _('Dietician')),)
		else:
			if org_setting.can_have_staff or org_setting.can_have_nurse or\
				org_setting.can_have_dietician:
				staff_types += ((USER_TYPE_OFFICE_STAFF, _('Staff')),)

		user_types = provider_types + staff_types
		if org_setting.can_have_tech_admin:
			user_types += ((USER_TYPE_TECH_ADMIN, _('Tech Admin')),)

		if role_category is None:
			return user_types
		if role_category == 1:
			return provider_types
		if role_category == 2:
			return staff_types
		return user_types

	def get_org_sub_user_types(self, format=0, role_category=None):
		""" Get user's types that can save for this organization.

		:param format: format is 0 or 1, 
			if format is 0, function will return list with user type flag
			if format is 1, function will return list with user type string
		:returns: list(id or type string)
		"""
		user_types = self.get_org_sub_user_types_tuple(role_category=role_category)
		return [t[format] for t in user_types]

	def get_parent_org(self):
		org_rss = OrganizationRelationship.objects.filter(organization=self)
		if org_rss and org_rss[0] and org_rss[0].parent and \
			org_rss[0].parent.id != RESERVED_ORGANIZATION_ID_SYSTEM:
			return org_rss[0].parent
		return None

DAYSNAMES = (
	(1, _('Monday')),
	(2, _('Tuesday')),
	(3, _('Wednesday')),
	(4, _('Thursday')),
	(5, _('Friday')),
	(6, _('Saturday')),
	(7, _('Sunday')),
)


#next set of models needed to keep track of open hours for each location
class PracticeHours(models.Model):
	"""
		holds open hours for each location per each day of the week, day of the week 
		match python's representation 0=Sunday if there is no office hours set for 
		a given day, we will treat office as closed
	"""

	practice_location = models.ForeignKey(PracticeLocation,
					related_name="practice_hours")	
	day_of_week = models.IntegerField(choices=DAYSNAMES)

	open = models.TimeField(help_text=HOURS_HELP_TEXT)
	close = models.TimeField(help_text=HOURS_HELP_TEXT)
	lunch_start = models.TimeField(help_text=HOURS_HELP_TEXT)
	lunch_duration = models.IntegerField(
					help_text=_("in minutes, 0 if the practice doesn't close for lunch"))

	class Meta:
		ordering = ["day_of_week"]
		verbose_name_plural = "Practice Hours"


#next set of models needed to keep track of open hours for each location
class PracticeHolidays(models.Model):
	"""
		holds days office closed for Holidays
	"""
	practice_location = models.ForeignKey(PracticeLocation, related_name='practice_holiday')	
	name = models.CharField(max_length=34, blank=True)
	designated_day = models.DateField(blank=False, validators=[validate_unixDate])

	class Meta:
		ordering = ["designated_day"]
		verbose_name_plural = "Practice Holidays"


#associations used by both office staff and providers
ASSOCIATION_ACTION_CHOICES = (
	('CRE', _('Created')),
	('RES', _('Resent')),
	('CAN', _('Canceled')),
	('REJ', _('Rejected')),
	('ACC', _('Accepted')),
)


class Pending_Association(models.Model):
	"""
 		 holds associations currently needing actions
	"""
	from_user = models.ForeignKey('MHLUsers.MHLUser', related_name='from_user_pa')
	to_user = models.ForeignKey('MHLUsers.MHLUser', related_name='to_user_pa')
	practice_location = models.ForeignKey(PracticeLocation, related_name='practice_pa')	
	created_time = models.DateTimeField()
	resent_time = models.DateTimeField(null=True)


class Log_Association(models.Model):
	"""
 		 holds associations currently needing actions
	"""
	association_id = models.IntegerField()
	from_user = models.ForeignKey('MHLUsers.MHLUser', related_name='from_user_la')
	to_user = models.ForeignKey('MHLUsers.MHLUser', related_name='to_user_la')
	practice_location = models.ForeignKey(PracticeLocation, related_name='practice_la')	
	action_user = models.ForeignKey('MHLUsers.MHLUser', related_name='user_la')
	action = models.CharField(max_length=3, choices=ASSOCIATION_ACTION_CHOICES)
	created_time = models.DateTimeField()

	def save_from_association(self, association, action_user_id, type=''):
		self.association_id = association.id
		self.from_user_id = association.from_user_id
		self.to_user_id = association.to_user_id
		self.practice_location_id = association.practice_location.id
		self.action_user_id = action_user_id
		self.action = type
		self.created_time = datetime.now()
		self.save()


class AccessNumber(models.Model):
	practice = models.ForeignKey(PracticeLocation)
	description = models.CharField(max_length=50, blank=True)
	number = MHLPhoneNumberField(blank=False)


#add by xlin in 20120411 to add class for store create info
CREATE_TYPE_CHOICES = (
	(1, _('Doctor')),
	(2, _('NP/PA/Midwife')),
	(3, _('Nurse')),
	(4, _('Dietician')),
)


class AccountActiveCode(models.Model):
	code = models.CharField(max_length=255, unique=True)
	sender = models.IntegerField()
	recipient = models.EmailField(verbose_name=_('Email Address'))
	userType = models.IntegerField(choices=CREATE_TYPE_CHOICES)
	practice = models.ForeignKey('MHLPractices.PracticeLocation',
						null=True, blank=True, default=None)
	requestTimestamp = models.DateTimeField(auto_now_add=True)


class ActiveOrganizationRelationship(models.Manager):
	def get_query_set(self):
		return super(ActiveOrganizationRelationship, self).get_query_set()\
				.filter(organization__delete_flag=False)


class OrganizationRelationship(models.Model):
	organization = models.ForeignKey('MHLPractices.PracticeLocation')
	parent = models.ForeignKey('MHLPractices.PracticeLocation',
			null=True, blank=True, default=None, related_name="parent_id")
	create_time = models.PositiveIntegerField(default=0)
	billing_flag = models.IntegerField(null=True, blank=True)

	objects = models.Manager()
	active_objects = ActiveOrganizationRelationship()

	class Meta():
		db_table = 'MHLPractices_organizationrelationship'
		unique_together = (("organization", "parent"),)


class OrganizationTypeSubs(models.Model):
	from_organizationtype = models.ForeignKey(OrganizationType, related_name="from_organizationtype")
	to_organizationtype = models.ForeignKey(OrganizationType, related_name="to_organizationtype")

	class Meta():
		db_table = 'MHLPractices_organizationtype_subs'
		unique_together = (("from_organizationtype", "to_organizationtype"),)
		verbose_name_plural = 'Organization Type Subs'


class ActiveOrganizationMemberOrgs(models.Manager):
	def get_query_set(self):
		return super(ActiveOrganizationMemberOrgs, self).get_query_set()\
			.filter(from_practicelocation__delete_flag=False, 
				to_practicelocation__delete_flag=False)


class OrganizationMemberOrgs(models.Model):
	from_practicelocation = models.ForeignKey(PracticeLocation, related_name="from_practicelocation")
	to_practicelocation = models.ForeignKey(PracticeLocation, related_name="to_practicelocation")
	create_time = models.PositiveIntegerField(default=0)
	billing_flag = models.IntegerField(null=True, blank=True)

	class Meta():
		db_table = 'MHLPractices_practicelocation_member_orgs'
		unique_together = (("from_practicelocation", "to_practicelocation"),)
		verbose_name_plural = 'Organization Member Orgs'

	objects = ActiveOrganizationMemberOrgs()
	full_objects = models.Manager()


class Pending_Org_Association(models.Model):
	"""
 		 holds org associations currently needing actions
	"""
	from_practicelocation = models.ForeignKey(PracticeLocation, 
			related_name="pending_org_from_practicelocation")
	to_practicelocation = models.ForeignKey(PracticeLocation, 
			related_name="pending_org_to_practicelocation")
	sender = models.ForeignKey('MHLUsers.MHLUser', related_name='pending_org_sender')
	create_time = models.PositiveIntegerField(default=time.time())
	resent_time = models.PositiveIntegerField(null=True)


class Log_Org_Association(models.Model):
	"""
 		 holds org associations currently needing actions
	"""
	association_id = models.IntegerField()
	from_practicelocation = models.ForeignKey(PracticeLocation, 
			related_name="pending_log_org_from_practicelocation  ")
	to_practicelocation = models.ForeignKey(PracticeLocation, 
			related_name="pending_log_org_to_practicelocation  ")
	sender = models.ForeignKey('MHLUsers.MHLUser', related_name='pending_org_log_sender')
	action_user = models.ForeignKey('MHLUsers.MHLUser', related_name='pending_org_log_action_user')
	action = models.CharField(max_length=3, choices=ASSOCIATION_ACTION_CHOICES)
	create_time = models.PositiveIntegerField(default=time.time())

