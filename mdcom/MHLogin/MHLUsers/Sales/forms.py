
from django import forms

from MHLogin.MHLUsers.models import MHLUser


class SalesPersonForm(forms.ModelForm):
	""" Sales person form """
	class Meta:
		model = MHLUser
		fields = ('first_name', 'last_name', 'email', 'address1', 'address2',
				'city', 'state', 'zip', 'mobile_phone', 'phone')

