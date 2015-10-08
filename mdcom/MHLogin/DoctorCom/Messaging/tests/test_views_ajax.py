import datetime

from pytz import timezone
from pytz.exceptions import UnknownTimeZoneError

from django.conf import settings
from django.test import TestCase

from MHLogin.DoctorCom.Messaging.views_ajax import _get_system_time_as_tz

class GetSystemTimeAsTzTest(TestCase):
	
	def setUp(self):
		self.TIMEZOME = settings.TIME_ZONE
		settings.TIME_ZONE = "America/Los_Angeles"
		
	def test_get_system_time_as_tz(self):
		t = datetime.datetime.now()
		origin = t
		expert = t-datetime.timedelta(hours=2)
		tz = timezone('Pacific/Honolulu')
		self.assertEqual(expert.strftime('%m/%d/%y %I:%M %p') \
						, _get_system_time_as_tz(origin,tz). \
						strftime('%m/%d/%y %I:%M %p'))
		origin = t
		expert = t-datetime.timedelta(hours=2)
		tz = 'Pacific/Honolulu'
		self.assertEqual(expert.strftime('%m/%d/%y %I:%M %p') \
						, _get_system_time_as_tz(origin,tz). \
						strftime('%m/%d/%y %I:%M %p'))
		origin = None
		expert = t-datetime.timedelta(hours=2)
		tz = 'Pacific/Honolulu'
		self.assertIsNone(_get_system_time_as_tz(origin,tz))
		origin = t
		expert = t-datetime.timedelta(hours=2)
		tz = 'Pacific/1234'
		with self.assertRaises(UnknownTimeZoneError): 
			_get_system_time_as_tz(origin,tz)

		
	def tearDown(self):	
		settings.TIME_ZONE = self.TIMEZOME
	