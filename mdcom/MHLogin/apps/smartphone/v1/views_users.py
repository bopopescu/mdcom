import json

from django.conf import settings
from django.db.models import Q
from django.forms.models import model_to_dict
from django.http import HttpResponse, HttpResponseBadRequest
from django.utils.translation import ugettext as _

from MHLogin.MHLUsers.models import OfficeStaff, Provider, MHLUser, Physician, \
	Office_Manager, Nurse, NP_PA
from MHLogin.MHLUsers.utils import get_all_site_providers, get_all_site_staff, \
	get_all_practice_providers, get_all_practice_staff, get_community_providers, \
	get_community_professionals, get_all_site_clinical_clerks, search_mhluser, \
	generate_name_query,get_fullname
from MHLogin.apps.smartphone.v1.utils_users import _set_providers_list, _set_staff_list
from MHLogin.apps.smartphone.v1.forms_users import UserSearchForm, UserPhotoForm
from MHLogin.apps.smartphone.v1.decorators import AppAuthentication
from MHLogin.apps.smartphone.v1.errlib import err_GE002, err_GE031, err_DM020
from MHLogin.utils.ImageHelper import get_image_by_type, generate_image
from MHLogin.utils.constants import USER_TYPE_OFFICE_MANAGER, USER_TYPE_DOCTOR,\
	USER_TYPE_OFFICE_STAFF, RESERVED_ORGANIZATION_TYPE_ID_PRACTICE
from MHLogin.MHLOrganization.utils import get_other_organizations,\
	get_custom_logos, get_prefer_logo
from MHLogin.MHLFavorite.utils import is_favorite, OBJECT_TYPE_FLAG_MHLUSER,\
	get_my_favorite_ids


@AppAuthentication
def site_providers(request, return_python=False):
	"""
	Gets a list of the providers at the user's current site.

	If return_python is true, this will just return the object that would have
	been converted to JSON format.
	"""
	p = request.role_user
	location = p.current_site

	response = {
		'data': {'users': []},
		'warnings': {},
	}

	if (not location):
		return HttpResponse(content=json.dumps(response), mimetype='application/json')

	providers = get_all_site_providers(location)

	response['data']['users'] = _set_providers_list(providers, p)

	if (return_python):
		return response

	return HttpResponse(content=json.dumps(response), mimetype='application/json')


@AppAuthentication
def site_students(request, return_python=False):
	"""
	Gets a list of the clinical clerks/med students at the user's current site.

	If return_python is true, this will just return the object that would have
	been converted to JSON format.
	"""
	p = request.role_user
	user_type = int(request.user_type)
	if not USER_TYPE_DOCTOR == user_type:
		return err_DM020()
	location = p.current_site

	response = {
		'data': {'users': []},
		'warnings': {},
	}

	if (not location):
		return HttpResponse(content=json.dumps(response), mimetype='application/json')

	providers = get_all_site_clinical_clerks(location)
	response['data']['users'] = _set_providers_list(providers, p, has_specialty=False)

	if (return_python):
		return response

	return HttpResponse(content=json.dumps(response), mimetype='application/json')


@AppAuthentication
def site_staff(request, return_python=False):
	"""
	Gets a list of the staff at the user's current site.

	If return_python is true, this will just return the object that would have
	been converted to JSON format.
	"""
	p = request.role_user

	location = p.current_site

	response = {
		'data': {'users': []},
		'warnings': {},
	}

	if (not location):
		return HttpResponse(content=json.dumps(response), mimetype='application/json')

	staff = get_all_site_staff(location)
	response['data']['users'] = _set_staff_list(staff, p)

	if (return_python):
		return response

	return HttpResponse(content=json.dumps(response), mimetype='application/json')


@AppAuthentication
def practice_providers(request, return_python=False):
	"""
	Gets a list of the providers at the user's current practice.

	If return_python is true, this will just return the object that would have
	been converted to JSON format.
	"""
	p = request.role_user

	location = p.current_practice

	response = {
		'data': {'users': []},
		'warnings': {},
	}

	if (not location):
		return HttpResponse(content=json.dumps(response), mimetype='application/json')

	providers = get_all_practice_providers(location, False)

	response['data']['users'] = _set_providers_list(providers, p)

	if (return_python):
		return response
	return HttpResponse(content=json.dumps(response), mimetype='application/json')


