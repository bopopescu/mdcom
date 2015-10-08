import re

from django import forms
from django.utils.translation import ugettext_lazy as _

hex_re = re.compile(r'^[0-9a-fA-F]*$')


class DeviceIDForm(forms.Form):
	device_id = forms.CharField(max_length=32, min_length=32)

	def clean_device_id(self):
		did = self.cleaned_data['device_id']
		if (not hex_re.match(did)):
			raise forms.ValidationError(_('Invalid device id.'))
		return did


class PushTokenForm(forms.Form):
	token = forms.CharField(max_length=255, min_length=64)
#	def clean_token(self):
#		if(hex_re.match(self.cleaned_data['token'])):
#			return self.cleaned_data['token']
#		else:
#			raise forms.ValidationError(_('Invalid token'))
