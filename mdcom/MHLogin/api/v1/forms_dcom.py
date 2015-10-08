import re

from django import forms
try:
	from django_localflavor_us.forms import USPhoneNumberField
except ImportError:  # remove when django 1.5 fully integrated
	from django.contrib.localflavor.us.forms import USPhoneNumberField


class USNumberForm(forms.Form):
	number = USPhoneNumberField(required=False)
	caller_number = USPhoneNumberField()

	def clean_number(self):
		return re.sub(r'[^0-9]', '', self.cleaned_data['number'])

	def clean_caller_number(self):
		return re.sub(r'[^0-9]', '', self.cleaned_data['caller_number'])


class PagerNumberForm(forms.Form):
	number = forms.CharField(max_length=20, min_length=1)
