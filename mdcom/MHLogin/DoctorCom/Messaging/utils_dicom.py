
import thread
import StringIO
import xml.etree.ElementTree as ET

from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _
from django.http import Http404

from MHLogin.DoctorCom.Messaging.models import MessageAttachment, MessageAttachmentDicom
from MHLogin.utils.DicomHelper import sendToDicomServer
from MHLogin.utils.errlib import err403
from MHLogin.KMS.shortcuts import encrypt_object, decrypt_cipherkey
from MHLogin.KMS.models import OwnerPublicKey
from MHLogin.DoctorCom.Messaging.utils_new_message import get_attachment_filename


def getDicomInfo(request, message_id, attachment_id, 
				dicom_jpg_func_name='MHLogin.DoctorCom.Messaging.views_dicom.dicom_view_jpg',
				secret=None):
	"""
	Handles dicom viewer.

	:param request: The HTTP request
	:type request: django.core.handlers.wsgi.WSGIRequest  
	:param message_id: Message uuid
	:type message_id: uuid
	:param attachment_id: Attachment uuid
	:type attachment_id: uuid
	:param dicom_jpg_func_name: function full path for getting dicom jpg file.
	:type dicom_jpg_func_name: string
	:param secret: secret for decrypting jpg(used for app).
	:type secret: string
	:returns: dict
	:raises: Exception 
	"""
	attachment = get_object_or_404(MessageAttachment, message__uuid=message_id, uuid=attachment_id)
	attachment_dicom = get_object_or_404(MessageAttachmentDicom, attachment=attachment)
	message = attachment.message

	if ((message.sender and request.user.pk != message.sender.pk) and
		not ((request.user.pk,) in message.recipients.values_list('id') or
			(request.user.pk,) in message.ccs.values_list('id'))):
		return err403(request, err_msg=_("You don't seem to be a valid recipient for this file."))

	clearkey = None
	if secret:
		# request must has the right 'key' value in session
		clearkey = decrypt_cipherkey(request, attachment_dicom, ss=secret)

	dicom_xml_string = attachment_dicom.get_xml_content(request, 0, key=clearkey)
	jpg_count = attachment_dicom.jpg_count
	xml = StringIO.StringIO(dicom_xml_string)
	doc = ET.parse(xml)

	context = {}
	context["jpgs"] = [{'index': i, 
		'url': reverse(dicom_jpg_func_name, 
			kwargs={'message_id': message_id, 'attachment_id':attachment_id, 'index':i})
	} for i in xrange(jpg_count)] if jpg_count else []

	context["jpg_count"] = jpg_count
	context["message_id"] = message_id
	context["attachment_id"] = attachment_id
	context["patient"] = {
			"name": getDicomInfoFromXML(doc, "00100010"),
			"id": getDicomInfoFromXML(doc, "00100020"),
			"birthday": getDicomInfoFromXML(doc, "00100030"),
			"sex": getDicomInfoFromXML(doc, "00100040"),
			"weight": getDicomInfoFromXML(doc, "00101030"),
		}
	acq_date = getDicomInfoFromXML(doc, "00080022")
	acquisition_date = acq_date[:4] + '-' + acq_date[4:6] + '-' + acq_date[6:8] \
		if 8 == len(acq_date) else acq_date
	acq_time = getDicomInfoFromXML(doc, "00080032")
	acquisition_time = acq_time[:2] + ':' + acq_time[2:4] + ':' + acq_time[4:6] \
		if 13 == len(acq_time) else acq_time

	context["dcm"] = {
		"file_name": get_attachment_filename(request, attachment, ss=secret),
		"acquisition_date": acquisition_date,
		"acquisition_time": acquisition_time,
		"institution_name": getDicomInfoFromXML(doc, "00080080"),
		"station_name": getDicomInfoFromXML(doc, "00081010"),
		"study_id": getDicomInfoFromXML(doc, "00200010"),
		"study_description": getDicomInfoFromXML(doc, "00081030"),
		"series_number": getDicomInfoFromXML(doc, "00200011"),
		"series_description": getDicomInfoFromXML(doc, "0008103E"),
		"slice_thickness": getDicomInfoFromXML(doc, "00180050"),
		"slice_location": getDicomInfoFromXML(doc, "00201041"),
	}

	return context


