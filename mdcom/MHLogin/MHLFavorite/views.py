#-*- coding: utf-8 -*-
'''
Created on 2013-5-28

@author: wxin
'''
import json

from django.http import HttpResponseBadRequest, HttpResponse

from MHLogin.MHLFavorite.forms import FavoriteListForm, ToggleFavoriteForm
from MHLogin.MHLFavorite.utils import do_toggle_favorite, get_my_favorite

def my_favorite(request):
	if (request.method == 'POST'):
		form = FavoriteListForm(request.POST)
	else:
		form = FavoriteListForm(request.GET)

	if form.is_valid():
		object_type_flag = None
		if "object_type_flag" in form.cleaned_data and form.cleaned_data["object_type_flag"]:
			object_type_flag = form.cleaned_data["object_type_flag"]

		can_send_refer = True
		if 'Broker' in request.session['MHL_Users']:
			can_send_refer = False

		owner = request.session['MHL_Users']['MHLUser']
		my_favorite_html = get_my_favorite(owner, object_type_flag=object_type_flag,
			html=True, can_send_refer = can_send_refer)
		return HttpResponse(my_favorite_html)
	else:
		err_obj = {
			'errors': form.errors,
		}
		return HttpResponseBadRequest(json.dumps(err_obj), mimetype='application/json')

def toggle_favorite(request):
	owner = request.session['MHL_Users']['MHLUser']
	if (request.method == 'POST'):
		form = ToggleFavoriteForm(request.POST)
	else:
		form = ToggleFavoriteForm(request.GET)

	if form.is_valid():
		object_type_flag = form.cleaned_data["object_type_flag"]
		object_id = form.cleaned_data["object_id"]
		is_favorite = form.cleaned_data["is_favorite"]
		do_toggle_favorite(owner, object_type_flag, object_id, is_favorite=is_favorite)
		return HttpResponse("ok")
	else:
		err_obj = {
			'errors': form.errors,
		}
		return HttpResponseBadRequest(json.dumps(err_obj), mimetype='application/json')