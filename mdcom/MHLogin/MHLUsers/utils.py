
import urllib
import traceback

from django.conf import settings
from django.db.models import Q
from django.utils.translation import ugettext as _

from MHLogin.KMS.models import UserPrivateKey, CRED_WEBAPP
from MHLogin.KMS.utils import store_user_key, recrypt_keys
from MHLogin.MHLUsers.models import MHLUser, Provider, Physician, Nurse, NP_PA, \
	Patient, Broker, OfficeStaff, Office_Manager, Dietician, Administrator,User,\
	Salesperson

from MHLogin.apps.smartphone.models import SmartPhoneAssn

from MHLogin.utils.geocode import miles2latlong_range, geocode2
from MHLogin.utils.constants import USER_TYPE_OFFICE_STAFF, USER_TYPE_TECH_ADMIN,\
	USER_TYPE_NURSE, USER_TYPE_MEDICAL_STUDENT, USER_TYPE_DIETICIAN, USER_TYPE_NPPA,\
	USER_TYPE_OFFICE_MANAGER, USER_TYPE_DOCTOR,\
	RESERVED_ORGANIZATION_TYPE_ID_PRACTICE
from MHLogin.Administration.tech_admin.utils import is_techadmin


def get_provider_types(user):
	"""
	Warning: This function is now deprecated. Please use
	request.session['MHL_UserIDs'] and request.session['MHL_Users'] instead. For
	information on these, please see the wiki page for MHLUsers at:

	https://private.myhealthincorporated.com/projects/mdcom/wiki/MHLUsers
	"""
	print _('This function (get_provider_types) is now deprecated. '
		'Please see the docstring for information.')
	traceback.print_stack()
	provider_types = []
	temp = [user_is_physician(user), user_is_nurse(user)]
	for i in temp:
		if i:
			provider_types.append(i)
	return provider_types


def user_is_active(user):
	"""
	Validate the login user is active or not.
	The parameter 'user' is an instance of User.
	If the user's field is_active is false, return "False";
	If the user login as Office staff(include Staff, Manager, Nurse and Dietician), but 
	not as Physician or NP_PA. and the staff's current practice is none, return "False";
	Others return "True".
	"""
	active = user.is_active
	try:
		staff = OfficeStaff.objects.get(user__pk=user.id)
		# Following, process special case: user is a staff, also is a provider.
		# return staff_is_active(staff, user)
		if staff.current_practice == None:
			try:
				Physician.objects.get(user__user__pk=user.id)
				return active
			except Physician.DoesNotExist:
				try:
					NP_PA.objects.get(user__user__pk=user.id)
					return active
				except NP_PA.DoesNotExist:
					return False
		else: 
			return active

	except OfficeStaff.DoesNotExist:
		return active


def staff_is_active(staff, user=None):
	"""
	Check the login staff is active or not; is used for staff login check.

	.. code-block python:: 

		if user is active, and:
			if staff's current practice is not None, then the staff is active,
				is a practice staff.
			if staff is pending for practice, is deemed active.
			if staff is also a provider, is deemed active. This is special case.
			else:
				is invalid
		else:
			is inactive

	:param staff: is an instance of OfficeStaff.
	:param user: is an instance of User.
	"""
	if not user:
		# Note: MHLUser is a subclass of User
		# TODO: If the relationship between MHLUser and User is changed, 
		# modify the following line. 
		user = staff.user

	is_active = user.is_active
	valid = False
	# if staff has current practice, then he is active
	if staff.current_practice:
		valid = True

	# Following, process special case: user is a staff, also is a provider.
	elif (Provider.objects.filter(user__pk=user.id).exists() \
				and (Physician.objects.get(user__user__pk=user.id).exists() \
				or NP_PA.objects.get(user__user__pk=user.id).exists())):
		valid = True

	return is_active and valid


def user_is_patient(user):
	"""
	Note: If checking if a user is a Patient from a request object, eg from 
	request.user it is better to do this:
	.. code-block:: python

		'Patient' in request.session['MHL_Users']

	If checking another user's type from our db for ex. use this function. 
	"""
	q = Patient.objects.filter(user=user)
	if (len(q) != 1):
		return False
	return True


def user_is_physician(user):
	"""
	Note: If checking if a user is a Physician from a request object, eg from 
	request.user it is better to do this:
	.. code-block:: python

		'Physician' in request.session['MHL_Users']

	If checking another user's type from our db for ex. use this function. 
	"""
	q = Physician.objects.filter(user=user)
	if (q.count() != 1):
		return False
	return q[0]


def user_is_nurse(user):
	"""
	Note: If checking if a user is a Nurse from a request object, eg from 
	request.user it is better to do this:
	.. code-block:: python

		'Nurse' in request.session['MHL_Users']

	If checking another user's type from our db for ex. use this function. 
	"""
	q = Nurse.objects.filter(user=user)
	if (q.count() != 1):
		return False
	return q[0]


