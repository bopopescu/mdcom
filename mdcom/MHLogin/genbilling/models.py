
from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from datetime import datetime
from calendar import monthrange

from django_braintree.models import PaymentLog, UserVault
from django.core.mail import EmailMessage
from django.utils.translation import ugettext as _

from MHLogin.utils.fields import UUIDField
from MHLogin.DoctorCom.Messaging.models import Message, MessageRecipient
from MHLogin.MHLPractices.models import PracticeLocation
from MHLogin.MHLUsers.models import MHLUser, OfficeStaff, Provider

from MHLogin.MHLUsers.Sales.models import Products

from MHLogin.genbilling.signals import credit_card_error, invoice_sent
from MHLogin.genbilling.utils import get_next_billing_period_for_date, \
	get_current_billing_period, get_next_billing_period

import logging
from django.conf import settings
from MHLogin.utils.mh_logging import get_standard_logger
from django.core.exceptions import ObjectDoesNotExist


# Setting up logging
logger = get_standard_logger('%s/genbilling/models.log' % \
	(settings.LOGGING_ROOT), 'genbilling.models', logging.WARN)


class _FauxRequestSession(object):
		session_key = ' '


class _FauxRequest(object):
		session = _FauxRequestSession


class AccountTransactionManager(models.Manager):
	def create_manual_debit(self, account, amount, memo):
		"""
		Posts Manual debit to account
		"""
		debit_transaction = AccountTransaction(account=account,
								tx_type='4',  # ATX_DEBIT
								amount=amount * -1,
								period_start=get_current_billing_period(),
								period_end=get_next_billing_period(),
								memo=memo)
		debit_transaction.save()

		return debit_transaction

	def create_manual_credit(self, account, amount, memo):
		"""
		Posts Manual Credit to account
		"""
		credit_transaction = AccountTransaction(account=account,
								tx_type='5',  # ATX_DEBIT
								amount=amount,
								period_start=get_current_billing_period(),
								period_end=get_next_billing_period(),
								memo=memo)
		credit_transaction.save()

		return credit_transaction

	def create_payment_for_invoice(self, invoice, charge):
		"""
		Posts payment transaction into genbiling_accounttransaction
		This method post payment for given invoice
		Manual payment use create_manual_payment function
		"""
		payment_memo = _("payment for invoice tx %(invoice_id)s, ref %(transaction_id)s") % \
			{'invoice_id': invoice.accounttransaction.id, 
				'transaction_id': charge.payment_log.transaction_id}
		payment_transaction = AccountTransaction(account=invoice.accounttransaction.account,
					tx_type='1',  # ATX_PAYMENT
					amount=charge.payment_log.amount,
					period_start=invoice.accounttransaction.period_start,
					period_end=invoice.accounttransaction.period_end,
					memo=payment_memo)
		payment_transaction.save()

		return payment_transaction

	def create_invoice(self, account, amount, current_period, next_period):
		"""
		Posts invoice transaction into genbiling_accounttransaction
		Creates invoice row to go with trasaction
		"""
		invoice_memo = _("Invoice for %(current_period)s -  %(next_period)s") % \
			{'current_period': current_period, 'next_period': next_period}
		invoice_transaction = AccountTransaction(account=account,
								tx_type='0',  # INVOICE
								amount=amount,
								period_start=current_period,
								period_end=next_period,
								memo=invoice_memo)
		invoice_transaction.save()

		invoice = Invoice(accounttransaction=invoice_transaction,
								paid=False,
								failed=False
								)
		invoice.save()

		return invoice

	def create_subscription(self, account, subscription, current_period, next_period):
		"""
		Posts charge transaction into genbiling_accounttransaction
		for the next month subscription for a product
		"""
		# determine amount of charge, normaly it is just price *-1
		# but in case of first time use, there may be prorated charges
		start_date = subscription.start_date  
		# datetime.datetime.strptime(subscription.start.date,"%Y-%m-%d")
		start_period = get_next_billing_period_for_date(start_date)

		if (start_period == current_period and start_date.day > 1):
		# we need to prorate
			num_of_day_in_month = monthrange(start_date.year, start_date.month)[1]
			price_per_day = subscription.price / num_of_day_in_month

			num_days_to_charge = (num_of_day_in_month + 1) - start_date.day

			amount = ((price_per_day * num_days_to_charge) + subscription.price) * -1
			charge_memo = _("%(description)s charge %(current_period)s - %(next_period)s "
						"plus first %(num_days)s days") % \
						{'description': subscription.product.description,
							'current_period': current_period, 'next_period': next_period, 
							'num_days': num_days_to_charge}
		else:
			amount = subscription.price * -1
			charge_memo = _("%(description)s charge %(current_period)s -  %(next_period)s") % \
							{'description': subscription.product.description, 
							'current_period': current_period, 'next_period': next_period}
		# append location to memo if needed
		if (subscription.practice_location != None):
			location = " (%s)" % (subscription.practice_location.practice_name)
			charge_memo = charge_memo + location

		subscription_transaction = AccountTransaction(account=account,
								tx_type='2',  # monthly product charge
								amount=amount,
								period_start=current_period,
								period_end=next_period,
								memo=charge_memo)
		subscription_transaction.save()

		return subscription_transaction


