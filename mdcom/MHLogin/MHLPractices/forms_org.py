
from django import forms
from django.utils.translation import ugettext_lazy as _

from MHLogin.MHLPractices.models import OrganizationType, \
	OrganizationSetting
from MHLogin.MHLOrganization.utils_org_type import how_many_instances
from MHLogin.utils.constants import RESERVED_ORGANIZATION_TYPE_ID_SYSTEM


class OrganizationTypeForm(forms.ModelForm):
	subs = forms.ModelMultipleChoiceField(queryset=OrganizationType.objects.filter
		(delete_flag=False).exclude(id=RESERVED_ORGANIZATION_TYPE_ID_SYSTEM).
			select_related('id', 'name'), widget=forms.CheckboxSelectMultiple(), required=False)

	class Meta:
		model = OrganizationType
		exclude = ['delete_flag', 'uuid', 'organization_setting']
		widgets = {
			'description': forms.Textarea(attrs={'rows': '6', 'cols': '70'})
		}

	def clean_subs(self):
		subs = self.cleaned_data['subs']
		if 'subs' not in self.initial:
			return subs
		initail_subs = self.initial['subs']
		new_subs_ids = [sub_type.id for sub_type in subs]
		id = self.initial['id']
		cannt_remove_names = []
		for initail_sub in initail_subs:
			if initail_sub not in new_subs_ids:
				orgs = how_many_instances(initail_sub, parent_type_id=id)
				if orgs and len(orgs) > 0:
					sub_type = OrganizationType.objects.get(id=initail_sub)
					cannt_remove_names.append(sub_type.name)
		err_msg = ""
		if cannt_remove_names and len(cannt_remove_names) > 0:
			if len(cannt_remove_names) > 1:
				cannt_remove_names = ", ".join(cannt_remove_names)
				err_msg = _("You can't remove the sub types %s, because they have been used.") \
					% (cannt_remove_names)
			else:
				err_msg = _("You can't remove the sub type %s, because it has been used.") \
					% (cannt_remove_names[0])

		if err_msg:
			raise forms.ValidationError(err_msg)
		else:
			return subs


class OrganizationSettingForm(forms.ModelForm):
	def clean(self):
		cleaned_data = self.cleaned_data
		return cleaned_data

	class Meta:
		model = OrganizationSetting
		exclude = ['staff', 'provider', 'techadmin', 'delete_flag']


class MemberSearchForm(forms.Form):
	first_name = forms.CharField(required=True)
	last_name = forms.CharField(required=True)

	def clean(self):
		return self.cleaned_data


