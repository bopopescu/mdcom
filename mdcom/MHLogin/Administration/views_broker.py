import calendar
import datetime
import json
import time
from pytz import timezone
from datetime import date
from dateutil.relativedelta import relativedelta

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db.models import Count, Q
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response

from MHLogin.Administration.forms import BrokerQueryForm, ReferTrackingForm
from MHLogin.DoctorCom.IVR.models import callLog
from MHLogin.DoctorCom.Messaging.models import Message, MessageRefer, \
	MessageRecipient

from MHLogin.DoctorCom.Messaging.views_ajax import sender_name_safe

from MHLogin.Invites.models import Invitation
from MHLogin.MHLUsers.decorators import RequireAdministrator
from MHLogin.MHLUsers.models import MHLUser, Broker
from MHLogin.utils.templates import get_context
from MHLogin.utils.timeFormat import time_format, formatTimeSetting,\
	getCurrentTimeZoneForUser, convert_dt_to_utz


@RequireAdministrator
def broker_page(request):
	context = get_context(request)
	now = datetime.datetime.now()
	day_latest = int(time.mktime((now - datetime.timedelta(days=30)).timetuple()))
	str_count_latest = 'SELECT COUNT(*) FROM Messaging_message WHERE Messaging_message.'\
		'sender_id = MHLUsers_broker.user_id and send_timestamp > %d' % day_latest
	broker_list = Broker.objects.extra(select={
						'count_all': 'SELECT COUNT(*) FROM Messaging_message WHERE '\
						'Messaging_message.sender_id = MHLUsers_broker.user_id',
						'count_latest': str_count_latest
					})

	context['broker_list'] = broker_list

	user = request.session['MHL_Users']['MHLUser']
	practice = context['current_practice']
	invites = Invitation.objects.filter(sender=request.user, userType=300).all()

	result = []
	for invite in invites:
		obj = {}
		invite_time = convert_dt_to_utz(invite.requestTimestamp, user, practice)
		obj['requestTimestamp'] = time_format(user, invite_time)
		obj['recipient'] = invite.recipient
		obj['code'] = invite.code
		obj['id'] = invite.id
		result.append(obj)

	context['invitation_list'] = result

	return render_to_response('broker_list.html', context)


@RequireAdministrator
def broker_tracking(request):
	context = get_context(request)
	broker_user_id = None

	try:
		broker_user_id = request.GET['user_id']
		context['broker_user_id'] = broker_user_id
	except:
		pass

	broker_from = broker_user_id or - 1
	broker_to = ''
	directions = 1
	period_from = ''
	period_to = ''

	if (request.method == 'POST'):
		form = BrokerQueryForm(request.POST)
		if form.is_valid():
			broker_from = int(form.cleaned_data['broker_from'])
			broker_to = form.cleaned_data['broker_to']
			directions = int(form.cleaned_data['directions'])
			period_from = form.cleaned_data['period_from']
			period_to = form.cleaned_data['period_to']

	form_init_data = {'directions': directions, 'broker_from': broker_from, 
			'broker_to': broker_to, 'period_from': period_from, 'period_to': period_to}
	context['form'] = BrokerQueryForm(initial=form_init_data)
	return render_to_response('broker_tracking.html', context)


@RequireAdministrator
def refer_tracking(request):
	context = get_context(request)
	form_init_data = {'period_from': date.today() + relativedelta(months=-1), 
					'period_to': date.today(), 'period_radio': '1', 'period_type': 9}
	if (request.method == 'POST'):
		form = ReferTrackingForm(request.POST)
		if form.is_valid():
			period_type = form.cleaned_data['period_type']
			period_radio = form.cleaned_data['period_radio']
			period_from = form.cleaned_data['period_from']
			period_to = form.cleaned_data['period_to']
			if(period_radio == '0'):
				period_from, period_to = get_peirod(period_type)
			form_init_data = {'period_from': period_from, 'period_to': period_to, 
					'period_radio': period_radio, 'period_type': period_type}
	context['form'] = ReferTrackingForm(initial=form_init_data)
	return render_to_response('refer_tracking.html', context)


@RequireAdministrator
def refer_tracking_detail(request, userID):
	context = get_context(request)
	context['userID'] = userID
	if (request.method == 'POST'):
		form = ReferTrackingForm(request.POST)
		if form.is_valid():
			period_type = form.cleaned_data['period_type']
			period_radio = form.cleaned_data['period_radio']
			period_from = form.cleaned_data['period_from']
			period_to = form.cleaned_data['period_to']
			if(period_radio == '0'):
				period_from, period_to = get_peirod(period_type)
			form_init_data = {'period_from': period_from, 'period_to': period_to, 
					'period_radio': period_radio, 'period_type': period_type}
			context['form'] = ReferTrackingForm(initial=form_init_data)
	return render_to_response('refer_tracking_detail.html', context)


