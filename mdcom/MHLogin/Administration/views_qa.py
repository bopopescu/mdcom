
from django.conf import settings
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.core.files.base import File
from django.db.models.query_utils import Q

from MHLogin.Administration.forms_qa import GenerateUsersForm, ReGenerateKeyForm
from MHLogin.DoctorCom.IVR.models import VMBox_Config
from MHLogin.KMS.utils import create_default_keys, generate_keys_for_users
from MHLogin.KMS.models import OwnerPublicKey, UserPrivateKey
from MHLogin.MHLUsers.decorators import RequireAdministrator
from MHLogin.MHLUsers.models import MHLUser, Provider, Physician, NP_PA, \
	OfficeStaff, Office_Manager, Nurse, Dietician
from MHLogin.utils.constants import USER_TYPE_DOCTOR, USER_TYPE_NPPA, \
	USER_TYPE_MEDICAL_STUDENT, USER_TYPE_OFFICE_MANAGER, USER_TYPE_NURSE, \
	USER_TYPE_DIETICIAN
from MHLogin.utils.mh_logging import get_standard_logger
from MHLogin.utils.templates import get_context
from MHLogin.utils.FileHelper import get_absolute_path, getTempFilePath
from MHLogin.MHLPractices.models import PracticeLocation

logger = get_standard_logger('%s/Administration/views_qa.log' % 
	(settings.LOGGING_ROOT), 'Administration.views_qa', settings.LOGGING_LEVEL)


@RequireAdministrator
def qa_tools(request):
	context = get_context(request)
	if (settings.DEBUG):
		start = 0

		mobile_perm = Permission.objects.get_or_create(\
				codename='access_smartphone',
				name='Can use smartphone app', 
				content_type=ContentType.objects.get_for_model(MHLUser))

		MHLUser.objects.update(mobile_phone='')
		MHLUser.objects.update(phone='')
		for u in MHLUser.objects.all():
			u.mobile_phone = "%d%04d" % (800555, start)
			u.phone = "%d%04d" % (800333, start)
			start += 1

			if '@' in u.email:
				u.email = u.email.split('@')[0] + str(start) + '@suzhoukda.com'
			u.mobile_confirmed = True

			u.user_permissions.add(mobile_perm[0])
			u.save()
		return render_to_response('qa_tools/qa_tools_complete.html', context)
	return HttpResponseRedirect(reverse('MHLogin.Administration.views.home'))


@RequireAdministrator
def generate_users(request):
	if (not settings.DEBUG):
		return HttpResponseRedirect(reverse('MHLogin.Administration.views.home'))
	context = get_context(request)
	if (request.method == 'GET'):
		context["form"] = GenerateUsersForm()
		return render_to_response('qa_tools/genereate_users.html', context)
	else:
		form = GenerateUsersForm(request.POST)
		if form.is_valid():
			current_practice = form.cleaned_data["practices"]
			user_type = int(form.cleaned_data["user_types"])
			number = int(form.cleaned_data["number"])
			user_name_start = form.cleaned_data["user_name_start"]
			generate_user = None
			for i in range(number):
				username = "%s_%d" % (user_name_start, i)
				first_name = "%s_f_%d" % (user_name_start, i)
				last_name = "%s_f_%d" % (user_name_start, i)
				email = "%s@test.com" % (username)
				password = "demo"
				if USER_TYPE_DOCTOR == user_type \
					or USER_TYPE_NPPA == user_type \
					or USER_TYPE_MEDICAL_STUDENT == user_type:
					provider = Provider(
						username=username,
						first_name=first_name,
						last_name=last_name,
						email=email,
						email_confirmed=True,
						lat=current_practice.practice_lat,
						longit=current_practice.practice_longit,

						address1=current_practice.practice_address1,
						address2=current_practice.practice_address2,
						city=current_practice.practice_city,
						state=current_practice.practice_state,
						zip=current_practice.practice_zip,

						current_practice=current_practice,
						is_active=1,
						office_lat=current_practice.practice_lat,
						office_longit=current_practice.practice_longit,

						mdcom_phone="8004664411"
					)
					provider.save()
					provider.set_password(password)

					provider.practices.add(current_practice)
					provider.user_id = provider.pk
					provider.save()

					if USER_TYPE_DOCTOR == user_type:
						#Physician
						ph = Physician(user=provider)
						ph.save()
					elif USER_TYPE_NPPA == user_type:
						#NP/PA/Midwife
						np = NP_PA(user=provider)
						np.save()
					elif USER_TYPE_MEDICAL_STUDENT == user_type:
						ph = Physician(user=provider)
						ph.save()

					create_default_keys(provider.user, password)
					# Generating the user's voicemail box configuration
					config = VMBox_Config(pin='')
					config.owner = provider
					config.save()
					generate_user = provider
				elif USER_TYPE_OFFICE_MANAGER == user_type \
					or USER_TYPE_NURSE == user_type \
					or USER_TYPE_DIETICIAN == user_type:
					mhluser = MHLUser(
						username = username,
						first_name = first_name,
						last_name = last_name,
						email = email,
						email_confirmed = True,

						is_active = 1,
						address1 = current_practice.practice_address1,
						address2 = current_practice.practice_address2,
						city = current_practice.practice_city,
						state = current_practice.practice_state,
						zip = current_practice.practice_zip,
						lat = current_practice.practice_lat,
						longit = current_practice.practice_longit
					)
					mhluser.save()
					mhluser.set_password(password)

					staff = OfficeStaff(
								user=mhluser,
								current_practice=current_practice
							)
					staff.user = mhluser
					staff.current_practice = current_practice
					staff.save()

					staff.practices.add(current_practice)
					staff.save()

					if USER_TYPE_OFFICE_MANAGER == user_type:
						manager = Office_Manager(user=staff, practice=current_practice)
						manager.save()
					if USER_TYPE_NURSE == user_type:
						nurse = Nurse(user=staff)
						nurse.save()
					elif USER_TYPE_DIETICIAN == user_type:
						dietician = Dietician(user=staff)
						dietician.save()
					generate_user = mhluser
				log_str = 'Generate user %d: for %s' % (i, str(generate_user))
				logger.debug(log_str)
				print log_str

			return render_to_response('qa_tools/genereate_users_success.html', context)
		else:
			context["form"] = form
			return render_to_response('qa_tools/genereate_users.html', context)


