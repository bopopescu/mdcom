
import datetime
import time

from django import forms
from django.http import HttpResponseRedirect
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

from MHLogin.MHLUsers.forms import NewStaffMHLUserForm, NewManagerMHLUserForm, \
		NewProviderForm, MSG_USERNAME_EXIST
from MHLogin.MHLUsers.models import OfficeStaff, Office_Manager, Provider, MHLUser, \
	Broker, States, Physician, NP_PA, Nurse, Dietician
from MHLogin.utils.constants import SPECIALTY_CHOICES, PROVIDER_TYPE_CHOICES, \
	BROKER_TYPE_CHOICES, STAFF_TYPE_CHOICES, RESERVED_ORGANIZATION_TYPE_ID_PRACTICE, \
	RESERVED_ORGANIZATION_ID_DOCTORCOM
from MHLogin.utils.wizard import FormWizard
from MHLogin.utils.geocode import geocode2
from MHLogin.Invites.models import Invitation

from MHLogin.MHLCallGroups.models import CallGroup, CallGroupMember

from MHLogin.MHLPractices.forms import PracticeProfileForm
from MHLogin.MHLPractices.models import PracticeLocation, OrganizationRelationship
from MHLogin.KMS.utils import create_default_keys
from MHLogin.DoctorCom.IVR.models import VMBox_Config
from MHLogin.MHLSites.models import Site
from django.utils.translation import ugettext_lazy as _

from MHLogin.DoctorCom.NumberProvisioner.forms import LocalNumberForm
from MHLogin.DoctorCom.NumberProvisioner.utils import twilio_ConfigureProviderLocalNumber
from django.contrib.contenttypes.models import ContentType
from MHLogin.MHLUsers.utils import check_username_another_server,\
	get_practice_org


# place form definition here
class OfficeManagerWizard(FormWizard):

	def __init__(self, redirect_url='/'):
		#since we have to assume the order and type of the forms
		#to assign foreign keys, we hard code this here instead of using urls.py
		formlist = [InvitationEntryForm, NewManagerMHLUserForm, PracticeProfileForm]
		self.redirect_url = redirect_url
		super(OfficeManagerWizard, self).__init__(formlist)

	def done(self, request, form_list):
		inviteform = form_list[0]
		userform = form_list[1]
		invite = Invitation.objects.get(code=inviteform.cleaned_data['code'], userType=100)
		if len(form_list) > 2:
			practiceform = form_list[2]
			practice = practiceform.save(commit=False)
			practice.practice_lat = practiceform.cleaned_data['practice_lat']
			practice.practice_longit = practiceform.cleaned_data['practice_longit']
			practice.organization_type_id = RESERVED_ORGANIZATION_TYPE_ID_PRACTICE
			callgroup = CallGroup(description=practiceform.cleaned_data['practice_name'])
			callgroup.save()
			practice.call_group = callgroup
			practice.save()
			org_relation = OrganizationRelationship(organization=practice, 
				parent_id=RESERVED_ORGANIZATION_ID_DOCTORCOM, create_time=time.time())
			org_relation.save()
			manager_role = 2
		else:
			practice = invite.assignPractice
			manager_role = 1

		user = userform.save(commit=False)
		user.set_password(userform.cleaned_data['password1'])
		# use mhluser's address1, address2, city, state, zip to store "address" information,
		user.address1 = practice.practice_address1
		user.address2 = practice.practice_address2
		user.city = practice.practice_city
		user.state = practice.practice_state
		user.zip = practice.practice_zip
		user.lat = practice.practice_lat
		user.longit = practice.practice_longit
		user.tos_accepted = True
		if invite.recipient == request.POST['email']:
			user.email_confirmed = True

		user.save()

		staff = OfficeStaff(user=user, current_practice=practice)
		staff.save()
		staff.practices.add(practice)

		manager = Office_Manager(user=staff, practice=practice, manager_role=manager_role)
		manager.save()

		# TESTING_KMS_INTEGRATION
		create_default_keys(user, userform.cleaned_data['password1'])

		# Remove the invitation.
		invite.delete(createdUser=user, createdPractice=practice, send_notice=False)
		msg = render_to_string('MHLSignup/practice_notification_email.txt',
			{'practice_name': practice.practice_name,
			'practice_id': practice.id,
			'timestamp': datetime.datetime.now().strftime("%I:%M %m/%d/%Y")})
		send_mail("new practice created", msg, 'noreply@mdcom.com', ["support@mdcom.com"])
		return HttpResponseRedirect(self.redirect_url)

	def get_template(self, step):
		if step == 0:
			return 'MHLSignup/signup.html'
		if step == 1:
			return 'MHLSignup/default_form_manager.html'
		if step == 2:
			return 'MHLSignup/edit_practice.html'

	def process_step(self, request, form, step):
		#fixme: trash these usertypes and make something less crappy
		if(step == 0 and form.is_valid()):
			code = form.cleaned_data['code']
			invit = Invitation.objects.filter(code=code, userType=100)[0]
			if invit:
				assignPractice = invit.assignPractice
				if assignPractice:
					self.initial[1] = {
								'city': assignPractice.practice_city,
								'zip': assignPractice.practice_zip,
								'address1': assignPractice.practice_address1,
								'address2': assignPractice.practice_address2,
								'state': assignPractice.practice_state,
								}
					if len(self.form_list) > 2 and assignPractice:
						self.form_list.pop(-1)
			else:
				raise forms.ValidationError(_("This is not a valid office manager invitation code"))
			self.initial[1] = {'email': request.POST['signEmail']}


