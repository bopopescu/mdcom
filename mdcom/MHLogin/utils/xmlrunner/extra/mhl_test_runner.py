# -*- coding: utf-8 -*-
'''
Implement MHLXMLTestResult, MHLXMLTestRunner

Created on 2012-9-5

@author: mwang
'''
from django.conf import settings, global_settings
import sys
from MHLogin.utils.xmlrunner import _XMLTestResult
from MHLogin.utils.xmlrunner.extra.djangotestrunner import XMLTestRunner


class MHLXMLTestResult(_XMLTestResult):
	"""A test result class that can express test results in a XML report.

	Used by XMLTestRunner.
	"""
	def __init__(self, stream=sys.stderr, descriptions=1, verbosity=1, \
		elapsed_times=True):
		"Create a new instance of MHLXMLTestResult."
		_XMLTestResult.__init__(self, stream, descriptions, verbosity, elapsed_times)
		self.django_login_url = global_settings.LOGIN_URL
		self.django_middlewares = global_settings.MIDDLEWARE_CLASSES
		self.django_caches = global_settings.CACHES
		# when running our unittests use our middlewares +django's and our login_url
		self.mhlogin_login_url = settings.LOGIN_URL
		self.mhlogin_middlewares = settings.MIDDLEWARE_CLASSES
		self.mhlogin_caches = settings.CACHES

	def startTest(self, test):
		"Called before execute each test method."
		if test.__module__.startswith('MHLogin'): 
			settings.LOGIN_URL = self.mhlogin_login_url
			settings.MIDDLEWARE_CLASSES = self.mhlogin_middlewares
			settings.CACHES = self.mhlogin_caches
		else:
			settings.LOGIN_URL = self.django_login_url
			settings.MIDDLEWARE_CLASSES = self.django_middlewares
			settings.CACHES = self.django_caches
		_XMLTestResult.startTest(self, test)

	def stopTest(self, test):
		"Called after execute each test method."
		_XMLTestResult.stopTest(self, test)
		settings.LOGIN_URL = self.mhlogin_login_url
		settings.MIDDLEWARE_CLASSES = self.mhlogin_middlewares
		settings.CACHES = self.mhlogin_caches


class MHLXMLTestRunner(XMLTestRunner):
	def __init__(self, *args, **kwargs):
		verbosity = kwargs.get('verbosity', 1)
		interactive = kwargs.get('interactive', True)
		failfast = kwargs.get('failfast', True)
		resultclass = kwargs.get('resultclass', MHLXMLTestResult)
		XMLTestRunner.__init__(self, verbosity, interactive, failfast, resultclass)

