import mock
import re
import shutil
import sys
import tempfile
import unittest
from logging import StreamHandler

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test.client import Client
from django.utils import unittest as unittest2

from MHLogin.Invites.models import Invitation
from MHLogin.MHLCallGroups.models import CallGroup, CallGroupMemberPending
from MHLogin.MHLPractices.models import PracticeLocation, Pending_Association, \
	OrganizationType, OrganizationSetting
from MHLogin.MHLUsers.models import MHLUser, Administrator, Provider, Physician, \
	OfficeStaff, Office_Manager
from MHLogin.utils.geocode import geocode2
from MHLogin.utils.mh_logging import get_standard_logger
from MHLogin.utils.storage import S3Storage, LocalStorage, _connection
from MHLogin.utils.templates import phone_formater, set_settings_to_dict
from MHLogin.Validates.models import Validation


@unittest2.skipIf(not _connection or not settings.S3_BUCKET_NAME, 
				"BUCKET_NAME not defined")
class S3StorageTests(unittest.TestCase):
	test_string1 = "this is a test string, there are many like it but this one is mine"
	test_string2 = "this string is less creative than Kunkka"
	test_string3 = "SPROINK!"

	def setUp(self):
		self.saved_bucket_name = settings.S3_BUCKET_NAME
		self.bucket_name = 'test_' + settings.S3_BUCKET_NAME
		settings.S3_BUCKET_NAME = self.bucket_name
		self.bucket = _connection.create_bucket(settings.S3_BUCKET_NAME)

	def tearDown(self):
		self.bucket.delete_keys(self.bucket.get_all_keys())
		self.bucket.delete()
		settings.S3_BUCKET_NAME = self.saved_bucket_name

	def test_s3(self):
		f = S3Storage.create_file("write_test")
		self.assertTrue(f)
		f.set_contents(self.test_string1)
		f2 = S3Storage.get_file("write_test")
		self.assertTrue(f2)
		self.assertEqual(f2.read(), self.test_string1)
		f.close()
		f2.close()
		f = S3Storage.create_file("overwrite_test")
		f.set_contents(self.test_string2)
		f2 = S3Storage.get_file("overwrite_test")
		self.assertEqual(f2.read(), self.test_string2)
		f2.close()
		f.set_contents(self.test_string3)
		f2 = S3Storage.get_file("overwrite_test")
		self.assertEqual(f2.read(), self.test_string3)
		self.assertEqual(S3Storage.get_file("idontexist"), None)


class LocalStorageTests(unittest.TestCase):
	test_string1 = "this is a test string, there are many like it but this one is mine"
	test_string2 = "this string is less creative than Kunkka"
	test_string3 = "SPROINK!"

	def setUp(self):
		self.saved_media = settings.MEDIA_ROOT
		self.media = tempfile.mkdtemp()
		settings.MEDIA_ROOT = self.media

	def tearDown(self):
		settings.MEDIA_ROOT = self.saved_media
		shutil.rmtree(self.media)

	def test_localstorage(self):
		f = LocalStorage.create_file("write_test")
		self.assertTrue(f)
		f.set_contents(self.test_string1)
		f.fp.flush()
		f2 = LocalStorage.get_file("write_test")

		self.assertTrue(f2)
		s = f2.read()
		self.assertEqual(s, self.test_string1)
		f.close()
		f2.close()
		f = LocalStorage.create_file("overwrite_test")
		f.set_contents(self.test_string2)
		f2 = LocalStorage.get_file("overwrite_test")
		self.assertEqual(f2.read(), self.test_string2)
		f2.close()
		f.set_contents(self.test_string3)
		f2 = LocalStorage.get_file("overwrite_test")
		self.assertEqual(f2.read(), self.test_string3)
		self.assertEqual(LocalStorage.get_file("idontexist"), None)


