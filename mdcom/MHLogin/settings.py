import os.path
from os.path import dirname, join

# Django settings for MHLogin project.
#
# To alter any value for your particular configuration, merely create a file
# in the root project directory named '.django-local-settings.py'. That file
# should be something of a miniature version of this file. The values defined
# will over-ride the ones defined here.
#
# Note that the .django-local-settings.py file is MANDATORY. Even if it's
# empty.
#
# Realistically, the file should (at a minimum) contain the following values:
#
# DATABASE_PASSWORD
# SECRET_KEY
#
# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ['*']  # override in local settings  

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'America/Los_Angeles'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = False

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = ''

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
	# Put strings here, like "/home/html/static" or "C:/www/django/static".
	join(dirname(__file__), 'static').replace('\\', '/'),
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
	'django.contrib.staticfiles.finders.FileSystemFinder',
	'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#	'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# The URL to which the @login_required() decorator should redirect users
# who aren't logged in yet. Also, the URL to which the login-requiring
# middleware should redirect users.
LOGIN_URL = '/'

TWILIO_RESPONSE_MIMETYPE = 'application/xml'
# Twilio Values
TWILIO_API_2008 = '2008-08-01'
# current twilio version; we still keep 2008 API for backward compatibility
TWILIO_API_VERSION = '2010-04-01'
# Twilio rollout: phase 1 = old and new api combo
# phase 2: all new number provisioned go to 2010 api
# phase 3: everything will be redirected to 2010 (TBD)
TWILIO_PHASE = 2
# http://en.wikipedia.org/wiki/Country_calling_code
COUNTRY_CODE = '+1'
PROJECT_ROOT = os.path.dirname(os.path.realpath(__file__))
FIXTURE_DIRS = (os.path.join(PROJECT_ROOT, 'fixtures'),)

TEMPLATE_CONTEXT_PROCESSORS = (
	"django.contrib.auth.context_processors.auth",
	"django.core.context_processors.debug",
	"django.core.context_processors.i18n",
	"django.core.context_processors.media",
	"django.core.context_processors.static",
	"django.core.context_processors.request",
	"django.contrib.messages.context_processors.messages",
	"MHLogin.utils.templates.processor",
)

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
	'django.template.loaders.filesystem.Loader',
	'django.template.loaders.app_directories.Loader',
#	 'django.template.loaders.eggs.Loader',
)

AUTHENTICATION_BACKENDS = (
	'django.contrib.auth.backends.ModelBackend',
	'MHLogin.DoctorCom.IVR.utils._IVR_AuthBackend',
)

MIDDLEWARE_CLASSES = (
	'django.middleware.common.CommonMiddleware',
	'django.contrib.sessions.middleware.SessionMiddleware',
#	'django.middleware.locale.LocaleMiddleware',
	'MHLogin.utils.middlewares.MHL_LanguageSetup_Middleware',
	'django.contrib.auth.middleware.AuthenticationMiddleware',
	'django.contrib.messages.middleware.MessageMiddleware',

	# Django-logging Middleware
	#'djangologging.middleware.LoggingMiddleware',
	#'djangologging.middleware.SuppressLoggingOnAjaxRequestsMiddleware',
	#'debug_toolbar.middleware.DebugToolbarMiddleware',

	# Tie database transactions to HTTP requests. If the view function returns
	# an exception, Django rolls-back any pending transactions. If the view
	# function returns normally, Django commits any pending transactions.
	# Note that this *only* works for engines that support transactions (e.g.,
	# InnoDB).
	'django.middleware.transaction.TransactionMiddleware',

	# MHLogin custom middlewares:
	'MHLogin.utils.middlewares.MHL_SessionSetup_Middleware',
	'MHLogin.utils.middlewares.MHL_StatusCheck_Middleware',
	'MHLogin.utils.middlewares.MHL_ACL_Middleware',
	'MHLogin.utils.middlewares.MHL_SSCheck_Middleware',
	'MHLogin.utils.middlewares.MHL_ForcePasswordChange_Middleware',
	# Standard Pagination Middleware
	'pagination.middleware.PaginationMiddleware',
	'MHLogin.utils.middlewares.GlobalConstantSetup_Middleware',
	'MHLogin.utils.middlewares.NoCacheMiddleware',
)

# Django >= 1.4 use only SHA1 hasher during integration
PASSWORD_HASHERS = (
#	'django.contrib.auth.hashers.PBKDF2PasswordHasher',
#	'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
#	'django.contrib.auth.hashers.BCryptPasswordHasher',
	'django.contrib.auth.hashers.SHA1PasswordHasher',
#	'django.contrib.auth.hashers.MD5PasswordHasher',
#	'django.contrib.auth.hashers.CryptPasswordHasher',
)

