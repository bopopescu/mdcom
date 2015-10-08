
from MHLogin.Administration.tech_admin import sites, options

from MHLogin.DoctorCom.models import PagerLog, Click2Call_Log, Click2Call_ActionLog,\
	SiteAnalytics, MessageLog


class Click2Call_LogAdmin(options.TechAdmin):
	list_display = ('caller', 'caller_number', 'called_user', 'called_number',
				'timestamp', 'source', 'connected', 'current_site')


class Click2Call_ActionLogAdmin(options.TechAdmin):
	list_display = ('action', '_get_click2call_log_callid', '_get_click2call_log_caller')

	def _get_click2call_log_callid(self, obj):
		return obj.callid
	_get_click2call_log_callid.short_description = 'CallId'

	def _get_click2call_log_caller(self, obj):
		return obj.caller
	_get_click2call_log_caller.short_description = 'Caller'


class MessageLogAdmin(options.TechAdmin):
	list_display = ('__unicode__', 'current_site', 'tx_number',
				'rx_number', 'timestamp', 'success')


class MessageTempAdmin(options.TechAdmin):
	list_display = ('user', 'timestamp')


class PagerLogAdmin(options.TechAdmin):
	list_display = ('pager', 'paged', 'current_site', 'callback', 'timestamp')


class SiteAnalyticsAdmin(options.TechAdmin):
	list_display = ('dateoflog', 'site', 'countPage', 'countMessage',
				 'countClick2Call', 'lastUpdate')


sites.register(PagerLog, PagerLogAdmin)
sites.register(Click2Call_Log, Click2Call_LogAdmin)
sites.register(MessageLog, MessageLogAdmin)
sites.register(SiteAnalytics, SiteAnalyticsAdmin)
sites.register(Click2Call_ActionLog, Click2Call_ActionLogAdmin)


from django.conf import settings
if(settings.DEBUG_MODELS):
	from MHLogin.utils.admin_utils import registerallmodels
	registerallmodels('DoctorCom')