@RequireAdministrator
def generate_photos(request):
	if (not settings.DEBUG):
		return HttpResponseRedirect(reverse('MHLogin.Administration.views.home'))
	context = get_context(request)
	# Generate photos for users who don't have photo
	users = MHLUser.objects.all()
	for user in users:
		if not user.photo or not user.photo.name:
			tf = generate_temp_file("/images/photos/user_test.jpg", user.username)
			user.photo.save("%s_%d.jpg" % (user.username, user.id), tf, save=True)
			user.save()
			log_str = 'Generate photo for %s' % (str(user))
			logger.debug(log_str)
			print log_str

	# Generate logos for organizations who don't have logo
	orgs = PracticeLocation.objects.all()
	for org in orgs:
		if not org.practice_photo or not org.practice_photo.name:
			tf = generate_temp_file("/images/photos/organization_test.jpg", org.practice_name)
			org.practice_photo.save("%s_%d.jpg" % (org.practice_name, org.id), tf, save=True)
			org.save()
			log_str = 'Generate photo for %s' % (str(org))
			logger.debug(log_str)
			print log_str
	return render_to_response('qa_tools/generate_photo_success.html', context)


def generate_temp_file(template_path, text):
	from PIL import Image
	from PIL import ImageDraw

	photo_path = get_absolute_path(template_path)
	img = Image.open(photo_path)
	tcolor = (255, 0, 0)
	text_pos = (5, 5)
	draw = ImageDraw.Draw(img)
	draw.text(text_pos, text, fill=tcolor)
	del draw
	temp_path = getTempFilePath("temp_file_55488949441.png")
	img.save(temp_path)
	temp_file = open(temp_path, "rb")
	tf = File(temp_file)
	return tf


@RequireAdministrator
def re_generate_key(request):
	if (not settings.DEBUG):
		return HttpResponseRedirect(reverse('MHLogin.Administration.views.home'))
	context = get_context(request)
	if (request.method == 'GET'):
		context["form"] = ReGenerateKeyForm()
		return render_to_response('qa_tools/re_genereate_key.html', context)
	else:
		form = ReGenerateKeyForm(request.POST)
		if form.is_valid():
			user_id_from = form.cleaned_data["user_id_from"]
			user_id_to = form.cleaned_data["user_id_to"]
			username = form.cleaned_data["username"]
			handled_users = []

			q_t = Q()
			if username:
				q_t = Q(username=username)
			elif user_id_from is not None or user_id_to is not None:
				if user_id_from is not None:
					q_t = Q(pk__gte=user_id_from)
				if user_id_to is not None:
					q_t = Q(pk__lte=user_id_to)

			users = MHLUser.objects.filter(q_t)
			for user in users:
				UserPrivateKey.objects.filter(user=user).delete()
				OwnerPublicKey.objects.filter_pubkey(owner=user).delete()
				handled_users.append({
					'username': user.username,
					'first_name': user.first_name,
					'last_name': user.last_name,
				})
			generate_keys_for_users(users=users)
			context["count"] = len(handled_users)
			context["handled_users"] = handled_users
			return render_to_response('qa_tools/re_genereate_key_success.html', context)
		else:
			context["form"] = form
			return render_to_response('qa_tools/re_genereate_key.html', context)
