# -*- coding: utf-8 -*-
'''
Created on 2012-9-26

@author: mwang
'''

from django.conf import settings
from django.db.models import Q
from django.forms.models import model_to_dict
from django.http import Http404

from MHLogin.MHLUsers.models import MHLUser, Nurse, Provider, OfficeStaff, Physician, NP_PA, Office_Manager
from MHLogin.utils import ImageHelper
from MHLogin.utils.geocode import geocode2, miles2latlong_range
from MHLogin.MHLOrganization.utils import get_custom_logos

def getProviderList(condition_dict, current_user=None, exclude_clerk=True):
	q_condition = Q()
	limit = None
	if condition_dict:
		if 'name' in condition_dict and condition_dict['name']:
			name = condition_dict['name']
			search_terms = unicode.split(name)
			if len(search_terms) == 1:
				first_name = search_terms[0]
				last_name2 = ''
			else:
				first_name = search_terms[0]
				last_name = search_terms[1:]
				last_name2 = ' '.join(last_name)
			if last_name2:
				q_condition.add(Q(Q(user__first_name__icontains=first_name) & Q(user__last_name__icontains=last_name2) | Q(user__first_name__icontains=last_name2) & Q(user__last_name__icontains=first_name)), Q.AND)
			else:
				q_condition.add(Q(Q(user__first_name__icontains=first_name) | Q(user__last_name__icontains=first_name)), Q.AND)

		if 'address' in condition_dict and condition_dict['address']:
			address = condition_dict['address']
			q_condition.add(Q(Q(user__address1__icontains=address) | Q(user__address2__icontains=address)), Q.AND)

		if 'city' in condition_dict and condition_dict['city']:
			city = condition_dict['city']
			q_condition.add(Q(user__city__icontains=city), Q.AND)

		if 'state' in condition_dict and condition_dict['state']:
			state = condition_dict['state']
			q_condition.add(Q(user__state=state), Q.AND)

		if 'zip' in condition_dict and condition_dict['zip']:
			zip = condition_dict['zip']
			result = geocode2('', '', '', zip)
			if (result['lat'] != 0.0 and result['lng'] != 0.0):
				lat = result['lat'] 
				longit = result['lng']
				distance = settings.PROXIMITY_RANGE
				if 'distance' in condition_dict and condition_dict['distance']:
					distance = condition_dict['distance']
				latmin, latmax, longitmin, longitmax = miles2latlong_range(lat, longit, distance)
				q_condition.add(Q(user__lat__range=(latmin, latmax), user__longit__range=(longitmin, longitmax)), Q.AND)

		if 'current_hospital' in condition_dict and condition_dict['current_hospital']:
			current_hospital = condition_dict['current_hospital']
			q_condition.add(Q(current_site__name__icontains=current_hospital), Q.AND)

		if 'hospital' in condition_dict and condition_dict['hospital']:
			hospital = condition_dict['hospital']
			q_condition.add(Q(sites__name__icontains=hospital), Q.AND)

		if 'current_practice' in condition_dict and condition_dict['current_practice']:
			current_practice = condition_dict['current_practice']
			q_condition.add(Q(current_practice__practice_name__icontains=current_practice), Q.AND)

		if 'practice' in condition_dict and condition_dict['practice']:
			practice = condition_dict['practice']
			q_condition.add(Q(practices__practice_name__icontains=practice), Q.AND)

		if 'specialty' in condition_dict and condition_dict['specialty']:
			specialty = condition_dict['specialty']
			provider_ids = None
			if specialty != "NP/PA/Midwife":
				provider_ids = Physician.objects.filter(specialty__icontains=specialty).values_list('user')
			else:
				physician_ids = Physician.objects.filter(Q(specialty=None) | Q(specialty='')).values_list('user')
				physician_ids = [pid[0] for pid in physician_ids]
				nppa_ids = NP_PA.objects.values_list('user')
				nppa_ids = [pid[0] for pid in nppa_ids]
				provider_ids = physician_ids + nppa_ids
			if provider_ids:
				q_condition.add(Q(pk__in=provider_ids), Q.AND)

		if 'limit' in condition_dict and condition_dict['limit']:
			limit = condition_dict['limit']

	query_rs = Provider.active_objects.filter(q_condition)
	if exclude_clerk:
		query_rs = query_rs.exclude(clinical_clerk='True')

	total_count = query_rs.count()
	if limit and query_rs.count() > limit:
		query_rs = query_rs[:limit]

	data = {}
	data['total_count'] = total_count
	data['results'] = setProviderResultList(query_rs, current_user)
	return data

