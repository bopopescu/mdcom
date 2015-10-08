
from django.core.exceptions import ValidationError

from MHLogin.Administration.tech_admin.management.commands.\
		create_admin_groups import TECH_ADMIN_GROUP
from MHLogin.Administration.tech_admin import sites, options
from MHLogin.Administration.tech_admin.forms import TechAdminForm, TechAdminUserForm

from MHLogin.MHLUsers.models import MHLUser, Provider, OfficeStaff, Physician,\
	Broker, Regional_Manager, Salesperson, PasswordResetLog
from MHLogin.MHLUsers.models import Nurse, NP_PA, Office_Manager, Dietician, Administrator
from MHLogin.MHLUsers.models import PhysicianGroup, PhysicianGroupMembers
from MHLogin.MHLUsers.models import EventLog
from MHLogin.utils.geocode import geocode2
from django.utils.translation import ugettext as _


class MHLUserAdmin(options.TechMHLUserAdmin):
	list_display = ('username', 'first_name', 'last_name', 'mobile_phone',
				'email', 'date_joined', 'last_login')
	list_filter = ('is_active', )
	search_fields = ('username', 'first_name', 'last_name', 'email', 'mobile_phone')

	def techadmin_queryset(self, request, qs):
		# filter more by groups matching all groups this tech admin is in
		query_grp = request.user.groups.exclude(name=TECH_ADMIN_GROUP)
		return qs.filter(groups__in=query_grp).distinct()

	def save_model(self, request, obj, form, change):
		if any(d in form.changed_data for d in ('address1', 'address2', 'city', 'state', 'zip')) or\
			((obj.lat == 0.0 and obj.longit == 0.0) or (obj.lat == None and obj.longit == None)):
			# attempt geocode only if not explicitly changing lat/longit or lat/long empty
			addr = "%s %s" % (obj.address1, obj.address2) if obj.address2 else obj.address1
			result = geocode2(addr, obj.city, obj.state, obj.zip)
			if (result['lat'] != 0.0 and result['lng'] != 0.0):
				obj.lat = result['lat']
				obj.longit = result['lng']

		super(MHLUserAdmin, self).save_model(request, obj, form, change)


class ProviderAdmin(MHLUserAdmin):
	class ProviderAdminForm(TechAdminUserForm):
		def clean_username(self):
			# Our unique Provider model needs extra form validation  
			uname = self.cleaned_data['username']
			other = Provider.objects.filter(username=uname).exclude(id=self.instance.id)
			if other.exists():
				raise ValidationError("Provider username must be unique, %s in use." % \
					 (', '.join("%s" % o.username for o in other)))

			return uname

	form = ProviderAdminForm
	list_display = ('username', 'first_name', 'last_name', 'mdcom_phone', 
		'mobile_phone', 'current_practice')
	list_filter = ('clinical_clerk', 'forward_voicemail', 'forward_anssvc', 'current_practice')
	search_fields = ('username', 'first_name', 'last_name', 'email', 'mdcom_phone', 
		'mobile_phone', 'practices__practice_name')
	filter_horizontal = ['sites', 'practices', 'licensure_states', 'groups', 'user_permissions']

	def save_model(self, request, obj, form, change):
		if any(d in form.changed_data for d in 
			('office_address1', 'office_address2', 'office_city', 'office_state', 'office_zip')) or \
			((obj.office_lat == 0.0 and obj.office_longit == 0.0) or \
			(obj.office_lat == None and obj.office_longit == None)):
			# attempt geocode only if not explicitly changing lat/longit or lat/long empty
			addr = "%s %s" % (obj.office_address1, obj.office_address2) \
				if obj.office_address2 else obj.office_address1
			result = geocode2(addr, obj.office_city, obj.office_state, obj.office_zip)
			if (result['lat'] != 0.0 and result['lng'] != 0.0):
				obj.office_lat = result['lat'] 
				obj.office_longit = result['lng']
		# Fix model, our 'unique' prov-mhuser reln: Provider is-a User and has-a User
		obj.user = obj if obj.user != obj else obj.user
		super(ProviderAdmin, self).save_model(request, obj, form, change)


