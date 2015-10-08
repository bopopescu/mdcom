
import magic
import mimetypes
import os
import re
import thread
import uuid
import json

from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models.query_utils import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.utils.html import conditional_escape
from django.utils.translation import ugettext as _
from exceptions import InvalidRecipientException

from MHLogin.DoctorCom.Messaging.forms import MessageOptionsForm, MessageForm, MessageEditCheckForm
from MHLogin.DoctorCom.Messaging.models import MessageCC, MessageRefer, Message, \
	MessageAttachment, MessageBody, MessageRecipient
from MHLogin.DoctorCom.Messaging.utils import sender_name_safe,\
	get_format_subject
from MHLogin.DoctorCom.view_boxes import body_decryption_helper
from MHLogin.KMS import utils
from MHLogin.KMS.models import OwnerPublicKey
from MHLogin.KMS.shortcuts import encrypt_object
from MHLogin.MHLPractices.models import PracticeLocation
from MHLogin.MHLUsers.models import MHLUser, Office_Manager
from MHLogin.MHLUsers.utils import get_fullname
from MHLogin.utils import errlib, FileHelper
from MHLogin.utils.DicomHelper import sendToDicomServer
from MHLogin.utils.errlib import err403, err404
from MHLogin.utils.mh_logging import get_standard_logger
from MHLogin.utils.templates import get_context
from MHLogin.utils.timeFormat import getCurrentTimeZoneForUser, formatTimeSetting
from MHLogin.genbilling.models import hasPermissionToUse

# Setting up logging
logger = get_standard_logger('%s/DoctorCom/Messaging/views.log' % (settings.LOGGING_ROOT), 
							'DCom.Msgng.views', settings.LOGGING_LEVEL)
suffix_re = re.compile('\.([^.]+)$')


def message_edit_multi(request, message_id=None):
	context = get_context(request)
	context['MAX_UPLOAD_SIZE'] = settings.MAX_UPLOAD_SIZE
	context['ioerror'] = ''
	if(request.method == 'GET'):
		user_recipients = request.GET['user_recipients']
	else:
		user_recipients = request.POST['user_recipients']

	if not user_recipients:
		return HttpResponseRedirect('/')

	recipient_ids = []
	for item in user_recipients.split(','):
		recipient_ids.append(int(item))
	form_initial_data = {'recipients': None, 'user_recipients': user_recipients}
	context['user_recipient_name'] = '; '.join([' '.join([user.first_name, user.last_name]) 
						for user in MHLUser.objects.filter(pk__in=recipient_ids)]) 
	context['recipientsform'] = MessageOptionsForm(initial={'user_recipients': user_recipients})

	if (request.method == 'POST'):
		form = MessageForm(request.POST, request.FILES)
		if (form.is_valid()):
			logger.debug('Form is valid')
			rec_count = len(recipient_ids)
			for recipient in recipient_ids:
				# Build the message and body
				rec_count -= 1
				msg = Message(
						sender=request.user,
						sender_site=None,
						subject=form.cleaned_data['subject'],
					)
				msg.save()
				MessageRecipient(message=msg, user_id=recipient).save()
				msg_body = msg.save_body(form.cleaned_data['body'])
				attachments = save_attachments(request, context, msg, form, rec_count == 0)
				msg.send(request, msg_body, attachments)			
			return HttpResponseRedirect('/')
		else:
			logger.debug('Form is invalid')
			file_saved_names = request.POST.getlist('file_saved_name')
			file_display_names = request.POST.getlist('file_display_name')
			file_charsets = request.POST.getlist('file_charset')
			file_sizes = request.POST.getlist('file_size')	
			file_len = len(file_saved_names)
			file_list = [
					{
						'file_saved_name':file_saved_names[i],
						'file_display_name':file_display_names[i],
						'file_charset':file_charsets[i],
						'file_size':file_sizes[i],
					}
					for i in range(file_len)
				]

			context['file_list'] = file_list
			context['form'] = form
	if (not message_id and request.method == 'GET'):
		# clean temp files
		FileHelper.cleanTempFile()	
		context['form'] = MessageForm(initial=form_initial_data)
	elif(message_id):
		# Grab the message in question
		msg = Message.objects.get(uuid=message_id)
		# Check to ensure that the user has rights to mess with this message
		if (request.user != msg.owner):
			errlib.err403()

	return render_to_response('DoctorCom/Messaging/MessageMultiEditForm.html', context)


