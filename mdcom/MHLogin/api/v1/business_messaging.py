# -*- coding: utf-8 -*-
'''
Created on 2012-10-12

@author: mwang
'''
import inspect
import time

from django.conf import settings
from django.core.mail import mail_admins
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _
from pytz import timezone

from MHLogin.DoctorCom.Messaging.forms import ReferEditForm, MessageReferForm
from MHLogin.DoctorCom.Messaging.models import MessageBodyUserStatus, MessageRecipient, \
	MessageAttachment, MessageRefer, MessageCC
from MHLogin.DoctorCom.Messaging.utils import _get_refer_from_mbus, updateRefer,\
	read_message
from MHLogin.DoctorCom.Messaging.utils_new_message import createNewMessage, createNewADS,\
	sendMessageCheck
from MHLogin.KMS.exceptions import KeyInvalidException
from MHLogin.KMS.shortcuts import decrypt_cipherkey
from MHLogin.api.v1.errlib import err_GE002, err_GE031, err_GE021
from MHLogin.api.v1.forms_messaging import MsgListForm, MsgCompositionForm, MsgBatchIDForm,\
	MsgGetForm
from MHLogin.api.v1.utils import HttpJSONSuccessResponse, HttpJSONErrorResponse
from MHLogin.api.v1.utils_messaging import _get_attachment_filename, \
	getReceivedMessageListData, getSentMessageListData
from MHLogin.utils.errlib import err403
from MHLogin.utils.timeFormat import getCurrentTimeZoneForUser,\
	formatTimeSetting


def getReceivedMessagesLogic(request, return_python=False):
	"""
	Gets a list of the received message headers.

	If return_python is true, this will just return the object that would have
	been converted to JSON format.
	"""

	if (request.method != 'POST'):
		return err_GE002()
	form = MsgListForm(request.POST)
	if (not form.is_valid()):
		return err_GE031(form)
	data = getReceivedMessageListData(request.user, form.cleaned_data)

	if (return_python):
		return {
			'data': data,
			'warnings': {},
		}
	return HttpJSONSuccessResponse(data=data)


def getSentMessagesLogic(request, return_python=False):
	"""
	Gets a list of the received message headers.

	If return_python is true, this will just return the object that would have
	been converted to JSON format.
	"""

	if (request.method != 'POST'):
		return err_GE002()
	form = MsgListForm(request.POST)
	if (not form.is_valid()):
		return err_GE031(form)

	data = getSentMessageListData(request.user, form.cleaned_data)

	if (return_python):
		return {
			'data': data,
			'warnings': {},
		}
	return HttpJSONSuccessResponse(data=data)


def getMessageLogic(request, message_id, ss=None):
	if (request.method != 'POST'):
		return err_GE002()

	msgs = list(MessageBodyUserStatus.objects.filter(user=request.user,
					delete_flag=False, msg_body__message__uuid=message_id).
			order_by('-msg_body__message__send_timestamp').select_related(
				'msg_body', 'msg_body__message', 'msg_body__message__sender'))

	# Integrity check.
	if (len(msgs) > 1):
		# shouldn't be possible!
		mail_admins('Duplicate message ID', ' '.join(['server: ',
				settings.SERVER_ADDRESS, '\n',
				'The message id with uuid', message_id, 'has returned with',
				'more than one Message!\nAt: ',
				str(inspect.getfile(inspect.currentframe())), ':',
						str(inspect.currentframe().f_back.f_lineno)
			]))
	if (len(msgs) == 0):
		raise Http404

	local_tz = timezone(settings.TIME_ZONE)
	status_obj = msgs[0]

	body = None
	try:
		# Get/set up data for KMS.
		request.session['key'] = request.device_assn.secret
		body = read_message(request, status_obj.msg_body, ss=ss)
	except KeyInvalidException:
		return err_GE021()

	if not body:
		return err_GE021()
	current_user = request.mhluser
	current_user_mobile = current_user.mobile_phone
	msg = status_obj.msg_body.message
	recipients = MessageRecipient.objects.filter(message__uuid=message_id).\
		select_related('user').only('user__first_name', 'user__last_name')
	ccs = MessageCC.objects.filter(message__uuid=message_id).\
		select_related('user').only('user__first_name', 'user__last_name')

	attachments = MessageAttachment.objects.filter(message=msg)

	ccs = MessageCC.objects.filter(message__uuid=message_id).select_related('user').\
		only('user__first_name', 'user__last_name', 'message')
	user = request.mhluser
	local_tz = getCurrentTimeZoneForUser(user)
	data = {
			'body': body,
			'timestamp': formatTimeSetting(user, msg.send_timestamp, 
										local_tz),

			'sender': {
						'name': ' '.join([
								msg.sender.first_name, msg.sender.last_name]) \
									if msg.sender else "System Message",
						'id': msg.sender.id if msg.sender else 0,
					},
			'recipients': [{
						'name': ' '.join([
								u.user.first_name, u.user.last_name]),
						'id': u.user.id,
						} for u in recipients],
			'ccs': [{
						'name': ' '.join([
								u.user.first_name, u.user.last_name]),
						'id': u.user.id,
						} for u in ccs],
			'attachments': [
					{
						'id': att.uuid,
						'filename': _get_attachment_filename(request, att, ss=ss),
						'filesize': att.size,
						'suffix':att.suffix,
					} for att in attachments],
			'message_type': msg.message_type if msg.message_type else 'NM',
			'callback_number': msg.callback_number,
			'callback_available': settings.CALL_ENABLE and bool(msg.callback_number)
				and bool(current_user_mobile),
			'urgent': bool(msg.urgent),
			'resolution_flag': bool(msg._resolved_by_id),
			'refer': _get_refer_from_mbus(status_obj, logo_size="Large"),
			'thread_uuid': msg.thread_uuid
		}
	return HttpJSONSuccessResponse(data=data)


