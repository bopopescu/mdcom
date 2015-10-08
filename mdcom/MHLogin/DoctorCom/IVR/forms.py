from django import forms
from django.forms import ModelForm
from django.forms.util import ErrorList
from django.utils.translation import ugettext_lazy as _

from models import VMBox_Config

class VMBox_ConfigForm(ModelForm):
	class Meta:
		model = VMBox_Config
		fields = ['notification_email', 'notification_sms', 'notification_page']

	def clean_pin(self):
		import re
		p1 = re.compile('\d+$')
		p2 = re.compile('\d{4,8}$')

		pin = self.cleaned_data['pin']
		if (not p1.match(pin)):
			raise forms.ValidationError(_('Please enter only digits.'))
		if (not p2.match(pin)):
			raise forms.ValidationError(_('Incorrect length: Please four to eight digits.'))

		return pin

class PinChangeForm(forms.Form):
	password = forms.CharField(widget=forms.PasswordInput, label=_("Password"))
	pin1 = forms.CharField(widget=forms.PasswordInput, min_length=4, max_length=8, label=_("Enter new pin number"))
	pin2 = forms.CharField(widget=forms.PasswordInput, min_length=4, max_length=8, label=_("Confirm new pin number"))

	user = None

#	def is_valid(self, user):
#		super('PinChangeForm', self).is_valid()
#		# Check the password
#		if (not user.check_password(self.cleaned_data['password'])):
#			if (not 'password' in self._errors):
#				self._errors['password'] = ErrorList(['Password is incorrect'])
#			else:
#				self._errors['password'].append('Password is incorrect')

	def clean_pin1(self):
		import re
		p1 = re.compile('\d+$')
		p2 = re.compile('\d{4,8}$')

		pin = self.cleaned_data['pin1']
		if (not p1.match(pin)):
			raise forms.ValidationError(_('Please enter only digits.'))
		if (not p2.match(pin)):
			raise forms.ValidationError(_('Incorrect length: Please four to eight digits.'))
		return pin
			
	def clean_pin2(self):
		if (not 'pin1' in self.cleaned_data):
			return self.cleaned_data['pin2']
		pin1 = self.cleaned_data['pin1']
		pin2 = self.cleaned_data['pin2']
		
		if (pin1 != pin2):
			raise forms.ValidationError(_('PINs don\'t match. Please enter them again.'))

		return pin2
	
	def clean_password(self):
		if (not self.user):
			raise Exception(_("User must be defined"))
		password = self.cleaned_data['password']
		if (not self.user.check_password(password)):
			raise forms.ValidationError(_('Password incorrect.'))
		return None