# URLs for which login should be required. This is a regex.
LOGIN_REQUIRED_URLS = (
	r'.*',
)
# URLs which are caught in LOGIN_REQUIRED_URLS that shouldn't need users to log in.
LOGIN_REQUIRED_URLS_EXCEPTIONS = (
	r'^/$',
	r'^/login',
	r'^/logout',
	r'^/Twilio',
	r'^/signup',
	r'^/IVR/',
	r'^/speech/',
	r'^/app',
	r'^/CheckUserName',
	r'^/Active',
	r'^/sucessActive',
	r'^/getDoctorNumber',
	r'^/getDoctorNumberSucess',
	r'^/privacy',
	r'^/api',
	r'^/DicomCalling',
	r'^/searchSites',
	r'^/searchStates',
	r'^/ValidateEmailAndPhone',
	r'^/ForgotPassword',
)

# URL exceptions for forced password changes.
FORCE_PW_CHANGE_URL_EXCEPTIONS = (
	r'^/login',
	r'^/logout',
	r'^/Twilio',
	r'^/IVR/',
	r'^/app',
	r'^/api',
	r'^/DicomCalling',
)

TOS_REQUIRED_URLS_EXCEPTIONS = (
	r'^/login',
	r'^/logout',
	r'^/admin',
	r'^/terms',
	r'^/eula',
	r'^/privacy',
	r'^/learn_more',
	r'^/Twilio',
	r'^/signup',
	r'^/tests/TwilioResponse/',
	r'/IVR/',
	r'/ProvisionNumber/',
	r'/Validations',
	r'^/TermsAgreement',
	r'^/Profile/ChangePassword/',
	r'^/toggle_mobile',
	r'^/app',
	r'^/CheckUserName',
	r'^/api',
	r'^/DicomCalling',
	r'^/ValidateEmailAndPhone',
)

# ACL_DEFAULT_BEHAVIOR defines what the access controller does with requests
# that don't match any explicit rule. Valid values are either 'ACCEPT' or
# 'DENY'.
ACL_DEFAULT_BEHAVIOR = 'DENY'
ACL_RULES = (
		# This tuple defines the ruleset for the ACL. Note that the ACL will
		# *always* act on the first rule match.
		#
		# Rules are in the format:
		# ('URL_path_regex', ('ACCEPT'|'DENY'), 'User_type1', 'User_type2', ...)
		# 	or:
		# ('URL_path_regex', ruletuple_1, ruletuple_2, ...)
		#		where ruletuple_# is defined as:
		#		(('ACCEPT'|'DENY'), 'User_type1', 'User_type2', ...)
		# Special Inputs:
		#	User Type:
		#		   * - Match any
		#		None - Match unauthenticated users (pass the Python None value, *NOT* the string 'None')
		#
		# Note that user type *MUST* be a type defined in MHLUsers/models.

		# Common access
		('^/$', 'ACCEPT', '*'),
		('^/login', 'ACCEPT', '*'),
		('^/logout', 'ACCEPT', '*'),
		('^/terms', 'ACCEPT', '*'),
		('^/eula', 'ACCEPT', '*'),
		('^/TermsAgreement', 'ACCEPT', '*'),
		('^/privacy', 'ACCEPT', '*'),
		('^/learn_more', 'ACCEPT', '*'),
		('^/user_agent', 'ACCEPT', '*'),
		('^/toggle_mobile', 'ACCEPT', '*'),
		('^/Profile', 'ACCEPT', '*'),
		('^/Org', 'ACCEPT', '*'),
		('^/searchSites', 'ACCEPT', '*'),
		('^/searchStates', 'ACCEPT', '*'),

		('^/CheckUserName', 'ACCEPT', '*'),
		('^/Active', 'ACCEPT', '*'),
		('^/sucessActive', 'ACCEPT', '*'),
		('^/getDoctorNumber', 'ACCEPT', '*'),
		('^/getDoctorNumberSucess', 'ACCEPT', '*'),
		('^/changeCurrentPractice', 'ACCEPT', '*'),
		('^/signup',
					('ACCEPT', None, '*'),
				),

		# Sales
		('^/Sales/',
					('ACCEPT', 'Salesperson', 'Administrator'),
					('DENY', '*'),
				),

		# DoctorCom
		('^/Messages/',
					('ACCEPT', 'Provider', 'OfficeStaff', 'Administrator', 'Broker'),
					#('DENY', '*'),
				),
		('^/Call/',
					('ACCEPT', 'Provider', 'OfficeStaff', 'Administrator', 'Broker'),
				),
		('^/Page/',
					('ACCEPT', 'Provider', 'Office_Manager', 'Administrator', 'Broker'),
				),

		# Follow-Ups
		('^/FollowUps/',
					('ACCEPT', 'OfficeStaff', 'Provider', 'Broker'),
				),

		# Administration
		('^/dcAdmin/', 'DENY', 'can_view_dcadmin'),

		('^/admin',
					('ACCEPT', 'Administrator'),
					('DENY', '*'),
				),
		('^/analytics',
					('ACCEPT', 'Administrator'),
					('DENY', '*'),
				),

		('^/tests',
					('ACCEPT', 'Administrator'),
					('DENY', '*'),
				),
		('^/SitesAdmin',
					('ACCEPT', 'Administrator'),
					('DENY', '*'),
				),

		# Twilio
		('^/Twilio',
					('ACCEPT', None),
					('DENY', '*'),
				),
		('^/IVR',
					('ACCEPT', '*'),
				),
		('^/speech',
					('ACCEPT', '*'),
				),


		# End-User/Customer Access: Reject staff types
		('^Sites/$',
					('DENY', 'Salesperson'),
				),
		('^/Provider_View/',
					('ACCEPT', '*'),
				),
		('^/User_View/',
					('ACCEPT', '*'),
				),

		# Search functions
		('^/Search/User/',
					('ACCEPT', '*'),
				),

		# get specialty options
		('^/Specialty/Get/',
					('ACCEPT', '*'),
				),

		#urls for office managers
		('^/Practice',
				('ACCEPT', 'OfficeStaff'),
			),
		('^/Provider_Info',
				('ACCEPT', 'OfficeStaff', 'Provider', 'Broker'),
			),
		('^/CallGroup',
				('DENY', None),
				('ACCEPT', '*'),
			),
		('^/Messages',
				('DENY', None),
				('ACCEPT', '*'),
			),
		('^/Support',
				('ACCEPT', '*'),
			),
		('^/Invitations',
				('ACCEPT', 'Salesperson'),
				('ACCEPT', 'Office_Manager')
			),
		('^/Validations',
				('ACCEPT', '*')
			),

		# App interface
		('^/app',
				('ACCEPT', None),
				('DENY', '*'),
			),

		# API interface
		('^/api',
				('ACCEPT', None),
				('DENY', '*'),
			),

		('^/billing/billing_menu/',
				('ACCEPT', 'Administrator'),
				('DENY', '*'),
		),
		('^/billing/', 
			('ACCEPT', 'Office_Manager')
		),

		# Default accept for providers since their URLConfs are all over the place
		('.*', 'ACCEPT', 'Provider'),

		('^/ProvisionNumber/',
				('ACCEPT', 'Broker'),
				('ACCEPT', 'Provider'),
			),
		('^/DicomCalling', 'ACCEPT', '*'),
		('^/EmailExist/', 'ACCEPT', '*'),
		('^/Organization/', 'ACCEPT', '*'),
		('^/ValidateEmailAndPhone',
			('ACCEPT', None, '*'),
		),
		('^/MyFavorite/', 'ACCEPT', '*'),
		('^/ForgotPassword', 'ACCEPT', '*'),
	)

