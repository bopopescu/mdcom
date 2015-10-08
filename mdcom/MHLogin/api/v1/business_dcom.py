# -*- coding: utf-8 -*-
'''
Created on 2012-10-11

@author: mwang
'''

import json

from django.conf import settings
from django.http import HttpResponse

from MHLogin.DoctorCom.Messaging.models import Message, MessageBodyUserStatus, CallbackLog
from MHLogin.DoctorCom.models import Click2Call_Log
from MHLogin.DoctorCom.views import send_page
from MHLogin.MHLPractices.models import PracticeLocation
from MHLogin.MHLUsers.models import Provider, OfficeStaff, MHLUser
from MHLogin.api.v1.errlib import err_TE005, err_GE031, err_GE010, err_TE006, err_GE002, err_TE002, err_TE003, err_SYS500
from MHLogin.api.v1.forms_dcom import USNumberForm, PagerNumberForm
from MHLogin.api.v1.utils import HttpJSONSuccessResponse

def smartPhoneCallLogic(request, *args, **kwargs):
	if (request.method != 'POST'):
		return err_GE002()
	if (not request.mhluser.mobile_phone):
		return err_TE005()
	called_number = ''
	called_mhluser = None
	form = USNumberForm(request.POST)
	if(not form.is_valid()):
		return err_GE031(form)

	if('user_id' in kwargs):
		user_id = kwargs['user_id']
		called_mhluser = MHLUser.objects.filter(pk=user_id)
		if (not called_mhluser):
			return err_GE010()
	
		called_mhluser = called_mhluser[0]
	
		if (not called_mhluser.mobile_phone):
			return err_TE005()
		called_number = called_mhluser.mobile_phone
	if('practice_id' in kwargs):
		practice_id = kwargs['practice_id']
		called_practice = PracticeLocation.objects.filter(id=practice_id)
		if not called_practice:
			return err_GE010()

		called_number = called_practice[0].practice_phone
		if called_practice[0].backline_phone:
			called_number = called_practice[0].backline_phone

		if (not called_number):
			return err_TE006()
	elif('number' in request.POST):
		called_number = form.cleaned_data['number']
	elif('number' in kwargs):
		called_number = kwargs['number']
	if not called_mhluser and not called_number:
		return err_TE003()

	log = Click2Call_Log()
	log.caller = request.mhluser
	log.called_user = called_mhluser
	log.called_number = called_number
	log.caller_number = form.cleaned_data['caller_number']
	role_user = request.role_user
	if role_user and hasattr(role_user, "current_site") and role_user.current_site:
		log.current_site = role_user.current_site
	log.source = 'APP'
	log.save()

	data = {
		'number': ''.join(['+1',str(settings.TWILIO_C2C_NUMBER)])
	}

	return HttpJSONSuccessResponse(data=data)

def smartPhoneMessageCallbackLogic(request, message_id):
	try:
		msg = Message.objects.get(uuid=message_id)
		mbus = MessageBodyUserStatus.objects.get(user=request.user.pk, msg_body__message=msg)
		CallbackLog(message=msg).save()

		return smartPhoneCallLogic(request, number=msg.callback_number)
	except Message.DoesNotExist, MessageBodyUserStatus.DoesNotExist:
		response =  HttpResponse("")
		response.status_code = 404 #ich, __init__ won't accept status_code in its kwargs
		return response

def pageUserLogic(request, user_id):
	if (request.method != 'POST'):
		return err_GE002()
	form = PagerNumberForm(request.POST)
	if (not form.is_valid()):
		return err_GE031(form)
	
	if (not MHLUser.objects.filter(pk=user_id).exists()):
		return err_GE010()
	
	provider = None
	try:
		provider = Provider.objects.get(user=user_id)
	except Provider.DoesNotExist:
		# This is ok.
		pass
	
	office_staff = None
	try:
		office_staff = OfficeStaff.objects.get(user=user_id)
	except OfficeStaff.DoesNotExist:
		# this is okay.
		pass
	
	paged = None # The user getting paged.
	if (provider):
		paged = provider
		if (not provider.pager):
			return err_TE002()
	elif (office_staff):
		paged = office_staff
		if (not office_staff.pager):
			return err_TE002()
	else:
		# Error! User doesn't appear to be a provider or an office staffer.
		return err_GE010()
	
	send_page(request.mhluser, paged, form.cleaned_data['number'])
	return HttpJSONSuccessResponse()

