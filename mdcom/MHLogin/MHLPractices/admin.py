
from MHLogin.Administration.tech_admin.management.commands.\
		create_admin_groups import TECH_ADMIN_GROUP
from MHLogin.Administration.tech_admin import sites, options
from MHLogin.Administration.tech_admin.forms import PracticeLocationForm

from MHLogin.MHLPractices.models import PracticeLocation, PracticeHours, \
	PracticeHolidays, Pending_Association, Log_Association, AccessNumber, \
	AccountActiveCode, OrganizationSetting, OrganizationRelationship, \
	OrganizationTypeSubs, OrganizationMemberOrgs, Pending_Org_Association, \
	Log_Org_Association

from MHLogin.utils.geocode import geocode2


class PracticeLocationAdmin(options.TechAdmin):
	list_display = ('practice_name', 'practice_phone', 'backline_phone',
		'mdcom_phone', 'practice_address1', 'practice_city',
		'practice_state', 'call_group', 'config_complete')
	search_fields = ('practice_name', 'practice_phone', 'backline_phone', 'mdcom_phone')
	filter_horizontal = ['call_groups']

	form = PracticeLocationForm

	def save_model(self, request, obj, form, change):
		if any(d in form.changed_data for d in
			('practice_address1', 'practice_address2', 
				'practice_city', 'practice_state', 'practice_zip')) or \
					((obj.practice_lat == 0.0 and obj.practice_longit == 0.0) or
					(obj.practice_lat == None and obj.practice_longit == None)):
			# attempt geocode only if not explicitly changing lat/longit or lat/long empty
			addr = "%s %s" % (obj.practice_address1, obj.practice_address2)
			result = geocode2(addr, obj.practice_city, obj.practice_state, obj.practice_zip)
			obj.practice_lat = result['lat']
			obj.practice_longit = result['lng']
		super(PracticeLocationAdmin, self).save_model(request, obj, form, change)

	def techadmin_queryset(self, request, qs):
		""" For practices change list to display empty practices or practices with
		one or more member belonging to request.user (tech_admin) groups """
		exclude_ids = []
		grps = request.user.groups.exclude(name=TECH_ADMIN_GROUP)
		for pract in qs:
			users = pract.get_members()
			if users:
				match = None
				# check if one or more members belong to request.user groups
				for u in users:
					match = u.groups.filter(id__in=(g.id for g in grps))
					if match:  # if match move on to next practice
						break
				# if no matches exclude this practice from list
				if not match:
					exclude_ids.append(pract.id)
		return qs.exclude(id__in=exclude_ids)


class PracticeHoursAdmin(options.TechAdmin):
	list_display = ('practice_location', 'day_of_week', 'open', 'close',
					'lunch_start', 'lunch_duration')


class PracticeHolidayAdmin(options.TechAdmin):
	list_display = ('practice_location', 'name', 'designated_day')


class Pending_AssociationAdmin(options.TechAdmin):
	list_display = ('from_user', 'to_user', 'practice_location', 'created_time', 'resent_time')


class Log_AssociationAdmin(options.TechAdmin):
	list_display = ('association_id', 'from_user', 'from_user', 'to_user', 'practice_location',
				'action_user', 'action', 'created_time')


class AccessNumberAdmin(options.TechAdmin):
	list_display = ('practice', 'description', 'number')


class AccountActiveCodeAdmin(options.TechAdmin):
	list_display = ('code', 'sender', 'recipient', 'userType', 'practice', 'requestTimestamp')


class OrganizationRelationshipAdmin(options.TechAdmin):
	list_display = ('organization', 'parent', 'create_time', 'billing_flag')


class OrganizationTypeSubsAdmin(options.TechAdmin):
	list_display = ('from_organizationtype', 'to_organizationtype')


class OrganizationMemberOrgsAdmin(options.TechAdmin):
	list_display = ('from_practicelocation', 'to_practicelocation', 'create_time', 'billing_flag')


class Pending_Org_AssociationAdmin(options.TechAdmin):
	list_display = ('from_practicelocation', 'to_practicelocation', 'sender', 
		'create_time', 'resent_time')


class Log_Org_AssociationAdmin(options.TechAdmin):
	list_display = ('association_id', 'from_practicelocation', 'to_practicelocation',
				'sender', 'action_user', 'action', 'create_time') 


sites.register(PracticeLocation, PracticeLocationAdmin)
sites.register(PracticeHours, PracticeHoursAdmin)
sites.register(PracticeHolidays, PracticeHolidayAdmin)
sites.register(Pending_Association, Pending_AssociationAdmin)
sites.register(Log_Association, Log_AssociationAdmin)
sites.register(AccessNumber, AccessNumberAdmin)
sites.register(AccountActiveCode, AccountActiveCodeAdmin)

sites.register(OrganizationSetting)
sites.register(OrganizationRelationship, OrganizationRelationshipAdmin)
sites.register(OrganizationTypeSubs, OrganizationTypeSubsAdmin)
sites.register(OrganizationMemberOrgs, OrganizationMemberOrgsAdmin)
sites.register(Pending_Org_Association, Pending_Org_AssociationAdmin)
sites.register(Log_Org_Association, Log_Org_AssociationAdmin)

