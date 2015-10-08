
import datetime
import json
import re
import string

from MHLogin.followup.models import FollowUps
from MHLogin.followup.forms import AddFollowUpForm, FollowUpForm
from MHLogin.utils.templates import get_context
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response, get_object_or_404
from django.utils.translation import ugettext_lazy as _
from MHLogin.DoctorCom.Messaging.models import Message, MessageBody
from django.http import Http404

from MHLogin.utils.errlib import err403, err404
from MHLogin.utils.timeFormat import convert_dt_to_stz, convert_dt_to_utz

# Create your views here.

def get_followups(user, index=0, itemsPerPage=10, mhluser=None, practice=None):
	followups = FollowUps.objects.filter(user=user).exclude(deleted=True)[itemsPerPage * index:itemsPerPage * (index + 1)]
	followup_count = len(FollowUps.objects.filter(user=user))
	for f in followups:
		f.due_date = convert_dt_to_utz(f.due_date, mhluser, practice)
	return (followups, followup_count)

def get_all_followups(user):
	followups = FollowUps.objects.filter(user=user).exclude(deleted=True)
	followup_count = len(followups)
	return (followups, followup_count)

VALID_OBJECT_TYPES = ('Message',)
uuid_re = re.compile(r'([0-9a-f]{32})$')
id_re = re.compile(r'[0-9]{,16}$')
def addFollowUp(request, messageID, msg_obj_str=''):
	#raise Exception('foo')
	#raise Exception(', '.join([repr(type(messageID)), messageID, repr(type(msg_obj_str)), msg_obj_str]))

	#raise Exception(messageId, msg_obj_str)
	if (msg_obj_str in VALID_OBJECT_TYPES):
		# The below code is temporary, pending Brian's new secure messaging
		# code. - BK
		if (msg_obj_str == 'Message'):
			uuid_match = uuid_re.match(messageID)
			id_match = id_re.match(messageID)
			id = None
			if (uuid_match):
				id = Message.objects.filter(uuid=uuid_match.group(1)).values_list('id', flat=True)
				if (len(id) != 1):
					raise Exception(_('More than one message was found with uuid %s.') % (uuid_match.group(1),))
				id = id[0]
			elif (id_match):
				id = int(messageID)
			else:
				# Validation error!
				return err404(request)
			
			msg_obj = get_object_or_404(Message, pk=id)
			if (msg_obj.sender != request.user and request.user not in msg_obj.recipients.all() and request.user not in msg_obj.ccs.all()):
				return err403(request, err_msg=_("You don't seem to own the message that you're trying to create a follow-up item for."))

		# Rana's original code follows. We'll return to this once we get
		# access verification for a user installed into relevant classes.
		# Additionally, we need a standardized way to get followup strings
		# out of all objects before this will work.
		# msg_str = "get_object_or_404(%s, pk=%s)" % (msg_obj_str, messageID)
		# msg_obj = eval(msg_str)
	else:
		return err404(request)

	context = get_context(request)

	if (request.method == "POST"):
		addfollowup_form = AddFollowUpForm(request.POST)

		if (addfollowup_form.is_valid()):
			followup_obj = addfollowup_form.save(commit=False)
			followup_obj.user = request.user
			followup_obj.msg_object = msg_obj
			user = request.session['MHL_Users']['MHLUser']
			practice = context['current_practice']
			followup_obj.due_date =convert_dt_to_stz(
													followup_obj.due_date, user, practice)
			followup_obj.save()

			return HttpResponseRedirect(reverse('MHLogin.MHLogin_Main.views.main'))

		else: # if not (addfollowup_form.is_valid()):
			context['addfollowup_form'] = addfollowup_form

	else: # if (request.method != "POST"):
		init_followup = {}
		if (msg_obj_str == 'Message'):
			body = MessageBody.objects.get(message=msg_obj).decrypt(request)
			init_followup['note'] = body
			init_followup['task'] = _('Followup on: ') + body[:30] + '...'
		else:
			init_followup['note'] = ''
			init_followup['task'] = ''
		if ('taskname' in request.GET):
			init_followup['task'] = request.GET['taskname']
		if ('duedate' in request.GET):
			init_followup['due_date'] = request.GET['duedate']
		context['addfollowup_form'] = AddFollowUpForm(initial=init_followup)

	context['messageID'] = messageID
	context['msg_obj_str'] = msg_obj_str

	return render_to_response('FollowUp/addfollowup.html', context)

