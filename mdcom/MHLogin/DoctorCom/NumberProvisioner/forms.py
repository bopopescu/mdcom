
from django import forms
from django.forms.util import ErrorList

from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from MHLogin.DoctorCom.NumberProvisioner.models import TOLL_FREE_CODES, INVALID_CODES

class LocalNumberForm(forms.Form):
	area_code = forms.CharField(max_length=3, min_length=3, label='Your desired Area Code: ')
	pin = forms.CharField(max_length=8, min_length=4, label="PIN number for Voicemail: ")

	mdcom_phone = ''
	mdcom_phone_sid = ''

	def clean_area_code(self):
		import re
		from MHLogin.DoctorCom.NumberProvisioner.models import NumberPool
		from MHLogin.DoctorCom.NumberProvisioner.views import _removeNumberPoolNumber
		from MHLogin.DoctorCom.NumberProvisioner.utils import twilio_ProvisionNewLocalNumber

		area_code = self.cleaned_data['area_code']
		
		p1 = re.compile('\d{3}$')
		if (not p1.match(area_code)):
			raise forms.ValidationError(_('Invalid input: Please enter three digits.'))
		
		p2 = re.compile('[2-9][0-8]\d')
		if (not p2.match(area_code)):
			raise forms.ValidationError(_('Invalid area code. The first digit may only be 2-9, the second digit may only be 0-8, and the third digit may only be 0-9.'))
		
		if (area_code in TOLL_FREE_CODES or area_code in INVALID_CODES):
			raise forms.ValidationError(_('Invalid area code. Local area codes only, please.'))

		if settings.CALL_ENABLE:
			new_number = None
			# first, see if any numbers in the number pool has the given area code
			numberPoolResults = NumberPool.objects.filter(area_code=area_code)
			if (numberPoolResults.count()):
				# Give the user the first record in the number pool.
				new_number = _removeNumberPoolNumber(numberPoolResults)
			# This is another if statement (rather than else or elif) because
			# _assignNumberPoolNumber returns False if the number pool is
			# exhausted between the above count check and when it goes to delete.
			if (not new_number):
				new_number = twilio_ProvisionNewLocalNumber(area_code)
			if (not new_number or not new_number[0]):
				# No number was provisioned because none was available in the
				# area code. Modify the form to indicate a validation error,
				# with a message indicating the problem.
				raise forms.ValidationError(_("It seems your area code is wrong. Please try again."))

			self.mdcom_phone = new_number[0]
			self.mdcom_phone_sid = new_number[1]
		else:
			import random
			new_number = random.randint(9001000000, 9009999999)
			self.mdcom_phone = new_number
			self.mdcom_phone_sid = new_number

		return area_code

	def add_area_code_error(self, msg):
		"""This method is necessary because it's generally considered bad form
		to access the form's _errors dictionary from outside of the object."""
		
		if (not 'area_code' in self._errors):
			self._errors["area_code"] = ErrorList([msg])
		else:
			self._errors["area_code"].append(msg)

	def clean_pin(self):
		import re
		p1 = re.compile('\d+$')
		p2 = re.compile('\d{4,8}$')

		pin = self.cleaned_data['pin']
		if (not p1.match(pin)):
			raise forms.ValidationError(_('Please enter only digits.'))
		if (not p2.match(pin)):
			raise forms.ValidationError(_('Incorrect length: Please enter four to eight digits.'))

		return pin


class TollFreeNumberForm(forms.Form):
	area_code = forms.CharField(max_length=3, min_length=3)
	pin = forms.CharField(max_length=8, min_length=4, label="PIN number for Voicemail")

	def clean_area_code(self):
		import re
		
		area_code = self.cleaned_data['area_code']
		
		p1 = re.compile('\d{3}$')
		if (not p1.match(area_code)):
			raise forms.ValidationError(_('Invalid input: Please enter three digits.'))
		
		if (not area_code in TOLL_FREE_CODES):
			raise forms.ValidationError(_('Invalid area code. Toll-free area codes only, please.'))
		
		return area_code

