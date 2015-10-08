
from MHLogin.KMS import utils
from MHLogin.utils import FileHelper
from MHLogin.utils.UploadHandlers import UploadProgressCachedHandler
from MHLogin.utils.mh_logging import get_standard_logger 
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadhandler import StopUpload
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils import simplejson
import logging
from django.utils.translation import ugettext_lazy as _


# Setting up logging
logger = get_standard_logger('%s/DoctorCom/Messaging/views_upload.log' % (settings.LOGGING_ROOT), 
							'DoctorCom.Messaging.views_upload', settings.LOGGING_LEVEL)


def upload(request):
	"""
	Handles upload message.

	:param request: The HTTP request
	:type request: django.core.handlers.wsgi.WSGIRequest  
	:returns: django.http.HttpResponse -- the result in an HttpResonse object 
	:raises: None
	"""
	if request.method == 'POST':
		ctx=dict()
		ctx["message"] = ""
		request.upload_handlers.insert(0, UploadProgressCachedHandler(request))
		progress_id = None
		if 'X-Progress-ID' in request.GET:
			progress_id = request.GET['X-Progress-ID']
		if progress_id:
			ctx["after_upload"] = request.GET["after_upload"]
			ctx["before_abort_upload"] = request.GET["before_abort_upload"]

			f = None
			try:
				f = request.FILES['file']
			except (StopUpload): 					
				ctx["message"] = _("The file is larger than %dM, please select a "
					"smaller file to upload.") % (settings.MAX_UPLOAD_SIZE)
			except (IOError): 					
				ctx["message"] = _("Upload is interrupted.")
			else:
				ctx["file_display_name"] = f.name
				file_name = FileHelper.generateTempFile(f.read(), utils.get_user_key(request))
				ctx["file_saved_name"] = file_name
				ctx["file_charset"] = f.charset
				ctx["file_size"] = f.size

		return render_to_response("DoctorCom/Messaging/MessageUploadResult.html",
				ctx, RequestContext(request))
	else:
		ctx = dict()	
		ctx["MAX_UPLOAD_SIZE"] = settings.MAX_UPLOAD_SIZE
		ctx["after_upload"] = request.GET["after_upload"]
		ctx["before_abort_upload"] = request.GET["before_abort_upload"]
		custom_button = False
		if "custom_button" in request.GET:
			custom_button = request.GET["custom_button"]
			custom_button = False if custom_button in ('false', 'False', '0') else bool(custom_button)
		ctx["custom_button"] = custom_button
		return render_to_response("DoctorCom/Messaging/MessageUploadForm.html", 
				ctx, RequestContext(request))	


def uploadProgress(request):
	"""
    Return JSON object with information about the progress of an upload.

	:param request: The HTTP request
	:type request: django.core.handlers.wsgi.WSGIRequest  
	:returns: django.http.HttpResponse -- the result in an HttpResonse object 
	:raises: None
    """
	progress_id = request.GET['X-Progress-ID']
	if progress_id:
		cache_key = "%s_%s" % (request.META['REMOTE_ADDR'], progress_id)
		data = cache.get(cache_key)
		if data:
			json = simplejson.dumps(data)
			return HttpResponse(json)
		else:
			json = simplejson.dumps({
				'state': 'uploading',
				'size': -1,
				'received': 0})
			return HttpResponse(json)
	else:
		logging.error("Received progress report request without X-Progress-ID parameter. "
				"request.GET: %s" % request.GET)
		return HttpResponseBadRequest('Server Error: You must provide X-Progress-ID parameter.')


def deleteAttachment(request):
	"""
    Handles upload message..

	:param request: The HTTP request
	:type request: django.core.handlers.wsgi.WSGIRequest  
	:returns: django.http.HttpResponse -- the JSON data containing result status true/false
	:raises: None
    """
	file_name = request.GET['file_name']
	if file_name:
		try:
			FileHelper.deleteTempFile(file_name)
			json = simplejson.dumps({'success': 'true'})
		except (OSError):
			json = simplejson.dumps({'success': 'false'})

	else:
		json = simplejson.dumps({'success': 'false'})	
	return HttpResponse(HttpResponse(json))

