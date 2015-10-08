import datetime
import inspect
import random
import time
import json

from smtplib import SMTPException
from urllib2 import HTTPError
from twilio import TwilioRestException

from django.conf import settings
from django.core.mail import send_mass_mail
from django.db import transaction
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _

from MHLogin.DoctorCom.SMS.views import twilioSMS_unloggedSender
from MHLogin.MHLUsers.models import Provider, MHLUser, OfficeStaff, Broker
from MHLogin.Validates.models import Validation, ValidationLog
from MHLogin.utils.admin_utils import mail_admins
from MHLogin.utils.twilio_utils import TWILIO_INVALID_TO_PHONE_NUMBER,\
	TWILIO_NOT_A_VALID_MOBILE_NUMBER

ValidateConfigs = {
	"1": {
		"desc": "Email"
	},
	"2": {
		"desc": "Mobile"
	},
	"3": {
		"desc": "Pager"
	},
}

ValidateStatus = {
	"Success": 0,
	"None": 1,
	"Error": 2,
	"Locked": 3,
	"Overdue": 4
}


def checkSendCodeEnable(type, applicant, recipient):
	if not recipient:
		return False
	send_remain_count, validate, send_waiting_time = \
				getTodayValidateInfo(type, applicant, recipient)
	return send_remain_count > 0 or send_waiting_time <= 0


def getTodaySendRemainCount(type, applicant):
	max_count = settings.SEND_MAXIMUM_PER_DAY
	validates = getTodayValidates(type, applicant)
	if (not validates):
		return max_count
	else:
		return max_count - len(validates)


def getTodayValidates(type, applicant):
	today = datetime.date.today()
#    now = datetime.datetime.now()
	return_set = Validation.objects.filter(type=type, applicant=applicant, sent_time__gte=today)
	return list(return_set.order_by("-sent_time"))


def getTodayLastValidate(type, applicant, recipient=None):
	validates = getTodayValidates(type, applicant)
	if not validates:
		return None
	validate = validates[0]
	if not recipient:
		return None

	if (validate.recipient == recipient):
		return validate
	else:
		return None


###
# return [send_remain_count, last_validate, send_waiting_time] 
###
def getTodayValidateInfo(type, applicant, recipient):
	send_remain_count = getTodaySendRemainCount(type, applicant)
	validate = getTodayLastValidate(type, applicant, recipient)
	if not validate:
		return [send_remain_count, validate, 0]
	sent_time = time.mktime(validate.sent_time.timetuple())
	now = time.mktime(datetime.datetime.now().timetuple())

	return [send_remain_count, validate, 
		settings.SEND_CODE_WAITING_TIME * 60 - (now - sent_time)]


def sendCodeLogic(form, user, request):
	if (form.is_valid()):
		recipient = form.cleaned_data["recipient"]
		type = form.cleaned_data["type"]
		init = form.cleaned_data["init"]
		send_remain_count, validate, send_waiting_time = \
			getTodayValidateInfo(type, user.id, recipient)
		now = datetime.datetime.now()
		validate_locked = checkValidateCodeLocked(validate, now)
		if send_remain_count <= 0:
			return {
						'send_remain_count': 0, 
						'send_waiting_time': int(send_waiting_time),
						'validate_locked': validate_locked,
						'has_code': validate is not None
					}

		if validate and init:
			return {
						'send_remain_count': send_remain_count, 
						'send_waiting_time': int(send_waiting_time),
						'validate_locked': validate_locked,
						'has_code': True
					}

		try:
			code = '%04d' % (int(random.random() * 10000))
			user_name = '%s %s' % (user.first_name, user.last_name)
			validate = Validation(code=code, type=type, applicant=user.id, recipient=recipient)
			validate.save()

			if type == "1":
				emailContext = {
						"user_name": user_name,
						"code": code,
#						"time": settings.SEND_CODE_WAITING_TIME
					}

				send_mass_mail(
					[
						(
							_('DoctorCom Email Validation'),
							render_to_string('Validates/validateByEmail.html', emailContext),
							settings.SERVER_EMAIL,
							[recipient]
						)
					]
				)
			else:
				if not settings.CALL_ENABLE:
					return {'error_code': 403}
				desc = ValidateConfigs[type]["desc"]
				context = {
						"user_name": user_name,
						"code": code,
						"desc": desc.lower(),
#						"time": settings.SEND_CODE_WAITING_TIME
					}
				body = render_to_string('Validates/validateByTwilio.html', context)
				twilioSMS_unloggedSender(request, recipient, body)

			send_waiting_time = settings.SEND_CODE_WAITING_TIME * 60
			return {
						'send_remain_count': send_remain_count - 1, 
						'send_waiting_time': send_waiting_time, 
						'validate_locked': False,
						'has_code': True
					}

		except SMTPException as e:
			transaction.rollback()
			validate = None
			err_email_body = '\n'.join([
					'Mail Send Error!',
					''.join(['Server: ', settings.SERVER_ADDRESS]),
					''.join(['Recipient: ', recipient]),
					''.join(['Exception: ', str(e)]),
					''.join(['Exception data (code): ', str(e.code)]),
					''.join(['Exception data (original_error): ', str(e.original_error)]),
				])
			mail_admins('Mail Send Error', '\n'.join([inspect.trace(), ]))
			raise e
		except TwilioRestException as e:
			transaction.rollback()
			validate = None
			code = getTwilioRestExceptionCode(e)
			err_email_body = '\n'.join([
					'SMS Send Error!',
					''.join(['Server: ', settings.SERVER_ADDRESS]),
					''.join(['Recipient: ', recipient]),
					''.join(['Exception: ', str(e)]),
					''.join(['Exception data (code): ', str(code)]),
					''.join(['Exception data (message): ', e.msg]),
				])
			mail_admins('SMS Send Error', err_email_body)
			if code in (TWILIO_INVALID_TO_PHONE_NUMBER, TWILIO_NOT_A_VALID_MOBILE_NUMBER): 
				return {'error_code': 404}
			else:
				raise e
		except HTTPError as e:
			transaction.rollback()
			validate = None
			err_email_body = '\n'.join([
					'SMS Send Error!',
					''.join(['Server: ', settings.SERVER_ADDRESS]),
					''.join(['Recipient: ', recipient]),
					''.join(['Exception: ', str(e)]),
					''.join(['Exception data (read): ', str(e.read())]),
				])
			mail_admins('SMS Send Error', err_email_body)
			raise e


