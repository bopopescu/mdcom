
try:
	from django.conf.urls import patterns
except ImportError:  # remove when django 1.5 fully integrated
	from django.conf.urls.defaults import patterns


urlpatterns = patterns('MHLogin.MHLCallGroups.Scheduler',
	(r'^getEvents/$', 'views.getEvents'),  # get all events for specific time period
	(r'^newEvents/', 'views.bulkNewEvents'),
	(r'^updateEvents/', 'views.bulkUpdateEvents'),
	(r'^rulesCheck/', 'views.rulesCheck'),
	(r'^undo/', 'views.undo'),
	(r'^redo/', 'views.redo'),
	(r'^getCurrentDate/', 'utils.getCurrentDate'),
	(r'^getViewInfo/', 'views.getViewInfo'),
	(r'^saveViewInfo/', 'views.saveViewInfo'),
	(r'^checkeUserInCallGroup/', 'views.checkeUserInCallGroup'),
)