@AppAuthentication
def practice_staff(request, return_python=False):
	"""
	Gets a list of the staff at the user's current practice.

	If return_python is true, this will just return the object that would have
	been converted to JSON format.
	"""
	p = request.role_user
	location = p.current_practice

	response = {
		'data': {'users': []},
		'warnings': {},
	}

	if (not location):
		return HttpResponse(content=json.dumps(response), mimetype='application/json')

	staff = get_all_practice_staff(location)

	response['data']['users'] = _set_staff_list(staff, p)

	if (return_python):
		return response
	return HttpResponse(content=json.dumps(response), mimetype='application/json')


@AppAuthentication
def community_providers(request):
	p = request.role_user
	user_type = int(request.user_type)

	providers = []
	if USER_TYPE_OFFICE_MANAGER == user_type:
		providers = get_community_professionals(p.current_practice)
	else:
		providers = get_community_providers(p)

	response = {
		'data': {'users': []},
		'warnings': {},
	}
	response['data']['users'] = _set_providers_list(providers, p)

	return HttpResponse(content=json.dumps(response), mimetype='application/json')


@AppAuthentication
def user_info(request, user_id):
	current_user = request.role_user
	current_user_mobile = current_user.user.mobile_phone
	try:
		mhluser = MHLUser.objects.get(pk=user_id)
	except MHLUser.DoesNotExist:
		err_obj = {
			'errno': 'PF001',
			'descr': _('User not found.'),
		}
		return HttpResponseBadRequest(content=json.dumps(err_obj), mimetype='application/json')

	response = {
		'data': {
				'first_name': mhluser.first_name,
				'last_name': mhluser.last_name,
				'specialty': _('N/A'),
				'mdcom_phone': '',
				# In order to avoid modifying client's code, don't change the key.
				'office_address1': mhluser.address1,
				'office_address2': mhluser.address2,
				'office_city': mhluser.city,
				'office_state': mhluser.state,
				'office_zip': mhluser.zip,
				'accepting_patients': False,
				'photo': ''.join([settings.MEDIA_URL, 'images/photos/generic_128.png']),
				'current_practice': {},
				'skill': mhluser.skill,
				'has_mobile': False,
				'has_pager': False,
				'custom_logos': [],
				'is_favorite': is_favorite(request.user, OBJECT_TYPE_FLAG_MHLUSER, user_id),
				'fullname':get_fullname(mhluser)
			},
		'warnings': {},
		}
	data = response['data']
	current_practice = None
	try:
		p = Provider.objects.get(user=mhluser)
	except Provider.DoesNotExist:
		p = None
	if (p):
#		data['office_address1'] = p.office_address1
#		data['office_address2'] = p.office_address2
#		data['office_city'] = p.office_city
#		data['office_state'] = p.office_state
#		data['office_zip'] = p.office_zip
		data['mdcom_phone'] = p.mdcom_phone
		data['photo'] = get_image_by_type(mhluser.photo, "Middle", "Provider")
		data['user_photo_m'] = get_image_by_type(mhluser.photo, "Middle", "Provider")
		data['current_practice'] = get_current_practice_for_user(
			p.current_practice, current_user, USER_TYPE_DOCTOR)

		data['has_mobile'] = bool(mhluser.mobile_phone) and \
			bool(current_user_mobile) and settings.CALL_ENABLE
		data['has_pager'] = bool(p.pager) and settings.CALL_ENABLE
		current_practice = p.current_practice

		phys = Physician.objects.filter(user=p)
		if (phys.exists()):
			phys = phys.get()

			if phys.user.clinical_clerk:
				data['specialty'] = ''
			elif phys.specialty:
				data['specialty'] = phys.get_specialty_display()
			data['accepting_patients'] = phys.accepting_new_patients

		nppas = NP_PA.active_objects.filter(user=p)
		if (nppas.exists()):
			data['specialty'] = 'NP/PA/Midwife'

	try:
		ostaff = OfficeStaff.objects.get(user=mhluser)
