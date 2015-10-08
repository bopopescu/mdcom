
import json
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from MHLogin.Invites.forms import inviteResendForm, ManagerInviteForm, inviteSendForm
from MHLogin.Invites.models import Invitation
from MHLogin.utils.templates import get_context

from MHLogin.utils.timeFormat import time_format, convert_dt_to_utz


def inviteHome(request):
	context = get_context(request)
	if (request.user.is_staff):
		invites = Invitation.objects.filter(sender=request.user, userType__in=(1, 2, 10)).all()
		context['user_is_staff'] = request.user.is_staff
	else:
		#context['outstandingInvites'] = Invitation.objects.filter(sender=request.user).all()
		#context['outstandingInvites'] = list(Invitation.objects.filter(
		# sender=request.session['MHL_UserIDs']['MHLUser'], assignPractice=None))
		invites = Invitation.objects.filter(
			sender=request.session['MHL_UserIDs']['MHLUser'], userType__in=(1, 2, 10))
	user = request.session['MHL_Users']['MHLUser']
	practice = context['current_practice']
	result = []

	for invite in invites:
		obj = {}
		obj['recipient'] = invite.recipient
		invite_time = convert_dt_to_utz(invite.requestTimestamp, user, practice)
		obj['requestTimestamp'] = time_format(user, invite_time)
		obj['code'] = invite.code
		obj['sender'] = invite.sender
		obj['id'] = invite.id
		result.append(obj)

	context['outstandingInvites'] = result
	return render_to_response('Invites/inviteHome.html', context)


def issueInvite(request):
	# Sales have their own invite view, we get here because ACL rules allow other
	# user types Provider, Physician, etc. to be Salespersons which is rare. 
	if ('Salesperson' in request.session['MHL_Users']):
		return HttpResponseRedirect(reverse('MHLogin.MHLUsers.Sales.views.new_invites'))
	if('Office_Manager' in request.session['MHL_UserIDs']):
		formclass = ManagerInviteForm
	else:
		formclass = inviteSendForm
	context = get_context(request)
	err = ''
	if (request.method == 'POST'):
		inviteForm = formclass(request.POST)
		if inviteForm.is_valid():
			if not User.objects.filter(email=request.POST['recipient']):
				invite = inviteForm.save(commit=False)
				#add by xlin in 20120509 for issue774
#				if 'Office_Manager' in request.session['MHL_UserIDs'] and 
							#int(inviteForm.cleaned_data['userType']) > 99:
#					invite.assignPractice = OfficeStaff.objects.filter(
#						user=request.user).only('current_practice').get().current_practice
				invite.sender = request.user

#				if('Office_Manager' in request.session['MHL_UserIDs']):
#					userType = inviteForm.cleaned_data['userType']
#				else:
#					userType = 1
				userType = inviteForm.cleaned_data['userType']
				invite.userType = userType

				invita = Invitation.objects.filter(recipient=request.POST['recipient'], 
							userType=userType, sender=request.user, assignPractice=None)
				if invita:
					invita[0].resend_invite()
				else:
					invite.save()
					if('Office_Manager' in request.session['MHL_UserIDs'] and 'createnow' in request.POST):
						return HttpResponseRedirect(invite.get_link({'createnow': True}))

					if (not invite.testFlag):
						invite.email_invite(inviteForm.cleaned_data['msg'])

				return HttpResponseRedirect(reverse('MHLogin.Invites.views.inviteHome'))
			else:
				err = _('This email address is already associated with a DoctorCom account.')
	else:
		inviteForm = formclass()

	context['inviteForm'] = inviteForm
	context['sender'] = request.session['MHL_UserIDs']['MHLUser']
	context['err'] = err
	return render_to_response('Invites/inviteIssue.html', context)


def resendInvite(request, inviteID):
	context = get_context(request)
	err = ''
	if (request.method == 'POST'):
		invite = Invitation.objects.get(id=inviteID)
		if not User.objects.filter(email=invite.recipient):
			if (not invite.testFlag):
				inviteResend = inviteResendForm(request.POST)
				msg = ''
				if (inviteResend.is_valid()):
					msg = inviteResend.cleaned_data['msg']
				invite.resend_invite(msg=msg)
			return HttpResponseRedirect(reverse('MHLogin.Invites.views.inviteHome'))
		else:
			err = _('At least one email address is already registered.')

	context['invite'] = Invitation.objects.get(id=inviteID)
	context['resend_form'] = inviteResendForm()
	context['err'] = err
	return render_to_response('Invites/inviteResendConfirm.html', context)


def cancelInvite(request, inviteID):
	context = get_context(request)

	if (request.method == 'POST'):
		invite = Invitation.objects.get(id=inviteID)
		#invite.delete(canceller=request.user, send_notice=True)
		invite.cancel_invitation()
		return HttpResponseRedirect(reverse('MHLogin.Invites.views.inviteHome'))

	context['invite'] = Invitation.objects.get(id=inviteID)
	invite = Invitation.objects.get(id=inviteID)
	context['cancel_invitation_tip'] = _("Are you sure you want to rescind the invitation to %s?") \
		% (invite.recipient)

	return render_to_response('Invites/inviteCancellationConfirm.html', context)


def cancelOrgInvite(request):
	inviteID = request.POST['id']
	try:
		invite = Invitation.objects.get(pk=inviteID)
		if invite:
			invite.cancel_invitation()
			return HttpResponse(json.dumps('ok'))
		else:
			return HttpResponse(json.dumps('err'))
	except:
		return HttpResponse(json.dumps('err'))


def resendOrgInvite(request):
	inviteID = request.POST['id']
	try:
		invite = Invitation.objects.get(pk=inviteID)
		invite.resend_invite()
		return HttpResponse(json.dumps('ok'))
	except:
		return HttpResponse(json.dumps('err'))


def resendInvitation(request):
	if request.method == 'POST':
		inviteID = request.POST['id']
		invite = Invitation.objects.get(id=inviteID)
		inviteResend = inviteResendForm(request.POST)
		msg = ''
		if (inviteResend.is_valid()):
			msg = inviteResend.cleaned_data['msg']

		invite.resend_invite(msg)
		if hasattr(invite, 'error'):
			return HttpResponse(json.dumps({'err': _('This email address is already '
							'associated with a DoctorCom account.')}))
		else:
			return HttpResponse(json.dumps({'err': 'ok'}))
	else:
		return HttpResponse(json.dumps(['err', _('A server error has occurred.')]))


def invitation_check_by_id(request):
	inviteID = request.POST['inviteID']
	invites = Invitation.objects.filter(id=inviteID)
	if invites:
		return HttpResponse(json.dumps('ok'))
	else:
		return HttpResponse(json.dumps('err'))


def invitation_check_with_email(request, practice_id=None):
	if request.method != 'POST':
		return HttpResponse(json.dumps('err'))

	user_type = get_data(request, 'type')

	#email is recipient's email for recipient
	email = get_data(request, 'email')
	if not practice_id:
		practice_id = get_data(request, 'practice')

	invites = Invitation.objects.all()
	if user_type:
		invites = invites.filter(userType=user_type)

	if email:
		invites = invites.filter(recipient=email)

	if practice_id:
		invites = invites.filter(assignPractice__pk=practice_id)

	if invites:
		return HttpResponse(json.dumps(invites[0].pk))
	return HttpResponse(json.dumps('err'))


def get_data(request, val):
	data = None
	if val in request.POST:
		data = request.POST[val]
	return data
