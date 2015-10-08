
import json
import time
from pytz import timezone

from django.conf import settings
from django.core.mail import mail_admins
from django.http import HttpResponse, Http404
from django.template.loader import render_to_string
from django.utils.html import conditional_escape 
from django.utils.translation import ugettext as _

from MHLogin.KMS.exceptions import KeyInvalidException
from MHLogin.KMS.shortcuts import decrypt_object

from MHLogin.MHLUsers.utils import get_fullname_bystr

from MHLogin.DoctorCom.Messaging.forms import MessageFetchForm_Offset, \
	MessageFetchForm_Timestamp, UpdateMessageForm
from MHLogin.DoctorCom.Messaging.models import MessageBodyUserStatus, \
	MessageAttachment, MessageCC, CallbackLog, MessageRecipient, Message
from MHLogin.DoctorCom.Messaging.utils_msg_threading import get_msgs_for_threading, \
	get_name_from_list
from MHLogin.DoctorCom.Messaging.utils import _get_refer_from_mbus, sender_name_safe, \
	get_subject, replace_number, update_message_status, get_message_action_history

# Setting up logging
from MHLogin.utils.mh_logging import get_standard_logger 
from MHLogin.utils.templates import get_context
from django.db.models.query_utils import Q
from MHLogin.utils.timeFormat import formatTimeSetting, getCurrentTimeZoneForUser
from MHLogin.MHLUsers.utils import getCurrentUserMobile, getCurrentUserInfo

# Setting up logging
logger = get_standard_logger('%s/DoctorCom/Messaging/views_ajax.log' % 
	(settings.LOGGING_ROOT), 'DoctorCom.Messaging.views_ajax', settings.LOGGING_LEVEL)


def message_view(request, message_id, type):
	"""Process message view request:

	:param request: The HTTP message view request
	:type request: django.core.handlers.wsgi.WSGIRequest  
	:param message_id: The message id
	:type message_id: int  
	:returns: django.http.HttpResponse -- the JSON result in an HttpResonse object
	:raises: None 
	"""
	resolved = request.GET['resolved']
	thread_uuid = Message.objects.get(uuid=message_id).thread_uuid

	msgs = MessageBodyUserStatus.objects.filter(user=request.user, delete_flag=False, 
				msg_body__message__thread_uuid=thread_uuid).order_by(
					'-msg_body__message__send_timestamp').\
						select_related('msg_body', 'msg_body__message', 
									'msg_body__message__sender')\
						.extra(select={'sender_title':"SELECT MHLUsers_mhluser.title \
						FROM MHLUsers_mhluser INNER JOIN Messaging_message ON \
						MHLUsers_mhluser.user_ptr_id = Messaging_message.sender_id \
						INNER JOIN  Messaging_messagebody ON \
						Messaging_message.id = Messaging_messagebody.message_id \
						WHERE Messaging_messagebody.id = Messaging_messagebodyuserstatus.msg_body_id"})

	if (resolved == ''):
		pass
	elif str(resolved).lower() in ("true"):
		msgs = msgs.filter(msg_body__message__in=[m.msg_body.message 
					for m in msgs if m.msg_body.message.resolved_by != None])
	else:
		msgs = msgs.filter(msg_body__message__in=[m.msg_body.message 
					for m in msgs if m.msg_body.message.resolved_by == None])

	msgs.select_related('msg_body', 'msg_body__message', 'msg_body__message__sender',)
	msgs = list(msgs)

	context = get_context(request)
	user = request.session['MHL_Users']['MHLUser']

	local_tz = getCurrentTimeZoneForUser(user, current_practice=context['current_practice'])
	is_received = type == 'received'

	current_user = getCurrentUserInfo(request)
	current_user_mobile = getCurrentUserMobile(current_user)
	call_enable = bool(current_user_mobile) and settings.CALL_ENABLE

	msgs_list = []
	audio_list = []
	for status_obj in msgs:
		try:
			read_flag = status_obj.read_flag
			body = decrypt_object(request, status_obj.msg_body)
			# TODO, this function need to refactor, when get threading message list, 
			# don't need to decrypt every message body in the threading message.
			# When refactors, use following line while reading message body.
