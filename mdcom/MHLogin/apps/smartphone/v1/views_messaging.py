
import inspect
import json
import time

from django.conf import settings
from django.db.models.query import QuerySet
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _

from MHLogin.MHLUsers.utils import get_fullname_bystr
from MHLogin.DoctorCom.Messaging.forms import ReferEditForm, MessageReferForm,\
	UpdateMessageForm
from MHLogin.DoctorCom.Messaging.models import MessageBodyUserStatus, \
	MessageRecipient, MessageAttachment, MessageRefer, MessageCC,\
	MessageActionHistory
from MHLogin.DoctorCom.Messaging.utils import _get_refer_from_mbus, updateRefer, read_message,\
	update_message_status, get_message_action_history, render_action_histories
from MHLogin.DoctorCom.Messaging.utils_new_message import createNewMessage, \
	get_attachment_filename, sendMessageCheck
from MHLogin.KMS.exceptions import KeyInvalidException
from MHLogin.KMS.shortcuts import decrypt_cipherkey
from MHLogin.apps.smartphone.v1.decorators import AppAuthentication
from MHLogin.apps.smartphone.v1.errlib import err_GE002, err_GE021, err_GE031,\
	err_IN003
from MHLogin.apps.smartphone.v1.forms_messaging import MsgListForm, MsgGetForm, \
	MsgCompositionForm, MsgCompositionCheckForm, GetMsgDetailsForm
from MHLogin.apps.smartphone.v1.utils_messaging import rx_message_list_data, \
	tx_message_list_data
from MHLogin.utils.errlib import err403
from MHLogin.utils.timeFormat import formatTimeSetting, getCurrentTimeZoneForUser
from MHLogin.utils.admin_utils import mail_admins

@AppAuthentication
def rx_message_list(request, return_python=False):
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

	from_timestamp = None
	if ('from_timestamp' in form.cleaned_data):
		from_timestamp = form.cleaned_data['from_timestamp']
	to_timestamp = None
	if ('to_timestamp' in form.cleaned_data):
		to_timestamp = form.cleaned_data['to_timestamp']
	count = None
	if ('count' in form.cleaned_data):
		count = form.cleaned_data['count']
	resolved = None
	if ('resolved' in request.POST):
		resolved = form.cleaned_data['resolved']
	read = None
	if ('read' in request.POST):
		read = form.cleaned_data['read']
	exclude_id = None
	if ('exclude_id' in form.cleaned_data):
		exclude_id = form.cleaned_data['exclude_id']

	is_threading = False
	if 'is_threading' in form.cleaned_data:
		is_threading = form.cleaned_data['is_threading']

	thread_uuid = None
	if 'thread_uuid' in form.cleaned_data:
		thread_uuid = form.cleaned_data['thread_uuid']

	use_time_setting = False
	if 'use_time_setting' in form.cleaned_data:
		use_time_setting = form.cleaned_data['use_time_setting']

	response = {
		'data': rx_message_list_data(request, from_timestamp, to_timestamp, 
							count, resolved, read, exclude_id, is_threading=is_threading, 
							use_time_setting=use_time_setting, thread_uuid=thread_uuid),
		'warnings': {},
	}

	if (return_python):
		return response
	return HttpResponse(content=json.dumps(response), mimetype='application/json')