ROOT_URLCONF = 'MHLogin.urls'

INSTALLED_APPS = (
	'django.contrib.auth',
	'django.contrib.contenttypes',
	'django.contrib.sessions',
	'django.contrib.sites',
	'django.contrib.admin',
	'django.contrib.staticfiles',
	'MHLogin.Administration',
	'MHLogin.Administration.tech_admin',
	'MHLogin.DoctorCom',
	'MHLogin.DoctorCom.IVR',
	'MHLogin.DoctorCom.Messaging',
	'MHLogin.DoctorCom.NumberProvisioner',
	'MHLogin.DoctorCom.speech',
	'MHLogin.KMS',
	'MHLogin.Logs',
	'MHLogin.MHLPractices',
	'MHLogin.MHLogin_Main',
	'MHLogin.MHLSites',
	'MHLogin.MHLUsers',
	'MHLogin.MHLUsers.Sales',
	'MHLogin.MHLUsers.forgotpassword',
	'MHLogin.Invites',
	'MHLogin.tests',
	'MHLogin.apps',
	'MHLogin.apps.smartphone',
	'MHLogin.DoctorCom.SMS',
	'pagination',
	'MHLogin.followup',
	'MHLogin.analytics',
	'MHLogin.MHLCallGroups',
	'MHLogin.MHLCallGroups.Scheduler',
	'MHLogin.utils',
	'kronos',
	'MHLogin.Validates',
	'MHLogin.Administration',
	'django_common',
	'django_braintree',
	'MHLogin.genbilling',
	'MHLogin.api',
	'MHLogin.MHLOrganization',
	'MHLogin.MHLFavorite',
	#'djangologging',
	#'ajax_filtered_fields',
)

INQUIRY_RECIPIENTS = ['inquiry@mdcom.com', ]
SUPPORT_RECIPIENTS = ['support@mdcom.com', ]