def addFollowUpAjax(request):
	context = get_context(request)
	count = int(request.POST['count'])
	if (request.method == "POST"):
		form = AddFollowUpForm(request.POST)
		task = request.POST['task']
		if len(task.strip()) == 0:
			return err403(request, err_msg=_("The task is invalid."))
		if (form.is_valid()):
			#raise Exception('foo')
			f_obj = form.save(commit=False)
			f_obj.user = request.user
			user = request.session['MHL_Users']['MHLUser']
			practice = context['current_practice']
			f_obj.due_date =convert_dt_to_stz(f_obj.due_date, user, practice)
			f_obj.save()
		else:
			field_errors = dict()
			for name in form._errors:
				field_errors[name] = [unicode(err) for err in form._errors[name]]
			non_field_errors = [unicode(err) for err in form.non_field_errors()]
			return_obj = dict()
			return_obj['error_type'] = 'form_validation'
			return_obj['non_field_errors'] = non_field_errors
			return_obj['field_errors'] = field_errors
			return HttpResponse(json.dumps(return_obj), mimetype="application/json", status=400)
	
	mhluser = request.session['MHL_Users']['MHLUser']
	followup = get_followups(request.user, 0, count, mhluser, context['current_practice'])

	context['followups'] = followup[0]
	context['followup_count'] = followup[1]
	return render_to_response('FollowUp/donefollowup.html', context)

def addFollowUpAjaxOffset(request, offset, count):
	offset = int(offset)
	count = int(count)
	context = get_context(request)
	
	mhluser = request.session['MHL_Users']['MHLUser']
	followup = get_followups(request.user, offset, count, mhluser, context['current_practice'])
	context['followups'] = followup[0]
	context['followup_count'] = followup[1]

	for i in followup[0]:
		i.note = string.strip(i.note)
	

	return render_to_response('FollowUp/donefollowup.html', context)

def editFollowUp(request, followupID):
	followup = get_object_or_404(FollowUps, id=followupID)
	if (followup.user != request.user):
		return err403(request, err_msg=_("You don't seem to own this follow-up item."))
	if (followup.deleted):
		raise Http404

	# Get the context *after* the ownership check. After all, why do all that
	# work if we're just going to return HTTP403?
	context = get_context(request)
	user = request.session['MHL_Users']['MHLUser']
	practice = context['current_practice']

	if followup:
		followup.due_date = convert_dt_to_utz(followup.due_date, user, practice)

	if (request.method == "POST"):
		editfollowup_form = FollowUpForm(request.POST, instance=followup)

		if (editfollowup_form.is_valid()):
			followup_obj = editfollowup_form.save(commit=False)
			if (followup_obj.done and not followup_obj.completion_date):
				followup_obj.completion_date = datetime.datetime.today()
			elif (not followup_obj.done):
				followup_obj.completion_date = None
			followup_obj.due_date =convert_dt_to_stz(followup_obj.due_date, user, practice)
			followup_obj.save()
			return HttpResponseRedirect(reverse('MHLogin.MHLogin_Main.views.main'))

		else: # if not (editfollowup_form.is_valid()):
			context['form_id'] = followupID
			context['editfollowup_form'] = editfollowup_form

	else: # if (request.method != "POST"):
		context['form_id'] = followupID
		context['editfollowup_form'] = FollowUpForm(instance=followup)
	return render_to_response('FollowUp/editfollowup.html', context)

def delFollowUp(request, followupID, count):
	followup = get_object_or_404(FollowUps, id=followupID)
	count = int(count)
	if (followup.user != request.user):
		return err403(request, err_msg=_("You don't seem to own this follow-up item."))
	if (followup.deleted):
		raise Http404

	if (followup.user == request.user):
		followup.deleted = True
		followup.save()
		context = get_context(request)
	
	mhluser = request.session['MHL_Users']['MHLUser']
	followup = get_followups(request.user, 0, count, mhluser, context['current_practice'])

	context['followups'] = followup[0]
	context['followup_count'] = followup[1]

	return render_to_response('FollowUp/donefollowup.html', context)

def doneFollowUp(request, followupID, offset, count):
	"""
	This function will toggle the state of the task as being done or not.
	It is used by an AJAX jQuery load method which updates the table that displays
	the follow up tasks.
	"""
	followup = get_object_or_404(FollowUps, id=followupID)
	offset = int(offset)
	count = int(count)
	if (followup.user != request.user):
		return err403(request, err_msg="You don't seem to own this follow-up item.")
	if (followup.deleted):
		raise Http404

	if (followup.user == request.user):
		if (not followup.done and not followup.completion_date):
			followup.done = True
			followup.completion_date = datetime.datetime.today()
		elif (not followup.done and followup.completion_date):
			followup.done = True
			followup.completion_date = datetime.datetime.today()
		elif (followup.done):
			followup.done = False
			followup.completion_date = None
		followup.save()
	context = get_context(request)
	
	mhluser = request.session['MHL_Users']['MHLUser']
	followup = get_followups(request.user, offset, count, mhluser, context['current_practice'])

	context['followups'] = followup[0]
	context['followup_count'] = followup[1]

	return render_to_response('FollowUp/donefollowup.html', context)

def reloadFollowUp(request, offset, count):
	"""
	This function will reload followups using AJAX.
	"""
	context = get_context(request)
	offset = int(offset)
	count = int(count)
	mhluser = request.session['MHL_Users']['MHLUser']
	followup = get_followups(request.user, offset, count, mhluser, context['current_practice'])
	context['followups'] = followup[0]
	context['followup_count'] = followup[1]
	
	return render_to_response('FollowUp/donefollowup.html', context)
