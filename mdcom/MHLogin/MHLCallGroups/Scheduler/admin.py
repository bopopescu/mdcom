
from MHLogin.Administration.tech_admin import sites, options

from MHLogin.MHLCallGroups.Scheduler.models import EventEntry


class EventEntryAdmin(options.TechAdmin):
	list_display = ('callGroup', 'oncallPerson', 'creator', 'startDate', 'endDate',
				'oncallLevel', 'eventStatus',)
	list_filter = ('oncallStatus', 'eventStatus', 'startDate', 'endDate',)
	search_fields = ('callGroup__description', 'oncallPerson__last_name',
					'oncallPerson__first_name', 'oncallPerson__username',)


sites.register(EventEntry, EventEntryAdmin)

