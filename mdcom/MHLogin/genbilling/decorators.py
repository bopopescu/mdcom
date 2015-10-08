from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils.decorators import available_attrs
from django.utils.translation import ugettext_lazy as _

from functools import wraps

from MHLogin.genbilling.models import Account


def good_account_standing(redirect_url=None):
	"""
	Decorator for views that checks that the users account is in good standing,
	if not will redirect to a page if supplied or will return 401
	Takes argument redirect_url that is a mapping of the django redirect
	https://docs.djangoproject.com/en/1.3/topics/http/shortcuts/#redirect
	"""
	def decorator(view_func):
		@wraps(view_func, assigned=available_attrs(view_func))
		def _wrapped_view(request, *args, **kwargs):
			user = request.user
			if not request.user.is_authenticated():
				#just return if not auth. Assuming use with login required dec
				return view_func(request, *args, **kwargs)

			account = Account.objects.filter(owner = user)
			if not account:
				account = Account.objects.filter(users = user)
				
			if account:
				account = account[0]#grab frist and only accout in list 
				if account.access_granted():
					return view_func(request, *args, **kwargs)
				else:
					if redirect_url:
						return redirect(redirect_url,  **kwargs)
					else:
						res = HttpResponse(_("Unauthorized"))
						res.status_code = 401
						return res
			else:
				raise ValidationError(_('Users must have account'))
			
		#end of _wrapped_view
		_wrapped_view.__doc__ = view_func.__doc__
		_wrapped_view.__repr__ = view_func.__repr__
		return _wrapped_view 
	
	return decorator


def account_owner_rights_required(redirect_url=None):
	"""
	Decorator for views only meant to be accesible to account owners
	"""
	def decorator(view_func):
		@wraps(view_func, assigned=available_attrs(view_func))
		def _wrapped_view(request, *args, **kwargs):
			user = request.user
			if not request.user.is_authenticated():
				#just return if not auth. Assuming use with login required dec
				return view_func(request, *args, **kwargs)

			account = Account.objects.filter(owner = user)
			if not account:
				if redirect_url:
					return redirect(redirect_url,  **kwargs)
				else:
					res = HttpResponse(_("Unauthorized"))
					res.status_code = 401
					return res
			else:
				return view_func(request, *args, **kwargs)
		#end of _wrapped_view
		_wrapped_view.__doc__ = view_func.__doc__
		_wrapped_view.__repr__ = view_func.__repr__
		return _wrapped_view 
	
	return decorator
