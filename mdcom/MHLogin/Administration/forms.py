
from django import forms
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _

from MHLogin.DoctorCom.Messaging.models import MESSAGE_TYPES
from MHLogin.Invites.models import Invitation
from MHLogin.MHLUsers.models import MHLUser, Broker
from MHLogin.MHLOrganization.utils import get_all_org_have_this_type_user

from MHLogin.utils.constants import DATE_FORMAT, \
	RESERVED_ORGANIZATION_TYPE_ID_PRACTICE, USER_TYPE_CHOICES


class EmailForm(forms.Form):
	email = forms.CharField()


class NameForm(forms.Form):
	name = forms.CharField()


class PasswordChangeForm(forms.Form):
	password1 = forms.CharField(widget=forms.PasswordInput(render_value=False))
	password2 = forms.CharField(widget=forms.PasswordInput(render_value=False))

	def clean_password2(self):
		password1 = self.cleaned_data['password1']
		password2 = self.cleaned_data['password2']
		if (password1 != password2):
			pass  # raise an exception
		return password1

	def set_password_invalid(self):
		pass


class PasswordForm(forms.Form):
	password = forms.CharField(widget=forms.PasswordInput(render_value=False))


class AdminMessageForm(forms.Form):
	recipient = forms.IntegerField(widget=forms.HiddenInput)
	subject = forms.CharField(max_length=200, required=False, label=_("Subject"))
	body = forms.CharField(widget=forms.Textarea, label=_("Message Text"))
	file = forms.FileField(required=False, label=_("File"))
	url = forms.CharField(required=False, label=_("Url"), 
		help_text=_("Only works with twilio recording urls"))
	callback_number = forms.CharField(max_length=10, required=False, label=_("Callback number"))
	message_type = forms.ChoiceField(choices=MESSAGE_TYPES, label=_("Message type"))

	def clean_recipient(self):
		recipient = self.cleaned_data['recipient']
		u = MHLUser.objects.filter(pk=recipient)
		if (not u.exists()):
			return forms.ValidationError(_('The intended recipient doesn\'t exist.'))
		return recipient

	def clean_callback_number(self):
		callback = self.cleaned_data['callback_number']
		if(self.cleaned_data['url']):
			if(not self.cleaned_data['callback_number']):
				raise forms.ValidationError(_('callback number is required when url is set'))
		return callback


class AdminInviteForm(forms.ModelForm):
#	message
	class Meta:
		model = Invitation
		fields = ['recipient', 'userType', 'typeVerified', 'createGroupPractice', 'createPractice', 
				'assignPractice', 'testFlag']

	def __init__(self, data=None, initial=None, *args, **kwargs):
		self.base_fields['assignPractice'].choices = [('', '------')]
		user_type_flag = None
		if data and "userType" in data:
			user_type_flag = data["userType"]
		practices = get_all_org_have_this_type_user(org_type_id=RESERVED_ORGANIZATION_TYPE_ID_PRACTICE,
				user_type_flag=user_type_flag)
		self.base_fields['assignPractice'].choices += [(t.id, t.practice_name)\
				for t in practices]
		super(AdminInviteForm, self).__init__(data=data,\
			initial=initial, *args, **kwargs)

	def clean_emailAddress(self):
		address = self.cleaned_data['emailAddress']
		if (Invitation.objects.filter(recipient=address).count()):
			raise forms.ValidationError(_("This email address already has an "
				"outstanding invitation."))
		if (User.objects.filter(email=address).count()):
			raise forms.ValidationError(_("This email address is already associated "
				"with a DoctorCom account."))
		return address

	def clean_userType(self):
		userType = self.cleaned_data['userType']
		if (not userType):
			return 0
		return userType
#comment these code by xlin in 20120618 because validate is in front-end
#	def clean_assignPractice(self):
#		data = self.cleaned_data
#		try:
#			if(data['userType'] == 101 and ('assignPractice' not in data or 
# 				not data['assignPractice'])):
#				raise forms.ValidationError(_("non-providers must be associated with a practice"))
#		except:
#			raise forms.ValidationError(_("This field is required."))


class GetAssignPracticeForm(forms.Form):
	userType = forms.ChoiceField(choices=USER_TYPE_CHOICES, required=False)
	assignPractice = forms.ChoiceField(choices=[('', '------')], required=False)

	def __init__(self, data=None, initial=None, *args, **kwargs):
		self.base_fields['assignPractice'].choices = [('', '------')]
		user_type_flag = None
		if data and "userType" in data:
			user_type_flag = data["userType"]
		practices = get_all_org_have_this_type_user(org_type_id=RESERVED_ORGANIZATION_TYPE_ID_PRACTICE,
				user_type_flag=user_type_flag)
		self.base_fields['assignPractice'].choices += [(t.id, t.practice_name)\
				for t in practices]
		super(GetAssignPracticeForm, self).__init__(data=data,\
			initial=initial, *args, **kwargs)


class MessageToAllForm(forms.Form):
	EMAIL_FILTER_CHOICES = (('everyone', _('Everyone')),
							('providers', _('Providers')),
							('managers', _('Managers')))

	subject = forms.CharField(required=True, label=_("Subject"))
	body = forms.CharField(widget=forms.Textarea, label=_("Message Text"))
	emailfilter = forms.ChoiceField(choices=EMAIL_FILTER_CHOICES, label=_("Filter"))


class BrokerQueryForm(forms.Form):
	broker_from = forms.ChoiceField()
	directions = forms.ChoiceField(choices=((1, _('All')), (2, _('In')), (3, _('Out')), ), 
				widget=forms.RadioSelect())
	broker_to = forms.CharField(required=False)
	period_from = forms.DateField(required=False, widget=forms.DateInput(format=DATE_FORMAT))
	period_to = forms.DateField(required=False, widget=forms.DateInput(format=DATE_FORMAT))

	def clean(self):
		cleaned_data = self.cleaned_data
		return cleaned_data

	def __init__(self, *args, **kwrds):
		super(BrokerQueryForm, self).__init__(*args, **kwrds)
		brokers = Broker.objects.all()
		choice_broker = [('-1', _('All'))] + [(broker.user.id, ' '.join(
			[broker.user.first_name, broker.user.last_name])) for broker in brokers]
		self.fields['broker_from'].choices = choice_broker


class ReferTrackingForm(forms.Form):
	PERIOD_CHOICES = (
						(1, _('all time')), 
						(2, _('today')), 
						(3, _('yesterday')),
						(4, _('this week')),
						(5, _('last week')),
						(6, _('last 7 days')),
						(7, _('this month')),
						(8, _('last month')),
						(9, _('last 30 days')),
						(10, _('this year')),
					)
	period_type = forms.ChoiceField(choices=PERIOD_CHOICES, widget=forms.Select(), required=False)
	period_from = forms.DateField(required=False, widget=forms.DateInput(format=DATE_FORMAT))
	period_to = forms.DateField(required=False, widget=forms.DateInput(format=DATE_FORMAT))
	period_radio = forms.CharField(widget=forms.HiddenInput)

	def clean(self):
		data = self.cleaned_data
		return data