#			body = read_message(request, status_obj.msg_body)
			if not read_flag:
				status_obj.read_flag = read_flag
				status_obj.save()
		except KeyInvalidException:
			mail_admins(_('Message Body Decryption Error'), ''.join([
				('An error occurred decryption data for user '), request.user.username,
				(' on server '), settings.SERVER_ADDRESS, '.\n',
				('Message ID: '), message_id
				]))
		callbacks = CallbackLog.objects.filter(message=status_obj.msg_body.message).\
						order_by('time').values('time')
		callbacks = [
			{
				'timestamp': _get_system_time_as_tz(c['time'], 
							local_tz).strftime('%m/%d/%y %H:%M'),
				'caller_name': 'Joe Bloggs',
				'caller_id': 123,
			}
			for c in callbacks]

		msg_cc_maps = MessageCC.objects.filter(message=status_obj.msg_body.message).\
			select_related('user').extra(select={'title':'SELECT title FROM MHLUsers_mhluser \
			WHERE MHLUsers_mhluser.user_ptr_id = Messaging_message_ccs.user_id'})\
			.only('user__first_name', 'user__last_name', 'message')
		ccs = '; '.join([get_fullname_bystr(msg_cc_map.user.last_name,\
									msg_cc_map.user.first_name,msg_cc_map.title)\
														for msg_cc_map in msg_cc_maps])

		msg_to_maps = MessageRecipient.objects.filter(message=status_obj.msg_body.message).\
			select_related('user').extra(select={'title':'SELECT title FROM MHLUsers_mhluser \
			WHERE MHLUsers_mhluser.user_ptr_id = Messaging_message_recipients.user_id'})\
			.only('user__first_name', 'user__last_name', 'message')
		recipients = '; '.join([get_fullname_bystr(msg_to_map.user.last_name,\
										msg_to_map.user.first_name,msg_to_map.title)\
															for msg_to_map in msg_to_maps])

		to_recipient_ids = []
		msg_sender = status_obj.msg_body.message.sender
		msg_sender_id = None
		if msg_sender:
			msg_sender_id = msg_sender.id
			to_recipient_ids.append(str(msg_sender_id))
		for rec in msg_to_maps:
			if rec.user.id != request.user.id:
				to_recipient_ids.append(str(rec.user.id))
		cc_recipient_ids = []
		for cc in msg_cc_maps:
			cc_recipient_ids.append(str(cc.user.id))

		is_read = status_obj.read_flag
		user_id = request.user.id
		read_recipients = [r.id for r in  status_obj.msg_body.message.recipients.all()]
		read_ccs = [c.id for c in status_obj.msg_body.message.ccs.all()]
		if not is_read:
			if is_received:
				if user_id not in read_recipients + read_ccs:
					is_read = True
			else:
				if msg_sender_id != request.user.id:
					is_read = True

		is_sender = request.user.id == msg_sender_id
		if is_received and (request.user.id == msg_sender_id and 
						user_id in read_recipients + read_ccs):
			is_sender = False

		result = {
			'id':status_obj.msg_body.message.uuid,
			'sender':sender_name_safe(status_obj.msg_body.message,title=status_obj.sender_title),
			'sender_id':msg_sender_id,
			'thread_uuid':status_obj.msg_body.message.thread_uuid,
			'timestamp':formatTimeSetting(user,
				status_obj.msg_body.message.send_timestamp, local_tz),
			'subject':conditional_escape(status_obj.msg_body.message.subject),
			'body':replace_number(status_obj.msg_body.clear_data, call_enable),
			'answering_service':status_obj.msg_body.message.message_type == 'ANS',
			'callback_number': replace_number(
				status_obj.msg_body.message.callback_number, call_enable),
			'callbacks': callbacks,
			'urgent':status_obj.msg_body.message.urgent,
			'ccs':ccs,
			'recipients':recipients,
			'to_recipient_ids':','.join(to_recipient_ids),
			'cc_recipient_ids':','.join(cc_recipient_ids),
			'is_sender':is_sender,
			'is_resolved':status_obj.msg_body.message.resolved_by != None,
			'read': 'true' if is_read else ''
		}
		attachments = MessageAttachment.objects.filter(message=status_obj.msg_body.message)

		result["attachments"] = []
		for att in attachments:
			attach_dict = {'id': att.uuid,
					'suffix': att.suffix,
					'size': att.size,
					'metadata': att.metadata,
					'filename': att.decrypt_filename(request),
					'msgId': status_obj.msg_body.message.uuid
					}
			result["attachments"].append(attach_dict)
			if att.suffix and att.suffix.lower() in ['mp3', 'wav']:
				audio_list.append(attach_dict)
		result["refer"] = _get_refer_from_mbus(status_obj, call_enable=call_enable)
		result["action_history"] = get_message_action_history(
			status_obj.msg_body.message.id, user, time_zone=local_tz)

		msgs_list.append(result)
	context['msgs'] = msgs_list
	context['audio_list'] = audio_list
	context['type'] = type
	return HttpResponse(render_to_string('DoctorCom/Messaging/MessageBody.html', context))


