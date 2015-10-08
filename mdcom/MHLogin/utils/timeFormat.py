import time
from datetime import datetime, timedelta
from pytz import timezone
from pytz.exceptions import UnknownTimeZoneError

from django.conf import settings
from MHLogin.utils.constants import TIME_ZONES_CHOICES

def time_format(user, ti):
	if not user.time_setting:#24
		return ti.strftime('%m/%d/%y %H:%M')
	else:#12
		return ti.strftime('%m/%d/%y %I:%M %p')

def hour_format(user, ti):
	if not user.time_setting:#24
		return ti.strftime('%H:%M')
	else:#12
		return ti.strftime('%I:%M %p')

def minute_format(s):
	h = s.split(':')[0]
	if 'am' in s or 'AM' in s:
		if h == '12' or h == '00':
			return '00' + s[2:5] + ':01'
		else:
			return s[0:5] + ':00'
	elif 'pm' in s or 'PM' in s:
		if h == '12':
			return s[0:5] + ':00'
		else:
			t = int(h) + 12
			return str(t) + s[2:5] + ':00'
	elif h == '00':
		return s[0:5] + ':01'
	else:
		return s

#add by xlin 121023 for todo1045
#remove from Doctorcom/Message/view.py in 121207
def formatTimeSetting(user, timestamp, local_tz, use_time_setting=True):
	if isinstance(local_tz, (str, unicode)):
		local_tz = timezone(local_tz)

	if use_time_setting and user.time_setting:
		return timezone_conversion(timestamp, local_tz).strftime('%m/%d/%y %I:%M %p')
	else:
		return timezone_conversion(timestamp, local_tz).strftime('%m/%d/%y %H:%M')
		
def timezone_conversion(timestamp, to_tz):
	"""Converts the UNIX timestamp value to a Python datetime in timezone to_tz.
	
	:param timestamp: The Unix timestamp structure
	:type timestamp: timestamp
	:param to_tz: The timezone to convert to
	:type to_tz: int  
	:returns: timezone - python datetime in the timezone to_tz 
	:raises: None 
	"""
	if isinstance(timestamp, (float, long, int)):
		time_orig = datetime.fromtimestamp(timestamp, timezone('UTC'))
		return time_orig.astimezone(to_tz)
	else:
		return timestamp

OLD_TIME_ZONES_MIGRATION = {
	# Eastern
	"America/New_York": "America/New_York",
	"America/Detroit": "America/New_York",
	"America/Kentucky/Louisville": "America/New_York",
	"America/Kentucky/Monticello": "America/New_York",
	"America/Indiana/Indianapolis": "America/New_York",
	"America/Indiana/Vincennes": "America/New_York",
	"America/Indiana/Winamac": "America/New_York",
	"America/Indiana/Marengo": "America/New_York",
	"America/Indiana/Petersburg": "America/New_York",
	"America/Indiana/Vevay": "America/New_York",
	# Central
	"America/Chicago": "America/Chicago",
	"America/Indiana/Tell_City": "America/Chicago",
	"America/Indiana/Knox": "America/Chicago",
	"America/Menominee": "America/Chicago",
	"America/North_Dakota/Center": "America/Chicago",
	"America/North_Dakota/New_Salem": "America/Chicago",
	"America/North_Dakota/Beulah": "America/Chicago",
	# Mountain
	"America/Denver": "America/Boise",
	"America/Boise": "America/Boise",
	"America/Shiprock": "America/Boise",
	"America/Phoenix": "America/Phoenix", 
	# Pacific
	"America/Los_Angeles": "America/Los_Angeles",
	# Alaska
	"America/Anchorage": "America/Anchorage",
	"America/Juneau": "America/Anchorage",
	"America/Sitka": "America/Anchorage",
	"America/Yakutat": "America/Anchorage",
	"America/Nome": "America/Anchorage",
	# Hawaii
	"Pacific/Honolulu": "Pacific/Honolulu",
}

def getCurrentTimeZoneForUser(mhluser, role_user=None, current_practice=None):
	""" Get user's current timezone.
	:param mhluser: is an instance of MHLUser
	:param role_user: is an instance of Provider/OfficeStaff/Broker
	:param current_practice: is an instance of PracticeLocation

	:returns: timezone string
	"""

	tz = settings.TIME_ZONE
	if mhluser and mhluser.time_zone:
		tz = mhluser.time_zone
	else:
		if role_user and hasattr(role_user, "current_practice") and role_user.current_practice:
			current_practice =role_user.current_practice
		if current_practice:
			tz = current_practice.time_zone

	try:
		timezone(tz)
	except UnknownTimeZoneError:
		tz = settings.TIME_ZONE

	try:
		tz = OLD_TIME_ZONES_MIGRATION[tz]
	except KeyError:
		pass

	return tz

def getCurrentPracticeTimeZone(role_user):
	""" Get user's current practice's timezone.
	:param role_user: is an instance of Provider/OfficeStaff/Broker

	:returns: timezone string
	"""
	tz = ""
	if role_user and hasattr(role_user, "current_practice") and role_user.current_practice:
		current_practice =role_user.current_practice
		tz = current_practice.time_zone
		if tz:
			try:
				tz = OLD_TIME_ZONES_MIGRATION[tz]
			except KeyError:
				pass
		else:
			tz = ""
	return tz

def convert_dt_to_stz(dt, user, practice):
	"""convert datetime to server's timezone
	:dt: datetime
	:user: current mhl_user
	:practice: current user's practice

	:return time convert to server's timezone
	"""
	local_tz = timezone(getCurrentTimeZoneForUser(user, current_practice=practice))
	local_dt = local_tz.localize((dt+timedelta(1, -1)), is_dst=None)
	return local_dt.astimezone (timezone(settings.TIME_ZONE)).replace(tzinfo=None)

def convert_dt_to_utz(dt, user, practice):
	"""convert datetime to user's timezone
	:dt: datetime
	:user: current mhl_user
	:practice: current user's practice

	:return time convert to server's timezone
	"""
	local_tz = timezone(getCurrentTimeZoneForUser(user, current_practice=practice))
	local_dt = timezone(settings.TIME_ZONE).localize(dt, is_dst=None)
	return local_dt.astimezone(local_tz).replace(tzinfo=None)

def getDisplayedTimeZone(tz):
	""" Get displayed timezone.
	:param tz: timezone string, such as: America/Los_Angeles

	:returns: displayed timezone string, such as: Pacific Time (PT).
	"""
	try:
		return dict(TIME_ZONES_CHOICES)[tz]
	except KeyError:
		return None

def convertDatetimeToUTCTimestamp(dt_local):
	""" Convert local datetime to UTC timestamp.
	:param dt_local: python datetime types of data 
	:returns: utc's timestamp 
	"""
	ts = 0
	if dt_local and type(dt_local) is datetime:
		ts = time.mktime(dt_local.timetuple())
	return ts
