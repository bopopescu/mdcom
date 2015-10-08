
import kronos
from django.conf import settings
from pyapns.client import OPTIONS, configure, notify, feedback

from MHLogin.apps.smartphone.models import SmartPhoneAssn
from MHLogin.apps.smartphone.v1.utils_gcm import GCM
from MHLogin.utils.mh_logging import get_standard_logger
from MHLogin.utils.admin_utils import mail_admins

logger = get_standard_logger('%s/apps/smartphone/v1/apns.log' % (settings.LOGGING_ROOT),
							'apps.smartphone.v1.apns', settings.LOGGING_LEVEL)


def notify_iphones(associations, notification):
	"""Common function: send notification to iPhone client.
		:param associations: list of SmartPhoneAssn.
		:param notification: notification data, dict object.
	"""
	try:
		if(not OPTIONS['CONFIGURED']):
			configure(None)
	except Exception as e:
		err_email_body = '\n'.join([
				('APNS configuration has errors!'),
				''.join(['Server: ', settings.SERVER_ADDRESS]),
				''.join(['Message: ', ('Notify mobile has errors.')]),
				''.join(['Exception: ', str(e)]),
				''.join(['Exception data: ', str(e.args)]),
			])
		mail_admins('notify mobile has errors', err_email_body)
		return

	tokens = [assn.push_token for assn in associations]
	try:
		notify(settings.APS_APPID, tokens, [notification] * len(tokens))
		logger.debug("Notify users(ios): %s for %s" % (str(tokens), str(notification)))
	except Exception:
		pass


def notify_new_message_iphones(associations, text=None, count=None, additional_data=None):
	"""Notify iPhone client, new message is coming.
		:param associations: list of SmartPhoneAssn.
		:param text: notification's content, string format.
		:param count: number of this user's current unread message.
		:param additional_data: additional data, dict object.
	"""
	notification = {'aps': {'alert': {}}}
	notification.update(additional_data)
	notification["aps"]["sound"] = "default"

	if(text):
		notification['aps']['alert']['body'] = str(text)
	else:
		notification['aps']['alert']['body'] = "you have a new doctorcom message"
	if(count is not None):
		notification['aps']['badge'] = count

	notify_iphones(associations, notification)


def notify_message_status_iphones(associations, count=None, additional_data=None):
	"""Notify iPhone client message's status is changed,
		:param associations: list of SmartPhoneAssn.
		:param count: number of this user's current unread message.
		:param additional_data: additional data, dict object.
	"""
	notification = {'aps': {'alert': {}}}
	notification.update(additional_data)

	if(count is not None):
		notification['aps']['badge'] = count

	notify_iphones(associations, notification)


@kronos.register("@daily")
def check_feedback():
	"""
	Entry point used by kronos to check_feedback, checks daily.  For django kronos 
	installtasks command to work decorated function must be in python module loaded at
	startup such as: models, __init__, admin, .cron, etc..
	"""
	import socket
	try:
		if not OPTIONS['CONFIGURED']:
			configure(None)

		tokens = feedback(settings.APS_APPID)
		for expire_time, token in tokens:
			associations = SmartPhoneAssn.objects.filter(push_token=token, platform='iPhone')
			if associations:
				associations.update(push_token=None)
		logger.info("APNS check_feedback() DONE.")
	except socket.error as e:
		logger.error(str(e))
		mail_admins("APNS check_feedback() error", str(e))


def notify_androids(associations, notification):
	"""Common function: send notification to Android client.
		:param associations: list of SmartPhoneAssn.
		:param notification: notification data, dict object.
	"""
	gcm = GCM(settings.GCM_API_KEY)
	tokens = []
	for assn in associations:
		if assn.push_token not in tokens:
			tokens.append(assn.push_token)
			try:
				gcm.plaintext_request(registration_id=assn.push_token, data=notification)
				logger.debug("Notify users(android): %s for %s" % 
							(str(assn.push_token), str(notification)))
			except Exception as e:
				logger.error(e)
				mail_admins("GCM error", e)


def notify_new_message_androids(associations, text=None, count=None, additional_data=None):
	"""Notify Android client, new message is coming.
		:param associations: list of SmartPhoneAssn.
		:param text: notification's content, string format.
		:param count: number of this user's current unread message.
		:param additional_data: additional data, dict object.
	"""
	notification = {
		'body': str(text),
		'badge': count if count else 0
		}
	notify_androids(associations, notification)


def notify_message_status_androids(associations, count=None, additional_data=None):
	"""Notify Android client message's status is changed,
		:param associations: list of SmartPhoneAssn.
		:param count: number of this user's current unread message.
		:param additional_data: additional data, dict object.
	"""
	notification = {
		'badge': count if count else 0
	}
	notification.update(additional_data)
	notify_androids(associations, notification)

