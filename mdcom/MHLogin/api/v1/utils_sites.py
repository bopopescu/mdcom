# -*- coding: utf-8 -*-
'''
Created on 2012-9-26

@author: mwang
'''

from django.db.models import Q
from django.forms.models import model_to_dict
from django.http import Http404

from MHLogin.MHLSites.models import Site
from MHLogin.MHLUsers.models import Provider
from MHLogin.api.v1.utils_users import setSubProviderResultList, setOfficeStaffResultList
from MHLogin.MHLUsers.utils import get_all_site_providers, get_all_site_staff, get_all_site_clinical_clerks

def getSiteList(condition_dict):
	q_condition = Q()
	limit = None
	if condition_dict:
		if 'name' in condition_dict and condition_dict['name']:
			name = condition_dict['name']
			q_condition.add(Q(name__icontains=name), Q.AND)

		if 'address' in condition_dict and condition_dict['address']:
			address = condition_dict['address']
			q_condition.add(Q(Q(address1__icontains=address) | Q(address2__icontains=address)), Q.AND)

		if 'city' in condition_dict and condition_dict['city']:
			city = condition_dict['city']
			q_condition.add(Q(city__icontains=city), Q.AND)

		if 'state' in condition_dict and condition_dict['state']:
			state = condition_dict['state']
			q_condition.add(Q(state=state), Q.AND)

		if 'zip' in condition_dict and condition_dict['zip']:
			zip = condition_dict['zip']
			q_condition.add(Q(zip=zip), Q.AND)

		if 'limit' in condition_dict and condition_dict['limit']:
			limit = condition_dict['limit']

	query_rs = Site.objects.filter(q_condition)
	total_count = query_rs.count()
	if limit and query_rs.count() > limit:
		query_rs = query_rs[:limit]

	data = {}
	data['total_count'] = total_count
	results = data['results'] = []
	for ele in query_rs:
		results.append(model_to_dict(ele, exclude=('lat', 'longit')))
	return data

def getSiteInfo(site_id):
	if not site_id:
		raise Http404 

	try:
		site = Site.objects.get(pk=site_id)
		return model_to_dict(site, exclude=('lat', 'longit'))
	except Site.DoesNotExist:
		raise Http404

def getSiteProviders(site_id):
	if not site_id:
		raise Http404 

	try:
		site = Site.objects.get(pk=site_id)
		rs = get_all_site_providers(site)
		data = {}
		data['users'] = setSubProviderResultList(rs)
		return data
	except Site.DoesNotExist:
		raise Http404

def getSiteStudents(site_id):
	if not site_id:
		raise Http404 

	try:
		site = Site.objects.get(pk=site_id)
		rs = get_all_site_clinical_clerks(site)
		data = {}
		data['users'] = setSubProviderResultList(rs)
		return data
	except Site.DoesNotExist:
		raise Http404

def getSiteStaff(site_id):
	if not site_id:
		raise Http404 

	try:
		site = Site.objects.get(pk=site_id)
		rs = get_all_site_staff(site)
		data = {}
		data['users'] = setOfficeStaffResultList(rs)
		return data
	except Site.DoesNotExist:
		raise Http404