def user_is_np_pa(user):
	"""
	Note: If checking if a user is a NP_PA from a request object, eg from 
	request.user it is better to do this:

	.. code-block:: python

		'NP_PA' in request.session['MHL_Users']

	If checking another user's type from our db for ex. use this function. 
	"""
	q = NP_PA.objects.filter(user=user)
	if (q.count() != 1):
		return False
	return q[0]


def user_is_dietician(user):
	"""
	Note: If checking if a user is a Dietician from a request object, eg from 
	request.user it is better to do this:
	.. code-block:: python

		'Dietician' in request.session['MHL_Users']

	If checking another user's type from our db for ex. use this function.
	"""
	q = Dietician.objects.filter(user=user)
	if (q.count() != 1):
		return False
	return q[0]


def user_is_office_manager(user):
	"""
	Note: If checking if a user is an Office_Manager from a request object, eg from 
	request.user it is better to do this:
	.. code-block:: python

		'Office_Manager' in request.session['MHL_Users']

	If checking another user's type from our db for ex. use this function. 
	"""
	q = Office_Manager.objects.filter(user=user)
	if (q.count() != 1):
		return False
	return q[0]


def user_is_administrator(user):
	"""
	Note: If checking if a user is an Administrator from a request object, eg from 
	request.user it is better to do this:

	.. code-block:: python

		'Administrator' in request.session['MHL_Users']

	If checking another user's type from our db for ex. use this function. 
	"""
	q = Administrator.objects.filter(user=user)
	if (q.count() != 1):
		return False
	return q[0]


def user_is_provider(user):
	"""
	Note: If checking if a user is a provider from a request object, eg from 
	request.user it is better to do this:
	.. code-block:: python

		'Provider' in request.session['MHL_Users']

	If checking another user's type from our db for ex. use this function. 
	"""
	q = Provider.objects.filter(id=user.id)
	if (q.count() != 1):
		return False
	return q[0]


def user_is_office_staff(user):
	"""
	Note: If checking if a user is an OfficeStaff from a request object, eg from 
	request.user it is better to do this:
	.. code-block:: python

		'OfficeStaff' in request.session['MHL_Users']

	If checking another user's type from our db for ex. use this function. 
	"""
	q = OfficeStaff.objects.filter(user=user)
	if (q.count() != 1):
		return False
	return q[0]


def user_is_mgr_of_practice_id(user, practice_id):
	""" Return True if user is manager of practice given practice id """
	is_pmgr = False
	# make sure they have a staff profile		
	oss = OfficeStaff.objects.filter(user=user)
	for os in oss:  # typically 1-1 staff <--> user
		if Office_Manager.objects.filter(user=os, practice__id=practice_id).exists():
			is_pmgr = True
			break

	return is_pmgr


def user_is_mgr_of_practice(user, practice):
	""" Return True if user is manager of practice """
	return user_is_mgr_of_practice_id(user, practice.id)


def get_all_practice_managers(practice):
	if (practice == None):
		return None

	mgrs = Office_Manager.active_objects.filter(user__practices=practice, 
		practice=practice).only('user').select_related('user')

	return [mgr.user for mgr in mgrs]


def get_all_practice_staff(practice):
	"""
	Returns all staff associated with the given practice.

	Note that the returned objects will have a new instance variable defined: 
	'type'. Type will be a human-readable string describing the type of the
	staffer.

	Valid type values are:
		"Manager"
	"""
	if (practice == None):
		return None
	users = list(Office_Manager.active_objects.filter(user__practices=practice))
	ret_users, staff_ids = remove_repeat_office_manager(users)
	ret_users.extend(OfficeStaff.active_objects.filter(practices=practice).
					exclude(id__in=staff_ids))
	return ret_users


def get_managed_practice(office_staff):
	practices = office_staff.practices.all()
	managed_practices = []
	for p in practices:
		if Office_Manager.objects.filter(user=office_staff, practice=p).exists():
			managed_practices.append(p)
	return managed_practices


def get_all_site_providers(site):
	# TODO: Update this to include nurses and office managers
	# no, site providers are just that site PROVIDERS, if you need to have ALL
	# we will need write new function and use that in places where you need providers
	# AND office staff
	if (site == None):
		return None
	providers = list(Physician.active_objects.filter(user__sites=site).exclude(
		user__clinical_clerk='True').select_related('user', 'user__user'))
	providers.extend(list(NP_PA.active_objects.filter(user__sites=site).
		select_related('user', 'user__user')))
	providers.sort(lambda x, y: cmp(x.user.user.last_name.lower(), y.user.user.last_name.lower()))

	return providers


