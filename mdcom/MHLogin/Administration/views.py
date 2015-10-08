
import datetime
import mimetypes
import re

from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import EmailMessage, get_connection
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.utils.translation import ugettext_lazy as _

from smtplib import SMTPResponseException

from MHLogin.Administration.forms import NameForm, EmailForm, PasswordForm, \
	PasswordChangeForm, AdminMessageForm, AdminInviteForm, MessageToAllForm,\
	GetAssignPracticeForm
from MHLogin.DoctorCom.IVR.models import \
	resolve_anssvc_dl_failures as models_resolve_anssvc_dl_failures
from MHLogin.DoctorCom.IVR.utils import save_voice_attachment
from MHLogin.DoctorCom.Messaging.exceptions import InvalidRecipientException
from MHLogin.DoctorCom.Messaging.models import Message, MessageRecipient, MessageAttachment
from MHLogin.Invites.models import Invitation
from MHLogin.KMS.shortcuts import encrypt_object
from MHLogin.KMS.utils import generate_keys_for_users, reset_user_invalid_keys, \
		generate_new_user_keys, strengthen_key
from MHLogin.KMS.models import import_rsa, OwnerPublicKey

from MHLogin.MHLUsers.models import MHLUser, Provider, PasswordResetLog, Office_Manager
from MHLogin.MHLPractices.models import PracticeLocation

from MHLogin.utils.errlib import err5xx
from MHLogin.utils.templates import get_context
from MHLogin.utils.timeFormat import time_format, convert_dt_to_utz

from MHLogin.MHLUsers.decorators import RequireAdministrator


suffix_re = re.compile('\.([^.]+)$')


def home(request):
	context = get_context(request)
	context['debug'] = settings.DEBUG
	return render_to_response('home.html', context)


@RequireAdministrator
def inviteHome(request):
	context = get_context(request)
	invites = Invitation.objects.filter(sender=request.user)
	user = request.session['MHL_Users']['MHLUser']
	practice = context['current_practice']

	result = []
	for invite in invites:
		obj = {}
		obj['recipient'] = invite.recipient
		invite_time = convert_dt_to_utz(invite.requestTimestamp, user, practice)
		obj['requestTimestamp'] = time_format(user, invite_time)
		obj['get_userType_display'] = invite.get_userType_display
		obj['typeVerified'] = invite.typeVerified
		obj['first_name'] = invite.sender.first_name
		obj['last_name'] = invite.sender.last_name
		obj['code'] = invite.code
		obj['testFlag'] = invite.testFlag
		obj['id'] = invite.id
		result.append(obj)
	context['outstandingInvites'] = result
	return render_to_response('inviteHome.html', context)


#modify by xlin in 20120604 for issue789
@RequireAdministrator
def issueInvite(request):
	context = get_context(request)
	err = ''
	if request.method == 'POST':
		inviteForm = AdminInviteForm(request.POST)
		if (inviteForm.is_valid()):
			if User.objects.filter(email=request.POST['recipient']):
				err = _('At least one email address is already registered.')
			else:
				pl = None
				if 'assignPractice' in request.POST and request.POST['assignPractice']:
					pl = PracticeLocation.objects.get(pk=request.POST['assignPractice'])

				if pl:
					inv = Invitation.objects.filter(sender=request.user, 
						userType=request.POST['userType'], 
						recipient=request.POST['recipient'], assignPractice=pl)
				else:
					inv = Invitation.objects.filter(sender=request.user, 
						userType=request.POST['userType'], 
						recipient=request.POST['recipient'])

				if inv:
					inv[0].resend_invite()
				else:
					invite = inviteForm.save(commit=False)
					invite.sender = request.user
					invite.assignPractice = pl
					invite.save()

					if not invite.testFlag:
						#from django.template.loader import render_to_string
						invite.email_invite()
				return HttpResponseRedirect(reverse('MHLogin.Administration.views.inviteHome'))
	else:
		if request.GET and request.GET['userType']:
			inviteForm = AdminInviteForm(initial={'userType': request.GET['userType']})
		else:
			inviteForm = AdminInviteForm()
	context['inviteForm'] = inviteForm
	context['err'] = err
	return render_to_response('inviteIssue.html', context)


@RequireAdministrator
def getAssignPractice(request):
	context = get_context(request)
	if request.method == 'POST':
		form = GetAssignPracticeForm(request.POST)
	else:
		form = GetAssignPracticeForm(request.GET)
	context['form'] = form
	return render_to_response('get_assign_practice.html', context)


@RequireAdministrator
def cancelInvite(request, inviteID):
	context = get_context(request)

	if (request.method == 'POST'):
		invite = Invitation.objects.filter(id=inviteID)
		if invite:
			invite[0].cancel_invitation()

