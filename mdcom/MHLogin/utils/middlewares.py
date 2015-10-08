
import datetime
import re
import sys

from django.utils import translation
from django.utils.cache import patch_vary_headers
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import logout
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.utils.translation import ugettext_lazy as _

from MHLogin.MHLUsers.models import Administrator, Dietician, MHLUser, Provider, Salesperson, \
	Physician, NP_PA, OfficeStaff, Nurse, Office_Manager, Broker, Regional_Manager
from MHLogin.MHLUsers.utils import getCurrentUserInfo
from MHLogin.utils.templates import get_context
from MHLogin.utils.mh_logging import get_standard_logger 
from MHLogin.utils.admin_utils import mail_admins

# Set up a specific logger with our desired output level
if (not 'logger' in locals()):
	logger = get_standard_logger('%s/utils/Middlewares.log' % (settings.LOGGING_ROOT),
								'utils.Middlewares', settings.LOGGING_LEVEL)


class ExceptionDumpMiddleware(object):
	"""
	Middleware to dump exceptions. Loosely based on:
	http://djangosnippets.org/snippets/638/
	"""

	def process_exception(self, request, exception):
		# Get the exception info now, in case another exception is thrown later.
		#if isinstance(exception, Http500):
		return self.handle_500(request, exception)

	def handle_500(self, request, exception):
		exc_info = sys.exc_info()
		return self.exception_email(request, exc_info)

	def exception_email(self, request, exc_info):
		subject = _('Error (%(ip)s IP): %(path)s') % \
			{'ip': (request.META.get('REMOTE_ADDR') in 
				settings.INTERNAL_IPS and 'internal' or 'EXTERNAL'), 'path': request.path}
		try:
			request_repr = repr(request)
		except:
			request_repr = "Request repr() unavailable"
		message = "%s\n\n%s" % (_get_traceback(exc_info), request_repr)
		mail_admins(subject, message, include_stack=False)


def _get_traceback(self, exc_info=None):
	"""Helper function to return the traceback as a string"""
	import traceback
	return '\n'.join(traceback.format_exception(*(exc_info or sys.exc_info())))


class twilio_debug_middleware(object):
	"""
	Logs requests and responses to/from Twilio.
	"""
	def __init__(self, *args, **kwargs):
		super(twilio_debug_middleware, self).__init__(*args, **kwargs)
		self.twilio_re = re.compile('TwilioProxy')

	def process_view(self, request, view_func, view_args, view_kwargs):
		if (self.twilio_re.match(request.META['HTTP_USER_AGENT'])):
			# dump data to logs.
			logger.debug('%s: Request POST data is %s' % (request.session.session_key, str(request.POST)))
			logger.debug('%s: Request META data is %s' % (request.session.session_key, str(request.META)))

		return None

	def process_response(self, request, response):
		if (self.twilio_re.match(request.META['HTTP_USER_AGENT'])):
			# dump data to logs
			# logger.debug('%s: Response is %s'%(request.session.session_key,response.content))
			logger.debug('Response is %s' % (response.content,))
		return response


