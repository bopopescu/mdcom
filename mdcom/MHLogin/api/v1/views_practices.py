# -*- coding: utf-8 -*-
'''
Created on 2012-9-24

@author: mwang
'''
from MHLogin.api.v1.decorators import APIAuthentication
from MHLogin.api.v1.errlib import err_GE002, err_GE031
from MHLogin.api.v1.forms_practices import PracticeSearchForm
from MHLogin.api.v1.utils import HttpJSONSuccessResponse
from MHLogin.api.v1.utils_practices import getPracticeList, getPracticeInfo, \
	getPracticeProviders, getPracticeStaff, getLocalOffice
from MHLogin.utils.constants import RESERVED_ORGANIZATION_TYPE_ID_PRACTICE

@APIAuthentication
def practiceSearch(request):
	if (request.method != 'POST'):
		return err_GE002()
	form = PracticeSearchForm(request.POST)
	if (not form.is_valid()):
		return err_GE031(form)

	data = getPracticeList(form.cleaned_data, org_type_id=RESERVED_ORGANIZATION_TYPE_ID_PRACTICE)
	return HttpJSONSuccessResponse(data=data)

@APIAuthentication
def practiceInfo(request, practice_id):
	data = getPracticeInfo(practice_id)
	return HttpJSONSuccessResponse(data=data)
#
@APIAuthentication
def practiceProviders(request, practice_id):
	data = getPracticeProviders(practice_id)
	return HttpJSONSuccessResponse(data=data)

@APIAuthentication
def practiceStaff(request, practice_id):
	data = getPracticeStaff(practice_id)
	return HttpJSONSuccessResponse(data=data)

@APIAuthentication
def myPracticeProviders(request):
	data = None
	if request.role_user and hasattr(request.role_user, "current_practice")\
		and request.role_user.current_practice:
		data = getPracticeProviders(request.role_user.current_practice.id)
	return HttpJSONSuccessResponse(data=data)

@APIAuthentication
def myPracticeStaff(request):
	data = None
	if request.role_user and hasattr(request.role_user, "current_practice")\
		and request.role_user.current_practice:
		data = getPracticeStaff(request.role_user.current_practice.id)
	return HttpJSONSuccessResponse(data=data)

@APIAuthentication
def localOffice(request):
	data = None
	if request.role_user and hasattr(request.role_user, "current_practice")\
		and request.role_user.current_practice:
		data = getLocalOffice(request.role_user.current_practice)
	return HttpJSONSuccessResponse(data=data)