#		data['office_address1'] = ostaff.office_address1
#		data['office_address2'] = ostaff.office_address2
#		data['office_city'] = ostaff.office_city
#		data['office_state'] = ostaff.office_state
#		data['office_zip'] = ostaff.office_zip
		data['photo'] = get_image_by_type(mhluser.photo, "Middle", "Staff")
		data['user_photo_m'] = get_image_by_type(mhluser.photo, "Middle", "Staff")
		data['specialty'] = "Office Staff"
		data['current_practice'] = get_current_practice_for_user(ostaff.current_practice, 
									current_user, USER_TYPE_OFFICE_STAFF)
		if ostaff.current_practice:
			data['mdcom_phone'] = ostaff.current_practice.mdcom_phone

		try:
			Nurse.objects.get(user=ostaff)
			data['photo'] = get_image_by_type(mhluser.photo, "Middle", "Nurse")
			data['user_photo_m'] = get_image_by_type(mhluser.photo, "Middle", "Nurse")
		except Nurse.DoesNotExist:
			pass

	except OfficeStaff.DoesNotExist:
		ostaff = None

	if (ostaff):
		current_practice = ostaff.current_practice
		if Office_Manager.objects.filter(user=ostaff).exists():
			data['photo'] = get_image_by_type(mhluser.photo, "Middle", "Staff")
			data['user_photo_m'] = get_image_by_type(mhluser.photo, "Middle", "Staff")
			data['specialty'] = "Office Manager"
			data['has_mobile'] = bool(mhluser.mobile_phone) and \
				bool(current_user_mobile) and settings.CALL_ENABLE
			data['has_pager'] = bool(ostaff.pager) and settings.CALL_ENABLE

	data['other_orgs'] = get_other_organizations(user_id)
	data['custom_logos'] = get_custom_logos(user_id, current_practice=current_practice)
	return HttpResponse(content=json.dumps(response), mimetype='application/json')


def get_current_practice_for_user(target_practice, current_user, type):
	"""
		Get target_user's current practice information.

		:param target_practice: which practice you want to show it's information.
			target_practice is an instance of PracticeLocation
		:parm current_user: current login user
			current_user is an instance of OfficeStaff/Provider
		:param type: the user type of the user you want to show
		:returns: dict
	"""

	if current_user is None:
		raise ValueError

	if not target_practice:
		return ""

	if type is None:
		type = 0
	type = int(type)

	practice = ''
	if not target_practice.organization_type:
		target_practice = None
	elif not RESERVED_ORGANIZATION_TYPE_ID_PRACTICE == target_practice.organization_type.id\
			and USER_TYPE_DOCTOR == type:
		target_practice = None

	if target_practice:
		practice = model_to_dict(target_practice,
								fields=('id', 
									'practice_name', 
									'practice_address1', 
									'practice_address2', 
									'practice_city', 
									'practice_state',
									'practice_zip'))
		practice['practice_photo'] = get_image_by_type(
				target_practice.practice_photo, "Large", "Practice")
		practice['practice_photo_m'] = get_image_by_type(
				target_practice.practice_photo, "Middle", "Practice")

		current_user_mobile = current_user.user.mobile_phone
		practice['call_available'] = (bool(target_practice.backline_phone)\
									or bool(target_practice.practice_phone))\
									and bool(current_user_mobile)\
									and settings.CALL_ENABLE
		has_manager = Office_Manager.active_objects.filter(practice=target_practice).exists()
		practice['msg_available'] = has_manager
		practice['org_type_id'] = target_practice.organization_type.id
	return practice


@AppAuthentication
def user_search(request):
	""" Query MHLUser by name (first and/or last) returning Providers and Staff """
	if (request.method != 'POST'):
		return err_GE002()
	form = UserSearchForm(request.POST)
	if (not form.is_valid()):
		return err_GE031(form)

	curr_mobile = request.role_user.user.mobile_phone
	object_ids = get_my_favorite_ids(request.user, OBJECT_TYPE_FLAG_MHLUSER)

	limit = form.cleaned_data['limit'] if 'limit' in form.cleaned_data else None
	qry = generate_name_query(form.cleaned_data['name'])
	user_qry = search_mhluser(qry, limit=limit)
	response = {'data': {'count': 0, 'results': []}, 'warnings': {}}

	provs = Provider.objects.filter(user__in=user_qry)
	staffs = OfficeStaff.objects.filter(user__in=user_qry)
	phys = Physician.objects.filter(user__in=provs)
	provs = {prov.user_id: prov for prov in provs}
	staffs = {staf.user_id: staf for staf in staffs}
	phys = {phy.user_id: phy for phy in phys}
	for user in user_qry:
		prov = provs[user.id] if user.id in provs else None
		staf = staffs[user.id] if user.id in staffs else None
		if not (staf or prov):
			continue  # only include staff/providers
		phy = phys[prov.id] if prov and prov.id in phys else None
		pract = (prov and prov.current_practice) or (staf and staf.current_practice)
		pphoto = pract and pract.practice_photo
		response['data']['results'].append({
			'id': user.id,
			'first_name': user.first_name,
			'last_name': user.last_name,
			'has_mobile': True if user.mobile_phone and curr_mobile else False,
			'has_pager': True if (prov and prov.pager) or (staf and staf.pager) else False,
			'thumbnail': get_image_by_type(user.photo, "Small", "Provider"),
			'user_photo_m': get_image_by_type(user.photo, "Middle", "Provider"),
			'practice_photo': get_image_by_type(pphoto, "Large", "Practice"), 
			'prefer_logo': get_prefer_logo(user.id, pract) if pract else '',
			'is_favorite': user.id in object_ids,
			'specialty': phy.get_specialty_display() if phy else '',
			'fullname':get_fullname(user)
		})
		response['data']['count'] += 1

	return HttpResponse(content=json.dumps(response), mimetype='application/json')


