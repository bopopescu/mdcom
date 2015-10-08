
from datetime import datetime
from pytz import timezone
import json
import time

from django.conf import settings
from django.db.models import Q
from django.http import HttpResponse, Http404

from MHLogin.followup.models import FollowUps
from MHLogin.apps.smartphone.v1.errlib import err_GE002, err_GE031
from MHLogin.apps.smartphone.v1.forms_followups import TaskDeltaForm, NewTaskForm, \
	TaskListForm, UpdateTaskForm
from MHLogin.apps.smartphone.v1.decorators import AppAuthentication
from MHLogin.apps.smartphone.v1.utils import TIME_DISPLAY_FORMAT
from MHLogin.utils.timeFormat import timezone_conversion, convertDatetimeToUTCTimestamp


@AppAuthentication
def list_tasks(request):
	if (request.method != 'POST'):
		return err_GE002()
	form = TaskListForm(request.POST)
	if (not form.is_valid()):
		return err_GE031(form)

	response = {
		'data': {},
		'warnings': {},
	}
	data = response['data']
	qs = FollowUps.objects.filter(user=request.user)

	data['total_task_count'] = qs.count()
	data['incomplete_task_count'] = qs.filter(done=False).count()

	local_tz = timezone(settings.TIME_ZONE)

	# Configuration values from the form.
	if ('done_from' in form.cleaned_data):
		done_from = form.cleaned_data['done_from']
		if ('due_from_timestamp' in form.cleaned_data and 
				form.cleaned_data['due_from_timestamp']):
			due_from = timezone_conversion(form.cleaned_data['due_from_timestamp'],
				local_tz).replace(tzinfo=None)
			if ('creation_from_timestamp' in form.cleaned_data and 
					form.cleaned_data['creation_from_timestamp']):
				creation_from = timezone_conversion(form.cleaned_data['creation_from_timestamp'],
									local_tz).replace(tzinfo=None)
				qs = qs.filter(Q(Q(done=done_from), Q(due_date=due_from, creation_date__gte=creation_from)
					| Q(due_date__gt=due_from)) | Q(done__gt=done_from))

			else:
				qs = qs.filter(Q(done=done_from, due_date__gte=due_from) | Q(done__gt=done_from))

	if ('done_to' in form.cleaned_data):
		done_to = form.cleaned_data['done_to']
		if ('due_to_timestamp' in form.cleaned_data and
											form.cleaned_data['due_to_timestamp']):
			due_to = timezone_conversion(form.cleaned_data['due_to_timestamp'],
								local_tz).replace(tzinfo=None)
			if ('creation_to_timestamp' in form.cleaned_data and
												form.cleaned_data['creation_to_timestamp']):
				creation_to = timezone_conversion(form.cleaned_data['creation_to_timestamp'],
									local_tz).replace(tzinfo=None)
				qs = qs.filter(Q(Q(done=done_to), Q(due_date=due_to, creation_date__lte=creation_to)
							| Q(due_date__lt=due_to)) | Q(done__lt=done_to))
			else:
				qs = qs.filter(Q(done=done_to, due_date__lte=due_to) | Q(done__lt=done_to))

	if ('exclude_id' in form.cleaned_data and
										form.cleaned_data['exclude_id']):
		exclude_id = form.cleaned_data['exclude_id']
		qs = qs.exclude(id=exclude_id)

	count = 20
	if ('count' in form.cleaned_data and form.cleaned_data['count']):
		count = form.cleaned_data['count']
	if ('completed' in request.POST):
		qs = qs.filter(done=form.cleaned_data['completed'])

	query_count = qs.count()
	if (query_count > count):
		qs = qs[:count]
		data['limit_hit'] = True
	else:
		data['limit_hit'] = False

	data['query_count'] = qs.count()

	tasks = data['tasks'] = []
	for task in qs:
		tasks.append({
				'id': task.id,
				'due': task.due_date.strftime(TIME_DISPLAY_FORMAT),
				'due_timestamp': convertDatetimeToUTCTimestamp(task.due_date),
				'creation_timestamp': convertDatetimeToUTCTimestamp(task.creation_date),
				'priority': task.priority,
				'description': task.task,
				'done_flag': task.done,
				'note': task.note,
			})
	return HttpResponse(content=json.dumps(response), mimetype='application/json')


@AppAuthentication
def delta_task_list(request):
	if (request.method != 'POST'):
		return err_GE002()
	form = TaskDeltaForm(request.POST)
	if (not form.is_valid()):
		return err_GE031(form)

	response = {
		'data': {},
		'warnings': {},
	}
	data = response['data']

	qs = FollowUps.objects.filter(user=request.user, update_timestamp__gte=form.cleaned_data['timestamp'])
	data['tasks'] = [{
				'id':task.id,
				'due': task.due_date.strftime(TIME_DISPLAY_FORMAT),
				'priority': task.priority,
				'description': task.task,
				'done_flag': task.done,
				'note': task.note,
			} for task in qs]
	data['timestamp'] = time.time()
	return HttpResponse(content=json.dumps(response), mimetype='application/json')


@AppAuthentication
def new_task(request):
	if (request.method != 'POST'):
		return err_GE002()
	form = NewTaskForm(request.POST)
	if (not form.is_valid()):
		return err_GE031(form)

	local_tz = timezone(settings.TIME_ZONE)

	task = FollowUps(
			user=request.user,
			due_date=timezone_conversion(
									form.cleaned_data['due'],
									local_tz,
									).replace(tzinfo=None),
			priority=form.cleaned_data['priority'],
			task=form.cleaned_data['description'],
			note=form.cleaned_data['note'],
		)

	task.save()

	response = {
		'data': {'id': task.id},
		'warnings': {},
	}
	return HttpResponse(content=json.dumps(response), mimetype='application/json')


@AppAuthentication
def update_task(request, task_id):
	if (request.method != 'POST'):
		return err_GE002()
	form = UpdateTaskForm(request.POST)
	if (not form.is_valid()):
		return err_GE031(form)

	try:
		task = FollowUps.objects.get(pk=task_id, user=request.user)
	except FollowUps.DoesNotExist:
		raise Http404

	local_tz = timezone(settings.TIME_ZONE)

	data = form.cleaned_data
	if ('due' in data):
		task.due_date = timezone_conversion(
									data['due'],
									local_tz,
									).replace(tzinfo=None)
	if ('priority' in data):
		task.priority = data['priority']
	if ('description' in data):
		task.task = data['description']
	if ('note' in data):
		task.note = data['note']
	if ('completed' in data):
		if (data['completed']):
			task.completion_date = datetime.now()
		task.done = data['completed']

	task.save()

	response = {
		'data': {},
		'warnings': {},
	}
	return HttpResponse(content=json.dumps(response), mimetype='application/json')


@AppAuthentication
def delete_task(request, task_id):
	try:
		task = FollowUps.objects.get(pk=task_id, user=request.user)
	except FollowUps.DoesNotExist:
		raise Http404
	task.delete()

	response = {
		'data': {},
		'warnings': {},
	}
	return HttpResponse(content=json.dumps(response), mimetype='application/json')

