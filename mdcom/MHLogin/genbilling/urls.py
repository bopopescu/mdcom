
try:
	from django.conf.urls import patterns, url
except ImportError:  # remove when django 1.5 fully integrated
	from django.conf.urls.defaults import patterns, url


urlpatterns = patterns('MHLogin.genbilling.views',
    url(r'^account_history/$', 'account_history'),
    url(r'^billing_menu/$', 'billing_menu'),
    url(r'^find_customer/$', 'find_customer'),
    url(r'^find_invoices/$', 'find_invoices'),
 	url(r'^invoice_list/$', 'invoice_list'),
  	url(r'^invoice_details/$', 'invoice_details'),
  	url(r'^account_details/$', 'account_details'),
  	url(r'^enter_transaction/$', 'enter_transaction'),
  	url(r'^create_transaction/$', 'create_transaction'),
    url(r'^payments-billing/$', 'payments_billing', name='payments_billing'),
	url(r'^payments-billing-callback/$', 'payments_billing_callback', name='payments_billing_callback')
)