RECAPTCHA_PUBLIC_KEY = '6Ldk57kSAAAAANSfwW_cvX7EeOELACRz69jK2ioa'
RECAPTCHA_PRIVATE_KEY = '6Ldk57kSAAAAALURH5GSKDVrLX79uZxzixhQq7uu'

#billing stuff
AESKEY = 'gy28NHcfQW7bFdop2VZhJAQmniuS42jF'
PP_USER_NAME = 'LD1O5RCDR0'
PP_PASS = 'HASEL62JLGHR8WHC'
PP_VENDOR = 'LD1O5RCDR0'
PP_PARTNER = 'PayPal'

# This is the default range to do search for hospitals near you during 
# signup process. The units are in miles. and should be treated as +/-.
PROXIMITY_RANGE = 50.0

# The path of temporary directory, if ATTACHMENTS_TEMP_ROOT is blank, it 
# will use the system temporary directory.
ATTACHMENTS_TEMP_ROOT = ''
# Timeout of temporary directory for cleaning, unit: s
ATTACHMENTS_TEMP_TIMEOUT = 24 * 60 * 60
# The uploaded file's max size unit: MB
MAX_UPLOAD_SIZE = 10

#auto refresh time length 5 minutes
MSGLIST_AUTOREFRESH_TIME = 5 * 60 * 1000

# Caches configuration, it's used to store the upload progress information.
# This configuration is very important to Linux system
# If your django's version is 1.3, you must config the cache like below, 
# and make sure the directory exists and is readable and writable by the user apache.
CACHES = {
	'default': {
		'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
		'LOCATION': '/var/tmp/django_cache',
		'TIMEOUT': 60 * 60,
		'OPTIONS': {
			'MAX_ENTRIES': 10000
		}
	}
}
# If your django's version is 1.2, you must config the cache like below, 
# and make sure the directory exists and is readable and writable by the user apache.
CACHE_BACKEND = 'file:///var/tmp/django_cache'

# Set schedule event undo/redo stack's depth, default 20. 
SCHEDULE_EVENT_UNDO_DEPTH = 20

# Forced language setting, if you configure this value, the system will display 
# messages/page by using this language. 
#   Default: en-us
# If you configure this value, you must provide files:
#   1.JS language package file "l10n_[FORCED_LANGUAGE_CODE].js" in the directory MHLogin/media/js/localization
FORCED_LANGUAGE_CODE = 'en-us'

# Configure the call feature whether it's enable, default: True.
CALL_ENABLE = True

#check user name exist in other servers
CHECKUSERNAME_URL = []

# Maximum times of sending code per day.
SEND_MAXIMUM_PER_DAY = 5
# Waiting time after last sending code, unit: minute
SEND_CODE_WAITING_TIME = 3
# Maximum times per hour of failure verify
FAIL_VALIDATE_MAXIMUM_PER_HOUR = 3
# The validate action will be locked if times of fail validate in one hour exceed FAIL_VALIDATE_MAXIMUM_PER_HOUR.
# It's the lock time below, unit: hour.
VALIDATE_LOCK_TIME = 1

# Set debug provider flag to false by default
DEBUG_PROVIDER = False

# Configurations for android push notification.
GCM_API_KEY = ''
GCM_PROJECT_ID = ''

# Dicom server configuration
# dicom server -- full path
DICOM_SERVER_URL = "https://dicom.mdcom.com/dicom/Dim2jpg"
# dicom REVOKE_PATH -- full path
DICOM_REVOKE_URL = ''

# organization tree menu max nodes
MAX_ORG_TREE_NODES = 4000

try:
	from django_local_settings import *
except ImportError, err:
	# need to copy django_local_settings-sample.py to django_local_settings.py then modify.
	raise Exception("%s:\nPlease copy django_local_settings-sample.py to "
		"django_local_settings.py and modify according to your needs.\n\n" % (str(err)))

# Changes to the settings values, should the user run in debug mode. Note that this MUST
# come after the django_local_settings.py import so that we can know the correct status of DEBUG.
if DEBUG:
	LOGIN_REQUIRED_URLS_EXCEPTIONS += (r'^/static', r'^/media')
	TOS_REQUIRED_URLS_EXCEPTIONS += (r'^/static', r'^/media')
	ACL_RULES = (('^/static', 'ACCEPT', '*'),) + ACL_RULES
	ACL_RULES = (('^/media', 'ACCEPT', '*'),) + ACL_RULES


#from cloudfiles.connection import Connection
#<insert In Flames reference here>
#if (not 'CLOUDFILE_TIMEOUT' in locals()):
#	CLOUDFILE_TIMEOUT = 5
#CLOUDCONNECTION = Connection(CLOUDFILE_USERNAME, CLOUDFILE_APIKEY, #timeout=CLOUDFILE_TIMEOUT)
