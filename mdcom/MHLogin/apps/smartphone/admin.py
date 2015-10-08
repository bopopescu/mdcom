
from django.forms import Textarea

from MHLogin.Administration.tech_admin import sites, options, forms

from models import SmartPhoneAssn


class SmartPhoneAssnAdmin(options.TechAdmin):
	class SmartPhonAssnForm(forms.TechAdminForm):
		ta = Textarea(attrs={'rows': 4, 'cols': 70, 'style': "font-family:courier;"})

		def __init__(self, *args, **kwargs):
			super(SmartPhoneAssnAdmin.SmartPhonAssnForm, self).__init__(*args, **kwargs)
			for f in self.fields:  # dev assn fields readonly and some fixed width
				if f in ['secret', 'secret_hash', 'db_secret', 'db_hash', 'push_token']:
					self.fields[f].widget = self.ta
				self.fields[f].widget.attrs['disabled'] = 'disabled'

	list_display = ('user', 'version', 'platform', '_get_push_tok', 'is_active')
	list_filter = ('version', 'platform', 'is_active',)
	search_fields = ('user__first_name', 'user__last_name', 'user__username',
					'version', 'platform')
	actions = ['dissociate_selected', ]
	actions_selection_counter = True

#	fields = ('user', 'name', 'version', 'platform', 'is_active', 'device_serial', 
#			'secret', 'secret_hash', 'db_secret', 'db_hash', 'push_token')

	form = SmartPhonAssnForm

	_get_push_tok = lambda self, obj: "%s..." % \
		(obj.push_token[:16] if obj.push_token else "")

	def __init__(self, model, admin_site):
		super(SmartPhoneAssnAdmin, self).__init__(model, admin_site)
		self._get_push_tok.im_func.short_description = 'Push Token'

	def dissociate_selected(self, request, obj):
		for o in obj:
			o.dissociate(request, administrative_request=True)

	def get_actions(self, request):
		actions = super(SmartPhoneAssnAdmin, self).get_actions(request)
		if ('delete_selected' in actions):
			del actions['delete_selected']
		return actions

	def save_model(self, request, obj, form, change):
		obj.save(request)

	def delete_model(self, request, obj):
		obj.dissociate(request, administrative_request=True)

	def has_add_permission(self, request, obj=None):
		return False

	def has_delete_permission(self, request, obj=None):
		return False


sites.register(SmartPhoneAssn, SmartPhoneAssnAdmin)