class Account(models.Model):
	"""Each billable entity (practice group) will have one account.
		status is actual state of account: active/trial/clsed/etc.
		last payment state is result of last charge attempt
		also stored date last time charge was attmpted/sucessfull or not
	"""

	TRIAL_STATUS = 'T'
	ACTIVE_STATUS = 'A'
	GRACE_STATUS = 'G'
	EXPIRED_STATUS = 'E'
	CANCELLED_STATUS = 'C'
	BILLINGINFO_INCOMPLETE_STATUS = 'I'

	STATUS_CHOICES = (
		(TRIAL_STATUS, _('Trial')),
		(ACTIVE_STATUS, _('Active')),
		(GRACE_STATUS, _('Grace')),
		(EXPIRED_STATUS, _('Expired')),
		(CANCELLED_STATUS, _('Cancelled')),
		(BILLINGINFO_INCOMPLETE_STATUS, _('Needs Payment Instrument')),
		)

	# used by access_granted function call
	GRANTED_STATUSES = [TRIAL_STATUS, ACTIVE_STATUS, GRACE_STATUS]

	BILL_STATUSES = [ACTIVE_STATUS, GRACE_STATUS]

	PAID_STATE = 'P'
	REJECTED_STATE = 'R'
	INITIAL_STATE = 'I'
	NOT_ATTEMPTED_STATE = 'N'
	INITIAL_UPDATE_STATE = 'U'

	STATE_CHOICES = (
		(PAID_STATE, _('Paid')),
		(REJECTED_STATE, _('Rejected')),
		(INITIAL_STATE, _('Inital Before First Charge')),
		(NOT_ATTEMPTED_STATE, _('No Charge Attempted')),
		(INITIAL_UPDATE_STATE, _('Inital AFTER CC UPDATE Before First Charge')),
		)

	account_no = UUIDField(max_length=255, auto=True, unique=True, editable=True)  
	# unique=True means index created
	practice_group_new = models.ForeignKey(PracticeLocation, unique=True,
			verbose_name=_('Organization'))
	owner = models.ForeignKey(User, unique=True)
	status = models.CharField(max_length=1, choices=STATUS_CHOICES, default=TRIAL_STATUS)
	last_bill_date = models.DateTimeField(blank=True, null=True)
	last_payment_state = models.CharField(max_length=1, choices=STATE_CHOICES, default=INITIAL_STATE)
	created_on = models.DateTimeField(auto_now_add=True)
	last_modified = models.DateTimeField(auto_now=True)

	class Meta:
		verbose_name = 'Account'
		verbose_name_plural = 'Accounts'

	def __unicode__(self):
		return "%s's account" % (self.owner.username)

	@property
	def bt_user_vault(self):
		return UserVault.objects.get_user_vault_instance_or_none(self.owner)

	def access_granted(self):
		""" Will return True in case status is contained GRANTED_STATUSES list,
			False in other case
		"""
		return self.status in self.GRANTED_STATUSES

	def billable(self):
		""" Will return True in case status is contained BILL_STATUSES list,
			we will only invoice and bill accounts with this status
			False in other case
		"""
		return self.status in self.BILL_STATUSES

	def get_invoice(self, period):
		"""Helper to get invoice for specific period for this account.

		:returns: the invoice from accoutntransaction related to the account, for a given period.
			Will return False if none invoice or more than 1 is found with for this period
		"""
		invoice_trasnaction = self.accounttransaction_set.filter(tx_type="0", period_start=period)

		if invoice_trasnaction.count() == 1:
			return invoice_trasnaction[0]
		else:
			return False

	def get_last_invoice_transaction(self):
		""" pulls up all invoice transactions for account, retruns one with lastest created date
			if no invoices found, returns false
		"""
		invoice_trasnaction = self.accounttransaction_set.filter(tx_type="0").order_by('created_on')

		if (invoice_trasnaction.count() == 0):
			return False
		else:
			return invoice_trasnaction[invoice_trasnaction.count() - 1]

	def get_all_transactions_for_invoice(self, invoice_transaction):
		""" pulls up all transaction that rolled into this invoice
		"""
		transactions = None
		prev_invoice_transactions = self.accounttransaction_set.filter(account=self, 
			tx_type="0", created_on__lt=invoice_transaction.created_on).order_by('created_on')
		if (prev_invoice_transactions.count() == 0):
			last_invoice_transaction = None
		else:
			last_invoice_transaction = prev_invoice_transactions[prev_invoice_transactions.count() - 1]

		if (last_invoice_transaction):
			# get all transaction created after it
			transactions = AccountTransaction.objects.filter(account=self, 
				created_on__gt=last_invoice_transaction.created_on, 
				created_on__lte=invoice_transaction.created_on).exclude(tx_type="1")
		else:
			# get all transactions for account
			transactions = AccountTransaction.objects.filter(account=self, 
				created_on__lte=invoice_transaction.created_on)

		return transactions

	def update_recurring_bill_success(self):
		"""Update genbilling_account with status and dates indicating last succesfull charge
		"""
		self.last_bill_date = datetime.now()
		self.last_payment_failed = False
		self.last_payment_state = 'P'  # PAID_STATE
		self.save()

	def update_recurring_bill_failure(self, invoice, charge):
		"""Update genbilling_account with status and dates indicating last succesfull charge
			also save faulire codes in separate table
		"""
		self.last_bill_date = datetime.now()
		self.last_payment_failed = True
		self.last_payment_state = 'R'  # REJECTED_STATE
		self.save()

		# save failure code
		failed_transaction = FailedTransaction(accounttransaction=invoice.accounttransaction,
			response_code=charge.response_code, message=charge.message)
		failed_transaction.save()

	def createInvoice(self, current_period, next_period):
		if (self.billable()):
			# first see if this account already has been invoiced this period, ONLY invoice ONVE
			invoice_trasnaction = self.get_invoice(current_period)

			if not invoice_trasnaction:
				# start creating charge lines and then invoice
				# get this account's active subscriptions, for eacf of subscriptions create CHARGE line
				subscriptions = Subscription.objects.filter(
					practice_group_new=self.practice_group_new, is_active=1)
				for subscription in subscriptions:
					# datetime.datetime.strptime(subscription.start_date,"%Y-%m-%d")
					start_date = subscription.start_date
					start_period_with_day = start_date.year * 10000 + \
						start_date.month * 100 + start_date.day
					current_period_with_day = current_period * 100 + 1

					if (current_period_with_day >= start_period_with_day):
						AccountTransaction.objectMgr.create_subscription(self, 
							subscription, current_period, next_period)
					# if start date greater than 1st of this month, skip
					#=========  done creating detail subscription charges ====================

				# if we here, user does not have invoice yet. create one: account
				# transaction and invoice rows
				last_invoice_trasnaction = self.get_last_invoice_transaction()

				if (last_invoice_trasnaction):
					# get all transaction created after it
					transactions = AccountTransaction.objects.filter(account=self,
						created_on__gt=last_invoice_trasnaction.created_on)
					sum_amt = last_invoice_trasnaction.amount * -1
				else:
					# get all transactions for account
					transactions = AccountTransaction.objects.filter(account=self)
					sum_amt = 0

				for transaction in transactions:
					sum_amt = sum_amt + transaction.amount
				# actual invoice amount stores as positve, so negate amount
				sum_amt = sum_amt * -1
				# now we can create transaction and invoice
				AccountTransaction.objectMgr.create_invoice(self, sum_amt, current_period, next_period)

	def chargeInvoice(self, current_period):
		if (self.billable()):

			invoice_trasnaction = self.get_invoice(current_period)

			if not invoice_trasnaction:
				invoice = False
			else:
				# get actual invoice data
				invoice = Invoice.objects.get(accounttransaction=invoice_trasnaction.id)

			# if invoice not found, something wrong with our data, report and error
			if invoice:
				if not invoice.paid:
					# take this invoice, and call braintree to charge, also update paid and failed flags
					# will add notification of charge if needed to charge_this_invoice function
					invoice.charge_this_invoice()