def save_attachments(request, context, msg, form, isDeleteFile=True):
	attachments = []
	file_saved_names = request.POST.getlist('file_saved_name')
	file_display_names = request.POST.getlist('file_display_name')
	file_charsets = request.POST.getlist('file_charset')
	file_sizes = request.POST.getlist('file_size')
	file_len = len(file_saved_names)

	if (file_len == 0):
		return attachments

	for i in range(file_len):
		file_saved_name = file_saved_names[i]
		file_display_name = file_display_names[i]

		try:
			decrypt_str = FileHelper.readTempFile(file_saved_name, 'rb', utils.get_user_key(request))
			attachment = encrypt_object(
				MessageAttachment,
				{
					'message': msg,
					'size': file_sizes[i],
					'encrypted': True,
				},
				opub=OwnerPublicKey.objects.get_pubkey(owner=request.user))

			attachment.encrypt_url(request, ''.join(['file://', attachment.uuid]))
			suffix = os.path.splitext(file_display_name)[1][1:]
			if (suffix):
				attachment.suffix = suffix.lower()
				(attachment.content_type, attachment.encoding) = mimetypes.guess_type(file_display_name)
				attachment.charset = file_charsets[i]
			else:
				m = magic.Magic(mime=True)
				attachment.content_type = m.from_buffer(decrypt_str)
				if(attachment.content_type == 'application/dicom'):
					attachment.suffix = "dcm"
					file_display_name += ".dcm"
				m = magic.Magic(mime_encoding=True)
				attachment.encoding = m.from_buffer(decrypt_str)

			attachment.encrypt_filename(request, file_display_name)
			attachment.encrypt_file(request, decrypt_str)

			attachment.save()
			if "dcm" == attachment.suffix:
				thread.start_new_thread(sendToDicomServer, (
					{"name": file_display_name, "token": attachment.uuid,
						"content": decrypt_str},))
			attachments.append(attachment)
			if isDeleteFile:
				FileHelper.deleteTempFile(file_saved_name)
		except (IOError):
			transaction.rollback()
			context['ioerror'] = True
			context['form'] = form
			return render_to_response('DoctorCom/Messaging/MessageEditForm.html', context)
	return attachments


def message_edit_check(request):
	valid = False
	if(request.method == 'POST'):
		form = MessageEditCheckForm(request.POST)
		if form.is_valid():
			manager_list = []
			if (form.cleaned_data['practice']):
				managers = Office_Manager.active_objects.filter(
						practice=form.cleaned_data['practice'])
				manager_list.extend(m.user.user.pk for m in managers)
			recipients, ccs = getFormatToAndCc(form.cleaned_data['recipients'],
						form.cleaned_data['ccs'], manager_list)

			len_att = 0
			try:
				len_att = int(form.cleaned_data['len_attachments'])
			except:
				pass
			valid = can_send_msg_with_attachments(request.user, 
				recipients, ccs, len_att) or 'Broker' in request.session['MHL_Users']
	return HttpResponse(json.dumps({'valid': valid}))


