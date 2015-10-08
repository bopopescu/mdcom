import datetime
import json
import os

from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotFound
from django.shortcuts import render_to_response, get_object_or_404
from django.utils.translation import ugettext as _

from MHLogin.DoctorCom.IVR.forms import VMBox_ConfigForm, PinChangeForm
from MHLogin.DoctorCom.IVR.models import get_new_pin_hash, VMBox_Config
from MHLogin.MHLPractices.forms import PreferenceForm, PreferenceProviderForm
from MHLogin.MHLUsers.forms import ProviderForm, UserForm, OfficeStaffForm, \
	PhysicianForm, BrokerForm, ChangePasswordForm, SecurityQuestionsForm, \
	CallForwardForm, UpdateSecurityForm, BrokerUserForm
from MHLogin.MHLUsers.models import SecurityQuestions, Broker, Provider, NP_PA, \
	Nurse, OfficeStaff, MHLUser
from MHLogin.MHLUsers.utils import change_pass, answerToHash, \
	has_mhluser_with_email, has_mhluser_with_mobile_phone,get_fullname
from MHLogin.utils import ImageHelper
from MHLogin.utils.constants import LANGUAGE, RESERVED_ORGANIZATION_TYPE_ID_PRACTICE
from MHLogin.utils.mh_logging import get_standard_logger
from MHLogin.utils.templates import get_context
from MHLogin.utils.timeFormat import OLD_TIME_ZONES_MIGRATION
from MHLogin.MHLOrganization.utils import get_other_organizations

# Setting up logging
logger = get_standard_logger('%s/MHLUsers/views.log' % (settings.LOGGING_ROOT),
							'MHLUsers.views', settings.LOGGING_LEVEL)


def changepin(request):
	context = get_context(request)
	if (request.method == 'POST'):
		form = PinChangeForm(request.POST)
		form.user = request.user
		if (form.is_valid()):
			if 'Provider' in request.session['MHL_Users']:			
				provider = Provider.objects.get(user__id=request.user.id)
				config = provider.vm_config.get()
				config.change_pin(request, new_pin=form.cleaned_data['pin1'])
				return render_to_response('Profile/changepinconfirmed.html', context)
			elif 'Broker' in request.session['MHL_Users']:			
				broker = Broker.objects.get(user__id=request.user.id)
				config = broker.vm_config.get()
				config.change_pin(request, new_pin=form.cleaned_data['pin1'])
				return render_to_response('Profile/changepinconfirmed.html', context)
			#add by xlin 121119 to fix bug 855 that practice mgr can change pin
			elif 'OfficeStaff' in request.session['MHL_Users']:
				os = OfficeStaff.objects.get(user__id=request.user.id)
				practice = os.current_practice
				practice.pin = get_new_pin_hash(form.cleaned_data['pin1'])
				practice.save()
				return render_to_response('Profile/practicechangepinconfirmed.html', context)

		context['form'] = form
	if (not 'form' in context):
		context['form'] = PinChangeForm()

	if 'OfficeStaff' in request.session['MHL_Users']:
		return render_to_response('Profile/practicechangepin.html', context)

	return render_to_response('Profile/changepin.html', context)


def profile_view(request):
	if ('Provider' in request.session['MHL_Users']):
		return profile_view_provider(request, request.session['MHL_Users']['Provider'])
	if ('OfficeStaff' in request.session['MHL_Users']):
		return profile_view_staff(request, request.session['MHL_Users']['OfficeStaff'])
	if ('Broker' in request.session['MHL_Users']):
		return profile_view_broker(request, request.session['MHL_Users']['Broker'])
	if ('Salesperson' in request.session['MHL_Users']):
		return HttpResponseRedirect(reverse('MHLogin.MHLUsers.Sales.views.profile'))
	# Patient access disabled
	# elif (user_is_patient(request.user)):
	#	 return profile_view_patient(request)
	else:
		# Return 404 with message, currently ACL Rule:
		# ('^/Profile', 'ACCEPT', '*'),
		return HttpResponseNotFound(_('User is of unknown type'))


