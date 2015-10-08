from pytz import timezone

from django.conf import settings

from MHLogin.DoctorCom.Messaging.utils import rx_msgs_by_timestamp, \
	tx_msgs_by_timestamp, get_subject, get_message_action_history_count
from MHLogin.utils.timeFormat import formatTimeSetting, getCurrentTimeZoneForUser
from django.utils.safestring import mark_safe

def rx_message_list_data(request, from_timestamp, to_timestamp, count, resolved, read=None, exclude_id=None, is_threading=True, use_time_setting=True, thread_uuid=None):
	user = request.user
	local_tz = getCurrentTimeZoneForUser(user)
	if thread_uuid:
		is_threading = False
	msg_data = rx_msgs_by_timestamp(user, from_ts=from_timestamp,
									to_ts=to_timestamp, count=count,
									resolved=resolved, read=read, exclude_id=exclude_id,
									is_threading=is_threading, thread_uuid=thread_uuid)
	return {
			'messages': [
						{
							'id': msg.uuid,
							'sender': {
										'name' : msg.sender_list[0]['name'] if msg.sender else "System Message",
										'id': msg.sender.id if msg.sender else 0,
								},
							'recipients': msg.recipients_list if is_threading else[{
									'name': ' '.join([
										u.first_name, u.last_name]),
									'id': u.id,
								} for u in msg.recipients_list],
							'ccs': msg.ccs_list if is_threading else[{
								'name': ' '.join([
									u.first_name, u.last_name]),
								'id':u.id,
								}for u in msg.ccs_list],
							'threading_msg_count': '' if not is_threading else msg.sender_number,
							'timestamp': formatTimeSetting(user, msg.send_timestamp, local_tz, use_time_setting),
							'send_timestamp': msg.send_timestamp,
							'send_time': formatTimeSetting(user, msg.send_timestamp, local_tz, use_time_setting),
							'subject': get_subject(mark_safe(msg.subject), msg.refer_status),
							'read_flag': msg.read_flag,
							'resolution_flag': msg.resolution_flag,
							'attachments': bool(msg.attachments),
							'message_type':msg.message_type if msg.message_type else 'NM',
							'callback_number':msg.callback_number,
							'urgent':bool(msg.urgent),
							'refer':msg.refer_status,
							'thread_uuid': msg.thread_uuid,
							# used for checking whether clear message detail's cache
							'action_history_count': get_message_action_history_count(msg.id)
						}
					for msg in msg_data['msgs']],
			'total_message_count': msg_data['total_count'],
			'unread_message_count': msg_data['unread_count'],
			'query_count': msg_data['query_count'],
		}

def tx_message_list_data(request, from_timestamp, to_timestamp, count, resolved, exclude_id=None, is_threading=True, use_time_setting=True, thread_uuid=None):
	user = request.user
	local_tz = getCurrentTimeZoneForUser(user)
	if thread_uuid:
		is_threading = False
	msg_data = tx_msgs_by_timestamp(user, from_ts=from_timestamp,
									to_ts=to_timestamp, count=count,
									resolved=resolved, exclude_id=exclude_id, 
									is_threading=is_threading,thread_uuid=thread_uuid)
	return {
			'messages': [
						{
							'id': msg.uuid,
							'sender': {
										'name' : (msg.sender_list[0]['name'] if msg.sender else "System Message") if is_threading else (' '.join([msg.sender.first_name, msg.sender.last_name]) if msg.sender else "System Message"),
										'id': msg.sender.id if msg.sender else 0,
								},
							'recipients': msg.recipients_list if is_threading else[{
									'name': ' '.join([
										u.first_name, u.last_name]),
									'id': u.id,
								} for u in msg.recipients_list],
							'ccs': msg.ccs_list if is_threading else[{
								'name': ' '.join([
									u.first_name, u.last_name]),
								'id':u.id,
								}for u in msg.ccs_list],
							'timestamp': formatTimeSetting(user, msg.send_timestamp, local_tz, use_time_setting),
							'send_timestamp': msg.send_timestamp,
							'send_time': formatTimeSetting(user, msg.send_timestamp, local_tz, use_time_setting),
							'subject': get_subject(mark_safe(msg.subject), msg.refer_status),
							'read_flag': msg.read_flag,
							'resolution_flag': msg.resolution_flag,
							'attachments': bool(msg.attachments),
							'urgent': bool(msg.urgent),
							'refer':msg.refer_status,
							'thread_uuid': msg.thread_uuid,
							'threading_msg_count': '' if not is_threading else msg.sender_number,
							# used for checking whether clear message detail's cache
							'action_history_count': get_message_action_history_count(msg.id)
						}
					for msg in msg_data['msgs']],
			'total_message_count': msg_data['total_count'],
			'unread_message_count': msg_data['unread_count'],
			'query_count': msg_data['query_count'],
		}
