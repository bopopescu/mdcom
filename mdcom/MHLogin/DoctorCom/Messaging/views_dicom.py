import json

from django.http import HttpResponseBadRequest, HttpResponse
from django.shortcuts import render_to_response, get_object_or_404

from MHLogin.DoctorCom.Messaging.forms import DicomCallingForm
from MHLogin.DoctorCom.Messaging.models import MessageAttachment, MessageAttachmentDicom
from MHLogin.DoctorCom.Messaging.utils_dicom import regenDicomAttachmentFile, \
	genDicomAttachmentFile, getDicomXML, getDicomJPG, getDicomInfo, checkDicom
from MHLogin.utils.templates import get_context


def dicom_calling(request):
	"""
	Java Dicom Server revoke this function.
	It saves converted jpg and xml files.

	:param request: The HTTP request
	:type request: django.core.handlers.wsgi.WSGIRequest  
		request must have keys: token,jpg_files,xml_files
	:returns: JSON data
	:raises: Exception 
	"""
	if (request.method == 'POST'):
		form = DicomCallingForm(request.POST, request.FILES)
		if not form.is_valid():
			result = {'errors': form.errors}
			return HttpResponseBadRequest(json.dumps(result), mimetype='application/json')
		token = form.cleaned_data['token']
		if ('jpg_files' not in request.FILES):
			result = {'errors': 'jpg_files is required.'}
			return HttpResponseBadRequest(json.dumps(result), mimetype='application/json')
		if ('xml_files' not in request.FILES):
			result = {'errors': 'xml_files is required.'}
			return HttpResponseBadRequest(json.dumps(result), mimetype='application/json')

		jpg_files = request.FILES.getlist('jpg_files')
		xml_files = request.FILES.getlist('xml_files')

		attachment = get_object_or_404(MessageAttachment, uuid=token)
		request.user = attachment.message.sender
		attachment_dicom = None
		try:
			attachment_dicom = MessageAttachmentDicom.objects.get(attachment=attachment)
			if not attachment_dicom.check_keys_for_users():
				regenDicomAttachmentFile(request, attachment_dicom, jpg_files, xml_files)
			else:
				if attachment_dicom.check_files():
					return HttpResponse(content=json.dumps({"success": True}), 
							mimetype='application/json')
				else:
					regenDicomAttachmentFile(request, attachment_dicom, jpg_files, xml_files)
		except MessageAttachmentDicom.DoesNotExist:
			genDicomAttachmentFile(request, attachment, jpg_files, xml_files)

		return HttpResponse(content=json.dumps({"success": True}), mimetype='application/json')


def dicom_view_xml(request, message_id, attachment_id):
	"""
	Handles download dicom xml request.

	:param request: The HTTP request
	:type request: django.core.handlers.wsgi.WSGIRequest  
	:param message_id: Message uuid
	:type message_id: uuid
	:param attachment_id: Attachment uuid
	:type attachment_id: uuid
	:returns: django.http.HttpResponse -- the result in an HttpResonse object
	:raises: Exception 
	"""
	return getDicomXML(request, message_id, attachment_id)


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
	return getDicomJPG(request, message_id, attachment_id, index)


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
	context = get_context(request)
	ret_context = getDicomInfo(request, message_id, attachment_id)
	context.update(ret_context)
	return render_to_response('DoctorCom/Messaging/DicomView.html', context)


def dicom_check(request, message_id, attachment_id):
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

	ret_data = checkDicom(request, message_id, attachment_id)
	return HttpResponse(content=json.dumps(ret_data), mimetype='application/json')

