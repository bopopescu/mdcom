# -*- coding: utf-8 -*-
'''
Created on 2012-9-26

@author: mwang
'''
from django import forms

class SiteSearchForm(forms.Form):
	name = forms.CharField(required=False)
	address = forms.CharField(required=False)
	city = forms.CharField(required=False)
	state = forms.CharField(required=False)
	zip = forms.CharField(required=False)
	limit = forms.IntegerField(required=False)
