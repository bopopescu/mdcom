
import re

from django import forms
from MHLogin.utils.constants import USER_TYPE_OFFICE_MANAGER

try:
	from django_localflavor_us.forms import USPhoneNumberField
except ImportError:  # remove when django 1.5 fully integrated
	from django.contrib.localflavor.us.forms import USPhoneNumberField

base64_regex = re.compile(r'^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$')


class GetKeyForm(forms.Form):
	secret = forms.CharField()

	def clean_secret(self):
		cleaned = self.cleaned_data['secret']
		if (not base64_regex.match(cleaned)):
			raise forms.ValidationError('Secret doesn\'t appear to be a valid secret.')
		return cleaned


class SetPracticeForm(forms.Form):
	current_practice = forms.IntegerField(required=False)

	def __init__(self, data=None, user_type=None, *args, **kwargs):
		super(forms.Form, self).__init__(data=data, *args, **kwargs)
		if user_type:
			self.user_type = int(user_type)

	def clean_current_practice(self):
		current_practice = self.cleaned_data['current_practice']
		if not current_practice:
			# If user is Office Staff/Manager, his current_practice can't be empty.
			if USER_TYPE_OFFICE_MANAGER == self.user_type:
				raise forms.ValidationError(_("This field is required."))
			else:
				return current_practice
		return current_practice

class SetSiteForm(forms.Form):
	current_site = forms.IntegerField(required=False)

fwd_pref_choices = (
	('Mobile', 'Mobile'),
	('Office', 'Office'),
	('Other', 'Other'),
	('Voicemail', 'Voicemail'),
)


class GetFwdPrefsForm(forms.Form):
	forward = forms.ChoiceField(choices=fwd_pref_choices)


class UpdateMobileForm(forms.Form):
	mobile_phone = USPhoneNumberField()