class MHL_SessionSetup_Middleware(object):
	"""
	This middleware shall configure common request session keys to help minimize
	recurring calls to functions to determine if the user is a Provider, for
	instance.

	Dependencies (i.e., this middleware must come after):
		django.contrib.sessions.middleware.SessionMiddleware
		django.contrib.auth.middleware.AuthenticationMiddleware
	"""

	# add all user types here, we should not add more - use groups and permissions :)
	str2klass = {'MHLUser': MHLUser, 'Provider': Provider, 'Physician': Physician,
				'NP_PA': NP_PA, 'Office_Manager': Office_Manager, 'OfficeStaff': OfficeStaff,
				'Dietician': Dietician, 'Administrator': Administrator, 'Nurse': Nurse,
				'Salesperson': Salesperson, 'Broker': Broker, 'Regional_Manager': Regional_Manager}

	def process_view(self, request, view_func, view_args, view_kwargs):
		if ('MHL_UserIDs' in request.session):
			# This means that the session has already been configured.
			# Just get the users and call it good.
			mhlusers = request.session['MHL_Users'] = dict()
			userIds = request.session['MHL_UserIDs']
			for key in userIds:
				try:
					mhlusers[key] = self.str2klass[key].objects.get(pk=userIds[key])
				except ObjectDoesNotExist:
					# This is OK exception -- If admin user modifying user's 
					# roles while that user is logged in causes this exception.
					logger.warning('Object does not exist %s' % key)
					logout(request)
					return HttpResponseRedirect('/')
				except NameError:
					# FAIL miserably crash and die this is a BUG somewhere else
					logger.error('NameError %s' % key)
				except Exception, e:
					print str(e)

			return None

		# First, kick out sessions that we don't need to set up.
		if (not request.user.is_authenticated()):
			# If the user isn't authenticated, there isn't much to do here.
			# Just accept the view.
			return None

		request.session['MHL_Users'] = dict()
		request.session['MHL_UserIDs'] = dict()

		request.session.modified = True
		userIds = request.session['MHL_UserIDs']  # a more convenient identifier

		# MHLUser object. Note that there *must* exist only *one* MHLUser for
		# every user. If this is not the case, an Exception is raised. This is
		# only here to ensure that we *only* have MHLUsers going through our
		# codebase.
		userIds['MHLUser'] = MHLUser.objects.get(pk=request.user.pk).pk

		# Provider and provider-based user types

		# Is the user a Provider?
		try:
			userIds['Provider'] = Provider.objects.get(user__pk=userIds['MHLUser']).pk
		except ObjectDoesNotExist:
			# This is a fine exception -- it just means the user isn't a Provider
			pass
		# Let all other exceptions pass.

		if ('Provider' in userIds):
			# Is the Provider a Physician?
			try:
				userIds['Physician'] = Physician.objects.get(user__pk=userIds['Provider']).pk
			except ObjectDoesNotExist:
				# This is a fine exception -- it just means the user isn't a Physician
				pass
			# Let all other exceptions pass.

			# Is the Provider an NP_PA?
			try:
				userIds['NP_PA'] = NP_PA.objects.get(user__pk=userIds['Provider']).pk
			except ObjectDoesNotExist:
				# This is a fine exception -- it just means the user isn't an NP_PA
				pass
			# Let all other exceptions pass.

		# Office Staff

		# Is the user OfficeStaff?
		try:
			userIds['OfficeStaff'] = OfficeStaff.objects.get(user__pk=userIds['MHLUser']).pk
		except ObjectDoesNotExist:
			# This is a fine exception -- it just means the user isn't OfficeStaff
			pass
		# Let all other exceptions pass.
		if ('OfficeStaff' in userIds):
			# Is the user a Nurse?
			try:
				userIds['Nurse'] = Nurse.objects.get(user__pk=userIds['OfficeStaff']).pk
			except ObjectDoesNotExist:
				# This is a fine exception -- it just means the user isn't a Nurse
				pass
			# Let all other exceptions pass.

			# Is the user an Office_Manager?
			try:
				practice = OfficeStaff.objects.get(user__pk=userIds['MHLUser']).current_practice
				userIds['Office_Manager'] = Office_Manager.objects.get(
						user__pk=userIds['OfficeStaff'], practice=practice).pk
			except ObjectDoesNotExist:
				# This is a fine exception -- it just means the user isn't a Office_Manager
				pass
			# Let all other exceptions pass.

			# Is the user a Dietician?
			try:
				userIds['Dietician'] = Dietician.objects.get(user__pk=userIds['OfficeStaff']).pk
			except ObjectDoesNotExist:
				# This is a fine exception -- it just means the user isn't a Dietician
				pass
			# Let all other exceptions pass.
			if ('Office_Manager' in userIds):
				try:
					userIds['Regional_Manager'] = Regional_Manager.objects.\
						get(office_mgr__pk=userIds['Office_Manager']).pk
				except ObjectDoesNotExist:
					# This is a fine exception -- it just means the user isn't a RegionalManager
					pass

		# Administrator/staff objects

		# Is the user an Administrator?
		try:
			userIds['Administrator'] = Administrator.objects.get(user=request.user).pk
		except ObjectDoesNotExist:
			# This is a fine exception -- it just means the user isn't an Administrator
			pass
		# Let all other exceptions pass.

		# Is the Provider a Salesperson?
		try:
			userIds['Salesperson'] = Salesperson.objects.get(user=request.user).pk
		except ObjectDoesNotExist:
			# This is a fine exception -- it just means the user isn't a Salesperson
			pass
		# Let all other exceptions pass.
		try:
			userIds['Broker'] = Broker.objects.get(user__pk=userIds['MHLUser']).pk
		except ObjectDoesNotExist:
			# This is a fine exception -- it just means the user isn't broker
			pass

		# Now, let's get the users
		mhlusers = request.session['MHL_Users']
		for key in userIds:
			mhlusers[key] = self.str2klass[key].objects.get(pk=userIds[key])

		# All done!
		return None

	def process_response(self, request, response):
		"""
		This method doesn't really do much beyond removal of
		request.session['MHL_Users'] so that we don't clutter up the session
		table more than we need to.
		"""
		if ('session' in dir(request)):
			if ('MHL_Users' in request.session):
				del request.session['MHL_Users']
		return response


