# -*- coding: utf-8 -*-
'''
Created on 2012-10-12

@author: mwang
'''

import mimetypes
import os
import re
import uuid
import thread
import magic

from django.conf import settings
from django.utils.translation import ugettext as _
from django.shortcuts import get_object_or_404
from django.db.models.query_utils import Q
from django.template.loader import render_to_string

from MHLogin.DoctorCom.Messaging.exceptions import InvalidRecipientException
from MHLogin.DoctorCom.Messaging.models import Message, MessageRecipient, \
	MessageAttachment, MessageRefer, MessageCC
from MHLogin.genbilling.models import hasPermissionToUse
from MHLogin.KMS.models import OwnerPublicKey
from MHLogin.KMS.shortcuts import decrypt_cipherkey, encrypt_object
from MHLogin.MHLUsers.models import MHLUser, Office_Manager
from MHLogin.utils import ImageHelper
from MHLogin.utils.storage import create_file
from MHLogin.utils.templates import get_context
from MHLogin.utils.admin_utils import mail_admins
from MHLogin.utils.DicomHelper import sendToDicomServer

suffix_re = re.compile('\.([^.]+)$')


def createNewMessage(request, sender, sender_role_user, recipients, body, ccs=None, subject=None,
	uploads=None, file_data_list=None, temporary_files_data=None, exist_attchments=None,
	exist_refer=None, refer_data=None, thread_uuid=None, ss=None):
	"""
	createNewMessage

	:param request: request
	:param sender: message's sender as auth_user
	:param sender_role_user: message's sender as Provider/Office Staff/Broker
	:param recipients: user_id for message's recipients (integer or integer list)
	:param body: message's content body
	:param ccs: user_id for message's ccs (integer or integer list)
	:param subject: messages subject
	:param uploads: uploads is from request.FILES
	:param file_data_list: files information to be stored in message (file information 
		dictionary list).  The element in the file_data_list likes
		[{'name':'','file_chunks':'','size':,'suffix':'','charset':},...]
	:param temporary_files_data: (reserved) temporary files information, structure like
		Example::
		{
		'file_saved_name': file saved name list,
		'file_display_name': file display name list,
		'file_charset': file charset list,
		'file_size': file size list,
		}
	:param exist_attchments: attachment information, structure like
		Example::
		{
		'message_id': message_id(used for validating the attachment),
		'attachment_ids': attachment_id list
		}
	:param exist_refer: used for forwarding refer pdf
		Example::
		{
		'message_id': message_id(used for validating the refer),
		'refer_id': refer_id
		}
	:param refer_data: refer information dictionary
	:param thread_uuid: is used for threading
	:param ss: sender's private key api_secret and ss are used for 
	:returns: Message
	:raises: Http404, KeyInvalidException
	"""
	# compose message and message body
	sender_site = None
	if sender_role_user and hasattr(sender_role_user, 'current_site'):
		sender_site = sender_role_user.current_site

	thread_uuid = thread_uuid if thread_uuid else uuid.uuid4().hex
	msg = Message(
			sender=sender,
			sender_site=sender_site,
			subject=subject,
			thread_uuid=thread_uuid,
			)
	msg.save()
	body = msg.save_body(body)

	# compose recipients and ccs
	if not isinstance(recipients, list):
		recipients = [recipients]
	if not isinstance(ccs, list):
		ccs = [ccs]
	recipients, ccs = getDistinctToAndCc(recipients, ccs)

	if recipients:
		for recipient in recipients:
			MessageRecipient(message=msg, user_id=recipient).save()
	if ccs:
		for cc in ccs:
			MessageCC(message=msg, user_id=cc).save()

	# compose upload attachment data
	attachments = saveAttachmentsUsingRequestFiles(request, msg, uploads)

	# compose attachment using data like [{'name':'','file_chunks':'','size':,'suffix':'','charset':},...]
	if file_data_list:
		for file_data in file_data_list:
			attachment = saveSingleAttachment(request, msg, file_data)
			attachments.append(attachment)

	# TODO: compose exist file it's in temporary directory
	#attachments.extend(saveAttachmentsUsingTemporaryFiles(request, msg, temporary_files_data))

	# compose exist file using exist attachment
	attachments.extend(saveAttachmentsUsingExistAttachments(request, msg, exist_attchments, ss))

	# compose exist refer pdf 
	attachments.extend(saveAttachmentsForForwardReferPdf(request, msg, exist_refer, ss))

	# compose refer data
	refers = createNewRefer(msg, request, sender, sender_role_user, refer_data=refer_data)

	msg.send(request, body, attachment_objs=attachments, refer_objs=refers)

	createReferFowarding(refers, request, sender, sender_role_user, 
						refer_data=refer_data, ss=ss)

	return msg


