
try:
	from django.conf.urls import patterns
except ImportError:  # remove when django 1.5 fully integrated
	from django.conf.urls.defaults import patterns

urlpatterns = patterns('MHLogin.analytics',
	(r'^$', 'views.home'),

	# mapping
	(r'map/$', 'views.map_view'),
	(r'map/lost/$', 'views.map_lost'),
	(r'map/get_lost_list/$', 'views.map_get_lost_list'),
	(r'map/get_content_info/$', 'views.map_get_content_info'),
	# click to call
	(r'click2call/$', 'views.click2call'),
	# doctor pages
	(r'pages/$', 'views.pages'),
	# invitations
	(r'invites/$', 'views.invites'),
	# summary (messages, click2call, pages, site analytics)
	(r'summary/$', 'views.summary'),
	# twilio call stats, not shown yet
	(r'twilio/$', 'views.twilio_stats'), 
)

