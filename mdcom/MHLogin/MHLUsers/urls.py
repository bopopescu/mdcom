
from django.conf.urls import patterns


urlpatterns = patterns('MHLogin.MHLUsers.views',
	(r'^$', 'profile_view'),
	(r'^Edit/$', 'profile_edit'),
	(r'^ChangePassword/$', 'change_password'),

	# User self-management - Settings
	(r'^Settings/ChangePin/$', 'changepin'),

	(r'^Forwarding/Voicemail/$', 'mdcom_forwarding'),
	(r'^Forwarding/AnsweringService/$', 'anssvc_forwarding'),
)
