
try:
	from django.conf.urls import patterns, url
except ImportError:  # remove when django 1.5 fully integrated
	from django.conf.urls.defaults import patterns, url


urlpatterns = patterns('MHLogin.Validates',
	url(r'^ValidationPage/$', 'views.validationPage'),
	url(r'^ContactInfo/$', 'views.contactInfo'),
	url(r'^SendCode/$', 'views.sendCode'),
	url(r'^Validate/$', 'views.validate'),
)
