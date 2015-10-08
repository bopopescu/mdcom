
import json

from django.conf import settings
from django.contrib.auth.views import logout
from django.contrib.auth import authenticate, login
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from MHLogin.DoctorCom.Messaging.utils import get_message_count
from MHLogin.Logs.models import LoginEvent, LogoutEvent
from MHLogin.MHLogin_Main.forms import LoginForm, ToSAcceptForm, ToSRejectForm
from MHLogin.MHLPractices.models import Pending_Association

from MHLogin.MHLUsers.models import MHLUser
from MHLogin.MHLUsers.utils import get_all_site_providers, \
	get_community_providers, get_community_professionals, \
	all_practice_members, get_all_site_clinical_clerks, user_is_active, \
	get_community_providers_by_coords, \
	set_providers_result, set_practice_members_result, get_all_site_staff,\
	set_site_staff_result
from MHLogin.KMS.utils import store_user_key, recrypt_keys
from MHLogin.KMS.models import UserPrivateKey, CRED_WEBAPP
from MHLogin.utils.templates import get_context, phone_formater
from MHLogin.utils.mh_logging import get_standard_logger 
from MHLogin.utils.constants import STATE_CHOICES

from MHLogin.MHLPractices.utils import get_practices_by_position, set_practices_result
from MHLogin.MHLOrganization.utils import get_org_type_name
from MHLogin.MHLOrganization.utils_org_tab import getOrganizationsOfUser, renderOrganizationForDashbord
from MHLogin.MHLFavorite.utils import get_my_favorite

# Setting up logging
logger = get_standard_logger('%s/DoctorCom/IVR/views_generic.log' % 
	(settings.LOGGING_ROOT), 'DCom.IVR.views_gen', settings.LOGGING_LEVEL)


def fp_test(request):
	return render_to_response('fp_test.html')


def main(request):
	if request.user.is_authenticated():
		if ('Physician' in request.session['MHL_Users']):
			return main_physician(request, request.session['MHL_Users']['Physician'])
			#return HttpResponseRedirect('/')
		if ('NP_PA' in request.session['MHL_Users']):
			return main_np_pa(request, request.session['MHL_Users']['NP_PA'])
		if ('Nurse' in request.session['MHL_Users']):
			#return main_nurse(request, request.session['MHL_Users']['Nurse'])
			return HttpResponseRedirect(reverse('MHLogin.MHLPractices.views.practice_main_view'))
		if ('Office_Manager' in request.session['MHL_Users']):
			return HttpResponseRedirect(reverse('MHLogin.MHLPractices.views.practice_main_view'))
		if ('OfficeStaff' in request.session['MHL_Users']):
			return HttpResponseRedirect(reverse('MHLogin.MHLPractices.views.practice_main_view'))
		if ('Dietician' in request.session['MHL_Users']):
			return main_physician(request, request.session['MHL_Users']['Dietician'])
		if ('Administrator' in request.session['MHL_Users']):
			return HttpResponseRedirect(reverse('MHLogin.Administration.views.home'))
		if ('Salesperson' in request.session['MHL_Users']):
			return HttpResponseRedirect(reverse('MHLogin.MHLUsers.Sales.views.dashboard'))
		if ('Broker' in request.session['MHL_Users']):
			return main_broker(request, request.session['MHL_Users']['Broker'])
		# error!
		raise Exception("User seems to be of unknown type.")
	else:  # user isn't authenticated
		if (settings.LOGIN_REDIRECT):
			return HttpResponseRedirect(settings.LOGIN_REDIRECT)
		# display login
		return login_user(request)


def main_physician(request, doctor):
	"""Displays the physician's home page."""
	return main_provider(request, doctor, 'physician')


def main_nurse(request, nurse):
	"""Displays the nurse's home page."""
	context = get_context(request)
	context['user_type'] = "nurse"

	context['site_providers'] = get_all_site_providers(nurse.user.current_site)
	context['site_clinical_clerks'] = get_all_site_clinical_clerks(nurse.user.current_site)
	context['community_physicians'] = get_community_professionals(nurse.user.current_practice)

	return render_to_response('home_nurse.html', context)


def main_np_pa(request, np_pa):
	"""Displays the np_pa's home page."""
	return main_provider(request, np_pa, 'np_pa')


