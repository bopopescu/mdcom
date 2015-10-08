from django.core.management import setup_environ
import settings
setup_environ(settings)
from django.core.management.base import BaseCommand, CommandError

from MHLogin.genbilling.models import Account, Invoice, AccountTransaction, Subscription
from MHLogin.genbilling.utils import get_current_billing_period, get_next_billing_period

import datetime 

class Command(BaseCommand):
    args = ''
    help = 'Create next period invoice, if it doesnt exist yet, for every active account'

        
    def handle(self, *args, **options):
    
        accounts = Account.objects.all()
        
        # Here we assume our billing period is monthly, first or later day of month
        current_period = get_current_billing_period()
    	next_period = get_next_billing_period()

        for account in accounts:
        	account.createInvoice(current_period, next_period)