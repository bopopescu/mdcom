'''
Created on 2013-6-7

@author: pyang
'''
import datetime
from django.conf import settings

from MHLogin.Validates.utils import getTodaySendRemainCount, getTodayValidates,\
	getTodayLastValidate, sendCodeLogic, getTodayValidateInfo, checkSendCodeEnable,\
	validateLogic, checkValidateCodeLocked, checkValidateCodeLockedByLog, getServerUrl
from MHLogin.Validates.tests.utils import ValidTest, randomCode
from MHLogin.Validates import utils
from MHLogin.Validates.models import Validation, ValidationLog
from MHLogin.Validates.forms import SendCodeForm, ValidateForm
from MHLogin.apps.smartphone.v1.tests.utils import generateHttpRequest
from MHLogin.DoctorCom.Messaging.tests import CalledTest

class GetTodaySendRemainCountTest(ValidTest):
	def testGetTodaySendRemainCount(self):
		type = 1
		self.assertEqual(getTodaySendRemainCount(type,self.user.id), \
				settings.SEND_MAXIMUM_PER_DAY)
#		type = 10
#		with self.assertRaises(ValueError):getTodaySendRemainCount(type,self.user.id)
		type = 'abcd'
		with self.assertRaises(ValueError):getTodaySendRemainCount(type,self.user.id)
#		
		validate = Validation()
		validate.code = randomCode()
		validate.type = 1
		validate.applicant = self.user.id
		validate.recipient = self.user
		validate.save()
		valid = getTodayValidates(validate.type,validate.applicant)
		self.assertEqual(getTodaySendRemainCount(validate.type,validate.applicant), \
				settings.SEND_MAXIMUM_PER_DAY-len(valid))

class GetTodayValidatesTest(ValidTest):
	def testGetTodayValidates(self):
#		type = 10
#		with self.assertRaises(ValueError):getTodayValidates(type,self.user.id)
		type = 'abcd'
		with self.assertRaises(ValueError):getTodayValidates(type,self.user.id)
		constant_times = settings.SEND_MAXIMUM_PER_DAY
		for i in range(constant_times):
			validate = Validation()
			validate.code = randomCode()
			validate.type = 1
			validate.applicant = self.user.id
			validate.recipient = self.user
			validate.save()
		valid = getTodayValidates(validate.type,validate.applicant)
		self.assertEqual(len(valid), constant_times)

class GetTodayLastValidateTest(ValidTest):
	def testGetTodayLastValidate(self):
		type = 1
		self.assertEqual(getTodayLastValidate(type,self.user.id),None)
#		type = 10
#		with self.assertRaises(ValueError):getTodayLastValidate(type,self.user.id)
#		type = 'abcd'
#		with self.assertRaises(ValueError):getTodayLastValidate(type,self.user.id)
		constant_times = settings.SEND_MAXIMUM_PER_DAY
		for i in range(constant_times):
			validate = Validation()
			validate.code = randomCode()
			validate.type = 1
			validate.applicant = self.user.id
			validate.recipient = self.user.mobile_phone
			validate.save()
		self.assertEqual(getTodayLastValidate(type,self.user.id),None)
		self.assertEqual(getTodayLastValidate(type,self.user.id,self.user),None)
		self.assertIsNotNone(getTodayLastValidate(type,self.user.id,self.user.mobile_phone))
		
class SendCodeLogicTest(ValidTest):
	def testSendCodeLogic(self):
		test_twilio = CalledTest()
		utils.twilioSMS_unloggedSender = test_twilio
		test_mail = CalledTest()
		utils.send_mass_mail = test_mail 
		request = generateHttpRequest()
		data = {'recipient':self.user.mobile_phone,'type':1,'init':True}
		form = SendCodeForm(data)
		self.assertEqual(sendCodeLogic(form,self.user,request)['send_remain_count'],4)
		data['type']=2
		form = SendCodeForm(data)
		settings.CALL_ENABLE = True
		self.assertEqual(sendCodeLogic(form,self.user,request)['send_waiting_time'],\
						settings.SEND_CODE_WAITING_TIME*60)
		self.assertTrue(test_twilio.was_called)
		validate = Validation()
		validate.code = randomCode()
		validate.type = 1
		validate.applicant = self.user.id
		validate.recipient = self.user.mobile_phone
		validate.save()
		data = {'recipient':self.user.mobile_phone,'type':1,'init':True}
		form = SendCodeForm(data)
		self.assertEqual(sendCodeLogic(form,self.user,request)['send_remain_count'],3)
		constant_times = settings.SEND_MAXIMUM_PER_DAY
		for i in range(constant_times):
			validate = Validation()
			validate.code = randomCode()
			validate.type = 1
			validate.applicant = self.user.id
			validate.recipient = self.user.mobile_phone
			validate.save()
		self.assertEqual(sendCodeLogic(form,self.user,request)['send_remain_count'],0)
	
