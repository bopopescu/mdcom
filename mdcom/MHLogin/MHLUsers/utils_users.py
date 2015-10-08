# -*- coding: utf-8 -*-
'''
Created on 2012-10-08

@author: mwang
'''
import random
import string
import time
import uuid

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

from MHLogin.DoctorCom.IVR.models import VMBox_Config
from MHLogin.KMS.utils import create_default_keys
from MHLogin.MHLPractices.models import AccountActiveCode
from MHLogin.MHLUsers.forms import CreateProviderForm, CreateMHLUserForm,\
	CreateOfficeStaffForm, CreateBrokerMHLUserForm, CreateBrokerForm
from MHLogin.MHLUsers.models import Physician, NP_PA, Nurse, Dietician
from MHLogin.utils.constants import USER_TYPE_DOCTOR, USER_TYPE_NPPA,\
	USER_TYPE_MEDICAL_STUDENT, USER_TYPE_NURSE, USER_TYPE_DIETICIAN
from MHLogin.MHLUsers.utils import get_practice_org


def createNewProvider(provider_form, current_user):
	if isinstance(provider_form, CreateProviderForm):
		current_practice = current_user.current_practice
		provider = provider_form.save(commit=False)
		provider.lat = provider_form.cleaned_data['lat']
		provider.longit = provider_form.cleaned_data['longit']

		provider.address1 = provider_form.cleaned_data['address1']
		provider.address2 = provider_form.cleaned_data['address2']
		provider.city = provider_form.cleaned_data['city']
		provider.state = provider_form.cleaned_data['state']
		provider.zip = provider_form.cleaned_data['zip']

		provider.current_practice = get_practice_org(current_practice)
		provider.is_active = 0
		provider.office_lat = 0.0 if not provider.office_lat else provider.office_lat
		provider.office_longit = 0.0 if not provider.office_longit else provider.office_longit
		provider.save()

		if current_practice:
			provider.practices.add(current_practice)
		provider.user_id = provider.pk
		provider.save()

		user_type = int(provider_form.cleaned_data['user_type'])

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

		# TESTING_KMS_INTEGRATION
		create_default_keys(provider.user)

		# Generating the user's voicemail box configuration
		config = VMBox_Config(pin='')
		config.owner = provider
		config.save()

		sendAccountActiveCode(provider_form, user_type, current_user)
	else:
		raise TypeError


def createNewOfficeStaff(mhluser_form, staff_form, current_user):
	if isinstance(mhluser_form, CreateMHLUserForm) and \
			isinstance(staff_form, CreateOfficeStaffForm):
		current_practice = current_user.current_practice
		mhluser = mhluser_form.save(commit=False)
		mhluser.is_active = 0
		if current_practice:
			mhluser.address1 = current_practice.practice_address1
			mhluser.address2 = current_practice.practice_address2
			mhluser.city = current_practice.practice_city
			mhluser.state = current_practice.practice_state
			mhluser.zip = current_practice.practice_zip
			mhluser.lat = current_practice.practice_lat
			mhluser.longit = current_practice.practice_longit
		else:
			mhluser.lat = 0.0
			mhluser.longit = 0.0
		mhluser.save()

		staff = staff_form.save(commit=False)
		staff.user = mhluser
		staff.current_practice = current_practice
		staff.save()

		if current_practice:
			staff.practices.add(current_practice)
		staff.save()

		staff_type = int(staff_form.cleaned_data['staff_type'])

		if USER_TYPE_NURSE == staff_type:
			nurse = Nurse(user=staff)
			nurse.save()
		elif USER_TYPE_DIETICIAN == staff_type:
			dietician = Dietician(user=staff)
			dietician.save()

		# TESTING_KMS_INTEGRATION
		create_default_keys(mhluser)

		sendAccountActiveCode(mhluser_form, 101, current_user)

	else:
		raise TypeError


def createNewBroker(mhluser_form, broker_form, current_user):
	if isinstance(mhluser_form, CreateBrokerMHLUserForm) and \
			isinstance(broker_form, CreateBrokerForm):
#		current_practice = current_user.current_practice
		mhluser = mhluser_form.save(commit=False)
		mhluser.is_active = 0
		mhluser.address1 = mhluser_form.cleaned_data['address1']
		mhluser.address2 = mhluser_form.cleaned_data['address2']
		mhluser.city = mhluser_form.cleaned_data['city']
		mhluser.state = mhluser_form.cleaned_data['state']
		mhluser.zip = mhluser_form.cleaned_data['zip']
		mhluser.lat = mhluser_form.cleaned_data['lat']
		mhluser.longit = mhluser_form.cleaned_data['longit']
		mhluser.save()

		broker = broker_form.save(commit=False)
		broker.user = mhluser
		broker.office_lat = 0.0 if not broker.office_lat else broker.office_lat
		broker.office_longit = 0.0 if not broker.office_longit else broker.office_longit
		broker.save()

		# TESTING_KMS_INTEGRATION
		create_default_keys(mhluser)

		# Generating the user's voicemail box configuration
		config = VMBox_Config(pin='')
		config.owner = broker
		config.save()

		sendAccountActiveCode(mhluser_form, 300, current_user)
	else:
		raise TypeError


def sendAccountActiveCode(form, userType, current_user):
	if isinstance(form, CreateProviderForm) or isinstance(form, CreateMHLUserForm) or \
			isinstance(form, CreateBrokerMHLUserForm):
		current_practice = current_user.current_practice
		username = form.cleaned_data['username']
		recipient_email = form.cleaned_data['email']
		first_name = form.cleaned_data['first_name']
		last_name = form.cleaned_data['last_name']

		code = getNewCreateCode(username)
		log = AccountActiveCode(code=code,
			sender=current_user.user.pk,
			recipient=recipient_email,
			#userType=int(request.POST['staff_type']),
			userType=userType,
			practice=current_practice)
		log.save()

		emailContext = dict()
		emailContext['username'] = username
		emailContext['code'] = code
		emailContext['email'] = recipient_email
		emailContext['name'] = first_name + ' ' + last_name
		emailContext['sender'] = current_user
		emailContext['address'] = settings.SERVER_ADDRESS
		emailContext['protocol'] = settings.SERVER_PROTOCOL
		msgBody = render_to_string('Staff/emailText.html', emailContext)
		send_mail('DoctorCom Activation', msgBody, settings.SERVER_EMAIL,\
				[recipient_email, ], fail_silently=False)
	else:
		raise TypeError


def getNewCreateCode(username):
	ctime = str(time.time())
	ctime = string.replace(ctime, '.', '')
	chars = username + ctime + uuid.uuid4().hex[0:4]
	code = r''.join([random.choice(chars) for x in range(50)])
	return code

