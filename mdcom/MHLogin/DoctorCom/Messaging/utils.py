
from pytz import timezone
import time
import re
import thread

from django.conf import settings
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import conditional_escape 
from django.utils.translation import ugettext as _
from django.utils.safestring import mark_safe
from django.db import transaction
from django.contrib.auth.models import User

from MHLogin.DoctorCom.Messaging.models import Message, MessageBody, MessageAttachment, \
	MessageBodyUserStatus, MessageRefer, REFER_STATUS, MessageRecipient, MessageCC,\
	MessageActionHistory
from MHLogin.DoctorCom.Messaging.utils_msg_threading import get_msgs_for_threading,\
	get_threading_mbus
from MHLogin.KMS.shortcuts import decrypt_object
from MHLogin.MHLUsers.models import GENDER_CHOICES, MHLUser, Physician
from MHLogin.MHLUsers.utils import get_fullname_bystr
from MHLogin.utils import ImageHelper
from MHLogin.apps.smartphone.v1.utils import notifyBatchMessageStatus
from MHLogin.utils.timeFormat import formatTimeSetting

MSG_SUBJECT_PREFIX_RE = "RE:"
MSG_SUBJECT_PREFIX_FW = "FW:"
MSG_SUBJECT_PREFIXS = (MSG_SUBJECT_PREFIX_RE, MSG_SUBJECT_PREFIX_FW)


def get_message_count(user, types, *args, **kwargs):
	# Note begin 5 lines in the function _get_user_rx_mbus, it has similar logic.

	mbus = MessageBodyUserStatus.objects.filter(user=user, delete_flag=False)

	if types:
		mbus = mbus.filter(msg_body__message__message_type__in=types)

	if ('read_flag' in kwargs):
		mbus = mbus.filter(read_flag=kwargs['read_flag'])
	if ('direction' in kwargs):
		direction = kwargs['direction']
		if 'received' == direction:
			mbus = mbus.filter(Q(msg_body__message__recipients=user) | 
							Q(msg_body__message__ccs=user))
		elif 'sent' == direction:
			mbus = mbus.filter(msg_body__message__sender=user)
	return mbus.distinct().count()


def rx_msgs_by_timestamp(user, from_ts=None, to_ts=None, count=None,\
			resolved=None, read=None, ccs=True, exclude_id=None,\
			is_threading=True, thread_uuid=None):
	"""
	Returns all received messages between the two timestamps, inclusive.

	:param from_ts: Either a UNIX timestamp in GMT or a datetime object indicating the oldest 
		time you're looking for messages from.
	:param to_ts: Either a UNIX timestamp in GMT or a datetime object indicating the earliest 
		time you're looking for messages from.
	:param count: The maximum number of messages to return. If omitted, the function will 
		return all the messages between the timestamps.
	:param resolved: If True or False (but not None), will filter messages based on 
		resolution status passed.
	:param read: If True or False (but not None), will filter messages based on read 
		status passed.
	:param ccs: Return CC'd messages if True.

		Note that this code will obey the time zone passed in the datetime object.
	"""
	if thread_uuid:
		pass
	elif is_threading:
		return get_msgs_for_threading(user, from_ts, to_ts, count,\
			resolved, read, ccs, exclude_id, 
			is_threading, thread_uuid, is_received_msg=True, offset=0) 

	# Is the from_ts value set?
	if (from_ts == None):
		if (count == None):
			count = 20
		return rx_msgs_by_offset(user, 0, count, resolved,\
				is_threading=is_threading, thread_uuid=thread_uuid)

	mbus, total_msg_count, unread_msg_count = _get_user_rx_mbus(user,\
			resolved, ccs, is_threading=is_threading, thread_uuid=thread_uuid) 

	if (read == None):
		pass
	elif (read):
		mbus = mbus.filter(read_flag=True)
	else:
		mbus = mbus.filter(read_flag=False)

	# from_ts and to_ts need to be UNIX timestamps. If they're datetime objects,
	# convert them to timestamps.
	gmt = timezone('GMT')
	if (from_ts and from_ts.__class__.__name__ == 'datetime'):
		from_ts = from_ts.astimezone(gmt)
	if (to_ts and to_ts.__class__.__name__ == 'datetime'):
		to_ts = to_ts.astimezone(gmt)

	mbus = mbus.filter(msg_body__message__send_timestamp__gte=from_ts)
	if (to_ts):
		mbus = mbus.filter(msg_body__message__send_timestamp__lte=to_ts)

	if exclude_id:
		mbus = mbus.exclude(msg_body__message__uuid=exclude_id)

	query_count = mbus.count()

	#mbus = mbus.only( 'read_flag', 'read_timestamp', 'delete_flag', 
	#'msg_body__message__uuid', 'msg_body__message__send_timestamp', 
	#'msg_body__message__subject', 'msg_body__message__sender__first_name',
	#'msg_body__message__sender__last_name')

	if (mbus.count() > count):
		mbus = mbus[:count]

	return _return_data_from_mbus(mbus, total_msg_count, unread_msg_count, query_count)


