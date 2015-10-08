
import re
import datetime

from django import forms
from django.conf import settings
from django.forms.util import ErrorList
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _

from MHLogin.DoctorCom.Messaging.models import REFER_STATUS, MessageRefer
from MHLogin.DoctorCom.models import MessageTemp
from MHLogin.MHLPractices.models import PracticeLocation
from MHLogin.MHLUsers.models import MHLUser, Office_Manager
from MHLogin.utils.constants import GENDER_CHOICES,DATE_FORMAT
from MHLogin.utils.mh_logging import get_standard_logger

# Setting up logging
logger = get_standard_logger('%s/DoctorCom/Messaging/forms.log' % (settings.LOGGING_ROOT),
							'DCom.Msgng.forms', settings.LOGGING_LEVEL)

msg_id_re = re.compile('[0-9a-f]{32}$')
user_id_re = re.compile('\d+$')

PHONE_NUMBER_HELP_TEXT = _("Please enter only digits. (e.g., 8005555555)")

class MessageEditCheckForm(forms.Form):
	recipients = forms.CharField(required=False) 
	ccs = forms.CharField(required=False) 
	len_attachments = forms.CharField(required=False)
	practice = forms.CharField(required=False)

class MessageOptionsForm(forms.Form):
	user_recipients = forms.CharField(required=False, widget=forms.HiddenInput) 
	thread_uuid = forms.CharField(required=False, widget=forms.HiddenInput) 
	user_cc_recipients = forms.CharField(required=False, widget=forms.HiddenInput) 
	practice_recipients = forms.CharField(required=False, widget=forms.HiddenInput) 
	msg_id = forms.CharField(required=False, widget=forms.HiddenInput)
	msg_prefix = forms.CharField(required=False, widget=forms.HiddenInput)
	def clean_user_recipients(self):
		if('user_recipients' not in self.cleaned_data):
			self.cleaned_data['user_recipients'] = ''
		list_str = self.cleaned_data['user_recipients']
		unclean_recipients = list_str.split(',')
		clean_recipients = []
		for recipient in unclean_recipients:
			if (user_id_re.match(recipient)):
				# Next, check to make sure that the ID is valid
				if (MHLUser.objects.filter(pk=int(recipient)).count()):
					clean_recipients.append(int(recipient))
			# else: Do nothing -- disregard the recipient since it's not a proper ID.
		return clean_recipients
	def clean_user_cc_recipients(self):
		if('user_cc_recipients' not in self.cleaned_data):
			self.cleaned_data['user_cc_recipients'] = ''
		list_str = self.cleaned_data['user_cc_recipients']
		unclean_recipients = list_str.split(',')
		clean_recipients = []
		for recipient in unclean_recipients:
			if (user_id_re.match(recipient)):
				# Next, check to make sure that the ID is valid
				if (MHLUser.objects.filter(pk=int(recipient)).count()):
					clean_recipients.append(int(recipient))
			# else: Do nothing -- disregard the recipient since it's not a proper ID.
		return clean_recipients
	def clean_practice_recipients(self):
		if('practice_recipients' not in self.cleaned_data):
			self.cleaned_data['practice_recipients'] = ''
		list_str = self.cleaned_data['practice_recipients']
		unclean_recipients = list_str.split(',')
		clean_recipients = []
		for recipient in unclean_recipients:
			if (user_id_re.match(recipient)):
				# Next, check to make sure that the ID is valid
				if (PracticeLocation.objects.filter(pk=int(recipient)).count()):
					clean_recipients.append(int(recipient))
			# else: Do nothing -- disregard the recipient since it's not a proper ID.
		
		return clean_recipients
#	def clean(self):
#		if(not self.cleaned_data['user_recipients'] and not self.cleaned_data['practice_recipients']):
#			raise forms.ValidationError(_("No valid recipients found"))
#		return self.cleaned_data


