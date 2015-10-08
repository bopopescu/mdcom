
from MHLogin.Administration.tech_admin import sites, options

from MHLogin.MHLCallGroups.models import CallGroup, CallGroupMember, Specialty


class CallGroupAdmin(options.TechAdmin):
	list_display = ('description', 'team', 'number_selection')


class CallGroupMemberAdmin(options.TechAdmin):
	list_display = ('member', 'call_group', 'alt_provider')
	list_filter = ('call_group',)


class SpecialtyAdmin(options.TechAdmin):
	list_display = ('name', 'practice_location', 'number_selection')


sites.register(CallGroup, CallGroupAdmin)
sites.register(CallGroupMember, CallGroupMemberAdmin)
sites.register(Specialty, SpecialtyAdmin)

