import json

from django.http import HttpResponse
from django.shortcuts import render_to_response

from MHLogin.KMS.exceptions import KeyInvalidException
from MHLogin.apps.smartphone.v1.decorators import AppAuthentication
from MHLogin.apps.smartphone.v1.errlib import err_GE021, err_GE031, err_GE002
from MHLogin.apps.smartphone.v1.forms_messaging import MsgGetForm
from MHLogin.DoctorCom.Messaging.utils_dicom import getDicomJPG, getDicomXML, getDicomInfo, checkDicom

@AppAuthentication
def dicom_view(request, message_id, attachment_id):
	"""
	Handles dicom viewer.
	
	:param request: The HTTP request
	:type request: django.core.handlers.wsgi.WSGIRequest  
	:param message_id: Message uuid
	:type message_id: uuid
	:param attachment_id: Attachment uuid
	:type attachment_id: uuid
	:returns: DicomView.html
	:raises: Exception 
	"""
	if (request.method != 'POST'):
		return err_GE002()

	form = MsgGetForm(request.POST)
	if (not form.is_valid()):
		return err_GE031(form)

	try:
		# Get/set up data for KMS.
		device_assn = request.device_assn
		request.session['key'] = device_assn.secret
		secret = form.cleaned_data['secret']
		context = getDicomInfo(request, message_id, attachment_id, 
							dicom_jpg_func_name='MHLogin.apps.smartphone.v1.views_messaging_dicom.dicom_view_jpg',
							secret=secret)

		context["secret"] = secret
		context["device_id"] = device_assn.device_id
		return render_to_response('DoctorCom/Messaging/DicomView_APP.html', context)

	except KeyInvalidException:
		return err_GE021()

@AppAuthentication
def dicom_info(request, message_id, attachment_id):
	"""
	Handles dicom viewer.
	
	:param request: The HTTP request
	:type request: django.core.handlers.wsgi.WSGIRequest  
	:param message_id: Message uuid
	:type message_id: uuid
	:param attachment_id: Attachment uuid
	:type attachment_id: uuid
	:returns: json
	:raises: Exception 
	"""
	if (request.method != 'POST'):
		return err_GE002()

	form = MsgGetForm(request.POST)
	if (not form.is_valid()):
		return err_GE031(form)

	try:
		# Get/set up data for KMS.
		device_assn = request.device_assn
		request.session['key'] = device_assn.secret
		secret = form.cleaned_data['secret']
		context = getDicomInfo(request, message_id, attachment_id, 
							dicom_jpg_func_name='MHLogin.apps.smartphone.v1.views_messaging_dicom.dicom_view_jpg',
							secret=secret)

		response = {
			'data': context,
			'warnings': {},
		}
		return HttpResponse(content=json.dumps(response), mimetype='application/json')

	except KeyInvalidException:
		return err_GE021()

@AppAuthentication
def dicom_view_jpg(request, message_id, attachment_id, index):
	"""
	Handles download dicom jpg request.
	
	:param request: The HTTP request
	:type request: django.core.handlers.wsgi.WSGIRequest  
	:param message_id: Message uuid
	:type message_id: uuid  
	:param attachment_id: Attachment uuid
	:type attachment_id: uuid
	:returns: django.http.HttpResponse -- the result in an HttpResonse object
	:raises: Exception 
	"""

	form = None
	if (request.method != 'POST'):
		form = MsgGetForm(request.GET)
	else:
		form = MsgGetForm(request.POST)

	if (not form or not form.is_valid()):
		return err_GE031(form)

	try:
		# Get/set up data for KMS.
		request.session['key'] = request.device_assn.secret
		secret = form.cleaned_data['secret']
		return getDicomJPG(request, message_id, attachment_id, index, secret=secret)
	except KeyInvalidException:
		return err_GE021()

@AppAuthentication
def dicom_view_xml(request, message_id, attachment_id):
	"""
	Handles download dicom jpg request.
	
	:param request: The HTTP request
	:type request: django.core.handlers.wsgi.WSGIRequest  
	:param message_id: Message uuid
	:type message_id: uuid  
	:param attachment_id: Attachment uuid
	:type attachment_id: uuid
	:returns: django.http.HttpResponse -- the result in an HttpResonse object
	:raises: Exception 
	"""

	form = MsgGetForm(request.POST)
	if (not form.is_valid()):
		return err_GE031(form)

	try:
		# Get/set up data for KMS.
		request.session['key'] = request.device_assn.secret
		return getDicomXML(request, message_id, attachment_id, secret=form.cleaned_data['secret'])
	except KeyInvalidException:
		return err_GE021()

@AppAuthentication
def check_dicom(request, message_id, attachment_id):
	"""
	Check dicom jpg exsit or not.
	
	:param request: The HTTP request
	:type request: django.core.handlers.wsgi.WSGIRequest  
	:param message_id: Message uuid
	:type message_id: uuid
	:param attachment_id: Attachment uuid
	:type attachment_id: uuid
	:returns: JSON Data
	:raises: Exception 
	"""

	if (request.method != 'POST'):
		return err_GE002()

	form = MsgGetForm(request.POST)
	if (not form.is_valid()):
		return err_GE031(form)

	try:
		# Get/set up data for KMS.
		request.session['key'] = request.device_assn.secret
		ret_data = checkDicom(request, message_id, attachment_id, secret=form.cleaned_data['secret'])
		response = {
			'data': ret_data,
			'warnings': {},
		}
		return HttpResponse(content=json.dumps(response), mimetype='application/json')

	except KeyInvalidException:
		return err_GE021()