def rx_msgs_by_offset(user, offset=0, count=20, resolved=None, ccs=True,\
		is_threading=True, thread_uuid=None):
	"""
	Returns /count/ messages starting at /offset/. As an example, this function will 
	get you 20 (count) messages starting with the 60th (offset) message.

	Nomenclature:
		mbus/MBUS: MessageBodyUserStatus

	:param user: The user to get messages for.
	:param offset: The offset for the first message to fetch. This is a Python index value.
	:param count: The number of messages to retrieve.
	:param resolved: The desired resolution flag to filter on. If None (as opposed to False), 
		the resolution flag is disregarded.
		ccs: If True, this function will return all messges this user has been CC'd in on.

	:returns: (msg_count, msgs)
		msg_count
		The total number of messages, given the filter options passed. (the only
		current filter option is the resolved flag)

		msgs
		All the messages, as Message objects, with additional custom fields scrubbed from 
		the MessageBodyUserStatus objects. Note that these additional fields should be 
		considered to be read-only.

		The following fields are added to the Message object:
			attachments: A list containing information on all attachments for this message. 
			The format is [{'id':uuid, 'suffix':'att_suffix'}, ...].
			delete_flag: The delete flag for this object, for the user.
			read_flag: The read flag for this object, for the user.
			resolution_flag: The resolution flag for this object, for the user.
	:rtype: tuple
	"""

	if thread_uuid:
		pass
	elif is_threading:
		return get_msgs_for_threading(user=user, count=count, 
			resolved=resolved, ccs=ccs, is_threading=is_threading,
			thread_uuid=thread_uuid, is_received_msg=True) 

	mbus, total_msg_count, unread_msg_count = _get_user_rx_mbus(user,\
			resolved, ccs, is_threading=is_threading, thread_uuid=thread_uuid)

	query_count = mbus.count()

	#mbus = mbus.only('resolution_flag', 'read_flag', 'read_timestamp', 'delete_flag', 
	#'msg_body__message__uuid', 'msg_body__message__send_timestamp', 
	#'msg_body__message__subject', 'msg_body__message__sender__first_name',
	#'msg_body__message__sender__last_name')

	mbus = mbus[offset * count:offset * count + count]

	return _return_data_from_mbus(mbus, total_msg_count, unread_msg_count, query_count)


def _get_user_rx_mbus(user, resolved, ccs, is_threading=True, thread_uuid=None):
	if thread_uuid:
		mbus = get_threading_mbus(user, resolved, thread_uuid)
		total_msg_count = mbus.count()
		unread_msg_count = mbus.filter(read_flag=False).count()
	else:
		mbus = MessageBodyUserStatus.objects.order_by(
				'-msg_body__message__send_timestamp', '-msg_body__message__id'
				).filter(Q(msg_body__message__recipients=user) | Q(
				msg_body__message__ccs=user), user=user, delete_flag=False
				).distinct().select_related('msg_body', 'msg_body__message')\
				.extra(select={'sender_title':"SELECT MHLUsers_mhluser.title \
					FROM MHLUsers_mhluser INNER JOIN Messaging_message ON \
					MHLUsers_mhluser.user_ptr_id = Messaging_message.sender_id \
					INNER JOIN  Messaging_messagebody ON \
					Messaging_message.id = Messaging_messagebody.message_id \
					WHERE Messaging_messagebody.id = Messaging_messagebodyuserstatus.msg_body_id"})

		# Book keeping values -- things that we're going to return.
		total_msg_count = mbus.count()
		unread_msg_count = mbus.filter(read_flag=False).count()
		if (resolved == None):
			pass
		elif (resolved):
			mbus = mbus.filter(msg_body__message__in=[m.msg_body.message for m in mbus 
				if m.msg_body.message.resolved_by != None])
		else:
			mbus = mbus.filter(msg_body__message__in=[m.msg_body.message for m in mbus 
				if m.msg_body.message.resolved_by == None])

	return (mbus, total_msg_count, unread_msg_count)


