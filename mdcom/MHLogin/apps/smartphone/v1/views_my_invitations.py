# -*- coding: utf-8 -*-
'''
Created on 2012-11-30

@author: mwang
'''

import json

from django.http import HttpResponse

from MHLogin.MHLUsers.utils import get_fullname
from MHLogin.apps.smartphone.v1.decorators import AppAuthentication
from MHLogin.Invites.utils import getUserInvitationPendings, acceptToJoinPractice, rejectToJoinPractice,\
	getInvitationPendings
from MHLogin.apps.smartphone.v1.forms_invites import HandleInviteForm
from MHLogin.apps.smartphone.v1.errlib import err_GE002, err_GE031
from MHLogin.MHLOrganization.utils_org_member import accept_member_org_invite,\
	rejected_member_org_invite
from MHLogin.MHLCallGroups.Scheduler.views_multicallgroup import join_call_group

@AppAuthentication
def getMyInvitations(request):
	response = {
		'data': getUserInvitationPendings(request.user, request.user_type),
		'warnings': {},
	}

	return HttpResponse(content=json.dumps(response), mimetype='application/json')

@AppAuthentication
def acceptOrgInvitation(request, pending_id):
	acceptToJoinPractice(request.user, pending_id, provider = request.role_user)
	response = {
		'data': {},
		'warnings': {},
	}
	return HttpResponse(content=json.dumps(response), mimetype='application/json')

@AppAuthentication
def refuseOrgInvitation(request, pending_id):
	rejectToJoinPractice(request.user, pending_id)
	response = {
		'data': {},
		'warnings': {},
	}
	return HttpResponse(content=json.dumps(response), mimetype='application/json')

@AppAuthentication
def acceptPracticeInvitation(request, pending_id):
	acceptToJoinPractice(request.user, pending_id, provider = request.role_user)

	response = {
		'data': {},
		'warnings': {},
	}
	return HttpResponse(content=json.dumps(response), mimetype='application/json')

@AppAuthentication
def refusePracticeInvitation(request, pending_id):
	rejectToJoinPractice(request.user, pending_id)

	response = {
		'data': {},
		'warnings': {},
	}
	return HttpResponse(content=json.dumps(response), mimetype='application/json')

@AppAuthentication
def getInvitations(request):
	rquest_host = '%s://%s' % (request.is_secure() and 'https' or 'http',request.get_host())
	response = {
		'data': getInvitationPendings(rquest_host, request.user, request.role_user, request.user_type),
		'warnings': {},
	}

	return HttpResponse(content=json.dumps(response), mimetype='application/json')

@AppAuthentication
def acceptInvitation(request, pending_id):
	if (request.method != 'POST'):
		return err_GE002()

	form = HandleInviteForm(request.POST)
	if (not form.is_valid()):
		return err_GE031(form)
	
	invite_type = form.cleaned_data['invite_type']
	user_id = request.user.id
	ret_data = {}
	if invite_type == 1:
		ret_data = acceptToJoinPractice(request.user, pending_id, provider = request.role_user)
	elif invite_type == 3:
		ret_data = join_call_group(pending_id, "Accept", request.role_user)
	else:
		ret_data = accept_member_org_invite(user_id, pending_id)
	response = {
		'data': ret_data,
		'warnings': {},
	}
	return HttpResponse(content=json.dumps(response), mimetype='application/json')

@AppAuthentication
def refuseInvitation(request, pending_id):
	if (request.method != 'POST'):
		return err_GE002()

	form = HandleInviteForm(request.POST)
	if (not form.is_valid()):
		return err_GE031(form)
	
	invite_type = form.cleaned_data['invite_type']
	mhluser_id = request.user.id
	first_name = request.user.first_name
	last_name = request.user.last_name
	fullname=get_fullname(request.user)
	ret_data = {}
	if	invite_type == 1:
		ret_data = rejectToJoinPractice(request.user, pending_id)
	elif invite_type == 3:
		ret_data = join_call_group(pending_id, "Reject", request.role_user)
	else:
		ret_data = rejected_member_org_invite(mhluser_id, fullname, pending_id)
	response = {
		'data': ret_data,
		'warnings': {},
	}
	return HttpResponse(content=json.dumps(response), mimetype='application/json')