def get_community_providers(doctor):
	"""
	about community search.
	Gets the community providers for the passed Physician/NP_PA object. 
	Refer to Provider comments: new code will not rely on Provider inheriting from MHLUser.
	Stating: use the provided user field to refer to the parent object...
	doctor.user is of type Provider which has foreign key object to user.  Provider
	will no longer inherit from MHLUser.
	"""
	return get_community_providers_by_coords(doctor.user.lat, doctor.user.longit)


def get_community_providers_by_coords(lat, longit, miles=settings.PROXIMITY_RANGE, licensure=None):
	if lat and  longit:
		latmin, latmax, longitmin, longitmax = miles2latlong_range(lat, longit, miles)
		#raise Exception(doctor, doctor.user.office_address1, doctor.user.office_city, 
		#latmin,latmax, longitmin, longitmax)
		# TODO: Update this to include nurses and office managers
		physicians = Physician.active_objects.filter(user__user__lat__range=(latmin, latmax), 
			user__user__longit__range=(longitmin, longitmax)).\
				exclude(user__clinical_clerk='True').select_related('user', 'user__user')
		np_pas = NP_PA.active_objects.filter(user__user__lat__range=(latmin, latmax), 
			user__user__longit__range=(longitmin, longitmax)).select_related('user', 'user__user')

		if licensure:
			physicians = physicians.filter(user__licensure_states__state=licensure)
			np_pas = np_pas.filter(user__licensure_states__state=licensure)

		users = list(physicians)	
		users.extend(list(np_pas))
		users.sort(lambda x, y: cmp(x.user.user.last_name.lower(), y.user.user.last_name.lower()))

		return users
	else:
		return get_all_community_providers(licensure)


def get_community_providers_by_zipcode(zip, miles=settings.PROXIMITY_RANGE, licensure=None):
	if (zip):
		geocode_data = geocode2(None, None, None, zip)
		lat = geocode_data['lat']
		longit = geocode_data['lng']	
		return get_community_providers_by_coords(lat, longit, miles, licensure)
	else:
		return get_all_community_providers(licensure)


def get_all_community_providers(licensure=None):
	physicians = Physician.active_objects.all().exclude(user__clinical_clerk='True').\
		select_related('user', 'user__user')
	np_pas = NP_PA.active_objects.all().select_related('user', 'user__user')

	if licensure:
		physicians = physicians.filter(user__licensure_states__state=licensure)
		np_pas = np_pas.filter(user__licensure_states__state=licensure)

	users = list(physicians)
	users.extend(list(np_pas))
	users.sort(lambda x, y: cmp(x.user.user.last_name.lower(), y.user.user.last_name.lower()))
	return users


def get_community_professionals(practice):
	if (practice == None):
		return get_all_community_providers()
	else:
		lat = practice.practice_lat
		longit = practice.practice_longit
		return get_community_providers_by_coords(lat, longit)


def get_all_site_clinical_clerks(site):
	"""
		about clerks search.
	"""
	# TODO: Update this to include nurses and office managers
	if (site == None):
		return None
	users = list(Physician.active_objects.filter(user__sites=site, 
		user__clinical_clerk='True').select_related('user', 'user__user'))
	users.sort(lambda x, y: cmp(x.user.user.last_name.lower(), y.user.user.last_name.lower()))

	return users


def get_all_clinical_clerks():
	users = list(Physician.active_objects.filter(user__clinical_clerk='True').
				select_related('user', 'user__user'))
	users.sort(lambda x, y: cmp(x.user.user.last_name.lower(), y.user.user.last_name.lower()))
	return users


def get_clinical_clerks_by_coords(lat, longit, miles=settings.PROXIMITY_RANGE):
	if not lat and not longit:
		return get_all_clinical_clerks()

	latmin, latmax, longitmin, longitmax = miles2latlong_range(lat, longit, miles)

	users = list(Physician.active_objects.filter(user__user__lat__range=(latmin, latmax), 
		user__user__longit__range=(longitmin, longitmax), 
			user__clinical_clerk='True').select_related('user', 'user__user'))
	users.sort(lambda x, y: cmp(x.user.user.last_name.lower(), y.user.user.last_name.lower()))
	return users


def get_clinical_clerks_by_zipcode(zip, miles=settings.PROXIMITY_RANGE):
	if (zip):
		geocode_data = geocode2(None, None, None, zip)
		lat = geocode_data['lat']
		longit = geocode_data['lng']	
		return get_clinical_clerks_by_coords(lat, longit, miles)
	else:
		return get_all_clinical_clerks()


