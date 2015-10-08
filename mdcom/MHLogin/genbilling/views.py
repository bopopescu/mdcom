
from urlparse import urljoin

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django_braintree.models import UserVault
from django.core.exceptions import ObjectDoesNotExist

from MHLogin.genbilling.models import Account, Invoice, AccountTransaction, Subscription
from MHLogin.genbilling.utils import get_current_billing_period, get_next_billing_period
from MHLogin.MHLUsers.models import  MHLUser, OfficeStaff, Office_Manager
from MHLogin.MHLPractices.models import PracticeLocation
from MHLogin.utils.templates import get_context

from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.urlresolvers import reverse

from braintree import Customer, TransparentRedirect
from django_common.decorators import ssl_required

from MHLogin.genbilling.forms import BraintreeForm, FindCustomerForm, ManualTransactionForm
from MHLogin.utils.errlib import err403
from decimal import Decimal

from django.utils.translation import ugettext_lazy as _

BAD_CC_ERROR_MSG = _('Oops! Doesn\'t seem like your Credit Card details are correct. Please re-check and try again.')
DUPLICATE_CC_ERROR_MSG = _('Billing information exists for this practice group and owned by different manager.')


#@account_owner_rights_required("/")
def account_history(request):
	"""
	Will create a list of every trasnaction that exist for the billing account of
	logged in user
	"""

	template_name = 'genbilling/account_history.html'
	context = get_context(request)
	context['no_account'] = False

	mhluser = MHLUser.objects.get(pk=request.user.pk)
	try:
		ostaff = OfficeStaff.objects.get(user=mhluser)
		omgr = Office_Manager.objects.get(user=ostaff, practice=ostaff.current_practice)
	except ObjectDoesNotExist:
		return err403(request)

	try:
		account = Account.objects.get(practice_group_new=\
				omgr.practice.get_parent_org())
	except ObjectDoesNotExist:
		context['no_account'] = True
		return render_to_response(template_name,
								context,
								context_instance=RequestContext(request))

	transactions = AccountTransaction.objects.filter(account=account)

	context['account'] = account
	context['transactions'] = transactions
	return render_to_response(template_name,
							context,
							context_instance=RequestContext(request))


@ssl_required()
@login_required
def payments_billing(request, template='genbilling/payments_billing.html'):
	context = get_context(request)

	check_for_duplicate = True
	mhluser = MHLUser.objects.get(pk=request.user.pk)

	try:
		ostaff = OfficeStaff.objects.get(user=mhluser)
		omgr = Office_Manager.objects.get(user=ostaff, practice=ostaff.current_practice)
	except ObjectDoesNotExist:
		return err403(request)
	if (omgr.manager_role != 2):
		return err403(request)

#per michael - office manager can manage mulyi location in SAME GROUP ONLY
#this is enforced via set up of user accounts and practicesby Docotor com staff!
#	practice_group = omgr.practice.practice_group
	practice_group = omgr.practice.get_parent_org()
	if  (practice_group is None):
		return err403(request)

	#for release 0.1 check if THIS practice group has account already, 
	#if yes, ONLY original user can change account
	try:
		account = Account.objects.get(practice_group_new=practice_group)
	except ObjectDoesNotExist:
		check_for_duplicate = False

	if (check_for_duplicate and account.owner != request.user):
		context['errors'] = DUPLICATE_CC_ERROR_MSG
		return render_to_response(template,
					context,
					context_instance=RequestContext(request))

	context['cc_form_post_url'] = TransparentRedirect.url()

	#see if this update or create
	if (check_for_duplicate):  # account exist
		user_vault = UserVault.objects.get_user_vault_instance_or_none(request.user)
		try:
			response = Customer.find(user_vault.vault_id)
			info = response.credit_cards[0]
			context['current_cc_info'] = True
			context['name'] = info.cardholder_name
			context['cc_number'] = info.masked_number
			context['expiration_date'] = info.expiration_date
			context['zip_code'] = info.billing_address.postal_code

		except Exception:
			context['errors'] = "Unable to retrieve your payment instrument "\
				"info, please notify support@mdcom.com."
			return render_to_response(template,
							context,
							context_instance=RequestContext(request))

	form = BraintreeForm(request.user, practice_group)

	# Generate the tr_data field; this MUST be called!
	if(settings.IS_DEV == True):
		call_back_url = '//%s%s' % (settings.SERVER_ADDRESS, 
				reverse('MHLogin.genbilling.views.payments_billing_callback'))
	else:
		abs_uri = '://'.join([settings.SERVER_PROTOCOL, settings.SERVER_ADDRESS])
		url = reverse('MHLogin.genbilling.views.payments_billing_callback')
		call_back_url = urljoin(abs_uri, url)
	if (check_for_duplicate):  # account exist
		tr_data = Customer.tr_data_for_update({
			"customer_id": user_vault.vault_id,
			"customer": {
				"credit_card": {
						"options": {
							"update_existing_token": info.token
						}
					}
				}
			}, call_back_url)
	else:
		tr_data = Customer.tr_data_for_create({
			"customer": {
				"company": practice_group.description
			}
		}, call_back_url)

	context['tr_data'] = tr_data

	return render_to_response(template,
							context,
							context_instance=RequestContext(request))


