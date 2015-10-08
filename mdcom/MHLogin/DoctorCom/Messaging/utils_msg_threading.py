from pytz import UTC
from django.db.models import Q
from MHLogin.MHLUsers.utils import get_fullname_bystr
from django.utils.translation import ugettext as _
from MHLogin.DoctorCom.Messaging.models import Message, MessageBodyUserStatus,\
	MessageRecipient, MessageCC, MessageAttachment, MessageRefer


def get_msgs_for_threading(user, from_ts=None, to_ts=None, count=20,
			resolved=None, read=None, ccs=True, exclude_id=None,
			is_threading=True, thread_uuid=None, is_received_msg=True, offset=0):
	if count is None:
		count = 20
	if offset is None:
		offset = 0

	mbus = get_threading_mbus(user, None, thread_uuid, is_received_msg)
	mbu_list_all = mbus.values_list('msg_body__message__thread_uuid', flat=True)
	total_msg_count = len(set(mbu_list_all))

	msg_unread_list = mbus.filter(read_flag=False).values_list('msg_body__message__id', flat=True)
	unread_msg_count = len(set(msg_unread_list))
	msg_list = []
	msg = Message.objects.filter().order_by('-send_timestamp', '-id'
				).select_related('sender', 'recipients', 'ccs')

	exclude_msg_thread_uuid = []
	if from_ts:
		if from_ts.__class__.__name__ == 'datetime':
			from_ts = from_ts.astimezone(UTC)
		exclude_msg_thread_uuid += list(msg.exclude(send_timestamp__gte=from_ts)
				.values_list('thread_uuid', flat=True)) 

	if to_ts:
		if to_ts.__class__.__name__ == 'datetime':
			to_ts = to_ts.astimezone(UTC)
		exclude_msg_thread_uuid += list(msg.exclude(send_timestamp__lte=to_ts)
				.values_list('thread_uuid', flat=True)) 

	if exclude_id:
		exclude_msg_thread_uuid += list(msg.filter(uuid=exclude_id)
				.values_list('thread_uuid', flat=True))

	msg = msg.exclude(thread_uuid__in=exclude_msg_thread_uuid)

	if is_received_msg:
		msg = msg.filter(Q(recipients=user) | Q(ccs=user))
	else:
		msg = msg.filter(sender=user)

	msg_id_list = list(msg.values_list('id', flat=True))

	mbus = MessageBodyUserStatus.objects.filter(user=user, delete_flag=False)\
		.order_by('-msg_body__message__send_timestamp', '-msg_body__message__id')\
		.select_related('msg_body', 'msg_body__message', 'msg_body__message__sender')\
		.extra(select={'sender_title':"SELECT MHLUsers_mhluser.title \
						FROM MHLUsers_mhluser INNER JOIN Messaging_message ON \
						MHLUsers_mhluser.user_ptr_id = Messaging_message.sender_id \
						INNER JOIN  Messaging_messagebody ON \
						Messaging_message.id = Messaging_messagebody.message_id \
						WHERE Messaging_messagebody.id = Messaging_messagebodyuserstatus.msg_body_id"})

	mbu_threading_uuid = [m.thread_uuid for m in msg]
	mbus = mbus.filter(msg_body__message__thread_uuid__in=mbu_threading_uuid)
	if resolved is None:
		pass
	else:
		msgs_resolved_uuid = Message.objects.filter(_resolved_by=None, thread_uuid__in=mbu_threading_uuid)\
			.values_list('thread_uuid', flat=True)
		if resolved:
			mbus = mbus.exclude(msg_body__message__thread_uuid__in=list(msgs_resolved_uuid))
		else:
			mbus = mbus.filter(msg_body__message__thread_uuid__in=list(msgs_resolved_uuid))

	if read is None:
		pass
	else:
		mbus_unread = MessageBodyUserStatus.objects.filter(user=user,\
				delete_flag=False, read_flag=False)\
				.select_related('msg_body__message')\
				.values_list('msg_body__message__thread_uuid', flat=True)
		if read:
			mbus = mbus.exclude(msg_body__message__thread_uuid__in=list(mbus_unread))
		else:
			mbus = mbus.filter(msg_body__message__thread_uuid__in=list(mbus_unread))

	mbu_dict = {}
	for mbu in mbus:
		if mbu.msg_body.message.thread_uuid not in mbu_dict:
			mbu_dict[mbu.msg_body.message.thread_uuid] = [mbu]
		else:
			mbu_dict[mbu.msg_body.message.thread_uuid].append(mbu)

	mbu_list = sorted(mbu_dict.values(),
		key=lambda item: item[0].msg_body.message.send_timestamp, reverse=True)
	query_count = len(mbu_list)

	ml = set()
	for v in mbu_list[offset * count:offset * count + count]:
		latest_msg = None
		mtd_msg_ids = set()
		senders = []
		read_flag = True
		delete_flag = False
		resolution_flag = True
		last_resolved_by = None
		last_resolution_timestamp = 0

		for m in v:
			if not latest_msg or m.msg_body.message.send_timestamp > latest_msg.send_timestamp:
				latest_msg = m.msg_body.message

			mtd_msg_ids.add(m.msg_body.message.id)
			ml.add(m.msg_body.message.id)

			senders.append({
				'id': m.msg_body.message.uuid,
				'name': sender_name_safe(m.msg_body.message,m.sender_title)
			})

			if m.msg_body.message.id in msg_id_list:
				read_flag = read_flag and m.read_flag

			if last_resolution_timestamp < m.msg_body.message.resolution_timestamp\
				and m.msg_body.message._resolved_by:
				last_resolution_timestamp = m.msg_body.message.resolution_timestamp
				last_resolved_by = ' '.join([m.msg_body.message._resolved_by.first_name,
										m.msg_body.message._resolved_by.last_name])
			if not m.msg_body.message._resolved_by_id:
				resolution_flag = False

			delete_flag = delete_flag or m.delete_flag

		msg = latest_msg
		msg.mtd_msg_ids = mtd_msg_ids
		msg.read_flag = read_flag
		msg.delete_flag = mbu.delete_flag
		msg.resolution_flag = resolution_flag
		msg.last_resolved_by = last_resolved_by
		msg.last_resolution_timestamp = last_resolution_timestamp
		
		msg.recipients_list = []
		msg.ccs_list = []
		msg.attachments = []
		msg.sender_list = senders
		msg.sender_number = len(mtd_msg_ids)
		msg.refer_status = ''
		msg_list.append(msg)

	msg_reps = MessageRecipient.objects.filter(message__id__in=ml).select_related('message',\
			'user').extra(select={'title':'SELECT title FROM MHLUsers_mhluser \
			WHERE MHLUsers_mhluser.user_ptr_id = Messaging_message_recipients.user_id'})\
			.values('message__id', 'user__id', 'user__first_name', 'user__last_name','title')

	msg_ccs = MessageCC.objects.filter(message__id__in=ml).select_related('message',\
			'user').extra(select={'title':'SELECT title FROM MHLUsers_mhluser \
			WHERE MHLUsers_mhluser.user_ptr_id = Messaging_message_ccs.user_id'})\
			.values('message__id', 'user__id', 'user__first_name', 'user__last_name','title')

	msg_atts = MessageAttachment.objects.filter(message__id__in=ml).select_related('message')\
			.values('uuid', 'suffix', 'size', 'filename', 'message__id')

	msg_refers = MessageRefer.objects.filter(message__id__in=ml).select_related('message__id')\
			.values('message__id', 'status')

	for m in msg_list:
		for msg_rep in msg_reps:
			if msg_rep['message__id'] in m.mtd_msg_ids:
				rep_dict = {
					'id': msg_rep['user__id'],
					'name': get_fullname_bystr(msg_rep['user__last_name'],msg_rep['user__first_name'],msg_rep['title'])
				}
				if rep_dict not in m.recipients_list:
					m.recipients_list.append(rep_dict)

		for msg_cc in msg_ccs:
			if msg_cc['message__id'] in m.mtd_msg_ids:
				m.ccs_list.append({
					'id': m.uuid,
					'name': get_fullname_bystr(msg_cc['user__last_name'],msg_cc['user__first_name'],msg_cc['title'])
				})

		for msg_att in msg_atts:
			if msg_att['message__id'] in m.mtd_msg_ids:
				m.attachments.append({
					'id': msg_att['uuid'],
					'suffix': msg_att['suffix'],
					'size': msg_att['size'],
					'filename': msg_att['filename']
				})

		for msg_refer in msg_refers:
			if msg_refer['message__id'] == m.id:
				m.refer_status = msg_refer['status']

	msg_list.sort(key=lambda item: item.send_timestamp, reverse=True)
	return {
			'total_count': total_msg_count,
			'unread_count': unread_msg_count,
			'query_count': query_count,
			'msg_count': query_count,
			'msgs': msg_list
	}


