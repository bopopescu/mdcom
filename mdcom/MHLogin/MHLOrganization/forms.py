from django import forms
from django.utils.translation import ugettext_lazy as _

from MHLogin.MHLOrganization.utils import get_orgs_I_can_manage, \
	format_tree_data, can_we_move_this_org_under_that_org_byid, get_possible_types_by_org_id
from MHLogin.MHLPractices.models import PracticeLocation
from MHLogin.utils.constants import PROVIDER_CREATE_CHOICES,\
	STAFF_CREATE_CHOICES
from django.core.exceptions import ValidationError

class OrgTypeForm(forms.Form):
	organization_type = forms.ChoiceField(widget=forms.Select())

	def __init__(self, data=None, initial=None, *args, **kwargs):
		user_id = kwargs.pop('user_id', None)
		org_id = kwargs.pop('org_id', None)
		if user_id:
			organization_types = get_possible_types_by_org_id(user_id, org_id=org_id)

			self.base_fields['organization_type'].choices  = [(t.id, t.name)\
				for t in organization_types]
		super(OrgTypeForm, self).__init__(data=data,\
			initial=initial, *args, **kwargs)

class ParentOrgForm(forms.Form):
	parent_org_ids = forms.ChoiceField()
	organization_type = forms.ChoiceField(widget=forms.Select(), help_text=_('You must change organization type of current organization.'))

	def __init__(self, data=None, initial=None, *args, **kwargs):
		self.user_id = kwargs.pop('user_id', None)
		parent_org_ids = kwargs.pop('parent_org_ids', None)
		self.org_id = kwargs.pop('org_id', None)
		if self.user_id:
			org_rs = get_orgs_I_can_manage(self.user_id, org_id_excluded=self.org_id, clear_no_type_org=True)
			self.base_fields['parent_org_ids'].choices = \
					format_tree_data(org_rs, True)
			organization_types = get_possible_types_by_org_id(self.user_id, org_id=self.org_id, parent_org_id=parent_org_ids)

			self.base_fields['organization_type'].choices  = [(t.id, t.name)\
				for t in organization_types]
				

		super(ParentOrgForm, self).__init__(data=data,\
			initial=initial, *args, **kwargs)
		self.fields['parent_org_ids'].label = "Parent Organizations"
	def clean(self): 
		if not can_we_move_this_org_under_that_org_byid(self.user_id, self.org_id, \
					self.cleaned_data['parent_org_ids']):
			raise forms.ValidationError(_("Can't move to the organization."))


class OrganizationProfileSimpleForm(forms.ModelForm):
	parent_org_ids = forms.ChoiceField()
	organization_type = forms.ChoiceField(widget=forms.Select())
	
	def __init__(self, data=None, initial=None, *args, **kwargs):
		super(OrganizationProfileSimpleForm, self).__init__(data=data,\
				initial=initial, *args, **kwargs)

		if initial:
			self.fields['parent_org_ids'].label = "Parent Organizations"
			org_rs = get_orgs_I_can_manage(initial['user_id'], clear_no_type_org=True)
			self.fields['parent_org_ids'].choices = \
					format_tree_data(org_rs, True)
			organization_types = get_possible_types_by_org_id(initial['user_id'], parent_org_id = data['parent_org_ids'])

			if organization_types:
				self.fields['organization_type'].choices  = [(t.id, t.name)\
					for t in organization_types]

	def clean_practice_name(self):
		practice_name = self.cleaned_data['practice_name'].strip()
		practices = PracticeLocation.full_objects.filter(\
				practice_name=practice_name)
		if self.instance.id:
			practices = practices.exclude(id=self.instance.id)
		if practices:
			raise ValidationError(_('This organization has been used.'))
		return practice_name

	class Meta:
		model = PracticeLocation
		fields = ('practice_name',)

class OrganizationSearchForm(forms.Form):
	org_name = forms.CharField()
	def clean_org_name(self):
		org_name = self.cleaned_data['org_name']
		org_name = org_name.strip()
		return org_name
