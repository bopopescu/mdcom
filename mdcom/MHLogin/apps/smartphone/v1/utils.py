
import time

from MHLogin.apps.smartphone.v1.apns import notify_new_message_iphones, notify_new_message_androids, \
		notify_message_status_iphones, notify_message_status_androids, notify_iphones,\
	notify_androids
from django.conf import settings
from MHLogin.apps.smartphone.models import SmartPhoneAssn
from MHLogin.utils.mh_logging import get_standard_logger

TIME_DISPLAY_FORMAT = '%m/%d/%Y %H:%M'

logger = get_standard_logger('%s/apps/smartphone/v1/utils.log' % (settings.LOGGING_ROOT), 
							'apps.smartphone.v1.utils', settings.LOGGING_LEVEL)

ASSOCIATIONS_KEY_IOS = "associations_ios"
ASSOCIATIONS_KEY_ANDROID = "associations_android"

TAB_CHANGE_SUPPORT_VERSION = {
	ASSOCIATIONS_KEY_IOS: "1.42.00",
	ASSOCIATIONS_KEY_ANDROID: "1.57.00"
}


def notify(associations, text=None, count=None, additional_data=None):
	"""Notify client message's new message is coming,
		:param associations: list of SmartPhoneAssn.
		:param text: notification's content, string format.
		:param count: number of this user's current unread message.
		:param additional_data: additional data, json format.
	"""
	iphones = [assn for assn in associations if assn.platform in ('iPhone', 'iPad')]
	notify_new_message_iphones(iphones, text=text, count=count, additional_data=additional_data)

	androids = [assn for assn in associations if assn.platform == 'Android']
	notify_new_message_androids(androids, text=text, count=count, additional_data=additional_data)


def notifyMessageStatus(user, count=None, additional_data=None):
	"""Notify client message's status is changed,
		:param user: is an instance of MHLUser.
		:param count: number of this user's current unread message.
		:param additional_data: additional data, json format.
	"""
	associations = SmartPhoneAssn.objects.filter(user__pk=user.pk, is_active=True).\
				exclude(push_token=None).exclude(push_token='')

	associations_iphones = []
	associations_androids = []
	for assn in associations:
		if assn.platform in ('iPhone', 'iPad'):
			associations_iphones.append(assn)
		elif assn.platform == 'Android':
			associations_androids.append(assn)

	if associations_iphones and len(associations_iphones) > 0:
		notify_message_status_iphones(associations_iphones, count=count, additional_data=additional_data)
	if associations_androids and len(associations_androids) > 0:
		notify_message_status_androids(associations_androids, count=count, additional_data=additional_data)


def notifyBatchMessageStatus(mbus):
	"""Notify client message's status is changed,
		:param mbus: is MessageBodyUserStatus list.
	"""
	from MHLogin.DoctorCom.Messaging.utils import get_message_count

	push_timestamp = int(time.time())
	for msgi in mbus:
		tmp_msg = msgi.msg_body.message
		additional_data = {
				'message': {
					'uuid': str(tmp_msg.uuid),
					'thread_uuid': str(tmp_msg.thread_uuid),
					'read': True,
					'resolve': bool(tmp_msg._resolved_by),
					'timestamp': push_timestamp,
				}
			}
		re_user = msgi.user
		count = get_message_count(re_user, None, read_flag=False, direction='received')
		notifyMessageStatus(re_user, count=count, additional_data=additional_data)


def notify_user_tab_changed(user_ids):
	"""Notify client app, user's tab is changed,
		:param user_ids: is user id list.
	"""
	if user_ids is None:
		return False

	if not isinstance(user_ids, list):
		user_ids = [user_ids]

	logger.debug("Notify users: %s" % str(user_ids))
	additional_data = {
			'user': {
				'tab_changed': True
			}
		}
	push_notification(user_ids, additional_data,\
				support_version=TAB_CHANGE_SUPPORT_VERSION)
	return True


