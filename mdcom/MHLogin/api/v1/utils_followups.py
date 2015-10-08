# -*- coding: utf-8 -*-
'''
Created on 2012-9-17

@author: mwang
'''
from datetime import datetime
from pytz import timezone
import time

from django.http import Http404
from django.conf import settings
from django.db.models import Q

from MHLogin.api.v1.utils import TIME_DISPLAY_FORMAT
from MHLogin.followup.models import FollowUps
from MHLogin.utils.timeFormat import timezone_conversion


def getFollowUpList(condition_dict, user_id):
	qs = FollowUps.objects.filter(user__id=user_id)
	data = {}
	data['total_task_count'] = qs.count()
	data['incomplete_task_count'] = qs.filter(done=False).count()

	# Configuration values from the form.
	if ('done_from' in condition_dict):
		done_from = condition_dict['done_from']
		if ('due_from_timestamp' in condition_dict and 
											condition_dict['due_from_timestamp']):
			due_from = timezone_conversion(condition_dict['due_from_timestamp'],
									timezone(settings.TIME_ZONE)).replace(tzinfo=None)
			if ('creation_from_timestamp' in condition_dict and 
												condition_dict['creation_from_timestamp']):
				creation_from = timezone_conversion(condition_dict['creation_from_timestamp'],
									timezone(settings.TIME_ZONE)).replace(tzinfo=None)
				qs = qs.filter(Q(Q(done=done_from), 
					Q(due_date=due_from, creation_date__gte=creation_from) |
					Q(due_date__gt=due_from)) | Q(done__gt=done_from))

			else:
				qs = qs.filter(Q(done=done_from, due_date__gte=due_from) | Q(done__gt=done_from))

	if ('done_to' in condition_dict):
		done_to = condition_dict['done_to']
		if ('due_to_timestamp' in condition_dict and
											condition_dict['due_to_timestamp']):
			due_to = timezone_conversion(condition_dict['due_to_timestamp'],
									timezone(settings.TIME_ZONE)).replace(tzinfo=None)
			if ('creation_to_timestamp' in condition_dict and
												condition_dict['creation_to_timestamp']):
				creation_to = timezone_conversion(condition_dict['creation_to_timestamp'],
									timezone(settings.TIME_ZONE)).replace(tzinfo=None)
				qs = qs.filter(Q(Q(done=done_to), 
					Q(due_date=due_to, creation_date__lte=creation_to) | 
					Q(due_date__lt=due_to)) | Q(done__lt=done_to))
			else:
				qs = qs.filter(Q(done=done_to, due_date__lte=due_to) | Q(done__lt=done_to))

	if ('exclude_id' in condition_dict and
										condition_dict['exclude_id']):
		exclude_id = condition_dict['exclude_id']
		qs = qs.exclude(id=exclude_id)

	count = 20
	if ('count' in condition_dict and condition_dict['count']):
		count = condition_dict['count']
	if ('completed' in condition_dict):
		#print repr(condition_dict['completed'])
		qs = qs.filter(done=condition_dict['completed'])

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
				'due_timestamp': time.mktime(task.due_date.timetuple()),
				'creation_timestamp': time.mktime(task.creation_date.timetuple()),
				'priority': task.priority,
				'description': task.task,
				'done_flag': task.done,
				'note': task.note,
			})
	return data


def createFollowUp(data_dict, user_id):
	task = FollowUps(
			user_id=user_id,
			due_date=timezone_conversion(
									data_dict['due'],
									timezone(settings.TIME_ZONE),
									).replace(tzinfo=None),
			priority=data_dict['priority'],
			task=data_dict['description'],
			note=data_dict['note'],
		)
	task.save()
	return task


def updateFollowUp(data_dict, task_id, user_id):
	if not task_id or not user_id:
		raise Http404

	try:
		task = FollowUps.objects.get(pk=task_id, user__id=user_id)
	except FollowUps.DoesNotExist:
		raise Http404

	data = data_dict
	if ('due' in data):
		task.due_date = timezone_conversion(
									data['due'],
									timezone(settings.TIME_ZONE),
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


def deleteFollowUp(task_id, user_id):
	if not task_id or not user_id:
		raise Http404

	try:
		task = FollowUps.objects.get(pk=task_id, user__id=user_id)
	except FollowUps.DoesNotExist:
		raise Http404
	task.delete()
