
import random
import httplib

from time import time
from django.shortcuts import render_to_response
from django.utils.translation import ugettext_lazy as _

from MHLogin.utils.templates import get_context
from MHLogin.utils.admin_utils import mail_admins


def err5xx(request, code=500, msg="", extra_ctx=None):
	""" Generic response for 5xx server-side error codes as per rfc2616

	:returns resp: Our DoctorCom'ish err5xx 
	""" 
	return errxxx(request, 'err5xx.html', code, msg, extra_ctx)


def err4xx(request, code=400, msg="", extra_ctx=None):
	""" Generic response for 4xx client-side error codes as per rfc2616

	:returns resp: Our DoctorCom'ish err4xx 
	""" 
	return errxxx(request, 'err4xx.html', code, msg, extra_ctx)


def errxxx(request, tmpl, code, msg, extra_ctx=None):
	ctx = get_context(request)
	ctx['err_title'] = httplib.responses[code] if code in httplib.responses else ""
	ctx['err_msg'] = msg
	ctx['err_code'] = str(code)
	ctx.update(extra_ctx or {})

	resp = render_to_response(tmpl, ctx)
	resp.status_code = code
	return resp


def msg3xx(request, code=300, msg=""):
	""" Generic response for 3xx re-direction responses, generally 
	handled with django in response templates
	"""
	raise Exception("Not currently implemented.")


def msg2xx(request, code=200, msg=""):
	""" Generic response for 2xx successful responses, generally 
	handled with django in response templates
	"""
	raise Exception("Not currently implemented.")


def msg1xx(request, code=100, msg=""):
	""" Generic response for 1xx informative responses, generally 
	handled with django in response templates
	"""
	raise Exception("Not currently implemented.")


def err403_denied(request):
	""" Helper to send access denied message to client and report incident to admin(s)

	:returns: HttpResonse with specified error template
	"""
	issue_code = ['ACD', str(int(time()) % 10000000)]
	if (request.user.is_authenticated()):
		issue_code.insert(1, str(request.user.pk))
		msg = '%s/%s: ACCESS DENIED to user %s %s (pk=%s) from %s. request.    "\
			"META is \'%s\'' % (request.session.session_key, '-'.join(issue_code), 
							request.user.first_name, request.user.last_name,
							request.user.pk, request.META['REMOTE_ADDR'], request.META)
	else:
		issue_code.insert(1, 'NA')
		msg = '%s/%s: ACCESS DENIED to anonymous user from %s. request.META is \'%s\'' % \
			(request.session.session_key, '-'.join(issue_code), 
				request.META['REMOTE_ADDR'], request.META)
	issue_code.append(str(random.randrange(100, 999)))

	issue_msg = '-'.join(issue_code)
	subj = _('ACL Denial %(issue_code)s: %(path)s') % \
		{'issue_code': issue_msg, 'path': request.path}
	mail_admins(subj, msg, fail_silently=False)

	return errxxx(request, 'ACL/access_denied.html', 403, None, {'issue_code': issue_msg})


### The methods below are now deprecated ###


def err403(request, err_msg=None):
	context = get_context(request)
	context['err_msg'] = err_msg
	resp = render_to_response('403.html', context)
	resp.status_code = 403
	return resp


def err404(request):
	resp = render_to_response('404.html', get_context(request))
	resp.status_code = 404
	return resp


def err500(request, err_msg=None):
	context = get_context(request)
	context['err_msg'] = err_msg
	resp = render_to_response('500.html', context)
	resp.status_code = 500
	return resp

