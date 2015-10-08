#-*- coding: utf-8 -*-
'''
Created on 2013-5-28

@author: wxin
'''
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db.models.query_utils import Q
from django.db.models.query import QuerySet
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _

from MHLogin.MHLFavorite.models import Favorite
from MHLogin.MHLPractices.models import PracticeLocation
from MHLogin.MHLUsers.models import MHLUser, OfficeStaff, Nurse, Dietician, \
	Provider, Physician, NP_PA, Office_Manager
from MHLogin.MHLUsers.utils import get_fullname
from MHLogin.utils import ImageHelper
from MHLogin.MHLOrganization.utils import get_prefer_logo
from MHLogin.utils.constants import RESERVED_ORGANIZATION_TYPE_ID_PRACTICE

OBJECT_TYPE_FLAG_MHLUSER = 1
OBJECT_TYPE_FLAG_ORG = 2

OBJECT_TYPES = {
	'mhluser': OBJECT_TYPE_FLAG_MHLUSER,
	'practicelocation': OBJECT_TYPE_FLAG_ORG
}

OBJECT_TYPE_FLAG_OPTS = (
	(OBJECT_TYPE_FLAG_MHLUSER, 'mhluser'),
	(OBJECT_TYPE_FLAG_ORG, 'practicelocation')
)
OBJECT_TYPE_FLAGS = dict(OBJECT_TYPE_FLAG_OPTS)

def get_my_favorite(owner, object_type_flag=None, html=False, can_send_refer=True,
				show_picture=False):
	""" Get my favorite list.
	:param owner: is an instance of MHLUser
	:param object_type_flag: the flag of favorite object, refer to OBJECT_TYPE_FLAG_OPTS.
	:param html: return style: if html is True, then return favorite list as html style.
	:param can_send_refer: whether can send refer
	:param show_picture: whether show picture in list
	:returns: list of favorite or html string
	"""
	if not owner or not isinstance(owner, MHLUser):
		raise ValueError

	current_user_mobile = owner.mobile_phone
	q_t = Q(owner=owner)
	if object_type_flag:
		object_type_flag = int(object_type_flag)
		type = OBJECT_TYPE_FLAGS[object_type_flag]
		q_t = q_t & Q(object_type__model=type)
	favorites = Favorite.objects.filter(q_t).select_related("object_type")

	providers = Provider.objects.all().select_related("user", "current_practice")
	provider_dict = _user_list_to_dict(providers)
#	physician_user_ids = Physician.objects.all().values_list('user_id', flat=True)
#	nppa_user_ids = NP_PA.objects.all().values_list('user_id', flat=True)

	staffs = OfficeStaff.objects.all().select_related("user", "current_practice")
	staff_dict = _user_list_to_dict(staffs)

	manager_ids = Office_Manager.active_objects.all().values_list('user_id', 'practice')
	manager_user_ids = []
	manager_practice_ids = []
	for ids in manager_ids:
		manager_user_ids.append(ids[0])
		manager_practice_ids.append(ids[1])

	nurse_user_ids = Nurse.objects.all().values_list('user_id', flat=True)
#	dietician_user_ids = Dietician.objects.all().values_list('user_id', flat=True)

	ret_favorites = []
	for fav in favorites:
		try:
			obj = fav.object
			if not obj:
				continue
			obj_id = fav.object_id
			object_type_flag = OBJECT_TYPES[fav.object_type.model]
			object_name = ''
			object_name_web_display = ''
			object_type_display = ''
			photo = ''
			photo_m = ''
			prefer_logo = ''
			call_available = False
			msg_available = False
			pager_available = False
			refer_available = False
			refer_displayable = False
			current_practice = None

			if OBJECT_TYPE_FLAG_MHLUSER == object_type_flag:
				object_name_web_display = object_name = get_fullname(obj)
				object_type_display = _("User")
				call_available = bool(obj.mobile_phone) and bool(current_user_mobile) and settings.CALL_ENABLE
				msg_available = True
				if obj_id in provider_dict:
					object_type_display = _("Provider")
					if show_picture:
						photo = ImageHelper.get_image_by_type(obj.photo, "Small", "Provider")
						photo_m = ImageHelper.get_image_by_type(obj.photo, "Middle", "Provider")
					data = provider_dict[obj_id]

					refer_available = data["has_practice"]
					refer_displayable = can_send_refer
					pager_available = bool(data["pager"]) and settings.CALL_ENABLE
					current_practice = data["current_practice"]

				elif obj_id in staff_dict:
					object_type_display = _('Office Staff')
					if show_picture:
						photo = ImageHelper.get_image_by_type(obj.photo, "Small", "Staff")
						photo_m = ImageHelper.get_image_by_type(obj.photo, "Middle", "Staff")

					data = staff_dict[obj_id]
					if data['id'] in manager_user_ids:
						object_type_display = _('Office Manager')
					elif data['id'] in nurse_user_ids:
						if show_picture:
							photo = ImageHelper.get_image_by_type(obj.photo, "Small", "Nurse")
							photo_m = ImageHelper.get_image_by_type(obj.photo, "Middle", "Nurse")

					pager_available = bool(data["pager"]) and settings.CALL_ENABLE
					current_practice = data["current_practice"]
				if show_picture:
					prefer_logo = get_prefer_logo(obj_id, current_practice = current_practice)

			elif OBJECT_TYPE_FLAG_ORG == object_type_flag:
				object_name_web_display = object_name = obj.practice_name
				object_type_display = _("Organization")
				if obj.organization_type and obj.organization_type.name:
					object_type_display = obj.organization_type.name 
				if show_picture:
					photo = ImageHelper.get_image_by_type(obj.practice_photo, 
						"Large", 'Practice', 'img_size_practice')
					photo_m = ImageHelper.get_image_by_type(obj.practice_photo,
						"Middle", 'Practice', 'img_size_practice')
				call_available = (bool(obj.backline_phone) or bool(obj.practice_phone))\
									and bool(current_user_mobile)\
									and settings.CALL_ENABLE
				msg_available = obj_id in manager_practice_ids

			ret_favorites.append({
				"object_name": object_name,
				"object_name_web_display": object_name_web_display,
				"object_type_flag": object_type_flag,
				"object_type_display": object_type_display,
				"object_id": fav.object_id,
				"photo": photo,
				"photo_m": photo_m,
				"prefer_logo": prefer_logo,
				"call_available": call_available,
				"msg_available": msg_available,
				"pager_available": pager_available,
				"refer_available": refer_available,
				"refer_displayable": refer_displayable
			})

		except KeyError:
			pass

	ret_favorites = sorted(ret_favorites, key=lambda item: item['object_name'].lower())
	if html:
		favorite_dict = {"favorites": ret_favorites}
		return render_to_string('my_favorite.html', favorite_dict)

	return ret_favorites

