
import collections
import logging

from datetime import datetime
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.db import models
from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch import receiver

from MHLogin.utils.mh_logging import get_standard_logger
from MHLogin.MHLUsers.models import MHLUser

# Setting up logging
logger = get_standard_logger('%s/MHLUsers/Sales/models.log' % (settings.LOGGING_ROOT),
							'MHLUser.Sales.models', logging.WARN)


class Products(models.Model):
	""" Description and standard starting price of all DoctorCom products """
	description = models.CharField(max_length=255, blank=True)
	code = models.CharField(max_length=64, blank=True, unique=True)
	price = models.DecimalField(max_digits=20, decimal_places=2)

	class Meta:
		verbose_name_plural = "Products"

	def __unicode__(self):
		return "%s %s $%s" % (self.description, self.code, self.price)

# list of possible sources - freeform, user can edit for other
SALES_SOURCE = (
	"Web search", 
	"Colleague",
	"Conference",
	"Reseller/Partner", 
	"other...",
	)

# format: code: (code_value, description), ...
SALES_STAGES = sorted({
	'prod': (120, '120 - Production'),
	'onboarding': (110, '110 - Onboarding'),
	'closedwon': (100, '100 - Closed Won'),
	'incontract': (90, '90 - In Contract'),
	'evalrcmd': (70, '70 - Eval/Rcmd OK'),
	'evalsched': (60, '60 - Evaluation Schd'),
	'demo': (50, '50 - Demoed'),
	'compcfmd': (40, '40 - Comp Cfmd'),
	'bant': (30, '30 - BANT'),
	'discovery': (10, '10 - Discovery'),
	'closed': (0, '0 - Closed Lost'),
	}.items(), key=lambda item: item[1][0])  # sorted by code_value

try:
	SALES_STAGES = collections.OrderedDict(SALES_STAGES)
except AttributeError:  # older pythons<2.7 try import external ordereddict package
	import ordereddict  # pip install ordereddict if not found
	SALES_STAGES = ordereddict.OrderedDict(SALES_STAGES)


class SalesLeads(models.Model):
	"""Sales leads table

	Contains all details pertaining to a sales lead.  
	"""
	practice = models.CharField(max_length=255, blank=True)
	region = models.CharField(max_length=64, blank=True)
	salestype = models.CharField(max_length=64, blank=True)
	price = models.DecimalField(max_digits=20, decimal_places=2)
	contact = models.CharField(max_length=255, blank=True)
	phone = models.CharField(max_length=64, blank=True)
	email = models.CharField(max_length=64, blank=True)
	website = models.CharField(max_length=255, blank=True)
	date_contact = models.DateField(default=datetime.now)
	date_appt = models.DateField(default=datetime.now)
	stage = models.CharField(max_length=64, default='discovery', 
		choices=((k, v[1]) for k, v in SALES_STAGES.items()))
	source = models.CharField(max_length=64, blank=True)
	notes = models.TextField()
	address = models.TextField()
	rep = models.ForeignKey(MHLUser, null=True, blank=True, related_name='rep_salesleads')

	date_of_billing = models.DateField(null=True, blank=True,
		verbose_name="Date when this lead went to billing.")
	date_of_training = models.DateField(null=True, blank=True,
		verbose_name="Date when this lead went to training.")

	__unicode__ = lambda self: "%s, rep: %s" % (self.practice, self.rep)

	class Meta:
		verbose_name_plural = "Salesleads"


class SalesProduct(models.Model):
	""" Sales product(s) per sales lead """
	is_active = models.BooleanField(default=False)
	lead = models.ForeignKey(SalesLeads, null=True, blank=True,
						related_name='lead_salesproduct')
	product = models.ForeignKey(Products, null=True, blank=True,
						related_name='product_salesproduct')
	quoted_price = models.DecimalField(max_digits=20, decimal_places=2)


""" The following are signals to keep all Sales Tables in sync """


@receiver(post_save, sender=SalesLeads)
def post_create_salesleads_callback(sender, **kwargs):
	""" Callback after a sales lead is created, now create his/her sales products """
	if kwargs['created'] == True:
		# get new sales lead instance
		sl = kwargs['instance']
		# create sales products for this sales lead
		for p in Products.objects.all():
			sp = SalesProduct()
			sp.is_active = False
			sp.lead = sl
			sp.product = p
			sp.quoted_price = p.price
			sp.save()


@receiver(pre_delete, sender=SalesLeads)
def pre_delete_salesleads_callback(sender, **kwargs):
	""" Callback before a sales lead is deleted, also remove their sales products """
	# delete sales products associated with this lead
	sl = kwargs['instance']
	prods = SalesProduct.objects.filter(lead=sl.id)
	prods.delete()


@receiver(pre_save, sender=SalesLeads)
def pre_save_salesleads_callback(sender, **kwargs):
	""" Called before a sales lead is saved, update date_of_billing if state goes to paying """
	try:
		sl_ram = kwargs['instance']
		sl_db = SalesLeads.objects.get(id=sl_ram.id)

		# check if stage has changed
		if (sl_db.stage != sl_ram.stage):
			sl_ram.date_of_billing = datetime.now() if (sl_ram.stage == "production") else None
			sl_ram.date_of_training = datetime.now() if (sl_ram.stage == "onboarding") else None

	except ObjectDoesNotExist:
		# handle case when creating, Django 1.3 pre_save signals have no 'created' in kwargs
		sl_ram.date_of_billing = datetime.now() if (sl_ram.stage == "production") else None
		sl_ram.date_of_training = datetime.now() if (sl_ram.stage == "onboarding") else None


@receiver(post_save, sender=Products)
def post_create_products_callback(sender, **kwargs):
	""" Callback new product created, notify SalesLead objects of new product """
	if kwargs['created'] == True:
		# get new sales lead instance
		product = kwargs['instance']
		for sl in SalesLeads.objects.all():
			# create new sales product for this lead
			sp = SalesProduct()
			sp.is_active = False
			sp.lead = sl
			sp.product = product
			sp.quoted_price = product.price
			sp.save()


@receiver(pre_delete, sender=Products)
def pre_delete_products_callback(sender, **kwargs):
	""" Callback before sales product is deleted, notify Sales Leads of removed product """
	# delete sales products associated with this lead
	p = kwargs['instance']
	prods = SalesProduct.objects.filter(product=p.id)
	prods.delete()
	# update existing sales lead object's price
	for sl in SalesLeads.objects.all():
		sales_setLeadPrice(sl)


@receiver(post_save, sender=SalesProduct)
def post_save_salesproduct_callback(sender, **kwargs):
	""" Callback after a SalesProduct was saved/modified - update SalesLead total price """
	if kwargs['created'] == False:
		sp = kwargs['instance']
		# only processing saves not creates
		sales_setLeadPrice(SalesLeads.objects.get(id=sp.lead_id))


# helper to set sales lead price
def sales_setLeadPrice(sl):
	price = 0
	# add up the prices
	for p in SalesProduct.objects.filter(lead=sl.id):
		if (p.is_active == True):
			price += p.quoted_price

	sl.price = price
	sl.save()

