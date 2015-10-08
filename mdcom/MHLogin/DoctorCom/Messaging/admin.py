
from datetime import datetime

from django import forms
from django.conf import settings

from MHLogin.Administration.tech_admin import sites, options

from models import Message, MessageBody, MessageBodyUserStatus, MessageAttachment


class MessageAdmin(options.TechAdmin):
	list_display = ('sender', '_get_recipients', 'send_timestamp', '_get_send_date', 
		'sender_site', 'subject', 'message_type', 'callback_number', 'related_message')
	list_filter = ('message_type', 'urgent')
	search_fields = ('sender__username', 'sender__first_name', 'sender__last_name',)
	readonly_fields = ['related_message']

	def _get_send_date(self, obj):
		return datetime.fromtimestamp(obj.send_timestamp).strftime("%m-%d-%y %H:%M:%S")
	_get_send_date.short_description = 'Send Date'

	def _get_recipients(self, obj):
		return ', '.join([str(r) for r in obj.recipients.all()])
	_get_recipients.short_description = 'Recipients'


class MessageBodyAdmin(options.TechAdmin):
	list_display = ('_get_message',) 
	readonly_fields = ['message']

	def _get_message(self, obj):
		return obj.message
	_get_message.short_description = 'Message'


class MessageBodyUserStatusAdmin(options.TechAdmin):
	list_display = ('user', 'read_flag', 'read_timestamp', 'delete_flag',
				'delete_timestamp', 'resolution_flag', 'resolution_timestamp') 
	ordering = ('msg_body', 'user')
	readonly_fields = ['msg_body']


class MessageAttachmentAdmin(options.TechAdmin):

	class MessageAttachmentForm(forms.ModelForm):
		_storage_name = forms.CharField(widget=forms.TextInput(attrs={'size': 40}))

		def __init__(self, *args, **kwargs):
			super(MessageAttachmentAdmin.MessageAttachmentForm, self).__init__(*args, **kwargs)
			if 'instance' in kwargs:
				attach = kwargs['instance']
				# Show disabled read-only uuid field
				self.fields['_storage_name'].initial = attach.uuid
			self.fields['_storage_name'].widget.attrs['disabled'] = 'disabled'

	list_display = ('message', 'encrypted', 'content_type', 'encoding', 'charset', 
				'suffix', 'size', 'metadata')
	readonly_fields = ['message']
	form = MessageAttachmentForm


sites.register(Message, MessageAdmin)
sites.register(MessageBody, MessageBodyAdmin)
sites.register(MessageBodyUserStatus, MessageBodyUserStatusAdmin)
sites.register(MessageAttachment, MessageAttachmentAdmin)


if (settings.DEBUG_MODELS):
	from MHLogin.utils.admin_utils import registerallmodels
	registerallmodels('Messaging')

