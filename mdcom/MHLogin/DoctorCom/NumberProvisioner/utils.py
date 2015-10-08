
import json

from urlparse import urljoin

from django.conf import settings
from django.core.urlresolvers import reverse

from twilio import TwilioRestException
from twilio.rest.resources import make_twilio_request
from MHLogin.DoctorCom.IVR.utils import _getUSNumber, _makeUSNumber
from MHLogin.utils.mh_logging import get_standard_logger

from MHLogin.utils.twilio_utils import client, client2008, TWILIO_AREACODE_PARAMETER_NOT_SUPPORTED, \
	TWILIO_INVALID_AREA_CODE, TWILIO_NO_PHONE_NUMBERS_IN_AREA_CODE

from django.utils.translation import ugettext_lazy as _

logger = get_standard_logger('%s/DoctorCom/NumProvUtil.log' % (settings.LOGGING_ROOT),
							'DoctorCom.NumProvUtil', settings.LOGGING_LEVEL)


def twilio_account_active():
	try:
		account = client.accounts.get(settings.TWILIO_ACCOUNT_SID)
		if account:
			return True
		else:
			return False
	except TwilioRestException:
		# if account is not active, suspended, etc
		return False


def twilio_get_available_number(area_code, incountry="US", intype="local"):
	"""
	request for number in area_code - returns available
	"""
	try:
		avail_numbers = client.phone_numbers.search(area_code=area_code,
    		country=incountry, type=intype)
		if avail_numbers:
			number_info = avail_numbers[0]
			logger.debug('twilio_ProvisionNewLocalNumber2010 areacode %s got %s' % (
				area_code, number_info.phone_number))
		else:
			number_info = None
		# if we don't get any number, retry...?
	except TwilioRestException as re:
		# This error indicates that no number was available.
		if re.code not in (TWILIO_AREACODE_PARAMETER_NOT_SUPPORTED,
			TWILIO_INVALID_AREA_CODE, TWILIO_NO_PHONE_NUMBERS_IN_AREA_CODE):
			raise Exception(_('Provision Local number fail: %s' % re.msg))
	except KeyError:
		pass  # return None if json fields not in resp
	return number_info


def twilio_old_get_available_number(area_code, incountry="US", intype="local"):
	"""
	request for number in area_code - DOES NOT RESPECT AREACODE restriction
	TO BE REMOVED - return only phone #
	"""
	auth, uri, = client.auth, client.account_uri
	abs_uri = '://'.join([settings.SERVER_PROTOCOL, settings.SERVER_ADDRESS])
	d = {
		'AreaCode': area_code,
	}
	num_tup = None
	try:
		resp = make_twilio_request('GET',
			uri + '/AvailablePhoneNumbers/US/Local', auth=auth, data=d)
		content = json.loads(resp.content)
		# get the first phone number entry that matches - phone # only
		number_info = content['available_phone_numbers'][0]['phone_number']
		# if we don't get any number, retry...?
		logger.debug('twilio_ProvisionNewLocalNumber2010 areacode %s got %s number %s' % (
			area_code, str(content), number_info))
		us_number_info = _getUSNumber(number_info)
	except TwilioRestException as re:
		# This error indicates that no number was available.
		if re.code not in (TWILIO_AREACODE_PARAMETER_NOT_SUPPORTED,
			TWILIO_INVALID_AREA_CODE, TWILIO_NO_PHONE_NUMBERS_IN_AREA_CODE):
			raise Exception(_('Provision Local number fail: %s' % re.msg))
	except KeyError:
		pass  # return None if json fields not in resp
	return us_number_info


def twilio_ProvisionNewLocalNumber2010(area_code):
	"""
	replicated from twilio_ProvisionNewLocalNumber - full replacemement when
	we convert fully to 2010
	:param area_code:
		area_code may be any valid three-digit string with the first digit
		being 2-9 (inclusive), second digit being 0-8 (inclusive) and last digit
		being 0-9 (inclusive). Toll-free numbers are excluded.

	:returns:
		The newly provisioned number on success, or None if Twilio doesn't have
		any available numbers for the requested area code.

	:raises:
		A generic exception if an invalid area code is requested.
		Raises an HTTPError if the Twilio request results in an error other than
		listed above.
	twilio 2010 uses 2 phase call: 1 to call to AvailablePhoneNumbers
	and with the resulting number, call to IncomingPhoneNumbers
	Note: Country is currently hardcoded
	"""
	auth, uri = client.auth, client.account_uri
	abs_uri = '://'.join([settings.SERVER_PROTOCOL, settings.SERVER_ADDRESS])
	url = reverse('MHLogin.DoctorCom.IVR.views_generic.UnaffiliatedNumber')
	num_tup = None
	try:
		number_info = twilio_get_available_number(area_code)
		# number_info is of type twilio.rest.resources.phone_numbers.AvailablePhoneNumber
		if number_info:
			number = client.phone_numbers.purchase(
				voice_url=urljoin(abs_uri, url),
				phone_number=number_info.phone_number,
				voice_method="POST")
			logger.debug('twilio_ProvisionNewLocalNumber2010 areacode %s number %s sid %s' % (
				area_code, number_info.phone_number, number.sid))
			num_tup = (_getUSNumber(number.phone_number), number.sid)
		else:
			return None
	except TwilioRestException as re:
		# This error indicates that no number was available.
		if re.code not in (TWILIO_AREACODE_PARAMETER_NOT_SUPPORTED,
			TWILIO_INVALID_AREA_CODE, TWILIO_NO_PHONE_NUMBERS_IN_AREA_CODE):
			raise Exception(_('Provision Local number fail: %s' % re.msg))
	except KeyError:
		pass  # return None if json fields not in resp
	return num_tup


