# -*- coding: utf-8 -*-
import json
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseServerError

from MHLogin.api.v1.constants import ERROR_LIB

TIME_DISPLAY_FORMAT = '%m/%d/%Y %H:%M'

class HttpJSONSuccessResponse(HttpResponse):
	def __init__(self, content='', mimetype=None, status=None, content_type=None, data=None, warnings=None):
		if not data:
			data = {}
		if not warnings:
			warnings = {}
		ret_content = json.dumps({
					'data': data,
					'warnings': warnings
				})
		if content:
			ret_content = content

		super(HttpJSONSuccessResponse, self).__init__(content=ret_content, mimetype='application/json', status=status,
			content_type=content_type)

class HttpJSONErrorResponse(HttpResponseBadRequest):
	def __init__(self, content='', mimetype=None, status=None, content_type=None, errno=None, form=None):
		desc = ''
		if errno:
			desc = ERROR_LIB[errno]

		if form:
			errno = 'GE031'
			desc = form.errors

		err_obj = {
			'errno': errno,
			'descr': desc,
		}
		ret_content = json.dumps(err_obj)
		super(HttpJSONErrorResponse, self).__init__(content=ret_content, mimetype='application/json', status=status,
			content_type=content_type)

class HttpJSONServerErrorResponse(HttpResponseServerError):
	def __init__(self, content='', mimetype=None, status=None, content_type=None, message=''):
		err_obj = {
			'errno': 'SYS500',
			'descr': message,
		}
		ret_content = json.dumps(err_obj)
		super(HttpJSONServerErrorResponse, self).__init__(content=ret_content, mimetype='application/json', status=status,
			content_type=content_type)