def tx_msgs_by_timestamp(user, from_ts=None, to_ts=None, count=None,\
		resolved=None, exclude_id=None, is_threading=True, thread_uuid=None):
	"""
	Returns all received messages between the two timestamps, inclusive.

	:param from_ts: Either UNIX timestamp in GMT or datetime object indicating the 
		oldest time you're looking for messages from.
	:param to_ts: Either a UNIX timestamp in GMT or a datetime object indicating the earliest 
		time you're looking for messages from.
	:param count: The maximum number of messages to return. If omitted, the function will 
		return all the messages between the timestamps.

		Note that this code will obey the time zone passed in the datetime object.
	"""
	if thread_uuid:
		pass
	elif is_threading:
		return get_msgs_for_threading(user, from_ts, to_ts, count, resolved, None,
			True, exclude_id, is_threading, thread_uuid, is_received_msg=False, offset=0) 

	# Is the from_ts value set? If not, run tx_msgs_by_offset using relatively 
	# default values.
	if (from_ts == None):
		if (count == None):
			count = 20
		return tx_msgs_by_offset(user, 0, count, resolved,\
				is_threading=is_threading, thread_uuid=thread_uuid)

	mbus = _get_user_tx_mbus(user, resolved, is_threading, thread_uuid)

	# Book keeping values -- things that we're going to return.
	total_msg_count = mbus.count()
	unread_msg_count = mbus.filter(read_flag=False).count()

	# from_ts and to_ts need to be UNIX timestamps. If they're datetime objects,
	# convert them to timestamps.
	gmt = timezone('GMT')
	if (from_ts and from_ts.__class__.__name__ == 'datetime'):
		from_ts = from_ts.astimezone(gmt)
	if (to_ts and to_ts.__class__.__name__ == 'datetime'):
		to_ts = to_ts.astimezone(gmt)

	# Now, apply our remaining filters.
	mbus = mbus.filter(msg_body__message__send_timestamp__gte=from_ts)
	if (to_ts):
		mbus = mbus.filter(msg_body__message__send_timestamp__lte=to_ts)

	if exclude_id:
		mbus = mbus.exclude(msg_body__message__uuid=exclude_id)

	query_count = mbus.count()

	if (mbus.count() > count):
		mbus = mbus[:count]

	return _return_data_from_mbus(mbus, total_msg_count, unread_msg_count, query_count)


def tx_msgs_by_offset(user, offset=-0, count=20, resolved=None,\
					is_threading=True, thread_uuid=None):
	"""
	Returns /count/ messages starting at /offset/. As an example, this function will 
	get you 20 (count) messages starting with the 60th (offset) message.

	Nomenclature:
		mbus/MBUS: MessageBodyUserStatus

	:param user: The user to get messages for.
	:param offset: The offset for the first message to fetch. This is a Python index value.
	:param count: The number of messages to retrieve.
	:param resolved: The desired resolution flag to filter on. If None (as opposed to False), 
		the resolution flag is disregarded.

	:returns: (msg_count, msgs)
		msg_count
		The total number of messages, given the filter options passed. (the only
		current filter option is the resolved flag)

		msgs
		All the messages, as Message objects, with additional custom fields scrubbed from
		the MessageBodyUserStatus objects. Note that these additional fields should be 
		considered to be read-only.

		The following fields are added to the Message object:
			attachments: A list containing information on all attachments for this message. 
			The format is [{'id':uuid, 'suffix':'att_suffix'}, ...].
			delete_flag: The delete flag for this object, for the user.
			read_flag: The read flag for this object, for the user.
			resolution_flag: The resolution flag for this object, for the user.
	:rtype: tuple
	"""

	if thread_uuid:
		pass
	elif is_threading:
		return get_msgs_for_threading(user, None, None, count, resolved, None,
			True, None, is_threading, thread_uuid, is_received_msg=False, offset=0) 

	mbus = _get_user_tx_mbus(user, resolved, is_threading, thread_uuid)

	# Book keeping values -- things that we're going to return.
	total_msg_count = mbus.count()
	unread_msg_count = mbus.filter(read_flag=False).count()

	query_count = mbus.count()

	mbus = mbus[offset * count: offset * count + count]

	return _return_data_from_mbus(mbus, total_msg_count, unread_msg_count, query_count)