class OfficeStaffWizard(FormWizard):
	def __init__(self, redirect_url='/'):
		formlist = [InvitationEntryForm, NewStaffMHLUserForm]
		self.redirect_url = redirect_url
		super(OfficeStaffWizard, self).__init__(formlist)

	def done(self, request, form_list):
		inviteform = form_list[0]
		userform = form_list[1]
		user = userform.save(commit=False)
		user.set_password(userform.cleaned_data['password1'])
		user.tos_accepted = True

		invite = Invitation.objects.get(code=inviteform.cleaned_data['code'], userType=101)
		if invite.recipient == request.POST['email']:
			user.email_confirmed = True
		user.email = request.POST['email']

		assignPractice = invite.assignPractice
		if assignPractice:
			# use mhluser's address1, address2, city, state, zip to store "address" information,
			user.address1 = assignPractice.practice_address1
			user.address2 = assignPractice.practice_address2
			user.city = assignPractice.practice_city
			user.state = assignPractice.practice_state
			user.zip = assignPractice.practice_zip
			user.lat = assignPractice.practice_lat
			user.longit = assignPractice.practice_longit

		user.save()

		staff = OfficeStaff(user=user, current_practice=assignPractice)
		staff.save()
		staff.practices.add(assignPractice)

		userType = request.POST['userType']
		if userType == '3':
			nurse = Nurse(user=staff)
			nurse.save()
		if userType == '4':
			dietician = Dietician(user=staff)
			dietician.save()

		# TESTING_KMS_INTEGRATION
		create_default_keys(user, userform.cleaned_data['password1'])

		# Remove the invitation.
		invite = Invitation.objects.get(code=inviteform.cleaned_data['code'], userType=101)
		invite.delete(createdUser=user, send_notice=False)
		return HttpResponseRedirect(self.redirect_url)

	def get_template(self, step):
		#return 'MHLSignup/default_form.html'
		if step == 1:
			return 'MHLSignup/default_form_staff.html'
		if step == 0:
			return 'MHLSignup/signup.html'

	def process_step(self, request, form, step):
		if(step == 0 and form.is_valid()):
			code = form.cleaned_data['code']
			invit = Invitation.objects.filter(code=code, userType=101)[0]
			if not invit:
				raise forms.ValidationError(_("This is not a valid office staff invitation code"))
			self.initial[1] = {'email': request.POST['signEmail'], 'assignPractice': invit.assignPractice}


