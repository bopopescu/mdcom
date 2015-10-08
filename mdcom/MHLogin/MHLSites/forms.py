
from django import forms
from django.forms import ModelForm
from django.forms.util import ErrorList
from django.utils.translation import ugettext_lazy as _

from MHLogin.utils.geocode import geocode2
from MHLogin.MHLSites.models import Site, Hospital, STATE_CHOICES


SEARCH_CHOICES = (
    ('AL', _('Display All')),
    ('NA', _('Search by Name')),
    ('CI', _('Search by City')),
    ('ST', _('Search by State')),
    ('ZI', _('Search by Zipcode')),
    ('PR', _('Search by Proximity'))
)


class CurrentSiteForm(forms.Form):
	current = forms.ChoiceField(choices=())

	def __init__(self, sites, *args, **kwargs):
		super(CurrentSiteForm, self).__init__(*args, **kwargs)

		self.fields['current'].choices = [['0', _('---(None)---')], ]

		for site in sites:
			self.fields['current'].choices.append([site.id, site.name])


class SiteManagementForm(forms.Form):
	record_key = forms.CharField(min_length=1, max_length=26, widget=forms.HiddenInput)
	site_list = forms.ModelMultipleChoiceField(queryset=Site.objects.none(), required=False, label="Sites")

	def __init__(self, searchby, searchbyvalue, latmin, latmax, longitmin, longitmax, site_list, *args, **kwargs):
		super(SiteManagementForm, self).__init__(*args, **kwargs)
		if latmin == 0 and latmax == 0 and longitmin == 0 and longitmax == 0:
			self.fields['site_list'].queryset = Site.objects.all()
		else:
			sites = Site.objects.filter(lat__range=(latmin, latmax)).\
					filter(longit__range=(longitmin, longitmax))
			site_ids = [s.id for s in sites] + site_list
			self.fields['site_list'].queryset = Site.objects.filter(pk__in=site_ids)
		"""
		if (searchby == 'name'):
			self.fields['site_list'].queryset=Site.objects.filter(name__istartswith=searchbyvalue)
		elif (searchby == 'city'):
			self.fields['site_list'].queryset=Site.objects.filter(city__istartswith=searchbyvalue)
		elif (searchby == 'state'):
			self.fields['site_list'].queryset=Site.objects.filter(state__iexact=searchbyvalue)
		elif (searchby == 'zip'):
			self.fields['site_list'].queryset=Site.objects.filter(zip__istartswith=searchbyvalue)
		else:
			self.fields['site_list'].queryset=Site.objects.filter(lat__range=(latmin,latmax)).\
				filter(longit__range=(longitmin, longitmax))
		"""
	def error_current_site_removal(self):
		msg = _('You cannot remove your current site. To remove it, please change your current site first.')
		if (not 'site_list' in self._errors):
			self._errors["site_list"] = ErrorList([msg])
		else:
			self._errors["site_list"].append(msg)
		return

		err_msg = _('You cannot remove your current site. To remove it, '
				'please change your current site first.')
		self._errors['site_list'] = ErrorList([_('The callback number must contain ONLY '
			'the digits 0-9, the asterisk (*) and/or pound (#) symbols.'), ])
		#self._errors['site_list'] = self.error_class([err_msg,])


class SiteForm(ModelForm):
	class Meta:
		model = Site


class MySiteForm(ModelForm):
	class Meta:
		model = Site

	def clean(self):
		#raise Exception('Entered SiteForm clean function.')
		cleaned_data = self.cleaned_data
		street = cleaned_data['address1']
		city = cleaned_data['city']
		state = cleaned_data['state']
		zip = cleaned_data['zip']
		if ((street and city and state)) or ((street and zip)):
			geocode_response = geocode2(street, city, state, zip)
			cleaned_data['lat'] = geocode_response['lat']
			cleaned_data['longit'] = geocode_response['lng']
		else:
			raise forms.ValidationError(_('At a minimum, please enter in either '
				'street, city and state or street and zip'))
		return cleaned_data


class HospitalForm(ModelForm):
	class Meta:
		model = Hospital


class SiteSearchForm(forms.Form):
	name = forms.CharField(required=False)
	city = forms.CharField(required=False)
	state = forms.ChoiceField(choices=STATE_CHOICES, required=False)
	zip = forms.CharField(required=False)
	proximity = forms.DecimalField(required=False)
	searchRadio = forms.ChoiceField(widget=forms.RadioSelect, choices=SEARCH_CHOICES, required=False)

