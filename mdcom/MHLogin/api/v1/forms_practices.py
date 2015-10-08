# -*- coding: utf-8 -*-
'''
Created on 2012-9-24

@author: mwang
'''
from django import forms

class PracticeSearchForm(forms.Form):
	practice_name = forms.CharField(required=False)
	practice_address = forms.CharField(required=False)
	practice_city = forms.CharField(required=False)
	practice_state = forms.CharField(required=False)
	practice_zip = forms.CharField(required=False)
	limit = forms.IntegerField(required=False)
