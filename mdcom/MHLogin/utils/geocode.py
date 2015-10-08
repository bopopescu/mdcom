
import logging

from geopy import geocoders
from django.conf import settings

from MHLogin.utils.admin_utils import mail_admins
from MHLogin.utils.mh_logging import get_standard_logger 


# Setting up logging
logger = get_standard_logger('%s/utils/geocode.log' % (settings.LOGGING_ROOT), 
							'utils.geocode', logging.WARN)


# helper to get geo location coordinates
def geocode2(addr, city, state, zipcode, geocoder=geocoders.Yahoo, appid=settings.YAHOO_APP_ID):
	""" 
	This is the new geocode lookup, it will by default use the yahoo
	geocoder, however a specific geocoder can be passed in in the geocoder field.  Note 
	some geocoders require an app id such as Yahoo, Google does not.
	see http://code.google.com/p/geopy/wiki/GettingStarted for supported geocoders.

	.. code-block:: python

		# TODO: pass in an ordered list of supported geocoders:
		geocoders = [(geocoder.Yahoo, appid), (geocoder.Google, None)]  # , etc..
		for geo in geocoders:  # something like this, some work without app_id like GoogleV3
			try:
				geo = geo[0](geo[1]) 
				msg, (lat, lng) = geo.geocode("%s, %s, %s, %s" % (addr, city, state, zipcode))
				break
			except Exception as err:
				msg = msg + str(err)
				lat = lng = 0.0

	:returns: dictionary lat, lng, msg.  msg will contain the location lookup and
		any error messages along the way.  lat,lng will be 0.0 if lookup fails
	"""
	# normalize
	msg = ""
	lat = lng = 0.0
	addr, city, state, zipcode = addr or "", city or "", state or "", zipcode or ""

	if addr or city or state or zipcode:
		try:
			geo = geocoder(appid) 
			msg, (lat, lng) = geo.geocode("%s, %s, %s, %s" % (addr, city, state, zipcode))
		except Exception as err:
			msg = msg + str(err)
			# fall back on Google but check if original geocoder was not google
			if geocoder != geocoders.GoogleV3:
				try:  # try google
					gg = geocoders.GoogleV3()
					results = gg.geocode("%s, %s, %s, %s" % (addr, city, state, zipcode))
					msg = msg + ", " + results[0]  # keep first geocoder error in msg
					lat, lng = results[1]
				except Exception as err:
					msg = msg + ", " + str(err)
					lat = lng = 0.0

		if (lat == 0.0 and lng == 0.0):
			msg = "Unable to determine address for %s, %s, %s, %s, description: %s" % \
				(addr, city, state, zipcode, msg)
			mail_admins('Geocode Error!', msg) 
			logger.warn(msg)

	return {'lat': lat, 'lng': lng, 'msg': msg}


def geocode_format_request(street, city, state, zipcode, get_data={}):
	if (street):
		get_data['line1'] = street
	if (city or state or zipcode):
		line2 = []
		if (city):
			line2.append(city)
			if (state or zipcode):
				line2.append(', ')
		if (state):
			line2.append(state)
			if (zipcode):
				line2.append(' ')
		if (zipcode):
			line2.append(zipcode)
		if 'de' in settings.FORCED_LANGUAGE_CODE:
			line2.append(', DE')
		else:
			line2.append(', USA')
		get_data['line2'] = ''.join(line2)
	return get_data


def miles2latlong(miles, lat, longit):
	"""
	This function takes a distance in miles and converts it to degrees in latitude and longitude.

	For Longitude, miles vary as a function of the cosine of the latitude, such that at the 
	equator 1 degree of longitude is equal to approx 69.17104 miles. However, at the poles, 
	1 degree of longitude is equal to zero miles. To avoid cosine computations, the following 
	4th order polynomial is used to approximate the miles in 1 degree of longitude:

	Miles/Longitude = (lat^4)/A + (lat^2)/B + C

	where: A = 4500000, B = -96, C = 69.17104

	This is a simplification to avoid having to do cosine calculations.

	For latitude, the degrees per mile only varies by 0.6959 miles and so a simple average 
	miles per degree latitude of 69.0815637 is used.

	# TODO: Confirm that computation time is shorter than doing a cosine function computation.

	:returns: a tuple with degree latitude and longitude for a 
		particular miles distance at a given latitude and longitude.
	"""
	# German used kilometer so transform kilometer to mile
	if 'de' in settings.FORCED_LANGUAGE_CODE:
		miles = miles * 0.6213712

	A = 4500000.0
	B = -96.0
	C = 69.17104

	LATPERMILE = 69.0815637

	longpermile = (lat ** 4) / A + (lat ** 2) / B + C
	del_long = miles / longpermile

	del_lat = miles / LATPERMILE

	return [del_lat, del_long]


def miles2latlong_range(lat, longit, miles=settings.PROXIMITY_RANGE):
	del_lat, del_longit = miles2latlong(miles, lat, longit)
	latmin = lat - del_lat
	latmax = lat + del_lat
	longitmin = longit - del_longit
	longitmax = longit + del_longit
	return [latmin, latmax, longitmin, longitmax]