### todo refactor push notification(new message, change message status) 
### using this function push_notification
def push_notification(user_ids, additional_data, support_version=None):
	"""Push notification to client app.
		:param user_ids: is user id list.
		:param additional_data: is a dict data.
		:return True or False
	"""
	from MHLogin.DoctorCom.Messaging.utils import get_message_count
	if not user_ids or not additional_data:
		return False

	if not isinstance(user_ids, list):
		user_ids = [user_ids]

	logger.debug("Notify users: %s" % str(user_ids))
	associations = get_associations(user_ids, support_version=support_version)
	if associations:
		for user_id in associations:
			count = get_message_count(user_id, None, read_flag=False, direction='received')
			assn_dict = associations[user_id]
			if ASSOCIATIONS_KEY_IOS in assn_dict:
				notification = render_iphone_notification(additional_data, count=count)
				logger.debug("push data - ios: %s for %s." % (str(notification), str(user_id)))
				notify_iphones(assn_dict[ASSOCIATIONS_KEY_IOS], notification)
			if ASSOCIATIONS_KEY_ANDROID in assn_dict:
				notification = render_android_notification(additional_data, count=count)
				logger.debug("push data - android: %s for %s." % (str(notification), str(user_id)))
				notify_androids(assn_dict[ASSOCIATIONS_KEY_ANDROID], notification)
	return True


def get_associations(user_ids, support_version=None):
	"""Get user's associations
		:param user_ids: is user id list.
		:return dict: the structure is :
		{
			user_id1 : {
				'associations_ios': [],
				'associations_androids': []
			},
			user_id2 : {
				...
			},
			...
		}
	"""
	if user_ids is None:
		return {}

	if not isinstance(user_ids, list):
		user_ids = [user_ids]

	associations = SmartPhoneAssn.objects.filter(user__pk__in=user_ids, is_active=True).\
				exclude(push_token=None).exclude(push_token='')
	logger.debug("user_ids: %s,  count: %d" % (str(user_ids), len(associations)))

	version_ios = None
	version_android = None
	if support_version:
		version_ios = support_version[ASSOCIATIONS_KEY_IOS]
		version_android = support_version[ASSOCIATIONS_KEY_ANDROID]

	ret_data = {}
	for assn in associations:
		if not assn.user.pk in ret_data:
			ret_data[assn.user.pk] = {}
		dict_data = ret_data[assn.user.pk]
		actual_version = assn.version
		if assn.platform in ('iPhone', 'iPad'):
			if version_ios is None or (version_ios and actual_version \
					and actual_version >= version_ios):
				logger.debug("actual ios version: %s, platform: %s"\
					% (str(actual_version), str(assn.platform)))
				add_assn_to_dict(assn, dict_data, ASSOCIATIONS_KEY_IOS)
		elif assn.platform == 'Android':
			if version_android is None or (version_android and actual_version \
					and actual_version >= version_android):
				logger.debug("actual android version: %s, platform: %s"\
					% (str(actual_version), str(assn.platform)))
				add_assn_to_dict(assn, dict_data, ASSOCIATIONS_KEY_ANDROID)
	logger.debug("associations: %s" % str(ret_data))
	return ret_data


def add_assn_to_dict(assn, dict_data, key):
	"""Add assn to dict_data with key
		:param assn: is an object.
		:param dict_data: is a dict data.
		:param key: is a string key.
		:raise ValueError
	"""
	if dict_data is None or not isinstance(dict_data, dict) or not key:
		raise ValueError
	if key in dict_data:
		if not assn in dict_data[key]:
			dict_data[key].append(assn)
	else:
		dict_data[key] = [assn]


def render_android_notification(additional_data, count=None):
	"""Render android's notification
		:param additional_data: notification data.
		:param count: unread message's count
		:return notification: is a dictionary.
	"""
	notification = {
		'badge': count if count else 0
	}
	notification.update(additional_data)
	logger.debug("notification content - android: %s" % str(notification))
	return notification


def render_iphone_notification(additional_data, count=None):
	"""Render iphone's notification
		:param additional_data: notification data.
		:param count: unread message's count
		:return notification: is a dictionary.
	"""
	notification = {'aps': {'alert': {}}}
	notification.update(additional_data)

	if(count is not None):
		notification['aps']['badge'] = count
	logger.debug("notification content - ios: %s" % str(notification))
	return notification


def setSystemInfoToResponse(response):
	if not response:
		return None
	response["settings"] = {
		"FORCED_LANGUAGE_CODE": settings.FORCED_LANGUAGE_CODE,
		"CALL_ENABLE": settings.CALL_ENABLE
	}
	return response

