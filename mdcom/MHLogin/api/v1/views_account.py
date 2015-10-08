# -*- coding: utf-8 -*-
'''
Created on 2012-10-08

@author: mwang
'''
from MHLogin.api.v1.decorators import APIAuthentication
from MHLogin.api.v1.business_account import practiceManageLogic, siteManageLogic, callFwdPrefsLogic, \
	getDComNumberLogic, getMobilePhoneLogic, updateMobilePhoneLogic, changePasswordLogic, profileLogic

@APIAuthentication
def practiceManage(request):
	return practiceManageLogic(request)

@APIAuthentication
def siteManage(request):
	return siteManageLogic(request)

@APIAuthentication
def callFwdPrefs(request):
	return callFwdPrefsLogic(request)

@APIAuthentication
def getDComNumber(request):
	return getDComNumberLogic(request)

@APIAuthentication
def getMobilePhone(request):
	return getMobilePhoneLogic(request)

@APIAuthentication
def updateMobilePhone(request):
	return updateMobilePhoneLogic(request)

@APIAuthentication
def changePassword(request):
	return changePasswordLogic(request)

@APIAuthentication
def profile(request):
	return profileLogic(request)

