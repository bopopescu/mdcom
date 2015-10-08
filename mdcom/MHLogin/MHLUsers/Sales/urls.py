
try:
	from django.conf.urls import patterns, url
except ImportError:  # remove when django 1.5 fully integrated
	from django.conf.urls.defaults import patterns, url


urlpatterns = patterns('MHLogin.MHLUsers.Sales',
	url(r'^$', 'views.dashboard', name='Sales_Dashboard'),
	url(r'^Invites/$', 'views.new_invites'),
	url(r'^Invites/(?P<invite_pk>\d+?)/Resend/$', 'views.resend_invite'),
	url(r'^Invites/(?P<invite_pk>\d+?)/Cancel/$', 'views.cancel_invite'),
	url(r'^Profile/$', 'views.profile'),
	url(r'^Profile/Edit/$', 'views.profile_edit_sales'),

	url(r'^salesleads/$', 'views.sales_view'),
	url(r'^sales_getdata/$', 'views.sales_getdata'),
	url(r'^sales_updatedata/$', 'views.sales_updatedata'),
	url(r'^sales_getproductdata/$', 'views.sales_getproductdata'),
	url(r'^sales_updateproductdata/$', 'views.sales_updateproductdata'),
	url(r'^sales_copyproductdata/$', 'views.sales_copyproductdata'),
	url(r'^sales_getuser_list/$', 'views.sales_getuser_list'),
	url(r'^sales_region_list/$', 'views.sales_region_list'),
	url(r'^sales_generate_excel/$', 'views.sales_generate_excel'),
)