class Message2SingleUserForm(forms.Form):
	#user_recipient = forms.ModelChoiceField(queryset=Provider.objects.exclude(mobile_phone='').order_by('last_name'))    
	recipient = forms.IntegerField(widget=forms.HiddenInput)
	
	subject = forms.CharField(max_length=200, required=False)
	body = forms.CharField(widget=forms.Textarea(attrs={'rows':'20', 'cols':'80'}))
	file = forms.FileField(required=False)
	def clean_recipient(self):
		recipient = self.cleaned_data['recipient']
		u = MHLUser.objects.filter(pk=recipient)
		if (not u.exists()):
			raise forms.ValidationError(_('The intended recipient doesn\'t exist.'))
		return recipient

class MessageForm(forms.Form):
	#user_recipient = forms.ModelChoiceField(queryset=Provider.objects.exclude(mobile_phone='').order_by('last_name'))	
	user_recipient = forms.IntegerField(widget=forms.HiddenInput, required=False)
	user_recipients = forms.CharField(widget=forms.HiddenInput, required=False)
	user_cc_recipients = forms.CharField(widget=forms.HiddenInput, required=False)
	practice_recipient = forms.IntegerField(widget=forms.HiddenInput, required=False)
	subject = forms.CharField(widget=forms.TextInput(attrs={'size':'45'}), max_length=1024, required=False)
	body = forms.CharField(max_length=10240, widget=forms.Textarea(attrs={'rows':'16','cols':'70'}))

	f = forms.FileField(widget=forms.FileInput(attrs={'size':'25'}), required=False)
	def clean(self):
		#data = self.cleaned_data
		recipient = self.cleaned_data.get('user_recipient', 0)
		practice = self.cleaned_data.get('practice_recipient', 0)
		users = self.cleaned_data.get('user_recipients', 0)
		recipients = [int(item) for item in users.split(',') if item]
		recipients.append(recipient)
		u = MHLUser.objects.filter(pk__in=recipients)
		p = PracticeLocation.objects.filter(pk=practice)
		if (not u.exists() and not p.exists()):
			raise forms.ValidationError(_('The intended recipient doesn\'t exist.'))
		if p.exists():
			o = Office_Manager.active_objects.filter(practice=p)
			if not o.exists():
				raise forms.ValidationError(_('There is no manager in this practice.'))

		return self.cleaned_data

				
class CallForm(forms.ModelForm):
	#body = forms.CharField(max_length=140)
	#recipients = forms.ModelMultipleChoiceField(MHLUser)
	#recipient_type = forms.ChoiceField(widget=forms.RadioSelect(),choices=RECIPIENT_TYPE_CHOICES,initial='AC')
	#user_recipients = forms.ModelMultipleChoiceField(MHLUser)
	
	action = forms.CharField(widget=forms.HiddenInput, initial="send")
	
	class Meta:
		model = MessageTemp
		fields = ['user_recipients']


class PageCallbackForm(forms.Form):
	callbackNumber = forms.CharField(max_length=20) # if making changes here, make sure you update the regex in clean()
	
	def clean(self):
		cleaned_data = self.cleaned_data
		callbackNumber = cleaned_data.get("callbackNumber")

		pattern = re.compile('^[0-9#*]{1,20}$')
		if (not pattern.match(callbackNumber)):
			self._errors['callbackNumber'] = ErrorList([_('The callback number must contain ONLY the digits 0-9, the asterisk (*) and/or pound (#) symbols.'), ])
		
		return cleaned_data

class MessageFetchForm_Offset(forms.Form):
	offset = forms.IntegerField()
	count = forms.IntegerField()
	resolved = forms.BooleanField(required=False)
	
	
class MessageFetchForm_Timestamp(forms.Form):
	timestamp = forms.IntegerField()
	resolved = forms.BooleanField(required=False)


class UpdateMessageForm(forms.Form):
	resolved = forms.BooleanField(required=False)
	deleted = forms.BooleanField(required=False)
	read = forms.BooleanField(required=False)

class MessageReferForm(forms.ModelForm):
	class Meta:
		model = MessageRefer
		exclude = ('message', 'status', 'alternative_phone_number')

