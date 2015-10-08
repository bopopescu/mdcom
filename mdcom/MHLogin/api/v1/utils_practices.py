# -*- coding: utf-8 -*-
'''
Created on 2012-9-24

@author: mwang
'''
from django.db.models import Q
from django.forms.models import model_to_dict
from django.http import Http404

from MHLogin.MHLPractices.models import PracticeLocation
from MHLogin.MHLSites.models import Site
from MHLogin.MHLUsers.models import Office_Manager, Provider, OfficeStaff
from MHLogin.utils import ImageHelper
from MHLogin.api.v1.utils_users import setSubProviderResultList, setOfficeStaffResultList
from MHLogin.MHLUsers.utils import get_all_practice_staff, get_all_practice_providers
from MHLogin.MHLPractices.utils import get_practices_by_position

def getPracticeList(condition_dict, org_type_id=None):
	q_condition = Q()
	if org_type_id:
		q_condition.add(Q(organization_type__id=org_type_id), Q.AND)

	limit = None
	if condition_dict:
		if 'practice_name' in condition_dict and condition_dict['practice_name']:
			name = condition_dict['practice_name']
			q_condition.add(Q(practice_name__icontains=name), Q.AND)

		if 'practice_address' in condition_dict and condition_dict['practice_address']:
			address = condition_dict['practice_address']
			q_condition.add(Q(Q(practice_address1__icontains=address) | Q(practice_address2__icontains=address)), Q.AND)

		if 'practice_city' in condition_dict and condition_dict['practice_city']:
			city = condition_dict['practice_city']
			q_condition.add(Q(practice_city__icontains=city), Q.AND)

		if 'practice_state' in condition_dict and condition_dict['practice_state']:
			state = condition_dict['practice_state']
			q_condition.add(Q(practice_state=state), Q.AND)

		if 'practice_zip' in condition_dict and condition_dict['practice_zip']:
			zip = condition_dict['practice_zip']
			q_condition.add(Q(practice_zip=zip), Q.AND)

		if 'limit' in condition_dict and condition_dict['limit']:
			limit = condition_dict['limit']

	query_rs = PracticeLocation.objects.filter(q_condition)
	total_count = query_rs.count()
	if limit and query_rs.count() > limit:
		query_rs = query_rs[:limit]

	data = {}
	data['total_count'] = total_count
	data['results'] = setPracticeResultList(query_rs)
	return data

def getPracticeInfo(practice_id):
	if not practice_id:
		raise Http404 

	try:
		practice = PracticeLocation.objects.get(pk=practice_id)
		data = setPracticeResult(practice, "Middle")
		return data
	except PracticeLocation.DoesNotExist:
		raise Http404

def setPracticeResultList(practices_rs):
	practice_list = []
	for p in practices_rs:
		practice_list.append(setPracticeResult(p, "Small"))
	return practice_list

def setPracticeResult(p, logo_size):
	ele = model_to_dict(p,  fields=('id', 
									'practice_name', 
									'practice_address1', 
									'practice_address2', 
									'practice_city', 
									'practice_state',
									'practice_zip',
									'mdcom_phone'))
	ele["practice_photo"] = ImageHelper.get_image_by_type(p.practice_photo, logo_size, 'Practice')
	has_manager = Office_Manager.active_objects.filter(practice__id=p.id).exists();
	# If mobile app use this function, the keys  'has_mobile', 'has_manager' is useful.
	has_mobile = bool(p.practice_phone)
	ele["has_mobile"] = has_mobile
	ele["call_available"] = has_manager

	ele["has_manager"] = has_manager
	ele["msg_available"] = has_manager
	return ele

def getPracticeProviders(practice_id):
	if not practice_id:
		raise Http404 

	try:
		practice = PracticeLocation.objects.get(pk=practice_id)
		rs = get_all_practice_providers(practice, False)
		data = {}
		data['users'] = setSubProviderResultList(rs)
		return data
	except PracticeLocation.DoesNotExist:
		raise Http404

def getPracticeStaff(practice_id):
	if not practice_id:
		raise Http404 

	try:
		practice = PracticeLocation.objects.get(pk=practice_id)
		rs = get_all_practice_staff(practice)
		data = {}
		data['users'] = setOfficeStaffResultList(rs)
		return data
	except PracticeLocation.DoesNotExist:
		raise Http404

def getLocalOffice(current_practice):
	if not current_practice or not current_practice.practice_lat or not current_practice.practice_longit:
		raise Http404 
	practices = get_practices_by_position(current_practice.practice_lat, current_practice.practice_longit)
	data = {}
	data['practices'] = setPracticeResultList(practices)
	return data
