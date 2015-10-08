# -*- coding: utf-8 -*
'''
Created on 2012-9-12

@author: mwang
'''
from MHLogin.api.v1.business_followups import listTasksLogic, newTaskLogic, \
	updateTaskLogic, deleteTaskLogic
from MHLogin.api.v1.decorators import APIAuthentication


@APIAuthentication
def listTasks(request):
	return listTasksLogic(request)


@APIAuthentication
def newTask(request):
	return newTaskLogic(request)


@APIAuthentication
def updateTask(request, task_id):
	return updateTaskLogic(request, task_id)


@APIAuthentication
def deleteTask(request, task_id):
	return deleteTaskLogic(request, task_id)