def twilio_ProvisionNewTollFreeNumber2010(area_code):
	"""
	replicated from twilio_ProvisionNewLocalNumber - full replacemement when
	we convert fully to 2010
	:param area_code:
		area_code may be one of 800, 888, 877 or 866, as per Twilio's
		documentation. If it isn't one of these values, this function will
		raise an Exception.

	:returns:
		The newly provisioned number on success, or None if Twilio doesn't have
		any available numbers for the requested area code.

	:raises:
		Raises a generic exception if an invalid area code is requested.
		Raises an HTTPError if the Twilio request results in an error other than
		listed above.
	"""
	auth, uri = client.auth, client.account_uri
	abs_uri = '://'.join([settings.SERVER_PROTOCOL, settings.SERVER_ADDRESS])
	url = reverse('MHLogin.DoctorCom.IVR.views_generic.UnaffiliatedNumber')
	num_tup = None
	try:
		number_info = twilio_get_available_number(area_code, "US", "tollfree")
		# number_info is of type twilio.rest.resources.phone_numbers.AvailablePhoneNumber
		if number_info:
			number = client.phone_numbers.purchase(
				voice_url=urljoin(abs_uri, url),
				phone_number=number_info.phone_number,
				voice_method="POST")
			logger.debug('twilio_ProvisionNewLocalNumber2010 tollfree areacode %s number %s sid %s' % (
				area_code, number_info.phone_number, number.sid))
			num_tup = (_getUSNumber(number.phone_number), number.sid)
		else:
			return None
	except TwilioRestException as re:
		# This error indicates that no number was available.
		if re.code not in (TWILIO_AREACODE_PARAMETER_NOT_SUPPORTED,
			TWILIO_INVALID_AREA_CODE, TWILIO_NO_PHONE_NUMBERS_IN_AREA_CODE):
			raise Exception(_('TollFree number fail: %s' % re.msg))
	except KeyError:
		pass  # return None if json fields not in resp
	return num_tup

# TODO:
# 1. Write a function for inactive phone numbers.
def twilio_ProvisionNewLocalNumber(area_code):
	"""
	DEPRECATED - in the future, it will be replaced by twilio_ProvisionNewLocalNumber2010
	Any changes here should be replicated to twilio_ProvisionNewLocalNumber2010
	:param area_code:
		area_code may be any valid three-digit string with the first digit
		being 2-9 (inclusive), second digit being 0-8 (inclusive) and last digit
		being 0-9 (inclusive). Toll-free numbers are excluded.

	:returns:
		The newly provisioned number on success, or None if Twilio doesn't have
		any available numbers for the requested area code.

	:raises:
		A generic exception if an invalid area code is requested.
		Raises an HTTPError if the Twilio request results in an error other than
		listed above.
	Note: twilio 2010 uses 2 phase call: 1 to call to AvailablePhoneNumbers
	and with the resulting number, call to IncomingPhoneNumbers
	"""
	if (settings.TWILIO_PHASE == 2):
		return twilio_ProvisionNewLocalNumber2010(area_code)
	else:
		auth, uri, = client2008.auth, client2008.account_uri
	abs_uri = '://'.join([settings.SERVER_PROTOCOL, settings.SERVER_ADDRESS])
	url = reverse('MHLogin.DoctorCom.IVR.views_generic.UnaffiliatedNumber')
	d = {
		#'From' : settings.TWILIO_CALLER_ID,
		'AreaCode': area_code,
		'FriendlyName': 'Unassigned Number',
		'Url': urljoin(abs_uri, url),
	}
	num_tup = None
	try:
		resp = make_twilio_request('POST',
			uri + '/IncomingPhoneNumbers/Local', auth=auth, data=d)
		content = json.loads(resp.content)
		number_info = content['TwilioResponse']['IncomingPhoneNumber']['PhoneNumber']
		sid = content['TwilioResponse']['IncomingPhoneNumber']['Sid']
		num_tup = (number_info, sid)
	except TwilioRestException as re:
		# This error indicates that no number was available.
		if re.code not in (TWILIO_AREACODE_PARAMETER_NOT_SUPPORTED,
			TWILIO_INVALID_AREA_CODE, TWILIO_NO_PHONE_NUMBERS_IN_AREA_CODE):
			raise Exception(_('Provision Local number fail: %s' % re.msg))
	except KeyError:
		pass  # return None if json fields not in resp
	return num_tup