@AppAuthentication
def tx_message_list(request, return_python=False):
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

	from_timestamp = None
	if ('from_timestamp' in form.cleaned_data):
		from_timestamp = form.cleaned_data['from_timestamp']
	to_timestamp = None
	if ('to_timestamp' in form.cleaned_data):
		to_timestamp = form.cleaned_data['to_timestamp']

	count = None
	if ('count' in form.cleaned_data):
		count = form.cleaned_data['count']
	resolved = None
	if ('resolved' in request.POST):
		resolved = form.cleaned_data['resolved']

	exclude_id = None
	if ('exclude_id' in form.cleaned_data):
		exclude_id = form.cleaned_data['exclude_id']

	is_threading = False
	if 'is_threading' in form.cleaned_data:
		is_threading = form.cleaned_data['is_threading']

	thread_uuid = None
	if 'thread_uuid' in form.cleaned_data:
		thread_uuid = form.cleaned_data['thread_uuid']

	use_time_setting = False
	if 'use_time_setting' in form.cleaned_data:
		use_time_setting = form.cleaned_data['use_time_setting']

	response = {
		'data': tx_message_list_data(request, from_timestamp, to_timestamp, 
					count, resolved, exclude_id, is_threading=is_threading, 
					use_time_setting=use_time_setting, thread_uuid=thread_uuid),
		'warnings': {},
	}

	if (return_python):
		return response
	return HttpResponse(content=json.dumps(response), mimetype='application/json')