def get_my_favorite_ids(owner, object_type_flag=None):
	""" Get my favorite id list.
	:param owner: is an instance of MHLUser
	:param object_type_flag: the flag of favorite object, refer to OBJECT_TYPE_FLAG_OPTS.
	:returns: list of object_id of favorite object.
	"""
	if not owner or not isinstance(owner, MHLUser):
		raise ValueError

	q_t = Q(owner=owner)
	if object_type_flag:
		object_type_flag = int(object_type_flag)
		type = OBJECT_TYPE_FLAGS[object_type_flag]
		q_t = q_t & Q(object_type__model=type)
	favorite_ids = Favorite.objects.filter(q_t).values_list("object_id", flat=True)
	return favorite_ids

def do_toggle_favorite(owner, object_type_flag, object_id, is_favorite=True):
	""" Add or Remove object from favorite list.
	:param owner: is an instance of MHLUser
	:param object_type_flag: is flag of object_type
	:param object_id: is id of object_type
	:param is_favorite: True or False, 
			if is_favorite is True, then add the object to favorite list,
			if is_favorite is False, then remove the object from favorite list,
			if is_favorite is None, do nothing.
	:raise: ValueError
	"""
	if not owner or not isinstance(owner, MHLUser)\
		or not object_type_flag or not object_id:
		raise ValueError
	object_type_flag = int(object_type_flag)
	object_id = int(object_id)
	object_type = None
	if OBJECT_TYPE_FLAG_MHLUSER == object_type_flag:
		get_object_or_404(MHLUser, pk=object_id)
		object_type=ContentType.objects.get_for_model(MHLUser)
	elif OBJECT_TYPE_FLAG_ORG == object_type_flag:
		get_object_or_404(PracticeLocation, pk=object_id)
		object_type=ContentType.objects.get_for_model(PracticeLocation)

	if not object_type:
		raise ValueError

	if is_favorite == True:
		if not Favorite.objects.filter(object_type=object_type, \
				object_id=object_id, owner=owner).exists():
			Favorite.objects.create(object_type=object_type, \
				object_id=object_id, owner=owner)
	elif is_favorite == False:
		Favorite.objects.filter(object_type=object_type, object_id=object_id, \
				owner=owner).delete()

def is_favorite(owner, object_type_flag, object_id):
	""" Check if the object is the owner's favorite.
	:param owner: is an instance of MHLUser
	:param object_type_flag: is flag of object_type
	:param object_id: is id of object_type
	:returns: True or False
	:raise: ValueError
	"""
	if not owner or not isinstance(owner, MHLUser)\
		or not object_type_flag or not object_id:
		raise ValueError

	object_type = None
	if OBJECT_TYPE_FLAG_MHLUSER == object_type_flag:
		get_object_or_404(MHLUser, pk=object_id)
		object_type=ContentType.objects.get_for_model(MHLUser)
	elif OBJECT_TYPE_FLAG_ORG == object_type_flag:
		get_object_or_404(PracticeLocation, pk=object_id)
		object_type=ContentType.objects.get_for_model(PracticeLocation)

	if not object_type:
		raise ValueError

	return Favorite.objects.filter(object_type=object_type, \
				object_id=object_id, owner=owner).exists()

def _user_list_to_dict(role_user_list, check_practice=False):
	""" Change the Provider/OfficeStaff list to dict.
	:param role_user_list: is a list of Provider/OfficeStaff.
	:returns: dict
		the structure like this:
			{
				'mhluser_id': {
					'id': role_user's id,
					'pager': role_user's pager number,
					'current_practice': role_user's current practice,
					'has_practice': role_user has practice or not
				}
			}
	:raise: ValueError
	"""

	if role_user_list is None or not isinstance(role_user_list, (list, QuerySet)):
		raise ValueError

	user_dict = {}
	for role_user in role_user_list:
		if isinstance(role_user, (Provider, OfficeStaff)) and role_user.user:
			user_dict[role_user.user.id] = {
					'id': role_user.id, #Note: this id is Provider/OfficeStaff's id
					'pager': role_user.pager,
					'current_practice': role_user.current_practice,
					'has_practice': len(role_user.practices.filter(
						organization_type__id = RESERVED_ORGANIZATION_TYPE_ID_PRACTICE)) > 0
				}
	return user_dict
