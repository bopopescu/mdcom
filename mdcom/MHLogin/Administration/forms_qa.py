# -*- coding: utf-8 -*-
'''
Created on 2012-10-25

@author: mwang
'''

from django import forms

from MHLogin.MHLPractices.models import PracticeLocation
from MHLogin.utils.constants import OFFICE_STAFF_INVITE_CHOICES

class GenerateUsersForm(forms.Form):
	practices = forms.ModelChoiceField(queryset=PracticeLocation.objects.all().
			select_related('id', 'practice_name'))
	user_types = forms.ChoiceField(choices=OFFICE_STAFF_INVITE_CHOICES)
	number = forms.IntegerField(max_value=1000000, min_value=1)
	user_name_start = forms.CharField()

class ReGenerateKeyForm(forms.Form):
	user_id_from = forms.IntegerField(required=False)
	user_id_to = forms.IntegerField(required=False)
	username = forms.CharField(required=False)
