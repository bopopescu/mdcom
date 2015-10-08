
try:
	from django.conf.urls import patterns, include
except ImportError:  # remove when django 1.5 fully integrated
	from django.conf.urls.defaults import patterns, include


urlpatterns = patterns('MHLogin.apps',
	(r'^smartphone/', include('MHLogin.apps.smartphone.urls')),
)