class MHL_SSCheck_Middleware(object):
	"""
	Middleware component to check if the 'ss' cookie is missing and
	redirect users to a page asking for their password to regenerate it
	"""
	def process_view(self, request, view_func, view_args, view_kwargs):
		if (request.user.is_authenticated() and not 'ss' in request.COOKIES):
			logout(request)
			return HttpResponseRedirect('/')

		if (not request.path.startswith("/IVR/") and
				request.user.is_authenticated() and
					'password_change_time' in request.session and
			MHLUser.objects.filter(pk=request.user.pk).only("password_change_time").\
				get().password_change_time > request.session['password_change_time']):

			logout(request)
			return HttpResponseRedirect('/')

required = tuple([re.compile(url) for url in settings.LOGIN_REQUIRED_URLS])
exceptions = tuple([re.compile(url) for url in settings.LOGIN_REQUIRED_URLS_EXCEPTIONS])
termsExceptions = tuple([re.compile(url) for url in settings.TOS_REQUIRED_URLS_EXCEPTIONS])


class MHL_StatusCheck_Middleware(object):
	"""
	Middleware component that wraps the login_required decorator around 
	matching URL patterns. To use, add the class to MIDDLEWARE_CLASSES and 
	define LOGIN_REQUIRED_URLS and LOGIN_REQUIRED_URLS_EXCEPTIONS in your 
	settings.py. For example:


	>>> LOGIN_REQUIRED_URLS = (
		r'/topsecret/(.*)$',
	)
	>>> LOGIN_REQUIRED_URLS_EXCEPTIONS = (
		r'/topsecret/login(.*)$', 
		r'/topsecret/logout(.*)$',
	)

	LOGIN_REQUIRED_URLS is where you define URL patterns; each pattern must 
	be a valid regex.	 

	LOGIN_REQUIRED_URLS_EXCEPTIONS is, conversely, where you explicitly 
	define any exceptions (like login and logout URLs).
	"""
	def __init__(self):
		pass	

	def process_view(self, request, view_func, view_args, view_kwargs):
		# No need to process URLs if user already logged in
		if request.user.is_authenticated():
			for url in termsExceptions:
				if url.match(request.path): 
					return None
			mhluser = MHLUser.objects.get(id=request.user.id)
			if (not mhluser.tos_accepted):
				return HttpResponseRedirect(reverse('MHLogin.MHLogin_Main.views.terms_acceptance'))
			#if (not mhluser.billing_account_accepted):
			#	return HttpResponseRedirect(reverse('MHLogin.Billing.views.billing_edit'))
			#if (not mhluser.email_confirmed):
			#	pass

			user = getCurrentUserInfo(request)
			if user and user.needValidateContactInfo:
				return HttpResponseRedirect(reverse('MHLogin.Validates.views.validationPage'))

			# See if this user is a provider or broker. If so, make sure they have a doctorcom number
			if (user and user.needConfigureProvisionLocalNumber):
				return HttpResponseRedirect(reverse(
					'MHLogin.DoctorCom.NumberProvisioner.views.provisionLocalNumber'))
			return None
		# An exception match should immediately return None
		for url in exceptions:
			if url.match(request.path): 
				return None
		# Requests matching a restricted URL pattern are returned 
		# wrapped with the login_required decorator
		for url in required:
			if url.match(request.path): 
				return login_required(view_func)(request, *view_args, **view_kwargs)
		# Explicitly return None for all non-matching requests
		return None

