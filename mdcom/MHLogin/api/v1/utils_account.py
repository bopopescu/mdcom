# -*- coding: utf-8 -*-
'''
Created on 2012-10-08

@author: mwang
'''

from django.forms.models import model_to_dict

from MHLogin.MHLUsers.forms import ProviderForm, PhysicianForm
from MHLogin.MHLUsers.models import Physician, Nurse
from MHLogin.utils import ImageHelper

def providerProfileView(role_user):
	mhluser = role_user.user
	mhluser_data = model_to_dict(mhluser, fields=('id', 'username', 'first_name', 'last_name', 'email', 'email_confirmed',
										'mobile_phone', 'mobile_confirmed', 'phone', 
										'address1', 'address2', 'city', 'state', 'zip'))
	role_user_data = model_to_dict(role_user, fields=('office_phone', 'pager', 'pager_confirmed', 'pager_extension', 'clinical_clerk'))

	ret_data = dict(mhluser_data.items()+role_user_data.items())
	ret_data["current_site"] = role_user.current_site.id
	ret_data["sites"] = list(role_user.sites.values('id', 'name', 'address1', 'address2', 'city', 'state', 'zip'))
	ret_data["current_practice"] = role_user.current_practice.id
	ret_data["practices"] = list(role_user.practices.values('id', 'practice_name', 'practice_address1', 'practice_address2',\
													 'practice_city', 'practice_state', 'practice_zip'))
	ret_data["licensure_states"] = list(role_user.licensure_states.values('id', 'state'))
	ret_data["photo"] = ImageHelper.get_image_by_type(mhluser.photo, "Middle", "Provider")
	phys = Physician.objects.filter(user=role_user)
	if (phys.exists()):
		phy = phys[0]
		ret_data['specialty'] = phy.get_specialty_display()
		ret_data['accepting_patients'] = phy.accepting_new_patients
	else:
		ret_data['specialty'] = 'NP/PA/Midwife'
	return ret_data

def officeStaffProfileView(role_user):
	mhluser = role_user.user
	mhluser_data = model_to_dict(mhluser, fields=('id', 'username', 'first_name', 'last_name', 'email', 'email_confirmed',
										'mobile_phone', 'mobile_confirmed', 'phone'))
	role_user_data = model_to_dict(role_user, fields=('office_phone', 'pager', 'pager_confirmed', 'pager_extension'))

	ret_data = dict(mhluser_data.items()+role_user_data.items())
	ret_data["photo"] = ImageHelper.get_image_by_type(mhluser.photo, "Middle", "Staff")
	nurses = Nurse.objects.filter(user=role_user)
	if (nurses.exists()):
		ret_data['photo'] = ImageHelper.get_image_by_type(mhluser.photo, "Middle", "Nurse")
	return ret_data

def brokerProfileView(role_user):
	mhluser = role_user.user
	mhluser_data = model_to_dict(mhluser, fields=('id', 'username', 'first_name', 'last_name', 'email', 'email_confirmed',
										'mobile_phone', 'mobile_confirmed', 'phone', 
										'address1', 'address2', 'city', 'state', 'zip'))
	role_user_data = model_to_dict(role_user, fields=('office_phone', 'pager', 'pager_confirmed', 'pager_extension'))

	ret_data = dict(mhluser_data.items()+role_user_data.items())
	ret_data["photo"] = ImageHelper.get_image_by_type(mhluser.photo, "Middle", "Broker")
	ret_data["licensure_states"] = list(role_user.licensure_states.values('id', 'state'))
	return ret_data
