#-*- coding: utf-8 -*-
'''
Created on 2013-4-14
	move from old org
@author: wxin
'''
from django.db.models.query_utils import Q
from django.template.loader import render_to_string

from MHLogin.MHLOrganization.utils import which_orgs_contain_this_user, get_all_related_org_ids_below_this_org
from MHLogin.MHLUsers.models import Provider, OfficeStaff, Office_Manager
from MHLogin.MHLUsers.utils import set_org_members_result, get_specialty_display_by_provider
from MHLogin.utils import ImageHelper

def getOrganizationsOfUser(mhluser, current_practice=None):
	current_practice_id = None
	if current_practice:
		current_practice_id = current_practice.id
	orgs = which_orgs_contain_this_user(mhluser.id, exclude_org_ids=current_practice_id)
	if orgs and len(orgs):
		return [{
					'id':u.pk,
					'name':u.practice_name,
					'logo': ImageHelper.get_image_by_type(u.practice_photo, "Small", '', resize_type='img_size_logo'),
					'logo_middle': ImageHelper.get_image_by_type(u.practice_photo, "Middle", '', resize_type='img_size_logo'),
					}for u in orgs]
	else:
		return []

def getOrgMembers(org_id, hospital=None, strip_staff_mobile=True, strip_staff_pager=True, org__org_status=1):
#	ps = PracticeLocation.objects.filter(practice__pk=org_id, org__org_status=org__org_status).values_list('mhluser')
#	#providers = MHLUser.objects.filter(pk__in=providers)

	tree_id = get_all_related_org_ids_below_this_org(org_id)

	q_p = Q(practices__id__in=tree_id["all_tree_ids"])
	q_s = Q(practices__id__in=tree_id["all_tree_ids"])

	if hospital:
		q_p.add(Q(sites__name__icontains=hospital), Q.AND)
		q_s.add(Q(sites__name__icontains=hospital), Q.AND)

	providers = list(Provider.active_objects.filter(q_p).distinct())
	staffers = list(OfficeStaff.active_objects.filter(q_s).distinct())
	# Notes: following logic is similar with all_practice_members in MHLUsers.utils.py 
	# when refine code following logic should be moved to set_org_members_result or set_practice_members_result
	if (strip_staff_mobile or strip_staff_pager):
		members = []
		for user in staffers:
			if not Office_Manager.objects.filter(user=user).exists():
				if strip_staff_mobile:
					user.user.mobile_phone = None
				if strip_staff_pager:
					user.pager = None
			members.append(user)
		providers.extend(members)
	else:
		providers.extend(staffers)
	return providers

def renderOrganizationForDashbord(orgs, request):
	ret_dic = []
	if orgs and len(orgs)>0:
		for org in orgs:
			members = getOrgMembers(org['id'], None, False, False)
			providers = set_org_members_result(members, request)
			for p in providers:
				if isinstance(p, Provider):
					p.template_specialty = get_specialty_display_by_provider(p)
				else:
					p.template_specialty = ""
			providers_for_userInfo3 = {'providers':providers}
			ret_dic.append({
					'id':org['id'],
					'context':render_to_string('userInfo3.html', providers_for_userInfo3)
				})
	return ret_dic