def main_provider(request, user, user_type):
	"""Displays the physician/np_pa's home page."""
	context = get_context(request)
	context['auto_refresh_time'] = settings.MSGLIST_AUTOREFRESH_TIME

	context['user_type'] = user_type
	current_provider = user.user

	providers = get_all_site_providers(current_provider.current_site)
	set_providers_result(providers, request)
	site_staffs = get_all_site_staff(current_provider.current_site)
	site_staffs = set_site_staff_result(site_staffs, current_provider)

	context['unread_msg_count'] = get_message_count(user.user, ('ANS', 'VM'), read_flag=False)

	community_physicians = get_community_providers(user)
	set_providers_result(community_physicians, request)
	context['community_physicians'] = community_physicians
	members = dict()
	local_practicesDict = dict()
	current_practice = current_provider.current_practice
	if (current_practice):
		practice_members = all_practice_members(current_practice, 
			strip_staff_mobile=False, strip_staff_pager=True)
		members['providers'] = set_practice_members_result(practice_members, request)
		practice_list = get_practices_by_position(current_practice.practice_lat, 
			current_practice.practice_longit).only('practice_name', 'id')
		local_practicesDict['providers'] = set_practices_result(practice_list, request)
	else:
		members['providers'] = []
		local_practicesDict['providers'] = []

	context['mdcom_fwd'] = current_provider.get_forward_voicemail_display()
	context['anssvc_fwd'] = current_provider.get_forward_anssvc_display()

	context['mobile_phone'] = phone_formater(current_provider.mobile_phone)
	context['office_phone'] = phone_formater(current_provider.office_phone)
	context['other_phone'] = phone_formater(current_provider.phone)
	context['mdcom_phone'] = phone_formater(current_provider.mdcom_phone, display_provisionLink=True)
	context['zip'] = current_provider.zip

	#does this provider have pending incoming request to join practices,
	pend_assoc = Pending_Association.objects.filter(to_user=request.user)
	assoc_lst = [{'practice_location':e.practice_location, 'from_user':e.from_user} 
				for e in pend_assoc]

	pend_list = []
	for e in assoc_lst:
		p = {}
		p['user'] = e['from_user'].first_name + ' ' + e['from_user'].last_name
		p['practice_name'] = e['practice_location'].practice_name
		p['type'] = ''
		p['practice_addr'] = e['practice_location'].practice_address1 + '' + \
			e['practice_location'].practice_address2
		p['practice_zip'] = e['practice_location'].practice_zip

		pend_list.append(p)
	context['accept_invites_count'] = pend_list

	#add by xlin in 20120207
	providersDict = dict()
	community = dict()
	siteStaffDict = dict()
	providersDict['providers'] = providers
	community['providers'] = community_physicians
	siteStaffDict['users'] = site_staffs

	providersDict['userType'] = 0

	#add org tab 20120820
	mhluser = request.session['MHL_Users']['MHLUser']
	orgs = getOrganizationsOfUser(mhluser, current_practice=current_practice)
	providersDict['org'] = orgs
	context['orgOroviders'] = renderOrganizationForDashbord(orgs, request)

	providersDict["current_organization_type"] = get_org_type_name(current_practice, none_text="")
	context['tabUI'] = render_to_string('tabUI.html', providersDict)
	context['providers'] = render_to_string('userInfo.html', providersDict)
	context['site_staff'] = render_to_string('userInfo4.html', siteStaffDict)

	context['community_physicians'] = render_to_string('userInfo.html', community)
	context['practice_members'] = render_to_string('userInfo3.html', members)
	context['local_practices'] = render_to_string('userInfo2.html', local_practicesDict)
	context['my_favorite'] = get_my_favorite(mhluser, html=True)

	return render_to_response('dashboard_provider.html', context)


