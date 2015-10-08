
from django import forms
from django.forms import ModelForm
from django.contrib.auth.models import User

from MHLogin.MHLCallGroups.models import CallGroup
from MHLogin.MHLCallGroups.Scheduler.models import EventEntry, EVENT_TYPE_CHOICES,\
	ONCALL_LEVEL_CHOICES, ONCALL_STATUS_CHOICES
from MHLogin.MHLCallGroups.Scheduler.models import EVENT_STATUS_CHOICES

class EventModelForm(ModelForm):	
	class Meta:
		model = EventEntry
		fields = ('callGroup', 'title', 'startDate', 'endDate', 'eventType', 'oncallPerson', 'oncallLevel',
			'oncallStatus', 'eventStatus', 'notifyState', 'whoCanModify', 'checkString')
		widgets = { 
		}

class EventEntryForm(forms.Form):
	tempid = forms.DecimalField()
	callGroup = forms.ModelMultipleChoiceField(CallGroup)
	title = forms.CharField(max_length=255)
	startDate = forms.DateTimeField(input_formats=['%Y-%m-%d %H:%M:%S'])
	endDate = forms.DateTimeField(input_formats=['%Y-%m-%d %H:%M:%S'])
	eventType = forms.ChoiceField(choices=EVENT_TYPE_CHOICES)
	oncallPerson = forms.ModelMultipleChoiceField(User)
	oncallLevel = forms.ChoiceField(choices=ONCALL_LEVEL_CHOICES)
	oncallStatus = forms.ChoiceField(choices=ONCALL_STATUS_CHOICES)
	creator = forms.ModelMultipleChoiceField(User)
	eventStatus = forms.ChoiceField(choices=EVENT_STATUS_CHOICES)
	checkString = forms.CharField(max_length=10)

class DateEntryForm(forms.Form):
# we should actually only display callgroups associated with the user
#	callGroup = forms.ModelMultipleChoiceField(queryset=CallGroup.objects.all())
	fromDate = forms.DateTimeField(input_formats=['%Y-%m-%d %H:%M:%S'])
	toDate = forms.DateTimeField(input_formats=['%Y-%m-%d %H:%M:%S'])

class OncallForm(forms.Form):
# we should actually only display callgroup associated with the user
	callGroup = forms.ModelMultipleChoiceField(queryset=CallGroup.objects.all())
	curDate = forms.DateTimeField(input_formats=['%Y-%m-%d %H:%M:%S'])

class BulkEventForm(forms.Form):
	data = forms.CharField(widget=forms.Textarea)  #widgets.Textarea(attrs={'rows':10, 'cols':80}) 