#		if (not invite.testFlag):
#			from django.template.loader import render_to_string
#			emailContext = dict()
#			emailContext['code'] = invite.code
#			emailContext['email'] = invite.recipient
#			msgBody = render_to_string('inviteRevokeEmail.html', emailContext)
#			send_mail(_('DoctorCom Invitation'), msgBody, 'do-not-reply@myhealthincorporated.com',
#					[invite.recipient], fail_silently=False)
#		
#		invite.delete(canceller=request.user)

		return HttpResponseRedirect(reverse('MHLogin.Administration.views.inviteHome'))

	context['invite'] = Invitation.objects.get(id=inviteID)
	return render_to_response('inviteCancellationConfirm.html', context)


@RequireAdministrator
def admin_message_edit(request, userID):
	"""
	Handles message composition, editing, and drafts.

	:param request: The HTTP request
	:type request: django.core.handlers.wsgi.WSGIRequest  
	:param userID: user's ID
	:type userID: int
	:returns: django.http.HttpResponse -- The webpage 
	"""
	context = get_context(request)
	recipients = []
	form_initial_data = {'recipient': userID}

	if (request.method == 'POST'):
		form = AdminMessageForm(request.POST, request.FILES)

		if (form.is_valid()):
			recipients = [form.cleaned_data['recipient']]
			for recipient in recipients:
				try:
					recipient = MHLUser.objects.get(pk=recipient)
				except MHLUser.DoesNotExist:
					raise InvalidRecipientException()
				if (not recipient.is_active):
					raise InvalidRecipientException()

			# Build the message and body
			msg = Message(
					subject=form.cleaned_data['subject'],
					message_type=form.cleaned_data['message_type'],
					callback_number=form.cleaned_data.get('callback_number', ''),
				)
			msg.save()
			msg_body = msg.save_body(form.cleaned_data['body'])

			for recipient in recipients:
				MessageRecipient(message=msg, user_id=recipient).save()

			# Build the attachments
			attachments = []
			if ('file' in request.FILES):
				upload = request.FILES['file']
				attachment = encrypt_object(
						MessageAttachment,
						{
							'message': msg,
							'size': upload.size,
							'encrypted': True,
						},
						opub=OwnerPublicKey.objects.get_pubkey(owner=request.user))
				attachment.encrypt_url(request, ''.join(['file://', attachment.uuid]))
				attachment.encrypt_filename(request, upload.name)
				attachment.encrypt_file(request, upload.chunks())

				suffix = suffix_re.search(upload.name)
				if (suffix):
					attachment.suffix = suffix.group(1)[:255]
					(attachment.content_type, attachment.encoding) = mimetypes.guess_type(upload.name)
					attachment.charset = upload.charset

				attachment.save()
				attachments.append(attachment)
			if(form.cleaned_data['url']):
				request.POST['CallSid'] = ''
				request.session['ivr_makeRecording_recording'] = form.cleaned_data['url']
				request.session['ivr_makeRecording_callbacknumber'] = \
					form.cleaned_data['callback_number']
				attachment = save_voice_attachment(request, msg)
				attachments.append(attachment)
			# Send the message
			msg.send(request, msg_body, attachments)

			return HttpResponseRedirect('/')
		else:
			context['recipient'] = MHLUser.objects.get(pk=userID)
			context['form'] = form
	else:
		context['recipient'] = MHLUser.objects.get(pk=userID)
		context['form'] = AdminMessageForm(initial=form_initial_data)
	return render_to_response('admin_message.html', context)


@RequireAdministrator
def resolve_anssvc_dl_failures(request):
	models_resolve_anssvc_dl_failures()
	return HttpResponseRedirect('/dcAdmin/')


@RequireAdministrator
def generate_user_keys(request):
	generate_keys_for_users()
	context = get_context(request)
	return render_to_response('KeyGenerationComplete.html', context)


@RequireAdministrator
def get_user_for_reset(request):
	"""This view gets the user whose password is going to get reset. Note that we
	don't bother to pass form validation errors back.

	:param request: The HTTP request
	:type request: django.core.handlers.wsgi.WSGIRequest  
	:returns: django.http.HttpResponse -- The webpage 
	"""
	context = get_context(request)

	if (request.method == 'POST'):
		form = None
		search_by = request.POST['search_by']
		if (search_by == 'username' or
				search_by == 'firstname' or 
				search_by == 'lastname'):
			form = NameForm(request.POST)
		if (search_by == 'email'):
			form = EmailForm(request.POST)
		if (form.is_valid()):
			qs = MHLUser.objects  # this is going to contain the queryset for the users

			if (search_by == 'firstname'):
				qs = qs.filter(first_name__icontains=form.cleaned_data['name'])
			elif (search_by == 'lastname'):
				qs = qs.filter(last_name__icontains=form.cleaned_data['name'])
			elif (search_by == 'username'):
				qs = qs.filter(username__icontains=form.cleaned_data['name'])
			elif (search_by == 'email'):
				qs = qs.filter(email__icontains=form.cleaned_data['email'])

			context['users'] = qs
			return render_to_response('PasswordResetUserSearchResults.html', context)

	context['name_form'] = NameForm()
	context['email_form'] = EmailForm()

	return render_to_response('PasswordResetUserSearch.html', context)