def createNewADS(request, sender, sender_role_user, recipients, body, 
	ccs=None, subject=None, uploads=None, file_data_list=None):
	"""
	createNewADS

	:param request: request
	:param sender: message's sender as auth_user
	:param sender_role_user: message's sender as Provider/Office Staff/Broker
	:param recipients: user_id for message's recipients (integer or integer list)
	:param body: message's content body
	:param ccs: user_id for message's ccs (integer or integer list)
	:param subject: message's subject
	:param uploads: files to be stored in message(file list)
	:param file_data_list: files information to be stored in message(file information dictionary list)
	:returns: Message(ADS) list
	"""
	ads = []
	if not isinstance(recipients, list):
		msg = createNewMessage(request, sender, sender_role_user, recipients, body, 
			ccs=ccs, subject=subject, uploads=uploads, file_data_list=file_data_list)
		ads.append(msg)
	for recip in recipients:
		msg = createNewMessage(request, sender, sender_role_user, recip, body, 
			ccs=ccs, subject=subject, uploads=uploads, file_data_list=file_data_list)
		ads.append(msg)
	return ads


def createNewRefer(msg, request, sender, sender_role_user, refer_data=None):
	"""
	createNewADS

	:param msg: message object which contain this refer
	:param request: request
	:param sender: message's sender as auth_user
	:param sender_role_user: message's sender as Provider/Office Staff/Broker
	:param refer_data: refer information dictionary
	:returns: MessageRefer list
	"""
	# compose refer data
	refers = []
	if refer_data:
		insurance_name = refer_data['insurance_name'].strip()
		insurance_id = refer_data['insurance_id'].strip()
		secondary_insurance_name = ''
		secondary_insurance_id = ''
		tertiary_insurance_name = ''
		tertiary_insurance_id = ''

		if insurance_name and insurance_id:
			secondary_insurance_name = refer_data['secondary_insurance_name'].strip()
			secondary_insurance_id = refer_data['secondary_insurance_id'].strip()
			if secondary_insurance_name and secondary_insurance_id:
				tertiary_insurance_name = refer_data['tertiary_insurance_name'].strip()
				tertiary_insurance_id = refer_data['tertiary_insurance_id'].strip()

		refer = encrypt_object(
				MessageRefer,
				{
					'message': msg,
					'first_name': refer_data['first_name'].strip(),
					'middle_name': refer_data['middle_name'].strip(),
					'last_name': refer_data['last_name'].strip(),
					'gender': refer_data['gender'],
					'date_of_birth': refer_data['date_of_birth'],
					'phone_number': refer_data['phone_number'],
					'alternative_phone_number': refer_data['alternative_phone_number'],
					'insurance_id': insurance_id,
					'insurance_name': insurance_name,
					'secondary_insurance_id': secondary_insurance_id,
					'secondary_insurance_name': secondary_insurance_name,
					'tertiary_insurance_id': tertiary_insurance_id,
					'tertiary_insurance_name': tertiary_insurance_name,
					'is_sendfax': refer_data['is_sendfax'],
					'status': 'NO',
				},
				opub=OwnerPublicKey.objects.get_pubkey(owner=request.user))
		context = get_context(request)
		getContextOfPractice(request, context, sender_role_user)
		context['referring_physician_name'] = ' '.join([
			request.user.first_name, request.user.last_name])
		context['dialogForm'] = refer_data
		generate_pdf(refer, request, context)
		refer.refer_pdf = refer.uuid
		if sender_role_user and sender_role_user.current_practice:
			refer.practice = sender_role_user.current_practice
		refer.save()
		refers.append(refer)
	return refers


