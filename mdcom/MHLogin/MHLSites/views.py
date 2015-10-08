import json

from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.utils.translation import ugettext as _
from django.http.response import HttpResponseBadRequest

from MHLogin.MHLSites.forms import SiteSearchForm, MySiteForm, CurrentSiteForm, \
	SiteManagementForm
from MHLogin.MHLSites.models import Site
from MHLogin.MHLUsers.decorators import RequireAdministrator
from MHLogin.MHLUsers.utils import user_is_provider, user_is_office_staff
from MHLogin.utils.geocode import miles2latlong_range, geocode2
from MHLogin.utils.templates import get_context


@RequireAdministrator
def site_admin(request):
	context = get_context(request)

	context['sites'] = Site.objects.all()

	if (request.POST):
		if (request.POST['searchRadio'] == 'ST'):
			if ('state' in request.POST):
				state = request.POST['state']
				context['sites'] = Site.objects.filter(state__iexact=state)
		elif (request.POST['searchRadio'] == 'PR'):
			if ('proximity' in request.POST):
				user = user_is_provider(request.user)
				# use MHLUser's lat, longit instead of Provider's office_lat, office_longit
				mylat = user.user.lat
				mylongit = user.user.longit
				miles = float(request.POST['proximity'])
				latmin, latmax, longitmin, longitmax = miles2latlong_range(mylat, mylongit, miles)
				nearbySites = Site.objects.filter(lat__range=(latmin, latmax)).filter(longit__range=(longitmin, longitmax))
				context['sites'] = nearbySites
		elif (request.POST['searchRadio'] == 'CI'):
			if ('city' in request.POST):
				city = request.POST['city']
				context['sites'] = Site.objects.filter(city__istartswith=city)
		elif (request.POST['searchRadio'] == 'ZI'):
			if ('zip' in request.POST):
				zip = request.POST['zip']
				context['sites'] = Site.objects.filter(zip__istartswith=zip)
		elif (request.POST['searchRadio'] == 'NA'):
			if ('name' in request.POST):
				name = request.POST['name']
				context['sites'] = Site.objects.filter(name__istartswith=name)
		#raise Exception(request.POST)
		else:
			context['sites'] = Site.objects.all()

	context['searchby'] = SiteSearchForm()

	return render_to_response('Sites/sites_view.html', context)


@RequireAdministrator
def site_add(request):
	context = get_context(request)

	if (request.method == 'POST'):
		site_form = MySiteForm(request.POST)
		if (site_form.is_valid()):
			#raise Exception('site_form is valid')
			site_form.save()
			return HttpResponseRedirect(reverse('MHLogin.MHLSites.views.site_admin'))

		else:  # if not (site_form.is_valid()):
			context['site'] = site_form
	else:  # if (request.method != "POST"):
		context['site'] = MySiteForm()

	return render_to_response('Sites/site_edit.html', context)


def site_edit(request, siteID):
	context = get_context(request)
	site = get_object_or_404(Site, id=siteID)

	if (request.method == 'POST'):
		site_form = MySiteForm(request.POST, instance=site)
		if (site_form.is_valid()):
			#raise Exception('site_form is valid')
			site_form.save()
			return HttpResponseRedirect(reverse('MHLogin.MHLSites.views.site_admin'))

		else:  # if not (site_form.is_valid()):
			context['site'] = site_form
	else:  # if (request.method != "POST"):
		context['site'] = MySiteForm(instance=site)

	return render_to_response('Sites/site_edit.html', context)


def manage_sites(request):
	provider = user_is_provider(request.user)
	staffer = user_is_office_staff(request.user)
	if (not (provider or staffer)):
		return HttpResponseRedirect('/')

	try:
		if (provider):
			user = provider
			lat = float(user.lat)
			longit = float(user.longit)
		elif (staffer):
			user = staffer
			if user.current_practice:
				lat = float(user.current_practice.practice_lat)
				longit = float(user.current_practice.practice_longit)
			else:
				geocode_response = geocode2(user.office_address1, \
						user.office_city, user.office_state, user.office_zip)
				lat = geocode_response['lat']
				longit = geocode_response['lng']
	except:
		lat, longit = (0, 0)

	context = get_context(request)

	# get the latitutde, longitude range to search for nearby sites
	if not lat and not longit:
		latmin, latmax, longitmin, longitmax = (0, 0, 0, 0)
	else:
		latmin, latmax, longitmin, longitmax = miles2latlong_range(lat, longit)

	sites = user.sites.all()

	if (request.method == "POST"):

		searchby = ''
		searchbyvalue = ''
		"""
		#raise Exception(request.POST)
		if ('submit_search_criteria' and 'searchby' and 'searchbyvalue' in request.POST):
			raise Exception(request.POST)
			searchby = request.POST['searchby']
			searchbyvalue = request.POST['searchbyvalue']
			#raise Exception(request.POST)

			if (searchby == 'proximity'):
					miles = float(searchbyvalue)
					del_lat, del_longit = miles2latlong(miles, lat, longit)
					latmin = lat - del_lat
					latmax = lat + del_lat
					longitmin = longit - del_longit
					longitmax = longit + del_longit
					#raise Exception(miles, latmin, latmax, longitmin, longitmax)
		"""

		context['site_form'] = CurrentSiteForm(sites, request.POST)
		site_list_ids = [site.id for site in sites]
		context['affiliation_form'] = SiteManagementForm(searchby, searchbyvalue, latmin, latmax, longitmin, longitmax, site_list_ids, request.POST)