class ProviderWizard(FormWizard):
	def __init__(self, redirect_url='/'):
		if settings.CALL_ENABLE:
			formlist = [InvitationEntryForm, NewProviderForm, ProviderInfoDetail, None, LocalNumberForm]
		else:
			formlist = [InvitationEntryForm, NewProviderForm, ProviderInfoDetail, None]
		self.redirect_url = redirect_url
		super(ProviderWizard, self).__init__(formlist)

	def process_step(self, request, form, step):
		invit = Invitation.objects.filter(code=request.POST['code'])[0]
		if(step == 0 and form.is_valid()):
			code = form.cleaned_data['code']
			#if(not Invitation.objects.filter(code=code, userType__in=(1, 2)).exists()):
			#add medical student by xlin in 20120619
			if(not Invitation.objects.filter(code=code, userType__in=(1, 2, 10)).exists()):
				raise forms.ValidationError(_("This is not a valid office staff invitation code"))
			self.initial[1] = {'email': form.cleaned_data['signEmail'], 'userType': invit.userType}
		if(step == 1 and form.is_valid()):
			if(form.cleaned_data['userType'] == '10'):
				self.form_list[3] = PhysicianExtraSetupForm

			if(form.cleaned_data['userType'] == '2'):
				self.form_list[3] = NPPAExtraSetupForm

			if form.cleaned_data['userType'] == '1':
				self.form_list[3] = PhysicianExtraSetupForm

			#add by xlin in 20110611 for issue897 add practice location info
			#pl = PracticeLocation.objects.filter(pk=invit.assignPractice)
			if invit.assignPractice and 'city' not in request.POST:
				assignPractice = invit.assignPractice
				self.initial[2] = {
								'email': request.POST['email'],
								'city': assignPractice.practice_city,
								'zip': assignPractice.practice_zip,
								'address1': assignPractice.practice_address1,
								'address2': assignPractice.practice_address2,
								'state': assignPractice.practice_state,
								}

	def get_template(self, step):
		if step == 0:
			return 'MHLSignup/signup.html'
		if step == 1:
			return 'MHLSignup/default_form_term.html'
		if step == 2:
			return 'MHLSignup/edit_practice_provider.html'
		if step == 3:
			return 'MHLSignup/physician_form.html'
		if step == 4:
			return 'MHLSignup/get_doctorcom_number.html'

	def done(self, request, form_list):
		inviteForm = form_list[0]
		providerForm = form_list[1]
		providerInfo = form_list[2]
		extraSetupForm = form_list[3]

		invite = Invitation.objects.get(code=inviteForm.cleaned_data['code'])
		provider = providerForm.save(commit=False)
		provider.set_password(providerForm.cleaned_data['password1'])
		if (invite.typeVerified):
			provider.status_verified = True
			provider.status_verifier = MHLUser.objects.get(id=invite.sender_id)
		provider.save()

		provider.user = MHLUser.objects.get(id=provider.id)
		type = providerForm.cleaned_data['userType']
		if type == '1':
			Physician(user=provider,
				specialty=extraSetupForm.cleaned_data['specialty'],
				accepting_new_patients=extraSetupForm.cleaned_data['accepting_new_patients'],
				staff_type=extraSetupForm.cleaned_data['staff_type']
			).save()
		if type == '10':
			Physician(user=provider,
				specialty=extraSetupForm.cleaned_data['specialty'],
				accepting_new_patients=extraSetupForm.cleaned_data['accepting_new_patients'],
				staff_type=extraSetupForm.cleaned_data['staff_type']
			).save()
			provider.clinical_clerk = True
		if type == '2':
			NP_PA(user=provider).save()

		lst = extraSetupForm.cleaned_data['sites']
		lst2 = extraSetupForm.cleaned_data['licensed_states']
		sitesList = lst.split(',')
		sitesList2 = lst2.split(',')

		slst = []
		slst2 = []
		for s in sitesList:
			if s:
				slst.append(int(s))

		for s in sitesList2:
			if s:
				slst2.append(int(s))
		if slst:
			provider.sites = Site.objects.filter(id__in=slst)

		if extraSetupForm.cleaned_data['current_site']:
			currentSites = Site.objects.filter(id=int(extraSetupForm.cleaned_data['current_site']))
			if currentSites:
				cs = currentSites[0]
				provider.current_site = cs

		if slst2:
			provider.licensure_states = States.objects.filter(id__in=slst2)

		geocode_response = geocode2(providerInfo.cleaned_data['address1'], \
								providerInfo.cleaned_data['city'], \
								providerInfo.cleaned_data['state'], \
								providerInfo.cleaned_data['zip'])
		lat = geocode_response['lat']
		longit = geocode_response['lng']

		# use mhluser's address1, address2, city, state, zip to store "address" information,
		provider.address1 = providerInfo.cleaned_data['address1']
		provider.address2 = providerInfo.cleaned_data['address2']
		provider.city = providerInfo.cleaned_data['city']
		provider.state = providerInfo.cleaned_data['state']
		provider.zip = providerInfo.cleaned_data['zip']
		provider.lat = lat
		provider.longit = longit

		#add by xlin in 20120504 to add current practice	
		if invite.assignPractice:
			prac = invite.assignPractice
			provider.current_practice = get_practice_org(prac)

		provider.tos_accepted = True
		if invite.recipient == request.POST['email']:
			provider.email_confirmed = True

		# Generating the user's voicemail box configuration
		config = VMBox_Config(pin='')
		config.owner = provider
		config.save()

		# LocalNumberForm, area_code, pin, mdcom_phone, mdcom_phone_sid
		numberForm = form_list[4]
		mdcom_phone = numberForm.mdcom_phone
		mdcom_phone_sid = numberForm.mdcom_phone_sid
		pin = numberForm.cleaned_data['pin']

		provider.mdcom_phone = mdcom_phone
		provider.mdcom_phone_sid = mdcom_phone_sid

		#add doctorcom number
		if settings.CALL_ENABLE:
			user_type = ContentType.objects.get_for_model(provider)
			config = VMBox_Config.objects.get(owner_type=user_type, owner_id=provider.id)
			#config.change_pin(request, new_pin=pin)
			config.set_pin(pin)
			config.save()
			twilio_ConfigureProviderLocalNumber(provider, provider.mdcom_phone)
			request.session['userId'] = provider.id
			request.session['pin'] = pin

		provider.save()

		if invite.assignPractice:
			provider.practices.add(prac)
			#add by xlin in 20120504 add new provider in call group
			group = PracticeLocation.objects.get(pk=invite.assignPractice.id)
			#ONLY if practice set up before V2 of answering service
			if (prac.uses_original_answering_serice()):
				cm = CallGroupMember(call_group=group.call_group, member=provider, alt_provider=1)
				cm.save()

		# TESTING_KMS_INTEGRATION
		create_default_keys(provider.user, providerForm.cleaned_data['password1'])

		# Remove the invitation.
		invite.delete(createdUser=provider.user, send_notice=False)
		return HttpResponseRedirect(self.redirect_url)


