from django import forms


class staffSearchForm(forms.Form):
	# Sample data:
	search_name = forms.CharField()


class AssociationProviderIdForm(forms.Form):
	prov_id = forms.IntegerField()


class AssociationAssocIdForm(forms.Form):
	assoc_id = forms.IntegerField()


class ProviderByMailForm(forms.Form):
	email = forms.CharField(required=False)
	fullname = forms.CharField(required=False)
	firstName = forms.CharField(required=False)
	lastName = forms.CharField(required=False)
	username = forms.CharField(required=False)


class ProviderSearchForm(forms.Form):
	firstName = forms.CharField(required=False)
	lastName = forms.CharField(required=False)


class currentStaffSearchForm(forms.Form):
	firstName = forms.CharField(required=False)
	lastName = forms.CharField(required=False)
