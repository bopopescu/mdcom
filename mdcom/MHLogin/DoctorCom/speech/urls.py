
try:
	from django.conf.urls import patterns, url
except ImportError:  # remove when django 1.5 fully integrated
	from django.conf.urls.defaults import patterns, url


urlpatterns = patterns('MHLogin.DoctorCom.speech',

	# filename does not support extensions, do we want to keep it like that?
	url(r'^get_voice_clip/(?P<confname>\w+)/(?P<filename>\w+)/$', 'views.get_voice_clip'),

	url(r'^debug/$', 'views.debug'),
)

