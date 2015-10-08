'''
Created on 2013-6-17

@author: pyang
'''
from MHLogin.api.v1.tests.utils import APITest
from MHLogin.api.v1.utils_followups import deleteFollowUp, updateFollowUp
from MHLogin.followup.models import FollowUps
from django.http import Http404
class DeleteFollowUpTest(APITest):
	def testDeleteFollowUp(self):
		with self.assertRaises(Http404):deleteFollowUp(1,self.user.id)
		task = FollowUps(user=self.user, priority=1)
		task.save()
		deleteFollowUp(task.id,self.user.id)
		with self.assertRaises(FollowUps.DoesNotExist):FollowUps.objects.get(pk=task.id)
		with self.assertRaises(ValueError):deleteFollowUp('ab','cd')
		
class UpdateFollowUpTest(APITest):
	def testUpdateFollowUp(self):
		task = FollowUps(user=self.user, priority=1)
		task.save()
		self.assertFalse(task.done)
		data = {'priority':10,'description':'this is followUps','completed':True}
		updateFollowUp(data, task.id, self.user.id)
		try:
			task = FollowUps.objects.get(pk=task.id)
			task.save()
		except:
			FollowUps.DoesNotExist
		self.assertTrue(task.done)
		