
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.forms import ModelForm
from django.utils.translation import ugettext as _
from MHLogin.MHLUsers.models import MHLUser, Physician, Provider, OfficeStaff, Broker
from MHLogin.utils.geocode import geocode2
from MHLogin.utils.constants import FORWARD_CHOICES, PROVIDER_CREATE_CHOICES, STAFF_CREATE_CHOICES
from MHLogin.MHLUsers.utils import has_mhluser_with_mobile_phone, has_mhluser_with_email,\
	check_username_another_server
from MHLogin.MHLPractices.models import PracticeLocation

MSG_GEO_ADDRESS_INVALID = _('Warning: Your form has been saved but '
	'determining coordinates from the entered address was not successful.  '
	'Please verify correctness, if this persists our staff will be notified.  '
	'Our apologies, thanks for your patience - DoctorCom staff.')
MSG_GEO_ADDRESS_NOT_FOUND = _('That address could not be found. Please recheck '
			'the address you entered.')
MSG_GEO_MULTIPLE_ADDRESSES_FOUND = _('Multiple addresses were found. %s Please '
			'recheck the address you entered.')
MSG_GEO_EMPTY = _('At a minimum, please enter in either street, city and state or street and zip')
MSG_MOBILE_PHONE_REQUIRED = _('A mobile phone number is required.')
MSG_FIELD_REQUIRED = _('This field is required')
MSG_USERNAME_EXIST = _("That username is already taken")


class NewMHLUserForm(forms.ModelForm):
	password1 = forms.CharField(widget=forms.PasswordInput(render_value=False), 
			label=_('Password'))
	password2 = forms.CharField(widget=forms.PasswordInput(render_value=False), 
			label=_('Confirm Password'))

	def clean_password2(self):
		data = self.cleaned_data
		if ('password1' not in data or
			'password2' not in data or
			data['password1'] != data['password2']):
			raise ValidationError(_("Passwords don't match"))

	class Meta:
		fields = (
				'username', 'first_name', 'last_name', 'email',
				'password1', 'password2',

				'gender', 'address1', 'address2', 'city', 'state', 'zip',
				'phone', 'mobile_phone'
			)

		model = MHLUser


class NewManagerMHLUserForm(forms.ModelForm):
	password1 = forms.CharField(widget=forms.PasswordInput(render_value=False), 
			label=_('Password'))
	password2 = forms.CharField(widget=forms.PasswordInput(render_value=False), 
			label=_('Confirm Password'))

#	def clean_password2(self):
#		data = self.cleaned_data
#		if('password1' not in data or
#			'password2' not in data or
#			data['password1'] != data['password2']):
#			raise ValidationError(_("Passwords don't match"))

	def clean_username(self):
		username = self.cleaned_data['username']
		if(MHLUser.objects.filter(username=username).exists()):
			raise ValidationError(MSG_USERNAME_EXIST)
		for url in settings.CHECKUSERNAME_URL:
			self.check_username_another_server(url, 0)
		return username

	def check_username_another_server(self, url, times):
		user_name = self.cleaned_data['username']
		if check_username_another_server(user_name, url, times):
			raise forms.ValidationError(MSG_USERNAME_EXIST)

	def clean_email(self):
		email = self.cleaned_data['email']
		if(MHLUser.objects.filter(email=email).exists()):
			raise ValidationError(_('Another account is using that email address'))
		return email

	class Meta:
		fields = (
				'username', 'first_name', 'last_name', 'email',
				'password1', 'gender', 'mobile_phone'
			)
		widgets = {
			'gender': forms.RadioSelect(),
		}

		model = MHLUser


class NewStaffMHLUserForm(forms.ModelForm):
	password1 = forms.CharField(widget=forms.PasswordInput(render_value=False), 
			label=_('Password'))
	password2 = forms.CharField(widget=forms.PasswordInput(render_value=False), 
			label=_('Confirm Password'))
	userType = forms.ChoiceField(choices=STAFF_CREATE_CHOICES, label=_("Staff Type"))

	def __init__(self, data=None, *args, **kwargs):
		super(NewStaffMHLUserForm, self).__init__(data=data, *args, **kwargs)
		if 'initial' in kwargs:
			initial = kwargs['initial']
			if 'assignPractice' in initial and initial['assignPractice']\
				and isinstance(initial['assignPractice'], PracticeLocation):
				self.base_fields['userType'].choices = \
					initial['assignPractice'].get_org_sub_user_types_tuple(role_category=2,
							include_manager=False)

