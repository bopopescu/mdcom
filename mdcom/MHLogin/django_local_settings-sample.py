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
# You'll want to make sure that the following values are customized for your
# local development environment:
from logging import WARN
from os.path import dirname
from settings import MIDDLEWARE_CLASSES, INSTALLED_APPS, ACL_RULES,\
	LOGIN_REQUIRED_URLS_EXCEPTIONS, TOS_REQUIRED_URLS_EXCEPTIONS

DEBUG = True
DEBUG_MODELS = DEBUG
TEMPLATE_DEBUG = DEBUG
CHARGE_CARD_DEBUG = DEBUG
APP_INTERFACE_DEBUG = DEBUG
DEBUG_PROVIDER = False

INTERNAL_IPS = ('127.0.0.1',)

# override in local settings, when DEBUG False this setting is used
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ['your.site.com', '.site.com']  # , 'www.site.com', etc..

IS_DEV = True
IS_PROD = False
PROJECT_NAME = "mhlogin"
TEMPLATE_STRING_IF_INVALID = "**INVALID VAR**"


ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
    ('Brian Kim', 'bkim@myhealthincorporated.com'),
)

MANAGERS = ADMINS

DATABASES = {
	'default' : {
		'ENGINE': 'django.db.backends.mysql',
		'NAME': 'mhlogin',
		'USER': 'djangouser',
		'PASSWORD': 'cat123',
		'HOST': '',
	},
}

from sys import argv
if 'test' in argv:
	TEST_RUNNER = 'MHLogin.utils.test_runner.TestRunner'
	DATABASES['default'] = {'ENGINE': 'django.db.backends.sqlite3'}
	SOUTH_TESTS_MIGRATE = False


SERVER_PORT = '8000'
SERVER_ADDRESS = 'localhost'
SERVER_PROTOCOL = 'https'
# Used for KMS/cloud services. Choices are 'Mac', 'Windows' or 'Linux'.
# This is used to provide compatibility for *both* older and newer versions of pycrypto.
# Newer versions of pycrypto prefix the RSAObj class names with an underscore, whereas
# older versions didn't. As a result, pickling/unpickling of these objects causes
# problems across pycrypto versions. Use 'Linux' for newer pycrypto versions, and 'Mac'
# for older ones.
SERVER_PLATFORM = 'Linux'

# This is the path to the current installation of the MHLogin project on your machine.
INSTALLATION_PATH = ''.join((dirname(__file__),'/'))

APS_APPID = '' 
PYAPNS_CONFIG = {
        'HOST': 'http://localhost:7077',
        'INITIAL': [
                (APS_APPID,
				'',#path to the aps cert goes here
				'production')
        ],
}

# 2 weeks, in seconds -- the default. The KMS cookie is based on the session
# cookie's settings.
SESSION_COOKIE_AGE = 1209600
# Should be True in production (where DEBUG is False) and False in development,
# where DEBUG is often True.
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_DOMAIN = None
SESSION_COOKIE_NAME = 'sessionid'
# Should be '/' in the general case. Once multiple MHLogin installations in a
# single domain name is figured out completely, you'll need to customize this.
SESSION_COOKIE_PATH = '/'

SESSION_COOKIE_HTTPONLY = True

# And that's it. If you're running in a production-like environment, you'll need
# to deal with some of the below values.


# If this value is not False (in a test), then users who would be redirected
# to the login page should be redirected to this URL instead. Note that this
# will be sent in an HTTP3xx-level response, so 
LOGIN_REDIRECT = False
# for example, LOGIN_REDIRECT = 'https://www.mdcom.com/'

# If this value is not False (in a test), then users who would be redirected
# to the login page following a failed login attempt should be redirected to
# this URL instead. Note that this will be sent in an HTTP3xx-level response.
LOGIN_FAILED_REDIRECT = False
# for example, LOGIN_REDIRECT = '%s?invalid_credentials'%LOGIN_REDIRECT


# This is the command to run ffmpeg. For most devlopment environments, this
# should just be the program name. For most server environments, it should be
# the absolute path to the program.
FFMPEG_EXECUTABLE = 'ffmpeg' # for development
# FFMPEG_EXECUTABLE = '/usr/local/bin/ffmpeg' # for servers