def get_all_site_staff(site):
	"""
	Returns all staff who are associated to a Practice at the site.

	Note that the returned objects will have a new instance variable defined: 
	'type'. Type will be a human-readable string describing the type of the
	staffer.

	Valid type values are:
		"Manager"
	"""
	if (site == None):
		return None

	users = list(Office_Manager.active_objects.filter(
		user__sites=site
	).select_related('user', 'user__user', 'user__current_practice').order_by())
	ret_users, staff_ids = remove_repeat_office_manager(users)
	ret_users.extend(OfficeStaff.active_objects.filter(
		sites=site
	).exclude(id__in=staff_ids).select_related(
		'user', 'user__user', 'user__current_practice'))
	return ret_users


def set_site_staff_result(staff, current_user, strip_staff_mobile=True, strip_staff_pager=True):
	"""
	Returns staff response data.
	:param staff: is a list of OfficeStaff/OfficeManager.
	:param current_user: current_user is an instance of Provider/OfficeStaff.

	pass strip_staff_mobile=True if you want all office staff users(exclude managers and
	above they) to come back without a mobile phone number defined. This is useful if
	you don't want the u to seem call-able.

	pass strip_staff_pager=True if you want all office staff users(exclude managers and
	above they) to come back without a pager number defined. This is useful if you
	don't want the u to seem call-able.

	:returns: user list.
	"""
#	current_user_mobile = getCurrentUserMobile(current_user)
	current_user_mobile = current_user.user.mobile_phone
	user_list = []
	if staff:
		for s in staff:
			if (s.__class__.__name__ == 'Office_Manager'):
				user_info = {
						'id': s.user.user.id,
						'fullname': get_fullname(s.user.user),
						'staff_type': _('Office Manager'),
						'call_available': bool(s.user.user.mobile_phone) and
							bool(current_user_mobile) and settings.CALL_ENABLE,
						'pager_available': bool(s.user.pager) and settings.CALL_ENABLE
					}
			else:
				user_info = {
						'id': s.user.id,
						'fullname': get_fullname(s.user),
						'staff_type': _('Office Staff'),
						'call_available': not strip_staff_mobile and
							bool(s.user.mobile_phone) and bool(current_user_mobile) and
								settings.CALL_ENABLE,
						'pager_available': not strip_staff_pager and
							bool(s.pager) and settings.CALL_ENABLE
					}
			user_list.append(user_info)
	return sorted(user_list, key=lambda item: "%s" %(item['fullname'].lower()))


def get_password_hash(raw_password):
	"""
	Based on Django 1.1.1's password hash generator.
	"""
	import random
	from MHLogin.DoctorCom.IVR.models import get_hexdigest
	algo = 'sha1'
	salt = get_hexdigest(algo, str(random.random()), str(random.random()))[:5]
	hsh = get_hexdigest(algo, salt, raw_password)
	return '%s$%s$%s' % (algo, salt, hsh)


def all_practice_members(practice, strip_staff_mobile=True, strip_staff_pager=True):
	"""
	TODO: consider using FK reverse lookups via related_name field in user models

	Returns every provider associated with the practice, and all office staff for the practice.

	pass strip_staff_mobile=True if you want all office staff users(exclude managers 
	and above they) to come back without a mobile phone number defined. This is useful if 
	you don't want the user to seem call-able.

	pass strip_staff_pager=True if you want all office staff users(exclude managers and 
	above they) to come back without a pager number defined. This is useful if you don't 
	want the user to seem call-able.
	"""
	# providers in this method mean everyone who belongs to this office
	#only the "hats" specified in this methid will be returned, Add new 
	#"hats" modify this function
	if (practice == None):
		return None

	#let's marry provides and office stuff into one list
	members = list(Provider.active_objects.filter(practices=practice).select_related('user'))

	if (strip_staff_mobile or strip_staff_pager):
		staff = list(OfficeStaff.active_objects.filter(practices=practice).select_related('user'))
		for user in staff:
			try:
				Office_Manager.objects.get(user=user, practice=practice)
			except Office_Manager.DoesNotExist:
				if strip_staff_mobile:
					user.user.mobile_phone = None
				if strip_staff_pager:
					user.pager = None
		members.extend(staff)
	else:
		members.extend(list(OfficeStaff.active_objects.filter(
			practices=practice).select_related('user')))

	return members


#add by xlin in 130122 to return user type text
#0 is office manager;1 is nurse;2 is staff
def getUserTypeText(user_id):
	if user_id:
		if Office_Manager.objects.filter(user__id=user_id).exists():
			return 0
		if Nurse.objects.filter(user__id=user_id).exists():
			return 1
	return 2


#add by xlin in 130114 to get all staff
#update by xlin in 130122 to remove Dietician
def all_staff_members(practice):
	members = list(OfficeStaff.active_objects.filter(practices=practice).select_related('user'))
	managers = Office_Manager.objects.filter(practice=practice).values_list('user__id')
	nurses = Nurse.objects.all().values_list('user__id')
	dieticians = Dietician.objects.all().values_list('user__id')
	ms = []
	for m in members:
		if (m.id,) not in dieticians or (m.id,) in managers:
			m.fullname = get_fullname(m.user)
			m.fullname = m.fullname.strip()
			ms.append(m)
