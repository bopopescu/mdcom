
from django import forms
from django.forms.util import ErrorList
from django.utils.encoding import force_text
from django.utils.html import format_html, format_html_join
from django.utils.translation import ugettext as _


from MHLogin.MHLUsers.validators import validate_phone


class PasswordForgotForm(forms.Form):
	username = forms.CharField(required=False, label=_('Username'))
	email = forms.EmailField(required=False, label=_('Email'))
	mobile_phone = forms.CharField(required=False, label=_('Mobile'))

	def clean_mobile_phone(self):
		# Normalize US phone
		if self.cleaned_data['mobile_phone']:
			validate_phone(self.cleaned_data['mobile_phone'])
		return self.cleaned_data['mobile_phone']

	def clean(self):
		if len(self.changed_data) != 2:
			raise forms.ValidationError(_("Please enter two fields."))

		return super(PasswordForgotForm, self).clean()

	def get_query(self):
		""" field names are same as MHLUser fields """
		return {field: self.cleaned_data[field] for field in self.changed_data}


class PasswordResetForm(forms.Form):
	password1 = forms.CharField(label=_('New password'), widget=forms.PasswordInput)
	password2 = forms.CharField(label=_('New password (confirm)'), widget=forms.PasswordInput)

	def __init__(self, user, *args, **kwargs):
		self._user = user  # cache user and validate in clean
		super(PasswordResetForm, self).__init__(*args, **kwargs)

	def clean(self):
		if len(self.changed_data) != 2:
			raise forms.ValidationError(_("Please enter twice to confirm."))
		password1 = self.cleaned_data['password1']
		password2 = self.cleaned_data['password2']
		if password1 != password2:
			raise forms.ValidationError(_("Passwords do not match."))
		if self._user.check_password(password2):
			raise forms.ValidationError(_("Password hash signature matches, "
				"leaving it unchanged."))

		return super(PasswordResetForm, self).clean()


class FormErrors(ErrorList):
	def as_div(self):
		err = '' if not self else format_html('<div class="errorlist">{0}</div>', 
			format_html_join(', ', '{0}', ((force_text(e),) for e in self)))
		return err