def _get_user_tx_mbus(user, resolved, is_threading=True, thread_uuid=None):
	mbus = MessageBodyUserStatus.objects.filter(user=user, delete_flag=False,\
			msg_body__message__sender=user)\
			.order_by('-msg_body__message__send_timestamp',\
					'-msg_body__message__id')\
			.select_related('msg_body', 'msg_body__message')\
			.extra(select={'sender_title':"SELECT MHLUsers_mhluser.title \
						FROM MHLUsers_mhluser INNER JOIN Messaging_message ON \
						MHLUsers_mhluser.user_ptr_id = Messaging_message.sender_id \
						INNER JOIN  Messaging_messagebody ON \
						Messaging_message.id = Messaging_messagebody.message_id \
						WHERE Messaging_messagebody.id = Messaging_messagebodyuserstatus.msg_body_id"})
	if thread_uuid:
		mbus = get_threading_mbus(user, resolved, thread_uuid)
	else:
		if (resolved == None):
			pass
		elif (resolved):
			mbus = mbus.filter(msg_body__message__in=[m.msg_body.message \
					for m in mbus if m.msg_body.message.resolved_by != None])
		else:
			mbus = mbus.filter(msg_body__message__in=[m.msg_body.message \
					for m in mbus if m.msg_body.message.resolved_by == None])

	return mbus


def _return_data_from_mbus(mbus, total_msg_count, unread_msg_count, query_count):
	msg_count = mbus.count()
	mbus.select_related("msg_body", "msg_body__message")\

	msg_ids = [m.msg_body.message_id for m in mbus]

	#mbus = mbus.only('resolution_flag', 'read_flag', 'read_timestamp', 'delete_flag',
	#'msg_body__message__uuid', 'msg_body__message__send_timestamp', 
	#'msg_body__message__subject', 'msg_body__message__sender__first_name',
	#'msg_body__message__sender__last_name')

	attachments = MessageAttachment.objects.filter(message__id__in=msg_ids)

	attachments_bymessage = {}
	for mbu in mbus:
		# Generate keys for all messages
		attachments_bymessage[mbu.msg_body.message_id] = []
	for attachment in attachments:
		attachments_bymessage[attachment.message_id].append(attachment)

	# Okay, time to set up recipients and CCs. First, we need to create the
	# lookup tables and ensure that all messages have a recipients and cc 
	# record.
	msg_recipients = dict()
	msg_ccs = dict()
	msg_refer = dict()
	for mbu in mbus:
		msg_recipients[mbu.msg_body.message_id] = []
		msg_ccs[mbu.msg_body.message_id] = []
		msg_refer[mbu.msg_body.message_id] = []

	# Deal with recipients
	msg_recipient_maps = MessageRecipient.objects.filter(message__in=msg_ids).\
		select_related('user').only('user__first_name', 'user__last_name', 'message')\
		.extra(select={'title':'SELECT title FROM MHLUsers_mhluser \
			WHERE MHLUsers_mhluser.user_ptr_id = Messaging_message_recipients.user_id'})

	for msg_recipient_map in msg_recipient_maps:
		msg_recipients[msg_recipient_map.message_id].append(msg_recipient_map.user)

	msg_cc_maps = MessageCC.objects.filter(message__in=msg_ids).select_related('user').\
		only('user__first_name', 'user__last_name', 'message')\
		.extra(select={'title':'SELECT title FROM MHLUsers_mhluser \
			WHERE MHLUsers_mhluser.user_ptr_id = Messaging_message_ccs.user_id'})

	for msg_cc_map in msg_cc_maps:
		if (not msg_cc_map.message_id in msg_ccs):
			msg_ccs[msg_cc_map.message_id] = []
		msg_ccs[msg_cc_map.message_id].append(msg_cc_map.user)

	msg_refer_maps = MessageRefer.objects.filter(message__in=msg_ids)

	for msg_refer_map in msg_refer_maps:
		if (not msg_refer_map.message_id in msg_refer):
			msg_refer[msg_refer_map.message_id] = []
		msg_refer[msg_refer_map.message_id].append(msg_refer_map)

	return {
			'total_count': total_msg_count,
			'unread_count': unread_msg_count,
			'query_count': query_count,
			'msg_count': total_msg_count,
			'msgs': _get_msgs_from_mbus(mbus, msg_recipients, msg_ccs, 
					attachments_bymessage, msg_refer)
		}


def _get_msgs_from_mbus(mbus, msg_recipients, msg_ccs, attachments_bymessage, msg_refer):
	"""
	Munges the return data set so that we return a list of all messages with the
	modified/new keys, as specified in the function docstring.
	"""
	msgs = []
	mbus.select_related('msg_body__message')
	senders = []
	for mbu in mbus:
		senders.append({
			'id': mbu.msg_body.message.uuid,
			'name': sender_name_safe(mbu.msg_body.message,mbu.sender_title)
		})
		msg = mbu.msg_body.message
		msg.attachments = [{'id': att.uuid, 'suffix': att.suffix,
			'size': att.size, 'filename': att.filename}
				for att in attachments_bymessage[mbu.msg_body.message.id]]
		msg.read_flag = mbu.read_flag
		msg.delete_flag = mbu.delete_flag
