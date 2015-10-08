
from MHLogin.MHLPractices.models import PracticeLocation
from MHLogin.MHLUsers.models import MHLUser, Office_Manager
from MHLogin.utils.fields import MHLCheckboxInput
from django import forms
from django.utils.translation import ugettext_lazy as _

import re


class MsgListForm(forms.Form):
	from_timestamp = forms.IntegerField(required=False)
	to_timestamp = forms.IntegerField(required=False)
	count = forms.IntegerField(required=False)
	resolved = forms.BooleanField(required=False, widget=MHLCheckboxInput)
	read = forms.BooleanField(required=False, widget=MHLCheckboxInput)
	exclude_id = forms.CharField(required=False)
	is_threading = forms.BooleanField(required=False, widget=MHLCheckboxInput)
	use_time_setting = forms.BooleanField(required=False, widget=MHLCheckboxInput)
	thread_uuid = forms.CharField(required=False)

base64_regex = re.compile(r'^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$')


class MsgGetForm(forms.Form):
	secret = forms.CharField()

	def clean_secret(self):
		cleaned = self.cleaned_data['secret']
		if (not base64_regex.match(cleaned)):
			raise forms.ValidationError(_('Secret doesn\'t appear to be a valid secret.'))
		return cleaned

recipients_re = re.compile(r'(\d+,)*\d+$')
single_uuid_re = re.compile(r'[A-Za-z0-9]{32}$')
attachment_ids_re = re.compile(r'([A-Za-z0-9]{32},)*[A-Za-z0-9]{32}$')


class MsgCompositionForm(forms.Form):
	# The validation function for recipients splits it into a list for you.
	recipients = forms.CharField(required=False)
	practice_recipients = forms.CharField(required=False)
	ccs = forms.CharField(required=False)
	attachment = forms.FileField(required=False)
	subject = forms.CharField(required=False)
	body = forms.CharField()
	message_id = forms.CharField(required=False)
	refer_id = forms.CharField(required=False)
	attachment_ids = forms.CharField(required=False)
	secret = forms.CharField(required=False)
	thread_uuid = forms.CharField(required=False)

	def clean_recipients(self):
		cleaned = self.cleaned_data['recipients']
		recipients = []
		if cleaned:
			if (not recipients_re.match(cleaned)):
				raise forms.ValidationError(_('Recipients list isn\'t of the correct form.'))
			recipients = cleaned.split(',')
			if ('0' in recipients):
				raise forms.ValidationError(_('0 is an invalid recipient ID.'))
			u = MHLUser.objects.filter(pk__in=recipients)
			if (not u.exists()):
				self.cleaned_data['recipients'] = cleaned
				raise forms.ValidationError(_('The intended recipient doesn\'t exist.'))
		return recipients

	def clean_practice_recipients(self):
		cleaned = self.cleaned_data['practice_recipients']
		practice_recipients = []
		if cleaned:
			if (not recipients_re.match(cleaned)):
				raise forms.ValidationError(_('Practice recipients list isn\'t of the correct form.'))
			_practice_recipients = cleaned.split(',')
			if ('0' in _practice_recipients):
				raise forms.ValidationError(_('0 is an invalid recipient ID.'))

			p = PracticeLocation.objects.filter(id__in=_practice_recipients)
			if not p.exists():
				raise forms.ValidationError(_('The intended practice recipient doesn\'t exist.'))
			managers = Office_Manager.active_objects.filter(practice__id__in=_practice_recipients)
			if not managers or len(managers) <= 0:
				raise forms.ValidationError(_('There is no manager in this practice.'))
			practice_recipients.extend(m.user.user.pk for m in managers)
		return practice_recipients

	def clean_ccs(self):
		cleaned = self.cleaned_data['ccs']
		ccs = []
		if cleaned:
			if (not recipients_re.match(cleaned)):
				raise forms.ValidationError(_('CCS list isn\'t of the correct form.'))
			ccs = cleaned.split(',')
			if ('0' in ccs):
				raise forms.ValidationError(_('0 is an invalid cc ID.'))
			u = MHLUser.objects.filter(pk__in=ccs)
			if (not u.exists()):
				self.cleaned_data['ccs'] = cleaned
				raise forms.ValidationError(_('The intended cc doesn\'t exist.'))
		return ccs

	def clean_message_id(self):
		cleaned = self.cleaned_data['message_id']
		if cleaned:
			if (not single_uuid_re.match(cleaned)):
				raise forms.ValidationError(_('message id isn\'t of the correct form.'))
		return cleaned

	def clean_refer_id(self):
		cleaned = self.cleaned_data['refer_id']
		if cleaned:
			if (not single_uuid_re.match(cleaned)):
				raise forms.ValidationError(_('refer id isn\'t of the correct form.'))
		return cleaned

	def clean_attachment_ids(self):
		cleaned = self.cleaned_data['attachment_ids']
		attachment_ids = []
		if cleaned:
			if (not attachment_ids_re.match(cleaned)):
				raise forms.ValidationError(_('attachment id list isn\'t of the correct form.'))
			attachment_ids = cleaned.split(',')
		return attachment_ids

	def clean_thread_uuid(self):
		cleaned = self.cleaned_data['thread_uuid']
		if cleaned:
			if (not single_uuid_re.match(cleaned)):
				raise forms.ValidationError(_('thread_uuid isn\'t of the correct form.'))
		return cleaned

	def clean_secret(self):
		attachment_ids = self.cleaned_data['attachment_ids']
		secret = self.cleaned_data['secret']
		if attachment_ids:
			if not secret:
				raise forms.ValidationError(_("This field is required."))
			if (not base64_regex.match(secret)):
				raise forms.ValidationError(_('Secret doesn\'t appear to be a valid secret.'))
		return secret

	def clean(self):
		if('recipients' in self.cleaned_data and not self.cleaned_data['recipients'] 
			and 'practice_recipients' in self.cleaned_data and not self.cleaned_data['practice_recipients']):
			raise forms.ValidationError(_("No valid recipients found"))
		return self.cleaned_data

