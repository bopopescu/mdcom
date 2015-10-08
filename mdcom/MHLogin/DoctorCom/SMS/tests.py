"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
"""

import time

from django.conf import settings
from django.test import TestCase

from MHLogin.MHLUsers.models import MHLUser

from views import alternativeCallerID

class alternativeCallerIDTest(TestCase):

	def setUp(self):
		# Create users to test against
		for i in range(10):
			mhl = MHLUser()
			mhl.lat = 0
			mhl.longit = 0
			mhl.username=str(i)
			mhl.save()
	
	successful = """
	def test_1_calledID(self):
		called = MHLUser.objects.get(pk=2)
		
		caller = []
		caller.append(MHLUser.objects.get(pk=3))
		caller.append(MHLUser.objects.get(pk=4))
		caller.append(MHLUser.objects.get(pk=5))
		caller.append(MHLUser.objects.get(pk=6))
		
		# Called user and called ID mapping for the user.
		# Format for the caller object is [MHLUser, calledID]
		caller_mappings = []
		
		settings.TWILIO_SMS_NUMBER_POOL = ['1231231234',]
		
		for usr in caller:
			# Test forward lookup
			self.assertEqual('1231231234', alternativeCallerID(called, usr))
			# Test to ensure lookup is maintained
			self.assertEqual('1231231234', alternativeCallerID(called, usr))
	"""
	
	def test_2_calledIDs(self):
		called = MHLUser.objects.get(username=str(2))
		
		caller = []
		caller.append(MHLUser.objects.get(username=str(3)))
		caller.append(MHLUser.objects.get(username=str(4)))
		caller.append(MHLUser.objects.get(username=str(5)))
		caller.append(MHLUser.objects.get(username=str(6)))
		
		# Called user and called ID mapping for the user.
		# Format for the caller object is [MHLUser, calledID]
		caller_mappings = []
		
		settings.TWILIO_SMS_NUMBER_POOL = ['1231231234', '9879879876']
		
		# Test forward lookup
		self.assertEqual('1231231234', alternativeCallerID(caller[0], called))
		# Test to ensure lookup is maintained
		self.assertEqual('1231231234', alternativeCallerID(caller[0], called))
		
		# Test forward lookup
		self.assertEqual('9879879876', alternativeCallerID(caller[1], called))
		# Test to ensure lookup is maintained
		self.assertEqual('9879879876', alternativeCallerID(caller[1], called))
		
		# Test forward lookup
		self.assertEqual('1231231234', alternativeCallerID(caller[2], called))
		# Test to ensure lookup is maintained
		self.assertEqual('1231231234', alternativeCallerID(caller[2], called))
		
		# Test forward lookup
		self.assertEqual('9879879876', alternativeCallerID(caller[3], called))
		# Test to ensure lookup is maintained
		self.assertEqual('9879879876', alternativeCallerID(caller[3], called))
				
	def test_4_callerIDs(self):
		called = MHLUser.objects.get(username=str(2))
		
		caller = []
		caller.append(MHLUser.objects.get(username=str(3)))
		caller.append(MHLUser.objects.get(username=str(4)))
		caller.append(MHLUser.objects.get(username=str(5)))
		caller.append(MHLUser.objects.get(username=str(6)))
		caller.append(MHLUser.objects.get(username=str(7)))
		caller.append(MHLUser.objects.get(username=str(8)))
		caller.append(MHLUser.objects.get(username=str(9)))
		
		# Called user and caller ID mapping for the user.
		# Format for the called object is [MHLUser, callerID]
		called_mappings = []
		
		settings.TWILIO_SMS_NUMBER_POOL = ['1231231234', '9879879876', '5555555555', '1010101010']
		
		# Test forward lookup
		self.assertEqual('1231231234', alternativeCallerID(caller[0], called))
		# Test to ensure lookup is maintained
		self.assertEqual('1231231234', alternativeCallerID(caller[0], called))
		
		# Test forward lookup
		self.assertEqual('9879879876', alternativeCallerID(caller[1], called))
		# Test to ensure lookup is maintained
		self.assertEqual('9879879876', alternativeCallerID(caller[1], called))
		
		# Test forward lookup
		self.assertEqual('5555555555', alternativeCallerID(caller[2], called))
		# Test to ensure lookup is maintained
		self.assertEqual('5555555555', alternativeCallerID(caller[2], called))
		
		# Test forward lookup
		self.assertEqual('1010101010', alternativeCallerID(caller[3], called))
		# Test to ensure lookup is maintained
		self.assertEqual('1010101010', alternativeCallerID(caller[3], called))
		
		# Test forward lookup
		self.assertEqual('1231231234', alternativeCallerID(caller[4], called))
		# Test to ensure lookup is maintained
		self.assertEqual('1231231234', alternativeCallerID(caller[4], called))
		
		# Test forward lookup
		self.assertEqual('9879879876', alternativeCallerID(caller[5], called))
		# Test to ensure lookup is maintained
		self.assertEqual('9879879876', alternativeCallerID(caller[5], called))
		
		# Test forward lookup
		self.assertEqual('5555555555', alternativeCallerID(caller[0], called))
		# Test to ensure lookup is maintained
		self.assertEqual('5555555555', alternativeCallerID(caller[0], called))