#		msg.resolution_flag = mbu.resolution_flag
		msg.resolution_flag = bool(msg._resolved_by_id)
		msg.recipients_list = msg_recipients[msg.id]
		msg.ccs_list = msg_ccs[msg.id]
		msg.refer_list = msg_refer[msg.id]
		msg.refer_status = msg_refer[msg.id][0].status if msg_refer[msg.id] else ''
		msg.sender_list = senders
		msgs.append(msg)
	return msgs


# Composite result json data, it's used for web and apps
def _get_refer_from_mbus(status_obj, logo_size="Middle", call_enable=False, refers=None):
	result = None
	if refers is None and status_obj:
		refers = MessageRefer.objects.filter(message=status_obj.msg_body.message)
	if refers:
		refer = refers[0]
		referring_physician_id = status_obj.msg_body.message.sender.id
		practice_name = ''
		practice_phone_number = ''
		practice_state = ''
		practice_city = ''
		practice_address = ''

		if refer.practice:
			practice_logo = ImageHelper.get_image_by_type(refer.practice.practice_photo, 
				logo_size, 'Practice', 'img_size_practice')
			practice_name = refer.practice.practice_name
			practice_phone_number = refer.practice.practice_phone
			if refer.practice.backline_phone:
				practice_phone_number = refer.practice.backline_phone
			practice_phone_number = replace_number(practice_phone_number, call_enable)
			practice_state = refer.practice.practice_state
			practice_city = refer.practice.practice_city
			practice_address = ' '.join([refer.practice.practice_address1, 
					refer.practice.practice_address2])
		else:
			practice_logo = ImageHelper.DEFAULT_PICTURE['Practice']

		result = {
			'patient_name': ' '.join([refer.first_name, refer.middle_name, refer.last_name]),
			'previous_name': refer.previous_name,
			'gender': dict(GENDER_CHOICES)[refer.gender].capitalize() if refer.gender else "",
			'insurance_id': refer.insurance_id,
			'insurance_name': refer.insurance_name,
			'secondary_insurance_id': refer.secondary_insurance_id,
			'secondary_insurance_name': refer.secondary_insurance_name,
			'tertiary_insurance_id': refer.tertiary_insurance_id,
			'tertiary_insurance_name': refer.tertiary_insurance_name,
			'phone_number': replace_number(refer.phone_number, call_enable),
			'home_phone_number': replace_number(refer.home_phone_number, call_enable),
			'alternative_phone_number': replace_number(refer.alternative_phone_number, call_enable),
			'date_of_birth': getStrFrmTime(refer.date_of_birth),
			'status': refer.status,
			'referring_physician': sender_name_safe(status_obj.msg_body.message,status_obj.sender_title),
			'referring_physician_id': referring_physician_id,
			'physician_phone_number': replace_number(
				status_obj.msg_body.message.sender.mhluser.mobile_phone, call_enable),
			'uuid': refer.uuid,
			'refer_pdf': refer.refer_pdf,
			'refer_jpg': refer.refer_jpg,
			"practice_logo": practice_logo,
			"practice_name": practice_name,
			"practice_phone_number": practice_phone_number,
			"practice_city": practice_city,
			"practice_state": practice_state,
			"practice_address": practice_address,
			"refer_mrn": refer.mrn,
			"refer_ssn": refer.ssn,
			"refer_address": refer.address,
			"prior_authorization_number": refer.prior_authorization_number,
			"other_authorization": refer.other_authorization,
			"internal_tracking_number": refer.internal_tracking_number,
			"notes": refer.notes,
			"icd_code": refer.icd_code,
			"ops_code": refer.ops_code,
			"medication_list": refer.medication_list,
			"refer_email": refer.email
		}
	return result


