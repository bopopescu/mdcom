# -*- coding: utf-8 -*-
'''
Created on 2012-9-17

@author: mwang
'''

from django import forms
from django.utils.translation import ugettext_lazy as _


class TaskListForm(forms.Form):
	done_from = forms.BooleanField(required=False)
	done_to = forms.BooleanField(required=False)
	due_from_timestamp = forms.IntegerField(required=False)
	due_to_timestamp = forms.IntegerField(required=False)
	creation_from_timestamp = forms.IntegerField(required=False)
	creation_to_timestamp = forms.IntegerField(required=False)
	count = forms.IntegerField(required=False)
	completed = forms.BooleanField(required=False)
	exclude_id = forms.CharField(required=False)

class TaskDeltaForm(forms.Form):
	timestamp = forms.IntegerField()

class NewTaskForm(forms.Form):
	due = forms.IntegerField()
	priority = forms.IntegerField()
	description = forms.CharField()
	note = forms.CharField(required=False)
	
	def clean_priority(self):
		priority = self.cleaned_data['priority']
		if (priority != 1 and priority != 5 and priority != 10):
			raise forms.ValidationError(_('Invalid priority. Values must be 1, 5, or 10.'))
		return priority
	
	def clean_due(self):
		due = self.cleaned_data['due']
		if (due < 0 or due > 4102473600):
			raise forms.ValidationError(_('The timestamp is outside of the allowable range.'))
		return due

class UpdateTaskForm(forms.Form):
	due = forms.IntegerField(required=False)
	priority = forms.IntegerField(required=False)
	description = forms.CharField(required=False)
	note = forms.CharField(required=False)
	completed = forms.BooleanField(required=False)
	
	def clean(self):
		data = self.cleaned_data
		
		if ('due' in data and not data['due']):
			del(data['due'])
		if ('priority' in data and not data['priority']):
			del(data['priority'])
		if ('description' in data and not data['description']):
			del(data['description'])
		if ('note' in data and not data['note']):
			del(data['note'])
		if ('completed' in self.data and self.data['completed'] == ''):
			del(data['completed'])
		
		if (not 'due' in data and
				not 'priority' in data and
				not 'description' in data and
				not 'note' in data and
				not 'completed' in data):
			raise forms.ValidationError(_('While all fields are optional, at least one field must be given.'))
		
		return data
	
	def clean_priority(self):
		priority = self.cleaned_data['priority']
		if (priority == None):
			return priority
		if (priority != 1 and priority != 5 and priority != 10):
			raise forms.ValidationError(_('Invalid priority. Values must be 1, 5, or 10.'))
		return priority

