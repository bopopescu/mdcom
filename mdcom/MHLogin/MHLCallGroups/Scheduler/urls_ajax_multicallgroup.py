
try:
	from django.conf.urls import patterns
except ImportError:  # remove when django 1.5 fully integrated
	from django.conf.urls.defaults import patterns

urlpatterns = patterns('MHLogin.MHLCallGroups.Scheduler',
	(r'^getEvents/$', 'views_multicallgroup.getEvents'),  # get all events for specific time period
	(r'^newEvents/', 'views_multicallgroup.bulkNewEvents'),
	(r'^updateEvents/', 'views_multicallgroup.bulkUpdateEvents'),
	(r'^rulesCheck/', 'views_multicallgroup.rulesCheck'),
	(r'^undo/', 'views_multicallgroup.undo'),
	(r'^redo/', 'views_multicallgroup.redo'),
	(r'^getCurrentDate/', 'utils.getCurrentDate'),
	(r'^getViewInfo/', 'views_multicallgroup.getViewInfo'),
	(r'^saveViewInfo/', 'views_multicallgroup.saveViewInfo'),
	(r'^checkeUserInCallGroup/', 'views_multicallgroup.checkUserInCallGroup'),

	(r'^checkProviderInCallGroup/', 'views_multicallgroup.checkProviderInCallGroup'),
	(r'^addProviderInGroup/', 'views_multicallgroup.addProviderInGroup'),
	(r'^addPrvoderIn/', 'views_multicallgroup.addPrvoderIn'),
)