def createReferFowarding(refers, request, sender, sender_role_user, 
						refer_data=None, ss=None):
	"""
	create refer's forwarding
	:param request: request
	:param sender: message's sender as auth_user
	:param sender_role_user: message's sender as Provider/Office Staff/Broker
	:param refer_data: refer information dictionary
	:param ss: sender's private key api_secret and ss are used for decrypting pdf file. 
	:returns: Message
	"""
	if refers:
		if not isinstance(refers, list):
			refers = [refers]
		for refer in refers:
			# forward refer pdf
			clearkey = decrypt_cipherkey(request, refer, ss=ss)
			pdf_data = refer.decrypt_file(request, key=clearkey)

			forward_recipients = refer_data['user_to_recipients']
			forward_ccs = refer_data['user_cc_recipients']

			if pdf_data and (forward_recipients or forward_ccs):
				file_data = {
						'name': _('Refer Forwarding') + '.pdf',
						'file_chunks': [pdf_data],
						'size': len(pdf_data),
						'charset': ''
					}
				forward_body = _("""
%s has forwarded you a refer, please see details in attachment.

Best,
DoctorCom
""") % ' '.join([request.user.first_name, request.user.last_name])
				forward_subject = u'Refer Forwarding'
				# refer_data must be None here, avoid infinite loop 
				# TODO, test this logic carefully, when implement refer feature for app.
				forward_recipients = forward_recipients.split(',') if forward_recipients else None
				forward_ccs = forward_ccs.split(',') if forward_ccs else None
				return createNewMessage(request, sender, sender_role_user, forward_recipients, 
						forward_body, ccs=forward_ccs, subject=forward_subject, 
							file_data_list=[file_data], refer_data=None)


def getContextOfPractice(request, context, user):
	"""
	getContextOfPractice

	:param request: Request info
	:type request: django.core.handlers.wsgi.WSGIRequest  
	:param context: Context info
	:type context: TODO  
	:returns: ???
	"""
	practice_photo = ImageHelper.DEFAULT_PICTURE['Practice']
	context['current_practice'] = ''
	context['current_practice_photo'] = practice_photo
	context['physician_phone_number'] = ''
	if user and user.user and user.user.mobile_phone:
		context['physician_phone_number'] = user.user.mobile_phone
	if user and user.current_practice:
		current_practice = user.current_practice
		context['current_practice'] = current_practice
		context['current_practice_photo'] = \
			ImageHelper.get_image_by_type(current_practice.practice_photo, 
						size="Middle", type='Practice') 


def generate_pdf(refer, request, context):
	"""
	generate_pdf

	:param refer: Refer info
	:type refer: TODO 
	:param request: The request info 
	:type request: django.core.handlers.wsgi.WSGIRequest  
	:param context: context
	:type context: TODO
	:returns: None -- Creates PDF file in refer/pdf directory
	"""
	try:
		from weasyprint import HTML
		# path contains leading / so use string join instead of path join
		img = ''.join([settings.INSTALLATION_PATH, context['current_practice_photo']]) 
		html = render_to_string('DoctorCom/Messaging/PreviewDialog.html', 
			{'pdf': True, 'practice_photo_path': img}, context)

		htmlobj = HTML(string=html)
		pdf = htmlobj.write_pdf() 

		encrypted_data = refer.encrypt_file(request, pdf)

		refer_pdf = '%s/refer/pdf' % (settings.MEDIA_ROOT,)
		if not os.path.exists(refer_pdf):
			os.makedirs(refer_pdf)		

		f = create_file('refer/pdf/%s' % refer.uuid)
		f.set_contents(encrypted_data)
		f.close()
	except IOError as e:
		err_email_body = '\n'.join([
				('PDF folder not exist!'),
				''.join(['Server: ', settings.SERVER_ADDRESS]),
				''.join(['Session: ', str(request.session.session_key)]),
				''.join(['Message: ', (u'PDF folder not exist: media/refer/pdf')]),
				''.join(['Exception: ', str(e)]),
				''.join(['Exception data: ', str(e.args)]),
			])
		mail_admins('PDF folder not exist', err_email_body)


def getFormatToAndCc(to_str, ccs_str, manager_list=None):
	manager_list = manager_list or []
	to_array = to_str.split(',')
	ccs_array = ccs_str.split(',')
	return getDistinctToAndCc(to_array, ccs_array, manager_list=manager_list)