@RequireAdministrator
def broker_tracking_ajax_message(request):

	broker_from = -1
	broker_to_name = '' 
	broker_to = ''
	directions = 1
	period_from = ''
	period_to = ''

	page_index = 1
	items_per_page = 10
	try:
		page_index = int(request.POST['page_index'])
		items_per_page = int(request.POST['items_per_page'])
	except:
		pass

	number_end = page_index * items_per_page
	number_begin = number_end - items_per_page

	broker_list = [broker.user.id for broker in Broker.objects.all()]
	if (request.method == 'POST'):
		form = BrokerQueryForm(request.POST)
		if form.is_valid():
			broker_from = int(form.cleaned_data['broker_from'])
			broker_to_name = form.cleaned_data['broker_to']
			directions = int(form.cleaned_data['directions'])
			period_from = form.cleaned_data['period_from']
			period_to = form.cleaned_data['period_to']

			broker_to = get_id_by_name(broker_to_name)

	message_list_all = Message.objects.all().select_related('recipients')
	q_message = Q()

	if broker_from == -1:
		q_message.add(Q(sender__in=broker_list), Q.OR)
		q_message.add(Q(recipients__in=broker_list), Q.OR)
		if directions == 2:
			q_message.add(Q(recipients__in=broker_list), Q.AND)
		elif directions == 3:
			q_message.add(Q(sender__in=broker_list), Q.AND)
	else:
		q_message.add(Q(sender=broker_from), Q.OR)
		q_message.add(Q(recipients=broker_from), Q.OR)

		if directions == 2:
			q_message.add(Q(recipients=broker_from), Q.AND)
		elif directions == 3:
			q_message.add(Q(sender=broker_from), Q.AND)

	if broker_to_name:
		q_message.add(Q(sender=broker_to) | Q(recipients=broker_to), Q.AND)
		if directions == 2:
			q_message.add(Q(sender=broker_to), Q.AND)
		elif directions == 3:
			q_message.add(Q(recipients=broker_to), Q.AND)

	if period_from:
		q_message.add(Q(send_timestamp__gte=int(time.mktime(period_from.timetuple()))), Q.AND)
	if period_to:
		period_to_cal = period_to + datetime.timedelta(days=1)
		q_message.add(Q(send_timestamp__lt=int(time.mktime(period_to_cal.timetuple()))), Q.AND)

	user = request.session['MHL_Users']['MHLUser']
	local_tz = getCurrentTimeZoneForUser(user)
	message_list = [{
						'time':formatTimeSetting(user, str(msg.send_timestamp), local_tz),
						'sender':sender_name_safe(msg),
						'recipients':', '.join([' '.join([
							u.first_name, u.last_name
						]) for u in msg.recipients.all()]),
					} for msg in message_list_all.filter(q_message)[number_begin:number_end]]

	return HttpResponse(json.dumps({
				'messageCount': message_list_all.filter(q_message).count(),
				'messages': message_list
			}))


@RequireAdministrator
def get_id_by_name(broker_to_name):
	broker_to = None

	if not broker_to_name:
		return broker_to

	search_terms = unicode.split(broker_to_name)
	return_set = MHLUser.objects.filter()
	for term in search_terms:
		return_set = return_set.filter(
					Q(first_name__icontains=term) | 
					Q(last_name__icontains=term))
	return_set = return_set.only('id')
	if return_set:
		broker_to = return_set[0].id
	return broker_to