def message_edit(request, message_id=None):
	"""
	Handles message composition, editing, and drafts.

	:param request: The HTTP request
	:type request: django.core.handlers.wsgi.WSGIRequest  
	:param message_id: Message id
	:type message_id: int  
	:returns: django.http.HttpResponse -- the result in an HttpResonse object 
	:raises: InvalidRecipientException, Http404
	"""
	context = get_context(request)
	context['show_subscribe'] = False
	context['ioerror'] = ''
	recipients = []
	form_initial_data = {'recipients': None}
	current_site = None

	if ('Provider' in request.session['MHL_Users']):
		current_site = request.session['MHL_Users']['Provider'].current_site
	if ('OfficeStaff' in request.session['MHL_Users']):
		current_practice = request.session['MHL_Users']['OfficeStaff'].current_practice
	requestDataDict = request.GET
	if(request.method == 'POST'):
		requestDataDict = request.POST
	recipientsform = MessageOptionsForm(requestDataDict)

	if (recipientsform.is_valid()):
		data = recipientsform.cleaned_data
		if ('user_recipients' in recipientsform.cleaned_data and 
				recipientsform.cleaned_data['user_recipients']):
			form_initial_data['user_recipient'] = recipientsform.cleaned_data['user_recipients']
			if (type(form_initial_data['user_recipient']) is list):
				form_initial_data['user_recipient'] = form_initial_data['user_recipient'][0]
			context['user_recipient'] = MHLUser.objects.get(pk=form_initial_data['user_recipient'])
			user_recipients = MHLUser.objects.filter(
					pk__in=recipientsform.cleaned_data['user_recipients'])
			user_recipientst=[]
			for user_recipient in user_recipients:
				user_recipientst=[{
										'id':user_recipient.id,
										'fullname':get_fullname(user_recipient)
										}]
			context['user_recipients']=user_recipientst

			user_cc_recipients = MHLUser.objects.filter(
					pk__in=recipientsform.cleaned_data['user_cc_recipients'])
			user_cc_recipientst=[]
			for user_cc_recipient in user_cc_recipients:
				user_cc_recipientst=[{
										'id':user_cc_recipient.id,
										'fullname':get_fullname(user_cc_recipient)
										}]
			context['user_cc_recipients']=user_cc_recipientst

			if 'msg_prefix' in data and data['msg_prefix']:
				user_recipients = MHLUser.objects.filter(
					pk__in=recipientsform.cleaned_data['user_recipients'])
				user_cc_recipients = MHLUser.objects.filter(
					pk__in=recipientsform.cleaned_data['user_cc_recipients'])

		elif ('practice_recipients' in recipientsform.cleaned_data and
				recipientsform.cleaned_data['practice_recipients']):
			form_initial_data['practice_recipient'] = recipientsform.cleaned_data['practice_recipients']
			if (type(form_initial_data['practice_recipient']) is list):
				form_initial_data['practice_recipient'] = form_initial_data['practice_recipient'][0]
			context['practice_recipient'] = PracticeLocation.objects.get(
				pk=form_initial_data['practice_recipient'])

		if 'msg_id' in data and data['msg_id'] and 'msg_prefix' in data and data['msg_prefix']:
			origin_msg = Message.objects.get(uuid=data['msg_id'])
			if  data['msg_prefix'] == "RE":
				form_initial_data['subject'] = get_format_subject(
						origin_msg.subject, data['msg_prefix'])
			elif data['msg_prefix'] == "FW":
				origin_attachment = MessageAttachment.objects.filter(message=origin_msg)
				file_list = []
				for att in origin_attachment:
					f = att.get_content_file(request)
					file_name = FileHelper.generateTempFile(f, utils.get_user_key(request))
					file_list.append(
							{
								'file_saved_name': file_name,
								'file_display_name': att.decrypt_filename(request),
								'file_charset': att.charset,
								'file_size': att.size,
							})
				refer = MessageRefer.objects.filter(message=origin_msg)
				if refer:
					f = refer[0].decrypt_file(request)
					file_name = FileHelper.generateTempFile(f, utils.get_user_key(request))
					file_list.append(
							{
								'file_saved_name': file_name,
								'file_display_name': 'refer.pdf',
								'file_charset': '',
								'file_size': len(f)
							})

				context['file_list'] = file_list
				form_initial_data['subject'] = get_format_subject(
							origin_msg.subject, data['msg_prefix'])
				msg_body = MessageBody.objects.filter(message=origin_msg)[0]
				form_initial_data['body'] = get_text_from_messge(request, origin_msg,
							msg_body, context['current_practice'])
				data['msg_id'] = ''