class GeocodeUnitTest(unittest.TestCase):
	class MockYahooGeo(object):
		__init__ = lambda self, *args, **kwargs: None

		def geocode(self, street=None, city=None, state=None, zipcode=None):
			raise Exception("Yahoo Unused")

	class MockGoogleGeo(object):
		def geocode(self, street=None, city=None, state=None, zipcode=None):
			return u'555 Bryant Street, Palo Alto, CA 94301, USA', \
				(37.44533089999999, -122.1606816)

	@mock.patch('MHLogin.utils.geocode.geocoders.GoogleV3', return_value=MockGoogleGeo())
	def test_goodaddress(self, geo):
		results = geocode2('555 Bryant St', 'Palo Alto', 'CA', '', self.MockYahooGeo)
		self.assertTrue(results['lat'] != 0.0 and results['lng'] != 0.0)
		self.assertEquals(round(results['lat'], 2), 37.45, results['lat'])
		self.assertEquals(round(results['lng'], 2), -122.16, results['lng'])

	@mock.patch('MHLogin.utils.geocode.geocoders.GoogleV3', return_value=MockGoogleGeo())
	def test_emptyaddress(self, geo):
		results = geocode2('', '', '', '', self.MockYahooGeo)
		self.assertTrue(results['lat'] == 0.0 and results['lng'] == 0.0)


class TemplateTest(unittest2.TestCase):

	@classmethod
	def setUpClass(cls):
		cls.temp_call_enable = settings.CALL_ENABLE
		settings.CALL_ENABLE = True
		cls.pl = PracticeLocation.objects.create(practice_lat=0.0, practice_longit=0.0)
		cls.provider = create_user("hmeister", "heal", "meister", "demo", 
							"555 Bryant St.", "Palo Alto", "CA", "", uklass=Provider)
		cls.provider.mdcom_phone = '234'
		cls.provider.save()

		cls.staff = create_user("sdude", "staff", "dude", "demo", 
							"Ocean Avenue", "Carmel", "CA", "93921", uklass=OfficeStaff)
		cls.staff.user.mdcom_phone = '456'
		cls.staff.current_practice = cls.pl
		cls.staff.user.save()
		cls.staff.save()

		cls.doctor = Physician.objects.get_or_create(user=cls.provider)[0]

	@classmethod
	def tearDownClass(cls):
		settings.CALL_ENABLE = cls.temp_call_enable
		PracticeLocation.objects.all().delete()
		Provider.objects.all().delete()
		MHLUser.objects.all().delete()
		OfficeStaff.objects.all().delete()
		Physician.objects.all().delete()

	def test_phone_formater(self):
		phonePattern = re.compile(r'(\d{3})\D*(\d{3})\D*(\d{4})\D*(\d*)$')
		# test bad number
		phone = phone_formater("xyz", display_provisionLink=False)
		match = phonePattern.search(phone)
		self.assertTrue(match == None, phone)

		# test good number
		phone = phone_formater("4085551212", display_provisionLink=False)
		match = phonePattern.search(phone)
		self.assertTrue(match != None, phone)

		# test blank number
		phone = phone_formater("", display_provisionLink=False)
		# this is questionable, we don't return a string object when blank
		self.assertTrue(type(phone) != str, type(phone))

		# test blank number with provision link
		phone = phone_formater("", display_provisionLink=True)

		match = phonePattern.search(phone)
		self.assertEqual(match, None, match)

		# test blank number with CALL_ENABLED
		temp = settings.CALL_ENABLE
		settings.CALL_ENABLE = not(temp)
		phone = phone_formater("", display_provisionLink=True)
		self.assertTrue(type(phone) != str, type(phone))
		settings.CALL_ENABLE = temp

	def test_mhlogin_template_context_processor(self):
		c = Client()
		# after successful login should get re-direct to /
		response = c.post('/login/', {'username': self.doctor.user.user.username, 
									'password': 'demo'})
		self.assertEqual(response.status_code, 302)
		# verify we are logged in
		self.assertEqual(c.session['_auth_user_id'], self.doctor.user.user.pk)

		response = c.get(reverse('MHLogin.DoctorCom.views.provider_view'))
		self.assertEqual(response.status_code, 200, response.status_code)
		# now logout, we can alternatively call c.post('/logout/')
		response = c.logout()
		self.assertFalse('_auth_user_id' in c.session)

		context = {"somekey": "somedata"} 
		set_settings_to_dict(context)
		self.assertTrue(context["CALL_ENABLE"] == settings.CALL_ENABLE)

		context = {}
		set_settings_to_dict(context)
		# if none verify it normalizes to empty dict but with no call_enable
		self.assertTrue(context != None and 'CALL_ENABLE' not in context)

	def test_office_staff_login(self):
		c = Client()
		# after successful login should get re-direct to /
		response = c.post('/login/', {'username': self.staff.user.username, 
									'password': 'demo'})
		self.assertEqual(response.status_code, 302)
		# verify we are logged in
		self.assertEqual(c.session['_auth_user_id'], self.staff.user.pk)

		response = c.get('/')  # get root page and get redirected to staff home
		self.assertEqual(response.status_code, 302, response.status_code)

		response = c.get(response['location'])
		self.assertEqual(response.status_code, 200, response.status_code)

		# now logout, we can alternatively call c.post('/logout/')
		response = c.logout()
		self.assertFalse('_auth_user_id' in c.session)