#	def clean_password2(self):
#		data = self.cleaned_data
#		if('password1' not in data or
#			'password2' not in data or
#			data['password1'] != data['password2']):
#			raise ValidationError(_("Passwords don't match"))

	def clean_username(self):
		username = self.cleaned_data['username']
		if(MHLUser.objects.filter(username=username).exists()):
			raise ValidationError(MSG_USERNAME_EXIST)
		for url in settings.CHECKUSERNAME_URL:
			self.check_username_another_server(url, 0)
		return username

	def check_username_another_server(self, url, times):
		user_name = self.cleaned_data['username']
		if check_username_another_server(user_name, url, times):
			raise forms.ValidationError(MSG_USERNAME_EXIST)

	def clean_email(self):
		email = self.cleaned_data['email']
		if(MHLUser.objects.filter(email=email).exists()):
			raise ValidationError(_('Another account is using that email address'))
		return email

	class Meta:
		fields = (
				'username', 'first_name', 'last_name', 'email',
				'password1', 'gender', 'mobile_phone'
			)
		widgets = {
			'gender': forms.RadioSelect(),
		}

		model = MHLUser


class ProviderForm(forms.ModelForm):
	old_email = forms.CharField(widget=forms.HiddenInput(), required=False)
	old_mobile_phone = forms.CharField(widget=forms.HiddenInput(), required=False)
	old_pager = forms.CharField(widget=forms.HiddenInput(), required=False)
	old_email_confirmed = forms.CharField(widget=forms.HiddenInput(), required=False)
	old_mobile_confirmed = forms.CharField(widget=forms.HiddenInput(), required=False)
	old_pager_confirmed = forms.CharField(widget=forms.HiddenInput(), required=False)
	non_field_warnings = None

	def __init__(self, data=None, files=None, instance=None, *args, **kwargs):
		super(ProviderForm, self).__init__(data=data, files=files, instance=instance, *args, **kwargs)
		if (instance):
			self.fields['old_email'].initial = instance.email
			self.fields['old_mobile_phone'].initial = instance.mobile_phone
			self.fields['old_pager'].initial = instance.pager
			self.fields['old_email_confirmed'].initial = instance.email_confirmed
			self.fields['old_mobile_confirmed'].initial = instance.mobile_confirmed
			self.fields['old_pager_confirmed'].initial = instance.pager_confirmed

		self.fields['address1'].label = _('Office address1')
		self.fields['address2'].label = _('Office address2')
		self.fields['city'].label = _('Office city')
		self.fields['state'].label = _('Office state')
		self.fields['zip'].label = _('Office zip')

	class Meta:
		model = Provider
		#exclude = ('address1','address2','city','state','zip',)
		fields = ('first_name', 'last_name', 'title', 'gender',
					'email', 'email_confirmed',
					'mobile_phone', 'mobile_confirmed',
					'office_phone', 'phone',
					'pager', 'pager_confirmed',
					'pager_extension',

					'address1', 'address2', 'city', 'state', 'zip',
					'photo', 'licensure_states', 'skill', 'public_notes',
					'certification')
		widgets = { 
				'email_confirmed': forms.HiddenInput(),
				'mobile_confirmed': forms.HiddenInput(),
				'pager_confirmed': forms.HiddenInput(),
				'certification': forms.Textarea(attrs={'id': "id_certification", 
					'rows': 10, 'name': "certification",
						'cols': 40, 'class': 'valid', 'maxlength': 200})
			}

	def clean(self):
		cleaned_data = self.cleaned_data
		street = cleaned_data['address1']
		city = cleaned_data['city']
		state = cleaned_data['state']
		zip = cleaned_data['zip']

		#clean mobile phone - required for providers	
		if(not 'mobile_phone' in cleaned_data or not cleaned_data['mobile_phone']):
			raise forms.ValidationError(MSG_MOBILE_PHONE_REQUIRED)

		email_confirmed = cleaned_data['email_confirmed']
		mobile_confirmed = cleaned_data['mobile_confirmed']
		pager_confirmed = cleaned_data['pager_confirmed']

		if not email_confirmed:
			cleaned_data['email'] = cleaned_data['old_email']
			cleaned_data['email_confirmed'] = cleaned_data['old_email_confirmed']
		if settings.CALL_ENABLE and not mobile_confirmed:
			cleaned_data['mobile_phone'] = cleaned_data['old_mobile_phone']
			cleaned_data['mobile_confirmed'] = cleaned_data['old_mobile_confirmed']
		if settings.CALL_ENABLE and not pager_confirmed and cleaned_data['pager']:
			cleaned_data['pager'] = cleaned_data['old_pager']
			cleaned_data['pager_confirmed'] = cleaned_data['old_pager_confirmed']

		if(self.instance):
			def compare(form, model, field):
				return form.cleaned_data[field] == model.__getattribute__(field)
			if(all(compare(self, self.instance, field) for field in 
					('address1', 'city', 'state', 'zip'))):
				self.cleaned_data['lat'] = self.instance.lat
				self.cleaned_data['longit'] = self.instance.longit
				return cleaned_data
		if ((street and city and state)) or ((street and zip)):
			results = geocode2(street, city, state, zip)
			if results['lat'] == 0.0 and results['lng'] == 0.0:
				from MHLogin.utils.admin_utils import mail_admins
				self.non_field_warnings = MSG_GEO_ADDRESS_INVALID
				mail_admins('Geocode error in Provider form save', 'Geocode lookup '
					'problems saving Provider: %s.\n\nGeocode message:\n%s' % 
					(self.instance.username, results['msg']))
			else:
				self.non_field_warnings = None
			cleaned_data['lat'] = results['lat']
			cleaned_data['longit'] = results['lng']
		else:
			raise forms.ValidationError(MSG_GEO_EMPTY)
		return cleaned_data