def getStaffList(condition_dict, current_user=None):
	q_condition = Q()
	limit = None
	if condition_dict:
		if 'name' in condition_dict and condition_dict['name']:
			name = condition_dict['name']
			search_terms = unicode.split(name)
			if len(search_terms) == 1:
				first_name = search_terms[0]
				last_name2 = ''
			else:
				first_name = search_terms[0]
				last_name = search_terms[1:]
				last_name2 = ' '.join(last_name)
			if last_name2:
				q_condition.add(Q(Q(user__first_name__icontains=first_name) & Q(user__last_name__icontains=last_name2) | Q(user__first_name__icontains=last_name2) & Q(user__last_name__icontains=first_name)), Q.AND)
			else:
				q_condition.add(Q(Q(user__first_name__icontains=first_name) | Q(user__last_name__icontains=first_name)), Q.AND)

		if 'address' in condition_dict and condition_dict['address']:
			address = condition_dict['address']
			q_condition.add(Q(Q(user__address1__icontains=address) | Q(user__address2__icontains=address)), Q.AND)

		if 'city' in condition_dict and condition_dict['city']:
			city = condition_dict['city']
			q_condition.add(Q(user__city__icontains=city), Q.AND)

		if 'state' in condition_dict and condition_dict['state']:
			state = condition_dict['state']
			q_condition.add(Q(user__state=state), Q.AND)

		if 'zip' in condition_dict and condition_dict['zip']:
			zip = condition_dict['zip']
			q_condition.add(Q(user__zip=zip), Q.AND)

		if 'current_hospital' in condition_dict and condition_dict['current_hospital']:
			current_hospital = condition_dict['current_hospital']
			q_condition.add(Q(current_site__name__icontains=current_hospital), Q.AND)

		if 'hospital' in condition_dict and condition_dict['hospital']:
			hospital = condition_dict['hospital']
			q_condition.add(Q(sites__name__icontains=hospital), Q.AND)

		if 'current_practice' in condition_dict and condition_dict['current_practice']:
			current_practice = condition_dict['current_practice']
			q_condition.add(Q(current_practice__practice_name__icontains=current_practice), Q.AND)

		if 'practice' in condition_dict and condition_dict['practice']:
			practice = condition_dict['practice']
			q_condition.add(Q(practices__practice_name__icontains=practice), Q.AND)

		if 'limit' in condition_dict and condition_dict['limit']:
			limit = condition_dict['limit']

	query_rs = OfficeStaff.active_objects.filter(q_condition)

	total_count = query_rs.count()
	if limit and query_rs.count() > limit:
		query_rs = query_rs[:limit]

	data = {}
	data['total_count'] = total_count
	data['results'] = setOfficeStaffResultList(query_rs, current_user)
	return data

def setProviderResultList(providers, current_user=None):
	current_user_mobile = None
	if current_user:
		current_user_mobile = current_user.user.mobile_phone
	user_list = []

	provider_ids = [p.id for p in providers]

	physician_set = Physician.objects.filter(user__id__in=provider_ids)

	for p in providers:

		call_available = bool(p.user.mobile_phone) and bool(current_user_mobile) and settings.CALL_ENABLE
		pager_available = bool(p.pager) and settings.CALL_ENABLE
		photo = ImageHelper.get_image_by_type(p.user.photo, "Small", "Provider")

		current_practice = {}
		if p.current_practice:
			current_practice = model_to_dict(p.current_practice, fields=('id', 'practice_name'))

		current_site = {}
		if p.current_site:
			current_site = model_to_dict(p.current_site, fields=('id', 'name'))

		user_info = {
				'id': p.user.id,
				'first_name': p.user.first_name,
				'last_name': p.user.last_name,
				'current_practice': current_practice,
				'current_site': current_site,
#
				'specialty': '',
				'call_available': call_available,
				'pager_available': pager_available,
				# reserved
				'refer_available': True,
#				'msg_available': True,
				'photo': photo,

				# Following three keys's name is not very good. As compatibility reason, reserve them.
				# We use call_available, pager_available, photo replace has_mobile, has_pager, thumbnail
				'has_mobile': call_available,
				'has_pager': pager_available,
				'thumbnail': photo,
			}
		physician = physician_set.filter(user__id=p.id)
		if physician and 'specialty' in dir(physician[0]) and physician[0].specialty:
			user_info['specialty'] = physician[0].get_specialty_display()
		else:
			user_info['specialty'] = "NP/PA/Midwife"
		user_list.append(user_info)
	return user_list


def setSubProviderResultList(providers, current_user=None):
	current_user_mobile = None
	if current_user:
		current_user_mobile = current_user.user.mobile_phone
	user_list = []
	for p in providers:

		call_available = bool(p.user.user.mobile_phone) and bool(current_user_mobile) and settings.CALL_ENABLE
		pager_available = bool(p.user.pager) and settings.CALL_ENABLE
		photo = ImageHelper.get_image_by_type(p.user.user.photo, "Small", "Provider")

		user_info = {
				'id': p.user.user.id,
				'first_name': p.user.first_name,
				'last_name': p.user.last_name,
				'specialty': '',
				'call_available': call_available,
				'pager_available': pager_available,
				# reserved
				'refer_available': True,
#				'msg_available': True,
				'photo': photo,

				# Following three keys's name is not very good. As compatibility reason, reserve them.
				# We use call_available, pager_available, photo replace has_mobile, has_pager, thumbnail
				'has_mobile': call_available,
				'has_pager': pager_available,
				'thumbnail': photo,
			}
		if ('specialty' in dir(p) and p.specialty):
			user_info['specialty'] = p.get_specialty_display()
		else:
			user_info['specialty'] = "NP/PA/Midwife"
		user_list.append(user_info)
	return user_list

