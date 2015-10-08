
import urlparse 

from django.utils import unittest
from django.test.client import Client
from django.conf import settings
from django.core.urlresolvers import reverse

from MHLogin.utils.mh_logging import get_standard_logger 
from MHLogin.MHLUsers.models import MHLUser, Salesperson, Administrator, Provider, Physician
from MHLogin.MHLPractices.models import PracticeLocation
from MHLogin.MHLSites.models import Site
from MHLogin.utils.tests import create_user
from MHLogin.utils.decorators import skipIfUrlFails

# Setting up logging
logger = get_standard_logger('%s/analytics/tests.log' % (settings.LOGGING_ROOT),
							'analytics.tests', settings.LOGGING_LEVEL)


class AnalyticsUnitTest(unittest.TestCase):
	""" Sales unittester for creating Salesperson, Salse Products, Sales Leads
		and verifying everything stays in sync with no errors or failures
	"""
	@classmethod
	def setUpClass(cls):  # done once for all AnalyticsUnitTest
		# needed at login
		# create admin and test user
		cls.admin = create_user("sduper", "super", "duper", "demo", 
							"Ocean Avenue", "Carmel", "CA", "93921", uklass=Administrator)
		cls.guest = create_user("cbear", "care", "bear", "demo", 
							"Winchester Blvd.", "San Jose", "CA", uklass=Salesperson)
		cls.practice = PracticeLocation.objects.create(practice_name='Beach bums',
				practice_address1='Del Monte Ave.', practice_city='Monterey',
				practice_state='CA', practice_lat=0.0, practice_longit=0.0)
		cls.site = Site.objects.create(name='Site 9', address1='Ala Moana Ct.',
				city='Saratoga', state='CA', lat=0.0, longit=0.0)
		cls.provider = create_user("dholiday", "doc", "holiday", "demo", 
							"123 Main St.", "Phoenix", "AZ", uklass=Provider)
		cls.docholiday = Physician.objects.create(user=cls.provider)

	@classmethod
	def tearDownClass(cls):  # done once for all AnalyticsUnitTest
		Administrator.objects.all().delete()
		MHLUser.objects.all().delete()
		Provider.objects.filter(id=cls.provider.id).delete()
		Physician.objects.filter(id=cls.docholiday.id).delete()
		PracticeLocation.objects.filter(id=cls.practice.id).delete()
		Site.objects.filter(id=cls.site.id).delete()

	def test_admin_can_view_analytics_home(self):
		c = Client()
		# after successful login should get re-direct to /
		response = c.post('/login/', {'username': self.admin.user.username, 
									'password': 'demo'})
		self.assertEqual(response.status_code, 302)
		# verify we are logged in
		self.assertEqual(c.session['_auth_user_id'], self.admin.user.pk)
		# now we redirect ourselves to user's default homepage, in this case /Sales
		response = c.get(response['location'])
		# should get 302
		self.assertEqual(response.status_code, 302)
		# should get /dcAdmin
		path = urlparse.urlparse(response['location']).path
		self.assertEqual(path, "/dcAdmin/")
		# we are at Admin Home page!  Now try to goto main analytics
		response = c.get('/analytics/')
		# should get 200
		self.assertEqual(response.status_code, 200)
		# now logout, we can alternatively call c.post('/logout/')
		response = c.logout()
		self.assertFalse('_auth_user_id' in c.session)

	def test_regular_user_cannot_view_analytics_home(self):
		c = Client()
		# after successful login should get re-direct to /
		response = c.post('/login/', {'username': self.guest.user.username, 
									'password': 'demo'})
		self.assertEqual(response.status_code, 302)
		# verify we are logged in
		self.assertEqual(c.session['_auth_user_id'], self.guest.user.pk)
		# now we redirect ourselves to user's default homepage, in this case /Sales
		response = c.get(response['location'])
		# should get 302
		self.assertEqual(response.status_code, 302)
		# Now try to goto main analytics, we should get ACL rule failure
		response = c.get('/analytics/')
		# should get 200
		self.assertEqual(response.status_code, 403)
		# now logout, we can alternatively call c.post('/logout/')
		response = c.logout()
		self.assertFalse('_auth_user_id' in c.session)

	@skipIfUrlFails("http://maps.google.com", "Skipping analytics map get requests")
	def test_analytics_get_requests(self):
		c = Client()
		# after successful login should get re-direct to /
		response = c.post('/login/', {'username': self.admin.user.username, 
									'password': 'demo'})
		self.assertEqual(response.status_code, 302)
		# verify we are logged in
		self.assertEqual(c.session['_auth_user_id'], self.admin.user.pk)
		# now we redirect ourselves to user's default homepage, in this case /Sales
		response = c.get(response['location'])
		# should get 302
		self.assertEqual(response.status_code, 302)
		# Now try to goto main analytics, we should get ACL rule failure
		response = c.get('/analytics/')
		self.assertEqual(response.status_code, 200, response.status_code)

		# test click2call view
		response = c.post(reverse('MHLogin.analytics.views.click2call'),
			{'start_date': '01-01-2012', 'end_date': '12-31-2012'})
		self.assertEqual(response.status_code, 200, response.status_code)
		# test page view
		response = c.post(reverse('MHLogin.analytics.views.pages'))
		self.assertEqual(response.status_code, 200, response.status_code)
		# test invite view
		response = c.post(reverse('MHLogin.analytics.views.invites'))
		self.assertEqual(response.status_code, 200, response.status_code)
		# test summary view
		response = c.post(reverse('MHLogin.analytics.views.summary'))
		self.assertEqual(response.status_code, 200, response.status_code)

		# test twilio view
		response = c.post(reverse('MHLogin.analytics.views.twilio_stats'))
		self.assertEqual(response.status_code, 200, response.status_code)

		# test map view
		response = c.get(reverse('MHLogin.analytics.views.map_view'))
		self.assertEqual(response.status_code, 200, response.status_code)
		for key, val in {"physicians": 200, "providers": 200, "admin": 200, 
					"managers": 200, "staff": 200, "all": 200, 
					"sites": 200, "practices": 200, "gibberish": 500}.items():
			response = c.get(reverse('MHLogin.analytics.views.map_view') + "?filter=%s" % key)
			self.assertEqual(response.status_code, val, response.status_code)
		response = c.get(reverse('MHLogin.analytics.views.map_lost'))
		self.assertEqual(response.status_code, 200, response.status_code)
		response = c.get(reverse('MHLogin.analytics.views.map_get_lost_list') + "?geocode=true")
		self.assertEqual(response.status_code, 200, response.status_code)

		# test content requests
		response = c.get(reverse('MHLogin.analytics.views.map_get_content_info') +
						"?type=user&id=" + str(self.admin.user.id))
		self.assertEqual(response.status_code, 200, response.status_code)
		response = c.get(reverse('MHLogin.analytics.views.map_get_content_info') +
						"?type=user&id=" + str(self.provider.user.id))
		self.assertEqual(response.status_code, 200, response.status_code)
		response = c.get(reverse('MHLogin.analytics.views.map_get_content_info') +
						"?type=practice&id=" + str(self.practice.id))
		self.assertEqual(response.status_code, 200, response.status_code)
		response = c.get(reverse('MHLogin.analytics.views.map_get_content_info') +
						"?type=site&id=" + str(self.site.id))
		self.assertEqual(response.status_code, 200, response.status_code)
		# test some invalid requests (view will - error is user facing)
		response = c.get(reverse('MHLogin.analytics.views.map_get_content_info') +
						"?type=site&id=" + str(101010))
		self.assertEqual(response.status_code, 200, response.status_code)
		response = c.get(reverse('MHLogin.analytics.views.map_get_content_info') +
						"?type=boo&id=" + str(self.site.id))
		self.assertEqual(response.status_code, 200, response.status_code)
		response = c.get(reverse('MHLogin.analytics.views.map_get_content_info'))
		self.assertEqual(response.status_code, 200, response.status_code)

		# now logout, we can alternatively call c.post('/logout/')
		response = c.logout()
		self.assertFalse('_auth_user_id' in c.session)