class AccountTransaction(models.Model):
	"""This is basic building block to keeping track of accounts debits and credits]
	also keeps invoice transaction (that is sum of all trasnactions for this month and does not 
    affect current balance)
    type of charge/debit is store in tx_type -for any new type of General Ledger like transaction 
    that we want to affect customer next invoice balance, add new type of account transaction
    credits stored as positive numbers, debits as negative
    please write period start and end for each transactions in form of yyyymm, that is 
    used for monthly balances and invoices

    some types of transactions may have associated models to store this specific 
    trasnaction type info such as Invoice
	 """
	# ATX stands for account transaction
	ATX_INVOICE = '0'
	ATX_PAYMENT = '1'
	ATX_PRODUCT_MONTHLY_CHARGE = '2'
	ATX_REFERRAL_CHARGE = '3'
	ATX_MANUAL_DEBIT = '4'
	ATX_MANUAL_CREDIT = '5'

	ATX_TYPE_CHOICES = (
		(ATX_INVOICE, _('Invoice')),
		(ATX_PAYMENT, _('Payment')),
		(ATX_PRODUCT_MONTHLY_CHARGE, _('Product Monthly Fee')),
		(ATX_REFERRAL_CHARGE, _('Referral')),
		(ATX_MANUAL_CREDIT, _('Manual Credit')),
		(ATX_MANUAL_DEBIT, _('Manual Debit')),
		)

	account = models.ForeignKey(Account)
	reference_no = UUIDField(max_length=64, auto=True, unique=True)  # unique=True means index created
	tx_type = models.CharField(max_length=3, choices=ATX_TYPE_CHOICES, null=False)
	amount = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('00.00'), blank=True)
	created_on = models.DateTimeField(auto_now_add=True)
	period_start = models.IntegerField(default=0)
	period_end = models.IntegerField(default=0)
	memo = models.CharField(max_length=200)
	objects = models.Manager()
	objectMgr = AccountTransactionManager()

	class Meta:
		verbose_name = 'Account Transaction'
		verbose_name_plural = 'Accounts Transactions'

	def __unicode__(self):
		return "%s's account tx_type = %s transaction for $%s" % \
			(self.account.owner.username, self.tx_type, self.amount)