#	else:
#		raise Http404

	data['user_recipients'] = ','.join(str(x) for x in data['user_recipients'] if x)
	data['practice_recipients'] = ','.join(str(x) for x in data['practice_recipients'] if x)
	context['recipientsform'] = MessageOptionsForm(initial=recipientsform.cleaned_data)

	if (request.method == 'POST'):
		form = MessageForm(request.POST, request.FILES)
		if (form.is_valid()):
			logger.debug('Form is valid')

			manager_list = []
			if(form.cleaned_data['practice_recipient']):
				managers = Office_Manager.active_objects.filter(
					practice=form.cleaned_data['practice_recipient'])
				manager_list.extend(m.user.user.pk for m in managers)

			recipients, ccs = getFormatToAndCc(form.cleaned_data['user_recipients'],
				form.cleaned_data['user_cc_recipients'], manager_list=manager_list)

			# Build the message and body
			thread_uuid = recipientsform.cleaned_data['thread_uuid'] if \
				recipientsform.cleaned_data['thread_uuid'] else uuid.uuid4().hex
			msg = Message(
					sender=request.user,
					sender_site=current_site,
					subject=form.cleaned_data['subject'],
					thread_uuid=thread_uuid,
				)
			msg.save()
			msg_body = msg.save_body(form.cleaned_data['body'])

			for recipient in recipients:
				MessageRecipient(message=msg, user_id=recipient).save()

			for cc in ccs:
				MessageCC(message=msg, user_id=cc).save()

			len_attachments = len(request.POST.getlist('file_saved_name'))
			if can_send_msg_with_attachments(request.user, recipients, ccs, len_attachments) \
				or 'Broker' in request.session['MHL_Users']:
				# Build the attachments
				attachments = save_attachments(request, context, msg, form)
				msg.send(request, msg_body, attachments)
				return HttpResponseRedirect('/')
			else:
				context['show_subscribe'] = True
				transaction.rollback()

		logger.debug('Form is invalid')
		file_saved_names = request.POST.getlist('file_saved_name')
		file_display_names = request.POST.getlist('file_display_name')
		file_charsets = request.POST.getlist('file_charset')
		file_sizes = request.POST.getlist('file_size')	
		file_len = len(file_saved_names)
		file_list = [
				{
					'file_saved_name':file_saved_names[i],
					'file_display_name':file_display_names[i],
					'file_charset':file_charsets[i],
					'file_size':file_sizes[i],
				}
				for i in range(file_len)
			]

		context['file_list'] = file_list
		context['form'] = form
	if (not message_id and request.method == 'GET'):
		# clean temp files
		FileHelper.cleanTempFile()	
		context['form'] = MessageForm(initial=form_initial_data)
	elif(message_id):
		# Grab the message in question
		msg = Message.objects.get(uuid=message_id)
		# Check to ensure that the user has rights to mess with this message
		if (request.user != msg.owner):
			errlib.err403(err_msg='')

	context['MAX_UPLOAD_SIZE'] = settings.MAX_UPLOAD_SIZE
	return render_to_response('DoctorCom/Messaging/MessageEditForm.html', context)


def message_view(request, message_id=None):
	"""
	Handles message view request.

	:param request: The HTTP request
	:type request: django.core.handlers.wsgi.WSGIRequest  
	:param message_id: Message id
	:type message_id: int  
	:returns: django.http.HttpResponse -- the result in an HttpResonse object 
	"""
	message = get_object_or_404(Message, uuid=message_id)
	msg_body = get_object_or_404(MessageBody, message=message)
	context = get_context(request)
	context['message'] = message
	context['body'] = body_decryption_helper(request, msg_body)
	return render_to_response('DoctorCom/Messaging/MessageView.html', context)