class ErrLibTest(unittest2.TestCase):
	@classmethod
	def setUpClass(cls):
		cls.provider = create_user("hmeister", "heal", "meister", "demo", 
							"555 Bryant St.", "Palo Alto", "CA", "", uklass=Provider)
		cls.doctor = Physician(user=cls.provider)
		cls.doctor.save()

	@classmethod
	def tearDownClass(cls):
		Provider.objects.all().delete()
		MHLUser.objects.all().delete()
		Physician.objects.all().delete()

	def test_errlib_erro404(self):
		c = Client()
		# after successful login should get re-direct to /
		response = c.post('/login/', {'username': self.doctor.user.user.username, 
									'password': 'demo'})
		self.assertEqual(response.status_code, 302)
		# verify we are logged in
		self.assertEqual(c.session['_auth_user_id'], self.doctor.user.user.pk)

		response = c.get('/page/not/found/')
		self.assertEqual(response.status_code, 404, response.status_code)
		# now logout, we can alternatively call c.post('/logout/')
		response = c.logout()
		self.assertFalse('_auth_user_id' in c.session)


class LoggerTest(unittest2.TestCase):

	def test_bad_create_logger(self):
		# Setting up logging
		class DevNull():
			def write(self, s):
				pass

		temp = sys.stderr
		sys.stderr = DevNull()  # keep logger quiet
		logger = get_standard_logger('/path_to/bad_path/test.log',
							'bad_path.test', settings.LOGGING_LEVEL)
		sys.stderr = temp		# set back to original stderr
		self.assertTrue(len(logger.handlers) == 1, len(logger.handlers))
		# this check could be better but we know under error StreamHandler is created 
		self.assertTrue(isinstance(logger.handlers[0], StreamHandler), 
								logger.handlers[0].__class__.__name__)


def create_user(username, first_name, last_name, password, 
			addr="", city="", state="", zipcode="", uklass=None):
	""" 
	Helper to create a user but will not work for all user types.  If this is 
	useful to add to common area we can make more generic to support all users.
	"""
	mhu = MHLUser(username=username, first_name=first_name, last_name=last_name)
	mhu.address1, mhu.city, mhu.state, mhu.zip = addr, city, state, zipcode
	mhu.is_active = mhu.is_staff = mhu.tos_accepted = mhu.mobile_confirmed = True
	mhu.set_password(password)
	if uklass != None and uklass == Administrator:
		mhu.is_superuser = True

	try:
		result = geocode2(mhu.address1, mhu.city, mhu.state, mhu.zip)
		mhu.lat, mhu.longit = result['lat'], result['lng']
	except Exception:
		# For unittests when geocode not avail for any reason set coords 0.0.  If a 
		# test depends on valid values make special case for that in those tests.
		mhu.lat, mhu.longit = 0.0, 0.0 
	mhu.save()

	if uklass != None:
		user = uklass(user=mhu)
		if hasattr(user, 'office_lat'):
			user.office_lat = 0.0
		if hasattr(user, 'office_longit'):
			user.office_longit = 0.0
		user.save()

	return user if uklass != None else mhu 


def clean_db_datas():
	PracticeLocation.objects.all().delete()
	Administrator.objects.all().delete()
	Provider.objects.all().delete()
	Office_Manager.objects.all().delete()
	OfficeStaff.objects.all().delete()
	MHLUser.objects.all().delete()
	Pending_Association.objects.all().delete()
	OrganizationType.objects.all().delete()
	OrganizationSetting.objects.all().delete()
	CallGroup.objects.all().delete()
	Invitation.objects.all().delete()
	CallGroupMemberPending.objects.all().delete()
	Validation.objects.all().delete()
