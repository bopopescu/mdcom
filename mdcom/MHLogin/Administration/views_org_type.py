import json
import thread
import time

from django.core.urlresolvers import reverse
from django.conf import settings
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseBadRequest
from django.shortcuts import render_to_response
from django.utils.translation import ugettext_lazy as _

from MHLogin.MHLPractices.forms_org import OrganizationTypeForm, OrganizationSettingForm
from MHLogin.MHLPractices.models import OrganizationType, PracticeLocation
from MHLogin.MHLUsers.decorators import RequireAdministrator
from MHLogin.utils.templates import get_context
from MHLogin.MHLOrganization.utils_org_type import can_we_remove_this_org_type, how_many_instances
from MHLogin.Administration.forms_org_type import CheckSubTypeForm
from MHLogin.MHLOrganization.utils import notify_org_users_tab_chanaged
from MHLogin.utils.mh_logging import get_standard_logger

logger = get_standard_logger('%s/Administration/views_org_type.log' % (settings.LOGGING_ROOT),
							'Administration.views_org_type', settings.LOGGING_LEVEL)

@RequireAdministrator
def org_type_list(request):
	context = get_context(request)
	org_types = OrganizationType.objects.filter(delete_flag=False)\
			.order_by('id')

	org_type_list = [{
				'id':org_type.id,
				'name':org_type.name,
				'description':org_type.description,
				'public': _('Yes') if org_type.is_public else _('No'),
				'can_delete': can_we_remove_this_org_type(org_type.id)
			} for org_type in org_types]
	context['org_type_list'] = org_type_list
	return render_to_response('organization/organization_type_list.html', context)


@RequireAdministrator
def org_type_create(request):
	context = get_context(request)
	type_form = OrganizationTypeForm()
	setting_form = OrganizationSettingForm()

	if request.method == 'POST':
		type_form = OrganizationTypeForm(request.POST)
		setting_form = OrganizationSettingForm(request.POST)
		if type_form.is_valid() and setting_form.is_valid():
			org_setting = setting_form.save()
			org_type = type_form.save(commit=False)
			org_type.organization_setting = org_setting
			org_type.save()

			sub_types = type_form.cleaned_data['subs']
			org_type.save_sub_types(list(sub_types))
			return HttpResponseRedirect(reverse('MHLogin.Administration.views_org_type.org_type_list'))

	context['page_name'] = _('Create Organization Type')
	context['type_form'] = type_form
	context['setting_form'] = setting_form
	return render_to_response('organization/create_organization_type.html', context)


@RequireAdministrator
def org_type_edit(request, org_type_id):
	context = get_context(request)

	org_type = None
	org_setting = None
	if org_type_id:
		org_types = OrganizationType.objects.filter(pk=org_type_id, delete_flag=False)
		if org_types:
			org_type = org_types[0]
			org_setting = org_type.organization_setting
			old_display_in_contact_list_tab = org_setting.display_in_contact_list_tab
	type_form = OrganizationTypeForm(instance=org_type)
	setting_form = OrganizationSettingForm(instance=org_setting)

	if request.method == 'POST':
		type_form = OrganizationTypeForm(request.POST, instance=org_type)
		setting_form = OrganizationSettingForm(request.POST, instance=org_setting)
		if type_form.is_valid() and setting_form.is_valid():
			org_setting = setting_form.save()
			org_type = type_form.save(commit=False)
			org_type.organization_setting = org_setting
			org_type.save()

			sub_types = type_form.cleaned_data['subs']
			org_type.save_sub_types(list(sub_types))
			context['has_saved'] = True

			new_display_in_contact_list_tab = org_setting.display_in_contact_list_tab
			logger.debug("new display_in_contact_list_tab: %s, old display_in_contact_list_tab: %s"\
					%(str(new_display_in_contact_list_tab), str(old_display_in_contact_list_tab)))
			if not new_display_in_contact_list_tab == old_display_in_contact_list_tab:
				org_ids = list(PracticeLocation.objects.filter(organization_type = org_type)\
					.values_list("id", flat=True))
				logger.debug("Following organization has this type: %s"%str(org_ids))
				# send notification to related users
				thread.start_new_thread(notify_org_users_tab_chanaged,\
							(org_ids, ), {"include_member_org": True})

	context['page_name'] = _('Edit Organization Type')
	context['type_form'] = type_form
	context['setting_form'] = setting_form
	return render_to_response(\
		'organization/create_organization_type.html', context)


@RequireAdministrator
def org_type_del(request, org_type_id):
	org_types = OrganizationType.objects.filter(pk=org_type_id, delete_flag=False)
	org_type = None
	if org_types:
		org_type = org_types[0]
		if can_we_remove_this_org_type(org_type.id):
			org_type.name = ' '.join([str(org_type.name),
				'Removed', str(int(time.time()))])
			org_type.delete_flag = True
			org_type.save()
			return HttpResponse(json.dumps('ok'))
	return HttpResponse(json.dumps('error'))


@RequireAdministrator
def check_remove_sub_type(request):
	cannt_remove_orgs = []
	if (request.method == 'POST'):
		form = CheckSubTypeForm(request.POST)
		if (form.is_valid()):
			type_ids = form.cleaned_data["type_ids"]
			parent_type_id = form.cleaned_data["parent_type_id"]
			for type_id in type_ids:
				orgs = how_many_instances(type_id, parent_type_id=parent_type_id)
				if orgs and len(orgs) > 0:
					cannt_remove_orgs.append(type_id)
		else:
			err_obj = {
				'errors': form.errors,
			}
			return HttpResponseBadRequest(json.dumps(err_obj), mimetype='application/json')

	ret_json = {
		"cannt_remove_orgs": cannt_remove_orgs
	}
	return HttpResponse(json.dumps(ret_json), mimetype='application/json')

