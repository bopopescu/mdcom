
from functools import wraps
from MHLogin.utils.errlib import err403, err404
from MHLogin.MHLPractices.models import PracticeLocation
from MHLogin.MHLOrganization.utils import can_user_manage_this_org


def RequireAdministrator(func):
	"""
	Used as a decorator for view functions requiring administrator rights.
	"""
	@wraps(func)
	def f(request, *args, **kwargs):
		if 'Administrator' not in request.session['MHL_Users']:
			return err403(request)

		return func(request, *args, **kwargs)

	return f


def RequireOrganizationManager(func):
	@wraps(func)
	def f(request, *args, **kwargs):
		if 'org_id' in request.REQUEST and \
			request.REQUEST['org_id']:
			org_id = int(request.REQUEST['org_id'])
			request.session['SELECTED_ORG_ID'] = org_id
		elif 'SELECTED_ORG_ID' in request.session and \
			request.session['SELECTED_ORG_ID']:
			org_id = request.session['SELECTED_ORG_ID']

		try:
			request.org = PracticeLocation.objects.get(pk=org_id)
		except:
			return err404(request)

		ret_data = can_user_manage_this_org(org_id, request.user.id)
		if not ret_data["can_manage_org"]:
			return err403(request)

		request.org_setting = request.org.get_setting()
		request.org_mgr = ret_data["Office_Manager"]
		request.org_admin = ret_data["Administrator"]
		return func(request, *args, **kwargs)
	return f