def getDistinctToAndCc(to_array, ccs_array, manager_list=None):
	manager_list = manager_list or []
	recipients, ccs = [], []
	for rec in to_array:
		if rec and int(rec) not in recipients:
			recipients.append(int(rec))
	if ccs_array:
		for cc in ccs_array:
			if cc and int(cc) not in ccs and int(cc) not in recipients:
				ccs.append(int(cc))

	if manager_list:
		for rec in manager_list:
			if rec not in recipients:
				recipients.append(int(rec))

	for recipient in recipients:
		try:
			recipient = MHLUser.objects.get(pk=recipient)
		except MHLUser.DoesNotExist:
			raise InvalidRecipientException()
		if (not recipient.is_active):
			raise InvalidRecipientException()

	for cc in ccs:
		try:
			cc = MHLUser.objects.get(pk=cc)
		except MHLUser.DoesNotExist:
			raise InvalidRecipientException()
		if (not cc.is_active):
			raise InvalidRecipientException()
	return recipients, ccs


def get_attachment_filename(request, attachment, ss=None):
	clearkey = None
	if ss:
		clearkey = decrypt_cipherkey(request, attachment, ss=ss)
	return attachment.decrypt_filename(request, key=clearkey)


def saveSingleAttachment(request, msg, file_data):
	"""
	Save a single attachment

	:param request: request
	:param msg: message object which contain this attachment
	:param file_data: attachment information
		Example::
		file_data : {
		'name': file's name,
		'file_chunks': file's chunk data,
		'size': file's size,
		'suffix': file's extension name,
		'charset': file's charset
		}
	:returns: MessageAttachment
	"""
	name = file_data['name']
	file_chunks = file_data['file_chunks']
	size = file_data['size']
	suffix = None
	if 'suffix' in file_data:
		suffix = file_data['suffix']
	charset = file_data['charset']

	attachment = encrypt_object(
		MessageAttachment,
		{
			'message': msg,
			'size': size,
			'encrypted': True,
		},
		opub=OwnerPublicKey.objects.get_pubkey(owner=request.user))

	attachment.encrypt_url(request, ''.join(['file://', attachment.uuid]))
	if not suffix:
		suffix = os.path.splitext(name)[1][1:]

	if (suffix):
		attachment.suffix = suffix.lower()
		(attachment.content_type, attachment.encoding) = mimetypes.guess_type(name)
		attachment.charset = charset
	else:
		try:
			m = magic.Magic(mime=True)
			attachment.content_type = m.from_buffer(file_chunks)
			if(attachment.content_type == 'application/dicom'):
				attachment.suffix = "dcm"
				name += ".dcm"
			m = magic.Magic(mime_encoding=True)
			attachment.encoding = m.from_buffer(file_chunks)
		except magic.MagicException as e:
			err_email_body = '\n'.join([
					('magic.MagicException!'),
					''.join(['Server: ', settings.SERVER_ADDRESS]),
					''.join(['Session: ', str(request.session.session_key)]),
					''.join(['Exception: ', str(e)]),
					''.join(['Exception data: ', str(e.args)]),
				])
			mail_admins('magic.MagicException', err_email_body)

	attachment.encrypt_filename(request, name)
	attachment.encrypt_file(request, file_chunks)

	attachment.save()
	if "dcm" == attachment.suffix:
		if not isinstance(file_chunks, str):
			file_chunks = ''.join(file_chunks)
		thread.start_new_thread(sendToDicomServer, ({
			"name": name, "token": attachment.uuid, "content": file_chunks},))
	return attachment


def saveAttachmentsUsingRequestFiles(request, msg, uploads):
	"""
	Save attachments using file information from request.FILES

	:param request: request the key 'key' must be in request.session
	:param msg: message object which contain these attachments
	:param uploads: uploads is from request.FILES
	:returns: MessageAttachment list
	"""
	attachments = []
	if uploads:
		for upload in uploads:
			file_data = {
					'name': upload.name,
					'file_chunks': upload.chunks(),
					'size': upload.size,
					'charset': upload.charset
				}

			attachment = saveSingleAttachment(request, msg, file_data)
			attachments.append(attachment)
	return attachments


def saveAttachmentsForForwardReferPdf(request, msg, exist_refer, ss):
	"""
	Save attachments when user forward a exist refer manually.

	:param request: request the key 'key' must be in request.session
	:param msg: message object which contain these attachments
	:param exist_refer: used for forwarding refer pdf
		Example::
		{
		'message_id': message_id(used for validating the refer),
		'refer_id': refer_id
		}
	:param ss: sender's private key ss is used for decrypting exist 
		attachments for mobile app.
	:returns: MessageAttachment list
	"""
	attachments = []
	if exist_refer and msg:
		origin_message_id = exist_refer['message_id']
		refer_id = exist_refer['refer_id']
		refer = get_object_or_404(MessageRefer, uuid=refer_id, message__uuid=origin_message_id)
		clearkey = None
		if ss:
			clearkey = decrypt_cipherkey(request, refer, ss=ss)
		decrypt_file_str = refer.decrypt_file(request, key=clearkey)
		file_data = {
				'name': 'refer.pdf',
				'file_chunks': decrypt_file_str,
				'size': len(decrypt_file_str),
				'charset': ''
			}

		attachment = saveSingleAttachment(request, msg, file_data)
		attachments.append(attachment)
	return attachments