pw_change_exceptions = tuple([re.compile(url) for url in settings.FORCE_PW_CHANGE_URL_EXCEPTIONS])


class MHL_ForcePasswordChange_Middleware(object):
	def process_view(self, request, view_func, view_args, view_kwargs):
		global pw_change_exceptions
		if(not request.path.startswith("/IVR/") and
			not request.path.startswith("/media/") and
			request.user.is_authenticated() and
			request.path != reverse('MHLogin.MHLUsers.views.change_password') and
			not any(url.match(request.path) for url in pw_change_exceptions) and
			MHLUser.objects.filter(pk=request.user.pk).only('force_pass_change')[0].force_pass_change):
				return HttpResponseRedirect(reverse("MHLogin.MHLUsers.views.change_password"))


class MHL_ACL_Middleware(object):
	"""
	This middleware shall allow us to define access to various paths with
	greater granularity than the MHL_StatusCheck_Middleware provides.

	Configuration is pulled from settings.py. The following variables are
	looked for:
	- ACL_RULES: Defines the urls/paths that users are allowed or denied access to. 
	The rule format is documented in settings.py.
	- ACL_DEFAULT_DENY: Set to true if you want the ACL system to default reject users 
	access to pages not explicitly allowed in ACL_WHITELIST. Use in conjunction with 
	the ACL_WHITELIST variable.

	Dependencies (i.e., this middleware must come after):
		- django.contrib.sessions.middleware.SessionMiddleware
		- django.contrib.auth.middleware.AuthenticationMiddleware
		- MHL_RequestSessionSetup_Middleware
	"""
	def __init__(self):
		self.rules_checked = None
		if (settings.ACL_DEFAULT_BEHAVIOR != 'ACCEPT' and settings.ACL_DEFAULT_BEHAVIOR != 'DENY'):
			raise Exception(_('ACL_DEFAULT_BEHAVIOR must be either \'ACCEPT\' or \'DENY\''))
		self.rules = []
		for rule in settings.ACL_RULES:
			pattern = re.compile(rule[0])
			self.rules.append([[pattern, rule[0]]])
			self.rules[-1].extend(rule[1:])

	# Our overall strategy here is to check to see if we match any blacklist
	# rules first, and reject any accesses that match those blacklist rules
	# summarily. Then, we check to see if ACL_DEFAULT_DENY is set to True. If
	# so, then we check to see if any whitelist rules match. If so, then
	# accept the request. Lastly, either accept or reject the request based on
	# ACL_DEFAULT_DENY.
	def process_view(self, request, view_func, view_args, view_kwargs):
		for rule in self.rules:
			if (not rule[0][0].match(request.path)):
				continue
			# Okay, this rule matches the current request.
			logger.debug('%s: Match on rule %s' % (request.session.session_key, rule))
			if (rule[1].__class__.__name__ == 'str'):
				logger.debug('%s: String found -- single rule for this regex' % 
							(request.session.session_key,))
				result = self._rule_check(request, rule[1], rule[2:])
				if (result == 'ACCEPT'):
					return None
				elif (result == 'DENY'):
					return self._denial_responder(logger, request)
			else:
				logger.debug('%s: Non-string found -- multiple rules for this regex' % 
							(request.session.session_key,))
				for user_type_match in rule[1:]:
					result = self._rule_check(request, user_type_match[0], user_type_match[1:])
					if (result == 'ACCEPT'):
						return None
					elif (result == 'DENY'):
						return self._denial_responder(logger, request)

		if (settings.ACL_DEFAULT_BEHAVIOR == 'ACCEPT'):
			return None
		elif (settings.ACL_DEFAULT_BEHAVIOR == 'DENY'):
			return self._denial_responder(logger, request)

	def _rule_check(self, request, action, user_types):
		logger.debug('%s: Into _rule_check with user_types %s and action %s' % 
					(request.session.session_key, user_types, action))
		for user_type in user_types:
			if (user_type == '*'):
				logger.debug('%s: Returning %s' % (request.session.session_key, action))
				return action
			if (user_type == None and not request.user.is_authenticated()):
				logger.debug('%s: user.is_authenticated() returns %s' % 
							(request.session.session_key, request.user.is_authenticated()))
				logger.debug('%s: Returning %s' % (request.session.session_key, action))
				return action
			if ('MHL_UserIDs' in request.session and user_type in request.session['MHL_UserIDs']):
				logger.debug('%s: Returning %s' % (request.session.session_key, action))
				return action
			if user_type and hasattr(self, user_type) and callable(getattr(self, user_type)):
				action = getattr(self, user_type)(request.user)  # TODO pass in view/path 
				return action

		logger.debug('%s: Returning None' % (request.session.session_key))
		return None

	# Proof of concept when we add view permissions make more generic, eg:
	# def can_view(self, user, url_or_view_name):
	def can_view_dcadmin(self, user):
		from MHLogin.Administration.tech_admin.utils import is_techadmin, is_readonly_admin
		return "ACCEPT" if is_techadmin(user) or is_readonly_admin(user) or \
			user.is_superuser else "DENY"

	def _denial_responder(self, logger, request):
		from time import time
		import random
		context = get_context(request)
		issue_code = ['ACD', str(int(time()) % 10000000)]
		if (request.user.is_authenticated()):
			issue_code.insert(1, str(request.user.pk))
			msg = '%s/%s: ACCESS DENIED to user %s %s (pk=%s) from %s. request.    META is \'%s\'' % \
				(request.session.session_key, '-'.join(issue_code), request.user.first_name, 
					request.user.last_name, request.user.pk, request.META['REMOTE_ADDR'], request.META)
			logger.error(msg)
		else:
			issue_code.insert(1, 'NA')
			msg = '%s/%s: ACCESS DENIED to anonymous user from %s. request.META is \'%s\'' % \
				(request.session.session_key, '-'.join(issue_code), 
					request.META['REMOTE_ADDR'], request.META)
			logger.error(msg)
		issue_code.append(str(random.randrange(100, 999)))

		context['issue_code'] = '-'.join(issue_code)

		subj = _('ACL Denial %(issue_code)s: %(path)s') % \
			{'issue_code': '-'.join(issue_code), 'path': request.path}

		mail_admins(subj, msg, fail_silently=False)

		response = render_to_response('ACL/access_denied.html', context)
		response.status_code = 403
		return response


