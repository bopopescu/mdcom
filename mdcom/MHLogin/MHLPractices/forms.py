
import re

from django.core.exceptions import ValidationError
from django.forms.fields import TimeField, IntegerField, MultipleChoiceField
from django import forms
from django.forms.forms import Form
from django.forms.models import ModelForm
from django.forms.extras.widgets import SelectDateWidget
from django.utils.translation import ugettext_lazy as _

from MHLogin.MHLPractices.models import PracticeHours, PracticeHolidays, \
	PracticeLocation, AccessNumber
from MHLogin.utils.geocode import geocode2
from MHLogin.MHLUsers.models import MHLUser

from MHLogin.utils.constants import CALLER_ANSSVC_CHOICES, TIME_ZONES_CHOICES


HOURS_HELP_TEXT = _('HH:MM 24 hour format')
LUNCH_DURATION_HELP_TEXT = _("In minutes")
REQUIRED_ERROR = _("This field is required.")


class HoursForm(ModelForm):
	open = TimeField(required=False, help_text=HOURS_HELP_TEXT)
	close = TimeField(required=False, help_text=HOURS_HELP_TEXT)
	lunch_start = TimeField(required=False, help_text=HOURS_HELP_TEXT)
	lunch_duration = IntegerField(required=False, help_text=LUNCH_DURATION_HELP_TEXT)

	class Meta:
		model = PracticeHours
		exclude = ['practice_location']

	def clean(self):
		if(not 'open' in self.cleaned_data or
		   not 'close' in self.cleaned_data or
		   not 'lunch_start' in self.cleaned_data or
		   not 'lunch_duration' in self.cleaned_data):
			if(open in self.cleaned_data and not self.cleaned_data['open']):
				self._errors = {}
			return self.cleaned_data

		if not self.cleaned_data['open']:
			self.cleaned_data['close'] = '17:00'
			self.cleaned_data['lunch_start'] = '12:00'
			self.cleaned_data['lunch_duration'] = '0'
		else:
			if(not self.cleaned_data['close']):
				self._errors['close'] = self.error_class([REQUIRED_ERROR])
			#'and duration != 0' is required because the first half evaluates to False in that case
			if(not self.cleaned_data['lunch_duration'] and self.cleaned_data['lunch_duration'] != 0):
				self._errors['lunch_duration'] = self.error_class([REQUIRED_ERROR])
			if (not self.cleaned_data['lunch_start'] and self.cleaned_data['lunch_duration'] == 0):
				self.cleaned_data['lunch_start'] = '12:00'
			elif (not self.cleaned_data['lunch_start']):
				self._errors['lunch_start'] = self.error_class([REQUIRED_ERROR])

		return self.cleaned_data


class HolidaysForm(ModelForm):
	class Meta:
		model = PracticeHolidays
		exclude = ['practice_location']
		widgets = {'designated_day': SelectDateWidget()}
#	name = forms.CharField(max_length=34, required=False)
#	designated_day = forms.DateField(widget=SelectDateWidget())


class RemoveForm(Form):
	remove = MultipleChoiceField(required=False, choices=())

	def __init__(self, request, choices, *args, **kwargs):
		super(Form, self).__init__(request, *args, **kwargs)
		self.fields['remove'].choices = choices

phone_re = re.compile('1?\d{10}$')