class BrokerWizard(FormWizard):
	def __init__(self, redirect_url='/'):
		if settings.CALL_ENABLE:
			formlist = [InvitationEntryForm, NewBrokerForm, ProviderInfoDetail, LocalNumberForm]
		else:
			formlist = [InvitationEntryForm, NewBrokerForm, ProviderInfoDetail]
		self.redirect_url = redirect_url
		super(BrokerWizard, self).__init__(formlist)

	def get_template(self, step):
		if step == 0:
			return 'MHLSignup/signup.html'
		if step == 1:
			return 'MHLSignup/default_form_term.html'
		if step == 3:
			return 'MHLSignup/get_doctorcom_number.html'
		if step == 2:
			if len(self.form_list) == 4:
				return 'MHLSignup/edit_practice_borker.html'
			if len(self.form_list) == 3:
				return 'MHLSignup/edit_practice_borker2.html'

	def process_step(self, request, form, step):
		if(step == 0 and form.is_valid()):
			code = form.cleaned_data['code']
			if(not Invitation.objects.filter(code=code, userType=300).exists()):
				raise forms.ValidationError(_("This is not a valid broker invitation code"))
			self.initial[1] = {'email': form.cleaned_data['signEmail']}

	def done(self, request, form_list):
		inviteForm = form_list[0]
		brokerForm = form_list[1]
		brokerInfo = form_list[2]

		invite = Invitation.objects.get(code=inviteForm.cleaned_data['code'], userType__in=(300,))
		geocode_response = geocode2(brokerInfo.cleaned_data['address1'], \
								brokerInfo.cleaned_data['city'], \
								brokerInfo.cleaned_data['state'], \
								brokerInfo.cleaned_data['zip'])
		lat = geocode_response['lat']
		longit = geocode_response['lng']

		mhuser = brokerForm.save(commit=False)
		mhuser.set_password(brokerForm.cleaned_data['password1'])
		# use mhluser's address1, address2, city, state, zip to store "address" information,
		mhuser.address1 = brokerInfo.cleaned_data['address1']
		mhuser.address2 = brokerInfo.cleaned_data['address2']
		mhuser.city = brokerInfo.cleaned_data['city']
		mhuser.state = brokerInfo.cleaned_data['state']
		mhuser.zip = brokerInfo.cleaned_data['zip']
		mhuser.lat = lat
		mhuser.longit = longit
		if (invite.typeVerified):
			mhuser.status_verified = True
			mhuser.status_verifier = MHLUser.objects.get(id=invite.sender_id)
		mhuser.tos_accepted = True
		if invite.recipient == request.POST['email']:
			mhuser.email_confirmed = True
		mhuser.save()

		broker = Broker()
		broker.user = mhuser
		broker.save()

		# Generating the user's voicemail box configuration
		config = VMBox_Config(pin='')
		config.owner = broker
		config.save()

		# LocalNumberForm, area_code, pin, mdcom_phone, mdcom_phone_sid
		numberForm = form_list[3]
		mdcom_phone = numberForm.mdcom_phone
		mdcom_phone_sid = numberForm.mdcom_phone_sid
		pin = numberForm.cleaned_data['pin']

		broker.mdcom_phone = mdcom_phone
		broker.mdcom_phone_sid = mdcom_phone_sid

		#add doctorcom number
		if settings.CALL_ENABLE:
			user_type = ContentType.objects.get_for_model(broker)
			config = VMBox_Config.objects.get(owner_type=user_type, owner_id=broker.id)
			#config.change_pin(request, new_pin=pin)
			config.set_pin(pin)
			config.save()
			twilio_ConfigureProviderLocalNumber(broker, broker.mdcom_phone)
			request.session['userId'] = mhuser.id
			request.session['pin'] = pin

		broker.save()

		# TESTING_KMS_INTEGRATION
		create_default_keys(mhuser, brokerForm.cleaned_data['password1'])

		# Remove the invitation.
		invite.delete()
		return HttpResponseRedirect(self.redirect_url)