#			m.usertypetext = getUserTypeText(m.id, practice)
			if (m.id,) in managers:
				m.usertypetext = 0
			elif (m.id,) in nurses:
				m.usertypetext = 1
			else:
				m.usertypetext = 2

	#sort by last name,first name
	ms.sort(lambda x, y: cmp(x.user.last_name.lower(), y.user.last_name.lower()))
	return ms


def get_all_practice_providers_without_text(practice):
	# providers in this method mean everyone who belongs to this office
	#only the "hats" specified in this methid will be returned, Add 
	#new "hats" modify this function
	if (practice == None):
		return None	
	#office staff type
	dieticians = Dietician.active_objects.filter(user__practices=practice)
	nurses = Nurse.active_objects.filter(user__practices=practice)

	#let's marry provides and office stuff into one list
	staff = list(OfficeStaff.active_objects.filter(Q(dietician__in=dieticians) | 
		Q(nurse__in=nurses)).select_related('user'))
	staff.sort(lambda x, y: cmp(x.user.last_name.lower(), y.user.last_name.lower()))
	return staff


def get_all_practice_providers(practice, exclude_clerk=True):
	# providers in this method mean everyone who belongs to this office
	#only the "hats" specified in this methid will be returned, Add new 
	#"hats" modify this function

	if (practice == None):
		return None
	physician_set = Physician.active_objects.filter(user__practices=practice)
	if exclude_clerk:
		physician_set = physician_set.exclude(user__clinical_clerk='True')
	providers = list(physician_set.select_related('user', 'user__user'))
	providers.extend(list(NP_PA.active_objects.filter(user__practices=practice).
		select_related('user', 'user__user')))
	providers.sort(lambda x, y: cmp(x.user.user.last_name.lower(), y.user.user.last_name.lower()))

	return providers


def get_providers_for_staff(practice):
	lat = practice.practice_lat
	longit = practice.practice_longit

	latmin, latmax, longitmin, longitmax = miles2latlong_range(lat, longit)

	#raise Exception(doctor, doctor.user.office_address1, doctor.user.office_city, 
	# latmin,latmax, longitmin, longitmax)
	# get list of docotors and nurse practitioners
	physicians = Physician.active_objects.filter(user__sites=None, 
		user__user__lat__range=(latmin, latmax), 
			user__user__longit__range=(longitmin, longitmax)).\
				exclude(user__clinical_clerk='True')
	np_pas = NP_PA.active_objects.filter(user__sites=None, 
		user__user__lat__range=(latmin, latmax), 
			user__user__longit__range=(longitmin, longitmax))
	users = list(Provider.active_objects.filter(Q(physician__in=physicians) | 
		Q(np_pa__in=np_pas)).select_related('user'))
	users.sort(lambda x, y: cmp(x.last_name.lower(), y.last_name.lower()))

	return users


def change_pass(form, request, response):
	# TESTING_KMS_INTEGRATION
	uprivs = UserPrivateKey.objects.filter(user=form.user,
				credtype=CRED_WEBAPP, gfather=False)
	recrypt_keys(uprivs, form.cleaned_data['old_password'],
		form.cleaned_data['new_password1'])

	form.user.set_password(form.cleaned_data['new_password1'])
	form.user.save()
	request.session['password_change_time'] = form.user.password_change_time
	store_user_key(request, response, form.cleaned_data['new_password1'])

	device_assn = SmartPhoneAssn.objects.filter(user=request.user)
	for device in device_assn:
		device.usr_password_reset(request)

	return response


def change_pass_common(form, request):
	# TESTING_KMS_INTEGRATION
	uprivs = UserPrivateKey.objects.filter(user=form.user,
				credtype=CRED_WEBAPP, gfather=False)
	recrypt_keys(uprivs, form.cleaned_data['old_password'],
		form.cleaned_data['new_password1'])
	form.user.set_password(form.cleaned_data['new_password1'])
	form.user.force_pass_change = False
	form.user.save()
	device_assn = SmartPhoneAssn.objects.filter(user=request.user)
	for device in device_assn:
		device.usr_password_reset(request)


def answerToHash(hashstr):
	data = hashstr.lower()
	#data = u''.join(e for e in str if e.isalnum())
	return get_password_hash(data)


def getErrorMessage(request):
	if "error_message" in request.session:
		msg = request.session["error_message"]
		request.session["error_message"] = ""
		if msg != "" and msg != None:
			return msg
		else:
			return ""
	else:
		return ""


def putErrorMessage(request, message):
	if "error_message" in request.session:
		request.session["error_message"] = request.session["error_message"] + " " + message
		return
	else:
		request.session["error_message"] = message
		return


