# -*- coding: utf-8 -*-
'''
Created on 2012-9-28

@author: mwang
'''
from django import forms

class ProviderSearchForm(forms.Form):
	name = forms.CharField(required=False)
	specialty = forms.CharField(required=False)
	hospital = forms.CharField(required=False)
	practice = forms.CharField(required=False)
#	address = forms.CharField(required=False)
#	city = forms.CharField(required=False)
#	state = forms.CharField(required=False)
	zip = forms.CharField(required=False)
	distance = forms.IntegerField(required=False)
	limit = forms.IntegerField(required=False)

class StaffSearchForm(forms.Form):
	name = forms.CharField(required=False)
	hospital = forms.CharField(required=False)
	practice = forms.CharField(required=False)
	limit = forms.IntegerField(required=False)