class UserTypeSelecterForm(forms.Form):
	provider_types = forms.ChoiceField(choices=PROVIDER_CREATE_CHOICES, label=_("User Type"))
	staff_types = forms.ChoiceField(choices=STAFF_CREATE_CHOICES, label=_("Staff Type"))

	def __init__(self, data=None, initial=None, current_practice=None, *args, **kwargs):
		if current_practice:
			self.base_fields['provider_types'].choices = \
				current_practice.get_org_sub_user_types_tuple(role_category=1)
			self.base_fields['staff_types'].choices = \
				current_practice.get_org_sub_user_types_tuple(
								role_category=2, 
								include_sub_staff_type=False
							)
		super(UserTypeSelecterForm, self).__init__(data=data,\
			initial=initial, *args, **kwargs)


#add by xlin in 20120328 to add new form for issue577
####### TODO we should use address1, address2, city, state, zip instead off office_address1, etc.
class CreateProviderForm(forms.ModelForm):

	user_type = forms.ChoiceField(choices=PROVIDER_CREATE_CHOICES, label=_("User Type"))
	non_field_warnings = None

	class Meta:
		model = Provider
		fields = ('username', 'first_name', 'last_name', 'email', 'mobile_phone', 'gender',
					'address1', 'address2', 'city', 'state', 'zip', 'clinical_clerk')
		widgets = {
			'clinical_clerk': forms.HiddenInput,
		}

	def __init__(self, data=None, files=None, instance=None, current_practice=None, *args, **kwargs):
		if current_practice:
			self.base_fields['user_type'].choices = \
				current_practice.get_org_sub_user_types_tuple(role_category=1)
		super(CreateProviderForm, self).__init__(data=data, files=files, 
						instance=instance, *args, **kwargs)
		self.fields['username'].label = _('User Name')
		self.fields['username'].help_text = ''
		self.fields['address1'].label = _('Office address1')
		self.fields['address2'].label = _('Office address2')
		self.fields['city'].label = _('Office city')
		self.fields['state'].label = _('Office state')
		self.fields['zip'].label = _('Office zip')

	def clean_username(self):
		username = self.cleaned_data['username']
		if not username:
			raise ValidationError(MSG_FIELD_REQUIRED)
		if(MHLUser.objects.filter(username=username).exists()):
			raise ValidationError(MSG_USERNAME_EXIST)
		for url in settings.CHECKUSERNAME_URL:
			self.check_username_another_server(url, 0)
		return username

	# When refine register feature, remove following function to a common function in utils.
	def check_username_another_server(self, url, times):
		user_name = self.cleaned_data['username']
		if check_username_another_server(user_name, url, times):
			raise forms.ValidationError(MSG_USERNAME_EXIST)

	def clean_mobile_phone(self):
		cleaned_data = self.cleaned_data
		if(not 'mobile_phone' in cleaned_data or not cleaned_data['mobile_phone']):
			raise forms.ValidationError(MSG_MOBILE_PHONE_REQUIRED)
		mobile_phone = cleaned_data['mobile_phone']
		if has_mhluser_with_mobile_phone(mobile_phone):
			raise forms.ValidationError(_("This mobile phone has been registered. "\
					"Please choose another mobile phone or invite him to your practice"))
		return mobile_phone

	def clean_email(self):
		cleaned_data = self.cleaned_data
		if(not 'email' in cleaned_data or not cleaned_data['email']):
			raise forms.ValidationError(MSG_FIELD_REQUIRED)
		email = cleaned_data['email']
		if has_mhluser_with_email(email):
			raise forms.ValidationError(_("This email has been registered. Please "\
						"choose another email or invite him to your practice."))
		return email

	def clean_address1(self):
		cleaned_data = self.cleaned_data
		if(not 'address1' in cleaned_data or not cleaned_data['address1']):
			raise forms.ValidationError(MSG_FIELD_REQUIRED)
		return cleaned_data['address1']

	def clean_city(self):
		cleaned_data = self.cleaned_data
		if(not 'city' in cleaned_data or not cleaned_data['city']):
			raise forms.ValidationError(MSG_FIELD_REQUIRED)
		return cleaned_data['city']

	def clean_state(self):
		cleaned_data = self.cleaned_data
		if(not 'state' in cleaned_data or not cleaned_data['state']):
			raise forms.ValidationError(MSG_FIELD_REQUIRED)
		return cleaned_data['state']

	def clean_zip(self):
		cleaned_data = self.cleaned_data
		if(not 'zip' in cleaned_data or not cleaned_data['zip']):
			raise forms.ValidationError(MSG_FIELD_REQUIRED)
		return cleaned_data['zip']

	def clean(self):
		cleaned_data = self.cleaned_data
		if not self.errors and 0 == len(self.errors):
			street = cleaned_data['address1']
			city = cleaned_data['city']
			state = cleaned_data['state']
			zip = cleaned_data['zip']
			user_type = cleaned_data['user_type']

			if '10' == user_type:
				cleaned_data["clinical_clerk"] = True

			if(self.instance):
				def compare(form, model, field):
					return form.cleaned_data[field] == model.__getattribute__(field)
				if(all(compare(self, self.instance, field) for field in 
						('address1', 'city', 'state', 'zip'))):
					self.cleaned_data['lat'] = self.instance.lat
					self.cleaned_data['longit'] = self.instance.longit
					return cleaned_data
			if ((street and city and state)) or ((street and zip)):
				results = geocode2(street, city, state, zip)
				if results['lat'] == 0.0 and results['lng'] == 0.0:
					from MHLogin.utils.admin_utils import mail_admins
					self.non_field_warnings = MSG_GEO_ADDRESS_INVALID
					mail_admins('Geocode error in Create Provider form save', 'Geocode lookup '
						'problems creating Provider: %s.\n\nGeocode message:\n%s' % 
						(self.instance.username, results['msg']))
				else:
					self.non_field_warnings = None
				cleaned_data['lat'] = results['lat']
				cleaned_data['longit'] = results['lng']
			else:
				raise forms.ValidationError(MSG_GEO_EMPTY)
		return cleaned_data


