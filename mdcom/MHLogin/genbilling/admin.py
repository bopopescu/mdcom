
from MHLogin.Administration.tech_admin import sites
from MHLogin.Administration.tech_admin import options

from MHLogin.genbilling.models import Account, AccountTransaction, Invoice, \
	Subscription, FailedTransaction


class SubscriptionAdmin(options.TechAdmin):
	list_display = ('practice_group_new', 'practice_location', 'product', 'price', 'is_active')
	search_fields = ('practice_group_new__practice_name', 'practice_location__practice_name',
					'product__code', 'product__description')


class AccountAdmin(options.TechAdmin):
	list_display = ('practice_group_new', 'owner', 'status', 'last_bill_date', 'last_payment_state')
	search_fields = ('practice_group_new__practice_name', 'owner__username',
					'owner__first_name', 'owner__last_name')


sites.register(Account, AccountAdmin)
sites.register(AccountTransaction)
sites.register(Invoice)
sites.register(Subscription, SubscriptionAdmin)
sites.register(FailedTransaction)