@ssl_required()
def payments_billing_callback(request, template='genbilling/payments_billing.html'):
	context = get_context(request)
	result = BraintreeForm.get_result(request)

	# If successful redirect to a thank you page
	if result and result.is_success:
		context['errors'] = "has been securely saved."
		#create vault if new customer and account
		try:
			UserVault.objects.get(user=request.user, vault_id=result.customer.id)
		except ObjectDoesNotExist:
			UserVault.objects.create(user=request.user, vault_id=result.customer.id)

		#this is ok as url only called by transparent redirect call back, and
		#NO ONE but office super manager with practice group set up should be calling this
		#if they do they will not go far

		mhluser = MHLUser.objects.get(pk=request.user.pk)
		#mhluser = request.session['MHL_Users']['MHLUser']
		ostaff = OfficeStaff.objects.get(user=mhluser)
		omgr = Office_Manager.objects.get(user=ostaff, practice=ostaff.current_practice)
#		practice_group = omgr.practice.practice_group
		practice_group = omgr.practice.get_parent_org()

		try:
			account = Account.objects.get(practice_group_new=practice_group)
			account.last_payment_state = Account.INITIAL_UPDATE_STATE
			account.save()
		except ObjectDoesNotExist:
			Account.objects.create(practice_group_new=practice_group, 
				owner=request.user, status=Account.ACTIVE_STATUS)
		#or just update account
		return render_to_response(template,
							context,
							context_instance=RequestContext(request))
	if result:
		context['errors'] = "Errors: %s" % " ".join(error.message for error in
							result.errors.deep_errors)
		return render_to_response(template,
							context,
							context_instance=RequestContext(request))
	#redirect to home
	return HttpResponseRedirect('/')


#set on internal use screen to manage billing
def billing_menu(request):
	"""
	Internal Use Menu to link to account management screens
	"""

	template_name = 'genbilling/billing_menu.html'
	context = get_context(request)

	return render_to_response(template_name,
							context,
							context_instance=RequestContext(request))


#find invoices for a period
def find_invoices(request):
	"""
	Internal Use Menu to find invoices for a period
	"""
	template_name = 'genbilling/find_invoices.html'
	context = get_context(request)
	return render_to_response(template_name,
							context,
							context_instance=RequestContext(request))


def invoice_list(request):
	"""
	Show invoices for desired period
	"""

	template_name = 'genbilling/invoice_list.html'
	context = get_context(request)
	context['no_invoices'] = True

	if 'begin_period' in request.POST:
		#get all invoices for the period
		transactions = AccountTransaction.objects.filter(
			period_start=request.POST['begin_period'], tx_type=0)
		if (len(transactions) > 0):
			#fill in account name
			for transaction in transactions:
				account = Account.objects.get(id=transaction.account_id)
				practice_group = PracticeLocation.objects.get(id=account.practice_group_new_id)
				transaction.customer = practice_group.description
				context['begin_period'] = request.POST['begin_period']
				context['transactions'] = transactions
				context['no_invoices'] = False

	return render_to_response(template_name,
							context,
							context_instance=RequestContext(request))