def saveAttachmentsUsingTemporaryFiles(request, msg, temporary_files_data):
	"""
	Save attachments using files in the temporary directory 
	(message forwarding can use this function)

	:param request: key 'key' must be in request.session
	:param msg: message object which contain these attachments
	:param temporary_files_data: temporary files information, structure like
		Example::
		{
		'file_saved_name': file saved name list,
		'file_display_name': file display name list,
		'file_charset': file charset list,
		'file_size': file size list,
		}
		'file_saved_name','file_display_name','file_charset','file_size' must have same length.
	:returns: MessageAttachment list
	:raises: Http404, KeyInvalidException
	"""
	attachments = []
	# compose exist file using exist attachment
	if temporary_files_data:
		# TODO
		pass
	return attachments


def saveAttachmentsUsingExistAttachments(request, msg, exist_attchments, ss):
	"""
	save attachments using exist attachments(message forwarding can use this function)

	:param request: key 'key' must be in request.session
	:param msg: message object which contain these attachments
	:param exist_attchments: attachment information, structure like
		Example::
		{
		'message_id': message_id(used for validating the attachment),
		'attachment_ids': attachment_id list
		}
	:param ss: senders private key ss is used for decrypting exist attachments for mobile app.
	:returns: MessageAttachment list
	:raises: Http404, KeyInvalidException
	"""
	attachments = []
	# compose exist file using exist attachment
	if exist_attchments:
		message_id = exist_attchments['message_id']
		attachment_ids = exist_attchments['attachment_ids']
		for attachment_id in attachment_ids:
			attachment = get_object_or_404(MessageAttachment, 
				message__uuid=message_id, uuid=attachment_id)
			clearkey = None
			if ss:
				clearkey = decrypt_cipherkey(request, attachment, ss=ss)

			content = attachment.get_content_file(request, key=clearkey)
			file_name = get_attachment_filename(request, attachment, ss)
			file_data = {
					'name': file_name,
					'file_chunks': [content],
					'size': attachment.size,
					'charset': attachment.charset
				}

			attachment = saveSingleAttachment(request, msg, file_data)
			attachments.append(attachment)
	return attachments


# TODO, clean same name funtion in the MHLogin.DoctorCom.Messaging.views.py
def can_send_msg_with_attachments(user, recipients, ccs, len_att):
	if len_att == 0:
		return True

	if hasPermissionToUse(user, 'fsh_srv'):
		return True

	for recipient in recipients:
		if not hasPermissionToUse(recipient, 'fsh_srv'):
			if len_att > 1 or MessageAttachment.objects.filter(Q(message__recipients=recipient) |
					Q(message__ccs=recipient)).exclude(message__sender=None).exists():
				return False

	for cc in ccs:
		if not hasPermissionToUse(cc, 'fsh_srv'):
			if len_att > 1 or MessageAttachment.objects.filter(Q(message__recipients=cc) |
					Q(message__ccs=cc)).exclude(message__sender=None).exists():
				return False
	return True


def sendMessageCheck(sender, attachment_count, recipients, ccs, practice_id=None, sender_is_broker=False):
	"""
	sendMessageCheck
		check can send message or not

	:param sender: message's sender, is an instance of MHLUser
	:param count_att: count of attachments

	:param recipients: message's recipients, is a (MHLUser's)id list.
	:param ccs: message's ccs, is a (MHLUser's)id list.

	:param practice_id: is used for sending message to practice.
	:param sender_is_broker: message's sender is a broker, or not.
			if message's sender is a broker, he can send message.
	"""

	manager_user_list = []
	if practice_id:
		managers = Office_Manager.active_objects.filter(practice=practice_id)
		manager_user_list.extend(m.user.user.pk for m in managers)

	recipients, ccs = getDistinctToAndCc(recipients, ccs, manager_user_list)
	return can_send_msg_with_attachments(sender, recipients, ccs, attachment_count) or sender_is_broker