@AppAuthentication
def get_all_providers_and_staffs(request):
	if (request.method != 'POST'):
		return err_GE002()
	response = {
		'users': {}
	}

	practice = None
	try:
		practice = Provider.objects.get(pk=request.user).current_practice
	except:
		try:
			practice = OfficeStaff.objects.get(pk=request.user).current_practice
		except:
			pass

	q_1 = Q()
	q_2 = Q()
	if 'name' in request.POST:
		search_terms = unicode.split(request.POST['name'])
		if search_terms:
			if len(search_terms) == 1:
				first_name = search_terms[0]
				last_name2 = ''
			else:
				first_name = search_terms[0]
				last_name = search_terms[1:]
				last_name2 = ' '.join(last_name)

			if last_name2:
				q_2 = Q(user__first_name__icontains=first_name) \
					& Q(user__last_name__icontains=last_name2) \
					| Q(user__first_name__icontains=last_name2) \
					& Q(user__last_name__icontains=first_name)
				q_1 = Q(user__user__first_name__icontains=first_name) \
					& Q(user__user__last_name__icontains=last_name2) \
					| Q(user__user__first_name__icontains=last_name2) \
					& Q(user__user__last_name__icontains=first_name)
			else:
				q_2 = Q(user__first_name__icontains=first_name) \
					| Q(user__last_name__icontains=first_name)
				q_1 = Q(user__user__first_name__icontains=first_name) \
					| Q(user__user__last_name__icontains=first_name)

	np_pas = NP_PA.active_objects.filter(q_1).\
		select_related('user', 'user__user', 'user__user__user')
	physicians = Physician.active_objects.filter(q_1).\
		select_related('user', 'user__user', 'user__user__user')
	office_managers = Office_Manager.active_objects.\
		filter(q_1).select_related('user', 'user__user')
	office_staffs = OfficeStaff.active_objects.filter(q_2).\
		filter(practices=practice).select_related('user', 'user__user')

	return_set = []
	for phy in physicians:
		u = phy.user
		user_info = {
					'id': u.user.id,
					'first_name': u.user.first_name,
					'last_name': u.user.last_name,
					'user_type': 'Physican',
					'office_address': ' '.join([u.user.address1,
						u.user.address2, u.user.city, u.user.state, u.user.zip]),
					'specialty': _('N/A'),
					'fullname':get_fullname(u.user)
				}
		if ('specialty' in dir(phy) and phy.specialty):
			user_info['specialty'] = phy.get_specialty_display()
		if u.clinical_clerk:
			user_info['specialty'] = ''
			user_info['user_type'] = 'Medical Student'
		return_set.append(user_info)

	for np_pa in np_pas:
		u = np_pa.user
		user_info = {
					'id': u.user.id,
					'first_name': u.user.first_name,
					'last_name': u.user.last_name,
					'user_type': 'NP/PA/Midwife',
					'office_address': ' '.join([u.user.address1,
						u.user.address2, u.user.city, u.user.state, u.user.zip]),
					'specialty': 'NP/PA/Midwife',
					'fullname':get_fullname(u.user)
				}
		return_set.append(user_info)

	for staff in office_staffs:
		user_info = {
			'id': staff.user.id,
			'first_name': staff.user.first_name,
			'last_name': staff.user.last_name,
			'user_type': 'Staff',
			'office_address': ' '.join([staff.user.address1,
				staff.user.address2, staff.user.city, staff.user.state, staff.user.zip]),
			'specialty': 'N/A',
			'fullname':get_fullname(staff)
		}
		if office_managers.filter(user=staff).exists():
			user_info['user_type'] = 'Manager'
		return_set.append(user_info)

	response['users'] = sorted_uses(return_set)

	return HttpResponse(json.dumps(response))