class CreateMHLUserForm(forms.ModelForm):
	class Meta:
		model = MHLUser
		fields = ('username', 'first_name', 'last_name', 'email', 'mobile_phone', 'gender',)

	def __init__(self, data=None, files=None, instance=None, *args, **kwargs):
		super(CreateMHLUserForm, self).__init__(data=data, files=files, instance=instance, *args, **kwargs)
		self.fields['username'].label = 'User Name'
		self.fields['username'].help_text = ''

	def clean_username(self):
		username = self.cleaned_data['username']
		if not username:
			raise ValidationError(MSG_FIELD_REQUIRED)
		if(MHLUser.objects.filter(username=username).exists()):
			raise ValidationError(MSG_USERNAME_EXIST)
		for url in settings.CHECKUSERNAME_URL:
			self.check_username_another_server(url, 0)
		return username

	# When refine register feature, remove following function to a common function in utils.
	def check_username_another_server(self, url, times):
		user_name = self.cleaned_data['username']
		if check_username_another_server(user_name, url, times):
			raise forms.ValidationError(MSG_USERNAME_EXIST)

	def clean_mobile_phone(self):
		cleaned_data = self.cleaned_data
		mobile_phone = cleaned_data['mobile_phone']
		if mobile_phone and has_mhluser_with_mobile_phone(mobile_phone):
			raise forms.ValidationError(_("This mobile phone has been registered. "
				"Please choose another mobile phone or invite him to your practice"))
		return mobile_phone

	def clean_email(self):
		cleaned_data = self.cleaned_data
		if(not 'email' in cleaned_data or not cleaned_data['email']):
			raise forms.ValidationError(MSG_FIELD_REQUIRED)
		email = cleaned_data['email']
		if has_mhluser_with_email(email):
			raise forms.ValidationError(_("This email has been registered. Please "
				"choose another email or invite him to your practice."))
		return email


class CreateOfficeStaffForm(forms.ModelForm):
	staff_type = forms.ChoiceField(choices=STAFF_CREATE_CHOICES, label=_("Staff Type"))

	class Meta:
		model = OfficeStaff
		fields = ()

	def __init__(self, data=None, initial=None, current_practice=None, 
			include_manager=True, *args, **kwargs):
		if current_practice:
			self.base_fields['staff_type'].choices = \
				current_practice.get_org_sub_user_types_tuple(
								role_category=2, include_manager=include_manager
							)
		super(CreateOfficeStaffForm, self).__init__(data=data,\
			initial=initial, *args, **kwargs)


