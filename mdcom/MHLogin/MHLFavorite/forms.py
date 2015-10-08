#-*- coding: utf-8 -*-
'''
Created on 2013-5-28

@author: wxin
'''
from django import forms

from MHLogin.utils.fields import MHLCheckboxInput
from MHLogin.MHLFavorite.utils import OBJECT_TYPE_FLAG_OPTS

class FavoriteListForm(forms.Form):
	object_type_flag = forms.ChoiceField(required=False, choices=OBJECT_TYPE_FLAG_OPTS)

class ToggleFavoriteForm(forms.Form):
	object_type_flag = forms.ChoiceField(choices=OBJECT_TYPE_FLAG_OPTS)
	object_id = forms.IntegerField()
	is_favorite = forms.BooleanField(required=False, widget=MHLCheckboxInput)

