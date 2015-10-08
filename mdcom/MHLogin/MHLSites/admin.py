
from MHLogin.Administration.tech_admin import sites, options

from MHLogin.MHLSites.models import Hospital


class HospitalAdmin(options.TechAdmin):
	list_display = ('name', 'address1', 'city', 'state', 'zip')
	search_fields = ('name', 'city', 'state', 'zip',)


sites.register(Hospital)

