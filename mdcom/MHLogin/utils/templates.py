"""Standard functions to reduce duplicative code"""

from MHLogin import __version__
import re
from django.conf import settings
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django.forms.models import model_to_dict

from MHLogin.utils.timeFormat import getCurrentTimeZoneForUser, getDisplayedTimeZone
from MHLogin.MHLUsers.utils import get_managed_practice,get_fullname
from MHLogin.MHLOrganization.utils import get_prefer_logo, get_org_type_name
from MHLogin.utils.constants import RESERVED_ORGANIZATION_TYPE_ID_PRACTICE
from MHLogin.MHLSites.forms import CurrentSiteForm


def phone_formater(phone, display_provisionLink=False):
	phonePattern = re.compile(r'''
                # don't match beginning of string, number can start anywhere
    (\d{3})     # area code is 3 digits (e.g. '800')
    \D*         # optional separator is any number of non-digits
    (\d{3})     # trunk is 3 digits (e.g. '555')
    \D*         # optional separator
    (\d{4})     # rest of number is 4 digits (e.g. '1212')
    \D*         # optional separator
    (\d*)       # extension is optional and can be any number of digits
    $           # end of string
    ''', re.VERBOSE)

	if (phone == ''):
		if (display_provisionLink):
			if settings.CALL_ENABLE:
				return '(<a href="/ProvisionNumber/">%s</a>)' % _('none; get yours here')
			else:
				return _('(none)')
		return _('(none)')

	match = phonePattern.search(phone)
	if (match):
		parts = match.groups()
		return "(%s) %s-%s" % (parts[0], parts[1], parts[2])
	else:
		return _("(invalid phone number: %s)") % (phone,)


def getTemplateDict(request, activeApp=None):
	"""Function obsoleted. We should have been using the more Django-esque term
	'context' for this function and its return data."""
	return get_context(request, activeApp=activeApp)


def processor(request, activeApp=None):
	"""Creates a dictionary complete with standard MyHealth template definitions."""
	context = {}

	mobile_device_check(request, context)

	context['debug'] = settings.DEBUG
	context['DEBUG'] = settings.DEBUG

	context['SERVER_ADDRESS'] = settings.SERVER_ADDRESS
	context['SERVER_PROTOCOL'] = settings.SERVER_PROTOCOL
	context['SERVERVERSION'] = "v%s" % '.'.join(__version__.split('.')[0:3])

	if (not 'MHL_UserIDs' in request.session or not 'MHL_Users' in request.session):
		return context

	# Get user types
	context['sender_types'] = request.session['MHL_UserIDs']

	if request and request.user.is_authenticated():
		# initialize to defaults
		context['current_site'] = ""
		context['current_practice'] = None
		context['current_time_zone'] = ""

		context['schedule_time_setting'] = 1

		if ('Provider' in request.session['MHL_Users']):
			provider = request.session['MHL_Users']['Provider']
			user = provider
			context['user_is_provider'] = True
			context['current_site'] = provider.current_site
			context['practice'] = provider.practices.filter(\
				organization_type__pk=RESERVED_ORGANIZATION_TYPE_ID_PRACTICE)
			current_practice = provider.current_practice
			if current_practice and current_practice.organization_type\
				and RESERVED_ORGANIZATION_TYPE_ID_PRACTICE == current_practice.organization_type.id:
				context['current_practice'] = current_practice
			context['unread_msg_count'] = provider.vm_msgs.filter(read_flag=False).count()
			sites = user.sites.all()
			if (user.current_site):
				current_site = {'current': user.current_site.id}
				context['site_form'] = CurrentSiteForm(sites, initial=current_site)
			else:
				context['site_form'] = CurrentSiteForm(sites)
		#inna - add some info for office manager	
		if ('OfficeStaff' in request.session['MHL_Users']):
			#add by xlin in 20120328 to fix bug 580 that current site not show
			context['current_site'] = request.session['MHL_Users']['OfficeStaff'].current_site

			if ('OfficeStaff' in request.session['MHL_Users']):
				staff = request.session['MHL_Users']['OfficeStaff']
				user = staff
				context['current_practice'] = request.\
					session['MHL_Users']['OfficeStaff'].current_practice
				context['current_practice_can_have_any_staff'] = \
						context['current_practice'] and\
						context['current_practice'].can_have_any_staff()
				context['current_practice_can_have_any_provider'] = \
						context['current_practice'] and\
						context['current_practice'].can_have_any_provider()

			if  ('Office_Manager' in request.session['MHL_UserIDs']):
				context['user_is_office_manager'] = True
				office_staff = request.session['MHL_Users']['OfficeStaff']
				user = office_staff
				context['managed_practices'] = get_managed_practice(office_staff)
			else:
				context['user_is_office_staff'] = True
			sites = user.sites.all()
			if (user.current_site):
				current_site = {
								'current': user.current_site.id,
						}
				context['site_form'] = CurrentSiteForm(sites, initial=current_site)
			else:
				context['site_form'] = CurrentSiteForm(sites)

		context['mhl_user_displayName'] = get_fullname(request.session['MHL_Users']['MHLUser'])
		current_time_zone_key = getCurrentTimeZoneForUser(
				request.session['MHL_Users']['MHLUser'],
				current_practice=context['current_practice'])
		context['current_time_zone'] = getDisplayedTimeZone(current_time_zone_key)

		#add by xlin 121017 for todo1045
		if request.session['MHL_Users']['MHLUser'].time_setting:
			context['schedule_time_setting'] = 0
		else:
			context['schedule_time_setting'] = 1

		# TODO, if dcAdmin need custom_logo, remove the limitation.
		if "dcAdmin" not in request.path_info:
			context['prefer_logo'] = get_prefer_logo(request.session['MHL_Users']['MHLUser'].id)

		current_practice = context['current_practice']
		context['can_have_answering_service'] = False
		context["current_organization_type"] = ""
		if current_practice:
			context['can_have_answering_service'] = current_practice.\
				get_setting_attr('can_have_answering_service')
			context["current_organization_type"] = get_org_type_name(current_practice)

	return context


