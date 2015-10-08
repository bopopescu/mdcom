"""
This file contains test for all model functions.

"""
import time
import datetime
import unittest
from mock import patch
from decimal import Decimal
from django_braintree.models import UserVault, PaymentLog
from django_braintree.utils import Charge

from MHLogin.MHLPractices.models import PracticeLocation, \
	OrganizationRelationship
from MHLogin.genbilling.models import Account, Subscription, AccountTransaction, \
	FailedTransaction, Invoice, hasActiveSubscription
from MHLogin.MHLUsers.models import MHLUser, OfficeStaff, Office_Manager
from MHLogin.MHLUsers.Sales.models import Products
from MHLogin.genbilling.signals import credit_card_error, invoice_sent


class GenBillingUnitTest(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		PracticeLocation.objects.all().delete()

		# practice group
		cls.practice_group_new = PracticeLocation(practice_name="test Group", 
			practice_lat=1000, practice_longit=1000)
		cls.practice_group_new.save()

		# practice location
		cls.practice_location = PracticeLocation(practice_name="test1", 
			practice_lat=1000, practice_longit=1000)
		cls.practice_location.save()

		OrganizationRelationship.objects.create(organization=cls.practice_location, 
			parent=cls.practice_group_new, create_time=int(time.time()))

		# location without group
		cls.old_style_practice_location = PracticeLocation(practice_name="test2", 
			practice_lat=1001, practice_longit=1000)
		cls.old_style_practice_location.save()
		# user
		user = MHLUser(username="tester123", first_name="bill", last_name="test")
		user.is_active = user.is_staff = user.tos_accepted = True
		user.set_password("demo")
		user.save()
		# user 2
		cls.user_alt = MHLUser(username="alt123", first_name="will", last_name="test")
		cls.user_alt.is_active = cls.user_alt.is_staff = cls.user_alt.tos_accepted = True
		cls.user_alt.set_password("demo")
		cls.user_alt.save()
		# make him office staff first
		cls.officestaff = OfficeStaff(user=user, current_practice=cls.practice_location)
		cls.officestaff.save()
		cls.officestaff.practices.add(cls.practice_location)
		# make him office manager
		cls.office_manager = Office_Manager(user=cls.officestaff, 
			practice=cls.practice_location, manager_role=2)
		cls.office_manager.save()
		# products
		p1 = Products(description="Answering Service Active", code="ANS", price="75")
		p1.save()
		p2 = Products(description="File Sharing Prorated", code="FSP", price="100")
		p2.save()
		p3 = Products(description="Old Product Inactive", code="OP", price="14.95")
		p3.save()
		p4 = Products(description="Future Product See Date", code="FP", price="25.95")
		p4.save()
		p5 = Products(description="Future Product NOT subscribed", code="FPNS", price="1.00")
		p5.save()
		# subscription - at this point manual, we will create add product function later on
		now = datetime.datetime(2011, 12, 1, 9, 30, 45)
		Subscription(practice_group_new=cls.practice_group_new, product=p1, 
			practice_location=cls.practice_location, is_active=True, price="75", start_date=now).save()
		Subscription(practice_group_new=cls.practice_group_new, 
			product=p3, is_active=False, price="14.95", start_date=now).save()
		now = datetime.datetime(2012, 5, 29, 10, 00, 00)
		Subscription(practice_group_new=cls.practice_group_new, product=p2, 
			is_active=True, price="38.75", start_date=now).save()
		now = datetime.datetime(2012, 7, 1, 10, 00, 00)
		s = Subscription(practice_group_new=cls.practice_group_new, product=p4, 
			is_active=True, price="29.95", start_date=now)
		s.save()
		s.__unicode__()

	@classmethod
	def tearDownClass(cls):
		MHLUser.objects.all().delete()
		Office_Manager.objects.all().delete()
		PracticeLocation.objects.all().delete()
		OrganizationRelationship.objects.all().delete()
		Subscription.objects.all().delete()
		Products.objects.all().delete()

	def setUp(self):
		# for each test, create new account, default status is trial, 
		# individual tests will update to desired status
		self.account = Account(practice_group_new=self.practice_group_new, owner=self.officestaff.user)
		self.account.save()
		self.uservault = UserVault(user=self.officestaff.user, vault_id="1")
		self.uservault.save()

	def tearDown(self):
		# after each test delete account and all detail accounting entries
		FailedTransaction.objects.all().delete()
		Invoice.objects.all().delete()
		AccountTransaction.objects.all().delete()
		self.account.delete()
		self.uservault.delete()

	@patch.object(invoice_sent, 'send')
	@patch.object(UserVault, 'charge')
	def test_account_active(self, my_charge_call, my_invoice_send):
		"""this test is for account in good standing that is active
				will calculate charges based on 4 subscriptions (active, not active, pro-rated, future)
				will create invoice - createInvoice
				will create payment (mock braintree call) - chargeInvoice
			run thru 2 invoice cycles
		"""
		# make account active
		self.account.status = Account.ACTIVE_STATUS
		self.account.save()
		self.assertEqual(True, self.account.access_granted())
		self.account.__unicode__()

		# create invoice for 201206
		self.account.createInvoice(201206, 201207)
		# issue/2030 Django w/MySQL does not store milliseonds in datetime fields, 
		# ensure transaction dates different than 2nd invoice by backing up 1 second
		for at in AccountTransaction.objects.all():
			at.created_on -= datetime.timedelta(seconds=1)
			at.save()
		# check if charges for this month and invoice are created properly:
		self.assertTrue(AccountTransaction.objects.all().count() == 3)  # two charges and one invoice

		invoice_tx = AccountTransaction.objects.get(account=self.account, tx_type="0", 
			period_start="201206", period_end="201207")
		invoice_tx.__unicode__()
		invoice = Invoice.objects.get()
		invoice.__unicode__()
		# invoice for 06-01 total
		self.assertEqual(Decimal("117.50"), invoice_tx.amount)
		self.assertTrue(invoice.paid == False)

		# call create invoice again, it should NOT do it!
		self.account.createInvoice(201206, 201207)

		# check if charges for this month and invoice are created properly:
		self.assertTrue(AccountTransaction.objects.all().count() == 3)  # two charges and one invoice

		invoice_tx = AccountTransaction.objects.get(account=self.account, tx_type="0", 
			period_start="201206", period_end="201207")
		invoice = Invoice.objects.get(accounttransaction=invoice_tx.id)
		# invoice for 06-01 total
		self.assertEqual(Decimal("117.50"), invoice_tx.amount)
		self.assertTrue(invoice.paid == False)

		# now we going to mock actual charge to brain tree but test all db updates as 
		# if charge went thru ok.
		# create local payment log
		payment_log = PaymentLog.objects.create(user=self.officestaff.user, 
			amount=Decimal("117.50"), transaction_id="unittest")

		# mock charge, its object returned by brain tree, point to payment log, has status
		charge = Charge()
		charge.amount = Decimal("117.50")
		charge.is_success = True
		charge.payment_log = payment_log

		# mock messaging to user notifying of payment processed
		my_invoice_send.return_value = True
		my_charge_call.return_value = charge

		# actual charge of invoice (BT call mocked)
		self.account.chargeInvoice(201206)

		# check results
		self.assertTrue(AccountTransaction.objects.all().count() == 4)  # two charges + invoice + payment
		payment_tx = AccountTransaction.objects.get(account=self.account, 
			tx_type="1", period_start="201206", period_end="201207")
		self.assertEqual(Decimal("117.50"), payment_tx.amount)
		invoice = Invoice.objects.get(accounttransaction=invoice_tx.id)
		self.assertTrue(invoice.paid == True)

		# call charge invoice again, but since it is PAID, should not do anything.
		self.account.chargeInvoice(201206)

		# check results
		self.assertTrue(AccountTransaction.objects.all().count() == 4)  # two charges + invoice + payment
		# second invoice cycle, just invoice, not need to mock payment again.

		self.account.createInvoice(201207, 201208)

		# check if charges for this month and invoice are created properly:
		self.assertTrue(AccountTransaction.objects.all().count() == 8)
		# 3 charges, 1 invoice, 4 tx for prev period

		invoice_tx = AccountTransaction.objects.get(account=self.account, tx_type="0", 
			period_start="201207", period_end="201208")
		invoice = Invoice.objects.get(accounttransaction=invoice_tx.id)
		# invoice for 07-01 total
		self.assertEqual(Decimal("143.70"), invoice_tx.amount)
		self.assertTrue(invoice.paid == False)

	@patch.object(credit_card_error, 'send')
	@patch.object(UserVault, 'charge')
	def test_account_active_BTfail(self, my_charge_call, my_error_send):
		"""this test is for account in good standing that is active that get credit 
			card payment rejected by BT
				will calculate charges based on 4 subscriptions (active, not active, 
				pro-rated, future)
				will create invoice - createInvoice
				will create failed payment (mock braintree call) - chargeInvoice
			run thru 2 invoice cycles
				second cycle should add two month charge charges together into ONE invoce.
		"""
		# make account active
		self.account.status = Account.ACTIVE_STATUS
		self.account.save()
		self.assertEqual(True, self.account.access_granted())

		# create invoice for 201206
		self.account.createInvoice(201206, 201207)
		# issue/2030 Django w/MySQL does not store milliseonds in datetime fields, 
		# ensure transaction dates different than 2nd invoice by backing up 1 second
		for at in AccountTransaction.objects.all():
			at.created_on -= datetime.timedelta(seconds=1)
			at.save()
		# check if charges for this month and invoice are created properly:
		self.assertTrue(AccountTransaction.objects.all().count() == 3)  # two charges and one invoice

		invoice_tx = AccountTransaction.objects.get(account=self.account, tx_type="0", 
			period_start="201206", period_end="201207")
		invoice = Invoice.objects.get(accounttransaction=invoice_tx.id)
		# invoice for 06-01 total
		self.assertEqual(Decimal("117.50"), invoice_tx.amount)
		self.assertTrue(invoice.paid == False)

		# now we going to mock actual charge to brain tree but test 
		# all db updates as if charge was rejected by BT.

		# mock charge, its object returned by brain tree, point to payment log, has status
		charge = Charge()
		charge.amount = Decimal("117.50")
		charge.is_success = False

		# mock messaging to user notifying of payment processed
		my_error_send.return_value = True

		my_charge_call.return_value = charge

		# actual charge of invoice (BT call mocked)
		self.account.chargeInvoice(201206)

		# check results
		self.assertTrue(AccountTransaction.objects.all().count() == 3)  
		# two charges + invoice + NO payment
		invoice = Invoice.objects.get(accounttransaction=invoice_tx.id)
		self.assertTrue(invoice.paid == False)
		failed_tx = FailedTransaction.objects.get(accounttransaction=invoice_tx.id)
		failed_tx.__unicode__()

		# second invoice cycle, just invoice, not need to mock payment again.
		self.account.createInvoice(201207, 201208)

		# check if charges for this month and invoice are created properly:
		self.assertTrue(AccountTransaction.objects.all().count() == 7)  
		# 3 charges, 1 invoice, 3 tx for prev period

		invoice_tx = AccountTransaction.objects.get(account=self.account, 
			tx_type="0", period_start="201207", period_end="201208")
		invoice = Invoice.objects.get(accounttransaction=invoice_tx.id)
		# invoice for 07-01 total
		self.assertEqual(Decimal("261.20"), invoice_tx.amount)
		self.assertTrue(invoice.paid == False)

	@patch.object(credit_card_error, 'send')
	def test_account_active_Vault_fail(self, my_error_send):
		"""this test is for account in good standing that is active but has NO credit card 
			associated with it
				will calculate charges based on 4 subscriptions (active, not active, 
				pro-rated, future)
				will create invoice - createInvoice
				will create failed payment (no attempt to call braintree call, 
				since no Vault present) - chargeInvoice
			run thru 1 invoice cycle to test no vault condition
		"""
		# make account active
		self.account.status = Account.ACTIVE_STATUS
		self.account.save()
		self.assertEqual(True, self.account.access_granted())

		# make user have no vault
		self.uservault.user = self.user_alt
		self.uservault.save()

		# create invoice for 201206
		self.account.createInvoice(201206, 201207)

		# check if charges for this month and invoice are created properly:
		self.assertTrue(AccountTransaction.objects.all().count() == 3)  # two charges and one invoice

		invoice_tx = AccountTransaction.objects.get(account=self.account, tx_type="0", 
			period_start="201206", period_end="201207")
		invoice = Invoice.objects.get(accounttransaction=invoice_tx.id)
		# invoice for 06-01 total
		self.assertEqual(Decimal("117.50"), invoice_tx.amount)
		self.assertTrue(invoice.paid == False)

		# mock messaging to user notifying of payment failing
		my_error_send.return_value = True

		# actual charge of invoice (BT call mocked)
		self.account.chargeInvoice(201206)

		# check results
		self.assertTrue(AccountTransaction.objects.all().count() == 3)  
		# two charges + invoice + NO payment
		invoice = Invoice.objects.get(accounttransaction=invoice_tx.id)
		self.assertTrue(invoice.paid == False)

	def test_account_inactive(self):
		"""this test is for account that is marked inactive
				4 subscriptions (active, not active, pro-rated, future) exists
				will call create invoice - createInvoice (should create NONE)
				will charge Invoice that should NOT attempt to call braintree call, since no Invoice
			run thru 1 invoice cycle to test inactive account condition
		"""
		# make account active
		self.account.status = Account.TRIAL_STATUS
		self.account.save()
		self.assertEqual(True, self.account.access_granted())
		self.assertEqual(False, self.account.billable())

		# create invoice for 201206
		self.account.createInvoice(201206, 201207)

		# actual charge of invoice (BT call mocked)
		self.account.chargeInvoice(201206)

		# check results
		self.assertTrue(AccountTransaction.objects.all().count() == 0)  
		# two charges + invoice + NO payment

	def test_account_active_no_active_subscriptions(self):
		"""this test is for account in good standing that is active
				will calculate charges based on 4 subscriptions (active, 
				not active, pro-rated, future)
				will create invoice - createInvoice
				will create payment (mock braintree call) - chargeInvoice
			run thru 2 invoice cycles
		"""
		# make account active
		self.account.status = Account.ACTIVE_STATUS
		self.account.save()
		self.assertEqual(True, self.account.access_granted())

		# create invoice for 2011-06
		self.account.createInvoice(201106, 201107)

		# check if charges for this month and invoice are created properly:
		self.assertTrue(AccountTransaction.objects.all().count() == 1)  # 1 invoice only
		invoice_tx = AccountTransaction.objects.get(account=self.account, tx_type="0", 
			period_start="201106", period_end="201107")
		invoice = Invoice.objects.get(accounttransaction=invoice_tx.id)
		# invoice for 06-01 total
		self.assertEqual(Decimal("0"), invoice_tx.amount)
		self.assertTrue(invoice.paid == False)

		self.account.chargeInvoice(201106)
		self.assertTrue(AccountTransaction.objects.all().count() == 1)  # 1 invoice only

	def test_invoice_before_dispatch(self):
		"""this test is for account in good standing that is active
				will calculate charges based on 4 subscriptions (active, not active, pro-rated, future)
				will create invoice - createInvoice
				will create payment (mock braintree call) - chargeInvoice
			run thru 2 invoice cycles
		"""
		# make account active
		self.account.status = Account.ACTIVE_STATUS
		self.account.save()
		self.assertEqual(True, self.account.access_granted())

		# charge invoice for 2011-12, note invoice NOT created yet
		self.account.chargeInvoice(201112)
		self.assertTrue(AccountTransaction.objects.all().count() == 0)  
		# nothing created, no charges means, no invoice, no payment

	def test_practiceHasActiveSubscription(self):
		"""this test is for helper function that checks if practice location has active subscription 
		"""
		pOne_lOne = hasActiveSubscription(self.practice_location, "ANS")
		self.assertEqual(True, pOne_lOne)

		pTwo_lOne = hasActiveSubscription(self.practice_location, "FSP")
		self.assertEqual(True, pTwo_lOne)

		pThree_lOne = hasActiveSubscription(self.practice_location, "OP")
		self.assertEqual(False, pThree_lOne)

		pOne_lTwo = hasActiveSubscription(self.old_style_practice_location, "ANS")
		self.assertEqual(True, pOne_lTwo)

		pX_lOne = hasActiveSubscription(self.practice_location, "ANS_TWO")
		self.assertEqual(True, pX_lOne)

		pFive_lOne = hasActiveSubscription(self.practice_location, "FPNS")
		self.assertEqual(False, pFive_lOne)

		pFive_lTwo = hasActiveSubscription(self.old_style_practice_location, "FPNS")
		self.assertEqual(True, pFive_lTwo)
