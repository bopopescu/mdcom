from MHLogin.utils.fields import MHLPhoneNumberField
from django import forms
from django.utils.translation import ugettext_lazy as _

PHONE_NUMBER_HELP_TEXT = _("Please enter only digits. (e.g., 8005555555)")

class ValidateForm(forms.Form):
	recipient = forms.CharField(max_length=200)
	code = forms.CharField(max_length=4)
	type = forms.CharField()

class SendCodeForm(forms.Form):
	recipient = forms.CharField(max_length=200)
	type = forms.CharField()
	init = forms.BooleanField(required=False)

class ContactInfoForm(forms.Form):
	mobile_phone = forms.CharField(max_length=15, label=_("Mobile Phone"), help_text=PHONE_NUMBER_HELP_TEXT)
	old_mobile_phone = forms.CharField(widget=forms.HiddenInput())
	mobile_confirmed = forms.CharField(widget=forms.HiddenInput())

	pager = forms.CharField(required=False, label=_("Pager"), help_text=PHONE_NUMBER_HELP_TEXT)
	old_pager = forms.CharField(widget=forms.HiddenInput(), required=False)
	pager_confirmed = forms.CharField(widget=forms.HiddenInput())

	email = forms.EmailField( max_length=200, label=_("E-mail address"))
	old_email = forms.CharField(widget=forms.HiddenInput())
	email_confirmed = forms.CharField(widget=forms.HiddenInput())

	def __init__(self, mhluser=None, login_user=None, request=None,  *args, **kwargs):
		super(forms.Form, self).__init__(request, *args, **kwargs)
		if mhluser:
			self.fields['mobile_phone'].initial = mhluser.mobile_phone
			self.fields['old_mobile_phone'].initial = mhluser.mobile_phone
			self.fields['mobile_confirmed'].initial = mhluser.mobile_confirmed
	
			self.fields['email'].initial = mhluser.email
			self.fields['old_email'].initial = mhluser.email
			self.fields['email_confirmed'].initial = mhluser.email_confirmed

		if login_user:
			self.fields['pager'].initial = login_user.pager
			self.fields['old_pager'].initial = login_user.pager
			self.fields['pager_confirmed'].initial = login_user.pager_confirmed

#	def clean(self):
#		cleaned_data = self.cleaned_data
#
#		email_confirmed = cleaned_data['email_confirmed']
#		mobile_confirmed = cleaned_data['mobile_confirmed']
#		pager_confirmed = cleaned_data['pager_confirmed']
#
#		if not email_confirmed:
#			cleaned_data['email'] = cleaned_data['old_email']
#			cleaned_data['email_confirmed'] = cleaned_data['old_email_confirmed']
#		if not mobile_confirmed:
#			cleaned_data['mobile_phone'] = cleaned_data['old_mobile_phone']
#			cleaned_data['mobile_confirmed'] = cleaned_data['old_mobile_confirmed']
#		if cleaned_data['pager'] and not pager_confirmed:
#			cleaned_data['pager'] = cleaned_data['old_pager']
#			cleaned_data['pager_confirmed'] = cleaned_data['old_pager_confirmed']
#		return cleaned_data

