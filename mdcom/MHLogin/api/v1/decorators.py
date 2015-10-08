# -*- coding: utf-8 -*-

'''
Created on 2012-9-12

@author: mwang
'''
import base64
import datetime
import re

from functools import wraps
from django.contrib.auth import authenticate
from django.contrib.auth.models import User

from MHLogin.MHLUsers.models import MHLUser, Provider, OfficeStaff, Broker
from MHLogin.api.v1.utils import HttpJSONErrorResponse
from MHLogin.utils.constants import USER_TYPE_DOCTOR, USER_TYPE_OFFICE_STAFF,\
	USER_TYPE_BROKER

uuid_re = re.compile(r'[A-Za-z0-9]{32}$')


def APIAuthentication(func, *args, **kwargs):
	"""
	Used as a decorator for api view functions
	"""
	@wraps(func)
	def f(request, *args, **kwargs):
		start_time = datetime.datetime.now()
		result = checkAndRequest(func, request, *args, **kwargs)
		end_time = datetime.datetime.now()
		# TODO API Authentication will need revisit for feature/2049, OAuth
		return result  # result

	return f


def checkAndRequest(func, request, *args, **kwargs):
	# MDCOM_API_KEY must be in HTTP header when accessing all API interface.
	# Note that MDCOM_API_KEY has 'HTTP_' prepended to it by Django,
	# so we're looking for HTTP_MDCOM_API_KEY.
	if (not 'HTTP_MDCOM_API_KEY' in request.META):
		return HttpJSONErrorResponse(errno='GE050')

	#api_key = request.META['HTTP_MDCOM_API_KEY']
	# TODO: verify hash api key matches hash of oauth user token key  

	if (not 'HTTP_MDCOM_USER_UUID' in request.META):
		return HttpJSONErrorResponse(errno='GE052')

	# TODO check private resources permission use MDCOM_USER_UUID and MDCOM_API_KEY
	user_uuid = request.META['HTTP_MDCOM_USER_UUID']
	if not uuid_re.match(user_uuid):
		return HttpJSONErrorResponse(errno='GE053')

	if not checkPartnerAccountAndSetRequest(request, user_uuid):
		return HttpJSONErrorResponse(errno='GE053')

	return func(request, *args, **kwargs)


def checkAPIKeyAndSetRequest(request, api_key):
	keys = api_key.split('-')
	if not keys or len(keys) < 3:
		return False
	uuid = base64.b64decode(keys[0])
	password = base64.b64decode(keys[1])

	user = None
	try:
		mhluser = MHLUser.objects.get(uuid=uuid)
		user = authenticate(username=mhluser.username, password=password)
		if not user or not user.is_active:
			return False
	except MHLUser.DoesNotExist:
		return False

	return True


def checkPartnerAccountAndSetRequest(request, user_uuid):
	try:
		# TODO after adding filed uuid to MHLUser, update following code.
		mhluser = MHLUser.objects.get(uuid=user_uuid)
		request.mhluser = mhluser
		user = User.objects.get(id=mhluser.pk)
		request.user = user
		request.user_type = None

		try:
			role_user = Provider.objects.get(user=mhluser)
			request.role_user = role_user
			request.user_type = USER_TYPE_DOCTOR
			return True
		except Provider.DoesNotExist:
			pass

		try:
			role_user = OfficeStaff.objects.get(user=mhluser)
			request.role_user = role_user
			request.user_type = USER_TYPE_OFFICE_STAFF
			return True
		except OfficeStaff.DoesNotExist:
			pass

		try:
			role_user = Broker.objects.get(user=mhluser)
			request.user_type = USER_TYPE_BROKER
			request.role_user = role_user
			return True
		except Broker.DoesNotExist:
			pass
	except MHLUser.DoesNotExist:
		return False
	return True