class FailedTransaction(models.Model):
	"""Stores reject codes from braintree for the charge transactions that are rejected
		one transaction will have as many Failed Transactions as times it was rejected. 
		None or One or More.
		It is tied to account transactions not invoice, only to provide for 
		future flexability, if we would decide to charge manually 
	"""
	accounttransaction = models.ForeignKey(AccountTransaction, unique=False)
	response_code = models.IntegerField(null=False)
	message = models.CharField(max_length=200)

	def __unicode__(self):
		return "%s's account failed charge for $%s" % \
			(self.accounttransaction.account.owner.username, self.accounttransaction.amount)

	class Meta:
		verbose_name = 'Failed Charge Transaction'
		verbose_name_plural = 'Failed Charge Transactions'


class Invoice(models.Model):
	"""Stores information for invoice trasnactions that only applicable to invoice transaction
	   ONE TO ONE relationship with accounttransaction
	   also ties to payment log is invoice paid successfully
	   and paid/failed are used for reprocessing and paid invoices lookups
	"""
	accounttransaction = models.OneToOneField(AccountTransaction)
	paid = models.BooleanField(default=False)
	failed = models.BooleanField(default=False)
	paymentlog = models.OneToOneField(PaymentLog, null=True)

	class Meta:
		verbose_name = 'Invoice'
		verbose_name_plural = 'Invoices'

	def __unicode__(self):
		return "%s's account invoice transaction for $%s" % \
			(self.accounttransaction.account.owner.username, self.accounttransaction.amount)

	def charge_this_invoice(self):
		"""Once invoice to be paid is found, it will call this method.
		This method will look up vault for account on this invoice,
		If found, will call braintree to charge account amount set on invoice
		If success, mark invoice as processed, update account and create account trasnaction 
		for payment If failure, mark invoice as failed, update account, and save failure code.

		if not user vault found, do nto attemp braintree charge but mark invoice as failed, 
		update account

		Uses messages to communicate failure or charge to account holder and email 
		failures to doctor com support
		"""

		amount = self.accounttransaction.amount
		if (amount <= 0):
			return

		account = self.accounttransaction.account
		user_vault = account.bt_user_vault

		# user vault is not connected to owner of account, message support, 
		# do not charge until resolved
		if not user_vault:
			# update invoice row
			self.failed = True
			self.save()
			# update account row
			account.last_bill_date = datetime.now()
			account.last_payment_failed = True
			account.last_payment_state = 'N'  # NOT_ATTEMPTED_STATE
			account.save()
			# inform maager and support of no cc found on file
			credit_card_error.send(sender=self, invoice=self, charge=None, owner=account.owner)
			return

		# actuall charge via braintree happens here!
		charge = user_vault.charge(self.accounttransaction.amount)
		# charge went thru OK, update related accounting tables
		if charge.is_success:
			# update invoice row
			self.paid = True
			self.failed = False
			self.paymentlog = charge.payment_log
			self.save()
			# add row to account transaction of type payment, tie to brian tree transaction id
			# charge.payment_log has info from braintree
			AccountTransaction.objectMgr.create_payment_for_invoice(self, charge)
			# update account row
			account.update_recurring_bill_success()
			# inform manager of charge
			invoice_sent.send(sender=self, invoice=self, charge=charge, owner=account.owner)
		else:
			# charge failed, update related tables, also store braintrees rejection code 
			# attached to account transaction not to invoice, in case we ever want to 
			# create separate charge transactions
			# update invoice
			self.failed = True
			self.save()
			# update account row
			account.update_recurring_bill_failure(self, charge)
			# inform manager and support of failed charge
			credit_card_error.send(sender=self, invoice=self, charge=charge, owner=account.owner)


