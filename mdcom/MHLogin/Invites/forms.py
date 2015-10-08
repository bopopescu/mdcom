
import re

from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.forms.util import ErrorList
from django.utils.translation import ugettext_lazy as _

from MHLogin.utils.mh_logging import get_standard_logger 

from MHLogin.Invites.models import Invitation
from MHLogin.utils.constants import PROVIDER_INVITE_CHOICES, SALES_INVITE_CHOICES, OFFICE_STAFF_INVITE_CHOICES

# Setting up logging
logger = get_standard_logger('%s/Invites/forms.log' % (settings.LOGGING_ROOT),
							'Invites.forms', settings.LOGGING_LEVEL)


class ManagerInviteForm(forms.ModelForm):
	userType = forms.ChoiceField(label=_('User Type'), choices=PROVIDER_INVITE_CHOICES)
	msg = forms.CharField(required=False, label=_('Note to your Colleague'), widget=forms.Textarea(attrs={'rows':4, 'cols':40}))
	sender = forms.HiddenInput()
	
	class Meta:
		model = Invitation
		fields = ['recipient']
	
#	def clean(self):
#		address = self.cleaned_data['recipient']
#		type = self.cleaned_data['userType']
#		if (Invitation.objects.filter(recipient=address, userType=type).count()):
#			raise forms.ValidationError(_("This email address already has an outstanding invitation."))
#		if (User.objects.filter(email=address).count()):
#			raise forms.ValidationError(_("This email address is already associated with a DoctorCom account."))
#		return self.cleaned_data

	def clean_userType(self):
		userType = self.cleaned_data['userType']
		if (not userType):
			return 0
		return userType
	
#add by xlin 20120711
class OfficeStaffInviteForm(forms.ModelForm):
	userType = forms.ChoiceField(label=_('User Type'), choices=OFFICE_STAFF_INVITE_CHOICES)
	msg = forms.CharField(required=False, label=_('Note to your Colleague'), widget=forms.Textarea(attrs={'rows':4, 'cols':40}))
	sender = forms.HiddenInput()
	
	class Meta:
		model = Invitation
		fields = ['recipient']
	def clean_userType(self):
		userType = self.cleaned_data['userType']
		if (not userType):
			return 0
		return userType	

class inviteSendForm(forms.ModelForm):
	userType = forms.ChoiceField(label=_('User Type'), choices=PROVIDER_INVITE_CHOICES)
	msg = forms.CharField(required=False, label=_('Note to your Colleague'), widget=forms.Textarea(attrs={'rows':4, 'cols':40}))
	class Meta:
		model = Invitation
		fields = ['recipient', ]

#	def clean(self):
#		address = self.cleaned_data['recipient']
#		if 'userType' in self.cleaned_data:
#			type = self.cleaned_data['userType']
#		else:
#			type = 1
#		if (Invitation.objects.filter(recipient=address, userType=type).count()):
#			raise forms.ValidationError(_("This email address already has an outstanding invitation."))
#		if (User.objects.filter(email=address).count()):
#			raise forms.ValidationError(_("This email address is already associated with a DoctorCom account."))
#		return self.cleaned_data

	def clean_userType(self):
		userType = self.cleaned_data['userType']
		if (not userType):
			return 0
		return userType


class multiUserSendForm(forms.Form):
	userType = forms.ChoiceField(choices=SALES_INVITE_CHOICES, label=_("User type"))
	emailAddresses = forms.CharField(required=True, widget=forms.Textarea(attrs={'cols':75, 'rows':3}), 
									label=_('Email Addresses (whitespace separated)'))
	#typeVerification = forms.BooleanField(required=False, label='Do you verify the recipient is of that type?')
	if (settings.DEBUG):
		test = forms.BooleanField(required=False, label=_('Set this if you are testing and don\'t want the recipient to get an email notification.'))
	msg = forms.CharField(required=False, label=_('Note (optional)'), widget=forms.Textarea(attrs={'rows':10, 'cols':75}))
	user = forms.HiddenInput()
	
	def clean(self):
		cleaned_data = self.cleaned_data
		type = cleaned_data['userType']
		email_re = re.compile(
				r"(^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*"  # dot-atom
				r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|\\[\001-011\013\014\016-\177])*"' # quoted-string
				r')@(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?$', re.IGNORECASE)  # domain
		addresses_str = ''
		if ('emailAddresses' in cleaned_data):
			addresses_str = cleaned_data['emailAddresses']
			del cleaned_data['emailAddresses']
		addresses = addresses_str.split()

		invalid_addresses = []
		existing_addresses = []
		existing_invite_addresses = []
		for addr in addresses:
			if (not email_re.match(addr)):
				logger.debug('Found invalid address %s' % (addr,))
				invalid_addresses.append(addr)
				logger.debug('invalid_addresses is %s' % (existing_addresses,))
			elif (User.objects.filter(email=addr).count()):
				logger.debug('Found existing User for %s' % (addr,))
				existing_addresses.append(addr)
				logger.debug('existing_addresses is %s' % (existing_addresses,))
#			elif (Invitation.objects.filter(recipient=addr, userType=type).count()):
#				logger.debug('Found existing invitation for %s' % (addr,))
#				existing_invite_addresses.append(addr)
#				logger.debug('existing_invite_addresses is %s' % (existing_invite_addresses,))
		err_strs = []
		if (len(invalid_addresses)):
			err_strs.append(_('At least one invalid email address was found: %s.') % (', '.join(invalid_addresses),))
		if (len(existing_addresses)):
			err_strs.append(_('At least one email address is already registered: %s.') % (', '.join(existing_addresses),))
		if (len(existing_invite_addresses)):
			err_strs.append(_('At least one email address already has an outstanding invite: %s.') % (', '.join(existing_invite_addresses),))

		if (err_strs):
			# save the first error as a return value for ValidationError
			self._errors['emailAddresses'] = ErrorList()
			for err_str in err_strs:
				self._errors['emailAddresses'].append(err_str,)
		
		cleaned_data['emailAddresses'] = addresses
		return cleaned_data

#	def clean_userType(self):
#		userType = self.cleaned_data['userType']
#		if (not userType):
#			return 0
#		return userType


class inviteCodeEntryForm(forms.Form):
	emailAddress = forms.EmailField(label=_('Your email address'))
	code = forms.CharField(max_length=8, label=_('Invitation code'))

class inviteResendForm(forms.Form):
	msg = forms.CharField(required=False, label=_('Note to Recipient'), widget=forms.Textarea(attrs={'rows':4, 'cols':40}))




