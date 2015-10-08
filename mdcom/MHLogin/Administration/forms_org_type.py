import re
from django import forms
from django.utils.translation import ugettext_lazy as _

type_ids_re = re.compile(r'(\d+,)*\d+$')


class CheckSubTypeForm(forms.Form):
	type_ids = forms.CharField()
	parent_type_id = forms.CharField()

	def clean_type_ids(self):
		cleaned = self.cleaned_data['type_ids']
		type_ids = []
		if cleaned:
			if (not type_ids_re.match(cleaned)):
				raise forms.ValidationError(_('type id list isn\'t of the correct form.'))
			type_ids = cleaned.split(',')
		return type_ids

