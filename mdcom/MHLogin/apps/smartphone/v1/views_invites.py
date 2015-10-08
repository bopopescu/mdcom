import json
from django.contrib.auth.models import User
from django.http import HttpResponse, Http404
from django.utils.translation import ugettext as _
from MHLogin.Invites.models import Invitation
from MHLogin.apps.smartphone.v1.decorators import AppAuthentication
from MHLogin.apps.smartphone.v1.errlib import err_GE002, err_GE031, err_IN002
from MHLogin.apps.smartphone.v1.forms_invites import NewInviteForm, \
	ResendInviteForm
from MHLogin.utils.constants import USER_TYPE_OFFICE_MANAGER, \
	USER_TYPE_OFFICE_STAFF
from MHLogin.utils.errlib import err403
from MHLogin.utils.timeFormat import formatTimeSetting, convertDatetimeToUTCTimestamp, \
	getCurrentTimeZoneForUser

@AppAuthentication
def list_invites(request):
#	if (request.method != 'POST'):
#		return err_GE002()
	
	user_type = int(request.user_type)
	if USER_TYPE_OFFICE_STAFF == user_type:
		return err403(request)

	invites = Invitation.objects.filter(sender=request.user).order_by('requestTimestamp')
	
	response = {
		'data': {'invitations':[]},
		'warnings': {},
	}
	
	invite_list = response['data']['invitations']
	
	use_time_setting = False
	if 'use_time_setting' in request.POST and request.POST['use_time_setting'] == 'true':
		use_time_setting = True
	user = request.user
	local_tz = getCurrentTimeZoneForUser(user)

	for invite in invites:
			desc = ''
			if not invite.assignPractice:
				desc = _('Invite to DoctorCom')
			else:
				desc = _('Invite to %s') % invite.assignPractice.practice_name
			invite_list.append({
						'id': invite.id,
						'recipient': invite.recipient,
						'timestamp': formatTimeSetting(user, invite.requestTimestamp, local_tz, use_time_setting),
						'request_timestamp': convertDatetimeToUTCTimestamp(invite.requestTimestamp),
						'desc' : desc,
						'code': invite.code,
				})
	
	return HttpResponse(content=json.dumps(response), mimetype='application/json')

@AppAuthentication
def new_invite(request):
	if (request.method != 'POST'):
		return err_GE002()
	
	user_type = int(request.user_type)
	role_user = request.role_user
	if USER_TYPE_OFFICE_STAFF == user_type:
		return err403(request)

	form = NewInviteForm(request.POST)
	if (not form.is_valid()):
		return err_GE031(form)

	invite_user_type = int(form.cleaned_data['invite_user_type'])
	invite_type = int(form.cleaned_data['invite_type'])
	recipient = form.cleaned_data['email']

	if USER_TYPE_OFFICE_MANAGER != user_type and 2 == invite_type:
		return err403(request)

	if User.objects.filter(email=recipient).exists():
		return err_IN002()

	note = ''
	if ('note' in form.cleaned_data and form.cleaned_data['note']):
		note = form.cleaned_data['note']

#	if (Invitation.objects.filter(recipient=form.cleaned_data['email']).exists()):
#		err_obj = {
#			'errno': 'IN001',
#			'descr': _('Recipient already has an outstanding invitation'),
#		}
#		return HttpResponseBadRequest(content=json.dumps(err_obj), mimetype='application/json')

	current_practice = role_user.current_practice
	invites = Invitation.objects.filter(sender=request.user, recipient=form.cleaned_data['email'], userType=invite_user_type)
	if 2 == invite_type and current_practice:
		invites = invites.filter(assignPractice=current_practice)
	else:
		invites = invites.filter(assignPractice=None)

	if (len(invites) > 0):
		invite = invites[0]
		invite.resend_invite(msg=note)
	else:
		invite = Invitation(
						sender=request.user,
						recipient=recipient,
						userType=invite_user_type,
					)
		if 2 == invite_type and current_practice:
			invite.assignPractice = current_practice
	
		invite.save()
		invite.email_invite(msg=note)
		
	use_time_setting = False
	if 'use_time_setting' in request.POST and request.POST['use_time_setting'] == 'true':
		use_time_setting = True
	user = request.user
	local_tz = getCurrentTimeZoneForUser(user)
	response = {
		'data': {
				'id':invite.id,
				'timestamp': formatTimeSetting(user, invite.requestTimestamp, local_tz, use_time_setting),
				'request_timestamp': convertDatetimeToUTCTimestamp(invite.requestTimestamp),
			},
		'warnings': {},
	}
		
	return HttpResponse(content=json.dumps(response), mimetype='application/json')


@AppAuthentication
def resend_invite(request, invitation_id):
	if (request.method != 'POST'):
		return err_GE002()
	
	user_type = int(request.user_type)
	if USER_TYPE_OFFICE_STAFF == user_type:
		return err403(request)

	note = ''
	if (request.method == 'POST'):
		form = ResendInviteForm(request.POST)
		if (not form.is_valid()):
			return err_GE031(form)
		if ('note' in form.cleaned_data):
			note = form.cleaned_data['note']

	try:
		invite = Invitation.objects.get(pk=invitation_id, sender=request.user)
	except Invitation.DoesNotExist:
		raise Http404

	if User.objects.filter(email=invite.recipient).exists():
		return err_IN002()
	invite.resend_invite(msg=note)
	
	use_time_setting = False
	if 'use_time_setting' in request.POST and request.POST['use_time_setting'] == 'true':
		use_time_setting = True
	user = request.user
	local_tz = getCurrentTimeZoneForUser(user)

	response = {
		'data': {
				'id': invite.id,
				'timestamp': formatTimeSetting(user, invite.requestTimestamp, local_tz, use_time_setting),
				'request_timestamp': convertDatetimeToUTCTimestamp(invite.requestTimestamp),
			},
		'warnings': {},
	}
	
	return HttpResponse(content=json.dumps(response), mimetype='application/json')

@AppAuthentication
def cancel_invite(request, invitation_id):
	user_type = int(request.user_type)
	if USER_TYPE_OFFICE_STAFF == user_type:
		return err403(request)

	try:
		invite = Invitation.objects.get(pk=invitation_id, sender=request.user)
	except Invitation.DoesNotExist:
		raise Http404
	
	invite.cancel_invitation()
	
	response = {
		'data': {},
		'warnings': {},
	}
	return HttpResponse(content=json.dumps(response), mimetype='application/json')