def main_broker(request, user):
	"""Displays the broker's home page."""
	context = get_context(request)
	context['auto_refresh_time'] = settings.MSGLIST_AUTOREFRESH_TIME

	context['user_type'] = 300

	context['unread_msg_count'] = get_message_count(user.user, ('ANS', 'VM'), read_flag=False)

	community_physicians = get_community_providers_by_coords(user.user.lat, user.user.longit)
	set_providers_result(community_physicians, request)
	context['community_physicians'] = community_physicians

	context['mdcom_fwd'] = user.get_forward_voicemail_display()
	context['anssvc_fwd'] = user.get_forward_anssvc_display()

	context['mobile_phone'] = phone_formater(user.user.mobile_phone)
	context['office_phone'] = phone_formater(user.office_phone)
	context['other_phone'] = phone_formater(user.user.phone)
	context['mdcom_phone'] = phone_formater(user.mdcom_phone, display_provisionLink=True)
	context['zip'] = user.user.zip

	pend_assoc = Pending_Association.objects.filter(to_user=request.user).count()
	context['accept_invites_count'] = pend_assoc

	context['providers'] = community_physicians
	mhluser = request.session['MHL_Users']['MHLUser']
	context['favorites'] = get_my_favorite(mhluser, can_send_refer=False)
	context['licensure_list'] = [('ALL', _('ALL'))] + list(STATE_CHOICES)
	return render_to_response('dashboard_broker.html', context)


def terms_acceptance(request):

	if (request.POST):
		accept_form = ToSAcceptForm(request.POST)
		reject_form = ToSRejectForm(request.POST)
		if (accept_form.is_valid()):
			if (accept_form.cleaned_data['accept']):
				# set the user's ToS to be true.
				mhluser = MHLUser.objects.get(id=request.user.id)
				mhluser.tos_accepted = True
				mhluser.save()
			else:
				LogoutEvent().customInit(user=request.user)
				logout(request)
		elif (reject_form.is_valid()):
			if (reject_form.cleaned_data['reject']):
				LogoutEvent().customInit(user=request.user)
				logout(request)
		return HttpResponseRedirect('/')
	return terms(request, show_accept=True)


def terms(request, show_accept=False):
	context = get_context(request)
	context['show_accept'] = show_accept
	if (show_accept):
		context['accept_form'] = ToSAcceptForm()
		context['reject_form'] = ToSRejectForm()

	return render_to_response('terms.html', context)


def eula(request):
	context = get_context(request)
	return render_to_response('eula.html', context)


def privacy(request):
	context = get_context(request)
	return render_to_response('privacy.html', context)


def learn_more(request):
	context = get_context(request)
	return render_to_response('learn_more.html', context)


def login_user(request):
	context = RequestContext(request)
	context['error_msg'] = None

	if (request.method == 'POST'):
		form = LoginForm(request.POST)
		if request.user.is_authenticated():
			logout(request)

		context['form'] = form
		if (form.is_valid()):
			user = authenticate(username=form.cleaned_data['username'], 
				password=form.cleaned_data['password'])
			if (user):
				if(user_is_active(user)):
					LoginEvent().customInit(username=form.cleaned_data['username'], \
							remote_ip=request.META['REMOTE_ADDR'], success=True, \
							user=user)
					login(request, user)
					request.session['password_change_time'] = MHLUser.objects.filter(
						pk=request.user.pk).only("password_change_time").get().password_change_time
					if ('next' in form.cleaned_data and form.cleaned_data['next']):
						response = HttpResponseRedirect(form.cleaned_data['next'])

					else:
						response = HttpResponseRedirect('/')

					store_user_key(request, response, form.cleaned_data['password'])
					# TESTING_KMS_INTEGRATION check if user is g'fathered
					uprivs = UserPrivateKey.objects.filter(user=user,
							credtype=CRED_WEBAPP, gfather=True)
					if uprivs.exists():
						recrypt_keys(uprivs, settings.SECRET_KEY, form.cleaned_data['password'])
					return response
				else:
					LoginEvent().customInit(username=form.cleaned_data['username'], \
								remote_ip=request.META['REMOTE_ADDR'], success=False, \
								user=user)
					# Return a 'disabled account' error message
					context['error_msg'] = _("Account appears to be disabled")
			else:
				# User couldn't be found.
				context['error_msg'] = _("Invalid username or password")
		else:
			# Form was invalid. This shouldn't be possible.
			context['error_msg'] = _("Invalid username or password")

		# At this point, the login attempt has failed.
		if (settings.LOGIN_FAILED_REDIRECT):
			return HttpResponseRedirect(settings.LOGIN_FAILED_REDIRECT)

	else:  # if (request.method != 'POST')
		if(request.user.is_authenticated()):
			return HttpResponseRedirect('/')
		next = ''
		if ('next' in request.GET):
			next = request.GET['next']
		context['form'] = LoginForm(initial={'next': next})

	if (settings.LOGIN_REDIRECT):
		return HttpResponseRedirect(settings.LOGIN_REDIRECT)

	context['STATIC_URL'] = ''.join([context['STATIC_URL'], 'temp/'])
	return render_to_response('temp/index.html', context)


