
try:
	from django.conf.urls import patterns, url
except ImportError:  # remove when django 1.5 fully integrated
	from django.conf.urls.defaults import patterns, url


urlpatterns = patterns('MHLogin.followup',
	url(r'^Add/$', 'views.addFollowUpAjax'),
	url(r'^Add/(?P<offset>\d+)/(?P<count>\d+)/$', 'views.addFollowUpAjaxOffset'),
	url(r'^Add/(?P<messageID>\d+)/(?P<msg_obj_str>\w+)/$', 'views.addFollowUp'),
	#url(r'^Add/(?P<msg_obj_str>\w+)/(?P<messageID>\d+)/$', 'views.addFollowUp'),
	url(r'^Add/(?P<msg_obj_str>\w+)/(?P<messageID>\w{,32})/$', 'views.addFollowUp'),

	url(r'^Reload/(?P<offset>\d+)/(?P<count>\d+)$', 'views.reloadFollowUp'),

	url(r'^Edit/(?P<followupID>\d+)$', 'views.editFollowUp'),
	url(r'^(?P<followupID>\w{,32})/Edit/$', 'views.editFollowUp'),

	url(r'^Del/(?P<followupID>\d+)/(?P<count>\d+)$', 'views.delFollowUp'),
	url(r'^(?P<followupID>\w{,32})$/Del/', 'views.delFollowUp'),

	url(r'^Done/(?P<followupID>\d+)/(?P<offset>\d+)/(?P<count>\d+)$', 'views.doneFollowUp'),
	url(r'^(?P<followupID>\w{,32})/Done/$', 'views.doneFollowUp'),
)
