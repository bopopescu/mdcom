# -*- coding: utf-8 -*
'''
Created on 2012-9-12

@author: mwang
'''
from MHLogin.api.v1.errlib import err_GE002, err_GE031
from MHLogin.api.v1.forms_followups import NewTaskForm, TaskListForm, UpdateTaskForm
from MHLogin.api.v1.utils import HttpJSONSuccessResponse

from MHLogin.api.v1.utils_followups import getFollowUpList, updateFollowUp, \
	deleteFollowUp, createFollowUp


def listTasksLogic(request):
	if (request.method != 'POST'):
		return err_GE002()
	form = TaskListForm(request.POST)
	if (not form.is_valid()):
		return err_GE031(form)

	data = getFollowUpList(form.cleaned_data, request.mhluser.id)
	return HttpJSONSuccessResponse(data=data)


def newTaskLogic(request):
	if (request.method != 'POST'):
		return err_GE002()
	form = NewTaskForm(request.POST)
	if (not form.is_valid()):
		return err_GE031(form)

	task = createFollowUp(form.cleaned_data, request.mhluser.id)
	data = {'id': task.id}
	return HttpJSONSuccessResponse(data=data)


def updateTaskLogic(request, task_id):
	if (request.method != 'POST'):
		return err_GE002()
	form = UpdateTaskForm(request.POST)
	if (not form.is_valid()):
		return err_GE031(form)

	updateFollowUp(form.cleaned_data, task_id, request.mhluser.id)
	return HttpJSONSuccessResponse()


def deleteTaskLogic(request, task_id):
	deleteFollowUp(task_id, request.mhluser.id)
	return HttpJSONSuccessResponse()

