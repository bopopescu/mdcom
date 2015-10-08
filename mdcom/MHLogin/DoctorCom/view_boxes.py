
import logging 

from django.conf import settings
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from MHLogin.utils.templates import get_context

from MHLogin.KMS.exceptions import KMSException
from MHLogin.KMS.shortcuts import decrypt_object
from MHLogin.utils.mh_logging import get_standard_logger 


# Setting up logging
if (not 'logger' in locals()):
	logger = get_standard_logger('%s/DoctorCom/views_boxes.log' % (settings.LOGGING_ROOT), 
								'DCom.views_boxes', logging.DEBUG)


def box_recent_received(request):
	"""
	Process box_recent_received view request

	:param request: The HTTP GET request
	:type request: django.core.handlers.wsgi.WSGIRequest  
	:returns: django.http.HttpResponse -- the result in an HttpResonse object 
	:raises: None 
	"""
	context = get_context(request)

	return render_to_string("Messaging/box_recent_received-RD.html", context)


def box_recent_sent(request):
	"""
	Process box_recent_sent view request

	:param request: The HTTP GET request
	:type request: django.core.handlers.wsgi.WSGIRequest  
	:returns: django.http.HttpResponse -- the result in an HttpResonse object 
	:raises: None 
	"""
	context = get_context(request)

	return render_to_string("Messaging/box_recent_sent-RD.html", context)


def body_decryption_helper(request, obj):
	"""
	Assists in decrypting by catching KMS.exceptions.KMSException
	"""
	try:
		return_data = decrypt_object(request, obj)
	except KMSException as e:
		# Not much to do here. 
		logger.critical('Got error %s' % repr(e))
		return_data = _('Data decryption error. Administrators have been notified.')
	return return_data