def twilio_ProvisionNewTollFreeNumber(area_code):
	"""
	DEPRECATED - in the future, it will be replaced by twilio_ProvisionNewTollFreeNumber2010
	Any changes here should be replicated to twilio_ProvisionNewTollFreeNumber2010
	:param area_code:
		area_code may be one of 800, 888, 877 or 866, as per Twilio's
		documentation. If it isn't one of these values, this function will
		raise an Exception.

	:returns:
		The newly provisioned number on success, or None if Twilio doesn't have
		any available numbers for the requested area code.

	:raises:
		Raises a generic exception if an invalid area code is requested.
		Raises an HTTPError if the Twilio request results in an error other than
		listed above.
	"""
	if (settings.TWILIO_PHASE == 2):
		return twilio_ProvisionNewTollFreeNumber2010(area_code)
	else:
		auth, uri = client2008.auth, client2008.account_uri
	abs_uri = '://'.join([settings.SERVER_PROTOCOL, settings.SERVER_ADDRESS])
	url = reverse('MHLogin.DoctorCom.IVR.views_generic.UnaffiliatedNumber')
	d = {
		#'From' : settings.TWILIO_CALLER_ID,
		'AreaCode': area_code,
		'FriendlyName': _('Unassigned Number'),
		'Url': urljoin(abs_uri, url),
	}
	num_tup = None
	try:
		resp = make_twilio_request('POST',
			uri + '/IncomingPhoneNumbers/TollFree', auth=auth, data=d)
		content = json.loads(resp.content)
		number_info = content['TwilioResponse']['IncomingPhoneNumber']['PhoneNumber']
		sid = content['TwilioResponse']['IncomingPhoneNumber']['Sid']
		num_tup = (number_info, sid)
	except TwilioRestException as re:
		# This error indicates that no number was available.
		if re.code not in (TWILIO_AREACODE_PARAMETER_NOT_SUPPORTED,
			TWILIO_INVALID_AREA_CODE, TWILIO_NO_PHONE_NUMBERS_IN_AREA_CODE):
			raise Exception(_('TollFree number fail: %s' % re.msg))
	except KeyError:
		pass  # return None if json fields not in resp
	return num_tup


def twilio_ConfigureProviderLocalNumber2010(provider, tw_number):
	"""
	Configures a provider's Twilio number to point to the correct Twilio IVR
	handler for the user, as well as sets the incoming phone number's friendly
	name appropriately.
	:param provider:
	2010 version - need different status callback url
	"""
	auth, uri = client.auth, client.account_uri
	tw_number = _getUSNumber(tw_number)
	# assume US number, need to add country code
	norm_number = _makeUSNumber(tw_number)
	abs_uri = '://'.join([settings.SERVER_PROTOCOL, settings.SERVER_ADDRESS])
	url = reverse('MHLogin.DoctorCom.IVR.views_provider_v2.ProviderIVR_Main_New')
	statusurl = reverse('MHLogin.DoctorCom.IVR.views_provider_v2.ProviderIVR_Status')
	smsurl = reverse('MHLogin.DoctorCom.SMS.views.twilioSMS_incoming')

	d = {
		'PhoneNumber': norm_number,
		'FriendlyName': _('%i\'s DCom Number') % (provider.id),
		'VoiceUrl': urljoin(abs_uri, url),
		'VoiceMethod': 'POST',
		'StatusCallback': urljoin(abs_uri, statusurl),
		'StatusCallbackMethod': 'POST',
		'SmsUrl': urljoin(abs_uri, smsurl),
	}
	# TODO: add resp = , Verify the resulting data from Twilio, in JSON format
	try:
		make_twilio_request('POST',
			uri + '/IncomingPhoneNumbers/' + provider.mdcom_phone_sid, auth=auth, data=d)
	except TwilioRestException:
		pass

	return True


