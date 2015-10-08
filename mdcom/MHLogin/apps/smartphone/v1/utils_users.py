
from django.conf import settings
from django.utils.translation import ugettext as _

from MHLogin.MHLUsers.models import Provider, OfficeStaff, Nurse, Physician, Office_Manager,\
	NP_PA
from MHLogin.MHLUsers.utils import get_fullname
from MHLogin.utils import ImageHelper
from MHLogin.utils.constants import USER_TYPE_OFFICE_MANAGER, USER_TYPE_OFFICE_STAFF
from MHLogin.MHLOrganization.utils import get_prefer_logo
from MHLogin.MHLFavorite.utils import get_my_favorite_ids,\
	OBJECT_TYPE_FLAG_MHLUSER

def _set_staff_list(staff, current_user, strip_staff_mobile=True, strip_staff_pager=True):
	"""
	Returns staff response data.
	:param users: is a list of Provider/OfficeStaff/OfficeManager.
	:param current_user: current_user is an instance of Provider/OfficeStaff.
	pass strip_staff_mobile=True if you want all office staff users(exclude managers and above they) to come back without a mobile phone number defined. This is useful if you don't want the u to seem call-able.

	
	pass strip_staff_pager=True if you want all office staff users(exclude managers and above they) to come back without a pager number defined. This is useful if you don't want the u to seem call-able.

	:returns: user list.
	"""
#	current_user_mobile = getCurrentUserMobile(current_user)
	current_user_mobile = current_user.user.mobile_phone
	object_ids = get_my_favorite_ids(current_user.user, object_type_flag=OBJECT_TYPE_FLAG_MHLUSER)
	user_list = []
	for s in staff:
		if (s.__class__.__name__ == 'Office_Manager'):
			user_info = {
					'id': s.user.user.id,
					'first_name': s.user.user.first_name,
					'last_name': s.user.user.last_name,
					'staff_type': _('Office Manager'),
					'has_mobile': bool(s.user.user.mobile_phone) and bool(current_user_mobile) and settings.CALL_ENABLE,
					'has_pager': bool(s.user.pager) and settings.CALL_ENABLE,
					'thumbnail': ImageHelper.get_image_by_type(s.user.user.photo, "Small", "Staff"),
					'user_photo_m': ImageHelper.get_image_by_type(s.user.user.photo, "Middle", "Staff"),
					'practice_photo': ImageHelper.get_image_by_type(s.user.current_practice.practice_photo, "Large", "Practice") \
						if s.user.current_practice else "",
					'prefer_logo': get_prefer_logo(s.user.user.id, current_practice=s.user.current_practice),
					'is_favorite': s.user.user.id in object_ids,
					'fullname':get_fullname(s.user.user)
				}
		else:
			user_info = {
					'id': s.user.id,
					'first_name': s.user.first_name,
					'last_name': s.user.last_name,
					'staff_type': _('Office Staff'),
					'has_mobile': not strip_staff_mobile and bool(s.user.mobile_phone) and bool(current_user_mobile) and settings.CALL_ENABLE,
					'has_pager': not strip_staff_pager and bool(s.pager) and settings.CALL_ENABLE,
					'thumbnail': ImageHelper.get_image_by_type(s.user.photo, "Small", "Staff"),
					'user_photo_m': ImageHelper.get_image_by_type(s.user.photo, "Middle", "Staff"),
					'practice_photo': ImageHelper.get_image_by_type(s.current_practice.practice_photo, "Large", "Practice") \
						if s.current_practice else "",
					'prefer_logo': get_prefer_logo(s.user.id, current_practice=s.current_practice),
					'is_favorite': s.user.id in object_ids,
					'fullname':get_fullname(s.user)
				}

			# TODO: Clean me up once we refactor the user classes.
			try:
				nurse = Nurse.objects.get(user=s)
				user_info['thumbnail'] = ImageHelper.get_image_by_type(s.user.photo, "Small", "Nurse")
				user_info['user_photo_m'] = ImageHelper.get_image_by_type(s.user.photo, "Middle", "Nurse"),
			except Nurse.DoesNotExist:
				pass
		user_list.append(user_info)
	return sorted_uses(user_list)


def _set_providers_list(providers, current_user, has_specialty=True):
	"""
	Returns org members response data.
	:param providers: is a list of Physician/NP_PA.
	:param current_user: current_user is an instance of Provider/OfficeStaff.
	:returns: user list.
	"""
	object_ids = get_my_favorite_ids(current_user.user, object_type_flag=OBJECT_TYPE_FLAG_MHLUSER)