def profile_view_broker(request, broker):
	context = get_context(request)
	context['profile'] = broker
	states_of_licensure = broker.licensure_states.all()
	states_of_licensure = [i.state for i in states_of_licensure]

	context['states_of_licensure'] = ', '.join(states_of_licensure)

	context['photo'] = ImageHelper.get_image_by_type(broker.user.photo, 'Middle', 'Broker') 

	context['time_setting']=broker.user.get_time_setting_display()
	context['time_zone']=broker.user.get_time_zone_display()
	context['language'] = LANGUAGE[settings.FORCED_LANGUAGE_CODE]
	context['fullname'] = get_fullname(broker)

	return render_to_response('Profile/profile_view_broker.html', context)


def profile_view_staff(request, staff):
	context = get_context(request)

	context['profile'] = staff
	context['sites'] = staff.sites

	#add by xlin 20120718
	nurse = Nurse.objects.filter(user=staff)
	context['fullname'] = get_fullname(staff)
	if nurse:
		context['photo'] = ImageHelper.get_image_by_type(
					staff.user.photo, size='Middle', type='Nurse')
	else:
		context['photo'] = ImageHelper.get_image_by_type(
					staff.user.photo, size='Middle', type='Staff')

	context['time_setting']=staff.user.get_time_setting_display()
	context['time_zone']=staff.user.get_time_zone_display()
	context['language'] = LANGUAGE[settings.FORCED_LANGUAGE_CODE]

	return render_to_response('Profile/profile_view_staff.html', context)


def profile_view_provider(request, provider):
	context = get_context(request)

	context['profile'] = provider
	context['sites'] = context['profile'].sites
	context['practices'] = provider.practices.filter(\
			organization_type__pk=RESERVED_ORGANIZATION_TYPE_ID_PRACTICE)
	# Other Organization
	context['other_orgs'] = get_other_organizations(provider.id)

	user = request.session['MHL_Users']['Provider']

	states_of_licensure = user.licensure_states.all()
	states_of_licensure = [i.state for i in states_of_licensure]

	context['states_of_licensure'] = ', '.join(states_of_licensure)
	context['skill'] = user.skill
	context['fullname'] = get_fullname(provider)
	if user.user.refer_forward == 1:
		context['refer_forward'] = _('Both office manager and I get a copy of referrals')
	else:
		context['refer_forward'] = _('Send Referrals to my office manager only')

	if ('Physician' in request.session['MHL_Users']):
		phys = request.session['MHL_Users']['Physician']
		clinical_clerk = phys.user.clinical_clerk
		context['physician'] = not clinical_clerk
		context['user'] = phys.user

		context['photo'] = ImageHelper.get_image_by_type(phys.user.photo, 
								size='Middle', type='Provider')
		context['specialty'] = ''
		context['accepting_new_patients'] = ''
		if (not clinical_clerk):
			context['specialty'] = str(phys.get_specialty_display())
			if (phys.accepting_new_patients):
				context['accepting_new_patients'] = _('Yes')
			else:
				context['accepting_new_patients'] = _('No')
			context['staff_type'] = str(phys.get_staff_type_display())
	if ('NP_PA' in request.session['MHL_Users']):
		np_pas = get_object_or_404(NP_PA, user=request.user)

		context['photo'] = ImageHelper.get_image_by_type(np_pas.user.photo, 
								size='Middle', type='Provider')
		context['user'] = np_pas.user


	context['time_setting']=provider.user.get_time_setting_display()
	context['time_zone']=provider.user.get_time_zone_display()
	context['language'] = LANGUAGE[settings.FORCED_LANGUAGE_CODE]
	return render_to_response('Profile/profile_view.html', context)


def profile_edit(request):
	if ('Provider' in request.session['MHL_Users']):
		return profile_edit_provider(request)
	if ('OfficeStaff' in request.session['MHL_Users']):
		return profile_edit_office_staff(request)
	if ('Broker' in request.session['MHL_Users']):
		return profile_edit_broker(request)
	# Patient access disabled
	# elif (user_is_patient(request.user)):
	#	 return profile_edit_patient(request)
	else:
		# Return 404 with message, currently ACL Rule:
		# ('^/Profile', 'ACCEPT', '*'),
		return HttpResponseNotFound(_('User is of unknown type'))