class StaffUserAdmin(options.TechAdmin):
	""" Admin site for db models having at least one Foreign Key (FK) to MHLUsers
	"""
	class StaffUserAdminForm(TechAdminForm):
		def clean_current_practice(self):
			if self.cleaned_data['current_practice'] == None:
				raise ValidationError(_("Please select valid current practice."))
			return self.cleaned_data['current_practice']

	form = StaffUserAdminForm
	list_display = ('_get_username', '_get_firstname', '_get_lastname', '_get_mobile',
				'_get_email', '_get_additional')
	search_fields = ('user__username', 'user__first_name', 'user__last_name',)

	_get_username = lambda self, obj: obj.user.username
	_get_firstname = lambda self, obj: obj.user.first_name
	_get_lastname = lambda self, obj: obj.user.last_name
	_get_mobile = lambda self, obj: obj.user.mobile_phone
	_get_email = lambda self, obj: obj.user.email

	def __init__(self, model, admin_site):
		super(StaffUserAdmin, self).__init__(model, admin_site)
		from MHLogin.utils.constants import SPECIALTY_CHOICES
		self._specialty = dict(SPECIALTY_CHOICES)
		self._get_username.im_func.short_description = 'Username'
		self._get_firstname.im_func.short_description = 'First name'
		self._get_lastname.im_func.short_description = 'Last name'
		self._get_mobile.im_func.short_description = 'Mobile phone'
		self._get_email.im_func.short_description = 'Email'
		self._get_additional.im_func.short_description = 'Additional'
		if self.model == OfficeStaff:
			self.filter_horizontal = ['sites', 'practices']

	def changelist_view(self, request, extra_context=None):
		# _get_additional is class var so dynamically set here instead of c'tor
		if self.model == Physician:
			self._get_additional.im_func.short_description = "Specialty"
		elif self.model == OfficeStaff or self.model == Nurse or self.model == Dietician:
			self._get_additional.im_func.short_description = "Current Practice"
		elif self.model == Office_Manager:
			self._get_additional.im_func.short_description = "Role"
		else:
			self._get_additional.im_func.short_description = 'Additional'
		return super(StaffUserAdmin, self).changelist_view(request, extra_context)

	def get_form(self, request, obj=None, **kwargs):
		form = super(StaffUserAdmin, self).get_form(request, obj, **kwargs)
		from MHLogin.Administration.tech_admin.utils import is_techadmin
		if is_techadmin(request.user) and 'user' in form.base_fields:
			self._modify_user_query(request.user, form.base_fields['user'])
		return form

	def techadmin_queryset(self, request, qs):
		# filter more by groups matching all groups this tech admin is in
		query = request.user.groups.exclude(name=TECH_ADMIN_GROUP)
		return qs.filter(user__groups__in=query).distinct()

	def _get_additional(self, obj):
		rc = None
		if self.model == Physician:
			rc = self._specialty[obj.specialty] if obj.specialty in self._specialty \
				else obj.specialty
		elif self.model == OfficeStaff:
			rc = obj.current_practice
		return rc

	def _modify_user_query(self, user, field):
		""" helper to filter list results in tech-admin FK add/select users """
		if field.queryset:
			query = user.groups.exclude(name=TECH_ADMIN_GROUP)
			klass = field.queryset[0].__class__
			field.queryset = klass.objects.filter(groups__in=query).distinct()


class OfficeStaffUserAdmin(StaffUserAdmin):
	list_filter = ('current_practice',)