def set_specialty_display(providers):
	if (providers):
		for provider in providers:
			if (hasattr(provider, 'specialty')):
				if (provider.specialty):
					provider.template_specialty = provider.get_specialty_display()
			else:
				provider.template_specialty = _('NP/PA/Midwife')


def get_specialty_display_by_provider(provider):
	phys = Physician.objects.filter(user=provider).select_related()
	if phys and phys[0].get_specialty_display():
		return  phys[0].get_specialty_display()
	return 'N/A'


def get_mhluser_by_email(email, exclude_user=None):
	"""
		Get MHLUser by email, If exclude_user is not None, exclude related MHLUser.
	"""
	users = MHLUser.objects.filter(email=email)
	if exclude_user is not None:
		users = users.exclude(id=exclude_user)
	users = list(users)
	if (users and len(users) > 0):
		return users
	else:
		return None 


def has_mhluser_with_email(email, exclude_user=None):
	"""
		Check whether has same MHLUser with the same email in database, 
		If exclude_user is not None, exclude related MHLUser.
	"""
	users = get_mhluser_by_email(email, exclude_user)
	if (users):
		return True
	else:
		return False


def get_mhluser_by_mobile_phone(mobile_phone, exclude_user=None):
	"""
		Get MHLUser by mobile_phone, If exclude_user is not None, exclude related MHLUser.
	"""
	users = MHLUser.objects.filter(mobile_phone=mobile_phone)
	if exclude_user is not None:
		users = users.exclude(id=exclude_user)
	users = list(users)
	if (users and len(users) > 0):
		return users
	else:
		return None 


def has_mhluser_with_mobile_phone(mobile_phone, exclude_user=None):
	"""
		Check whether has same MHLUser with the same mobile_phone in database, 
		If exclude_user is not None, exclude related MHLUser.
	"""
	users = get_mhluser_by_mobile_phone(mobile_phone, exclude_user)
	if (users):
		return True
	else:
		return False


def getCurrentUserInfo(request):
	mhluser = request.session['MHL_Users']['MHLUser']
	user = None
	if ('Provider' in request.session['MHL_Users']):
		user = request.session['MHL_Users']['Provider']
		user.needValidateContactInfo = needValidateContactInfo(mhluser, user)
		user.needConfigureProvisionLocalNumber = needConfigureProvisionLocalNumber(user)
	elif ('Broker' in request.session['MHL_Users']):
		user = request.session['MHL_Users']['Broker']
		user.needValidateContactInfo = needValidateContactInfo(mhluser, user)
		user.needConfigureProvisionLocalNumber = needConfigureProvisionLocalNumber(user)
	elif 'OfficeStaff' in request.session['MHL_Users']:
		user = request.session['MHL_Users']['OfficeStaff']
		user.needValidateContactInfo = needValidateContactInfo(mhluser, user)
		user.needConfigureProvisionLocalNumber = False
	elif 'Salesperson' in request.session['MHL_Users']:
		user = request.session['MHL_Users']['Salesperson']
		user.needValidateContactInfo = False
		user.needConfigureProvisionLocalNumber = False

	return user


def needValidateContactInfo(mhluser, user):
	# See whether this user's mobile phone/pager/email is validated. 
	# If mobile phone is not validated and settings.CALL_ENABLE is True, return True.
	# If email is not validated, return True.
	if ((mhluser.mobile_phone and not mhluser.mobile_confirmed and settings.CALL_ENABLE) 
		or (mhluser.email and not mhluser.email_confirmed)):
		return True
	# If pager is not validated and settings.CALL_ENABLE is True, return True.
	if user.pager and not user.pager_confirmed and settings.CALL_ENABLE:
		return True
	return False


# See if this user is a provider or broker and his mdcom_phone is null and
# CALL_ENABLE is True, then return True. 
def needConfigureProvisionLocalNumber(user):
	try:
		if user and not user.mdcom_phone and settings.CALL_ENABLE:
			return True
		return False
	except AttributeError:
		return False


def generate_name_query(name):
	""" Helper generate name query, name can be first/last separated by spaces """
	qry = Q()
	name = name and name.strip()
	if name:
		namesplit = unicode.split(name)
		if len(namesplit) == 1:
			fname, lname = namesplit[0], ''
		else:
			fname, lname = namesplit[0], ' '.join(namesplit[1:])
		if lname:
			qry = Q(first_name__icontains=fname) & Q(last_name__icontains=lname) \
				| Q(first_name__icontains=lname) & Q(last_name__icontains=fname)
		else:
			qry = Q(first_name__icontains=fname) | Q(last_name__icontains=fname)
	return qry


