from django import forms
import logging

import datetime

from django_common.helper import md5_hash
from braintree import TransparentRedirect, Transaction, Customer, CreditCard
from django_braintree.models import UserVault
from MHLogin.genbilling.models import Account, AccountTransaction

#from django.forms.util import ErrorDict, ErrorList
from braintree.exceptions.not_found_error import NotFoundError
from MHLogin.genbilling.utils import get_response, get_current_billing_period, get_next_billing_period


class BraintreeForm(forms.Form):
	"""
		A base Braintree form that we use to get cc via transparent redirect
	"""
	

	@classmethod
	def get_result(cls, request):
		"""
			Get the result (or None) of a transparent redirect given a Django
			Request object.

				>>> result = MyForm.get_result(request)
				>>> if result.is_success:
						take_some_action()

			This method uses the request.META["QUERY_STRING"] parameter to get
			the HTTP query string.
		"""
		try:
			result = TransparentRedirect.confirm(request.META["QUERY_STRING"])
		except (KeyError, NotFoundError):
			result = None

		return result

	def __init__(self, user, practice_group, *args, **kwargs):
		"""
		Takes in a user to figure out whether a vault id exists or not etc.
		
		@post_to_update: if set to True, then form contents are meant to be posted to Braintree, otherwise its implied
		this form is meant for rendering to the user, hence initialize with braintree data (if any).
		"""
		self.__user = user
		self.__practice_group = practice_group

	@classmethod
	def create_VaultAccount(self, vault_id):
		"""
		Takes in a user to figure out whether a vault id exists or not etc.
		
		@post_to_update: if set to True, then form contents are meant to be posted to Braintree, otherwise its implied
		this form is meant for rendering to the user, hence initialize with braintree data (if any).
		"""
		UserVault.objects.create(user=self.__user, vault_id=vault_id)
		account = Account.objects.create(practice_group_new=self.__practice_group, owner=self.__user, status=Account.ACTIVE_STATUS)

#internal accounting find customer form
class FindCustomerForm(forms.Form):
	practice_group_name = forms.ChoiceField()
	
	def clean(self):
		cleaned_data = self.cleaned_data
		return cleaned_data

	def __init__(self,*args,**kwrds):
		super(FindCustomerForm,self).__init__(*args,**kwrds)
		accounts = Account.objects.all()
		choice_customer = [(account.id, ' '.join([account.practice_group_new.description])) for account in accounts]
		self.fields['practice_group_name'].choices = choice_customer
		
#internal accounting create debit/credit customer form
ENTRY_CHOICES = (
    ('4', 'Charge Customer'),
    ('5', 'Credit Customer'),
)
class ManualTransactionForm(forms.Form):
	practice_group_name = forms.ChoiceField()
	type_choice_field = forms.ChoiceField(choices=ENTRY_CHOICES, label = 'Transaction Type')
	amount = forms.DecimalField(required=True, label = 'Amount, do NOT enter $ - or +')
	memo = forms.CharField(widget=forms.TextInput(attrs={'size':'80','minlength':'1','maxlength':'200'}))
	

	def __init__(self,*args,**kwrds):
		super(ManualTransactionForm,self).__init__(*args,**kwrds)
		accounts = Account.objects.all()
		choice_customer = [(account.id, ' '.join([account.practice_group_new.description])) for account in accounts]
		self.fields['practice_group_name'].choices = choice_customer	

