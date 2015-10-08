from MHLogin.followup.models import FollowUps
from MHLogin.utils.constants import DATE_FORMAT
from django import forms
from django.forms.widgets import DateInput
import datetime


class AddFollowUpForm(forms.ModelForm):
	due_date = forms.DateField(initial=datetime.date.today, widget=forms.DateInput(format=DATE_FORMAT))
	class Meta:
		model = FollowUps
		exclude = ('user', 'done', 'creation_date', 'completion_date', 'deleted', 'content_type', 'object_id')

class FollowUpForm(forms.ModelForm):
	class Meta:
		model = FollowUps
		exclude = ('user', 'creation_date', 'completion_date', 'deleted', 'content_type', 'object_id')
		widgets = {
			'due_date': DateInput(format=DATE_FORMAT),
		}
