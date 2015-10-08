
from django.conf.urls import patterns, url


urlpatterns = patterns('MHLogin.MHLUsers.forgotpassword.views',
	# step 1: initial form, validate user, send email
	url(r'^$', 'forgot_password', name='forgot_password'),
	url(r'^emailsent/$', 'email_sent', name='email_sent'),
	# step 2: process and validate email, change user password
	url(r'^change/(?P<token>[\w:-]+)/(?P<tempcode>\w+)/$', 'password_change', name='password_change'),
	url(r'^complete/$', 'password_complete', name='password_complete'),
)