def setOfficeStaffResultList(staff, current_user=None, strip_staff_mobile=True, strip_staff_pager=True):
	"""
	Returns staff response data.
	
	pass strip_staff_mobile=True if you want all office staff users(exclude managers and above they) to come back without a mobile phone number defined. This is useful if you don't want the user to seem call-able.
	
	pass strip_staff_pager=True if you want all office staff users(exclude managers and above they) to come back without a pager number defined. This is useful if you don't want the user to seem call-able.
	"""
	current_user_mobile = None
	if current_user:
		current_user_mobile = current_user.user.mobile_phone

	user_list = []
	for s in staff:

		if (s.__class__.__name__ == 'Office_Manager'):
			call_available = bool(s.user.user.mobile_phone) and bool(current_user_mobile) and settings.CALL_ENABLE
			pager_available = bool(s.user.pager) and settings.CALL_ENABLE
			photo = ImageHelper.get_image_by_type(s.user.user.photo, "Small", "Staff")

			user_info = {
					'id': s.user.user.id,
					'first_name': s.user.user.first_name,
					'last_name': s.user.user.last_name,
					'staff_type': 'Office Manager',
					'call_available': call_available,
					'pager_available': pager_available,
					# reserved
					'refer_available': False,
	#				'msg_available': True,
					'photo': photo,

					# Following three keys's name is not very good. As compatibility reason, reserve them.
					# We use call_available, pager_available, photo replace has_mobile, has_pager, thumbnail
					'has_mobile': call_available,
					'has_pager': pager_available,
					'thumbnail': photo,
				}
		else:
			call_available = not strip_staff_mobile and bool(s.user.mobile_phone) and bool(current_user_mobile) and settings.CALL_ENABLE
			pager_available = not strip_staff_pager and bool(s.pager) and settings.CALL_ENABLE
			photo = ImageHelper.get_image_by_type(s.user.photo, "Small", "Staff")

			user_info = {
					'id': s.user.id,
					'first_name': s.user.first_name,
					'last_name': s.user.last_name,
					'staff_type': 'Office Staff',
					'call_available': call_available,
					'pager_available': pager_available,
					# reserved
					'refer_available': False,
	#				'msg_available': True,
					'photo': photo,

					# Following three keys's name is not very good. As compatibility reason, reserve them.
					# We use call_available, pager_available, photo replace has_mobile, has_pager, thumbnail
					'has_mobile': call_available,
					'has_pager': pager_available,
					'thumbnail': photo,
				}

			# TODO: Clean me up once we refactor the user classes.
			try:
				nurse = Nurse.objects.get(user=s)
				user_info['thumbnail'] = user_info['photo'] = ImageHelper.get_image_by_type(nurse.user.user.photo, "Small", "Nurse")
			except Nurse.DoesNotExist:
				pass
		user_list.append(user_info)
	return user_list

def getUserInfo(user_id, current_user=None):
	try:
		mhluser = MHLUser.objects.get(pk=user_id)
	except MHLUser.DoesNotExist:
		return Http404

	data = {
				'id': mhluser.id,
				'first_name': mhluser.first_name,
				'last_name': mhluser.last_name,
				'specialty': '',
				'staff_type': '',
				'mdcom_phone': '',
				'office_address1': mhluser.address1,
				'office_address2': mhluser.address2,
				'office_city': mhluser.city,
				'office_state': mhluser.state,
				'office_zip': mhluser.zip,
				'accepting_patients': False,
				'photo': ''.join([settings.MEDIA_URL, 'images/photos/generic_128.png']),
				'custom_logos': get_custom_logos(mhluser.id)
			}
	
	try:
		p = Provider.objects.get(user=mhluser)
	except Provider.DoesNotExist:
		p = None
	if (p):
		# In order to compatibility  
		data['mdcom_phone'] = p.mdcom_phone
		data['photo'] = ImageHelper.get_image_by_type(mhluser.photo, "Middle", "Provider")
		phys = Physician.objects.filter(user=p)
		if (phys.exists()):
			phys = phys.get()
			data['specialty'] = phys.get_specialty_display()
			data['accepting_patients'] = phys.accepting_new_patients
		else:
			data['specialty'] = 'NP/PA/Midwife'

	try:
		ostaff = OfficeStaff.objects.get(user=mhluser)
		data['photo'] = ImageHelper.get_image_by_type(mhluser.photo, "Middle", "Staff")
		data['staff_type'] = "Office Staff"
		if ostaff.current_practice:
			data['mdcom_phone'] = ostaff.current_practice.mdcom_phone

		try:
			nurse = Nurse.objects.get(user=ostaff)
			data['photo'] = ImageHelper.get_image_by_type(mhluser.photo, "Middle", "Nurse")
		except Nurse.DoesNotExist:
			pass

	except OfficeStaff.DoesNotExist:
		ostaff = None

	if (ostaff):
		try:
			omgr = Office_Manager.objects.get(user=ostaff)
			data['staff_type'] = "Office Manager"
		except Office_Manager.DoesNotExist:
			omgr = None
	
	return data