def search_mhluser(qry=None, limit=None, *related):
	""" Search MHLUser table by query Q object qry """
	qry = qry or Q()

	user_qry = MHLUser.objects.filter(is_active=True).filter(qry).\
		select_related(*related).order_by('last_name', 'first_name', 'id')

	return user_qry[:limit] if limit else user_qry


def search_by_name(name, limit=None, *related):
	filt = Q(is_active=True)
	if name:
		namesplit = unicode.split(name)
		if len(namesplit) == 1:
			first_name = namesplit[0]
			last_name2 = ''
		else:
			first_name = namesplit[0]
			last_name = namesplit[1:]
			last_name2 = ' '.join(last_name)
		if last_name2:
			filt = filt & Q(first_name__icontains=first_name) \
				& Q(last_name__icontains=last_name2) \
				| Q(first_name__icontains=last_name2) \
				& Q(last_name__icontains=first_name)
		else:
			filt = filt & Q(first_name__icontains=first_name) \
				| Q(last_name__icontains=first_name)

	provs = list(Provider.objects.all().values_list("user__id", flat=True))
	staffs = list(OfficeStaff.objects.all().values_list("user__id", flat=True))
	filt = filt & Q(Q(pk__in=provs) | Q(pk__in=staffs))
	user_qry = MHLUser.objects.filter(filt).select_related(*related)
	return user_qry[:limit] if limit else user_qry


def set_providers_result(providers, request):
	"""
	Set providers list results.  current_user is provider/office 
	staff/broker from session

	:param providers: actually, providers is a Physician/NP_PA list.
		Note, the function will be changed, when implement the ticket #272
	:param request:
	:returns: Physician/NP_PA list
	"""
	current_user = getCurrentUserInfo(request)
	current_user_mobile = getCurrentUserMobile(current_user)
#	current_user_pager = current_user.pager
	if (providers):
		for provider in providers:
			provider.fullname = get_fullname(provider.user)
			if (hasattr(provider, 'specialty')):
				if (provider.specialty):
					provider.template_specialty = provider.get_specialty_display()
			else:
				provider.template_specialty = _('NP/PA/Midwife')
			if current_user_mobile and settings.CALL_ENABLE:
				provider.call_available = bool(provider.user.user.mobile_phone)
			else:
				provider.call_available = False

			if settings.CALL_ENABLE:
				provider.pager_available = bool(provider.user.pager)
			else:
				provider.pager_available = False
			if hasattr(provider, 'practice_count'):
				provider.refer_available = provider.practice_count
			else:
				provider.refer_available = len(provider.user.practices.filter(
					organization_type__id=RESERVED_ORGANIZATION_TYPE_ID_PRACTICE)) > 0
	return providers


"""
	Set practice members list results.
	current_user is provider/office staff/broker from session
	:param practice_members: practice_members is a Provider/OfficeStaff list.
	:parm request
	:returns: Provider/OfficeStaff list
"""


def set_practice_members_result(practice_members, request):
	current_user = getCurrentUserInfo(request)
	current_user_mobile = getCurrentUserMobile(current_user)
#	current_user_pager = current_user.pager
#	phys = Physician.objects.filter()
	if (practice_members):
		for member in practice_members:
			member.fullname=get_fullname(member.user)
			if current_user_mobile and settings.CALL_ENABLE:
				member.call_available = bool(member.user.mobile_phone)
			else:
				member.call_available = False

			if settings.CALL_ENABLE:
				member.pager_available = bool(member.pager)
			else:
				member.pager_available = False

			if isinstance(member, OfficeStaff):
				member.refer_displayable = False
			else:
				member.refer_displayable = True
				member.refer_available = len(member.practices.filter(
					organization_type__id=RESERVED_ORGANIZATION_TYPE_ID_PRACTICE)) > 0
	return practice_members


def set_org_members_result(org_members, request):
	"""
	Set organization members list results. current_user is provider/office 
	staff/broker from session

	:param org_members: org_members is a Provider/OfficeStaff list.
	:param request:
	:returns: Provider/OfficeStaff list
		Note: at present, set_org_members_result and set_practice_members_result have 
		the same logic, so, I invoke the function set_practice_members_result in 
		set_org_members_result directly. If the logic change, please change this function.
	"""
	return set_practice_members_result(org_members, request)


def update_staff_address_info_by_practice(practice):
	"""
	Change office staff's address information by using practice

	Note: When practice's profile information is changed,
		the address information of the office staff(include office manager) whose current 
		practice is this practice will be changed.
		Only change office staff's address information, don't change provider/broker's.

	:param practice: practice.
	:returns: None
	"""
	staff = OfficeStaff.objects.filter(current_practice=practice)
	staff_ids = [u.user_id for u in staff]
	providers = Provider.objects.all()
	exclude_ids = [u.user_id for u in providers]
	brokers = Broker.objects.all()
	exclude_ids.extend([u.user_id for u in brokers])
	MHLUser.objects.filter(pk__in=staff_ids).exclude(pk__in=exclude_ids).update(
			address1=practice.practice_address1,
			address2=practice.practice_address2,
			city=practice.practice_city,
			state=practice.practice_state,
			zip=practice.practice_zip,
			lat=practice.practice_lat,
			longit=practice.practice_longit,
		)


