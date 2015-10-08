
from MHLogin.Administration.tech_admin import sites, options

from MHLogin.MHLUsers.Sales.models import Products, SalesLeads, SalesProduct


class SalesLeadsAdmin(options.TechAdmin):
	list_display = ('rep', 'practice', 'region', 'stage', 'source')


class SalesProductAdmin(options.TechAdmin):
	list_display = ('_get_lead_info', 'product', 'quoted_price', 'is_active')

	_get_lead_info = lambda self, obj: '/'.join([str(obj.lead.rep), obj.lead.practice])
	_get_lead_info.short_description = 'Lead Info'


sites.register(Products)
sites.register(SalesLeads, SalesLeadsAdmin)
sites.register(SalesProduct, SalesProductAdmin)