#OLD s2s form		
class UserCCDetailsForm(forms.Form):
	__MONTH_CHOICES = (
		(1, 'January'),
		(2, 'February'),
		(3, 'March'),
		(4, 'April'),
		(5, 'May'),
		(6, 'June'),
		(7, 'July'),
		(8, 'August'),
		(9, 'September'),
		(10, 'October'),
		(11, 'November'),
		(12, 'December'),
	)

	__YEAR_CHOICES = (

		(2012, '2012'),
		(2013, '2013'),
		(2014, '2014'),
		(2015, '2015'),
		(2016, '2016'),
		(2017, '2017'),
		(2018, '2018'),
		(2019, '2019'),
		(2020, '2020'),
		(2021, '2021'),
		(2022, '2022'),
	)
	name = forms.CharField(max_length=64, label='Name as on card')

	cc_number = forms.CharField(max_length=16, label='Credit Card Number')
	expiration_month = forms.ChoiceField(choices=__MONTH_CHOICES)
	expiration_year = forms.ChoiceField(choices=__YEAR_CHOICES)

	zip_code = forms.CharField(max_length=8, label='Zip Code')
	cvv = forms.CharField(max_length=4, label='CVV')

	#tr_data = forms.CharField(widget=forms.HiddenInput)

	def __init__(self, user, practice_group, post_to_update=False, *args, **kwargs):
		"""
		Takes in a user to figure out whether a vault id exists or not etc.
		
		@post_to_update: if set to True, then form contents are meant to be posted to Braintree, otherwise its implied
		this form is meant for rendering to the user, hence initialize with braintree data (if any).
		"""
		self.__user = user
		self.__user_vault = UserVault.objects.get_user_vault_instance_or_none(user)
		self.__practice_group = practice_group

		if not post_to_update and self.__user_vault and not args:
			logging.debug('Looking up payment info for vault_id: %s' % self.__user_vault.vault_id)

			try:
				response = Customer.find(self.__user_vault.vault_id)
				info = response.credit_cards[0]

				initial = {
					'name': info.cardholder_name,
					'cc_number': info.masked_number,
					'expiration_month': int(info.expiration_month),
					'expiration_year': info.expiration_year,
					'zip_code': info.billing_address.postal_code,
				}
				super(UserCCDetailsForm, self).__init__(initial=initial, *args, **kwargs)
			except Exception, e:
				logging.error('Was not able to get customer from vault. %s' % e)
				super(UserCCDetailsForm, self).__init__(initial={'name': '%s %s' % (user.first_name, user.last_name)},
					*args, **kwargs)
		else:
			super(UserCCDetailsForm, self).__init__(initial={'name': '%s %s' % (user.first_name, user.last_name)},
				*args, **kwargs)

	def clean(self):
		today = datetime.today()
		exp_month = int(self.cleaned_data['expiration_month'])
		exp_year = int(int(self.cleaned_data['expiration_year']))

		if exp_year < today.year or (exp_month <= today.month and exp_year <= today.year):
			raise forms.ValidationError('Please make sure your Credit Card expires in the future.')

		return self.cleaned_data

	def save(self, request, prepend_vault_id=''):
		"""
		Adds or updates a users CC to the vault.
		
		@prepend_vault_id: any string to prepend all vault id's with in case the same braintree account is used by
		multiple projects/apps.
		"""
		assert self.is_valid()

		cc_details_map = {	# cc details
			'number': self.cleaned_data['cc_number'],
			'cardholder_name': self.cleaned_data['name'],
			'expiration_date': '%s/%s' % \
				(self.cleaned_data['expiration_month'], self.cleaned_data['expiration_year']),
			'cvv': self.cleaned_data['cvv'],
			'billing_address': {
				'postal_code': self.cleaned_data['zip_code'],
			}
		}

		if self.__user_vault:
			try:
				# get customer info, its credit card and then update that credit card
				response = Customer.find(self.__user_vault.vault_id)
				cc_info = response.credit_cards[0]
				return CreditCard.update(cc_info.token, params=cc_details_map)
			except Exception, e:
				logging.error('Was not able to get customer from vault. %s' % e)
				self.__user_vault.delete()  # delete the stale instance from our db


	#	respone = TransparentRedirect.confirm(request.META["QUERY_STRING"])

	#	respone = Customer.create({	# creating a customer, but we really just want to store their CC details
	#		'id': new_customer_vault_id,   # vault id, uniquely identifies customer. We're not caring about tokens (used for storing multiple CC's per user)
	#		'credit_card': cc_details_map,
	#		'company' : self.__practice_group.description
	#			#add more vault feidls such as name, company etc
	#	})

		if respone.is_success:  # save a new UserVault instance
			UserVault.objects.create(user=self.__user, vault_id=new_customer_vault_id)
			account = Account.objects.create(practice_group=self.__practice_group, owner=self.__user, status=Account.ACTIVE_STATUS)


		return respone



class ProductsForm(forms.Form):
	def __init__(self, product_list, *args, **kwargs):
		super(ProductsForm, self).__init__(*args, **kwargs)
		for product in product_list:
			self.fields[product.name] = forms.BooleanField(label=product.description, initial=product.active, required=False)
			self.fields[product.name].price = product.flat_rate + product.step_cost * product.step
