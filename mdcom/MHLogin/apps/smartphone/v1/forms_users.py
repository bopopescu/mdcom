
import re
from django import forms

from MHLogin.MHLUsers.models import MHLUser
from MHLogin.utils.fields import MHLCheckboxInput

recipients_re = re.compile(r'[a-zA-Z ]$')


class UserSearchForm(forms.Form):
	name = forms.CharField()
	limit = forms.IntegerField(required=False, min_value=0)


class UserPhotoForm(forms.ModelForm):
	def __init__(self, data=None, files=None, instance=None, *args, **kwargs):
		super(UserPhotoForm, self).__init__(data=data, files=files, instance=instance, *args, **kwargs)

	class Meta:
		model = MHLUser
		fields = ('photo',)


class UserTabForm(forms.Form):
	is_only_user_tab = forms.BooleanField(required=False, widget=MHLCheckboxInput)
	show_my_favorite = forms.BooleanField(required=False, widget=MHLCheckboxInput)
