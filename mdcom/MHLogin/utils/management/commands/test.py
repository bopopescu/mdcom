
from optparse import make_option
from django.core.management.commands import test
from django.conf import settings


class Command(test.Command):
	""" Our custom test command which inherits django test command.  First 
	version includes option to turn on code coverage generation statistics
	"""
	test.Command.option_list += (
		make_option('--no-coverage', action='store_true', dest='nocoverage', default=False,
				help='Turn off code coverage, primarily for debugging.'),
		make_option('--output', default='html_coverage', dest='output',
				help='Code coverage output directory, default: html_coverage/'),
		make_option('--xmlrunner', action='store_true', dest='usexmlrunner', default=False,
				help='XML test runner, --no-coverage option ignored in this case.'))

	nocoverage = False
	coverageOutput = ""

	def __init__(self):
		super(Command, self).__init__()
		# our default test runner, may be overridden with options
		settings.TEST_RUNNER = 'MHLogin.utils.test_runner.TestRunner'

	# override handle to start coverage start and stop
	def handle(self, *test_labels, **options):
		""" 
		Override default handle and check if we have custom MHLogin options 
		"""
		Command.nocoverage = options.pop('nocoverage', False)
		Command.coverageOutput = options.pop('output', "")
		Command.usexmlrunner = options.pop('usexmlrunner', False)

		if (Command.usexmlrunner):
			self._setup_xml_runner()		
		super(Command, self).handle(*test_labels, **options)

	# setup xml runner here if using
	def _setup_xml_runner(self):
		settings.TEST_RUNNER = 'MHLogin.utils.xmlrunner.extra.mhl_test_runner.MHLXMLTestRunner'
		settings.TEST_OUTPUT_VERBOSE = True
		settings.TEST_OUTPUT_DESCRIPTIONS = True
		settings.TEST_OUTPUT_DIR = 'xmlrunner'
		settings.EXCLUDE_APPS = ()