def download_attachment(request, message_id, attachment_id):
	"""
	Handles download attachment request.

	:param request: The HTTP request
	:type request: django.core.handlers.wsgi.WSGIRequest  
	:param message_id: Message id
	:type message_id: int  
	:param attachment_id: Attachment id
	:type attachment_id: int  
	:returns: django.http.HttpResponse -- the result in an HttpResonse object
	:raises: Exception 
	"""
	attachment = get_object_or_404(MessageAttachment, message__uuid=message_id, uuid=attachment_id)

	if (request.user != attachment.message.sender and not
			(request.user in attachment.message.recipients.all() or
				request.user in attachment.message.ccs.all())):
		return err403(request, err_msg=_("You don't seem to be a valid recipient for this file."))

	url = attachment.decrypt_url(request)
	if (url[0:4] == 'file'):
		try:
			content_type = attachment.content_type if attachment.content_type \
				else "application/octet-stream"
			response = HttpResponse(content_type=content_type)
			attachment.get_file(request, response)
			return response
		except(IOError):
			return err404(request)	

	elif (url[0:4] == 'http'):
		# This is likely a fully qualified URL
		if (not attachment.encrypted):
			return HttpResponseRedirect(url)
		else:
			# Download and decrypt this attachment.
			pass
	else:
		raise Exception(_('A seemingly invalid URL has been stored: %(url)s, for '
			'MessageAttachment %(attachment_id)s.') % {'url': url, 'attachment_id': attachment_id})


def check_attachment(request, message_id, attachment_id):
	"""
	Handles check attachment request.

	:param request: The HTTP request
	:type request: django.core.handlers.wsgi.WSGIRequest  
	:param message_id: Message id
	:type message_id: int  
	:param attachment_id: Attachment id
	:type attachment_id: int  
	:returns: django.http.HttpResponse -- the result in an HttpResonse object
	"""
	attachment = get_object_or_404(MessageAttachment, message__uuid=message_id, uuid=attachment_id)

	if (request.user != attachment.message.sender and not
			(request.user in attachment.message.recipients.all() or
				request.user in attachment.message.ccs.all())):
		return err403(request, err_msg=_("You don't seem to be a valid recipient for this file."))

	if os.path.exists('%s/attachments/%s' % (settings.MEDIA_ROOT, attachment.uuid,)):
		return HttpResponse("success")
	else:
		return err404(request)


def message_history(request):
	pass


def message_drafts(request):
	pass


def can_send_msg_with_attachments(user, recipients, ccs, len_att):
	if len_att == 0:
		return True

	if hasPermissionToUse(user, 'fsh_srv'):
		return True

	for recipient in recipients:
		if not hasPermissionToUse(recipient, 'fsh_srv'):
			if len_att > 1 or MessageAttachment.objects.filter(Q(
					message__recipients=recipient) | Q(message__ccs=recipient)).\
						exclude(message__sender=None).exists():
				return False

	for cc in ccs:
		if not hasPermissionToUse(cc, 'fsh_srv'):
			if len_att > 1 or MessageAttachment.objects.filter(Q(message__recipients=cc) | 
				Q(message__ccs=cc)).exclude(message__sender=None).exists():
				return False
	return True


def getFormatToAndCc(to_str, ccs_str, manager_list=None):
	manager_list = manager_list or []
	recipients, ccs = [], []
	for rec in to_str.split(','):
		if rec and int(rec) not in recipients:
			recipients.append(int(rec))
	for cc in ccs_str.split(','):
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


def get_text_from_messge(request, msg, msg_body, practice):
	user = request.session['MHL_Users']['MHLUser']
	local_tz = getCurrentTimeZoneForUser(user, current_practice=practice)

	msg_to_maps = MessageRecipient.objects.filter(message=msg).select_related('user').\
		only('user__first_name', 'user__last_name', 'message')
	to_list = '; '.join([' '.join([to.user.first_name, to.user.last_name]) for to in msg_to_maps])

	msg_cc_maps = MessageCC.objects.filter(message=msg).select_related('user').\
		only('user__first_name', 'user__last_name', 'message')
	ccs_list = '; '.join([' '.join([msg_cc_map.user.first_name, msg_cc_map.user.last_name]) 
						for msg_cc_map in msg_cc_maps])

	result = '\n\n\n---------------------------------------------------------------------------------------\n'
	result += _('From: ') + sender_name_safe(msg_body.message) + '\n'
	result += _('Date: ') + formatTimeSetting(user, msg.send_timestamp, local_tz) + '\n'
	if to_list:
		result += _('To: ') + to_list + '\n'
	if ccs_list:
		result += _('Cc: ') + ccs_list + '\n'
	result += _('Subject: ') + conditional_escape(msg_body.message.subject) + '\n'

	result += '\n' + msg_body.decrypt(request) + '\n'
	return result