def get_threading_mbus(user, resolved, thread_uuid=None, is_received_msg=None):
	mbus = MessageBodyUserStatus.objects.order_by(
				'-msg_body__message__send_timestamp', '-msg_body__message__id'
				).filter(user=user, delete_flag=False
				).select_related('msg_body', 'msg_body__message')\
				.extra(select={'sender_title':"SELECT MHLUsers_mhluser.title \
					FROM MHLUsers_mhluser INNER JOIN Messaging_message ON \
					MHLUsers_mhluser.user_ptr_id = Messaging_message.sender_id \
					INNER JOIN  Messaging_messagebody ON \
					Messaging_message.id = Messaging_messagebody.message_id \
					WHERE Messaging_messagebody.id = Messaging_messagebodyuserstatus.msg_body_id"})

	if is_received_msg is None:
		pass
	elif is_received_msg:
		mbus = mbus.filter(Q(msg_body__message__recipients=user) | Q(
			msg_body__message__ccs=user))
	else:
		mbus = mbus.filter(msg_body__message__sender=user)

	if thread_uuid and mbus:
		mbus = mbus.filter(msg_body__message__thread_uuid=thread_uuid)

	if resolved is None:
		pass
	elif resolved:
		# Using ``_resolved_by_id`` to make sure ``resolved_by`` does
		# not cause a separate user load from the database
		mbus = mbus.exclude(msg_body__message__in=[
				m.msg_body.message
				for m in mbus
				if m.msg_body.message._resolved_by_id == 0])
	else:
		# Using ``_resolved_by_id`` to make sure ``resolved_by`` does
		# not cause a separate user load from the database
		mbus = mbus.filter(msg_body__message__in=[
				m.msg_body.message
				for m in mbus
				if m.msg_body.message._resolved_by_id == 0])
	return mbus


def get_name_from_list(name_dict):
	# sorting is not required here, but gives consisten results
	names = sorted(set(n['name'] for n in name_dict))
	return '; '.join(names)


def sender_name_safe(message,title):
	if (message.sender):
		return get_fullname_bystr(message.sender.last_name, 
							message.sender.first_name,title=title)
	else:
		return _('System Message')