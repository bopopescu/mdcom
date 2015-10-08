# -*- coding: utf-8 -*-
'''
Created on 2012-10-12

@author: mwang
'''
from pytz import timezone

from django.conf import settings

from MHLogin.DoctorCom.Messaging.utils import rx_msgs_by_timestamp,\
	tx_msgs_by_timestamp, get_subject
from MHLogin.KMS.shortcuts import decrypt_cipherkey
from MHLogin.utils.timeFormat import timezone_conversion
from django.utils.safestring import mark_safe


def getReceivedMessageListData(user, condition_dict):
	from_timestamp = None
	if ('from_timestamp' in condition_dict):
		from_timestamp = condition_dict['from_timestamp']
	to_timestamp = None
	if ('to_timestamp' in condition_dict):
		to_timestamp = condition_dict['to_timestamp']
	count = None
	if ('count' in condition_dict):
		count = condition_dict['count']
	resolved = None
	if ('resolved' in condition_dict):
		resolved = condition_dict['resolved']
	read = None
	if ('read' in condition_dict):
		read = condition_dict['read']
	exclude_id = None
	if ('exclude_id' in condition_dict):
		exclude_id = condition_dict['exclude_id']

	msg_data = rx_msgs_by_timestamp(user, from_ts=from_timestamp, 
			to_ts=to_timestamp, count=count, 
			resolved=resolved, read=read, exclude_id=exclude_id)

	return {
			'messages': [
				{
					'id': msg.uuid,
					'sender': {
							'name': ' '.join([msg.sender.first_name, 
								msg.sender.last_name]) if msg.sender else "System Message",
							'id': msg.sender.id if msg.sender else 0,
						},
					'timestamp': timezone_conversion(
							msg.send_timestamp,
							timezone(settings.TIME_ZONE),
							).strftime('%m/%d/%y %H:%M'),
					'send_timestamp': msg.send_timestamp,
					'send_time': timezone_conversion(
							msg.send_timestamp,
							timezone(settings.TIME_ZONE),
							).strftime('%m/%d/%y %H:%M'),
					'subject': get_subject(mark_safe(msg.subject), msg.refer_list),
					'read_flag': msg.read_flag,
					'resolution_flag': msg.resolution_flag,
					'attachments': bool(msg.attachments),
					'message_type':msg.message_type if msg.message_type else 'NM',
					'callback_number':msg.callback_number,
					'refer':get_refer(msg.refer_list),
				} for msg in msg_data['msgs']],
			'total_message_count': msg_data['total_count'],
			'unread_message_count': msg_data['unread_count'],
			'query_count': msg_data['query_count'],
		}


def getSentMessageListData(user, condition_dict):
	from_timestamp = None
	if ('from_timestamp' in condition_dict):
		from_timestamp = condition_dict['from_timestamp']
	to_timestamp = None
	if ('to_timestamp' in condition_dict):
		to_timestamp = condition_dict['to_timestamp']
	count = None
	if ('count' in condition_dict):
		count = condition_dict['count']
	resolved = None
	if ('resolved' in condition_dict):
		resolved = condition_dict['resolved']
	read = None
	if ('read' in condition_dict):
		read = condition_dict['read']
	exclude_id = None
	if ('exclude_id' in condition_dict):
		exclude_id = condition_dict['exclude_id']

	msg_data = tx_msgs_by_timestamp(user, from_ts=from_timestamp, 
			to_ts=to_timestamp, count=count, 
			resolved=resolved, exclude_id=exclude_id)

	return {
			'messages': [
						{
							'id': msg.uuid,
							'recipients':[{
									'name': ' '.join([
										u.first_name, u.last_name]),
									'id': u.id,
								} for u in msg.recipients_list],
							'timestamp': timezone_conversion(
									msg.send_timestamp,
									timezone(settings.TIME_ZONE),
									).strftime('%m/%d/%y %H:%M'),
							'send_timestamp': msg.send_timestamp,
							'send_time': timezone_conversion(
									msg.send_timestamp,
									timezone(settings.TIME_ZONE),
									).strftime('%m/%d/%y %H:%M'),
							'subject': mark_safe(mark_safe(msg.subject), msg.refer_list),
							'read_flag': msg.read_flag,
							'resolution_flag': msg.resolution_flag,
							'attachments': bool(msg.attachments),
							'urgent': msg.urgent,
							'refer':get_refer(msg.refer_list),
						}
					for msg in msg_data['msgs']],
			'total_message_count': msg_data['total_count'],
			'unread_message_count': msg_data['unread_count'],
			'query_count': msg_data['query_count'],
		}


def _get_attachment_filename(request, attachment, ss=None):
	request.session['key'] = request.device_assn.secret
	clearkey = decrypt_cipherkey(request, attachment, ss=ss)

	return attachment.decrypt_filename(request, key=clearkey)


def get_refer(refer_list):
	refer = ''
	if refer_list:
		refer = refer_list[0].status
	return refer