@RequireAdministrator
def broker_tracking_ajax_call(request):
	broker_from = -1
	broker_to = ''
	broker_to_name = '' 
	directions = 1
	period_from = ''
	period_to = ''

	page_index = 1
	items_per_page = 10
	try:
		page_index = int(request.POST['page_index'])
		items_per_page = int(request.POST['items_per_page'])
	except:
		pass

	number_end = page_index * items_per_page
	number_begin = number_end - items_per_page
	broker_list = [broker.user.id for broker in Broker.objects.all()]

	if (request.method == 'POST'):
		form = BrokerQueryForm(request.POST)
		if form.is_valid():
			broker_from = int(form.cleaned_data['broker_from'])
			broker_to_name = form.cleaned_data['broker_to']
			directions = int(form.cleaned_data['directions'])
			period_from = form.cleaned_data['period_from']
			period_to = form.cleaned_data['period_to']
			broker_to = get_id_by_name(broker_to_name)

	call_list_all = callLog.objects.all().order_by('-timestamp')
	q_call = Q()

	if broker_from == -1:
		q_call.add(Q(caller_id__in=broker_list), Q.OR)
		q_call.add(Q(called_id__in=broker_list), Q.OR)
		if directions == 2:
			q_call.add(Q(called_id__in=broker_list), Q.AND)
		elif directions == 3:
			q_call.add(Q(caller_id__in=broker_list), Q.AND)
	else:
		q_call.add(Q(caller_id=broker_from), Q.OR)
		q_call.add(Q(called_id=broker_from), Q.OR)

		if directions == 2:
			q_call.add(Q(called_id=broker_from), Q.AND)
		elif directions == 3:
			q_call.add(Q(caller_id=broker_from), Q.AND)

	if broker_to_name:
		q_call.add(Q(caller_id=broker_to) | Q(called_id=broker_to), Q.AND)
		if directions == 2:
			q_call.add(Q(caller_id=broker_to), Q.AND)
		elif directions == 3:
			q_call.add(Q(called_id=broker_to), Q.AND)

	if period_from:
		q_call.add(Q(timestamp__gte=period_from), Q.AND)
	if period_to:
		period_to_cal = period_to + datetime.timedelta(days=1)
		q_call.add(Q(timestamp__lte=period_to_cal), Q.AND)

	call_list = [{
					'datetime':call.timestamp.strftime('%m/%d/%y %H:%M'),
					'duration':call.call_duration if call.call_duration else '',
					'caller': getUserNameById(call.caller_id),
					'called':getUserNameById(call.called_id)
				} for call in call_list_all.filter(q_call)[number_begin:number_end]]

	return HttpResponse(json.dumps({
				'callCount': call_list_all.filter(q_call).count(),
				'calls': call_list
			}))


@RequireAdministrator
def broker_update_active(request):
	userId = request.POST['userId']
	user = MHLUser.objects.get(id=userId)
	user.is_active = not user.is_active
	user.save()
	result = {'statusAccount': user.is_active}
	response = HttpResponse(json.dumps(result), mimetype='application/json')
	return response


@RequireAdministrator
def update_broker_invite(request, inviteID, isCancel=''):
	context = get_context(request)
	context['isCancel'] = isCancel
	err = ''
	if (request.method == 'POST'):
		invite = Invitation.objects.get(id=inviteID)
		if isCancel:
#			if (not invite.testFlag):
#				emailContext = dict()
#				emailContext['code'] = invite.code
#				emailContext['email'] = invite.recipient
#				msgBody = render_to_string('inviteRevokeEmail.html', emailContext)
#				send_mail('DoctorCom Invitation', msgBody, 'do-not-reply@myhealthincorporated.com',
#						[invite.recipient], fail_silently=False)
#			invite.delete(canceller=request.user)
			invite.cancel_invitation()
			return HttpResponseRedirect(reverse('MHLogin.Administration.views_broker.broker_page'))
		else:
#			if (not invite.testFlag):
#				emailContext = dict()
#				invite.resend_invite()
			invite.resend_invite()
			if hasattr(invite, 'error'):
				err = invite.error
			else:
				return HttpResponseRedirect(reverse('MHLogin.Administration.views_broker.broker_page'))

	context['invite'] = Invitation.objects.get(id=inviteID)
	context['err'] = err
	return render_to_response('broker_invite_confirm.html', context)


@RequireAdministrator
def refer_tracking_ajax(request):
	page_index = 1
	items_per_page = 10
	try:
		page_index = int(request.POST['page_index'])
		items_per_page = int(request.POST['items_per_page'])
	except:
		pass

	number_end = page_index * items_per_page
	number_begin = number_end - items_per_page

	if (request.method == 'POST'):
		form = ReferTrackingForm(request.POST)
		if form.is_valid():
			period_type = form.cleaned_data['period_type']
			period_radio = form.cleaned_data['period_radio']
			period_from = form.cleaned_data['period_from']
			period_to = form.cleaned_data['period_to']
			if(period_radio == '0'):
				period_from, period_to = get_peirod(period_type)

	q_refer = Q()
	recipients_all = MessageRecipient.objects.values('user').annotate(count=Count('user'))

	refer_list_all = MessageRefer.objects.values('message')
	if period_from:
		q_refer.add(Q(message__send_timestamp__gte=int(time.mktime(period_from.timetuple()))), Q.AND)
	if period_to:
		period_to_cal = period_to + datetime.timedelta(days=1)
		q_refer.add(Q(message__send_timestamp__lt=int(time.mktime(period_to_cal.timetuple()))), Q.AND)

	r_recipients = [refer['message'] for refer in refer_list_all.filter(q_refer)]
	recipients = recipients_all.filter(message__in=r_recipients)

	refer_list = []
	for refer in recipients[number_begin:number_end]:
		user = MHLUser.objects.get(id=int(refer['user']))
		name = ' '.join([user.first_name, user.last_name])
		refer_list.append({'id': user.id, 'name': name, 'count': refer['count']})

	return HttpResponse(json.dumps({
				'referCount': len(recipients) or 0,
				'refers': refer_list
			}))