# Set up the server_address to contain the port information, if defined.
if ('SERVER_PORT' in locals()):
	SERVER_ADDRESS = ''.join([SERVER_ADDRESS, ':', SERVER_PORT])

# Default to the console email backend -- this will print all of your cookies
# out to the console when you're running using the development server.
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'abcdefg'

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = ''.join([INSTALLATION_PATH, '/media/'])

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
#MEDIA_URL = 'http://localhost/mhlTrunk_media/'
MEDIA_URL = '/media/'

# Absolute path to the directory that log files should go to.
# Example: "/home/media/media.lawrence.com/"
LOGGING_ROOT = ''.join([INSTALLATION_PATH, '/logfiles/'])
LOGGING_LEVEL = WARN
LOGGING_LOG_SQL = False # Set to True, then let's get our site optimized a bit!
LOGGING_SHOW_METRICS = True

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    ''.join([INSTALLATION_PATH,'/templates/']),
)

# Yahoo! App ID, used for geolocation. This ID is for the dev account.
YAHOO_APP_ID = 'M2e9wa7e'

# Twilio AccountSid and AuthToken
TWILIO_ACCOUNT_SID = 'abcdefg'
TWILIO_ACCOUNT_TOKEN = 'abcdefg'

# Outgoing Caller ID previously validated with Twilio
TWILIO_CALLER_ID = '8005551212'

# Twilio Generic SMS Number Pool -- 18 numbers in here in total!
# Numbers can be added casually, but take care in removing numbers -- they're
# also stored in the SMS_senderlookup table.
TWILIO_SMS_NUMBER_POOL = [
	'8004664411',
]

#number smartphones will call to connect to the smartphone interface
TWILIO_C2C_NUMBER = 1234567890

# Password for these default keys is 'demo'. Note that the default keys are
# built against pycrypto for Linux. They may not work in Windows.
if (SERVER_PLATFORM == 'Mac'):
	CRYPTO_ADMIN_KEYPAIR = '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'
	CRYPTO_ADMIN_PUBLIC_KEY = 'KGlDcnlwdG8uUHVibGljS2V5LlJTQQpSU0FvYmoKcDEKKGRwMgpTJ2UnCkw2NTUzN0wKc1MnbicKTDE4OTQ3MDA0OTk0NTAwOTUxMDM1NDgwMzgzNjk5ODU4ODc4Njc0NzQ3MzEyMzY3MzA0MjEzNzU0MjI5NDczMTExNjI1MjA5ODk5NTgyMTEwODI0MTYyOTk1MDUyMDg2NTExNzEwMjEwNzM1NDE0MDkzNjE1Mjc5MDI2Mzg2NTQyNTY2MDA5NzYyOTk2NjI0OTIwMDY2MDg5MjExMjE5MTMxNDMwODg3NDI4NjYxMDkwNDA1Njk3Nzc1OTY4NDIxOTI4MTY2NzE0NTQzNTU5NzEyNTk1MTE4NDk3NDQ0Nzc2Mjg0OTIwMTY3Mzg3NjEzMDk5NDYwNzUwNzYxNzY5MDIzNzI5NDY2OTQ2NTgwNTIyMjA4OTYzMjc1MTIwODk4Nzg5Nzk5OTM1NjU1OTkyMTQ4OTY3MzE5MDExMTkxMjIyMzA5MDYyMjk4MzI5OTA2ODk5MjMwNTY1MDk1NTk0OTYyNDkyNDgwNjAzNjk3MjU3NTA3OTkyMjY5NTQ3NDAyNjkyNTY5OTA5NjY5NjMzNzA1MjQ2MDIxNTE4MjQzNTEzMjEwMTA1NDg3MDYxNDIzMzQwNTk5NDQ4MDM5NTY5OTY0Mzk2NjY3MTU2NDkwMzQ5NDIyMjc5OTM1MTc1MjgyMzYwNDU1MDUwNjg4OTI1OTA5MDM4MDQ5MjkxOTM5OTM3MTA3NjYzOTk5NjkwMDUzMjg3NTczMDc4MTA5NTY3NjQwMDQzOTkxNDQyOTQ1NjE2NjI1MDg1NjM3NTIyMjkyNjAxNDM4MTA2MTY2MDgyMTgzNDI4MzE5MDI1NzQ5OTQ5NDM0MDQzNTYxTApzYi4='
