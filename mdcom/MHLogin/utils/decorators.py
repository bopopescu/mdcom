
from urllib2 import urlopen
from functools import wraps
from httplib import FORBIDDEN

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponseForbidden
from django.utils.unittest.case import skip
from django.utils.translation import ugettext as _

from MHLogin.utils.admin_utils import mail_admins
from MHLogin.utils.twilio_utils import validator
from MHLogin.utils.errlib import err4xx


def TwilioAuthentication(allow_get=False):
	"""   
	Decorator functions with arguments have inner decorator which behaves as
	standard decorator declared like @my_decorator with no params and args.  
	Outer most argument allow_get accessible by decorator implementation.  For 
	more detailed description see link and weblog comments:
	http://www.artima.com/weblogs/viewpost.jsp?thread=240845

	:param allow_get: explicitly allow GET for certain views
	:returns inner_decorator: the standard decorator
	"""
	def inner_decorator(func):
		""" Decorator for view functions requiring Twilio authentication """
		@wraps(func)
		def decorator_impl(request, *args, **kwargs):
			valid = False
			twilio_msg = _("Twilio signature invalid or missing.")
			if request.method == 'POST' or allow_get:
				if 'HTTP_X_TWILIO_SIGNATURE' not in request.META:
					mail_admins('HTTP_X_TWILIO_SIGNATURE missing', repr(request))
				else:			
					valid = validator.validate(uri=request.build_absolute_uri(), 
						signature=request.META['HTTP_X_TWILIO_SIGNATURE'],
							params=request.POST)
					if not valid:
						mail_admins("Twilio request didn't validate", repr(request))
			else:
				admin_msg = 'We received an unexpected request from Twilio to this URL:' \
					'\n\n%s\n\nIt is possible the configured url did not end with a "/", ' \
					'the configuration uses GET\ninstead of POST, or the view function ' \
					'should allow GET.  Please check the Twilio\nconfig for this user ' \
					'or practice, or check the view function.\n\n\n%s' % \
					(request.path, str(request))
				twilio_msg = _('Received unexpected request type from Twilio')
				mail_admins(twilio_msg, admin_msg)

			return func(request, *args, **kwargs) if valid else \
				err4xx(request, FORBIDDEN, twilio_msg)

		return decorator_impl
	return inner_decorator


def no_cache(func):
	""" No cache decorator adds settings to response so it's not cached in browser.
		TODO: Consider django.views.decorators.cache.never_cache() 
	"""
	@wraps(func)
	def decorator_impl(request, *args, **kwargs):
		response = func(request, *args, **kwargs)
		# no-cache required for ie7, expires=-1 should be enough for the other browsers
		response['Cache-Control'] = 'max-age=0,no-cache,no-store,post-check=0,pre-check=0'
		response['Expires'] = '-1'
		return response

	return decorator_impl


def skipIfUrlFails(url, reason, timeout=1):
	""" Skip decorator check for tests requiring network access """
	def check_connectivity(url, timeout):
		rc = True
		try:
			urlopen(url, timeout=timeout)
		except Exception:
			rc = False
		return rc

	if not check_connectivity(url, timeout):
		return skip(reason)

	return lambda arg: arg


def ratelimitview(limit=10, length=86400):
	""" 
	Decorator based off one from django snippets.  Rate limit 
	specific views, length in seconds and defaults to a day.
	"""
	def decorator(func):
		@wraps(func)
		def inner_impl(request, *args, **kwargs):
			if not settings.DEBUG:
				ip_hash = str(hash(request.META['REMOTE_ADDR']))
				hashkey = ip_hash + '_ratelimview_' + func.func_name
				# TODO: profile --> hash the whole string instead of just ip?
				hit = cache.get(hashkey)
				if hit:
					hit = int(hit)
					if hit >= limit:
						mail_admins("Telling my mom! Rate limit exceeded", repr(request))
						resp = HttpResponseForbidden("Too many requests!")
					else:
						hit += 1
						cache.set(hashkey, hit, length)
						resp = func(request, *args, **kwargs)
				else:
					cache.add(hashkey, 1, length)
					resp = func(request, *args, **kwargs)
			else:
				resp = func(request, *args, **kwargs)
			return resp

		return inner_impl
	return decorator