class ReferEditForm(forms.Form):
	status = forms.ChoiceField(choices=REFER_STATUS)
	refuse_reason = forms.CharField(required=False)

class DicomCallingForm(forms.Form):
	token = forms.CharField()

class ReferClinicalForm(forms.Form):
	user_recipients = forms.CharField(required=False, widget=forms.HiddenInput)
	user_to_recipients = forms.CharField(required=False, widget=forms.HiddenInput) 
	user_cc_recipients = forms.CharField(required=False, widget=forms.HiddenInput) 

	selected_practice = forms.CharField(required=False, widget=forms.HiddenInput)
	icd_code = forms.CharField(max_length=255,required=False)
	ops_code = forms.CharField(max_length=255,required=False)
	medication_list = forms.CharField(max_length=255,required=False)
	reason_of_refer = forms.CharField(widget=forms.Textarea(\
			attrs={'rows':'10', 'cols':'111'}), required=True)
	attachments = forms.FileField(widget=forms.FileInput(\
			attrs={'size':'25'}), required=False)

class ReferDemographicsForm(forms.Form):
	first_name = forms.CharField(max_length=30,required=True, label=_("First Name"))
	last_name = forms.CharField(max_length=30,required=True, label=_("Last Name"))
	previous_name = forms.CharField(max_length=30,required=False, label=_("Previous Name"))
	gender = forms.ChoiceField(choices=[('','------')] + list(GENDER_CHOICES), required=False)
	date_of_birth = forms.DateField(required=True,\
			 widget=forms.DateInput(format=DATE_FORMAT))
	mrn = forms.CharField(max_length=30,required=True)
	ssn = forms.CharField(max_length=30,required=False)
	address = forms.CharField(max_length=30,required=False)
	phone_number = forms.CharField(max_length=20,required=False, \
			widget=forms.TextInput(attrs={'size':'25'}), \
			help_text=PHONE_NUMBER_HELP_TEXT)
	home_phone_number = forms.CharField(max_length=20,required=False, \
			widget=forms.TextInput(attrs={'size':'25'}),
			help_text=PHONE_NUMBER_HELP_TEXT)
	email = forms.CharField(max_length=64,required=False)
	notes = forms.CharField(widget=forms.Textarea(\
			attrs={'rows':'10', 'cols':'111'}), required=False)

	def clean_phone_number(self):
		cleaned_data = self.cleaned_data
		if "phone_number" in cleaned_data and cleaned_data['phone_number']:
			cleaned_data['phone_number'] = cleaned_data['phone_number'].replace('-','').replace("(", "").replace(") ","")
			return cleaned_data['phone_number']
		else:
			return ''

	def clean_home_phone_number(self):
		cleaned_data = self.cleaned_data
		if "home_phone_number" in cleaned_data and cleaned_data['home_phone_number']:
			cleaned_data['home_phone_number'] = cleaned_data['home_phone_number'].replace('-','').replace("(", "").replace(") ","")
			return cleaned_data['home_phone_number']
		else:
			return ''

	def clean_date_of_birth(self):
		date_of_birth = self.cleaned_data['date_of_birth']
		if date_of_birth > datetime.date.today():
			raise ValidationError(_('The date of birth must be before today.'))
		return date_of_birth

class ReferInsuranceForm(forms.Form):
	prior_authorization_number= forms.CharField(max_length=30,widget=forms.TextInput(attrs={'size':'25'}), required=False)
	other_authorization = forms.CharField(max_length=200,widget=forms.TextInput(attrs={'size':'25'}), required=False)
	internal_tracking_number = forms.CharField(max_length=30,widget=forms.TextInput(attrs={'size':'25'}), required=False)
	insurance_id = forms.CharField(max_length=30,widget=forms.TextInput(attrs={'size':'25'}), required=False)
	secondary_insurance_id = forms.CharField(max_length=30,widget=forms.TextInput(attrs={'size':'25'}), required=False)
	tertiary_insurance_id = forms.CharField(max_length=30,widget=forms.TextInput(attrs={'size':'25'}), required=False)