@AppAuthentication
def user_update_photo(request):
	if (request.method != 'POST'):
		return err_GE002()
	try:
		mhluser = request.user
	except MHLUser.DoesNotExist:
		err_obj = {
			'errno': 'PF001',
			'descr': _('User not found.'),
		}
		return HttpResponseBadRequest(content=json.dumps(err_obj), mimetype='application/json')

	old_url = None
	if mhluser.photo:
		old_url = request.user.photo.name
	form = UserPhotoForm(request.POST, request.FILES, instance=mhluser)
	user = form.save(commit=False)
	user.save()
	new_url = None
	if user.photo:
		new_url = user.photo.name
	if old_url != new_url:
		generate_image(old_url, new_url)

	user_type = int(request.user_type)
	if user_type in [USER_TYPE_OFFICE_MANAGER, USER_TYPE_OFFICE_STAFF]:
		nurse = Nurse.objects.filter(user__user=mhluser)
		if nurse:
			photo = get_image_by_type(mhluser.photo, "Middle", type="Nurse")
		else:
			photo = get_image_by_type(mhluser.photo, "Middle", type="Staff")
	else:
		photo = get_image_by_type(mhluser.photo, "Middle")

	if photo:
		response = {
			'photo': photo,
			'warnings': {},
		}
		return HttpResponse(content=json.dumps(response), mimetype='application/json')
	else:
		err_obj = {
			'errno': 'PF002',
			'descr': _('Update user photo failed.'),
		}
		return HttpResponse(content=json.dumps(err_obj), mimetype='application/json')

#def _get_first(physicians, np_pas, managers, staff):
#	"""
#	Temporary workaround function to pop off and automatically return the user who 
#	comes first alphabetically.
#	
#	Note that if all of the lists of users have length 0, this function will choke.
#	"""
#	
#	phys = None
#	phys_user = None
#	if (physicians):
#		phys = physicians[0]
#		phys_user = phys.user
#	np_pa = None
#	np_pa_user = None
#	if (np_pas):
#		np_pa = np_pas[0]
#		np_pa_user = np_pa.user
#	mgr = None
#	mgr_user = None
#	if (managers):
#		mgr = managers[0]
#		mgr_user = mgr.user
#	staffer = None
#	if (staff):
#		staffer = staff[0]
#
#	prov_winner = None # keep track of the user who "wins"
#	compare = _compare_users(phys_user, np_pa_user)
#	if (compare < 0):
#		prov_winner = np_pa
#		phys = None
#	else:
#		prov_winner = phys
#		np_pa = None # prefer NP/PAs in a tie
#
#	off_winner = None # keep track of the user who "wins"
#	compare = _compare_users(mgr_user, staffer)
#	if (compare < 0):
#		off_winner = staffer
#		mgr = None
#	else:
#		off_winner = mgr
#		staffer = None # prefer Managers in a tie
#	
#	prov_user = None
#	if (prov_winner):
#		prov_user = prov_winner.user
#	off_user = None
#	if (off_winner):
#		off_user = off_winner
#		if (off_winner.__class__.__name__ == 'Office_Manager'):
#			off_user = off_user.user
#	compare = _compare_users(prov_user, off_user)
#	if (compare < 0):
#		if (off_winner.__class__.__name__ == 'Office_Manager'):
#			return managers.pop(0)
#		return staff.pop(0)
#	else:
#		if (prov_winner.__class__.__name__ == 'Physician'):
#			return physicians.pop(0)
#		return np_pas.pop(0)
#
#def _compare_users(u1, u2):
#	"""
#	Compares two users by first_name and last_name. Returns 1 
#		if u1 < u2, -1 if u1 > u2, and 0 if u1 == u2.
#	
#	In other words, if u1 should come first, then 1 is returned. 
#		If u2 should  come first, then -1 is returned. 0 in the event of a tie.
#	"""
#	if (not u1 and not u2):
#		return 0
#	if (not u1):
#		return -1
#	if (not u2):
#		return 1
#	
#	if (u1.user.last_name < u2.user.last_name):
#		return 1
#	if (u1.user.last_name > u2.user.last_name):
#		return -1
#	
#	if (u1.user.first_name < u2.user.first_name):
#		return 1
#	if (u1.user.first_name > u2.user.first_name):
#		return -1
#	
#	return 0


def sorted_uses(user_list):
	return sorted(user_list, key=lambda item: "%s%s" % 
		(item['last_name'].lower(), item['first_name'].lower()))