def getDicomXML(request, message_id, attachment_id, secret=None):
	"""
	Handles download dicom xml request.

	:param request: The HTTP request
	:type request: django.core.handlers.wsgi.WSGIRequest  
	:param message_id: Message uuid
	:type message_id: uuid  
	:param attachment_id: Attachment uuid
	:type attachment_id: uuid
	:param index: index of dicom jpg
	:type index: int
	:param secret: secret for decrypting jpg(used for app).
	:type secret: string
	:returns: django.http.HttpResponse -- the result in an HttpResonse object
	:raises: Exception 
	"""

	attachment = get_object_or_404(MessageAttachment, message__uuid=message_id, uuid=attachment_id)
	attachment_dicom = get_object_or_404(MessageAttachmentDicom, attachment=attachment)
	message = attachment.message

	if ((message.sender and request.user.pk != message.sender.pk) and
		not ((request.user.pk,) in message.recipients.values_list('id') or
			(request.user.pk,) in message.ccs.values_list('id'))):
		return err403(request, err_msg=_("You don't seem to be a valid recipient for this file."))

	clearkey = None
	if secret:
		# request must has the right 'key' value in session
		clearkey = decrypt_cipherkey(request, attachment_dicom, ss=secret)

	return attachment_dicom.get_dicom_xml_to_response(request, 0, key=clearkey)


def getDicomJPG(request, message_id, attachment_id, index, secret=None):
	"""
	Handles download dicom jpg request.

	:param request: The HTTP request
	:type request: django.core.handlers.wsgi.WSGIRequest  
	:param message_id: Message uuid
	:type message_id: uuid  
	:param attachment_id: Attachment uuid
	:type attachment_id: uuid
	:param index: index of dicom jpg
	:type index: int
	:param secret: secret for decrypting jpg(used for app).
	:type secret: string
	:returns: django.http.HttpResponse -- the result in an HttpResonse object
	:raises: Exception 
	"""
	attachment = get_object_or_404(MessageAttachment, message__uuid=message_id, uuid=attachment_id)
	attachment_dicom = get_object_or_404(MessageAttachmentDicom, attachment=attachment)
	if int(index) >= attachment_dicom.jpg_count:
		raise Http404

	message = attachment.message

	if ((message.sender and request.user.pk != message.sender.pk) and
		not ((request.user.pk,) in message.recipients.values_list('id') or
			(request.user.pk,) in message.ccs.values_list('id'))):
		return err403(request, err_msg=_("You don't seem to be a valid recipient for this file."))

	clearkey = None
	if secret:
		# request must has the right 'key' value in session
		clearkey = decrypt_cipherkey(request, attachment_dicom, ss=secret)

	index = int(index)
	return attachment_dicom.get_dicom_jpg_to_response(request, index, key=clearkey)


def checkDicom(request, message_id, attachment_id, secret=None):
	"""
	Check dicom jpg exsit or not.

	:param request: The HTTP request
	:type request: django.core.handlers.wsgi.WSGIRequest  
	:param message_id: Message uuid
	:type message_id: uuid
	:param attachment_id: Attachment uuid
	:type attachment_id: uuid
	:param secret: secret for decrypting jpg(used for app).
	:type secret: string
	:returns: JSON Data
	:raises: Exception 
	"""
	attachment = get_object_or_404(MessageAttachment, message__uuid=message_id, uuid=attachment_id)
	exist = True

	try:
		attachment_dicom = MessageAttachmentDicom.objects.get(attachment=attachment)
		exist = attachment_dicom.check_files() and attachment_dicom.check_keys_for_users()
	except MessageAttachmentDicom.DoesNotExist:
		exist = False

	send_if_not_exist = False
	if "send_if_not_exist" in request.POST:
		send_if_not_exist = True

	if send_if_not_exist and not exist:
		clearkey = None
		if secret:
			# request must has the right 'key' value in session
			clearkey = decrypt_cipherkey(request, attachment, ss=secret)
		file_display_name = get_attachment_filename(request, attachment, ss=secret)
		decrypt_str = attachment.get_content_file(request, key=clearkey)
		thread.start_new_thread(sendToDicomServer, 
			({"name": file_display_name, "token": attachment.uuid, "content": decrypt_str},))

	return {"exist": exist}


def getDicomInfoFromXML(doc, attr_tag):
	ele = doc.findall('.//attr[@tag="%s"]' % (attr_tag))
	return ele[0].text if ele and len(ele) > 0 else ''


def genDicomAttachmentFile(request, attachment, jpg_files, xml_files):
	attachment_dicom = encrypt_object(
		MessageAttachmentDicom,
		{
			'attachment': attachment,
			'jpg_count': len(jpg_files) if jpg_files and len(jpg_files) > 0 else 0,
			'xml_count': len(xml_files) if xml_files and len(xml_files) > 0 else 0,
		},
		opub=OwnerPublicKey.objects.get_pubkey(owner=request.user))
	attachment_dicom.gen_keys_for_users(request)
	attachment_dicom.encrypt_jpgs(request, jpg_files)
	attachment_dicom.encrypt_xmls(request, xml_files)
	return attachment_dicom


def regenDicomAttachmentFile(request, attachment_dicom, jpg_files, xml_files):
	attachment_dicom.regen_keys_for_users(request)
	attachment_dicom.encrypt_jpgs(request, jpg_files)
	attachment_dicom.encrypt_xmls(request, xml_files)