class PracticeProfileForm(ModelForm):
	def __init__(self, *args, **kwargs):
		super(PracticeProfileForm, self).__init__(*args, **kwargs)
		self.fields['time_zone'].choices = TIME_ZONES_CHOICES
	
	#use_zip = BooleanField(required=False)
	def clean_practice_name(self):
		practice_name = self.cleaned_data['practice_name'].strip()
		practices = PracticeLocation.full_objects.filter(\
				practice_name=practice_name)
		if self.instance.id:
			practices = practices.exclude(id=self.instance.id)
		if practices:
			raise ValidationError(_('This organization has been used.'))
		return practice_name

	non_field_warnings = None

	def clean(self):
		cleaned_data = self.cleaned_data
		street = cleaned_data['practice_address1']
		city = cleaned_data['practice_city']
		state = cleaned_data['practice_state']
		zip = cleaned_data['practice_zip']

		if(self.instance):

			def compare(form, model, field):
				return form.cleaned_data[field] == model.__getattribute__(field)
			if(all(compare(self, self.instance, field) for field in ('practice_address1', 
					'practice_city', 'practice_state', 'practice_zip'))):
				self.cleaned_data['practice_lat'] = self.instance.practice_lat
				self.cleaned_data['practice_longit'] = self.instance.practice_longit
				return cleaned_data
		if ((street and city and state)) or ((street and zip)):
			results = geocode2(street, city, state, zip)
			if results['lat'] == 0.0 and results['lng'] == 0.0:
				from MHLogin.utils.admin_utils import mail_admins
				self.non_field_warnings = _('Warning: Your form has been saved but '
					'determining coordinates from the entered address was not successful.  '
					'Please verify correctness, if this persists our staff will be notified.  '
					'Our apologies, thanks for your patience - DoctorCom staff.')
				mail_admins('Geocode error in Practice form save', 'Geocode lookup '
					'problems saving PracticeLocation: %s.\n\nGeocode message:\n%s' % 
					(self.instance.practice_name, results['msg']))
			else:
				self.non_field_warnings = None
			cleaned_data['practice_lat'] = results['lat']
			cleaned_data['practice_longit'] = results['lng']
		else:
			raise ValidationError(_('At a minimum, please enter in either '
				'street, city and state or street and zip'))
		return cleaned_data

	class Meta:
		model = PracticeLocation
		fields = (
				'practice_name',
				'practice_zip',
				'backline_phone',
				'practice_phone',
				'time_zone',
				'practice_address1',
				'practice_address2',
				'practice_city',
				'practice_state',
				'practice_photo',
			)


class AccessNumberForm(ModelForm):
	class Meta:
		model = AccessNumber
		fields = ('number', 'description')


class ActiveAccountForm(Form):
	email = forms.CharField(widget=forms.HiddenInput)
	activeCode = forms.CharField(widget=forms.HiddenInput)

	password1 = forms.CharField(widget=forms.PasswordInput, label=_("Password"))
	password2 = forms.CharField(widget=forms.PasswordInput, label=_("Password Verify"))

	def __init__(self, data=None, initial=None, *args, **kwargs):
		super(ActiveAccountForm, self).__init__(data=data, initial=initial, *args, **kwargs)
		if initial:
			self.fields['email'].initial = initial["email"]
			self.fields['activeCode'].initial = initial["activeCode"]
			self.cleaned_data = {}
			self.cleaned_data['email'] = initial["email"]
			self.cleaned_data['activeCode'] = initial["activeCode"]
		if data:
			self.fields['email'].initial = data["email"]
			self.fields['activeCode'].initial = data["activeCode"]

	def clean_password2(self):
		password1 = self.cleaned_data['password1']
		password2 = self.cleaned_data['password2']
		if password1 != password2:
			raise forms.ValidationError(_('\"Password Verify\" is not same with \"Password\"'))
		return password2


class PreferenceProviderForm(ModelForm):
	class Meta:
		model = MHLUser
		fields = ('time_setting', 'time_zone', 'refer_forward')
		widgets = {'time_setting': forms.RadioSelect(),
				'refer_forward': forms.RadioSelect()}

class PreferenceForm(ModelForm):
	class Meta:
		model = MHLUser
		fields = ('time_setting', 'time_zone')
		widgets = {'time_setting': forms.RadioSelect()}

class CallerAnssvcForm(forms.Form):
	forward = forms.ChoiceField(choices=CALLER_ANSSVC_CHOICES)




