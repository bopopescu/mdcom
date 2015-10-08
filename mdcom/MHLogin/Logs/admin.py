
try:
	from django.conf.urls import patterns, url
except ImportError:  # remove when django 1.5 fully integrated
	from django.conf.urls.defaults import patterns, url

from MHLogin.Administration.tech_admin import sites, options

from MHLogin.Logs.models import LogFiles
from MHLogin.Logs.views import logfiles_list, logfile_view


class EventAdmin(options.TechAdmin):
	fieldsets = [
		(None, {
			'fields':(
				'timestamp',
			)}),
	]


class LoginEventAdmin(options.TechAdmin):
	fieldsets = [
		(None, {
			'fields':(
				('username', 'success', 'timestamp'),
				('remote_ip', 'user'),
			)}),
	]


class LogoutEventAdmin(options.TechAdmin):
	fieldsets = [
		(None, {
			'fields':(
				('user', 'timestamp'),
			)}),
	]


class LogFilesAdmin(options.TechAdmin):
	def urls(self):
		info = self.model._meta.app_label, self.model._meta.module_name
		return patterns('',
			url(r'^$', logfiles_list, name='%s_%s_changelist' % info, 
					kwargs={'root_path': '/dcAdmin/tech_admin/'}),
			url(r'^(?P<logfile_id>\d+)/$', logfile_view, name='log-file-admin', 
					kwargs={'root_path': '/dcAdmin/tech_admin/'}))
	urls = property(urls)

	def has_add_permission(self, request):
		return False


sites.register(LogFiles, LogFilesAdmin)
#sites.register(Event, EventAdmin)
#sites.register(LoginEvent, LoginEventAdmin)
#sites.register(LogoutEvent, LogoutEventAdmin)

