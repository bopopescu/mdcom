from MHLogin.utils.constants import MANAGER_INVITE_CHOICES
from django import forms
from django.utils.translation import ugettext as _

INVITE_TYPE_CHOICES = (
	(1, _('DoctorCom')),
	(2, _('Practice')),
)


class NewInviteForm(forms.Form):
	email = forms.EmailField()
	note = forms.CharField(required=False)
	invite_user_type = forms.ChoiceField(choices=MANAGER_INVITE_CHOICES)
	invite_type = forms.ChoiceField(choices=INVITE_TYPE_CHOICES)


class ResendInviteForm(forms.Form):
	note = forms.CharField(required=False)


class HandleInviteForm(forms.Form):
	invite_type = forms.IntegerField(required=True)