message_ids_re = re.compile(r'([A-Za-z0-9]{32},)*[A-Za-z0-9]{32}$')


class MsgBatchIDForm(forms.Form):
	message_ids = forms.CharField()

	def clean_message_ids(self):
		cleaned = self.cleaned_data['message_ids']
		message_ids = []
		if cleaned:
			if (not message_ids_re.match(cleaned)):
				raise forms.ValidationError(_('Message id list isn\'t of the correct form.'))
			message_ids = cleaned.split(',')
		return message_ids


class MsgCompositionCheckForm(forms.Form):
	# The validation function for recipients splits it into a list for you.
	recipients = forms.CharField(required=False)
	practice_recipients = forms.CharField(required=False)
	ccs = forms.CharField(required=False)
	attachment_count = forms.IntegerField()

	def clean_recipients(self):
		cleaned = self.cleaned_data['recipients']
		recipients = []
		if cleaned:
			if (not recipients_re.match(cleaned)):
				raise forms.ValidationError(_('Recipients list isn\'t of the correct form.'))
			recipients = cleaned.split(',')
			if ('0' in recipients):
				raise forms.ValidationError(_('0 is an invalid recipient ID.'))
			u = MHLUser.objects.filter(pk__in=recipients)
			if (not u.exists()):
				self.cleaned_data['recipients'] = cleaned
				raise forms.ValidationError(_('The intended recipient doesn\'t exist.'))
		return recipients

	def clean_practice_recipients(self):
		cleaned = self.cleaned_data['practice_recipients']
		practice_recipients = []
		if cleaned:
			if (not recipients_re.match(cleaned)):
				raise forms.ValidationError(_('Practice recipients list isn\'t of the correct form.'))
			_practice_recipients = cleaned.split(',')
			if ('0' in _practice_recipients):
				raise forms.ValidationError(_('0 is an invalid recipient ID.'))

			p = PracticeLocation.objects.filter(id__in=_practice_recipients)
			if not p.exists():
				raise forms.ValidationError(_('The intended practice recipient doesn\'t exist.'))
			managers = Office_Manager.active_objects.filter(practice__id__in=_practice_recipients)
			if not managers or len(managers) <= 0:
				raise forms.ValidationError(_('There is no manager in this practice.'))
			practice_recipients.extend(m.user.user.pk for m in managers)
		return practice_recipients

	def clean_ccs(self):
		cleaned = self.cleaned_data['ccs']
		ccs = []
		if cleaned:
			if (not recipients_re.match(cleaned)):
				raise forms.ValidationError(_('CCS list isn\'t of the correct form.'))
			ccs = cleaned.split(',')
			if ('0' in ccs):
				raise forms.ValidationError(_('0 is an invalid cc ID.'))
			u = MHLUser.objects.filter(pk__in=ccs)
			if (not u.exists()):
				self.cleaned_data['ccs'] = cleaned
				raise forms.ValidationError(_('The intended cc doesn\'t exist.'))
		return ccs

	def clean(self):
		if('recipients' in self.cleaned_data and not self.cleaned_data['recipients'] 
			and 'practice_recipients' in self.cleaned_data and not self.cleaned_data['practice_recipients']):
			raise forms.ValidationError(_("No valid recipients found"))
		return self.cleaned_data

class GetMsgDetailsForm(forms.Form):
	message_uuids = forms.CharField()
	secret = forms.CharField()

	def clean_message_uuids(self):
		cleaned = self.cleaned_data['message_uuids']
		message_ids = []
		if cleaned:
			if (not message_ids_re.match(cleaned)):
				raise forms.ValidationError(_('Message id list isn\'t of the correct form.'))
			message_ids = cleaned.split(',')
		return message_ids

	def clean_secret(self):
		cleaned = self.cleaned_data['secret']
		if (not base64_regex.match(cleaned)):
			raise forms.ValidationError(_('Secret doesn\'t appear to be a valid secret.'))
		return cleaned