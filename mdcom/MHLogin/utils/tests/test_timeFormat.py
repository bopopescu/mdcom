#-*- coding: utf-8 -*-
import time
from datetime import datetime, timedelta
from django.test import TestCase
from django.conf import settings

from MHLogin.utils.timeFormat import time_format, hour_format, formatTimeSetting,\
	getCurrentPracticeTimeZone, getDisplayedTimeZone, timezone_conversion, timezone,\
	convertDatetimeToUTCTimestamp, convert_dt_to_utz, convert_dt_to_stz, \
	getCurrentTimeZoneForUser, minute_format, TIME_ZONES_CHOICES
from MHLogin.utils.tests.tests import create_user
from MHLogin.MHLPractices.models import PracticeLocation


class TimeFormatTest(TestCase):
	@classmethod
	def setUpClass(cls):
		# create admin and test user
		cls.mhluser = create_user("mhluser1", "fn", "ln", "demo",
							"Ocean Avenue", "Carmel", "CA", "93921")

	def test_time_format(self):
		dt = datetime(2013, 02, 20, 01, 01, 01)
		mhluser = self.mhluser
		ft = time_format(mhluser, dt)
		self.assertEqual(ft, '02/20/13 01:01')
		mhluser.time_setting = True
		ft = time_format(mhluser, dt)
		self.assertEqual(ft, '02/20/13 01:01 AM')
		mhluser.time_setting = False
		ft = time_format(mhluser, dt)
		self.assertEqual(ft, '02/20/13 01:01')

	def test_hour_format(self):
		dt = datetime(2013, 02, 20, 01, 01, 01)
		mhluser = self.mhluser
		ft = hour_format(mhluser, dt)
		self.assertEqual(ft, '01:01')
		mhluser.time_setting = True
		ft = hour_format(mhluser, dt)
		self.assertEqual(ft, '01:01 AM')
		mhluser.time_setting = False
		ft = hour_format(mhluser, dt)
		self.assertEqual(ft, '01:01')

	def test_minute_format(self):
		dt_dict = {
					'12:01:01 AM': '00:01:01',
					'11:01:01 AM': '11:01:00',
					'12:01:01 PM': '12:01:00',
					'11:01:01 pm': '23:01:00',
					'00:01:55': '00:01:01',
					'01:01:00': '01:01:00',
				}
		for dt, result in dt_dict.iteritems():
			self.assertEqual(minute_format(dt), result)

	def test_formatTimeSetting(self):
		ts_int = 1359456033
		cmp_dt = datetime(2013, 01, 29, 10, 40, 33, 0)
		cmp_dt1 = cmp_dt.strftime('%m/%d/%y %I:%M %p')
		cmp_dt2 = cmp_dt.strftime('%m/%d/%y %H:%M')
		local_tz = ('utc')
		self.mhluser.time_setting = True
		self.assertEqual(cmp_dt1, formatTimeSetting(self.mhluser, ts_int, local_tz))
		self.mhluser.time_setting = False
		self.assertEqual(cmp_dt2, formatTimeSetting(self.mhluser, ts_int, local_tz))

	def test_getCurrentTimeZoneForUser(self):
		tz = settings.TIME_ZONE
		self.assertEqual(tz, getCurrentTimeZoneForUser(None))
		self.mhluser.time_zone = None
		self.assertEqual(tz, getCurrentTimeZoneForUser(None))

		local_tz = 'America/New_York'
		role_user = self.mhluser
		practice = PracticeLocation()
		practice.time_zone = local_tz
		role_user.current_practice = practice
		self.assertEqual(local_tz, getCurrentTimeZoneForUser(self.mhluser, role_user))
		self.assertEqual(local_tz, getCurrentTimeZoneForUser(self.mhluser, None, practice))

		user_local_tz = 'America/Chicago'
		self.mhluser.time_zone = user_local_tz
		self.assertEqual(user_local_tz, getCurrentTimeZoneForUser(self.mhluser, role_user))
		self.assertEqual(user_local_tz, getCurrentTimeZoneForUser(self.mhluser, None, practice))

	def test_getCurrentPracticeTimeZone(self):
		role_user = self.mhluser
		self.assertEqual('', getCurrentPracticeTimeZone(role_user))
		practice = PracticeLocation()

		local_tz = 'America/New_York'
		practice.time_zone = "America/Detroit"
		role_user.current_practice = practice
		self.assertEqual(local_tz, getCurrentPracticeTimeZone(role_user))

		practice.time_zone = None
		role_user.current_practice = practice
		self.assertEqual('', getCurrentPracticeTimeZone(role_user))

	def test_convert_dt_to_stz(self):
		local_tz = 'America/New_York'
		practice = PracticeLocation()
		practice.time_zone = local_tz
		dt = datetime(2013, 01, 29)
		local_tz = timezone(local_tz)
		local_dt = local_tz.localize((dt + timedelta(1, -1)), is_dst=None)
		cmp_dt = local_dt.astimezone(timezone(settings.TIME_ZONE)).replace(tzinfo=None)
		self.assertEqual(cmp_dt, convert_dt_to_stz(dt, self.mhluser, practice))

	def test_convert_dt_to_utz(self):
		local_tz = 'America/New_York'
		practice = PracticeLocation()
		practice.time_zone = local_tz
		dt = datetime(2013, 01, 29)
		local_tz = timezone(local_tz)
		local_dt = timezone(settings.TIME_ZONE).localize(dt, is_dst=None)
		cmp_dt = local_dt.astimezone(local_tz).replace(tzinfo=None)
		self.assertEqual(cmp_dt, convert_dt_to_utz(dt, self.mhluser, practice))

	def test_timezone_conversion(self):
		ts_int = 1359456033
		ts_float = 1359456033.0
		ts_long = long(1359456033)
		ts_str = '1359456033'
		cmp_dt = datetime(2013, 01, 29, 10, 40, 33, 0)
		to_tz = timezone('utc')
		self.assertEqual(cmp_dt, timezone_conversion(ts_int, to_tz)
						.replace(tzinfo=None))
		self.assertEqual(cmp_dt, timezone_conversion(ts_float, to_tz)
						.replace(tzinfo=None))
		self.assertEqual(cmp_dt, timezone_conversion(ts_long, to_tz)
						.replace(tzinfo=None))
		self.assertEqual(ts_str, timezone_conversion(ts_str, to_tz))

	def test_getDisplayedTimeZone(self):
		time_dict = dict(TIME_ZONES_CHOICES)
		time_dict['None'] = None
		for k, v in time_dict.iteritems():
			self.assertEqual(v, getDisplayedTimeZone(k))

	def test_convertDatetimeToUTCTimestamp(self):
		ts = time.mktime((2013, 02, 20, 01, 01, 01, 0, 0, 0))
		dt = datetime(2013, 02, 20, 01, 01, 01)
		dt_utc_ts = int(convertDatetimeToUTCTimestamp(dt))
		self.assertEqual(ts, dt_utc_ts)