class Subscription(models.Model):
	"""Stores products practice GROUP subscribed to and price to be charged 
	monthly for each group/product.
	Only Active subscriptions get a charge line on customer's invoice
	If practice location added, will show separate line on the invoice for each location, 
	but total bill is per GROUP
	"""
	practice_group_new = models.ForeignKey(PracticeLocation,
		related_name="%(class)s_related_practice_group", verbose_name=_('Organization'))
	practice_location = models.ForeignKey(PracticeLocation, blank=True,
		null=True, verbose_name=_('Sub Organization'))
	product = models.ForeignKey(Products)
	is_active = models.BooleanField(default=False)
	price = models.DecimalField(max_digits=20, decimal_places=2)
	start_date = models.DateTimeField(blank=True, null=True)
	created_on = models.DateTimeField(auto_now_add=True)
	last_modified = models.DateTimeField(auto_now=True)

	class Meta:
		verbose_name = 'Subscription'
		verbose_name_plural = 'Subscriptions'

	def __unicode__(self):
		return "%s's subscription for $%s product" % \
			(self.practice_group_new.description, self.product.description)


def handle_errors(invoice, charge, owner, **kwargs):
	if not charge:
		# The user does not have a CC# number attached and charge never went through
		# logging.error(" %s does not have credit card entered", owner)

		# Notify the user via docotor com messaging, its account owner who gets message
		msg = Message(sender=None, sender_site=None, 
			subject="Action required: Please set up Doctor Com Billing")
		recipient = MHLUser.objects.get(id=owner.id)
		msg.urgent = False
		msg.message_type = 'NM'
		msg.save()

		formatted_body = "The last charge for your last invoice in the amount of $%s was " \
			"rejected due to the missing billing information of file. Please update your " \
			"billing information. Contact support@mdcom.com, if you have any additional " \
			"questions." % (invoice.accounttransaction.amount)
		attachments = []
		msg_body = msg.save_body(formatted_body)

		MessageRecipient(message=msg, user=recipient).save()
		# Send the message
		request = _FauxRequest()
		msg.send(request, msg_body, attachments)

		# email support
		email_body = "Account number %s failed autopayment due to account owner not " \
			"having a payment instrument on file." % (invoice.accounttransaction.account.id)
		email_msg = EmailMessage("Problem with payment",
			email_body, settings.DEFAULT_FROM_EMAIL, settings.SUPPORT_RECIPIENTS)
		email_msg.send()
	else:
		# logging.error(" %s error charging with message. %s", (owner, charge.message))
		# Notify the user via docotor com messaging, its account owner who gets message
		msg = Message(sender=None, sender_site=None, subject="Action required: "
			"Your last auto payment was rejected")
		recipient = MHLUser.objects.get(id=owner.id)
		msg.urgent = False
		msg.message_type = 'NM'
		msg.save()

		formatted_body = _("The last charge for your last invoice in the amount of "
			"$%(amount)s was rejected with the following error: %(message)s Please update "
			"your billing information. Contact support@mdcom.com if you have any additional "
			"questions.") % {'amount': charge.amount, 'message': charge.message}
		attachments = []
		msg_body = msg.save_body(formatted_body)

		MessageRecipient(message=msg, user=recipient).save()
		# Send the message
		request = _FauxRequest()
		msg.send(request, msg_body, attachments)

		# email support
		email_body = "Account number %(account_id)s failed autopayment due to the " \
			"following error %(message)s" % {'account_id': invoice.accounttransaction.account.id, 
				'message': charge.message}
		email_msg = EmailMessage("Problem with payment",
			email_body, settings.DEFAULT_FROM_EMAIL, settings.SUPPORT_RECIPIENTS)
		email_msg.send()


