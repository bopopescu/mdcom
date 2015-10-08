
try:
	from django.conf.urls import include, patterns
except ImportError:  # remove when django 1.5 fully integrated
	from django.conf.urls.defaults import include, patterns


urlpatterns = patterns('',
	(r'^v1/', include('MHLogin.apps.smartphone.v1.urls')),
)
