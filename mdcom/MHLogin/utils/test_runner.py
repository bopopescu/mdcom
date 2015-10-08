
import sys
from coverage import coverage

from django.conf import settings, global_settings
from django.test.simple import DjangoTestSuiteRunner
from django.utils.unittest import TextTestRunner
from django.utils.unittest.runner import TextTestResult

from MHLogin.utils.management.commands import test


# custom test result so we can control middleware behavior during tests
class MHLResult(TextTestResult):
	""" We use this class to hook into every start and stop of every unittest """

	def __init__(self, stream, descriptions, verbosity):
		# when running django unittests use their middlewares and login_url
		self.django_login_url = global_settings.LOGIN_URL
		self.django_middlewares = global_settings.MIDDLEWARE_CLASSES
		self.django_caches = global_settings.CACHES
		# when running our unittests use our middlewares +django's and our login_url
		self.mhlogin_login_url = settings.LOGIN_URL
		self.mhlogin_middlewares = settings.MIDDLEWARE_CLASSES
		self.mhlogin_caches = settings.CACHES
		super(MHLResult, self).__init__(stream, descriptions, verbosity)

	def startTest(self, test):
		""" For non MHLogin modules test with only django middlewares otherwise all.
		For django tests use LOGIN_URL as '/accounts/login/' as they expect to see
		location/next values for next view after successful login, we don't support yet.
		"""
		if test.__module__.startswith('MHLogin'): 
			settings.LOGIN_URL = self.mhlogin_login_url
			settings.MIDDLEWARE_CLASSES = self.mhlogin_middlewares
			settings.CACHES = self.mhlogin_caches
		else:
			settings.LOGIN_URL = self.django_login_url
			settings.MIDDLEWARE_CLASSES = self.django_middlewares
			settings.CACHES = self.django_caches
		super(MHLResult, self).startTest(test)

	def stopTest(self, test):
		""" Set middlewares back running environment """
		# set middlewares and login back to default
		settings.LOGIN_URL = self.mhlogin_login_url
		settings.MIDDLEWARE_CLASSES = self.mhlogin_middlewares
		settings.CACHES = self.mhlogin_caches
		super(MHLResult, self).stopTest(test)


# custom test runner
class TestRunner(DjangoTestSuiteRunner):
	""" Test runner for MHLogin - for modifying default unittest behavior very early
	and at end of unittests
	"""
	def run_tests(self, test_labels, extra_tests=None, **kwargs):
		""" Hook in from parent class, we need to save test_labels if we use coverage """
		self.test_labels = test_labels  # save test_labels later for coverage option
		return super(TestRunner, self).run_tests(test_labels, extra_tests, **kwargs)

	def run_suite(self, suite, **kwargs):
		""" Hook in from parent class so we can use our own result class """
		ttr = TextTestRunner(verbosity=self.verbosity, failfast=self.failfast, resultclass=MHLResult)
		return ttr.run(suite)

	def setup_test_environment(self, **kwargs):
		""" Hook in from parent class, we want to start coverage if enabled """
		super(TestRunner, self).setup_test_environment(**kwargs)
		if (test.Command.nocoverage == False):
			include_list = self._build_include_list(self.test_labels)
			sys.stderr.write("Starting code coverage....\n\n")
			self.cov = coverage(branch=True, include=include_list)
			self.cov.start()

	def teardown_test_environment(self, **kwargs):
		""" Hook in from parent class, we want to stop coverage if enabled """
		if (test.Command.nocoverage == False):
			sys.stderr.write("\nWriting code coverage output to directory %s...\n\n" %
							test.Command.coverageOutput)
			self.cov.stop()
			self.cov.html_report(directory=test.Command.coverageOutput)
		super(TestRunner, self).teardown_test_environment(**kwargs)

	def _build_include_list(self, test_labels):
		""" From list of app_labels return a list of absolute pathnames to their location

		:returns: list of absolute path names 
		""" 
		if test_labels:
			ilist = []
			for l in test_labels:
				if '.' in l:  # grab the app label, ignore class and/or test
					l = l.split('.')[0] 
				for app in settings.INSTALLED_APPS:
					if l == app.split('.')[-1]:
						ilist.append(sys.modules[app].__path__[0] + '/*')
		else:  # empty means running all unittests - no app args
			ilist = None

		return ilist	

