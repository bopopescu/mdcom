
import logging
from django.test import TestCase
from django.conf import settings
from utils import twilio_get_available_number, twilio_account_active
from MHLogin.utils.decorators import skipIfUrlFails

@skipIfUrlFails("http://www.twilio.com", "Skipping twilio requests")
class NumberProvisioningTest(TestCase):

	def setUp(self):
		pass

	def tearDown(self):
		pass

	def testNumberProvisioning(self):
#		import pdb; pdb.set_trace()
#		anumber = twilio_old_get_available_number('510')
		logger = logging.getLogger()  # get the Root logger
		self.assertTrue(logger.handlers == [], logger.handlers)
		# for staging setup?
		if not settings.TWILIO_ACCOUNT_SID or settings.TWILIO_ACCOUNT_SID != 'abcdefg':
			if twilio_account_active():
				bnumber = twilio_get_available_number('510')
				self.assertEqual(bnumber.phone_number[0:5], '+1510')
		# TODO: FIXME: Twilio rest client adds stream handler to root logger, where, when, 
		# why, how, yadda, yadda is unknown.  TODO: possibly related, we should use logging's 
		# basicConfig(**kwargs) to setup our logging system instead of what we do now
		# in utils/mh_logging.py
		if logger.handlers:
			logger.removeHandler(logger.handlers[0]) 