else:
	CRYPTO_ADMIN_KEYPAIR = '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'
	CRYPTO_ADMIN_PUBLIC_KEY = 'KGlDcnlwdG8uUHVibGljS2V5LlJTQQpfUlNBb2JqCnAxCihkcDIKUydlJwpMNjU1MzdMCnNTJ24nCkwxNjQ3NjgyNjgyNTAzMTI4NTE5NTQ5Nzk2MDU2ODE0MjA1MDM5OTA5NzE2MTg3MTYxMTQ1NzA2MjM0MjQyODI2ODI3MDk2MTMzMTYzMzc2NjgzMTU0ODQ2NTQ3MDI2ODU2MzA0NjI2NjA1Mjk0MDEyMDM3NjgwNjU4NjEzNzQ4ODQ1NjcyNTIxMzM2MDI3OTczOTk0MDY2OTQ2NDgzODI3NDk1Nzc4OTcwOTk1MTI2NzIwMjEzNjc4MTY1MjM2ODQ0MTk2MTIzMjAwMTYyMzQ2NzE1MjYwMzcwOTU2MjQ3NjI0NDA4NzgzNzk5NTMxNTQyMTcxNjUwNTQxNzE4NTY4MTY4ODExNjU0MjkyMDIwODY1MTU3OTQwMjcwNTQ1MzQ0MDgwMjk1ODQ0MjE3ODA1OTI0NTc3NzY2MTY5MTExMzg5OTI2MTEzMTIyNDE2NjgwOTYxMjkwODkzNDkxNjE5Mzg3MDI1MDAwMTQzMDU5MTg4ODY1MDU2NjMxNjYxODk5Mzg4MzAyNzI3OTQ3MDI1MDE2OTkyNzA2MDU2MjExNDk2MTQ5NDU0NzE5MjYyNDA0NzUzMDA3Njc2Mzk0MTI1MDgxNTk5OTYzMDQ1NjkwNzA4NDM3OTAyMTA0ODAzMDAzNDcxMzEwNDk0OTMxMjU2MTEwODE1ODk1NTM4NDgxMzQxMDEzNDExMzY5NjQ0ODg0NjUxODkwNjAyOTU3OTg4NjUwMzYzMTEwNTc2MzkyNDI1Mzg1ODAxMjEwNzEzMjgzNDM4MTIwMzU2NTYzMzcwNTg0MjU0MDk1Mzg3MDY1NTA0MTczNTM1N0wKc2Iu'

# Debug Goodies. You probably only want to mess with DEBUG_TOOLBAR_CONFIG --
# that's for the Django Debug Toolbar.
MIDDLEWARE_CLASSES += ('debug_toolbar.middleware.DebugToolbarMiddleware',)
INTERNAL_IPS = ('127.0.0.1',)
INSTALLED_APPS += ('debug_toolbar','django_extensions',)
DEBUG_TOOLBAR_CONFIG = {
    'INTERCEPT_REDIRECTS': False,
    #'SHOW_TOOLBAR_CALLBACK': custom_show_toolbar,
    #'EXTRA_SIGNALS': ['myproject.signals.MySignal'],
    'HIDE_DJANGO_SQL': False,
    #'TAG': 'div',
}
LOGIN_REQUIRED_URLS_EXCEPTIONS += (r'^/__debug__/',)
TOS_REQUIRED_URLS_EXCEPTIONS += (r'^/__debug__/',)
ACL_RULES = (('^/__debug__/', 'ACCEPT', '*'),)+ACL_RULES

#how long user can submit another request
RESET_PASSWORD_HOURS = 3
#how many time user can try when they answer security questions 
SECURITY_ANSWER_MAXUMIN_FAIL_TIME = 3

#admin password for reset user password
ADMIN_PASSWORD = 'demo'