class CreateBrokerMHLUserForm(forms.ModelForm):
	class Meta:
		model = MHLUser
		fields = ('username', 'first_name', 'last_name', 'email', 'mobile_phone', 
			'gender', 'address1', 'address2', 'city', 'state', 'zip')

	def __init__(self, data=None, files=None, instance=None, *args, **kwargs):
		super(CreateBrokerMHLUserForm, self).__init__(data=data, 
			files=files, instance=instance, *args, **kwargs)
		self.fields['username'].label = _('User Name')
		self.fields['username'].help_text = ''
		self.fields['address1'].label = _('Office address1')
		self.fields['address2'].label = _('Office address2')
		self.fields['city'].label = _('Office city')
		self.fields['state'].label = _('Office state')
		self.fields['zip'].label = _('Office zip')

	def clean_username(self):
		username = self.cleaned_data['username']
		if not username:
			raise ValidationError(MSG_FIELD_REQUIRED)
		if(MHLUser.objects.filter(username=username).exists()):
			raise ValidationError(MSG_USERNAME_EXIST)
		for url in settings.CHECKUSERNAME_URL:
			self.check_username_another_server(url, 0)
		return username

	# When refine register feature, remove following function to a common function in utils.
	def check_username_another_server(self, url, times):
		user_name = self.cleaned_data['username']
		if check_username_another_server(user_name, url, times):
			raise forms.ValidationError(MSG_USERNAME_EXIST)

	def clean_mobile_phone(self):
		cleaned_data = self.cleaned_data
		if(not 'mobile_phone' in cleaned_data or not cleaned_data['mobile_phone']):
			raise forms.ValidationError(MSG_MOBILE_PHONE_REQUIRED)
		mobile_phone = cleaned_data['mobile_phone']
		if has_mhluser_with_mobile_phone(mobile_phone):
			raise forms.ValidationError(_("This mobile phone has been registered. "
				"Please choose another mobile phone or invite him to your practice"))
		return mobile_phone

	def clean_email(self):
		cleaned_data = self.cleaned_data
		if(not 'email' in cleaned_data or not cleaned_data['email']):
			raise forms.ValidationError(MSG_FIELD_REQUIRED)
		email = cleaned_data['email']
		if has_mhluser_with_email(email):
			raise forms.ValidationError(_("This email has been registered. Please choose "
				"another email or invite him to your practice."))
		return email

	def clean_address1(self):
		cleaned_data = self.cleaned_data
		if(not 'address1' in cleaned_data or not cleaned_data['address1']):
			raise forms.ValidationError(MSG_FIELD_REQUIRED)
		return cleaned_data['address1']

	def clean_city(self):
		cleaned_data = self.cleaned_data
		if(not 'city' in cleaned_data or not cleaned_data['city']):
			raise forms.ValidationError(MSG_FIELD_REQUIRED)
		return cleaned_data['city']

	def clean_state(self):
		cleaned_data = self.cleaned_data
		if(not 'state' in cleaned_data or not cleaned_data['state']):
			raise forms.ValidationError(MSG_FIELD_REQUIRED)
		return cleaned_data['state']

	def clean_zip(self):
		cleaned_data = self.cleaned_data
		if(not 'zip' in cleaned_data or not cleaned_data['zip']):
			raise forms.ValidationError(MSG_FIELD_REQUIRED)
		return cleaned_data['zip']

	def clean(self):
		cleaned_data = self.cleaned_data
		if not self.errors and 0 == len(self.errors):
			street = cleaned_data['address1']
			city = cleaned_data['city']
			state = cleaned_data['state']
			zip = cleaned_data['zip']

			if(self.instance):
				def compare(form, model, field):
					return form.cleaned_data[field] == model.__getattribute__(field)
				if(all(compare(self, self.instance, field) for field in 
						('address1', 'city', 'state', 'zip'))):
					self.cleaned_data['lat'] = self.instance.lat
					self.cleaned_data['longit'] = self.instance.longit
					return cleaned_data
			if ((street and city and state)) or ((street and zip)):
				results = geocode2(street, city, state, zip)
				if results['lat'] == 0.0 and results['lng'] == 0.0:
					from MHLogin.utils.admin_utils import mail_admins
					self.non_field_warnings = MSG_GEO_ADDRESS_INVALID
					mail_admins('Geocode error in Create Provider form save', 'Geocode lookup '
						'problems creating Provider: %s.\n\nGeocode message:\n%s' % 
						(self.instance.username, results['msg']))
				else:
					self.non_field_warnings = None
				cleaned_data['lat'] = results['lat']
				cleaned_data['longit'] = results['lng']
			else:
				raise forms.ValidationError(MSG_GEO_EMPTY)
		return cleaned_data


class CreateBrokerForm(forms.ModelForm):
	class Meta:
		model = Broker
		fields = ('office_phone', 'pager', 'pager_extension', 'licensure_states')


class GetNewPhysicianForm(forms.ModelForm):
	class Meta:
		model = Physician
		fields = ('specialty', 'accepting_new_patients',)