def update_message(request, message_id):
	"""update_message request:

	:param request: The HTTP update message request
	:type request: django.core.handlers.wsgi.WSGIRequest  
	:param message_id: The message uuid
	:type message_id: uuid  
	:returns: django.http.HttpResponse -- the JSON result in an HttpResonse object
	:raises: None 
	"""
	if (request.method == 'GET'):
		request_data = request.GET
		form = UpdateMessageForm(request.GET)
	else:
		request_data = request.POST
		form = UpdateMessageForm(request.POST)

	if (not form.is_valid()):
		logger.error('%s: Invalid form data!' % (request.session.session_key,))
		result = {'error': 'Invalid form data'}
		response = HttpResponse(json.dumps(result), mimetype='application/json')
		response.status_code = 400
		return response

	context = get_context(request)
	user = request.session['MHL_Users']['MHLUser']
	local_tz = getCurrentTimeZoneForUser(user, current_practice=context['current_practice'])
	result = update_message_status(request.user, message_id, 
		request_data, is_treading=True, local_tz=local_tz)
	return HttpResponse(json.dumps(result))  # , mimetype='application/json')


def get_messages(request, type):
	"""get_messages request:

	:param request: The HTTP update message request
	:type request: django.core.handlers.wsgi.WSGIRequest  
	:param typ: The message id
	:type type: string
	:returns: django.http.HttpResponse -- the JSON result in an HttpResonse object
	:raises: None 
	"""
	if (type != 'Sent' and type != 'Received'):
		raise Http404()

	request_data = request.REQUEST
	offset_form = MessageFetchForm_Offset(request_data)
	timestamp_form = MessageFetchForm_Timestamp(request_data)

	offset_form_validity = offset_form.is_valid()
	timestamp_form_validity = timestamp_form.is_valid()
	if (not offset_form_validity and not timestamp_form_validity):
		raise Exception(_('Invalid request'))

	if (offset_form_validity):
		form = offset_form
	else:
		form = timestamp_form

	request_time = int(time.time()) - 1

	resolved = None
	if ('resolved' in request_data):
		resolved = form.cleaned_data['resolved']

	user = request.session['MHL_Users']['MHLUser']

	context = get_context(request)
	local_tz = getCurrentTimeZoneForUser(user, current_practice=context['current_practice'])

	count = 20
	offset = 0
	from_ts = None
	if (offset_form_validity):
		count = form.cleaned_data['count']
		offset = form.cleaned_data['offset']
	else:
		from_ts = form.cleaned_data['timestamp']

	is_received_msg = type == 'Received'
	msg_data = get_msgs_for_threading(request.user, from_ts=from_ts, count=count,
		resolved=resolved, is_received_msg=is_received_msg, offset=offset)

	msgs = [
		{
			'id': msg.uuid,
			'recipients': get_name_from_list(msg.recipients_list + msg.ccs_list),
			'sender': get_name_from_list(msg.sender_list),
			'sender_number':msg.sender_number,
			'sender_id':sender_pk_safe(msg),
			'subject':get_subject(msg.subject, msg.refer_status),
			'timestamp':formatTimeSetting(user, msg.send_timestamp, local_tz),
			'resolved': msg.resolution_flag,
			'last_resolved_by': msg.last_resolved_by,
			'last_resolution_timestamp': formatTimeSetting(user, 
				msg.last_resolution_timestamp, local_tz),
			'read':msg.read_flag,
			'attachments':msg.attachments,
			'urgent':msg.urgent,
			'message_type': msg.message_type,
			'callback_number': msg.callback_number,
			'refer': msg.refer_status,
			'thread_uuid':msg.thread_uuid,
		} for msg in msg_data['msgs']
	]

	return HttpResponse(json.dumps({
				'count': msg_data['query_count'],
				'msgs': msgs,
				'request_timestamp': request_time,
				'unreadMsgs': msg_data['unread_count']
			}))


def get_unread_count(request):
	"""get_unread_count request:
	:param request: The HTTP update message request
	:returns: django.http.HttpResponse -- the JSON result in an HttpResonse object
	"""
	user = request.user
	mbus = MessageBodyUserStatus.objects.filter(user=user, delete_flag=False,
			read_flag=False).select_related('msg_body', 'msg_body__message')
	mbus = mbus.filter(Q(msg_body__message__recipients=user) | Q(msg_body__message__ccs=user))
	mbus_read = MessageBodyUserStatus.objects.filter(read_flag=True)\
			.select_related('msg_body', 'msg_body__message')\
			.values_list('msg_body__message__id', flat=True)
	mbus = mbus.exclude(msg_body__message__id__in=list(mbus_read))
	count = mbus.count()
	return HttpResponse(json.dumps({'count': count}))


def sender_pk_safe(message):
	if (message.sender_id):
		return message.sender.pk
	else:
		return None


def _get_system_time_as_tz(time_obj, tz):
	"""_get_system_time_as_tz time_obj ,tz:
	:param time_obj: an object of datetime
	:param tz: timezone
	:return datetime
	"""
	if not time_obj:
		return None

	if not tz:
		return None

	if isinstance(tz, (str, unicode)):
		tz = timezone(tz)
	time_obj = time_obj.replace(tzinfo=timezone(settings.TIME_ZONE))
	return time_obj.astimezone(tz)

