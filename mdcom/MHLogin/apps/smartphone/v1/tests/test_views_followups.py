import json

from django.http import Http404
from django.test import TestCase

from MHLogin.apps.smartphone.v1.tests.utils import generateHttpRequest
from MHLogin.apps.smartphone.v1.views_followups import list_tasks, new_task, \
	delete_task, update_task
from MHLogin.followup.models import FollowUps


#add by xlin in 130130 to test list_tasks
class ListTasksTest(TestCase):
	def test_list_tasks(self):
		request = generateHttpRequest()

		#get method
		request.method = 'GET'
		result = list_tasks(request)
		self.assertEqual(result.status_code, 400)
		msg = json.loads(result.content)
		self.assertEqual(msg['errno'], 'GE002')

		#post method
		request.method = 'POST'

		request.POST['done_from'] = ''
		request.POST['due_from_timestamp'] = ''
		request.POST['creation_from_timestamp'] = ''
		request.POST['done_to'] = ''
		request.POST['due_to_timestamp'] = ''
		request.POST['creation_to_timestamp'] = ''
		request.POST['count'] = ''
		request.POST['completed'] = ''

		result = list_tasks(request)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		self.assertEqual(msg['data']['query_count'], 0)


#add by xlin in 130130 to test new_task
class NewTaskTest(TestCase):
	def test_new_task(self):
		test = 'test note'
		request = generateHttpRequest()

		#get method
		request.method = 'GET'
		result = new_task(request)
		self.assertEqual(result.status_code, 400)
		msg = json.loads(result.content)
		self.assertEqual(msg['errno'], 'GE002')

		#post method
		request.method = 'POST'

		#invalid form data
		request.POST['due'] = '23swasdf'
		request.POST['priority'] = 2
		request.POST['description'] = 'test'
		request.POST['note'] = test
		result = new_task(request)
		self.assertEqual(result.status_code, 400)
		msg = json.loads(result.content)
		self.assertEqual(msg['errno'], 'GE031')

		#valid form data
		request.POST['due'] = '1358932953'
		request.POST['priority'] = 1
		result = new_task(request)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		fid = FollowUps.objects.get(note=test).id
		self.assertEqual(msg['data']['id'], fid)


#add by xlin in 130130 to test delete_task
class DeleteTaskTest(TestCase):
	def test_delete_task(self):
		task_id = 0
		request = generateHttpRequest()

		#invalid task id
		try:
			delete_task(request, task_id)
		except Http404:
			self.assertRaises(Http404())

		#valid task id
		task = FollowUps(user=request.user, priority=1)
		task.save()
		result = delete_task(request, task.pk)
		self.assertEqual(result.status_code, 200)
		self.assertEqual(FollowUps.objects.count(), 0)


#add by xlin in 130130 to test update_task
class UpdateTaskTest(TestCase):
	def test_update_task(self):
		task_id = 0
		test = 'test'
		request = generateHttpRequest()

		#get method
		request.method = 'GET'
		result = update_task(request, task_id)
		self.assertEqual(result.status_code, 400)
		msg = json.loads(result.content)
		self.assertEqual(msg['errno'], 'GE002')

		#post method
		request.method = 'POST'

		#invalid form data
		request.POST['due'] = 'wsass'
		request.POST['priority'] = 1
		request.POST['description'] = test
		request.POST['note'] = test
		request.POST['completed'] = '1'  # in app/api value is string

		result = update_task(request, task_id)
		self.assertEqual(result.status_code, 400)
		msg = json.loads(result.content)
		self.assertEqual(msg['errno'], 'GE031')

		#valid form data
		request.POST['due'] = '1358932953'

		#404 not find followup
		with self.assertRaises(Http404):
			update_task(request, task_id)

		#valid followup
		task = FollowUps.objects.create(user=request.user, priority=1)
		request.POST['completed'] = '0'  # in app/api value is string  
		result = update_task(request, task.pk)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		task = FollowUps.objects.get(pk=task.pk, user=request.user)
		self.assertEqual(task.done, False)
		self.assertEqual(msg['data'], {})
		note = FollowUps.objects.get(id=task.id).note
		self.assertEqual(note, test)

		request.POST['completed'] = '1'  # in app/api value is string
		result = update_task(request, task.pk)
		task = FollowUps.objects.get(pk=task.pk, user=request.user)
		self.assertEqual(task.done, True)