####### TODO make sure this isn't used, use MHLSignup.forms.NewProviderForm
class NewProviderForm(forms.ModelForm):
	# TODO_PROVINH:
	# The following 2 lines of fields are django.authentication.user
	# fields. To eliminate the Provider inheritance, these just need
	# to be removed since they're replicated in MHLUserForm above.
	password1 = forms.CharField(widget=forms.PasswordInput(render_value=False), 
			label=_("Password"))
	password2 = forms.CharField(widget=forms.PasswordInput(render_value=False), 
			label=_("Password Verify"))

	class Meta:
		model = Provider
		fields = (
				# TODO_PROVINH:
				# The following 2 lines of fields are django.authentication.user
				# fields. To eliminate the Provider inheritance, these just need
				# to be removed since they're replicated in MHLUserForm above.
				'username', 'first_name', 'last_name', 'email',
				'password1', 'password2',

				# TODO_PROVINH:
				# The following 2 lines of fields are MHLogin
				# fields. To eliminate the Provider inheritance, these just need
				# to be removed since they're replicated in MHLUserForm above.
				#'user',
				'gender', 'address1', 'address2', 'city', 'state', 'zip',
				'phone', 'mobile_phone',

				'pager', 'pager_extension',
				# TODO we should use address1, address2, city instead of office_address1, etc.
				'address1', 'address2', 'city',
				'zip', 'phone',

				'sites', 'current_site',
				'licensure_states',
				'photo',
			)

	def clean_password2(self):
		pass1 = self.cleaned_data['password1']
		pass2 = self.cleaned_data['password2']

		if (pass1 != pass2):
			raise forms.ValidationError(_("Passwords do not match."))

		return pass1

	def clean_mobile_phone(self):
		# TODO:
		# Verify that the given phone number is valid.
		import re
		p1 = re.compile('\((\d{3})\) ?(\d{3})[. -](\d{4})$')
		p2 = re.compile('(\d{3})[. -](\d{3})[. -](\d{4})$')
		p3 = re.compile('\d{10}$')

		number = self.cleaned_data['mobile_phone']

		if (not number):
			raise forms.ValidationError(_('This field is required.'))

		m = p3.match(number)
		if (m):
			return m
		m = p1.match(number)
		if (not m):
			m = p2.match(number)
		if (not m):
			raise forms.ValidationError(_('An invalid number was entered. '
				'Please use format (xxx) xxx-xxxx.'))

		return '%s%s%s' % (m.group(1), m.group(2), m.group(3),)


class OfficeStaffForm(ModelForm):
	old_pager = forms.CharField(widget=forms.HiddenInput(), required=False)
	old_pager_confirmed = forms.CharField(widget=forms.HiddenInput(), required=False)

	class Meta:
		model = OfficeStaff
		fields = ('office_phone', 'pager', 'pager_confirmed', 'pager_extension')
		widgets = { 
				'pager_confirmed': forms.HiddenInput()
			}

	def __init__(self, data=None, files=None, instance=None, *args, **kwargs):
		super(OfficeStaffForm, self).__init__(data=data, files=files, instance=instance, *args, **kwargs)
		if (instance):
			self.fields['old_pager'].initial = instance.pager
			self.fields['old_pager_confirmed'].initial = instance.pager_confirmed

	def clean(self):
		cleaned_data = self.cleaned_data
		pager_confirmed = cleaned_data['pager_confirmed']

		if settings.CALL_ENABLE and not pager_confirmed and cleaned_data['pager']:
			cleaned_data['pager'] = cleaned_data['old_pager']
			cleaned_data['pager_confirmed'] = cleaned_data['old_pager_confirmed']
		return cleaned_data


class UserForm(ModelForm):
	old_email = forms.CharField(widget=forms.HiddenInput(), required=False)
	old_mobile_phone = forms.CharField(widget=forms.HiddenInput(), required=False)
	old_email_confirmed = forms.CharField(widget=forms.HiddenInput(), required=False)
	old_mobile_confirmed = forms.CharField(widget=forms.HiddenInput(), required=False)

	def __init__(self, data=None, files=None, instance=None, *args, **kwargs):
		super(UserForm, self).__init__(data=data, files=files, instance=instance, *args, **kwargs)
		if (instance):
			self.fields['old_email'].initial = instance.email
			self.fields['old_mobile_phone'].initial = instance.mobile_phone
			self.fields['old_email_confirmed'].initial = instance.email_confirmed
			self.fields['old_mobile_confirmed'].initial = instance.mobile_confirmed

	class Meta:
		model = MHLUser
		fields = ('first_name', 'last_name', 'title', 'gender', 'photo',
					'email', 'email_confirmed',
					'mobile_phone', 'phone', 'mobile_confirmed', 'skill', 'public_notes')
		widgets = { 
				'email_confirmed': forms.HiddenInput(),
				'mobile_confirmed': forms.HiddenInput()
			}

	def clean(self):
		cleaned_data = self.cleaned_data
		email_confirmed = cleaned_data['email_confirmed']
		mobile_confirmed = cleaned_data['mobile_confirmed']

		if not email_confirmed:
			cleaned_data['email'] = cleaned_data['old_email']
			cleaned_data['email_confirmed'] = cleaned_data['old_email_confirmed']
		if settings.CALL_ENABLE and not mobile_confirmed and cleaned_data['mobile_phone']:
			cleaned_data['mobile_phone'] = cleaned_data['old_mobile_phone']
			cleaned_data['mobile_confirmed'] = cleaned_data['old_mobile_confirmed']
		if not cleaned_data['mobile_phone']:
			cleaned_data['mobile_confirmed'] = False
		return cleaned_data