#		context['affiliation_form'] = SiteManagementForm(request.POST)

		if (context['site_form'].is_valid()):
			new_site_id = int(context['site_form'].cleaned_data['current'])
			if (new_site_id == 0):
				new_site = None
			else:
				site_ids = [site.id for site in sites]
				if (not new_site_id in site_ids):
					raise Exception(_("User tried to select site id ") + str(new_site_id) + _(", but isn't affiliated with that site."))

				# Check to see if the site exists
				new_site = Site.objects.filter(id=new_site_id).all()
				if (new_site.count() != 1):
					raise Exception(_("Incorrect number of sites found for id ") + str(new_site_id))
				new_site = new_site[0]

			user.current_site = new_site
			user.save()
			return HttpResponseRedirect(reverse('MHLogin.MHLUsers.views.profile_view'))

		elif (context['affiliation_form'].is_valid()):
			new_sites = context['affiliation_form'].cleaned_data['site_list']
			new_site_ids = [site.id for site in new_sites]

			# This ensures that providers can't remove their current site. The outer check
			# is just to make sure that an error doesn't occur when the provider doesn't have
			# a current site.
			site_match = True
			if (user.current_site != None):
				site_match = False
				for site in new_site_ids:
					if (user.current_site.id == site):
						site_match = True

			if (site_match):
				user.sites = new_sites
				user.save()
				return HttpResponseRedirect(reverse('MHLogin.MHLUsers.views.profile_view'))
			else:
				context['affiliation_form'].error_current_site_removal()
	else:
		if (user.sites):
			site_list_ids = [site.id for site in user.sites.all()]
			site_list = {
					'site_list': site_list_ids,
					'record_key': '1IFSWP3s8gjRpqzJyvhM',
				}
			context['affiliation_form'] = SiteManagementForm('proximity', 'none', latmin, 
				latmax, longitmin, longitmax, site_list_ids, initial=site_list)
#			context['affiliation_form'] = SiteManagementForm(initial=site_list)
		else:
			site_list = dict()
			site_list = {
					'record_key': '1IFSWP3s8gjRpqzJyvhM',
				}
			context['affiliation_form'] = SiteManagementForm('proximity', 'none', latmin, 
				latmax, longitmin, longitmax, [], initial=site_list)
#			context['affiliation_form'] = SiteManagementForm(initial=site_list)

	if (user.current_site):
		current_site = {
						'current': user.current_site.id,
				}
		context['site_form'] = CurrentSiteForm(sites, initial=current_site)
	else:
		context['site_form'] = CurrentSiteForm(sites)

	#context['new_affiliation_form'] = NewSiteManagementForm(initial=site_list)
	return render_to_response("Sites/sites_edit.html", context)


#add by xlin 121011 for issue1289
def searchSites(request):
	option = request.GET['term'].lower()
	sites = Site.objects.filter(name__icontains=option)
	results = [{'name':site.name, 'id':site.id}
			for site in sites]
	return HttpResponse(json.dumps(results))


def change_current_site(request):
	context = get_context(request)
	provider = user_is_provider(request.user)
	staffer = user_is_office_staff(request.user)
	if (provider):
		user = provider
	if (staffer):
		user = staffer
	sites = user.sites.all()
	if (request.method == "POST"):
		current = request.POST.get('id')
		form = CurrentSiteForm(sites, request.POST)
		context['site_form'] = form
		if (form.is_valid()):
			new_site_id = int(context['site_form'].cleaned_data['current'])
			if (new_site_id == 0):
				new_site = None
			else:
				site_ids = [site.id for site in sites]
				if (not new_site_id in site_ids):
					raise Exception(_("User tried to select site id ") + str(new_site_id) +
								 _(", but isn't affiliated with that site."))
				new_site = Site.objects.filter(id=new_site_id).all()
				if (new_site.count() != 1):
					raise Exception(_("Incorrect number of sites found for id ") + str(new_site_id))
				new_site = new_site[0]

			user.current_site = new_site
			user.save()
			return HttpResponse(json.dumps({'status': 'ok'}))
		else:
			err_obj = {
				'errors': form.errors,
			}
			return HttpResponseBadRequest(json.dumps(err_obj), mimetype='application/json')

