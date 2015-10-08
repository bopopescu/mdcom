#-*- coding: utf-8 -*-
'''
Created on 2013-5-29

@author: wxin
'''
import json

from django.http import HttpResponse

from MHLogin.MHLFavorite.utils import get_my_favorite, do_toggle_favorite
from MHLogin.apps.smartphone.v1.decorators import AppAuthentication
from MHLogin.MHLFavorite.forms import FavoriteListForm, ToggleFavoriteForm
from MHLogin.apps.smartphone.v1.errlib import err_GE031, err_GE002

@AppAuthentication
def my_favorite(request):
	if (request.method != 'POST'):
		return err_GE002()
	form = FavoriteListForm(request.POST)
	if (not form.is_valid()):
		return err_GE031(form)

	object_type_flag = None
	if "object_type_flag" in form.cleaned_data and form.cleaned_data["object_type_flag"]:
		object_type_flag = form.cleaned_data["object_type_flag"]

	favorites = get_my_favorite(request.user, object_type_flag=object_type_flag, 
				show_picture=True)
	response = {
		'data': {"favorites": favorites},
		'warnings': {},
	}
	return HttpResponse(content=json.dumps(response), mimetype='application/json')

@AppAuthentication
def toggle_favorite(request):
	if (request.method != 'POST'):
		return err_GE002()
	owner = request.user
	form = ToggleFavoriteForm(request.POST)
	if (not form.is_valid()):
		return err_GE031(form)

	object_type_flag = form.cleaned_data["object_type_flag"]
	object_id = form.cleaned_data["object_id"]
	is_favorite = form.cleaned_data["is_favorite"]
	do_toggle_favorite(owner, object_type_flag, object_id, is_favorite=is_favorite)

	response = {
		'data': {},
		'warnings': {},
	}
	return HttpResponse(content=json.dumps(response), mimetype='application/json')