class BrokerUserForm(UserForm):
	non_field_warnings = None

	class Meta:
		model = MHLUser
		fields = ('first_name', 'last_name', 'title', 'gender', 'photo',
					'email', 'email_confirmed', 'address1', 'address2', 'city', 'state', 'zip',
					'mobile_phone', 'phone', 'mobile_confirmed')
		widgets = { 
				'email_confirmed': forms.HiddenInput(),
				'mobile_confirmed': forms.HiddenInput()
			}

	def __init__(self, data=None, files=None, instance=None, *args, **kwargs):
		super(BrokerUserForm, self).__init__(data=data, files=files, instance=instance, *args, **kwargs)
		self.fields['address1'].label = _('Office address1')
		self.fields['address2'].label = _('Office address2')
		self.fields['city'].label = _('Office city')
		self.fields['state'].label = _('Office state')
		self.fields['zip'].label = _('Office zip')

	def clean(self):
		cleaned_data = super(BrokerUserForm, self).clean()
		street = cleaned_data['address1']
		city = cleaned_data['city']
		state = cleaned_data['state']
		zip = cleaned_data['zip']

		if(self.instance):
			def compare(form, model, field):
				return form.cleaned_data[field] == model.__getattribute__(field)
			if(all(compare(self, self.instance, field) for field in 
					('address1', 'city', 'state', 'zip'))):
				self.cleaned_data['lat'] = self.instance.lat
				self.cleaned_data['longit'] = self.instance.longit
				return cleaned_data
		if ((street and city and state)) or ((street and zip)):
			results = geocode2(street, city, state, zip)
			if results['lat'] == 0.0 and results['lng'] == 0.0:
				from MHLogin.utils.admin_utils import mail_admins
				self.non_field_warnings = MSG_GEO_ADDRESS_INVALID
				mail_admins('Geocode error in Broker form save', 'Geocode lookup '
					'problems saving Broker: %s.\n\nGeocode message:\n%s' % 
					(self.instance.username, results['msg']))
			else:
				self.non_field_warnings = None
			cleaned_data['lat'] = results['lat']
			cleaned_data['longit'] = results['lng']
		else:
			raise forms.ValidationError(MSG_GEO_EMPTY)

		return cleaned_data


class PhysicianForm(forms.ModelForm):
	class Meta:
		model = Physician
		exclude = ('user')


class ChangePasswordForm(forms.Form):
	old_password = forms.CharField(widget=forms.PasswordInput(render_value=False), 
						label=_("Old Password"), required=False)
	new_password1 = forms.CharField(widget=forms.PasswordInput(render_value=False), 
						label=_("New Password"), required=False)
	new_password2 = forms.CharField(widget=forms.PasswordInput(render_value=False), 
						label=_("New Password Verify"), required=False)
	redirect_view = forms.CharField(widget=forms.HiddenInput(), required=False)

	def __init__(self, user, *args, **kwargs):
		super(forms.Form, self).__init__(*args, **kwargs)
		self.user = user

	def clean(self):
		if('new_password1' in self.cleaned_data and 'new_password2' in self.cleaned_data):
			pass1 = self.cleaned_data['new_password1']
			pass2 = self.cleaned_data['new_password2']
		else:
			return
		if (not self.cleaned_data['old_password']):
			raise forms.ValidationError(_("Old password needed."))
		if (self.cleaned_data['old_password'] and not pass1):
			raise forms.ValidationError(_("New password needed."))
		if (pass1 != pass2):
			raise forms.ValidationError(_("Passwords do not match."))
		if (self.cleaned_data['old_password'] == pass1):
			raise forms.ValidationError(_("New password needs to be different than the old password."))

		if(self.cleaned_data['old_password'] or
		   self.cleaned_data['new_password1'] or
		   self.cleaned_data['new_password2']):
			if(not self.user.check_password(self.cleaned_data['old_password'])):
				self._errors['old_password'] = self.error_class(["Password Invalid."])
		return self.cleaned_data