def profile_edit_broker(request):
	broker = request.session['MHL_Users']['Broker']
	context = get_context(request)
	#context['all_providers_box'] = box_all_providers()
	if (request.method == "POST"):
		old_url = None
		if broker.user.photo:
			old_url = broker.user.photo.name
		# First, deal with user form stuff
		if("old_password" in request.POST):
			password_form = ChangePasswordForm(broker.user, request.POST)
			broker_form = BrokerForm(instance=broker)
			user_form = BrokerUserForm(instance=broker.user)
		else:
			broker_form = BrokerForm(request.POST, instance=broker)
			user_form = BrokerUserForm(request.POST, request.FILES, instance=broker.user)
			password_form = ChangePasswordForm(broker.user)
			preference_form = PreferenceForm(request.POST, instance=broker.user)
			#user_form.save(commit=False)

		context['user'] = broker
		context['user_form'] = user_form
		context['broker_form'] = broker_form
		context['password_form'] = password_form
		context['preference_form'] = preference_form

		if(password_form.is_valid()):
			if(password_form.cleaned_data['old_password']):
				response = HttpResponseRedirect(reverse('MHLogin.MHLUsers.views.profile_view'))
				return change_pass(password_form, request, response)

		if (broker_form.is_valid() and user_form.is_valid() and preference_form.is_valid()):
			broker_form.save()
			user_form.save()
			mhluser = MHLUser.objects.get(id=broker.user.id)
			mhluser.time_setting = preference_form.cleaned_data['time_setting']
			mhluser.time_zone = preference_form.cleaned_data['time_zone']
			mhluser.save()

			context = get_context(request)
			new_url = None
			if broker.user.photo:
				new_url = broker.user.photo.name
			ImageHelper.generate_image(old_url, new_url)
			return HttpResponseRedirect(reverse('MHLogin.MHLUsers.views.profile_view'))
	else:
		context['user'] = broker
		context['user_form'] = BrokerUserForm(instance=broker.user)
		context['broker_form'] = BrokerForm(instance=broker)
		context['password_form'] = ChangePasswordForm(user=broker.user)
		context['preference_form'] = PreferenceForm(initial={'time_setting':
				broker.user.time_setting if broker.user.time_setting else 0,
						'time_zone': broker.user.time_zone})

	context['mobile_required'] = True
	from django import conf
	context['Language'] = LANGUAGE[conf.settings.FORCED_LANGUAGE_CODE]
	return render_to_response('Profile/profile_edit.html', context)


