
from django import forms
from django.conf import settings
from django.forms.util import ErrorList
from django.forms import ModelForm

from MHLogin.DoctorCom.models import MessageTemp
from MHLogin.MHLUsers.models import Provider
from MHLogin.utils.mh_logging import get_standard_logger 

from django.utils.translation import ugettext as _

# Setting up logging
logger = get_standard_logger('%s/DoctorCom/forms.log' % (settings.LOGGING_ROOT), 
					'DCom.forms', settings.LOGGING_LEVEL)


class MessageForm(ModelForm):
	#body = forms.CharField(max_length=140)
	#recipients = forms.ModelMultipleChoiceField(MHLUser)
	#recipient_type = forms.ChoiceField(widget=
		#forms.RadioSelect(),choices=RECIPIENT_TYPE_CHOICES,initial='AC')
	#user_recipients = forms.ModelMultipleChoiceField(queryset=
		#Provider.objects.exclude(mobile_phone='').order_by('last_name'))	
	user_recipients = forms.MultipleChoiceField(choices=())
	action = forms.CharField(widget=forms.HiddenInput, initial="send")
	body = forms.CharField(widget=forms.Textarea)

	def __init__(self, site, *args, **kwargs):
		session_key = None
		if (not 'session_key' in kwargs):
			logger.warn('Into Message2SingleUserForm without a session key!')
		else:
			session_key = kwargs['session_key']
			del kwargs['session_key']
		site = None
		if ('site' in kwargs):
			site = kwargs['site']
			del kwargs['site']
		logger.debug('%s: Into MessageForm with site %s' % (session_key, site,))
		super(Message2SingleUserForm, self).__init__(*args, **kwargs)

		self.fields['user_recipients'].choices = [['0', '---(Site Providers)---'], ]

		if (site):
			providers = Provider.objects.exclude(user__mobile_phone='').filter(sites=site).\
				order_by('last_name').values_list('pk', 'first_name', 'last_name')
		else:
			import traceback
			logger.warn('%s: Into MessageForm without site. Traceback: %s' % 
				(session_key, traceback.extract_stack()))
			providers = Provider.objects.exclude(user__mobile_phone='').order_by('last_name').\
				values_list('pk', 'first_name', 'last_name')
		for user in providers:
			self.fields['user_recipients'].choices.append([user[0], '%s %s' % (user[1], user[2])])

		# TODO_FIND_COMMPROV
		# We need a better way to find community providers
		self.fields['user_recipients'].choices.append(['0', _('---(Community Providers)---')])
		community_providers = Provider.objects.exclude(user__mobile_phone='').\
			filter(sites=None).order_by('last_name').values_list('pk', 'first_name', 'last_name')
		for user in community_providers:
			self.fields['user_recipients'].choices.append([user[0], '%s %s' % (user[1], user[2])])

	class Meta:
		model = MessageTemp
		fields = ['user_recipients', 'body']


class Message2SingleUserForm(ModelForm):
	#user_recipient = forms.ModelChoiceField(queryset=\
		#Provider.objects.exclude(mobile_phone='').order_by('last_name'))	
	user_recipient = forms.ChoiceField(choices=())
	action = forms.CharField(widget=forms.HiddenInput, initial="send")
	body = forms.CharField(widget=forms.Textarea)

	def __init__(self, *args, **kwargs):
		session_key = None
		if (not 'session_key' in kwargs):
			logger.warn('Into Message2SingleUserForm without a session key!')
		else:
			session_key = kwargs['session_key']
			del kwargs['session_key']
		site = None
		if ('site' in kwargs):
			site = kwargs['site']
			del kwargs['site']
		logger.debug('%s: Into Message2SingleUserForm with site %s' % (session_key, site,))
		super(Message2SingleUserForm, self).__init__(*args, **kwargs)

		self.fields['user_recipient'].choices = [['0', '---(Site Providers)---'], ]

		if (site):
			providers = Provider.objects.exclude(user__mobile_phone='').filter(sites=site).\
				order_by('last_name').values_list('pk', 'first_name', 'last_name')
		else:
			import traceback
			logger.warn('%s: Into Message2SingleUserForm without site. Traceback: %s' % 
				(session_key, traceback.extract_stack()))
			providers = Provider.objects.exclude(user__mobile_phone='').order_by('last_name').\
				values_list('pk', 'first_name', 'last_name')
		for user in providers:
			self.fields['user_recipient'].choices.append([user[0], '%s %s' % (user[1], user[2])])

		# TODO_FIND_COMMPROV
		# We need a better way to find community providers
		self.fields['user_recipient'].choices.append(['0', _('---(Community Providers)---')])
		community_providers = Provider.objects.exclude(user__mobile_phone='').filter(sites=None).\
			order_by('last_name').values_list('pk', 'first_name', 'last_name')
		for user in community_providers:
			self.fields['user_recipient'].choices.append([user[0], '%s %s' % (user[1], user[2])])

	class Meta:
		model = MessageTemp
		fields = ['body']