# Modify security questions form        
class SecurityQuestionsForm(forms.Form):
	security_question1 = forms.CharField(widget=forms.Select, label=_('Security Question1'))
	custom_question1 = forms.CharField(widget=forms.TextInput, required=False)
	security_answer1 = forms.CharField(widget=forms.TextInput, label=_('Security Answer1'), min_length=6)

	security_question2 = forms.CharField(widget=forms.Select, label=_('Security Question2'))
	custom_question2 = forms.CharField(widget=forms.TextInput, required=False)
	security_answer2 = forms.CharField(widget=forms.TextInput, label=_('Security Answer2'), min_length=6)

	security_question3 = forms.CharField(widget=forms.Select, label=_('Security Question3'))
	custom_question3 = forms.CharField(widget=forms.TextInput, required=False)
	security_answer3 = forms.CharField(widget=forms.TextInput, label=_('Security Answer3'), min_length=6)

	def clean(self):
		# First, store all of our questions in
		# cleaned_data['selected_question<n>'] so that we can move some of our
		# form validation logic out of the view, and help simplify the view.
		# This will also to make security question uniqueness easier to verify.
		if self.cleaned_data['security_question1'] == 'Custom Question':
			# If the custom question isn't given or didn't validate....
			if not 'custom_question1' in self.cleaned_data or self.cleaned_data['custom_question1'] == '':
				self._errors['custom_question1'] = self.error_class(['This field is required.'])
			else:
				self.cleaned_data['selected_question1'] = self.cleaned_data['custom_question1']
		else:
			self.cleaned_data['selected_question1'] = self.cleaned_data['security_question1']

		if self.cleaned_data['security_question2'] == 'Custom Question':
			# If the custom question isn't given or didn't validate....
			if not 'custom_question2' in self.cleaned_data or self.cleaned_data['custom_question2'] == '':
				self._errors['custom_question2'] = self.error_class(['This field is required.'])
			else:
				self.cleaned_data['selected_question2'] = self.cleaned_data['custom_question2']
		else:
			self.cleaned_data['selected_question2'] = self.cleaned_data['security_question2']

		if self.cleaned_data['security_question3'] == 'Custom Question':
			# If the custom question isn't given or didn't validate....
			if not 'custom_question3' in self.cleaned_data or self.cleaned_data['custom_question3'] == '':
				self._errors['custom_question3'] = self.error_class(['This field is required.'])
			else:
				self.cleaned_data['selected_question3'] = self.cleaned_data['custom_question3']
		else:
			self.cleaned_data['selected_question3'] = self.cleaned_data['security_question3']

		# Okay, now all of our questions are stored in 
		# self.cleaned_data['security_question<n>'].

		# Make sure we have 3 questions.
		if (not 'selected_question1' in self.cleaned_data or
			not 'selected_question2' in self.cleaned_data or
			not 'selected_question3' in self.cleaned_data):
			raise forms.ValidationError(_("A form validation error occurred."))

		# Make sure that the questions are all unique.
		if self.cleaned_data['selected_question1'] == self.cleaned_data['selected_question2'] \
			or self.cleaned_data['selected_question1'] == self.cleaned_data['selected_question3']:
			raise forms.ValidationError(_('All security questions must be unique.'))

		if self.cleaned_data['selected_question2'] == self.cleaned_data['selected_question3']:
			raise forms.ValidationError(_('All security questions must be unique.'))

		return self.cleaned_data


#update security form 
#by xlin 20111027
class UpdateSecurityForm(forms.Form):
	password = forms.CharField(widget=forms.PasswordInput(render_value=False), label=_("Password"))


class AddPracticeToProviderForm(forms.Form):
	pract_id = forms.IntegerField()
	assoc_id = forms.IntegerField()


class PracticesSearchForm(forms.Form):
	# Sample data:
	search_name = forms.CharField()


class PractIdAssociationForm(forms.Form):
	pract_id = forms.IntegerField()


class AssocIdAssociationForm(forms.Form):
	assoc_id = forms.IntegerField()


class nameSearchFormOld(forms.Form):
	# Sample data:
	# search.php?q=b&limit=15&timestamp=1297167007274
	q = forms.CharField()
	limit = forms.IntegerField(required=False, initial=5, min_value=1, max_value=100)
	# disregard timestamp argument
	# timestamp = forms.IntegerField()


class nameSearchForm(forms.Form):
	# Sample data:
	# search.php?q=b&limit=15&timestamp=1297167007274
	q = forms.CharField()
	limit = forms.IntegerField(required=False, initial=5, min_value=1, max_value=100)
	# disregard timestamp argument
	# timestamp = forms.IntegerField()


class ProximitySearchForm(forms.Form):
	zip = forms.CharField(required=False)
	proximity = forms.IntegerField()
	tab_type = forms.CharField()
	licensure = forms.CharField(required=False)


class CallForwardForm(forms.Form):
	forward = forms.ChoiceField(choices=FORWARD_CHOICES)


class BrokerForm(forms.ModelForm):
	old_pager = forms.CharField(widget=forms.HiddenInput(), required=False)
	old_pager_confirmed = forms.CharField(widget=forms.HiddenInput(), required=False)

	class Meta:
		model = Broker
		fields = ('office_phone', 'pager', 'pager_confirmed', 'pager_extension',
				'licensure_states')
		widgets = { 
				'pager_confirmed': forms.HiddenInput()
			}

	def __init__(self, data=None, files=None, instance=None, *args, **kwargs):
		super(BrokerForm, self).__init__(data=data, files=files, instance=instance, *args, **kwargs)
		if (instance):
			self.fields['old_pager'].initial = instance.pager
			self.fields['old_pager_confirmed'].initial = instance.pager_confirmed

	def clean(self):
		cleaned_data = self.cleaned_data
		pager_confirmed = cleaned_data['pager_confirmed']
		if settings.CALL_ENABLE and not pager_confirmed and cleaned_data['pager']:
			cleaned_data['pager'] = cleaned_data['old_pager']
			cleaned_data['pager_confirmed'] = cleaned_data['old_pager_confirmed']

		return cleaned_data