def validateLogic(form, user, user_type):
	if (form.is_valid()):
		recipient = form.cleaned_data["recipient"]
		code_input = form.cleaned_data["code"]
		type = int(form.cleaned_data["type"])
		validate = getTodayLastValidate(type, user.id, recipient)

		if not validate:
			return {'flag': ValidateStatus["None"]}

		now = datetime.datetime.now()
		validate_locked = checkValidateCodeLocked(validate, now)
		if validate_locked:
			return {'flag': ValidateStatus["Locked"]}

		code = validate.code
		if code_input == code:
			validate.validate_success_time = now
			validate.validate_locked_time = None
			validate.save()
			# Do something after update validation	
			if 1 == type:
				MHLUser.objects.filter(id=user.id).update(email_confirmed=True, email=recipient)
			elif 2 == type:
				MHLUser.objects.filter(id=user.id).update(mobile_confirmed=True, mobile_phone=recipient)

				user_email = user.email
				if user_email:
					user_name = ' '.join([user.first_name, user.last_name])
					guide_address = getServerUrl('media/guide/Mobile_App_User_Guide.pdf')
					# if the mobile phone number is verified, system will send user "Mobile App User Guide"
					emailContext = {
							"user_name": user_name,
							"mobile_phone": recipient,
							"guide_address": guide_address,
							"support_email": 'support@mdcom.com'
						}
	
					send_mass_mail(
						[
							(
								_('DoctorCom Mobile App User Guide'),
								render_to_string('Validates/sentUserGuide.html', emailContext),
								settings.SERVER_EMAIL,
								[user_email]
							)
						]
					)

			elif 3 == type and user_type:
				# User_type detail information in MHLogin/utils/constants.py -> USER_TYPE_CHOICES   
				if 1 == user_type or 2 == user_type or 10 == user_type:
					Provider.objects.filter(id=user.id).update(pager_confirmed=True, pager=recipient)
				elif 100 == user_type or 101 == user_type:
					OfficeStaff.objects.filter(user__id=user.id).update(pager_confirmed=True, pager=recipient)
				elif 300 == user_type:
					Broker.objects.filter(user__id=user.id).update(pager_confirmed=True, pager=recipient)

			return {'flag': ValidateStatus["Success"]}
		else:
			validation_log = ValidationLog(validation=validate, code_input=code_input, validate_time=now)
			validation_log.save()
			validate_locked = checkValidateCodeLockedByLog(validate, now)
			if validate_locked:
				validate.is_active = False
				validate.validate_locked_time = now
				validate.save()
				return {'flag': ValidateStatus["Locked"]}
			else:
				return {'flag': ValidateStatus["Error"]}
	else:
		return {'flag': ValidateStatus["Error"]}


def checkValidateCodeLocked(validate, now):
	if validate and not validate.is_active and validate.validate_locked_time:
		unlock_time = validate.validate_locked_time + datetime.timedelta(hours=settings.VALIDATE_LOCK_TIME)
		return now < unlock_time
	if validate:
		validate.is_active = True
		validate.validate_locked_time = None
		validate.save()
	return False


def checkValidateCodeLockedByLog(validate, now):
	start_fail_time = now - datetime.timedelta(hours=1)
	fail_times = ValidationLog.objects.filter(validation__pk=validate.pk, validate_time__lte=now, validate_time__gt=start_fail_time).count()
	return fail_times >= settings.FAIL_VALIDATE_MAXIMUM_PER_HOUR

def getTwilioRestExceptionCode(e):
	"""Get error code from TwilioRestExceptionCode,
		:param e: an instance of TwilioRestExceptionCode, if not raise TypeError
		:return int
	"""
	if not isinstance(e, TwilioRestException):
		raise TypeError
	if not e.msg:
		return 0
	try:
		msg = json.loads(e.msg)
		if "TwilioResponse" not in msg:
			return 0
		temp = msg["TwilioResponse"]
		if "RestException" not in temp:
			return 0
		temp = temp["RestException"]
		if "Code" not in temp:
			return 0
		return int(temp["Code"])

	except ValueError:
		return 0

def getServerUrl(relative_path=None):
	"""Get Server Url
		:param relative_path: str, is relative path
			if relative_path is None, then return server path prefix
		:return str
	"""
	path_prev = ''.join([settings.SERVER_PROTOCOL, '://', settings.SERVER_ADDRESS])
	if relative_path and isinstance(relative_path, str):
		if not relative_path.startswith('/'):
			relative_path = ''.join(['/', relative_path])
	else:
		relative_path = ''
	return ''.join([path_prev, relative_path])