def profile_edit_provider(request):
	""" This function allows for physicians to edit their profiles. Note that it displays 
		elements of two forms for a provider profile page:
		1. Provider form
		2. Provider type (Physician, Nurse, etc.) form
	"""
	context = get_context(request)

	# First, get the relevant user's profile. Everything requires it.
	provider = Provider.objects.filter(id=request.user.id)
	if (provider.count() != 1):
		raise Exception(_('Incorrect number of provider objects returned: ') + str(provider.count()))
	provider = provider[0]

	vmconfig_obj = provider.vm_config.get()

	phys = None
	if ('Physician' in request.session['MHL_Users']):
		phys = request.session['MHL_Users']['Physician']
	context['physician'] = phys

	if (request.method == "POST"):
		old_url = None
		if provider.photo:
			old_url = provider.photo.name
		settings_form = VMBox_ConfigForm(request.POST, instance=vmconfig_obj)
		provider_form = ProviderForm(data=request.POST, files=request.FILES, instance=provider)

		preference_form = PreferenceProviderForm(request.POST, instance=provider.user)

		if (phys):
			physician_form = PhysicianForm(request.POST, instance=phys)
		else:
			physician_form = None

		if (physician_form):
			physician_form_validity = physician_form.is_valid()
		else:
			physician_form_validity = True

		if (provider_form.is_valid() and physician_form_validity and \
				settings_form.is_valid() and preference_form.is_valid()):
			provider = provider_form.save(commit=False)
			provider.lat = provider_form.cleaned_data['lat']
			provider.longit = provider_form.cleaned_data['longit']
			provider.licensure_states = provider_form.cleaned_data['licensure_states']
			#add by xlin in 20120611 for issue897 that add city, address, zip into database
			provider.address1 = provider_form.cleaned_data['address1']
			provider.address2 = provider_form.cleaned_data['address2']
			provider.city = provider_form.cleaned_data['city']
			provider.state = provider_form.cleaned_data['state']
			provider.zip = provider_form.cleaned_data['zip']
			provider.save()
			mhluser = MHLUser.objects.get(id=provider.user.id)
			mhluser.time_setting = preference_form.cleaned_data['time_setting']
			mhluser.time_zone = preference_form.cleaned_data['time_zone']
			mhluser.refer_forward = preference_form.cleaned_data['refer_forward']
			mhluser.save()
			if (physician_form):
				physician_form.save()
			settings_form.save()

			new_url = provider.photo.name if provider.photo else None
			#thumbnail creating code moved from here to save method of provider mode
			#use common method to generate
			ImageHelper.generate_image(old_url, new_url)
			if not provider_form.non_field_warnings:
				return HttpResponseRedirect(reverse('MHLogin.MHLUsers.views.profile_view'))
			else:
				context['user_form'] = provider_form
				context['physician_form'] = physician_form
				context['settings_form'] = settings_form
				context['preference_form'] = preference_form
		else:  # if not (user_form.is_valid() and provider_form):
			context['user_form'] = provider_form
			context['physician_form'] = physician_form
			context['settings_form'] = settings_form
			context['preference_form'] = preference_form

	else:  # if (request.method != "POST"):
		context['user_form'] = ProviderForm(instance=Provider.objects.get(id=request.user.id))
		context['settings_form'] = VMBox_ConfigForm(instance=vmconfig_obj, initial={'pin': ''})
		context['preference_form'] = PreferenceProviderForm(initial={'time_setting':
				provider.user.time_setting if provider.user.time_setting else 0,
						'time_zone': provider.user.time_zone,
						'refer_forward': provider.user.refer_forward})
		if (phys):
			context['physician_form'] = PhysicianForm(instance=phys)

	from django import conf
	context['Language'] = LANGUAGE[conf.settings.FORCED_LANGUAGE_CODE]
	context['mobile_required'] = True
	context['isProvider'] = True
	return render_to_response('Profile/profile_edit.html', context)


def profile_edit_office_staff(request):
	""" This function allows for ofice staff to edit their profiles.
	"""
	# First, get the relevant user's profile. Everything requires it.
	context = get_context(request)
	staff = request.session['MHL_Users']['OfficeStaff']

	if (not staff.vm_config.count()):
		config = VMBox_Config()
		config.owner = staff
		config.save()

	vmconfig_obj = staff.vm_config.get()
	#context['all_providers_box'] = box_all_providers()
	if (request.method == "POST"):
		old_url = None
		if staff.user.photo:
			old_url = staff.user.photo.name

		# First, deal with user form stuff
		if("old_password" in request.POST):
			password_form = ChangePasswordForm(staff.user, request.POST)
			# set these here so they still display properly when we get form errors 
			# in the password form
			staff_form = OfficeStaffForm(instance=staff)
			user_form = UserForm(instance=staff.user)
		else:
			staff_form = OfficeStaffForm(request.POST, instance=staff)
			user_form = UserForm(request.POST, request.FILES, instance=staff.user)
			password_form = ChangePasswordForm(staff.user)
			settings_form = VMBox_ConfigForm(request.POST, instance=vmconfig_obj)
			preference_form = PreferenceForm(request.POST, instance=staff.user)
		if user_form.is_valid():
			user_form.save(commit=False)
			context['user'] = staff
			context['user_form'] = user_form
			context['staff_form'] = staff_form
			context['password_form'] = password_form

			if(password_form.is_valid()):
				if(password_form.cleaned_data['old_password']):
					response = HttpResponseRedirect(reverse('MHLogin.MHLUsers.views.profile_view'))
					return change_pass(password_form, request, response)

			if (staff_form.is_valid() and user_form.is_valid() and settings_form.is_valid() \
					and preference_form.is_valid()):
				staff_form.save()
				user_form.save()
				settings_form.save()
				mhluser = MHLUser.objects.get(id=staff.user.id)
				mhluser.time_setting = preference_form.cleaned_data['time_setting']
				mhluser.time_zone = preference_form.cleaned_data['time_zone']
				mhluser.save()

				new_url = None
				if staff.user.photo:
					new_url = staff.user.photo.name
				ImageHelper.generate_image(old_url, new_url)

				return HttpResponseRedirect(reverse('MHLogin.MHLUsers.views.profile_view'))
		else:
			context['user_form'] = user_form
			context['staff_form'] = staff_form
			context['settings_form'] = settings_form
			context['preference_form'] = preference_form
	else:
		context['user'] = staff
		context['user_form'] = UserForm(instance=staff.user)
		context['staff_form'] = OfficeStaffForm(instance=staff)
		context['password_form'] = ChangePasswordForm(user=staff.user)
		context['settings_form'] = VMBox_ConfigForm(instance=vmconfig_obj, 
									initial={'pin': ''})
		context['preference_form'] = PreferenceForm(initial={'time_setting':
			staff.user.time_setting if staff.user.time_setting else 0,
					'time_zone': staff.user.time_zone})

	from django import conf
	context['Language'] = LANGUAGE[conf.settings.FORCED_LANGUAGE_CODE]
	context['mobile_required'] = False
	context['isStaff'] = True
	return render_to_response('Profile/profile_edit.html', context)