def remove_repeat_office_manager(manager_rs):
	"""
	remove the repeated office manager

	Because office manager can manage many practice, so Office_Manager may has many records.
	and we should remove the repeated office manager.

	:param manager_list: manager result set.
	:returns: distinct manager result set.
	:returns: Staff id for related manager
	"""

	ret_managers_rs = []
	staff_ids = []
	for manager in manager_rs:
		if manager.user_id not in staff_ids:
			staff_ids.append(manager.user_id)
			ret_managers_rs.append(manager)

	return [ret_managers_rs, staff_ids]


#get user type display text by mhluser
def getUserTypeByUser(user):
	user_id = user.id
	provs = Provider.objects.filter(user__id=user_id)
	if provs:
		return getProviderTypeBy(provs[0])
	return getOfficeTypeByUser(user_id)


def getOfficeTypeByUser(user_id):
	u = Office_Manager.objects.filter(user__user__id=user_id)
	if u:
		return 'Office manager'
	return 'Office staff'


def getProviderTypeBy(user):
	np = NP_PA.objects.filter(user=user)
	if np:
		return 'NP/PA/Midwife'
	elif user.clinical_clerk:
		return 'Medical Student'
	else:
		return 'Doctor'


def getCurrentUserMobile(current_user):
	mobile_phone = current_user.user.mobile_phone
	if isinstance(current_user, OfficeStaff):
		mgrs = Office_Manager.objects.filter(user=current_user)
		if mgrs:
			staff = mgrs[0].user
			if staff.caller_anssvc == 'MO':
				mobile_phone = staff.user.mobile_phone
			elif staff.caller_anssvc == 'OF':
				mobile_phone = staff.office_phone
			elif staff.caller_anssvc == 'OT':
				mobile_phone = staff.user.phone
			else:
				mobile_phone = None
	return mobile_phone


def check_username_another_server(username, url, times):
	return False
	times += 1
	line = 0
	try:
		url_full = ''.join([url, '/CheckUserName/', username])
		page = urllib.urlopen(url_full)
		line = int(page.readline())
		page.close()
	except:
		if times == 3:
			pass
		else:
			check_username_another_server(username, url, times)
	if line == 1:
		return True
	return False


def get_user_type_ids(user):
	type_ids = []
	provider = user_is_provider(user)
	if provider:
		if user_is_physician(provider):
			if provider.clinical_clerk:
				type_ids.append(USER_TYPE_MEDICAL_STUDENT)
			else:
				type_ids.append(USER_TYPE_DOCTOR)
		if user_is_np_pa(provider):
			type_ids.append(USER_TYPE_NPPA)

	staff = user_is_office_staff(user)
	if staff:
		type_ids.append(USER_TYPE_OFFICE_STAFF)
		if user_is_office_manager(staff):
			type_ids.append(USER_TYPE_OFFICE_MANAGER)
		if user_is_dietician(staff):
			type_ids.append(USER_TYPE_DIETICIAN)
		if user_is_nurse(staff):
			type_ids.append(USER_TYPE_NURSE)

	if is_techadmin(user):
		type_ids.append(USER_TYPE_TECH_ADMIN)
	return type_ids


def get_practice_org(org):
	"""
	Get practice type of organization if the org type is not practice then return None

	:param org: an instance of organization
	:returns: organization.
	"""
	if not org:
		return None
	org_type = org.organization_type
	if not org_type:
		return None
	if not RESERVED_ORGANIZATION_TYPE_ID_PRACTICE == org_type.id:
		return None
	return org

def get_fullname_bystr(lastname, firstname, title=None, delimiter=", "):
	ret_str = ""
	if lastname:
		ret_str = ret_str + lastname

	if firstname:
		if ret_str:
			ret_str = ret_str + delimiter
		ret_str = ret_str + firstname

	if title:
		if ret_str:
			ret_str = ret_str + delimiter
		ret_str = ret_str + title
	return ret_str

def get_fullname(user, delimiter=", "):
	""" Get fullname like last name, title, first name.
	:param user: can be MHLUser,Provider,OfficeStaff or Borker
	:param delimiter: fullname will spilt by delimiter default is ', '
	:returns: string of fullname
	"""
	if isinstance(user, (Provider, OfficeStaff, Broker, Salesperson)):
		user = user.user
	elif isinstance(user, MHLUser):
		user = user
	else:
		return ""

	return get_fullname_bystr(user.last_name, user.first_name, user.title, 
				delimiter=delimiter)
