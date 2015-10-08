
try:
	from django.conf.urls import include, patterns
except ImportError:  # remove when django 1.5 fully integrated
	from django.conf.urls.defaults import include, patterns


urlpatterns = patterns('MHLogin.MHLCallGroups.Scheduler',
	(r'^$', 'views_multicallgroup.display_scheduler'),
	(r'^Print/$', 'views_multicallgroup.getPrintableSchedule'),
	(r'^AJAX/', include('MHLogin.MHLCallGroups.Scheduler.urls_ajax_multicallgroup')),
)