# Rackspace Cloud Files configuration
CLOUDFILE_USERNAME='changeme'
CLOUDFILE_APIKEY='thatsthepasswordtomyluggage!'
# The prefix for the container/directory that this installation's attachments
# will go into. Please make ownership of the container clear.
CONTAINER_PREFIX='blarg'
# Timout for SSL connections. This has been reported to be an issue with RS
# Cloud, and is something we've seen. 10 seconds is the current experimental
# suggestion. This variable is optional. If you comment it out (or delete it),
# the timeout defaults to 5 seconds, the standard libarary default.
CLOUDFILE_TIMEOUT = 10

# The path of temporary directory, if ATTACHMENTS_TEMP_ROOT is blank, it will use the system temporary directory.
ATTACHMENTS_TEMP_ROOT = ''
# Timeout of temporary directory for cleaning, unit: s
ATTACHMENTS_TEMP_TIMEOUT = 24*60*60
# The uploaded file's max size unit: MB
MAX_UPLOAD_SIZE = 10

# Caches configuration, it's used to store the upload progress information.
# This configuration is very important to Linux system
# If your django's version is 1.3, you must config the cache like below, 
# and make sure the directory exists and is readable and writable by the user apache.
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': '/var/tmp/django_cache',
        'TIMEOUT': 60*60,
        'OPTIONS': {
            'MAX_ENTRIES': 10000
        }
    }
}


BRAINTREE_MERCHANT_ID = 'YOUR_BT_MERCH_ID'
BRAINTREE_PUBLIC_KEY = 'YOUR_BT_PUBLIC_KEY'
BRAINTREE_PRIVATE_KEY = 'YOUR_BT_PRIVATE_KEY'
from braintree import Configuration, Environment

Configuration.configure(
    Environment.Production if IS_PROD else Environment.Sandbox,
    BRAINTREE_MERCHANT_ID,
    BRAINTREE_PUBLIC_KEY,
    BRAINTREE_PRIVATE_KEY
)


# If your django's version is 1.2, you must config the cache like below, 
# and make sure the directory exists and is readable and writable by the user apache.
CACHE_BACKEND = 'file:///var/tmp/django_cache'

AWS_ACCESS_KEY_ID = None
AWS_SECRET_ACCESS_KEY = None
S3_BUCKET_NAME = None

# Forced language setting, if you configure this value, the system will display messages/page by using this language. 
#   Default: en-us
# If you configure this value, you must provide files:
#   1.JS language package file "l10n_[FORCED_LANGUAGE_CODE].js" in the directory MHLogin/media/js/localization
FORCED_LANGUAGE_CODE='en-us'

# Configure LOCALE_PATHS for Django 1.5. Or, django can't find the .mo file.
LOCALE_PATHS = (''.join([INSTALLATION_PATH, '/locale/']),)

# Configure the call feature whether it's enable, default: True.
CALL_ENABLE = True

CHECKUSERNAME_URL = ['http://10.200.0.111','https://dev-maint3.mdcom.com']

# Maximum times of sending code per day.
SEND_MAXIMUM_PER_DAY = 5
# Waiting time after last sending code, unit: minute
SEND_CODE_WAITING_TIME = 2
# Maximum times per hour of failure verify
FAIL_VALIDATE_MAXIMUM_PER_HOUR = 3
# The validate action will be locked if times of fail validate in one hour exceed FAIL_VALIDATE_MAXIMUM_PER_HOUR.
# It's the lock time below, unit: hour.
VALIDATE_LOCK_TIME = 2

GCM_API_KEY = ''
GCM_PROJECT_ID = ''

AWS_ACCESS_KEY_ID = None
AWS_SECRET_ACCESS = None
S3_BUCKET_NAME = None

# Dicom server configuration
# dicom server -- full path
DICOM_SERVER_URL="https://dicom.mdcom.com/dicom/Dim2jpg"
# dicom REVOKE_PATH -- full path
DICOM_REVOKE_URL=''.join((SERVER_PROTOCOL,'://',SERVER_ADDRESS,'/DicomCalling/'))

# used for SalesLeads export, if undefined export feature is disabled
#SALES_LEADS_EXPORT_URL = 'http://10.0.0.123:8185/path/to/generate.php'

# 2013-02-25 add by mwang 
TWILIO_APP_SID = 'AP94cb411ef0da5586491232f1d0ae88b0'