def change_password(request, redirect_view='MHLogin.MHLUsers.views.profile_view'):
	context = get_context(request)
	if (request.method == "POST"):
		# Deal with a submitted form.
		form = ChangePasswordForm(
						request.session['MHL_Users']['MHLUser'], request.POST)
		if (form.is_valid()):
			response = HttpResponseRedirect(reverse(form.cleaned_data['redirect_view']))
			change_pass(form, request, response)
			form.user.force_pass_change = False
			form.user.save()
			return response
	else:
		form = ChangePasswordForm(request.session['MHL_Users']['MHLUser'], 
								initial={'redirect_view': redirect_view})

	context['form'] = form
	return render_to_response('Profile/password_change.html', context)


def security_questions(request):
	#add this check to prevent load this page using url
	if 'password_is_valid' in request.session and  request.session['password_is_valid']:
		context = get_context(request)
		context['error'] = ''
		context['timeout'] = ''
		context['cookie_is_valid'] = 0
		records = SecurityQuestions.objects.filter(user=request.user)
		if(datetime.datetime.now() - request.session['question_timeout']).seconds > 18 * 60:
			return HttpResponseRedirect(reverse('MHLogin.MHLUsers.views.update_security_questions'))
		else:
			if(request.POST):
				form = SecurityQuestionsForm(request.POST)
				if(form.is_valid()):

					security_answer1 = answerToHash(form.cleaned_data['security_answer1'])
					security_answer2 = answerToHash(form.cleaned_data['security_answer2'])
					security_answer3 = answerToHash(form.cleaned_data['security_answer3'])

					if len(records) == 0:
						record = SecurityQuestions(user=request.user,
							security_question1=form.cleaned_data['selected_question1'],
							security_question2=form.cleaned_data['selected_question2'],
							security_question3=form.cleaned_data['selected_question3'],
							security_answer1=security_answer1,
							security_answer2=security_answer2,
							security_answer3=security_answer3)
					else:
						record = records[0]
						record.security_question1 = form.cleaned_data['selected_question1']
						record.security_question2 = form.cleaned_data['selected_question2']
						record.security_question3 = form.cleaned_data['selected_question3']
						record.security_answer1 = security_answer1
						record.security_answer2 = security_answer2
						record.security_answer3 = security_answer3

					record.save()
					#request.session['password_is_valid'] = False
					return HttpResponseRedirect('/')
				else:
					context['cookie_is_valid'] = 1
			else:
				error = ''
				if len(records) != 0:
					error = _('Your old security questions are not shown for security reasons.')
				context['error'] = error
				form = SecurityQuestionsForm()
			context['form'] = form
		return render_to_response('Profile/profile_security.html', context)
	else:
		return HttpResponseRedirect(reverse('MHLogin.MHLUsers.views.update_security_questions'))