class MHL_LanguageSetup_Middleware(object):
	"""
	This is a very simple middleware that parses a request
	and decides what translation object to install in the current
	thread context. This allows pages to be dynamically
	translated to the language the system desires -- configure in the settings.py(if the language
	is available, of course).
	"""
	def process_request(self, request):
		language = translation.get_language_from_request(request)
		if settings.FORCED_LANGUAGE_CODE:
			translation.activate(settings.FORCED_LANGUAGE_CODE)
		request.LANGUAGE_CODE = translation.get_language()

	def process_response(self, request, response):
		patch_vary_headers(response, ('Accept-Language',))
		if 'Content-Language' not in response:
			response['Content-Language'] = translation.get_language()
		translation.deactivate()
		return response


class GlobalConstantSetup_Middleware(object):
	"""
	This is a very simple middleware that append desired global constant variables to the request.
	"""
	def process_request(self, request):
		request.CALL_ENABLE = settings.CALL_ENABLE
		request.MAX_UPLOAD_SIZE = settings.MAX_UPLOAD_SIZE
		today = datetime.date.today()
		request.SERVER_TIME_YEAR = today.year
		request.SEND_CODE_WAITING_TIME = settings.SEND_CODE_WAITING_TIME
		request.VALIDATE_LOCK_TIME = settings.VALIDATE_LOCK_TIME

	def process_response(self, request, response):
		return response

PREVENT_CACHE_PATH_PREFIX = [
	'/app/smartphone/',
	'/api/'
]

class NoCacheMiddleware(object):
	def process_response(self, request, response):
		req_path = request.path
		prevent_cache = False
		for prefix in PREVENT_CACHE_PATH_PREFIX:
			if req_path and req_path.startswith(prefix):
				prevent_cache = True
				break
		if prevent_cache:
			response['Pragma'] = 'no-cache'
			response['Cache-Control'] = 'no-store'
		return response
