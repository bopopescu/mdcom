# -*- coding: utf-8 -*-

"""
	Modify unittest-xml-reporting 1.3.2, we can specify other TestResult for XMLTestRunner.
		Original module: XMLTestRunnerhttps://github.com/danielfm/unittest-xml-reporting/zipball/1.3.2
"""

"""Custom Django test runner that runs the tests using the
XMLTestRunner class.

This script shows how to use the XMLTestRunner in a Django project. To learn
how to configure a custom TestRunner in a Django project, please read the
Django docs website.
"""

from django.conf import settings
try:
	from django.utils import unittest
except ImportError:
	# only available in Django1.3+ http://docs.djangoproject.com/en/dev/topics/testing/#writing-unit-tests
	import unittest  # we just defeault to the basic unittest 

from django.db.models import get_app, get_apps
from django.test.utils import setup_test_environment, teardown_test_environment
from django.test.simple import build_suite, build_test, DjangoTestSuiteRunner
from MHLogin.utils import xmlrunner


class XMLTestRunner(DjangoTestSuiteRunner):

	def __init__(self, verbosity=1, interactive=True, failfast=True, resultclass=None):
		DjangoTestSuiteRunner.__init__(self, verbosity, interactive, failfast)
		self.resultclass = resultclass

	def run_tests(self, test_labels, verbosity=1, interactive=True, extra_tests=[]):
		"""
		Run the unit tests for all the test labels in the provided list.
		Labels must be of the form:
		 - app.TestClass.test_method
			Run a single specific test method
		 - app.TestClass
			Run all the test methods in a given class
		 - app
			Search for doctests and unittests in the named application.

		When looking for tests, the test runner will look in the models and
		tests modules for the application.

		A list of 'extra' tests may also be provided; these tests
		will be added to the test suite.

		Returns the number of tests that failed.
		"""
		setup_test_environment()

		settings.DEBUG = False

		verbose = getattr(settings, 'TEST_OUTPUT_VERBOSE', False)
		descriptions = getattr(settings, 'TEST_OUTPUT_DESCRIPTIONS', False)
		output = getattr(settings, 'TEST_OUTPUT_DIR', '.')
		exclude_apps = getattr(settings, 'EXCLUDE_APPS', None)

		suite = unittest.TestSuite()

		if test_labels:
			for label in test_labels:
				if '.' in label:
					suite.addTest(build_test(label))
				else:
					app = get_app(label)
					suite.addTest(build_suite(app))
		else:
			for app in get_apps():
				exclude = False
				if exclude_apps:
					for e_app in exclude_apps:
						if app.__name__.startswith(e_app):
							exclude = True
				if not exclude:
					suite.addTest(build_suite(app))

		for test in extra_tests:
			suite.addTest(test)

		old_config = self.setup_databases()

		result = xmlrunner.XMLTestRunner(verbose=verbose, descriptions=descriptions, 
			output=output, resultclass=self.resultclass).run(suite)

		self.teardown_databases(old_config)
		teardown_test_environment()

		return len(result.failures) + len(result.errors)