@AppAuthentication
def get_message(request, message_id):
	if (request.method != 'POST'):
		return err_GE002()
	form = MsgGetForm(request.POST)
	if (not form.is_valid()):
		return err_GE031(form)

	msgs = list(MessageBodyUserStatus.objects.filter(user=request.user,
					delete_flag=False, msg_body__message__uuid=message_id)
			.extra(select={'sender_title':"SELECT MHLUsers_mhluser.title \
				FROM MHLUsers_mhluser INNER JOIN Messaging_message ON \
				MHLUsers_mhluser.user_ptr_id = Messaging_message.sender_id \
				INNER JOIN  Messaging_messagebody ON \
				Messaging_message.id = Messaging_messagebody.message_id \
				WHERE Messaging_messagebody.id = Messaging_messagebodyuserstatus.msg_body_id"}).
			order_by('-msg_body__message__send_timestamp').select_related(
				'msg_body', 'msg_body__message', 'msg_body__message__sender'))\

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

	status_obj = msgs[0]

	# Get/set up data for KMS.
	request.session['key'] = request.device_assn.secret
	ss = form.cleaned_data['secret']

	current_user = request.role_user
	current_user_mobile = current_user.user.mobile_phone
	try:
		read_message(request, status_obj.msg_body, ss=ss)
	except KeyInvalidException:
		return err_GE021()
	msg = status_obj.msg_body.message
	recipients = MessageRecipient.objects.filter(message__uuid=message_id).\
		select_related('user').extra(select={'title':'SELECT title FROM MHLUsers_mhluser \
			WHERE MHLUsers_mhluser.user_ptr_id = Messaging_message_recipients.user_id'}).\
		only('user__first_name', 'user__last_name')

	attachments = MessageAttachment.objects.filter(message=msg)

	ccs = MessageCC.objects.filter(message__uuid=message_id).select_related('user').\
		extra(select={'title':'SELECT title FROM MHLUsers_mhluser \
			WHERE MHLUsers_mhluser.user_ptr_id = Messaging_message_ccs.user_id'}).\
		only('user__first_name', 'user__last_name', 'message')

	use_time_setting = False
	if 'use_time_setting' in request.POST and request.POST['use_time_setting'] == 'true':
		use_time_setting = True
	user = request.user
	local_tz = getCurrentTimeZoneForUser(user)
	action_history = get_message_action_history(status_obj.msg_body.message.id)
	response = {
		'data': {
				'body': status_obj.msg_body.clear_data,
				'timestamp': formatTimeSetting(user, msg.send_timestamp, 
										local_tz, use_time_setting),
				'send_timestamp': msg.send_timestamp,
				'sender': {
							'name': get_fullname_bystr(msg.sender.last_name,msg.sender.first_name,status_obj.sender_title)\
										if msg.sender else "System Message",
							'id': msg.sender.id if msg.sender else 0,
						},
				'recipients': [{
							'name': get_fullname_bystr(u.user.last_name,u.user.first_name,u.title),
							'id': u.user.id,
							} for u in recipients],
				'ccs': [{
							'name': get_fullname_bystr(u.user.last_name,u.user.first_name,u.title),
							'id': u.user.id,
							} for u in ccs],
				'attachments': [
						{
							'id': att.uuid,
							'filename': get_attachment_filename(request, att, ss),
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
				'thread_uuid': msg.thread_uuid,
				'action_history': action_history,
				'action_history_count': len(action_history)
			},
		'warnings': {},
	}

	return HttpResponse(content=json.dumps(response), mimetype='application/json')


@AppAuthentication
def get_message_details(request):
	if (request.method != 'POST'):
		return err_GE002()
	form = GetMsgDetailsForm(request.POST)
	if (not form.is_valid()):
		return err_GE031(form)

	message_uuids = form.cleaned_data['message_uuids']

	msgss = list(MessageBodyUserStatus.objects.filter(user=request.user,
					delete_flag=False, msg_body__message__uuid__in=message_uuids)
			.extra(select={'sender_title':"SELECT MHLUsers_mhluser.title \
				FROM MHLUsers_mhluser INNER JOIN Messaging_message ON \
				MHLUsers_mhluser.user_ptr_id = Messaging_message.sender_id \
				INNER JOIN  Messaging_messagebody ON \
				Messaging_message.id = Messaging_messagebody.message_id \
				WHERE Messaging_messagebody.id = Messaging_messagebodyuserstatus.msg_body_id"})
			.order_by('-msg_body__message__send_timestamp')
			.select_related('msg_body', 'msg_body__message', 'msg_body__message__sender'))

	if (len(msgss) == 0):
		raise Http404

	# Get/set up data for KMS.
	request.session['key'] = request.device_assn.secret
	ss = form.cleaned_data['secret']

	recipients = MessageRecipient.objects.filter(message__uuid__in=message_uuids) \
						.select_related('user', 'message')\
						.only('user__first_name', 'user__last_name',
								'message__uuid')
	recp_dict = convert_query_set_to_dict_with_uuid(recipients)

	ccs = MessageCC.objects.filter(message__uuid__in=message_uuids)\
						.select_related('user', 'message')\
						.only('user__first_name', 'user__last_name', 'message__uuid')
	cc_dict = convert_query_set_to_dict_with_uuid(ccs)

	attachments = MessageAttachment.objects.filter(message__uuid__in=message_uuids)\
						.select_related('message')
	attach_dict = convert_query_set_to_dict_with_uuid(attachments)

	mahs = MessageActionHistory.objects.filter(message__uuid__in=message_uuids)\
				.select_related('user', 'message')\
				.extra(select={'title':'SELECT title FROM MHLUsers_mhluser \
					WHERE MHLUsers_mhluser.user_ptr_id = Messaging_messageactionhistory.user_id'})
	mah_dict = convert_query_set_to_dict_with_uuid(mahs)

	refers = MessageRefer.objects.filter(message__uuid__in=message_uuids)\
				.select_related('message')
	refer_dict = convert_query_set_to_dict_with_uuid(refers)

	user = request.user
	local_tz = getCurrentTimeZoneForUser(user)
	current_user = request.role_user
	current_user_mobile = current_user.user.mobile_phone

	ret_msgs = []
	for status_obj in msgss:
		try:
			read_message(request, status_obj.msg_body, ss=ss)
		except KeyInvalidException:
			return err_GE021()
		msg = status_obj.msg_body.message
		msg_uuid = msg.uuid
		recipients = []
		if msg_uuid in recp_dict:
			recipients = [{
						'name': get_fullname_bystr(msg.sender.last_name,
							msg.sender.first_name,status_obj.sender_title),
						'id': u.user.id,
						} for u in recp_dict[msg_uuid]]

		ccs = []
		if msg_uuid in cc_dict:
			ccs = [{
						'name': get_fullname_bystr(u.user.last_name,
									u.user.first_name, u.title),
						'id': u.user.id,
						} for u in cc_dict[msg_uuid]]
		attachments = []
		if msg_uuid in attach_dict:
			attachments = [
					{
						'id': att.uuid,
						'filename': get_attachment_filename(request, att, ss),
						'filesize': att.size,
						'suffix':att.suffix,
					} for att in attach_dict[msg_uuid]]
		refer = None
		if msg_uuid in refer_dict:
			refer = _get_refer_from_mbus(status_obj, logo_size="Large", 
										refers=refer_dict[msg_uuid])
		action_history = []
		if msg_uuid in mah_dict:
			action_history = render_action_histories(mah_dict[msg_uuid], 
								user=user, time_zone=local_tz)

		ret_msgs.append({
			'body': status_obj.msg_body.clear_data,
			'timestamp': formatTimeSetting(user, msg.send_timestamp, 
									local_tz, True),
			'send_timestamp': msg.send_timestamp,
			'sender': {
						'name': get_fullname_bystr(msg.sender.last_name,
									msg.sender.first_name,status_obj.sender_title)\
										if msg.sender else "System Message",
						'id': msg.sender.id if msg.sender else 0,
					},
			'recipients': recipients,
			'ccs': ccs,
			'attachments': attachments,
			'message_type': msg.message_type if msg.message_type else 'NM',
			'callback_number': msg.callback_number,
			'callback_available': settings.CALL_ENABLE and bool(msg.callback_number)
				and bool(current_user_mobile),
			'urgent': bool(msg.urgent),
			'resolution_flag': bool(msg._resolved_by_id),
			'refer': refer,
			'thread_uuid': msg.thread_uuid,
			'action_history': action_history,
			'action_history_count': len(action_history)
		})

	response = {
		'data': ret_msgs,
		'warnings': {},
	}

	return HttpResponse(content=json.dumps(response), mimetype='application/json')

@AppAuthentication
def delete_message(request, message_id):
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
		return err_IN003()

	status = msgs[0]
	status.delete_flag = True
	if (not status.delete_timestamp):
		status.delete_timestamp = int(time.time())
	status.save()

	response = {
		'data': {},
		'warnings': {},
	}
	return HttpResponse(content=json.dumps(response), mimetype='application/json')


@AppAuthentication
def update_message(request, message_id):
	"""update_message request:

	:param request: The HTTP update message request
	:type request: django.core.handlers.wsgi.WSGIRequest  
	:param message_id: The message uuid
	:type message_id: uuid  
	:returns: django.http.HttpResponse -- the JSON result in an HttpResonse object
	:raises: None 
	"""
	if (request.method != 'POST'):
		return err_GE002()
	form = UpdateMessageForm(request.POST)
	if (not form.is_valid()):
		return err_GE031(form)

	update_message_status(request.user, message_id, request.POST)
	response = {
		'data': {},
		'warnings': {},
	}
	return HttpResponse(content=json.dumps(response), mimetype='application/json')


@AppAuthentication
def get_attachment(request, message_id, attachment_id):
	if (request.method != 'POST'):
		return err_GE002()
	form = MsgGetForm(request.POST)
	if (not form.is_valid()):
		return err_GE031(form)

	attachment = get_object_or_404(MessageAttachment, message__uuid=message_id, uuid=attachment_id)
	message = attachment.message

	if ((message.sender and request.user.pk != message.sender.pk) and
		not ((request.user.pk,) in message.recipients.values_list('id') or
			(request.user.pk,) in message.ccs.values_list('id'))):
		return err403(request, err_msg="You don't seem to be a valid recipient for this file.")

	# Get/set up data for KMS.
	request.session['key'] = request.device_assn.secret
	try:
		clearkey = decrypt_cipherkey(request, attachment, ss=form.cleaned_data['secret'])
	except KeyInvalidException:
		return err_GE021()

	url = attachment.decrypt_url(request, key=clearkey)
	if (url[0:4] == 'file'):
		response = HttpResponse(content_type=attachment.content_type)
		attachment.get_file(request, response)
		return response

	elif (url[0:4] == 'http'):
		# This is likely a fully qualified URL
		if (not attachment.encrypted):
			return HttpResponseRedirect(url)
		else:
			# Download and decrypt this attachment.
			pass
	else:
		raise Exception('A seemingly invalid URL has been stored: %s, '
			'for MessageAttachment %s.' % (url, attachment_id,))


@AppAuthentication
def compose_message(request):
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
		err_obj = {
			'errno': 'MS002',
			'descr': _("Thank you for your interest in sharing files with DoctorCom's secure system." \
			+ "This share is compliments of DoctorCom and your file has been sent to the intended party." \
			+ "However, to have full access you'll need a subscription for only $25/month."),
		}
		return HttpResponseBadRequest(content=json.dumps(err_obj), mimetype='application/json')

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

	request.session['key'] = request.device_assn.secret
	ss = form.cleaned_data['secret']
	createNewMessage(request, sender, sender_role_user, recipients, body,
					ccs=ccs, subject=subject, uploads=attachments,
					exist_attchments=exist_attchments,
					exist_refer=exist_refer, thread_uuid=thread_uuid, ss=ss)
	response = {
		'data': {},
		'warnings': {},
	}

	return HttpResponse(content=json.dumps(response), mimetype='application/json')


# (reserved)
@AppAuthentication
def compose_refer(request):
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

	request.session['key'] = request.device_assn.secret
	ss = request.POST['secret']

	createNewMessage(request, sender, sender_role_user, recipients, body,
					ccs=None, subject=subject, uploads=attachments, file_data_list=None,
					refer_data=form.cleaned_data, api_secret=None, ss=ss)

	response = {
		'data': {},
		'warnings': {},
	}

	return HttpResponse(content=json.dumps(response), mimetype='application/json')


@AppAuthentication
def get_refer_pdf(request, refer_id):
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

	# Get/set up data for KMS.
	request.session['key'] = request.device_assn.secret
	try:
		clearkey = decrypt_cipherkey(request, refer, ss=form.cleaned_data['secret'])
	except KeyInvalidException:
		return err_GE021()

	try:
		response = refer.get_file(request, clearkey)
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


@AppAuthentication
def update_refer(request, refer_id):
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
	response = {
		'data': {},
		'warnings': {},
	}
	return HttpResponse(content=json.dumps(response), mimetype='application/json')


@AppAuthentication
def send_message_check(request):
	if (request.method != 'POST'):
		return err_GE002()
	form = MsgCompositionCheckForm(request.POST)
	if (not form.is_valid()):
		return err_GE031(form)

	sender = request.user
	recipients = []
	form.cleaned_data['recipients']
	if 'recipients' in form.cleaned_data and len(form.cleaned_data['recipients']) > 0:
		recipients = form.cleaned_data['recipients']
	elif 'practice_recipients' in form.cleaned_data and len(form.cleaned_data['practice_recipients']) > 0:
		recipients = form.cleaned_data['practice_recipients']

	ccs = []
	if 'ccs' in form.cleaned_data and len(form.cleaned_data['ccs']) > 0:
		ccs = form.cleaned_data['ccs']

	attachment_count = 0
	if 'attachment_count' in form.cleaned_data and form.cleaned_data['attachment_count']:
		attachment_count = form.cleaned_data['attachment_count']

	valid = sendMessageCheck(sender, attachment_count, recipients, ccs)
	response = {
		'data': {'valid': valid},
		'warnings': {},
	}
	return HttpResponse(content=json.dumps(response), mimetype='application/json')

def convert_query_set_to_dict_with_uuid(q_set):
	if not isinstance(q_set, QuerySet):
		return None
	ret_dict = {}
	for recp in q_set:
		if recp.message.uuid in ret_dict:
			ret_dict[recp.message.uuid].append(recp)
		else:
			ret_dict[recp.message.uuid] = [recp]
	return ret_dict