# send email to all users	
@RequireAdministrator
def send_email_to_all_users(request):
	""" Sends emails to bulk users (all, providers, or office managers)

	:param request: The HTTP request
	:type request: django.core.handlers.wsgi.WSGIRequest  
	:returns: django.http.HttpResponse -- The webpage or back to parent page after POST 
	:raises: None 
	"""
	context = get_context(request)
	# add default subject and body template text to start off the message
	form_initial_data = {"body": "Message...\n\n\nBest,\nDoctorCom staff"}

	if (request.method == 'POST'):
		form = MessageToAllForm(request.POST)

		if (form.is_valid() == True):
			if (form.cleaned_data['emailfilter'] == 'everyone'):
				users = MHLUser.objects.all()	
			elif (form.cleaned_data['emailfilter'] == 'providers'):
				providers = Provider.objects.all()
				users = [provider.user for provider in providers]
			else:
				mgrs = Office_Manager.objects.all()
				users = [mgr.user.user for mgr in mgrs]

			# Build the message and body, empty emails allowed in bcc
			recipients = [user.email for user in users if user.email]
			connection = get_connection(fail_silently=False)
			msg = EmailMessage(form.cleaned_data['subject'],
				# TODO pickup from db instead of hard code
				form.cleaned_data['body'], 'support@mdcom.com', bcc=recipients,
				connection=connection)
			try:			
				msg.send()
				resp = HttpResponseRedirect('..')
			except SMTPResponseException, smtpe:
				msg = _("Problem sending email using email backend, details:\n\n%s") % \
					str(smtpe)
				resp = err5xx(request, code=smtpe.smtp_code, msg=msg)

			return resp
		else:
			context['form'] = form
	else:
		form = MessageToAllForm(initial=form_initial_data)

	context['form'] = form
	return render_to_response('send_message_to_all.html', context)


@RequireAdministrator
def reset_user_password(request, user_pk):
	"""
	This view resets the given user's password.

	:param request: The HTTP request
	:type request: django.core.handlers.wsgi.WSGIRequest  
	:param user_pk: user's ID (primary key)
	:type user_pk: int
	:returns: django.http.HttpResponse -- The webpage 
	"""
	context = get_context(request)
	user = context['user'] = MHLUser.objects.get(pk=user_pk)

	if (request.method == 'POST'):
		form = context['form'] = PasswordChangeForm(request.POST)
		if (form.is_valid()):
			PasswordResetLog.objects.create(user=user,
				reset=True, requestor=request.user,
				requestor_ip=request.META['REMOTE_ADDR'],
				reset_ip=request.META['REMOTE_ADDR'],
				reset_timestamp=datetime.datetime.now())
			# TODO: update when rm #2115 goes in
			generate_new_user_keys(user, form.cleaned_data['password1'])
			user.set_password(form.cleaned_data['password1'])
			user.save()
			return render_to_response('PasswordResetComplete.html', context)
	else:
		context['form'] = PasswordChangeForm()

	return render_to_response('PasswordReset.html', context)


@RequireAdministrator
def reset_private_keys(request):
	"""
	This view takes the KMS administrator password, and for each user whose
	password was reset, generates new private keys.

	:param request: The HTTP request
	:type request: django.core.handlers.wsgi.WSGIRequest  
	:returns: django.http.HttpResponse -- The webpage 
	"""
	context, resp = get_context(request), None
	log_qs = PasswordResetLog.objects.filter(reset=True, resolved=False).values('user')
	reset_users = context['reset_users'] = MHLUser.objects.filter(pk__in=log_qs)

	if request.method == 'POST':
		form = context['form'] = PasswordForm(request.POST)
		if form.is_valid():
			try:
				from MHLogin._admin_reset import ADMIN_RESET_ENCD_RSA
				creds = strengthen_key(form.cleaned_data['password'])
				admin_rsa = import_rsa(ADMIN_RESET_ENCD_RSA, creds)
			except ValueError:
				msg = _('Invalid password for admin reset key.')
				form._errors['password'] = form.error_class([msg])
			else:
				for user in reset_users:
					reset_user_invalid_keys(user, admin_rsa)
					PasswordResetLog.objects.filter(reset=True, resolved=False,
							user=user).update(resolved=True, servicer=request.user,
							servicer_ip=request.META['REMOTE_ADDR'],
							resolution_timestamp=datetime.datetime.now())
				resp = render_to_response('PrivateKeyResetComplete.html', context)
	else:
		context['form'] = PasswordForm()

	return resp or render_to_response('PrivateKeyReset.html', context)

