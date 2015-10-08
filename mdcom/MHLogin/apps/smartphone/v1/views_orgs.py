# -*- coding: utf-8 -*-
'''
Created on 2012-11-30

@author: mwang
'''
import json

from django.http import HttpResponse
from django.utils.translation import ugettext as _

from MHLogin.apps.smartphone.v1.decorators import AppAuthentication
from MHLogin.apps.smartphone.v1.utils_users import _set_org_members_list
from MHLogin.MHLOrganization.utils import which_orgs_contain_this_user
from MHLogin.utils import ImageHelper
from MHLogin.MHLOrganization.utils_org_tab import getOrganizationsOfUser, getOrgMembers
from MHLogin.apps.smartphone.v1.errlib import err_GE002, err_GE031
from MHLogin.apps.smartphone.v1.forms_users import UserTabForm
from django.core.urlresolvers import reverse


@AppAuthentication
def getMyOrgs(request):
	role_user = request.role_user
	response = {
		'data': {
				'organizations': getOrganizationsOfUser(
					request.user, current_practice=role_user.current_practice),
			},
		'warnings': {},
	}
	return HttpResponse(content=json.dumps(response), mimetype='application/json')


@AppAuthentication
def getOrgUsers(request, org_id):
	members = getOrgMembers(org_id)
	response = {
		'data': {
				'users': _set_org_members_list(members, request.role_user)
			},
		'warnings': {},
	}
	return HttpResponse(content=json.dumps(response), mimetype='application/json')


@AppAuthentication
def getUserTabs(request):
	if (request.method != 'POST'):
		return err_GE002()

	form = UserTabForm(request.POST)
	if (not form.is_valid()):
		return err_GE031(form)

	role_user = request.role_user
	current_practice = role_user.current_practice
	mhluser = request.user
	is_only_user_tab = False
	if "is_only_user_tab" in form.cleaned_data:
		is_only_user_tab = form.cleaned_data['is_only_user_tab']

	show_my_favorite = False
	if "show_my_favorite" in form.cleaned_data:
		show_my_favorite = form.cleaned_data["show_my_favorite"]

	current_practice_id = None
	if current_practice is None:
		type_name = ""
	else:
		type_name = current_practice.organization_type.name
		current_practice_id = current_practice.id
	userTab = [{
				'tab_name':_('Site Providers'),
				'tab_type':'1',
				'logo': '',
				'logo_middle': '',
				'logo_large': '',
				'org_id':'',
				'url': reverse('MHLogin.apps.smartphone.v1.views_users.site_providers')
			}, {
				'tab_name':_('Site Staff'),
				'tab_type':'2',
				'logo': '',
				'logo_middle': '',
				'logo_large': '',
				'org_id':'',
				'url': reverse('MHLogin.apps.smartphone.v1.views_users.site_staff')
			}, {
				'tab_name': _('%s Provider') % (type_name),
				'tab_type':'3',
				'logo': '',
				'logo_middle': '',
				'logo_large': '',
				'org_id':'',
				'url': reverse('MHLogin.apps.smartphone.v1.views_users.practice_providers')
			}, {
				'tab_name':_('%s Staff') % (type_name),
				'tab_type':'4',
				'logo': '',
				'logo_middle': '',
				'logo_large': '',
				'org_id':'',
				'url': reverse('MHLogin.apps.smartphone.v1.views_users.practice_staff')
			}, {
				'tab_name':_('Community Providers'),
				'tab_type':'5',
				'logo': '',
				'logo_middle': '',
				'logo_large': '',
				'org_id':'',
				'url': reverse('MHLogin.apps.smartphone.v1.views_users.community_providers')
			}]

	if not is_only_user_tab:
		userTab.append({
				'tab_name': _('Local Practices'),
				'tab_type': '6',
				'logo': '',
				'logo_middle': '',
				'logo_large': '',
				'org_id': '',
				'url': reverse('MHLogin.apps.smartphone.v1.views_practices.local_office')
			})

	orgs = which_orgs_contain_this_user(mhluser.id, exclude_org_ids=current_practice_id)
	if orgs and len(orgs):
		for org in orgs:
			userTab.append({
						'tab_name': org.practice_name,
						'tab_type': '7',
						'logo': ImageHelper.get_image_by_type(
							org.practice_photo, "Small", '', resize_type='img_size_logo'),
						'logo_middle': ImageHelper.get_image_by_type(
							org.practice_photo, "Middle", '', resize_type='img_size_logo'),
						'logo_large': ImageHelper.get_image_by_type(
							org.practice_photo, "Large", '', resize_type='img_size_logo'),
						'org_id': org.pk,
						'url': reverse('MHLogin.apps.smartphone.v1.views_orgs.getOrgUsers', 
							kwargs={'org_id': org.pk})
					})

	if show_my_favorite:
		userTab.append({
				'tab_name': _('My Favorites'),
				'tab_type': '8',
				'logo': '',
				'logo_middle': '',
				'logo_large': '',
				'org_id': '',
				'url': reverse('MHLogin.apps.smartphone.v1.views_my_favorite.my_favorite')
			})

	response = {
		'data': userTab,
		'warnings': {},
	}

	return HttpResponse(content=json.dumps(response), mimetype='application/json')