def invoice_details(request):
	"""
	Show details for specific invoice
	"""

	template_name = 'genbilling/invoice_details.html'

	context = get_context(request)

	if 'id' in request.GET:
		invoice_transaction = AccountTransaction.objects.get(id=request.GET['id'])
		#get customer info, and invoice total
		account = Account.objects.get(id=invoice_transaction.account_id)
		practice_group = PracticeLocation.objects.get(id=account.practice_group_new_id)
		invoice = Invoice.objects.get(accounttransaction=invoice_transaction)
		context['invoice_internal'] = invoice_transaction.id
		context['customer'] = practice_group.description
		context['invoice_no'] = invoice_transaction.reference_no
		context['inv_amount'] = invoice_transaction.amount
		context['created_on'] = invoice_transaction.created_on
		#create status description:
		if (invoice.paid):
			context['paid'] = "Paid"
		else:
			if (invoice.failed):
				context['paid'] = "Payment Rejected"	
			else:
				context['paid'] = "Not Paid"		

		#get all invoices for the period
		transactions = Account.get_all_transactions_for_invoice(account, invoice_transaction)
		context['transactions'] = transactions

	return render_to_response(template_name,
							context,
							context_instance=RequestContext(request))


#find account infor for aspecific customer
def find_customer(request):
	"""
	Internal Use Menu to find customer account info
	"""

	template_name = 'genbilling/find_customer.html'
	form = FindCustomerForm()

	context = get_context(request)
	context['practice_group_name'] = FindCustomerForm()
	return render_to_response(template_name,
							context,
							context_instance=RequestContext(request))


def account_details(request):
	"""
	Show details for specific account
	"""

	template_name = 'genbilling/account_details.html'

	context = get_context(request)

	if 'practice_group_name' in request.POST:
		#get account info
		account = Account.objects.get(id=request.POST['practice_group_name'])
		practice_group = PracticeLocation.objects.get(id=account.practice_group_new_id)
		context['customer'] = practice_group.description
		context['owner'] = account.owner

		transactions = AccountTransaction.objects.filter(account=account).order_by('-id')
		subscriptions = Subscription.objects.filter(practice_group_new=practice_group)

		context['account'] = account
		context['transactions'] = transactions
		context['subscriptions'] = subscriptions

	return render_to_response(template_name,
							context,
							context_instance=RequestContext(request))


#enter manual credit or debit for a customer
def enter_transaction(request):
	"""
	Internal Use Menu to create account transaction for an account
	"""
	template_name = 'genbilling/create_transaction.html'

	context = get_context(request)
	#get begin and end period

	context['begin_period'] = get_current_billing_period()
	context['end_period'] = get_next_billing_period()

	context['practice_group_name'] = ManualTransactionForm()

	return render_to_response(template_name,
							context,
							context_instance=RequestContext(request))


def is_number(s):
	try:
		float(s)
		return True
	except ValueError:
		return False							


def create_transaction(request):
	"""
	Internal Use Menu to create account transaction for an account
	"""
	template_name = 'genbilling/create_transaction.html'
	context = get_context(request)
	context['errors'] = ''

	if ('practice_group_name' in request.POST and 'type_choice_field' in request.POST 
		and 'amount' in request.POST and 'memo' in request.POST):
		#validate memo and amount
		a = request.POST['amount'].strip(' "')

		if is_number(a):
			amount = round(float(a), 2)
		else:
			amount = 0

		if (amount <= 0):
			context['errors'] = 'Amount Must be Numeric and Greater than 0.'
		elif(request.POST['memo'] == ''):
			context['errors'] = 'Memo is Required Entry Field.'
		else:
			#get account info
			account = Account.objects.get(id=request.POST['practice_group_name'])
			practice_group = PracticeLocation.objects.get(id=account.practice_group_new_id)
			amount_to_charge = Decimal(str(amount))
			if (request.POST['type_choice_field'] == '4'):  # debit
				transaction = AccountTransaction.objectMgr.create_manual_debit(
					account, amount_to_charge, request.POST['memo'])
			else:
				transaction = AccountTransaction.objectMgr.create_manual_credit(
					account, amount_to_charge, request.POST['memo'])
			context['errors'] = "Transaction Added To %s in amount of $%s with memo line: %s" % \
				(practice_group.description, transaction.amount, transaction.memo)
	else:  # something went wrong
		context['errors'] = 'Missing required parameters.'

	return render_to_response(template_name,
							context,
							context_instance=RequestContext(request))