def getAttachmentLogic(request, message_id, attachment_id, ss=None):
	if (request.method != 'POST'):
		return err_GE002()

	attachment = get_object_or_404(MessageAttachment, message__uuid=message_id, uuid=attachment_id)
	message = attachment.message

	if ((message.sender and request.user.pk != message.sender.pk) and 
		not ((request.user.pk,) in message.recipients.values_list('id') or (request.user.pk,) 
			in message.ccs.values_list('id'))):
		return err403(request, err_msg="You don't seem to be a valid recipient for this file.")

	# Get/set up data for KMS.
	request.session['key'] = request.device_assn.secret
	try:
		clearkey = decrypt_cipherkey(request, attachment, ss=ss)
	except KeyInvalidException:
		return err_GE021()

	url = attachment.decrypt_url(request, key=clearkey)
	if (url[0:4] == 'file'):
		response = HttpResponse(content_type=attachment.content_type)
		attachment.get_file(request, response, key=clearkey)
		return response

	elif (url[0:4] == 'http'):
		# This is likely a fully qualified URL
		if (not attachment.encrypted):
			return HttpResponseRedirect(url)
		else:
			# Download and decrypt this attachment.
			pass
	else:
		raise Exception('A seemingly invalid URL has been stored: %s, for '
			'MessageAttachment %s.' % (url, attachment_id,))


def composeMessageLogic(request, recipients_together=True, ss=None):
	if (request.method != 'POST'):
		return err_GE002()
	form = MsgCompositionForm(request.POST)
	if (not form.is_valid()):
		return err_GE031(form)

	sender = request.user
	sender_role_user = request.role_user
	subject = form.cleaned_data['subject']
	body = form.cleaned_data['body']
	recipients = []
	form.cleaned_data['recipients']
	if 'recipients' in form.cleaned_data and len(form.cleaned_data['recipients']) > 0:
		recipients = form.cleaned_data['recipients']

	elif 'practice_recipients' in form.cleaned_data and \
			len(form.cleaned_data['practice_recipients']) > 0:
		recipients = form.cleaned_data['practice_recipients']

	ccs = []
	if 'ccs' in form.cleaned_data and len(form.cleaned_data['ccs']) > 0:
		ccs = form.cleaned_data['ccs']

	attachments = []
	if ('attachment' in request.FILES):
		attachments = request.FILES.getlist('attachment')

	attachment_count = len(attachments)
	if not sendMessageCheck(sender, attachment_count, recipients, ccs):
		return HttpJSONErrorResponse(errno='MS002')
	exist_attchments = None
	if 'message_id' in form.cleaned_data and form.cleaned_data['message_id']\
		and 'attachment_ids' in form.cleaned_data and \
			len(form.cleaned_data['attachment_ids']) > 0:
		exist_attchments = {
				"message_id": form.cleaned_data['message_id'],
				"attachment_ids": form.cleaned_data['attachment_ids']
			}
	exist_refer = None
	if 'message_id' in form.cleaned_data and form.cleaned_data['message_id'] \
		and 'refer_id' in form.cleaned_data and form.cleaned_data['refer_id']:
		exist_refer = {
				"message_id": form.cleaned_data['message_id'],
				"refer_id": form.cleaned_data['refer_id']
			}

	thread_uuid = None
	if 'thread_uuid' in form.cleaned_data and form.cleaned_data['thread_uuid']:
		thread_uuid = form.cleaned_data['thread_uuid']

	if recipients_together:
		createNewMessage(request, sender, sender_role_user, recipients, body,
					ccs=ccs, subject=subject, uploads=attachments,
					exist_attchments=exist_attchments,
					exist_refer=exist_refer, thread_uuid=thread_uuid, ss=ss)
	else:
		createNewADS(request, sender, sender_role_user, recipients, body,
					subject=subject, uploads=attachments)

	return HttpJSONSuccessResponse()