def twilio_ConfigureProviderLocalNumber(provider, tw_number):
	"""
	DEPRECATED - in the future, it will be replaced by twilio_ConfigureProviderLocalNumber2010
	Any changes here should be replicated to twilio_ConfigureProviderLocalNumber2010
	Configures a provider's Twilio number to point to the correct Twilio IVR
	handler for the user, as well as sets the incoming phone number's friendly
	name appropriately.
	:param provider:
	"""
	if (settings.TWILIO_PHASE == 2):
		return twilio_ConfigureProviderLocalNumber2010(provider, tw_number)
	else:
		auth, uri = client2008.auth, client2008.account_uri

	abs_uri = '://'.join([settings.SERVER_PROTOCOL, settings.SERVER_ADDRESS])
	url = reverse('MHLogin.DoctorCom.IVR.views_provider.ProviderIVR_Main')
	smsurl = reverse('MHLogin.DoctorCom.SMS.views.twilioSMS_incoming')

	d = {
		'FriendlyName': _('%i\'s DCom Number') % (provider.id),
		'Url': urljoin(abs_uri, url),
		'SmsUrl': urljoin(abs_uri, smsurl),
	}
	# TODO: add resp = , Verify the resulting data from Twilio, in JSON format
	try:
		make_twilio_request('POST',
			uri + '/IncomingPhoneNumbers/' + provider.mdcom_phone_sid, auth=auth, data=d)
	except TwilioRestException:
		pass

	return True


def twilio_ConfigurePracticeLocalNumber2010(practice, tw_number):
	"""
	Configures a practice's Twilio number to point to the correct Twilio IVR
	handler for the user, as well as sets the incoming phone number's friendly
	name appropriately.
	:param practice - practiceLocation which has mdcom_phone and mdcom_phone_sid set:
	2010 version - need different status callback url
	"""
	auth, uri = client.auth, client.account_uri
	tw_number = _getUSNumber(tw_number)
	# assume US number, need to add country code
	norm_number = '+1' + tw_number
	abs_uri = '://'.join([settings.SERVER_PROTOCOL, settings.SERVER_ADDRESS])
	url = reverse('MHLogin.DoctorCom.IVR.views_practice_v2.PracticeIVR_Main_New')
	statusurl = reverse('MHLogin.DoctorCom.IVR.views_practice_v2.PracticeIVR_Status')
	smsurl = reverse('MHLogin.DoctorCom.SMS.views.twilioSMS_incoming')

	d = {
		'PhoneNumber': norm_number,
		'FriendlyName': _('%s\'s DCom Number') % (practice.practice_name),
		'VoiceUrl': urljoin(abs_uri, url),
		'VoiceMethod': 'POST',
		'StatusCallback': urljoin(abs_uri, statusurl),
		'StatusCallbackMethod': 'POST',
		'SmsUrl': urljoin(abs_uri, smsurl),
	}
	# TODO: add resp = , Verify the resulting data from Twilio, in JSON format
	try:
		make_twilio_request('POST',
			uri + '/IncomingPhoneNumbers/' + practice.mdcom_phone_sid, auth=auth, data=d)
	except TwilioRestException:
		pass

	return True

def twilio_ConfigurePracticeLocalNumber(practice, tw_number):
	"""
	DEPRECATED - in the future, it will be replaced by twilio_ConfigurePracticeLocalNumber2010
	Any changes here should be replicated to twilio_ConfigurePracticeLocalNumber2010
	Configures a practice's Twilio number to point to the correct Twilio IVR
	handler for the user, as well as sets the incoming phone number's friendly
	name appropriately.
	:param practice - PracticeLocation with mdcom_phone and mdcom_phone_sid set to the number
	whose urls is being set
	"""
	if (settings.TWILIO_PHASE == 2):
		return twilio_ConfigurePracticeLocalNumber2010(practice, tw_number)
	else:
		auth, uri = client2008.auth, client2008.account_uri

	abs_uri = '://'.join([settings.SERVER_PROTOCOL, settings.SERVER_ADDRESS])
	url = reverse('MHLogin.DoctorCom.IVR.views_practice.PracticeIVR_Main')
	smsurl = reverse('MHLogin.DoctorCom.SMS.views.twilioSMS_incoming')

	d = {
		'FriendlyName': _('%s\'s DCom Number') % (practice.practice_name),
		'Url': urljoin(abs_uri, url),
		'SmsUrl': urljoin(abs_uri, smsurl),
	}
	# TODO: add resp = , Verify the resulting data from Twilio, in JSON format
	try:
		make_twilio_request('POST',
			uri + '/IncomingPhoneNumbers/' + practice.mdcom_phone_sid, auth=auth, data=d)
	except TwilioRestException:
		pass

	return True


def twilio_ResetLocalNumber():
	pass

