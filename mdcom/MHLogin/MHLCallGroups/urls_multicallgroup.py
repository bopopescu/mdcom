
try:
	from django.conf.urls import include, patterns
except ImportError:  # remove when django 1.5 fully integrated
	from django.conf.urls.defaults import include, patterns


urlpatterns = patterns('MHLogin.MHLCallGroups',
	(r'^Schedule/', include('MHLogin.MHLCallGroups.Scheduler.urls_multicallgroup')),
	(r'AJAX/getMembers/', 'views_multicallgroup.getMembers'),
)