# At the moment, it's only used for partner api
# TODO, complete logic for mobile app using ss
def composeReferLogic(request, api_secret=None, ss=None):
	if (request.method != 'POST'):
		return err_GE002()

	form = MessageReferForm(request.POST, request.FILES)
	if (not form.is_valid()):
		return err_GE031(form)

	sender = request.user
	sender_role_user = request.role_user
	subject = u'Refer'
	body = form.cleaned_data['reason_of_refer']
	recipients = form.cleaned_data['user_recipients']
	attachments = []
	if ('attachments' in request.FILES):
		attachments = request.FILES.getlist('attachments')

	createNewMessage(request, sender, sender_role_user, recipients, body,
					ccs=None, subject=subject, uploads=attachments, file_data_list=None,
					refer_data=form.cleaned_data, api_secret=api_secret, ss=ss)
	return HttpJSONSuccessResponse()


def getReferPDFLogic(request, refer_id, ss=None):
	"""
	get_refer_pdf

	:param request: Request info
	:type request: django.core.handlers.wsgi.WSGIRequest
	:param refer_id: referall id
	:type refer_id: uuid
	:returns: django.http.HttpResponse -- the result in an HttpResonse object
	"""
	if (request.method != 'POST'):
		return err_GE002()
	form = MsgGetForm(request.POST)
	if (not form.is_valid()):
		return err_GE031(form)

	refer = get_object_or_404(MessageRefer, uuid=refer_id)

	message = refer.message
	if ((message.sender and request.user.pk != message.sender.pk) and 
		not ((request.user.pk,) in message.recipients.values_list('id') or 
			(request.user.pk,) in message.ccs.values_list('id'))):
		return err403(request, err_msg=_("You don't seem to be a valid recipient for this file."))

	# special for mobile app api
	# Get/set up data for KMS.
	request.session['key'] = request.device_assn.secret
	try:
		clearkey = decrypt_cipherkey(request, refer, ss=ss)
	except KeyInvalidException:
		return err_GE021()

	try:
		response = refer.get_file(request, key=clearkey)
		return response
	except Exception as e: 
		err_email_body = '\n'.join([
				('PDF file not exist!'),
				''.join(['Server: ', settings.SERVER_ADDRESS]),
				''.join(['Session: ', str(request.session.session_key)]),
				''.join(['Message: ', (u'PDF file not exist in media/refer/pdf')]),
				''.join(['Exception: ', str(e)]),
				''.join(['Exception data: ', str(e.args)]),
			])
		mail_admins(_('PDF folder not exist'), err_email_body)
		raise Exception(_('A seemingly invalid URL has been stored for Refer Pdf.'))


def updateReferLogic(request, refer_id):
	"""
	update_refer

	:param request: Recipient info
	:type request: django.core.handlers.wsgi.WSGIRequest
	:param refer_id: The refferal's id
	:type refer_id: uuid
	:returns: {
		'data': {},
		'warnings': {},
		}
	"""
	if (request.method != 'POST'):
		return err_GE002()
	form = ReferEditForm(request.POST)
	if (not form.is_valid()):
		return err_GE031(form)

	updateRefer(request, form, refer_id)
	return HttpJSONSuccessResponse()


def deleteMessageLogic(request, message_id):
	msgs = list(MessageBodyUserStatus.objects.filter(user=request.user, 
		delete_flag=False, msg_body__message__uuid=message_id))
	# Integrity check.
	if (len(msgs) > 1):
		# shouldn't be possible!
		mail_admins('Duplicate message ID', ' '.join(['server: ', 
				settings.SERVER_ADDRESS, '\n',
				'The message id with uuid', message_id, 'has returned with',
				'more than one Message!\nAt: ', 
				str(inspect.getfile(inspect.currentframe())), ':', 
					str(inspect.currentframe().f_back.f_lineno)
			]))
	elif (len(msgs) == 0):
		raise Http404

	status = msgs[0]
	status.delete_flag = True
	if (not status.delete_timestamp):
		status.delete_timestamp = int(time.time())
	status.save()
	return HttpJSONSuccessResponse()


def deleteMessagesLogic(request, delete_flag=True):
	if (request.method != 'POST'):
		return err_GE002()
	form = MsgBatchIDForm(request.POST)
	if (not form.is_valid()):
		return err_GE031(form)
	delete_timestamp = 0
	if delete_flag:
		delete_timestamp = int(time.time())
	message_ids = form.cleaned_data['message_ids']
	MessageBodyUserStatus.objects.filter(user=request.user, 
		delete_flag=not delete_flag, msg_body__message__uuid__in=message_ids).\
			update(delete_flag=delete_flag, delete_timestamp=delete_timestamp)
	return HttpJSONSuccessResponse()


def markMessageLogic(request, read_flag=True):
	if (request.method != 'POST'):
		return err_GE002()
	form = MsgBatchIDForm(request.POST)
	if (not form.is_valid()):
		return err_GE031(form)
	read_timestamp = 0
	if read_flag:
		read_timestamp = int(time.time())
	message_ids = form.cleaned_data['message_ids']
	MessageBodyUserStatus.objects.filter(user=request.user, 
		read_flag=not read_flag, msg_body__message__uuid__in=message_ids).\
			update(read_flag=read_flag, read_timestamp=read_timestamp)
	return HttpJSONSuccessResponse()
