import re
from django.utils.translation import ugettext_lazy as _

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


class TwiMLCallbackForm(forms.Form):
	CallSid = forms.CharField()
	caller_user_id = forms.IntegerField()
	called_number = USPhoneNumberField(required=False)
	called_user_id = forms.IntegerField(required=False)
	called_practice_id = forms.IntegerField(required=False)

	def clean(self):
		if('called_number' in self.cleaned_data and not self.cleaned_data['called_number'] 
			and 'called_user_id' in self.cleaned_data and not self.cleaned_data['called_user_id']
			and 'called_practice_id' in self.cleaned_data and not self.cleaned_data['called_practice_id']):
			raise forms.ValidationError(_("No valid called number"))
		return self.cleaned_data