class NewProviderForm(forms.ModelForm):
	password1 = forms.CharField(widget=forms.PasswordInput(render_value=False), label=_('Password'))
	password2 = forms.CharField(widget=forms.PasswordInput(render_value=False), label=_('Confirm Password'))
	userType = forms.ChoiceField(choices=PROVIDER_TYPE_CHOICES, label=_('UserType'))

	def clean_username(self):
		if(MHLUser.objects.filter(username=self.cleaned_data['username']).exists()):
			raise forms.ValidationError(_("That username is already taken"))
		for url in settings.CHECKUSERNAME_URL:
			self.check_username_another_server(url, 0)
		return self.cleaned_data['username']

	def check_username_another_server(self, url, times):
		user_name = self.cleaned_data['username']
		if check_username_another_server(user_name, url, times):
			raise forms.ValidationError(MSG_USERNAME_EXIST)

	def clean_email(self):
		email = self.cleaned_data['email']
		if(MHLUser.objects.filter(email=email).exists()):
			raise forms.ValidationError(_('Another account is using that email address'))
		return email

	def clean_mobile_phone(self):
		phone = self.cleaned_data['mobile_phone']
		if(not phone):
			raise forms.ValidationError(_('This field is required.'))
		if(Provider.objects.filter(mobile_phone=phone).exists()):
			raise forms.ValidationError(_('That mobile phone number is in use by another user.'))
		return phone

	class Meta:
		model = Provider
		fields = ('username', 'first_name', 'last_name', 'email', 'mobile_phone', 'gender')
		widgets = {
			'gender': forms.RadioSelect(),
			'first_name': forms.TextInput(attrs={'value': _('First Name')}),
			'last_name': forms.TextInput(attrs={'value': _('Last Name')}),
		}


