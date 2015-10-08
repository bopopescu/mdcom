
import json
import unittest
import decimal
import urlparse
#import pyttsx
from datetime import date

from django.test.client import Client
from django.conf import settings
from django.core.urlresolvers import reverse

from MHLogin.utils.mh_logging import get_standard_logger
from MHLogin.Invites.models import Invitation
from MHLogin.MHLUsers.models import MHLUser, Salesperson, Administrator, Provider
from MHLogin.MHLUsers.Sales.models import SalesLeads, SalesProduct, Products
from MHLogin.utils.tests import create_user

# Setting up logging
logger = get_standard_logger('%s/MHLUsers/Sales/tests.log' % (settings.LOGGING_ROOT),
							'MHLUser.Sales.tests', settings.LOGGING_LEVEL)


class SalesUnitTest(unittest.TestCase):
	""" Sales unittester for creating Salesperson, Salse Products, Sales Leads
		and verifying everything stays in sync with no errors or failures
	"""

	def setUp(self):
		SalesLeads.objects.all().delete()
		MHLUser.objects.all().delete()
		Administrator.objects.all().delete()
		Provider.objects.all().delete()
		Products.objects.all().delete()

		self.salesperson = create_user("bblazejowsky", "bill", "blazejowsky", "demo",
							"Ocean Avenue", "Carmel", "CA", "93921", uklass=Salesperson)
		self.admin = create_user("sduper", "super", "duper", "demo",
							"Ocean Avenue", "Carmel", "CA", "93921", uklass=Administrator)
		self.provider = create_user("hmeister", "heal", "meister", "demo",
							"555 Bryant St.", "Palo Alto", "CA", "", uklass=Provider)

		Products(description="Fancie smansie product", code="fsm", price="29.95").save()
		Products(description="Generic Shampoo", code="gsham", price="9.95").save()
		Products(description="Bicycle Tires", code="bt", price="14.95").save()

	def tearDown(self):
		SalesLeads.objects.all().delete()
		MHLUser.objects.all().delete()
		Administrator.objects.all().delete()
		Provider.objects.all().delete()
		Products.objects.all().delete()
		self.assertTrue(Products.objects.all().count() == 0)
		self.assertTrue(SalesProduct.objects.all().count() == 0)

	def test_sales_products(self):
		# create a new Sales Lead, verify it created associated sales products
		sl = SalesLeads(practice="London Dentistry", rep=self.salesperson.user, price="0.00")
		self.assertTrue(SalesProduct.objects.filter(lead=sl).count() == 0,
					"Sales Products should be empty before save")
		sl.save()
		sps = SalesProduct.objects.filter(lead=sl)
		# verify backend created associated sales products
		self.assertTrue(sps.count() == Products.objects.all().count(),
					""""Sales products created for this sales lead should equal
					the number of products we have in our system""")

	def test_sales_products_price(self):
		# create a new Sales Lead, verify it created associated sales products
		sl = SalesLeads(practice="Belfast Liver Dispensary", rep=self.salesperson.user, price="0.00")
		sl.save()
		sps = SalesProduct.objects.filter(lead=sl)

		# test sales leads price updates when we change products for them
		total = 0
		for sp in sps:
			sp.is_active = True
			sp.quoted_price = sp.product.price
			total += sp.quoted_price
			sp.save()

		# reload, verify price quote for SalesLeads matches the sum of sales products prices
		sl = SalesLeads.objects.get(id=sl.id)
		self.assertTrue(sl.price == total, "prices should match %d, %d" % (sl.price, total))

	def test_product_added_and_updated(self):
		# create a Sales Lead
		SalesLeads(practice="Florida Gator Rehabilitation", rep=self.salesperson.user, price="50.00").save()
		# create a new product and verify SalesLead(s) were updated
		Products(description="Retro Encabulator", code="re", price="2500.00").save()
		# verify SalesLeads matching number of SalesProducts to Products
		for sl in SalesLeads.objects.all():
			sps = SalesProduct.objects.filter(lead=sl)
			self.assertTrue(sps.count() == Products.objects.all().count())

	def test_saleslead_product_update(self):
		# create new SalesLeads
		sl = SalesLeads(practice="Manhattan Heart Transplants", rep=self.salesperson.user, price="0.00")
		sl.save()
		sps = SalesProduct.objects.filter(lead=sl)
		# verify at least one salesproduct present
		self.assertTrue(sps.count() > 0)
		sp = sps[0]
		# add 10.99 to a product and verify total price in sales leads reflects change
		orig_total = sp.quoted_price
		added_price = 10.99

		# add price to first salesproduct and verify SalesLead total was updated
		sp.quoted_price += decimal.Decimal(str(added_price))
		# set active to true so SalesLeads price is updated
		sp.is_active = True
		sp.save()
		# refresh from db
		sp = SalesProduct.objects.get(id=sp.id)
		sl = SalesLeads.objects.get(id=sl.id)
		# test prices match
		self.assertTrue(sl.price == orig_total + decimal.Decimal(str(added_price)))

	def test_sales_date_of_billing(self):
		# change Sales Lead to billing and verify date of billing
		today = date.today()
		sl = SalesLeads(practice="SF Mental Health Clinic", rep=self.salesperson.user, price="0.00")
		sl.stage = "production"
		sl.save()
		# verify date not equal, date_of_billing resolution is days
		self.assertTrue(sl.date_of_billing != today)
		# refresh
		sl = SalesLeads.objects.get(id=sl.id)
		sl.status = "Paying"
		sl.save()
		# refresh
		sl = SalesLeads.objects.get(id=sl.id)

		# check if date is equal, date_of_billing resolution is days
		self.assertTrue(sl.date_of_billing == today)

	def test_sales_get_user_list_view(self):
		c = Client()
		# after successful login should get re-direct to /
		response = c.post('/login/', {'username': self.salesperson.user.username,
									'password': 'demo'})
		self.assertEqual(response.status_code, 302)
		# verify we are logged in
		self.assertEqual(c.session['_auth_user_id'], self.salesperson.user.pk)
		# now we redirect ourselves to user's default homepage, in this case /Sales
		response = c.get(response['location'])
		# should get 302
		self.assertEqual(response.status_code, 302)
		# should get /Sales
		sales_path = urlparse.urlparse(response['location']).path
		self.assertEqual(sales_path, "/Sales/")
		# we are at Sales Home page!  Now try and get sales_getuser_list view
		response = c.get(response['location'] + 'sales_getuser_list/')
		# should get 200
		self.assertEqual(response.status_code, 200)
		# convert to python list, should count 2, Provider should not be in list
		user_list = json.loads(response.content)
		self.assertEqual(len(user_list), 2)
		# sales person should be a list with id, first_name, last_name
		sales_guy = user_list[0]
		self.assertEqual(sales_guy[0], self.salesperson.user.id, "userids don't match")
		# now logout, we can alternatively call c.post('/logout/')
		response = c.logout()
		self.assertFalse('_auth_user_id' in c.session)

	def test_sales_product_removal(self):
		# create a Sales Lead
		sl = SalesLeads(practice="Primate Anesthesiology", rep=self.salesperson.user, price="150.00")
		sl.save()

		sps = SalesProduct.objects.filter(lead=sl)

		# test sales leads price updates when we change products for them
		total = 0
		for sp in sps:
			sp.is_active = True
			sp.quoted_price = sp.product.price
			total += sp.quoted_price
			sp.save()

		# reload, verify price quote for SalesLeads matches the sum of sales products prices
		sl = SalesLeads.objects.get(id=sl.id)
		self.assertTrue(sl.price == total, "prices should match %d, %d" % (sl.price, total))

		# now remove one of the products and verify SalesLeads price was updated
		p = Products.objects.get(description="Generic Shampoo")
		price = p.price
		# tickle __unicode__ code for coverage and don't output anything
		"Deleting Product %s" % (p)
		p.delete()

		# reload and verify SalesLeads price is reflected by removal of Product
		sl = SalesLeads.objects.get(id=sl.id)
		self.assertTrue(sl.price == (total - price),
					"prices should match %d, %d" % (sl.price, total - price))

	def test_sales_get_sales_leads_view(self):
		c = Client()
		# after successful login should get re-direct to /
		response = c.post('/login/', {'username': self.salesperson.user.username,
									'password': 'demo'})
		self.assertEqual(response.status_code, 302)
		# verify we are logged in
		self.assertEqual(c.session['_auth_user_id'], self.salesperson.user.pk)
		# now we redirect ourselves to user's default homepage, in this case /Sales
		response = c.get(response['location'])
		# should get 302
		self.assertEqual(response.status_code, 302)
		# should get /Sales
		sales_path = urlparse.urlparse(response['location']).path
		self.assertEqual(sales_path, "/Sales/")
		# we are at Sales Home page!  Now try and sales leads page
		response = c.get(reverse('MHLogin.MHLUsers.Sales.views.sales_view'))
		# should get 200, OK
		self.assertEqual(response.status_code, 200)
		# now logout, we can alternatively call c.post('/logout/')
		response = c.logout()
		self.assertFalse('_auth_user_id' in c.session)

	def test_sales_get_leads_data(self):
		SalesLeads(practice="Arachnophobia Anonymous", rep=self.salesperson.user,
				price="350.00").save()

		for u in [self.admin, self.salesperson]:
			c = Client()
			# after successful login should get re-direct to /
			response = c.post('/login/', {'username': u.user.username,
										'password': 'demo'})
			self.assertEqual(response.status_code, 302)
			# verify we are logged in
			self.assertEqual(c.session['_auth_user_id'], u.user.pk)
			# now we redirect ourselves to user's default homepage, in this case /Sales
			response = c.get(response['location'])
			# should get 302
			self.assertEqual(response.status_code, 302)
			# we are at user's default home page!  Now try and sales leads page data
			response = c.get(reverse('MHLogin.MHLUsers.Sales.views.sales_getdata'))
			# should get 200, OK
			self.assertEqual(response.status_code, 200, response.status_code)
			# now logout, we can alternatively call c.post('/logout/')
			response = c.logout()
			self.assertFalse('_auth_user_id' in c.session)

	def test_sales_new_invites(self):
		c = Client()
		# after successful login should get re-direct to /
		response = c.post('/login/', {'username': self.admin.user.username,
									'password': 'demo'})
		self.assertEqual(response.status_code, 302)
		# post a new invite with results expect 302 - redirect
		response = c.post(reverse('MHLogin.MHLUsers.Sales.views.new_invites'),
						{'userType': 1, 'emailAddresses': 'doc@mdcom.com'})
		self.assertEqual(response.status_code, 302, response.status_code)
		# go to the dashboard
		response = c.get(reverse('MHLogin.MHLUsers.Sales.views.dashboard'))
		self.assertEqual(response.status_code, 200, response.status_code)
		# resend an invite created by post, no-confirm then confirm
		invs = Invitation.objects.filter(sender=self.admin.user)
		response = c.get(reverse('MHLogin.MHLUsers.Sales.views.resend_invite', 
						kwargs={'invite_pk': invs[0].pk}))
		self.assertEqual(response.status_code, 200, response.status_code)
		response = c.get(reverse('MHLogin.MHLUsers.Sales.views.resend_invite', 
						kwargs={'invite_pk': invs[0].pk}) + '?action=confirm')
		self.assertEqual(response.status_code, 302, response.status_code)
		# cancel invite, no-confirm then with confirm
		response = c.get(reverse('MHLogin.MHLUsers.Sales.views.cancel_invite', 
						kwargs={'invite_pk': invs[0].pk}))
		self.assertEqual(response.status_code, 200, response.status_code)
		response = c.get(reverse('MHLogin.MHLUsers.Sales.views.cancel_invite', 
						kwargs={'invite_pk': invs[0].pk}) + '?action=confirm')
		self.assertEqual(response.status_code, 302, response.status_code)
		response = c.logout()
		self.assertFalse('_auth_user_id' in c.session)

	def test_sales_view_edit(self):
		c = Client()
		# after successful login should get re-direct to /
		response = c.post('/login/', {'username': self.admin.user.username,
									'password': 'demo'})
		self.assertEqual(response.status_code, 302)
		# get main sales profile view
		response = c.get(reverse('MHLogin.MHLUsers.Sales.views.profile'))
		self.assertEqual(response.status_code, 200, response.status_code)
		# edit main sales profile view
		response = c.get(reverse('MHLogin.MHLUsers.Sales.views.profile_edit_sales'))
		self.assertEqual(response.status_code, 200, response.status_code)
		# post edit main sales profile view
		response = c.post(reverse('MHLogin.MHLUsers.Sales.views.profile_edit_sales'))
		self.assertEqual(response.status_code, 200, response.status_code)
		# now with some data and expect redirect
		response = c.post(reverse('MHLogin.MHLUsers.Sales.views.profile_edit_sales'),
			{'first_name': 'joe', 'last_name': 'montana', 'email': 'salesguy@mdcom.com'})
		self.assertEqual(response.status_code, 302, response.status_code)
		response = c.logout()
		self.assertFalse('_auth_user_id' in c.session)

	def test_get_sales_leads_product_data(self):
		sl = SalesLeads.objects.create(practice="Cancer Busters", 
					rep=self.admin.user, price="99.00")
		c = Client()
		# after successful login should get re-direct to /
		response = c.post('/login/', {'username': self.admin.user.username,
									'password': 'demo'})
		self.assertEqual(response.status_code, 302)
		# get product data as admin
		response = c.get(reverse('MHLogin.MHLUsers.Sales.views.sales_getproductdata') +
						'?id=' + str(sl.id))
		self.assertEqual(response.status_code, 200, response.status_code)
		response = c.logout()
		self.assertFalse('_auth_user_id' in c.session)
		c = Client()
		# after successful login should get re-direct to /
		response = c.post('/login/', {'username': self.salesperson.user.username,
									'password': 'demo'})
		self.assertEqual(response.status_code, 302)
		# get product data as regular sales guy who doesn't have permission
		response = c.get(reverse('MHLogin.MHLUsers.Sales.views.sales_getproductdata') +
						'?id=' + str(sl.id))
		self.assertEqual(response.status_code, 200, response.status_code)
		response = c.logout()

	def test_sales_get_regions(self):
		c = Client()
		# after successful login should get re-direct to /
		response = c.post('/login/', {'username': self.admin.user.username,
									'password': 'demo'})
		self.assertEqual(response.status_code, 302)
		response = c.get(reverse('MHLogin.MHLUsers.Sales.views.sales_region_list'))
		self.assertEqual(response.status_code, 200, response.status_code)
		response = c.logout()

	def test_sales_update_data(self):
		sl = SalesLeads.objects.create(practice="Hillbilly Hamstring Repair", 
					rep=self.admin.user, price="121.00", email='bah@mdcom.com')
		c = Client()
		# after successful login should get re-direct to /
		response = c.post('/login/', {'username': self.admin.user.username,
									'password': 'demo'})
		self.assertEqual(response.status_code, 302)
		self.assertTrue(sl.email == 'bah@mdcom.com', sl.email)
		# change the email to something else
		getstr = '&c0=%s&c1=%s&c2=%s&c4=%s&c5=%s&c6=%s&c7=%s&c8=%s&c9=%s&c10=%s'\
			'&c11=%s&c12=%s&c13=%s&c14=%s&c15=%s' % (sl.practice, sl.region,
			sl.salestype, sl.price, sl.contact, sl.phone, 'boo@mdcom.com', sl.website,
			sl.date_contact, sl.date_appt, sl.stage, sl.source, sl.notes,
			sl.address, sl.rep.pk) 
		response = c.get(reverse('MHLogin.MHLUsers.Sales.views.sales_updatedata') +
						'?!nativeeditor_status=updated&gr_id=' + str(sl.id) + getstr)
		self.assertEqual(response.status_code, 200, response.status_code)

		sl = SalesLeads.objects.get(practice="Hillbilly Hamstring Repair", 
					rep=self.admin.user, price="121.00")
		self.assertTrue(sl.email == 'boo@mdcom.com', sl.email)
		# now delete it
		response = c.get(reverse('MHLogin.MHLUsers.Sales.views.sales_updatedata') +
						'?!nativeeditor_status=deleted&gr_id=' + str(sl.id) + getstr)
		self.assertEqual(response.status_code, 200, response.status_code)
		sl = SalesLeads.objects.filter(practice="Hillbilly Hamstring Repair", 
					rep=self.admin.user, price="121.00")
		self.assertTrue(len(sl) == 0, sl)
		response = c.logout()


#	def test_speech_to_text(self):
#		engine = pyttsx.init()
#
#		ii = 0
#		voices = engine.getProperty('voices')
#		for voice in voices:
#			engine.setProperty('voice', voice.id)
#			engine.sayToURL('Welcome to DoctorCom, press 1 if having a heart attack,'\
#				'press 2 if having a seizure, or press 3 to continue.  ',
#				url='file:///Users/dekard/tmp/test%s.wav' % str(ii))
#			ii += 1
#		engine.runAndWait()