class CallForm(ModelForm):
	#body = forms.CharField(max_length=140)
	#recipients = forms.ModelMultipleChoiceField(MHLUser)
	#recipient_type = forms.ChoiceField(widget=forms.RadioSelect(), 
		#choices=RECIPIENT_TYPE_CHOICES,initial='AC')
	#user_recipients = forms.ModelMultipleChoiceField(MHLUser)

	action = forms.CharField(widget=forms.HiddenInput, initial="send")

	class Meta:
		model = MessageTemp
		fields = ['user_recipients']


class PageCallbackForm(forms.Form):
	# if making changes here, make sure you update the regex in clean()
	callbackNumber = forms.CharField(max_length=20)

	def clean(self):
		cleaned_data = self.cleaned_data
		callbackNumber = cleaned_data.get("callbackNumber")

		import re
		pattern = re.compile('^[0-9#*]{1,20}$')
		if (not pattern.match(callbackNumber)):
			self._errors['callbackNumber'] = ErrorList([_('The callback number must '
				'contain ONLY the digits 0-9, the asterisk (*) and/or pound (#) symbols.'), ])

		return cleaned_data


#class MessageForm (forms.Form):
#    body = forms.CharField(max_length=140)
#    recipient_type = forms.ChoiceField(widget=forms.RadioSelect(), 
#		choices=RECIPIENT_TYPE_CHOICES,initial='AC')
#
#
#class GroupMessageForm(forms.Form):
#    body = forms.CharField(max_length=140)
#    my_physician_groups= forms.ModelMultipleChoiceField(queryset=PhysicianGroupMembers.objects.all())
#
#    def __init__(self,request, *args, **kwargs):
#        super(GroupMessageForm, self).__init__(*args, **kwargs) 
#        myPhysicianObj = Physician.objects.get(user=request.user)
#        self.fields['my_physician_groups'].queryset = \
#			PhysicianGroupMembers.objects.filter(physician=myPhysicianObj) 
#        self.fields['my_physician_groups'].label_from_instance = lambda obj: "%s" % (obj.physician_group) 
# 
#
#class PatientAdminForm(ModelForm):
#    class Meta:
#        model = PatientAdmin
#        exclude = ('user','patient')
#
#
#class MobileVerificationForm(forms.Form):
#    last_name = forms.CharField(max_length=20)
#    verification_code = forms.CharField(max_length=5) 
#
#
#class NewUserFormPatientAdmin(forms.Form):
#    username = forms.CharField(max_length=30)
#    password = forms.CharField(max_length=20,widget=forms.PasswordInput())
#    first = forms.CharField(max_length=20)
#    last = forms.CharField(max_length=20)
#    email = forms.EmailField(max_length=30)
#    relation_to_patient = forms.CharField(max_length=2,widget=forms.Select(choices=RELATION_CHOICES))
#    gender = forms.CharField(max_length=1,widget=forms.Select(choices=GENDER_CHOICES))
#    home_phone = forms.CharField(max_length=30)
#    mobile_phone = forms.CharField(max_length=30)
#
#
#class MessageRecipientFormAdd(ModelForm):
#    class Meta:
#        model = MessageRecipient
#        fields = ('first_name','last_name','email','mobile_phone','relation_to_patient')
#
#class MessageRecipientFormEdit(ModelForm):
#    class Meta:
#        model = MessageRecipient
#        fields = ('first_name','last_name','email','mobile_phone','relation_to_patient','disable')
#
#
#class MessageRecipientPhysicianFormAdd(ModelForm):
#    class Meta:
#        model = MessageRecipientPhysician
#        fields = ('physician')
#