def logout_user(request):
	if request.user.is_authenticated():
		LogoutEvent().customInit(user=request.user)
		logout(request)
	return HttpResponseRedirect('/')


def getSubTabs(templateDict, tab='Home'):
	templateDict['mhl_mainTabName'] = tab
	templateDict['mhl_subtabs'] = []

	templateDict['mhl_subtabs'].append(
			{
				'image_name': 'Home',
			})


def user_agent(request):
	ua = "No User Agent String in Request"
	if 'HTTP_USER_AGENT' in request.META:
		ua = request.META['HTTP_USER_AGENT']

	msg = _('%(user)s \nUser Agent String is: "%(ua)s"') % \
		{'user': repr(request.user), 'ua': ua}

	send_mail(_('User Agent'), msg, 'do-not-reply@myhealthincorporated.com',
		['rdutta@myhealthincorporated.com', ], fail_silently=False)

	return HttpResponse('Your User Agent String is: "%s"' % ua)


def toggle_mobile(request):
	if ('set_to_mobile' in request.session):
		request.session['set_to_mobile'] = not(request.session['set_to_mobile'])
	else:
		request.session['set_to_mobile'] = True
	return HttpResponseRedirect('/')


def faqs(request):
	context = get_context(request)
	if ('Provider' in request.session['MHL_Users']):
		resp = render_to_response('faqs.html', context)
	elif ('OfficeStaff' in request.session['MHL_Users']):
		resp = render_to_response('faqs2.html', context)
	else:  # default faq for Sales, etc. we may want a specific faq for each type?
		resp = render_to_response('faqs.html', context)

	return resp


def iphoneFAQs(request):
	context = get_context(request)
	return render_to_response('iphoneFAQs.html', context)


def androidFAQs(request):
	context = get_context(request)
	return render_to_response('androidFAQs.html', context)


#add by xlin 20120203
def videoTutorial(request):
	context = get_context(request)
	return render_to_response('videoTutorial.html', context)


def contact_ajax(request):
	if (request.method == "POST"):
		mDict = {}
		mDict['first_name'] = request.user.first_name
		mDict['last_name'] = request.user.last_name
		mDict['email'] = request.user.email
		mDict['sessionid'] = request.COOKIES['sessionid']
		subject = "Subscription request from %s" % request.user.username
		msg = render_to_string('Support/supportsubscriptionemailtemplate.html', mDict)
		send_mail(subject, msg, request.user.email, settings.SUPPORT_RECIPIENTS, fail_silently=False)
	return HttpResponse(json.dumps({'data': 'ok'}))


def contact_confirm(request):
	context = get_context(request)
	return render_to_response('Support/supportemailsentconfirmation.html', context)


def contact(request):
	context = get_context(request)
	if (request.POST):
		mDict = {}
		mDict['first_name'] = request.user.first_name
		mDict['last_name'] = request.user.last_name
		mDict['email'] = request.user.email
		mDict['message'] = request.POST['message']
		mDict['call_back_number'] = request.POST['call_back_number']
		mDict['sessionid'] = request.COOKIES['sessionid']
		mDict['meta'] = request.META
		mDict['meta'].pop('HTTP_COOKIE')
		subject = "Support request from %s" % request.user.username
		msg = render_to_string('Support/supportemailtemplate.html', mDict)
		send_mail(subject, msg, request.user.email, settings.SUPPORT_RECIPIENTS, fail_silently=False)
		return render_to_response('Support/supportemailsentconfirmation.html', context)

	mhluser = request.session['MHL_Users']['MHLUser']
	context["call_back_number"] = mhluser.mobile_phone
	return render_to_response('Support/contact.html', context)
