from django.core.management import setup_environ
import settings
setup_environ(settings)
from django.core.management.base import BaseCommand, CommandError

from MHLogin.genbilling.models import Account, Invoice
from MHLogin.genbilling.utils import get_current_billing_period

class Command(BaseCommand):

    args = ''
    help = 'Find all unpaind invoices for current period and charge them'

    def error_and_exit(self, message):
        """
        Print the error and exit
        """
        raise CommandError(message)
        
    def handle(self, *args, **options):
    	"""
    	Get all Active accounts (based on flag active, NOT a account status)
    
    	for each active account, look for invoice account transaction (type = 0) for current period
   		and also get invoice row for each of the invoice account transactions
    	
    	attempt to charge total due on the invoice (ONLY IF NOT PAID ALREADY)
    	actual charge attempt and updates of all related data occurs in invoice.charge_this_invoice()    	
		"""

    	accounts = Account.objects.all()
        # Here we assume our billing period is monthly
        current_period = get_current_billing_period()

        for account in accounts:
			account.chargeInvoice(current_period)