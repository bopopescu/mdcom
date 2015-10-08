
from django import forms

from MHLogin.Administration.tech_admin import sites, options
from MHLogin.KMS.models import UserPrivateKey, OwnerPublicKey, EncryptedObject


class OwnerPublicKeyAdmin(options.TechAdmin):
	class InnerForm(forms.ModelForm):
		ta = forms.Textarea(attrs={'rows': 10, 'cols': 65, 'style': "font-family:courier;"})
		ta2 = forms.Textarea(attrs={'rows': 30, 'cols': 65, 'style': "font-family:courier;"})
		_publickey = forms.CharField(label="Public Key", widget=ta)
		_adminscopy = forms.CharField(label="Private Key (Admin's copy)", widget=ta2)
		_admincipher = forms.CharField(label="Cipherkey (Decrypted "
					"with admin reset key)", widget=ta)

		def __init__(self, *args, **kwargs):
			super(OwnerPublicKeyAdmin.InnerForm, self).__init__(*args, **kwargs)
			opub = kwargs.get('instance', None)
			self.fields['_publickey'].initial = opub and opub.publickey
			self.fields['_admincipher'].initial = opub and opub.admincipher
			self.fields['_adminscopy'].initial = opub and opub.adminscopy
			for fname in ['_publickey', '_admincipher', '_adminscopy']:
				self.fields[fname].widget.attrs['disabled'] = 'disabled'

# 	def has_delete_permission(self, request, obj=None):
# 		return False

# TODO: in django 1.6...
# 	def get_search_results(self, request, queryset, search_term):
# 		queryset, distinct = super(OwnerPublicKeyAdmin, self).\
# 			get_search_results(request, queryset, search_term)
# 		try:
# 			queryset |= self.model.objects.filter(owner__username=search_term)
# 		except Exception as e:
# 			print e
# 		return queryset, distinct

	form = InnerForm
	list_display = ('owner', 'owner_type', 'owner_id', 'keytype', 'create_date')
	search_fields = ('owner_id', )
	readonly_fields = ('owner_type', 'owner_id', 'keytype', 'active')


class UserPrivateKeyAdmin(options.TechAdmin):
	class InnerForm(forms.ModelForm):
		ta = forms.Textarea(attrs={'rows': 30, 'cols': 65, 'style': "font-family:courier;"})
		_privatekey = forms.CharField(label="Private Key (encrypted via credentials)", widget=ta)

		def __init__(self, *args, **kwargs):
			super(UserPrivateKeyAdmin.InnerForm, self).__init__(*args, **kwargs)
			upriv = kwargs.get('instance', None)
			self.fields['_privatekey'].initial = upriv and upriv.privatekey
			for fname in ['_privatekey']:
				self.fields[fname].widget.attrs['disabled'] = 'disabled'

# 	def has_delete_permission(self, request, obj=None):
# 		return False

	form = InnerForm
	list_display = ('user', 'opub', 'credtype', 'create_date', 'expire_date', 'gfather')
	search_fields = ('user__username', 'user__first_name', 'user__last_name')
	list_filter = ('gfather', 'opub__keytype', 'credtype')
	readonly_fields = ('user', 'opub', 'credtype')


class EncryptedObjectAdmin(options.TechAdmin):
	class InnerForm(forms.ModelForm):
		ta = forms.Textarea(attrs={'rows': 10, 'cols': 65, 'style': "font-family:courier;"})
		_cipherkey = forms.CharField(label="Cipherkey (pubkey encrypted)", widget=ta)

		def __init__(self, *args, **kwargs):
			super(EncryptedObjectAdmin.InnerForm, self).__init__(*args, **kwargs)
			encobj = kwargs.get('instance', None)
			self.fields['_cipherkey'].initial = encobj and encobj.cipherkey
			self.fields['_cipherkey'].widget.attrs['disabled'] = 'disabled'

# 	def has_delete_permission(self, request, obj=None):
# 		return False

	form = InnerForm
	list_display = ('object_type', 'object_id', 'object', 'opub', 'create_date')
	readonly_fields = ['object_type', 'object_id', 'object', 'opub', 'create_date']
	search_fields = ('object_id', )
	list_filter = ('opub__owner_type', 'opub__keytype')

sites.register(OwnerPublicKey, OwnerPublicKeyAdmin)
sites.register(UserPrivateKey, UserPrivateKeyAdmin)
sites.register(EncryptedObject, EncryptedObjectAdmin)

