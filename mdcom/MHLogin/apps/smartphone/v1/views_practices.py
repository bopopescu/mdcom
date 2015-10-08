import json
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest
from django.utils.translation import ugettext as _

from MHLogin.MHLPractices.models import PracticeLocation
from MHLogin.MHLPractices.utils import get_practices_by_position
from MHLogin.MHLUsers.models import Office_Manager
from MHLogin.apps.smartphone.v1.decorators import AppAuthentication
from MHLogin.utils import ImageHelper
from MHLogin.MHLFavorite.utils import is_favorite, OBJECT_TYPE_FLAG_ORG,\
	get_my_favorite_ids


@AppAuthentication
def local_office(request):
	role_user = request.role_user
	response = {
		'data': {},
		'warnings': {},
	}
	current_user_mobile = role_user.user.mobile_phone
	current_practice = role_user.current_practice
	if current_practice:
		object_ids = get_my_favorite_ids(request.user, object_type_flag=OBJECT_TYPE_FLAG_ORG)
		practices = list(get_practices_by_position(current_practice.practice_lat, 
			current_practice.practice_longit).only('practice_name', 'id'))
		managed_prac_ids = list(Office_Manager.active_objects.all().\
			values_list("practice__id", flat=True))
		practice_list = []
		for p in practices:
			practice_photo = ImageHelper.get_image_by_type(
				p.practice_photo, "Large", 'Practice', 'img_size_practice')
			practice_photo_m = ImageHelper.get_image_by_type(
				p.practice_photo, "Middle", 'Practice', 'img_size_practice')
			has_manager = p.id in managed_prac_ids
			practice_list.append({
					'id': p.id,
					'practice_photo': practice_photo,
					'practice_photo_m': practice_photo_m,
					'practice_name': p.practice_name,
					'has_mobile': (bool(p.backline_phone) or bool(p.practice_phone))\
									and bool(current_user_mobile)\
									and settings.CALL_ENABLE,
					'has_manager': has_manager,
					'is_favorite': p.id in object_ids
				})
		response['data']['practices'] = sorted(practice_list, 
				key=lambda item: "%s" % (item['practice_name'].lower())) 
	else:
		response['data']['practices'] = []

	return HttpResponse(content=json.dumps(response), mimetype='application/json')


@AppAuthentication
def practice_info(request, practice_id):
	role_user = request.role_user
	current_user_mobile = role_user.user.mobile_phone
	try:
		practice = PracticeLocation.objects.get(pk=practice_id)
		practice_photo = ImageHelper.get_image_by_type(
			practice.practice_photo, "Large", 'Practice', 'img_size_practice')
		practice_photo_m = ImageHelper.get_image_by_type(
			practice.practice_photo, "Middle", 'Practice', 'img_size_practice')
		has_manager = Office_Manager.active_objects.filter(practice__id=practice_id).exists()
		response = {
			'data': {
				'id': practice.id,
				'practice_name': practice.practice_name,
				'practice_photo': practice_photo,
				'practice_photo_m': practice_photo_m,
				'practice_address1': practice.practice_address1,
				'practice_address2': practice.practice_address2,
				'practice_city': practice.practice_city,
				'practice_state': practice.practice_state,
				'practice_zip': practice.practice_zip,
				'mdcom_phone': practice.mdcom_phone,
				'has_mobile': (bool(practice.backline_phone)\
								or bool(practice.practice_phone))\
								and bool(current_user_mobile) and settings.CALL_ENABLE,
				'has_manager': has_manager,
				'is_favorite': is_favorite(request.user, OBJECT_TYPE_FLAG_ORG, practice.id)
			},
			'warnings': {},
		}
		return HttpResponse(content=json.dumps(response), mimetype='application/json')
	except PracticeLocation.DoesNotExist:
		err_obj = {
			'errno': 'PF003',
			'descr': _('Requested practice not found.'),
		}
		return HttpResponseBadRequest(content=json.dumps(err_obj), mimetype='application/json')