def handle_charge(invoice, charge, owner, **kwargs):
	# Notify the user via docotor com messaging, its account owner who gets message
	msg = Message(sender=None, sender_site=None, subject=_("Your Autopayment Processed"))
	recipient = MHLUser.objects.get(id=owner.id)
	msg.urgent = False
	msg.message_type = 'NM'
	msg.save()

	formatted_body = _("The payment in amount of $%s was charged to your credit card on file.") \
		% (charge.amount)
	attachments = []
	msg_body = msg.save_body(formatted_body)

	MessageRecipient(message=msg, user=recipient).save()
	# Send the message
	request = _FauxRequest()
	msg.send(request, msg_body, attachments)

credit_card_error.connect(handle_errors)
invoice_sent.connect(handle_charge)


def hasPermissionToUse(mhlUser, product_code):
	"""
    This is a SUBSCRIPTION check, not security permission or actually paying status!
    This is for a USER. Based on what practices he belongs to and subscription status of the practices.
    Will return True if user has active current subscription for a product specified by product_code
    Will return False if subscription not active, not current or does not exist in genbilling_subscription

    If product_code does not match code in  Sales_products, will return True and logs a warning

    Business logic differs per products. 
    As of now implemented file sharing product: 
             user considered ok to use product if he belongs to ANY practice location that 
             has active subscription for file sharing
    """
	# check if product code is valid in Sales_products table

	products = Products.objects.filter(code=product_code)
	if (products.count() != 1):
	# log incorrect code sent error
		logger.warning('Error product code sent %s. Number of rows in sales_products with '
			'code is %s' % (product_code, products.count()))
		return True  # for now customer gets a free pass, until we fix data issue
	# process file sharing product
	if (product_code == 'fsh_srv'):
		# now we need to get either Provider or OfficeStaff
		try:
			user_with_practices = OfficeStaff.objects.get(user=mhlUser)
		except ObjectDoesNotExist:
			try:
				user_with_practices = Provider.objects.get(user=mhlUser)
			except ObjectDoesNotExist:
				return False  # not provider, not office staff NOT going to be subscribed 
			# to file sharing

		# take user and check his practices, if find active file sharing product in one 
		# of the practice locations, return true
		practices_set = user_with_practices.practices.all()
		return_val = Subscription.objects.filter(product=products[0], 
			practice_location__in=practices_set, is_active=1, 
			start_date__lte=datetime.now()).exists()
		return return_val
	else:
		# for all the rest of products if checked for will return True until we 
		# define business logic for each product subscription
		return True


