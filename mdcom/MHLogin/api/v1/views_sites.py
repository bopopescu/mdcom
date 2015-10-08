# -*- coding: utf-8 -*-
'''
Created on 2012-9-24

@author: mwang
'''
from MHLogin.api.v1.decorators import APIAuthentication
from MHLogin.api.v1.errlib import err_GE002, err_GE031
from MHLogin.api.v1.forms_sites import SiteSearchForm
from MHLogin.api.v1.utils import HttpJSONSuccessResponse
from MHLogin.api.v1.utils_sites import getSiteList, getSiteInfo, getSiteProviders, getSiteStaff, getSiteStudents

@APIAuthentication
def siteSearch(request):
	if (request.method != 'POST'):
		return err_GE002()
	form = SiteSearchForm(request.POST)
	if (not form.is_valid()):
		return err_GE031(form)

	data = getSiteList(form.cleaned_data)
	return HttpJSONSuccessResponse(data=data)

@APIAuthentication
def siteInfo(request, site_id):
	data = getSiteInfo(site_id)
	return HttpJSONSuccessResponse(data=data)
#
#
@APIAuthentication
def siteProviders(request, site_id):
	data = getSiteProviders(site_id)
	return HttpJSONSuccessResponse(data=data)

@APIAuthentication
def siteStaff(request, site_id):
	data = getSiteStaff(site_id)
	return HttpJSONSuccessResponse(data=data)

@APIAuthentication
def mySiteProviders(request):
	data = None
	if request.role_user and hasattr(request.role_user, "current_site") \
			and request.role_user.current_site:
		data = getSiteProviders(request.role_user.current_site.id)
	return HttpJSONSuccessResponse(data=data)

@APIAuthentication
def mySiteMedStudents(request):
	data = None
	if request.role_user and hasattr(request.role_user, "current_site") \
		and request.role_user.current_site:
		data = getSiteStudents(request.role_user.current_site.id)
	return HttpJSONSuccessResponse(data=data)

@APIAuthentication
def mySiteStaff(request):
	data = None
	if request.role_user and hasattr(request.role_user, "current_site") \
		and request.role_user.current_site:
		data = getSiteStaff(request.role_user.current_site.id)
	return HttpJSONSuccessResponse(data=data)

