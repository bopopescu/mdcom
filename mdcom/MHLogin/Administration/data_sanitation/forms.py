
from django import forms
from django.utils.translation import ugettext_lazy as _


class sanitationConfirmationForm(forms.Form):
	confirmationString = forms.CharField()

	def clean_confirmationString(self):
		confirmation = self.cleaned_data['confirmationString']

		if (confirmation != _('YES, I AM ABSOLUTELY SURE.')):
			raise forms.ValidationError(_("Please enter the string exactly as it appears, "
				"in all-caps, and with all punctuation between (but exclusive of) the quotes."))

		return confirmation