# Update refer, it's used for web, api and apps
def updateRefer(request, form, refer_id):
	refer = MessageRefer.objects.get(uuid=refer_id)
	if refer.status != 'NO':
		return False

	refer.status = form.cleaned_data["status"]
	refer.refuse_reason = form.cleaned_data["refuse_reason"]
	refer.save()

	message = Message.objects.filter(id=refer.message_id).extra(select=
				{'title':'SELECT title FROM MHLUsers_mhluser \
				WHERE MHLUsers_mhluser.user_ptr_id = Messaging_message.sender_id'})

	sender = message[0].sender
	recipient_name=get_fullname_bystr(sender.last_name,sender.first_name,message[0].title)
	get_object_or_404(MessageBody, message=message)

	recipient_email_list = []
	recipient_list = []
	recipient_email_list.append(sender.email)
	duser_ids = list(Physician.objects.all().values_list("user__user__pk", flat=True))
	recipients= message[0].recipients.all().extra(select={'title':'SELECT title FROM MHLUsers_mhluser \
			WHERE MHLUsers_mhluser.user_ptr_id = Messaging_message_recipients.user_id'})
	for recipient in recipients:
		recipient_list.append(get_fullname_bystr(str(recipient.last_name),str(recipient.first_name),recipient.title))

	emailContext = dict()
	emailContext['refuse_reason'] = ''
	emailContext['sender_name'] = ', '.join(recipient_list)
	emailContext['recipient_name'] = recipient_name
	emailContext['patient_name'] = ' '.join([refer.first_name, refer.middle_name, refer.last_name])
	emailContext['operator_name'] = ' '.join([request.user.first_name, request.user.last_name])

	emailContext['status'] = dict(REFER_STATUS)[refer.status].lower()
	if refer.status == "RE":
		if refer.refuse_reason:
			emailContext['refuse_reason'] = _(u'\nDeclined Reason: %s') % refer.refuse_reason
		else:
			emailContext['refuse_reason'] = _(u'\nDeclined Reason: N/A')

	msgBody = render_to_string('DoctorCom/Messaging/ReferStaUpdEmail.html', emailContext)

	msg_subject = _('DoctorCom: Refer [%s]') % dict(REFER_STATUS)[refer.status]
	msg = Message(sender=None, sender_site=None, subject=msg_subject, message_type='NM')
	msg.save()

	MessageRecipient(user=sender, message=msg).save()
	msg_body = msg.save_body(msgBody)
	msg.send(request, msg_body)

	email_msgBody = msgBody + _("\n Best, \n DoctorCom")
	send_mail(msg_subject, email_msgBody, settings.SERVER_EMAIL,
			recipient_email_list, fail_silently=False)
	return True


def get_subject(subject, refer_status):
	if refer_status and refer_status != 'NO':
		return conditional_escape('%s[%s]' % (subject, dict(REFER_STATUS)[refer_status]))
	return conditional_escape(subject)


def sender_name_safe(message, title=None):
	if (message.sender):
		return get_fullname_bystr(message.sender.last_name,
								message.sender.first_name, title=title)
	else:
		return _('System Message')


def getStrFrmTime(date):
	return date.strftime("%x")


def replace_number(body_str, call_enable):
	data = conditional_escape(body_str)
	number_re = re.compile(r'(?<!\d{1})(?<!\+)(((\+?1)[\s,-]{1})?(\(\d{3}\)'
		'|\d{3})[\s,-]{1}\d{3}[\s,-]\d{4}|(\+?1)?\d{10})(?!\d{1})')
	mstr = number_re.sub(lambda m: gen_for_number(m.group(0), call_enable), data)
	return mstr


def gen_for_number(number, call_enable):
	"""Helper to generate format number
	:param number: string object of full phone number
	:param call_enable: bool object of current user can call
	:returns: call format string if call_enable is true
	"""
	if call_enable:
		phone_number_re = re.compile(r'[\D]*')
		only_number = phone_number_re.sub('', number)[-10:]
		return mark_safe('<a href="/Call/Number/?called_number=%s">%s</a>' %\
						(only_number, number))
	else:
		return number


def read_message(request, msg_body, ss=None):
	"""Read message, this function include following logic:
	1. Decrypt message body, and return the decrypted body.
	2. Mark the message is read.
	In addition, if the message's type is ANS, mark the related user(receiver 
	and ccs)'s message body is read, and send push notification to these users.
	:param request: HTTP request object.
	:param msg_body: an instance of MessageBodyUserStatus.
	:param ss: user's private key
	"""
	body = decrypt_object(request, msg_body, ss=ss)
	mark_message_as_read(request.user, msg_body)
	return body


