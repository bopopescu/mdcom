
import json

from django.db.models import Q
from django.http import HttpResponse
from django.utils.translation import ugettext as _
from django.shortcuts import render_to_response

from models import Provider
from forms import nameSearchForm

from MHLogin.utils.templates import get_context
from MHLogin.utils.errlib import err5xx


def search_by_practice(request):
	if (request.method == 'POST'):
		form = nameSearchForm(request.POST)
	else:
		form = nameSearchForm(request.GET)

	if (form.is_valid()):
		search_terms = unicode.split(form.cleaned_data['q'])
		limit = form.cleaned_data['limit']
		return_set = Provider.objects.filter()
		for term in search_terms:
			return_set = return_set.filter(
							Q(user__first_name__icontains=term) |
							Q(user__last_name__icontains=term))
		return_set = return_set.only('user__first_name', 'user__last_name')[:limit]

		return_obj = [[u.user.pk, ' '.join([u.user.first_name, u.user.last_name])] 
					for u in return_set]

		return_obj = ['ok', return_obj]

		return HttpResponse(json.dumps(return_obj), mimetype='application/json')

	else:  # if (not form.is_valid())
		return HttpResponse(json.dumps(['err', _('A server error has occurred.')]), 
			mimetype='application/json')


#series of functions to handle stuff association with practice
def practicesHome(request):
	context = get_context(request)
	if ('Provider' in request.session['MHL_UserIDs']):
		#print "%s %s is a Provider"%(request.user.first_name, request.user.last_name)
		#context = get_context(request)
		pass
	else:
		return err5xx(request, 501, _('Only Providers can manager their practice associations'))

	return render_to_response('Staff/practicesHome.html', context)