def update_security_questions(request):
	context = get_context(request)
	context['error'] = ''
	form = UpdateSecurityForm()
	if request.method == 'POST':
		form = UpdateSecurityForm(request.POST)
		if form.is_valid():
			#check whether password is valid
			user = authenticate(username=request.user, password=form.cleaned_data['password'])
			if user:
				request.session['password_is_valid'] = True
				request.session['question_timeout'] = datetime.datetime.now()
				return HttpResponseRedirect(reverse('MHLogin.MHLUsers.views.security_questions'))
			else:
				context['error'] = _('The entered password was incorrect.')
				#return HttpResponseRedirect(reverse('MHLogin.MHLUsers.views.profile_view'))
	context['form'] = form
	return render_to_response('Profile/update_profile_security.html', context)


def mdcom_forwarding(request):
	if (request.POST):
		if ('Broker' in request.session['MHL_Users']):
			provider = get_object_or_404(Broker, user=request.user)
		else:
			provider = get_object_or_404(Provider, user=request.user)
		form = CallForwardForm(request.POST)
		if(form.is_valid()):
			provider.forward_voicemail = form.cleaned_data['forward']
			provider.save()
	return HttpResponse(json.dumps({'fwd_setting': 
			provider.get_forward_voicemail_display()}), mimetype='application/json')


def anssvc_forwarding(request):
	if (request.POST):
		provider = get_object_or_404(Provider, user=request.user)
		form = CallForwardForm(request.POST)
		if(form.is_valid()):
			provider.forward_anssvc = form.cleaned_data['forward']
			provider.save()
	return HttpResponse(json.dumps({'fwd_setting':
			provider.get_forward_anssvc_display()}), mimetype='application/json')


def check_user_name(request, userName):
	isExist = 0
	user = User.objects.filter(username=userName)
	if user.exists():
		isExist = 1
	return HttpResponse(isExist)


def unique_check(request):
	"""
		Validate user's email/mobile_phone's uniqueness.
		If the email is unique, the email_unique's value is True, or it's False.
		If the mobile_phone is unique, the mobile_phone_unique's value is True, or it's False.
	"""
	result = dict()
	if (request.POST):
		email = request.POST["email"]
		mobile_phone = request.POST["mobile_phone"]

		result = {
				'email_unique': not has_mhluser_with_email(email, request.user.id),
				'mobile_phone_unique': not has_mhluser_with_mobile_phone(
										mobile_phone, request.user.id)
			}

	return HttpResponse(json.dumps(result), mimetype='application/json')


def profile_preference(request):
	context = get_context(request)
	mhluser = request.session['MHL_Users']['MHLUser']

	if request.method == 'POST':
		if 'Provider' in request.session['MHL_Users']:
			form = PreferenceProviderForm(request.POST, instance=mhluser)
		else:
			form = PreferenceForm(request.POST, instance=mhluser)
		if form.is_valid():
			form.save()
			# refresh context after saving
			context = get_context(request)
			context['flag'] = 1
	else:
		if 'Provider' in request.session['MHL_Users']:
			form = PreferenceProviderForm(initial={'time_setting':
				mhluser.time_setting if mhluser.time_setting else 0,
						'time_zone': mhluser.time_zone,
						'refer_forward': mhluser.refer_forward})
		else:
			form = PreferenceForm(initial={'time_setting':
				mhluser.time_setting if mhluser.time_setting else 0,
						'time_zone': mhluser.time_zone})

		context['flag'] = 0
	context['form'] = form
	from django import conf
	context['Language'] = LANGUAGE[conf.settings.FORCED_LANGUAGE_CODE]

	practice = context['current_practice']
	context['current_practice_time_zone'] = ''
	context['user_old_time_zone'] = mhluser.time_zone
	if practice and practice.time_zone:
		try:
			context['current_practice_time_zone'] = \
					OLD_TIME_ZONES_MIGRATION[practice.time_zone]
		except:
			pass
	return render_to_response('Profile/profile_preference.html', context)