@RequireAdministrator
def refer_tracking_detail_ajax(request, userID):
	page_index = 1
	items_per_page = 10
	try:
		page_index = int(request.POST['page_index'])
		items_per_page = int(request.POST['items_per_page'])
	except:
		pass

	number_end = page_index * items_per_page
	number_begin = number_end - items_per_page

	if (request.method == 'POST'):
		form = ReferTrackingForm(request.POST)
		if form.is_valid():
			period_type = form.cleaned_data['period_type']
			period_radio = form.cleaned_data['period_radio']
			period_from = form.cleaned_data['period_from']
			period_to = form.cleaned_data['period_to']
			if(period_radio == '0'):
				period_from, period_to = get_peirod(period_type)

	q_refer = Q()
	refer_list_all = MessageRefer.objects.all().order_by('message__send_timestamp')

	recipients = MessageRecipient.objects.values('message').filter(user=userID)
	r_recipients = [rep['message'] for rep in recipients]
	q_refer.add(Q(message__in=r_recipients), Q.AND)
	if period_from:
		q_refer.add(Q(message__send_timestamp__gte=int(time.mktime(period_from.timetuple()))), Q.AND)
	if period_to:
		period_to_cal = period_to + datetime.timedelta(days=1)
		q_refer.add(Q(message__send_timestamp__lt=int(time.mktime(period_to_cal.timetuple()))), Q.AND)

	user = request.session['MHL_Users']['MHLUser']
	refer_list = [{
						#'time':timezone_conversion(refer.message.send_timestamp, 
						#	timezone(settings.TIME_ZONE)).strftime('%m/%d/%y %H:%M'),
						'time':formatTimeSetting(user, refer.message.send_timestamp, timezone(settings.TIME_ZONE)),
						'sender':sender_name_safe(refer.message),
						'practice': refer.practice.practice_name if refer.practice else '',
						'recipients':', '.join([' '.join([u.first_name, u.last_name]) 
											for u in refer.message.recipients.all()]),
					} for refer in refer_list_all.filter(q_refer)[number_begin:number_end]]
	return HttpResponse(json.dumps({
				'referCount': refer_list_all.filter(q_refer).count() or 0,
				'refers': sorted(refer_list, key=lambda k: k['time'], reverse=True)
			}))


def getUserNameById(id):
	if not id:
		return ''
	user = MHLUser.objects.get(id=id)
	if user and id:
		return ' '.join([user.first_name, user.last_name])
	else:
		return ''


def get_peirod(period_type):
	type = int(period_type)
	today = date.today()

	if type == 1:  # all time
		return None, None
	elif type == 2:  # today
		return today, today
	elif type == 3:  # yesterday
		yesterday = today + relativedelta(days=-1)
		return yesterday, yesterday
	elif type == 4:  # this week
		week_begin = today + relativedelta(weekday=calendar.MONDAY, days=-6)
		week_end = week_begin + relativedelta(days=6)
		return week_begin, week_end
	elif type == 5:  # last week
		week_begin = today + relativedelta(weekday=calendar.MONDAY, days=-13)
		week_end = week_begin + relativedelta(days=6)
		return week_begin, week_end
	elif type == 6:  # last 7 days
		return today + relativedelta(days=-6), today
	elif type == 7:  # this month
		return today + relativedelta(day=1), today + relativedelta(day=31)
	elif type == 8:  # last month
		return today + relativedelta(months=-1, day=1), today + relativedelta(months=-1, day=31)
	elif type == 9:  # last 30 days
		return today + relativedelta(days=-30), today
	elif type == 10:  # this year
		return today + relativedelta(month=1, day=1), today + relativedelta(month=12, day=31)

	return None, None