def mark_message_as_read(user, msg_body):
	"""Mark message as read,

	If the message's type is ANS, mark the related user(receiver and ccs)'s message 
	body is read, and send push notification to other related users(don't include himself).
	:param user: is an instance of User/MHLUser.
	:param msg_body: an instance of MessageBodyUserStatus.
	:param ss: user's private key
	: *** Note ***: The function will commit transaction, if caller function 
	depends on other operation, don't use this function
	"""
	msg = msg_body.message
	read_timestamp = int(time.time())
	if 'ANS' == msg.message_type:
		msgs = list(MessageBodyUserStatus.objects.filter(read_flag=False, msg_body=msg_body))
		for msgi in msgs:
			msgi.read_flag = True
			msgi.read_timestamp = read_timestamp
			msgi.save()
			MessageActionHistory.create_read_history(msg, msgi.user, timestamp=read_timestamp)
		"""
		Note: transaction commit manually, in order to start a new thread.
		"""
		transaction.commit()
		thread.start_new_thread(notifyBatchMessageStatus, (msgs,))

	else:
		MessageBodyUserStatus.objects.filter(user__pk=user.pk, read_flag=False, 
			msg_body=msg_body).update(read_flag=True, read_timestamp=read_timestamp)
		MessageActionHistory.create_read_history(msg, user, timestamp=read_timestamp)


def update_message_status(user, message_uuid, request_data, is_treading=False, local_tz=None):
	"""Update message status,
	Note: The function will commit transaction, if caller function 
	depends on other operation, don't use this function

	:param user: is an instance of User/MHLUser.
	:param message_uuid: message's uuid.
	:param request_data: request data dict if 'resolved' in it, then update 
		resolved status if 'read' in it, then mark the message is read
	:param is_treading: true or false if 'is_treading' is True, then update 
		message threading status if 'is_treading' is False, then update 
		this message status
	:raise: ValueError
	"""
	if not user or not message_uuid or not request_data:
		return ValueError
	status = get_object_or_404(MessageBodyUserStatus, user=user, 
							msg_body__message__uuid=message_uuid)

	resolved_read_count = 0
	if ('resolved' in request_data):
		msgs = None
		if is_treading:
			msgs = Message.objects.filter(thread_uuid=status.msg_body.message.thread_uuid)
		else:
			msgs = Message.objects.filter(uuid=message_uuid)

		if not msgs:
			return False

		resolved_status = request_data['resolved']
		resolved_status = False if resolved_status in ('false', 'False', '0') else bool(resolved_status)
		current_timestamp = int(time.time())
		if (resolved_status):
			msgs.update(_resolved_by=user, resolution_timestamp=current_timestamp)
			#mbus = MessageBodyUserStatus.objects.filter(msg_body__message__in=msgs, 
			# resolution_timestamp=None)
			#mbus.update(resolution_timestamp = int(time.time()))

			# mark related message status is read
			mbus_read = MessageBodyUserStatus.objects.filter(
					msg_body__message__in=msgs, user=user, read_flag=False)
			resolved_read_count = mbus_read.count()
			mbus_read.update(read_flag=True, read_timestamp=current_timestamp)
			status.read_flag = True
			status.read_timestamp = current_timestamp
		else:
			msgs.update(_resolved_by=None, resolution_timestamp=0)

		status.save()
		# record action history
		for msg in msgs:
			MessageActionHistory.create_resolve_history(msg, user,\
					resolve=resolved_status, timestamp=current_timestamp)
			if resolved_status:
				MessageActionHistory.create_read_history(msg, user,\
					timestamp=current_timestamp)

		"""
		Note: transaction commit manually, in order to start a new thread.
		"""
		transaction.commit()
		# send notification to related users
		mbus = MessageBodyUserStatus.objects.filter(msg_body__message__in=msgs).\
					select_related('body', 'body__message', 'user')
		thread.start_new_thread(notifyBatchMessageStatus, (mbus,))

	if ('deleted' in request_data):
		pass
	if ('read' in request_data):
#		status_modified = True
#		status.read_flag = True
#		status.read_timestamp = int(time.time())
		mark_message_as_read(user, status.msg_body)

	data = {}
	resolve_info = get_resolved_info(user, status.msg_body.message.thread_uuid, None, local_tz=local_tz)
	if resolve_info:
		data = resolve_info
	data['resolved_read_count'] = resolved_read_count
	data['read'] = status.read_flag
	data['deleted'] = status.delete_flag

	result = {
		'success': 'True',
		'data': data
	}
	return result


