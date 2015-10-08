# -*- coding: utf-8 -*-
'''
Created on 2012-10-11

@author: mwang
'''

from MHLogin.api.v1.business_dcom import smartPhoneCallLogic,\
	smartPhoneMessageCallbackLogic, pageUserLogic
from MHLogin.api.v1.decorators import APIAuthentication

@APIAuthentication
def smartPhoneCall(request, *args, **kwargs):
	""" Call by using C2C number, used for smart phone client
	"""
	return smartPhoneCallLogic(request, *args, **kwargs)


@APIAuthentication
def smartPhoneMessageCallback(request, message_id):
	""" Call by using C2C number, used for smart phone client
	"""
	return smartPhoneMessageCallbackLogic(request, message_id)

# Can use app's interface
#@TwilioAuthentication
#def connect_call(request):

@APIAuthentication
def pageUser(request, user_id):
	return pageUserLogic(request, user_id)

@APIAuthentication
def call(request, *args, **kwargs):
	#todo implement this function using new click2call_initiate
	pass

