#-*- coding: utf-8 -*-
'''
Created on 2013-3-24

@author: wxin
'''
from django.db.models.query_utils import Q

from MHLogin.MHLPractices.models import OrganizationType, OrganizationTypeSubs, PracticeLocation,\
	OrganizationRelationship
from MHLogin.utils.constants import RESERVED_ORGANIZATION_TYPES_RESERVED,\
	RESERVED_ORGANIZATION_TYPE_ID_SYSTEM

def get_sub_types_by_typeid(type_id, is_public=None):
	""" Get sub organization's types of this organization type.
	:param type_id: is org's type id
	:param is_public: public filter
	:returns: list(OrganizationType)
	"""
	q_f = Q(delete_flag=False)
	if is_public:
		q_f = q_f & Q(is_public=True)

	try:
		org_type = OrganizationType.objects.get(id=type_id)
		subs = list(org_type.subs.filter(q_f)\
				.exclude(id=RESERVED_ORGANIZATION_TYPE_ID_SYSTEM))
	except:
		return []
	return subs

def get_parent_types_by_typeid(type_id, is_public=None):
	""" Get parent organization's types of this organization type.
	:param type_id: is org's type id
	:param is_public: public filter
	:returns: list(OrganizationType)
	"""
	q_f = Q(from_organizationtype__delete_flag=False) & Q(to_organizationtype__id=type_id)
	if is_public:
		q_f = q_f & Q(from_organizationtype__is_public=True)

	parent_type = OrganizationTypeSubs.objects.filter(q_f).select_related('from_organizationtype')
	org_types_f_c = []
	for pt in parent_type:
		org_types_f_c.append(pt.from_organizationtype)
	return org_types_f_c

def can_we_remove_this_org_type(org_type_id):
	""" Check this organization type can be removed.
	:param org_type_id: is org's type id
	:returns: True or False
	"""
	if org_type_id in RESERVED_ORGANIZATION_TYPES_RESERVED:
		return False
	if len(how_many_instances(org_type_id)):
		return False
	if OrganizationTypeSubs.objects.filter(Q(from_organizationtype__id=org_type_id)
		or Q(to_organizationtype__id=org_type_id)).exists():
		return False

	return True

def can_we_create_this_type_under_that_type(sub_type_id, parent_type_id):
	""" Check this type(sub_type_id) of organization can be created under 
			that type(parent_type_id) of organization
	:param sub_type_id: is org's type id
	:param parent_type_id: is org's type id
	:returns: True or False
	"""
	if sub_type_id == RESERVED_ORGANIZATION_TYPE_ID_SYSTEM:
		return False
	return OrganizationTypeSubs.objects.filter(from_organizationtype__id=parent_type_id, to_organizationtype__id=sub_type_id).exists()

def how_many_instances(type_id, parent_type_id=None):
	""" Get organizations of this organization type
	:param type_id: is org type id
	:param parent_type_id: is org parent type id
		if parent_type_id is not None, return PracticeLocation list whose type's id is type_id, 
		and the PracticeLocation below the organization type of parent_type_id
	:returns: list(PracticeLocation)
	"""
	q_f = Q(organization_type__id=type_id)
	if parent_type_id:
		org_ids = OrganizationRelationship.objects.filter(parent__organization_type__id=parent_type_id).values_list("organization__id", flat=True);
		q_f = q_f & Q(organization_type__id=type_id, id__in=org_ids)
	return list(PracticeLocation.objects.filter(q_f))