def hasActiveSubscription(practiceLocation, product_code):
	"""
    This is a SUBSCRIPTION check, not security permission or actually paying status!
    This is for a PRACTICE LOCATION. 

    Will return True if practice location has active current subscription for a product 
    specified by product_code.

    Will check for GROUP PRACTICE level subscription only if no rows (active, expired, 
    non active, etc) exists for this practice location, and will return True if active 
    current subscription for a product specified by product_code exist at GROUP PRACTICE level.
    (assumes not ALL locations have business umbrella assigned yet, skip above check 
    for locations with GROUP PRACTICE null)

    Will return False if subscription not active, not current or does not exist 
    in genbilling_subscription

    If product_code does not match code in  Sales_products, will return True and 
    logs a warning If practice location does NOT have group practice umbrella 
    assigned yet, will return True and log a warning

    Same logic applies to all products. 
    """
	# check if product code is valid in Sales_products table

	products = Products.objects.filter(code=product_code)
	if (products.count() != 1):
	# log incorrect code sent error
		logger.warning('Error product code sent %s. Number of rows in sales_products '
			'with code is %s' % (product_code, products.count()))
		return True  # for now customer gets a free pass, until we fix data issue

	# check for exact practice location match
	return_val = Subscription.objects.filter(product=products[0], 
		practice_location=practiceLocation, is_active=1, start_date__lte=datetime.now()).exists()

	# if no subscription found, check is we need to look at group practice
	if (not return_val):
		org_parent = practiceLocation.get_parent_org()
		if (org_parent is None):  # old style practice
			logger.warning('Check subscription for Location %s failed.Returned True.Group '
				'Practice NOT set up.' % (practiceLocation.practice_name))
			return True  # for now customer gets a free pass, until we set up group 
		# practice for this practice location
		else:  # new style practice with business umbrella set up
			# check is ANY rows exist for this practice location, as it takes precedence over group level
			any_subscrtiptions = Subscription.objects.filter(product=products[0], 
				practice_location=practiceLocation).exists()
			if (not any_subscrtiptions):  # still not found any subscriptions
				# check by practice group
				return_val = Subscription.objects.filter(product=products[0], 
					practice_group_new=org_parent, practice_location__isnull=True, 
					is_active=1, start_date__lte=datetime.now()).exists()

	return return_val