class GetTodayValidateInfoTest(ValidTest):
	def testGetTodayValidateInfo(self):
		type=2
		send_remain_count,validate, send_waiting_time= \
				getTodayValidateInfo(type, self.user.id ,self.user.mobile_phone)
		self.assertEqual(validate,None)
		self.assertEqual(send_remain_count,settings.SEND_MAXIMUM_PER_DAY)
		validate = Validation()
		validate.code = randomCode()
		validate.type = 2
		validate.applicant = self.user.id
		validate.recipient = self.user.mobile_phone
		validate.save()
		list = getTodayValidateInfo(type, self.user.id ,self.user.mobile_phone)
		self.assertEqual(list[0],4)
		self.assertEqual(list[1].id,1)
		
class CheckSendCodeEnableTest(ValidTest):
	def testCheckSendCodeEnable(self):
		type=2
		b = checkSendCodeEnable(type,self.user.id,self.user.mobile_phone)
		self.assertTrue(b, 'this send_remain_count > 0')
		constant_times = settings.SEND_MAXIMUM_PER_DAY
		for i in range(constant_times):
			validate = Validation()
			validate.code = randomCode()
			validate.type = 2
			validate.applicant = self.user.id
			validate.recipient = self.user.mobile_phone
			validate.save()
		a = checkSendCodeEnable(type,self.user.id,self.user.mobile_phone)
		self.assertFalse(a, 'this send_remain_count <= 0')
		
class ValidateLogicTest(ValidTest):
	def testValidateLogic(self):
		data = {'recipient':self.provider.email,'code':5642,'type':2}
		form = ValidateForm(data)
		self.assertEqual(validateLogic(form, self.provider, 1)['flag'],1)
		validate = Validation()
		validate.code = 5642
		validate.type = 2
		validate.applicant = self.provider.user.id
		validate.recipient = self.provider.email
		validate.save()
		self.assertEqual(validateLogic(form, self.provider, 1)['flag'],0)
		validate.code = 1234
		validate.save()
		vl = ValidationLog()
		vl.validation = validate
		vl.code_input = 5214
		vl.validate_time = datetime.datetime(2013,4,12)
		vl.save()
		self.assertEqual(validateLogic(form, self.provider.user, 1)['flag'],2)

class CheckValidateCodeLockedTest(ValidTest):
	def testCheckValidateCodeLocked(self):
		validate = Validation()
		validate.code = randomCode()
		validate.type = 2
		validate.applicant = self.provider.user.id
		validate.recipient = self.user.mobile_phone
		validate.save()
		self.assertFalse(checkValidateCodeLocked(validate,datetime.datetime.now()))
		validate.validate_locked_time = datetime.datetime.now()
		validate.is_active = False
		validate.save()
		self.assertTrue(checkValidateCodeLocked(validate,datetime.datetime.now()))

class CheckValidateCodeLockedByLogTest(ValidTest):
	def testCheckValidateCodeLockedByLog(self):
		validate = Validation()
		validate.code = randomCode()
		validate.type = 2
		validate.applicant = self.provider.user.id
		validate.recipient = self.user.mobile_phone
		validate.save()
		vl = ValidationLog()
		vl.validation = validate
		vl.code_input = 5214
		vl.validate_time = datetime.datetime.now()-datetime.timedelta(hours=0.1)
		vl.save()
		self.assertFalse(checkValidateCodeLockedByLog(validate,datetime.datetime.now()))
		vl = ValidationLog()
		vl.validation = validate
		vl.code_input = 5214
		vl.validate_time = datetime.datetime.now()-datetime.timedelta(hours=0.2)
		vl.save()
		vl = ValidationLog()
		vl.validation = validate
		vl.code_input = 5214
		vl.validate_time = datetime.datetime.now()-datetime.timedelta(hours=0.5)
		vl.save()
		self.assertTrue(checkValidateCodeLockedByLog(validate,datetime.datetime.now()))

class GetServerUrlTest(ValidTest):
	def testGetServerUrl(self):
		path = '/media/guide/Mobile_App_User_Guide.pdf'
		path_prev = ''.join([settings.SERVER_PROTOCOL, '://', settings.SERVER_ADDRESS])
		self.assertEqual(getServerUrl(), path_prev)
		self.assertEqual(getServerUrl(path), ''.join([path_prev, path]))