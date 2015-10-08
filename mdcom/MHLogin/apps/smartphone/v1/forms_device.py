import re

from django import forms
from django.utils.translation import ugettext_lazy as _

from MHLogin.utils.fields import MHLCheckboxInput

from ..models import PLATFORM_CHOICES


class CheckUserForm(forms.Form):
	username = forms.CharField(max_length=30)


class AssociationForm(forms.Form):
	username = forms.CharField(max_length=30)
	password = forms.CharField(max_length=20)
	device_id = forms.CharField(max_length=255)
	app_version = forms.CharField()
	platform = forms.ChoiceField(choices=PLATFORM_CHOICES)
	name = forms.CharField(max_length=255, required=False)
	# Consider the compatibility, use the key: "allow_staff_login" -- 
	# it's optional, distinguish different client version
	allow_staff_login = forms.BooleanField(required=False, widget=MHLCheckboxInput)

base64_regex = re.compile(r'^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$')


class CheckInForm(forms.Form):
	key = forms.CharField(required=False)
	rx_timestamp = forms.IntegerField(required=False)
	tx_timestamp = forms.IntegerField(required=False)

	def clean_key(self):
		cleaned = self.cleaned_data['key']
		if (not base64_regex.match(cleaned)):
			raise forms.ValidationError(_('Key doesn\'t appear to be a valid secret.'))
		return cleaned


class PasswordForm(forms.Form):
	password = forms.CharField()


class VersionUpdateForm(forms.Form):
	app_version = forms.CharField()