#create new class for user info just like zip code, address
#xlin 20120620
class ProviderInfoDetail(forms.ModelForm):
	class Meta:
		model = MHLUser
		fields = ('address1', 'address2', 'zip', 'city', 'state', 'phone',)


class ProviderExtraSetupForm(forms.Form):
	sites = forms.CharField(required=False)
	current_site = forms.CharField(required=False)
	licensed_states = forms.CharField(required=False)

	def __init__(self, *args, **kwargs):
		#crappy workaround for formwizard
		super(ProviderExtraSetupForm, self).__init__(*args, **kwargs)

	def clean_username(self):
		username = self.cleaned_data['username']
		if(MHLUser.objects.filter(username=username).exists()):
			raise forms.ValidationError(_('That username is taken.'))
		for url in settings.CHECKUSERNAME_URL:
			self.check_username_another_server(url, 0)
		return username

	def check_username_another_server(self, url, times):
		user_name = self.cleaned_data['username']
		if check_username_another_server(user_name, url, times):
			raise forms.ValidationError(MSG_USERNAME_EXIST)


class NPPAExtraSetupForm(ProviderExtraSetupForm):
	pass  # just to make the code more clear, no extra info needed here


class PhysicianExtraSetupForm(ProviderExtraSetupForm):
	specialty = forms.ChoiceField(choices=SPECIALTY_CHOICES, required=False)
	accepting_new_patients = forms.BooleanField(initial=True, required=False)
	staff_type = forms.ChoiceField(choices=STAFF_TYPE_CHOICES, required=False)


class NewBrokerForm(forms.ModelForm):
	password1 = forms.CharField(widget=forms.PasswordInput(render_value=False), label=_('Password'))
	password2 = forms.CharField(widget=forms.PasswordInput(render_value=False), label=_('Confirm Password'))
	userType = forms.ChoiceField(choices=BROKER_TYPE_CHOICES)

	def clean_username(self):
		if(MHLUser.objects.filter(username=self.cleaned_data['username']).exists()):
			raise forms.ValidationError(_("That username is already taken"))
		for url in settings.CHECKUSERNAME_URL:
			self.check_username_another_server(url, 0)
		return self.cleaned_data['username']

	def check_username_another_server(self, url, times):
		user_name = self.cleaned_data['username']
		if check_username_another_server(user_name, url, times):
			raise forms.ValidationError(MSG_USERNAME_EXIST)

	def clean_email(self):
		email = self.cleaned_data['email']
		if(MHLUser.objects.filter(email=email).exists()):
			raise forms.ValidationError(_('Another account is using that email address'))
		return email

	def clean_mobile_phone(self):
		phone = self.cleaned_data['mobile_phone']
		if(not phone):
			raise forms.ValidationError(_('This field is required.'))
		if(Provider.objects.filter(mobile_phone=phone).exists()):
			raise forms.ValidationError(_('That mobile phone number is in use by another user.'))
		return phone

	class Meta:
		model = MHLUser
		fields = ('username', 'first_name', 'last_name', 'email', 'gender', 'mobile_phone')


class InvitationEntryForm(forms.Form):
	code = forms.CharField(max_length=8, label=_("Invitation Code"))
	signEmail = forms.EmailField(label=_("Your Email Address"))

	def clean(self):
		cleaned = self.cleaned_data

		code = cleaned.get('code')
		email = cleaned.get('signEmail')
		if (not code or not email):
			return cleaned

		invite = Invitation.objects.filter(code=str(code).upper())
		if (invite.count() != 1):
			raise forms.ValidationError(_("Either the given code or email address is "
				"incorrect. Please ensure that the code is exactly what you received "
				"in your email, and that the email address is the one at which you "
				"received the invitation. You will be able to specify a different email "
				"address for your account later."))

		invite = invite[0]

		if (not invite.recipient or invite.recipient.lower() != email.lower()):
			raise forms.ValidationError(_("Either the given code or email address is "
				"incorrect. Please ensure that the code is exactly what you received "
				"in your email, and that the email address is the one at which you "
				"received the invitation. You will be able to specify a different "
				"email address for your account later."))

		return cleaned