def get_resolved_info(user, thread_uuid, resolved, local_tz=None):
	"""get resolved information of the message threading,
	:param user: is an instance of User/MHLUser.
	:param thread_uuid: message's thread_uuid.
	:param resolved: is None or not None
	:param local_tz: timezone object or string
	:return {
		'resolved': resolve status of message threading,
		'last_resolution_timestamp': last resolve timestamp of message threading,
				if time_zone is None, then don't format timestamp.
				if time_zone has value, then format timastamp with the time_zone
		'last_resolved_by': last resolver of message threading.
	}
	"""
	mbus = get_threading_mbus(user, resolved, thread_uuid, None)
	resolved = True
	last_resolved_by = None
	last_resolution_timestamp = 0
	for m in mbus:
		if m.msg_body.message.resolved_by == None:
			resolved = False
			break

		if last_resolution_timestamp < m.msg_body.message.resolution_timestamp:
			last_resolution_timestamp = m.msg_body.message.resolution_timestamp
			last_resolved_by = ' '.join([m.msg_body.message._resolved_by.first_name,
									m.msg_body.message._resolved_by.last_name])

	mhluser = None
	if user:
		if isinstance(user, MHLUser):
			mhluser = user
		elif isinstance(user, User):
			mhluser = list(MHLUser.objects.filter(pk=user.pk))
			if mhluser and len(mhluser) > 0:
				mhluser = mhluser[0]

	return {
			"resolved": resolved,
			"last_resolution_timestamp": formatTimeSetting(mhluser, last_resolution_timestamp, local_tz)\
					if local_tz and mhluser and last_resolution_timestamp else last_resolution_timestamp,
			"last_resolved_by": last_resolved_by
		}


def get_message_action_history(message_id, user=None, time_zone=None):
	"""Get message action history.
	:param message_id: message's id, int value.
	:param user: is an instance of MHLUser, 
		if user is None, then don't format timestamp.
		if user has value, then format timastamp with the time_zone
	:param time_zone: time_zone object or string, 
		if time_zone is None, then don't format timestamp.
		if time_zone has value, then format timastamp with the time_zone
	:raise: ValueError
	"""
	if not message_id:
		raise ValueError
	message_id = int(message_id)

	mahs = MessageActionHistory.objects.filter(message__id=message_id).select_related('user')\
				.extra(select={'title':'SELECT title FROM MHLUsers_mhluser \
					WHERE MHLUsers_mhluser.user_ptr_id = Messaging_messageactionhistory.user_id'})
	return render_action_histories(mahs, user=user, time_zone=time_zone)

def render_action_histories(mahs, user=None, time_zone=None):
	return [{
			'content': _("[%(user_name)s] %(type)s this message at") %\
				{'user_name': get_fullname_bystr(mah.user.last_name, mah.user.first_name,mah.title),
				'type': mah.get_type_display().lower()},
			'timestamp': formatTimeSetting(user, mah.timestamp, time_zone)\
					if time_zone is not None and user else mah.timestamp
		}for mah in mahs]

def get_message_action_history_count(message_id):
	"""Get message action history count.
	:param message_id: message's id, int value.
	:raise: ValueError
	"""
	if not message_id:
		raise ValueError
	message_id = int(message_id)
	return MessageActionHistory.objects.filter(message__id=message_id).count()


def get_format_subject(subject, decorate_str):
	"""Get format subject.
	:param subject: message's subject.
	"""
	if not subject:
		return ""
	if not decorate_str:
		return subject

	if len(subject) >= 3 and subject[0:3].upper() in (MSG_SUBJECT_PREFIXS):
		subject = subject[3:]
	subject = subject.strip()
	return ': '.join([decorate_str, subject])


def get_prefix_from_subject(subject):
	"""Get message subject's  prefix.
	:param subject: message's subject.
	"""
	if not subject:
		return ""
	if len(subject) >= 3 and subject[0:3].upper() in (MSG_SUBJECT_PREFIXS):
		return subject[0:3]
	return ""


def remove_prefix_from_subject(subject):
	"""Remove all prefix(RE: or FW:) from message subject
	:param subject: message's subject.
	"""
	if not subject:
		return ""
	if len(subject) >= 3 and subject[0:3].upper() in (MSG_SUBJECT_PREFIXS):
		subject = subject[3:]
		subject = subject.strip()
		return remove_prefix_from_subject(subject)
	else:
		subject = subject.strip()
		return subject


def clean_subject_prefix(subject):
	"""Replace multiple prefix(RE: or FW:) with the first prefix(RE: or FW:)
		if subject start with multiple (RE: or FW:), preserve the first (RE: or FW:)
	:param subject: message's subject.
	"""
	if not subject:
		return ""
	prefix = get_prefix_from_subject(subject)
	subject = remove_prefix_from_subject(subject)
	final_sub = ' '.join([prefix, subject])
	return final_sub.strip()