#	current_user_mobile = getCurrentUserMobile(current_user)
	current_user_mobile = current_user.user.mobile_phone
	user_list = []
	for p in providers:
		user_info = {
				'id': p.user.user.id,
				'first_name': p.user.first_name,
				'last_name': p.user.last_name,
				'specialty': '',
				'has_mobile': bool(p.user.user.mobile_phone) and bool(current_user_mobile) and settings.CALL_ENABLE,
				'has_pager': bool(p.user.pager) and settings.CALL_ENABLE,
				'thumbnail': ImageHelper.get_image_by_type(p.user.user.photo, "Small", "Provider"),
				'user_photo_m': ImageHelper.get_image_by_type(p.user.user.photo, "Middle", "Provider"),
				'practice_photo': ImageHelper.get_image_by_type(p.user.current_practice.practice_photo, "Large", "Practice") \
						if p.user.current_practice else "",
				'prefer_logo': get_prefer_logo(p.user.user.id, current_practice=p.user.current_practice),
				'is_favorite': p.user.user.id in object_ids,
				'fullname': get_fullname(p.user)
			}
		if ('specialty' in dir(p) and p.specialty and has_specialty):
			user_info['specialty'] = p.get_specialty_display()
		if NP_PA.active_objects.filter(user=p.user):
			user_info['specialty'] = 'NP/PA/Midwife'

		user_list.append(user_info)
	return sorted_uses(user_list)

def _set_org_members_list(users, current_user):
	"""
	Returns org members response data.
	:param users: is a list of Provider/OfficeStaff.
	:param current_user: current_user is an instance of Provider/OfficeStaff.
	:returns: user list.
	"""
	object_ids = get_my_favorite_ids(current_user.user, object_type_flag=OBJECT_TYPE_FLAG_MHLUSER)
#	current_user_mobile = getCurrentUserMobile(current_user)
	current_user_mobile = current_user.user.mobile_phone
#	current_user_pager = current_user.pager
	user_list = []
	for u in users:
		prefer_logo = get_prefer_logo(u.user.id, current_practice=u.current_practice)
		user_info = {
				'id': u.user.id,
				'first_name': u.user.first_name,
				'last_name': u.user.last_name,
				'specialty': '',
				'has_mobile': bool(u.user.mobile_phone) and bool(current_user_mobile) and settings.CALL_ENABLE,
				'has_pager': bool(u.pager) and settings.CALL_ENABLE,
				'practice_photo': ImageHelper.get_image_by_type(u.current_practice.practice_photo, "Large", "Practice") \
					if u.current_practice else "",
				'practice_photo_m': ImageHelper.get_image_by_type(u.current_practice.practice_photo, "Middle", "Practice") \
					if u.current_practice else "",
				'prefer_logo': prefer_logo,
				'is_favorite': u.user.id in object_ids,
				'fullname':get_fullname(u.user)
			}

		if(u.__class__.__name__ == 'OfficeStaff'):
			user_info["user_type"] = _('Office Staff')
			user_info["thumbnail"] = ImageHelper.get_image_by_type(u.user.photo, "Small", "Staff")
			user_info["user_photo_m"] = ImageHelper.get_image_by_type(u.user.photo, "Middle", "Staff")
			if Office_Manager.objects.filter(user=u).exists():
				user_info["user_type"] = _('Office Manager')
			else:
				# TODO: Clean me up once we refactor the u classes.
				try:
					nurse = Nurse.objects.get(user=u)
					user_info['thumbnail'] = ImageHelper.get_image_by_type(u.user.photo, "Small", "Nurse")
					user_info['user_photo_m'] = ImageHelper.get_image_by_type(u.user.photo, "Middle", "Nurse")
				except Nurse.DoesNotExist:
					pass

		elif(u.__class__.__name__ == 'Provider'):
			user_info["user_type"] = _('Provider')
			user_info["thumbnail"] = ImageHelper.get_image_by_type(u.user.photo, "Small", "Provider")
			user_info["user_photo_m"] = ImageHelper.get_image_by_type(u.user.photo, "Middle", "Provider")
			# TODO: Clean me up once we refactor the u classes.
			try:
				p = Physician.objects.get(user=u)
				user_info['specialty'] = p.get_specialty_display()
			except Physician.DoesNotExist:
				pass

		user_list.append(user_info)
	return sorted_uses(user_list)

def sorted_uses(user_list):
	return sorted(user_list, key=lambda item: "%s%s" % (item['last_name'].lower(), item['first_name'].lower()))