def get_context(request, activeApp=None):
	"""Creates a dictionary complete with standard MyHealth template definitions."""
	# context created in processor template callback	
	return RequestContext(request, current_app=activeApp)


def get_context_for_organization(request, activeApp=None):
	"""Get context for organization module."""
	context = get_context(request, activeApp=activeApp)

	context['can_manage_setting'] = 'Administrator' in \
			request.session['MHL_Users'] 

	if request.org_setting:
		org_setting = request.org_setting
		org_setting_dict = model_to_dict(request.org_setting, exclude='id')
		context.update(org_setting_dict)
		context["can_have_provider_users"] = org_setting.can_have_physician or\
				org_setting.can_have_nppa or\
				org_setting.can_have_medical_student
		context["can_have_staff_users"] = org_setting.can_have_staff or\
				org_setting.can_have_manager or org_setting.can_have_nurse or\
				org_setting.can_have_dietician

	context["selected_organization_type"] = get_org_type_name(request.org)
	return context


def mobile_device_check(request, context):
	user_agent = ""
	if 'HTTP_USER_AGENT' in request.META:
		user_agent = request.META['HTTP_USER_AGENT']

	#comment = "Mozilla/5.0 (Linux; U; Android 2.1-update1; en-us; SGH-T959 Build/ECLAIR) 
	# AppleWebKit/530.17 (KHTML, like Gecko) Version/4.0 Mobile Safari/530.17"

	agents_list = ['Nokia', 'bMOT', '^LGE?b', 'SonyEricsson',
	'Ericsson', 'BlackBerry', 'DoCoMo', 'Symbian',
	'Windows CE', 'NetFront', 'Klondike', 'PalmOS',
	'PalmSource', 'portalmm', 'S[CG]H-', 'bSAGEM',
	'SEC-', 'jBrowser-WAP', 'Mitsu', 'Panasonic-',
	'SAMSUNG-', 'Samsung-', 'Sendo', 'SHARP-',
	'Vodaphone', 'BenQ', 'iPAQ', 'AvantGo',
	'Go.Web', 'Sanyo-', 'AUDIOVOX', 'PG-',
	'CDM[-d]', '^KDDI-', '^SIE-', 'TSM[-d]',
	'^KWC-', 'WAP', '^KGT [NC]', 'iPhone', 'Android', 'droid',
	'android', 'Nexus', 'HTC', 'HTC_HD2', 'Motorola', ]
	context['is_mobile'] = False
	for agent in agents_list:
		if re.search(agent, user_agent):
			context['is_mobile'] = True

	context['is_blackberry'] = False
	if re.search('BlackBerry', user_agent):
		context['is_blackberry'] = True

	if ('set_to_mobile' in request.session):
		context['is_mobile'] = request.session['set_to_mobile']


def set_settings_to_dict(context):
	if context:
		context["CALL_ENABLE"] = settings.CALL_ENABLE
		return context
	else:
		return {} 