class StaffUserAdmin2(StaffUserAdmin):
	search_fields = ('user__user__username', 'user__user__first_name', 'user__user__last_name',)

	_get_username = lambda self, obj: obj.user.user.username
	_get_firstname = lambda self, obj: obj.user.user.first_name
	_get_lastname = lambda self, obj: obj.user.user.last_name
	_get_mobile = lambda self, obj: obj.user.user.mobile_phone
	_get_email = lambda self, obj: obj.user.user.email

	def _get_additional(self, obj):
		rc = None
		if self.model == Office_Manager:
			rc = obj.manager_role
		elif self.model == Nurse or self.model == Dietician:
			rc = obj.user.current_practice
		return rc

	def techadmin_queryset(self, request, qs):
		# filter more by groups matching all groups this tech admin is in
		query_grp = request.user.groups.exclude(name=TECH_ADMIN_GROUP)
		return qs.filter(user__user__groups__in=query_grp).distinct()

	def _modify_user_query(self, user, field):
		""" helper to filter list results in tech-admin FK add/select users """
		if field.queryset:
			query = user.groups.exclude(name=TECH_ADMIN_GROUP)
			klass = field.queryset[0].__class__
			field.queryset = klass.objects.filter(user__groups__in=query).distinct()


class Regional_ManagerAdmin(options.TechAdmin):
	list_display = ('_get_username', '_get_firstname', '_get_lastname', 
		'_get_mobile', '_get_email', '_get_additional')
	search_fields = ('office_mgr__user__user__username', 
		'office_mgr__user__user__first_name', 'office_mgr__user__user__last_name',)

	_get_username = lambda self, obj: obj.office_mgr.user.user.username
	_get_username.short_description = 'Username'
	_get_firstname = lambda self, obj: obj.office_mgr.user.user.first_name
	_get_firstname.short_description = 'First Name'
	_get_lastname = lambda self, obj: obj.office_mgr.user.user.last_name
	_get_lastname.short_description = 'Last Name'
	_get_mobile = lambda self, obj: obj.office_mgr.user.user.mobile_phone
	_get_mobile.short_description = 'Mobile'
	_get_email = lambda self, obj: obj.office_mgr.user.user.email
	_get_email.short_description = 'Email'
	_get_additional = lambda self, obj: obj.office_mgr.manager_role
	_get_additional.short_description = 'Role'

	def techadmin_queryset(self, request, qs):
		# filter more by groups matching all groups this tech admin is in
		query_grp = request.user.groups.exclude(name=TECH_ADMIN_GROUP)
		return qs.filter(office_mgr__user__user__groups__in=query_grp).distinct()

	def get_form(self, request, obj=None, **kwargs):
		form = super(Regional_ManagerAdmin, self).get_form(request, obj, **kwargs)
		from MHLogin.Administration.tech_admin.utils import is_techadmin
		if is_techadmin(request.user) and 'office_mgr' in form.base_fields:
			self._modify_user_query(request.user, form.base_fields['office_mgr'])
		return form

	def _modify_user_query(self, user, field):
		""" helper to filter list results in tech-admin FK add/select users """
		if field.queryset:
			query = user.groups.exclude(name=TECH_ADMIN_GROUP)
			klass = field.queryset[0].__class__
			field.queryset = klass.objects.filter(user__user__groups__in=query).distinct()


class PasswordResetLogAdmin(options.TechAdmin):
	list_display = ('user', 'reset', 'resolved', 'requestor', 'request_timestamp', 
		'reset_timestamp', 'servicer', 'resolution_timestamp')
	search_fields = ('user__username', 'servicer__username', 'requestor__username') 

	def has_add_permission(self, request):
		return False


sites.register(MHLUser, MHLUserAdmin)
sites.register(Provider, ProviderAdmin)
sites.register(OfficeStaff, OfficeStaffUserAdmin)
sites.register([Administrator, Broker, NP_PA, Physician, Salesperson], StaffUserAdmin)
sites.register([Nurse, Dietician, Office_Manager], StaffUserAdmin2)
sites.register(Regional_Manager, Regional_ManagerAdmin)
sites.register(EventLog)
sites.register(PhysicianGroup)
sites.register(PhysicianGroupMembers)
sites.register(PasswordResetLog, PasswordResetLogAdmin)

