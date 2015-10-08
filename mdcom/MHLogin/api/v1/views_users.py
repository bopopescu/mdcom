# -*- coding: utf-8 -*-
'''
Created on 2012-9-27

@author: mwang
'''

from MHLogin.MHLUsers.forms import CreateProviderForm, CreateOfficeStaffForm, CreateMHLUserForm, CreateBrokerMHLUserForm, CreateBrokerForm
from MHLogin.api.v1.decorators import APIAuthentication
from MHLogin.api.v1.errlib import err_GE002, err_GE031
from MHLogin.api.v1.forms_users import ProviderSearchForm, StaffSearchForm
from MHLogin.api.v1.utils_users import getProviderList, getStaffList, getUserInfo
from MHLogin.api.v1.utils import HttpJSONSuccessResponse
from MHLogin.MHLUsers.utils_users import createNewProvider, createNewOfficeStaff, createNewBroker


@APIAuthentication
def searchProviders(request):
	if (request.method != 'POST'):
		return err_GE002()
	form = ProviderSearchForm(request.POST)
	if (not form.is_valid()):
		return err_GE031(form)

	data = getProviderList(form.cleaned_data)
	return HttpJSONSuccessResponse(data=data)


@APIAuthentication
def searchStaff(request):
	if (request.method != 'POST'):
		return err_GE002()
	form = StaffSearchForm(request.POST)
	if (not form.is_valid()):
		return err_GE031(form)

	data = getStaffList(form.cleaned_data)
	return HttpJSONSuccessResponse(data=data)


@APIAuthentication
def providerInfo(request, user_id):
	data = getUserInfo(user_id)
	return HttpJSONSuccessResponse(data=data)


@APIAuthentication
def staffInfo(request, user_id):
	data = getUserInfo(user_id)
	return HttpJSONSuccessResponse(data=data)


@APIAuthentication
def createProvider(request):
	if (request.method != 'POST'):
		return err_GE002()
	form = CreateProviderForm(request.POST)
	if (not form.is_valid()):
		return err_GE031(form)

	createNewProvider(form, request.role_user)
	return HttpJSONSuccessResponse()


@APIAuthentication
def createOfficeStaff(request):
	if (request.method != 'POST'):
		return err_GE002()

	staff_form = CreateOfficeStaffForm(request.POST)
	mhluser_form = CreateMHLUserForm(request.POST, request.FILES)
	if (not mhluser_form.is_valid()):
		return err_GE031(mhluser_form)
	if (not staff_form.is_valid()):
		return err_GE031(staff_form)

	createNewOfficeStaff(mhluser_form, staff_form, request.role_user)
	return HttpJSONSuccessResponse()


@APIAuthentication
def createBroker(request):
	if (request.method != 'POST'):
		return err_GE002()

	broker_form = CreateBrokerForm(request.POST)
	mhluser_form = CreateBrokerMHLUserForm(request.POST, request.FILES)
	if (not mhluser_form.is_valid()):
		return err_GE031(mhluser_form)
	if (not broker_form.is_valid()):
		return err_GE031(broker_form)

	createNewBroker(mhluser_form, broker_form, request.role_user)
	return HttpJSONSuccessResponse()

