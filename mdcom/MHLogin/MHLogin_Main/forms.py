
from django import forms
from django.forms import ModelForm

from MHLogin.MHLUsers.models import MHLUser

class LoginForm(forms.Form):
	username = forms.CharField(max_length=30)
	password = forms.CharField(widget=forms.PasswordInput(),max_length=20)
	next = forms.CharField(widget=forms.HiddenInput(), required=False)

class ToSAcceptForm(forms.Form):
	accept = forms.BooleanField(widget=forms.HiddenInput, initial=True)

class ToSRejectForm(forms.Form):
	reject = forms.BooleanField(widget=forms.HiddenInput, initial=True)
