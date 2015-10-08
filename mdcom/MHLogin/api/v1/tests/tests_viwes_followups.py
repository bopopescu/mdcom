'''
Created on 2013-5-14

@author: pyang
'''
from MHLogin.api.v1.tests.utils import APITest
from django.core.urlresolvers import reverse
from MHLogin.api.v1.errlib import err_GE002
import json
from MHLogin.followup.models import FollowUps


class FollowUpsTest(APITest):
	def testListTasks(self):
		response = self.client.post(reverse(
			'MHLogin.api.v1.views_followups.listTasks'), **self.extra)
		self.assertEqual(response.status_code, 200, response.status_code)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 2)
		
		response = self.client.get(reverse(
			'MHLogin.api.v1.views_followups.listTasks'), **self.extra)
		self.assertEqual(response.content, err_GE002().content, response.status_code)

	def testNewTask(self):
		data={'description':'the test is test newTask',
			'due':'20',
			'priority':'1'}
		response = self.client.post(reverse(
			'MHLogin.api.v1.views_followups.newTask'), data, **self.extra)
		self.assertEqual(response.status_code, 200, response.status_code)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 2)
		
		response = self.client.get(reverse(
			'MHLogin.api.v1.views_followups.newTask'), **self.extra)
		self.assertEqual(response.content, err_GE002().content, response.status_code)
		
	def testUpdateTask(self):
		task = FollowUps(user=self.user, priority=1)
		task.save()
		response = self.client.get(reverse(
			'MHLogin.api.v1.views_followups.updateTask',args=(task.id,)), **self.extra)
		self.assertEqual(response.content, err_GE002().content, response.status_code)

		response = self.client.post(reverse(
			'MHLogin.api.v1.views_followups.updateTask',args=(task.id,)), **self.extra)
		self.assertEqual(response.status_code, 200, response.status_code)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 2)
	
	def testDeleteTask(self):
		task = FollowUps(user=self.user, priority=1)
		task.save()
		response = self.client.post(reverse(
			'MHLogin.api.v1.views_followups.deleteTask',args=(task.id,)), **self.extra)
		self.assertEqual(response.status_code, 200, response.status_code)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 2)
	
	