
import json
from urlparse import urljoin
from httplib import SERVICE_UNAVAILABLE

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db import transaction
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.utils.translation import ugettext as _
from django.template.loader import render_to_string
from twilio import twiml as twilio, TwilioRestException
from twilio.rest.resources import make_twilio_request

import MHLogin.utils.errlib as errlib

from MHLogin.MHLUsers.models import NP_PA, OfficeStaff, MHLUser, Physician, Nurse, \
	Office_Manager
from MHLogin.MHLUsers.utils import user_is_physician, user_is_np_pa, user_is_provider, \
	getCurrentUserInfo, getCurrentUserMobile, set_practice_members_result, all_staff_members, \
	user_is_office_manager,get_fullname

from MHLogin.DoctorCom.forms import Provider, PageCallbackForm
from MHLogin.DoctorCom.models import Click2Call_Log, PagerLog
from MHLogin.DoctorCom.speech.utils import tts
from MHLogin.DoctorCom.view_boxes import box_recent_received, box_recent_sent
from MHLogin.MHLPractices.models import PracticeLocation

from MHLogin.utils.templates import phone_formater, get_context
from MHLogin.utils.decorators import TwilioAuthentication
from MHLogin.utils.mh_logging import get_standard_logger 
from MHLogin.utils import ImageHelper
from MHLogin.utils.admin_utils import mail_admins
from MHLogin.utils.twilio_utils import client, client2008
from MHLogin.MHLOrganization.utils import get_custom_logos, which_orgs_contain_this_user,\
	get_other_organizations
from MHLogin.utils.constants import RESERVED_ORGANIZATION_TYPE_ID_PRACTICE
from MHLogin.MHLFavorite.utils import is_favorite, OBJECT_TYPE_FLAG_MHLUSER,\
	OBJECT_TYPE_FLAG_ORG

from django.db.models.query import QuerySet
# Setting up logging
logger = get_standard_logger('%s/DoctorCom/views.log' % (settings.LOGGING_ROOT),
							'DoctorCom.views', settings.LOGGING_LEVEL)


def received_sent(request):
	"""Process received_sent view request:  

	:param request: The HTTP GET request
	:type request: django.core.handlers.wsgi.WSGIRequest  
	:returns: django.http.HttpResponse -- the result in an HttpResonse object 
	:raises: None 
	"""
	context = get_context(request)
	context['recent_received_box'] = box_recent_received(request)
	context['recent_sent_box'] = box_recent_sent(request)
	context['auto_refresh_time'] = settings.MSGLIST_AUTOREFRESH_TIME

	if ('Physician' in request.session['MHL_Users']):
		context['user_type'] = "doctor"
		#doctor = user_is_physician(request.user)
		doctor = Physician.objects.filter(user=request.user)
		mobile_number = phone_formater(doctor[0].user.mobile_phone)
		context['mobile_phone'] = mobile_number
	elif ('NP_PA' in request.session['MHL_Users']):
		context['user_type'] = "np_pa"
		np_pa = NP_PA.objects.filter(user=request.user)
		mobile_number = phone_formater(np_pa[0].user.mobile_phone)
		context['mobile_phone'] = mobile_number

	return render_to_response('received-sent-mobile.html', context)


def provider_info(request):
	"""Process provider_info view request:  

	:param request: The HTTP GET request
	:type request: django.core.handlers.wsgi.WSGIRequest  
	:returns: django.http.HttpResponse -- the result in an HttpResonse object 
	:raises: None 
	"""
	context = get_context(request)
	context['can_send_refer'] = True
	if ('Broker' in request.session['MHL_Users']):
		context['can_send_refer'] = False

	if (request.GET):
		if ('provider' in request.GET):
			provider_id = int(request.GET['provider'])

			user = None
			clinical_clerk = 0
			try:
				user = Physician.objects.get(user=provider_id)
			except Physician.DoesNotExist:
				pass
			if (user):
				phys = get_object_or_404(Physician, user=provider_id)
				clinical_clerk = phys.user.clinical_clerk
				context['user'] = phys.user

				context['specialty'] = ''
				context['accepting_new_patients'] = ''

				specialty = ''
				if (not clinical_clerk):
					specialty = str(phys.get_specialty_display())
				if (specialty):					
					context['specialty'] = specialty
			user = None
			try:
				user = Provider.objects.get(user=provider_id)
				context['photo'] = ImageHelper.get_image_by_type(user.photo,
									size='Middle', type='Provider')
			except:
				pass

			if (user):
				clinical_clerk = user.clinical_clerk
				setUserDetailToContext(request.session['MHL_Users']['MHLUser'], context, user)

	return render_to_response("MHLUsers/tab_provider_info.html", context)


def office_staff_info(request):
	"""Process office_staff_info view request:  

	:param request: The HTTP GET request
	:type request: django.core.handlers.wsgi.WSGIRequest  
	:returns: django.http.HttpResponse -- the result in an HttpResonse object 
	:raises: None 
	"""
	context = get_context(request)
	if ('Broker' in request.session['MHL_Users']):
		context['can_send_refer'] = False
	if (request.GET):
		if ('provider' in request.GET):
			provider_id = int(request.GET['provider'])

			user = None
			nurse = None
			try:
				user = OfficeStaff.objects.get(user=provider_id)
				context['photo'] = ImageHelper.get_image_by_type(
							user.user.photo, size='Middle', type='Staff')
				nurse = Nurse.objects.filter(user=user)
			except OfficeStaff.DoesNotExist:
				pass

			if nurse:
				context['photo'] = ImageHelper.get_image_by_type(
							user.user.photo, size='Middle', type='Nurse')

			if not user:
				user = Provider.objects.get(user=provider_id)
				context['photo'] = ImageHelper.get_image_by_type(
									user.photo, size='Middle', type='Provider')
			setUserDetailToContext(request.session['MHL_Users']['MHLUser'], context, user)
	return render_to_response("MHLUsers/tab_officeuser_info.html", context)

def setUserDetailToContext(current_user, context, user):
	""" Append common information to context. 

	:param current_user: current login user
	:type current_user: an instance of MHLUser
	:param context: The HTTP GET request
	:type dict: dictionary
	:param user: the user be shown
	:type user: an instance of Provider/OfficeStaff
	:returns: None 
	:raises: None 
	"""
	mhluser = user.user
	context['user'] = mhluser
	context['address1'] = mhluser.address1
	context['address2'] = mhluser.address2

	context['city'] = mhluser.city
	context['state'] = mhluser.state
	context['zip'] = mhluser.zip
	context['mhluser_id'] = mhluser.id
	context['is_favorite'] = is_favorite(current_user,\
						OBJECT_TYPE_FLAG_MHLUSER, mhluser.id)

	# Practice
	pracs = which_orgs_contain_this_user(mhluser.id, in_tab=None, 
		type_id=RESERVED_ORGANIZATION_TYPE_ID_PRACTICE)
	practices = [{
		'name':p.practice_name
	} for p in pracs]
	context['practices'] = practices

	# Hospital
	sites = user.sites.all()
	sites = [{
		'name': cs.name,
	}for cs in sites]
	context['sites'] = sites

	# Other Organization
	context['other_orgs'] = get_other_organizations(mhluser.id)

	context['skill'] = mhluser.skill
	context['custom_logos'] = get_custom_logos(mhluser.id, user.current_practice)

	context['fullname'] = get_fullname(mhluser)


#add by xlin for practice info 20120213
def practice_info(request):
	"""Process pratice_info view request:  

	:param request: The HTTP GET request
	:type request: django.core.handlers.wsgi.WSGIRequest  
	:returns: django.http.HttpResponse -- the result in an HttpResonse object 
	:raises: None 
	"""
	context = get_context(request)
	if (request.GET):
		if ('provider' in request.GET):
			location_id = int(request.GET['provider'])
			location = PracticeLocation.objects.get(id=location_id)
			context['location'] = location
			context['photo'] = ImageHelper.get_image_by_type(
				location.practice_photo, "Middle", 'Practice', 'img_size_practice')
			#update by xlin for improvement 1562 to add current site office staff list
			practice_membersDict = dict()
			practice_members = all_staff_members(location_id)
			#check user length is larger than 10
			if len(practice_members) > 10:
				practice_membersDict['scroll'] = True
			else:
				practice_membersDict['scroll'] = False
			practice_membersDict['providers'] = set_practice_members_result(practice_members, request)
			context['practice_members'] = render_to_string('allStaffs.html', practice_membersDict)
			context['is_favorite'] = context['is_favorite'] = is_favorite(\
					request.session['MHL_Users']['MHLUser'], \
					OBJECT_TYPE_FLAG_ORG, location_id)
	return render_to_response("MHLUsers/practice_info.html", context)


def provider_view(request):
	"""Process provider view request:  Determine is_mobile flag set and render
	different page for mobile users.

	:param request: The HTTP GET request
	:type request: django.core.handlers.wsgi.WSGIRequest  
	:returns: django.http.HttpResponse -- the result in an HttpResonse object 
	:raises: None 
	"""
	context = get_context(request)
	context['can_send_refer'] = True
	if ('Broker' in request.session['MHL_Users']):
		context['can_send_refer'] = False

	current_user = getCurrentUserInfo(request)
	current_user_mobile = getCurrentUserMobile(current_user)

	if (request.GET):
		if ('provider' in request.GET):
			provider_id = int(request.GET['provider'])
			provider = get_object_or_404(Provider, id=provider_id)
			mhluser_id = provider.user.id
			context['fullname']=get_fullname(provider)
			context['mhluser_id'] =  mhluser_id
			context['is_favorite'] = is_favorite(request.session['MHL_Users']['MHLUser'],\
						OBJECT_TYPE_FLAG_MHLUSER, mhluser_id)
			context['other_orgs'] = get_other_organizations(mhluser_id)
			context['refer_available'] = len(provider.practices.filter(
					organization_type__id = RESERVED_ORGANIZATION_TYPE_ID_PRACTICE))>0
			user = user_is_physician(provider_id)
			if (user):
				physicians = Physician.objects.filter(user=provider_id)[:1]
				phys = physicians[0] if physicians else None
				context['provider'] = phys
				if phys:
					context['user_current_site'] = phys.user.current_site
					context['user_current_practice'] = phys.user.current_practice

					states_of_licensure = phys.user.licensure_states.all()
					states_of_licensure = [i.state for i in states_of_licensure]	
					context['states_of_licensure'] = ', '.join(states_of_licensure)

					clinical_clerk = phys.user.clinical_clerk
					context['photo'] = ImageHelper.get_image_by_type(
										phys.user.photo, "Middle", 'Provider')
					context['specialty'] = ''
					if (not clinical_clerk):
						context['specialty'] = str(phys.get_specialty_display())

					if current_user_mobile and settings.CALL_ENABLE:
						context['call_available'] = bool(phys.user.user.mobile_phone)

					if settings.CALL_ENABLE:
						context['pager_available'] = bool(phys.user.pager)

			user = user_is_np_pa(provider_id)
			if (user):
				np_pas = NP_PA.objects.filter(user=provider_id)[:1]
				np_pa = np_pas[0] if np_pas else None
				context['provider'] = np_pa
				if np_pa:
					context['user_current_site'] = np_pa.user.current_site
					context['user_current_practice'] = np_pa.user.current_practice
					states_of_licensure = np_pa.user.licensure_states.all()
					states_of_licensure = [i.state for i in states_of_licensure]	
					context['states_of_licensure'] = ', '.join(states_of_licensure)
					context['photo'] = ImageHelper.get_image_by_type(
									np_pa.user.photo, "Middle", 'Provider')
					if current_user_mobile and settings.CALL_ENABLE:
						context['call_available'] = bool(np_pa.user.user.mobile_phone)

					if settings.CALL_ENABLE:
						context['pager_available'] = bool(np_pa.user.pager)

	return render_to_response("MHLUsers/provider_info.html", context)

def user_view(request):
	"""Process user view request:  Determine is_mobile flag set and render
	different page for mobile users.

	:param request: The HTTP GET request
	:type request: django.core.handlers.wsgi.WSGIRequest
	:returns: django.http.HttpResponse -- the result in an HttpResonse object
	:raises: None
	"""
	context = get_context(request)
#	context['can_send_refer'] = True
	if ('Broker' in request.session['MHL_Users']):
		context['can_send_refer'] = False

	current_user = getCurrentUserInfo(request)
	current_user_mobile = getCurrentUserMobile(current_user)

	if (request.GET):
		if ('user_id' in request.GET):
			user_id = int(request.GET['user_id'])
			try:
				role_user = Provider.objects.get(user__id=user_id)
				context['refer_displayable'] = True
				context['refer_available'] = len(role_user.practices.filter(
						organization_type__id = RESERVED_ORGANIZATION_TYPE_ID_PRACTICE))>0
				states_of_licensure = role_user.licensure_states.all()
				states_of_licensure = [i.state for i in states_of_licensure]
				context['states_of_licensure'] = ', '.join(states_of_licensure)

				context['photo'] = ImageHelper.get_image_by_type(
									role_user.photo, "Middle", 'Provider')

				physicians = list(Physician.objects.filter(user=role_user))
				phys = physicians[0] if physicians else None
				if phys:
					clinical_clerk = role_user.clinical_clerk
					context['specialty'] = ''
					if (not clinical_clerk):
						context['specialty'] = str(phys.get_specialty_display())

			except Provider.DoesNotExist:
				try:
					role_user=OfficeStaff.objects.get(user__id=user_id)
					context['refer_displayable'] = False
					if Nurse.objects.filter(user__id=role_user.id).exists():
						context['photo'] = ImageHelper.get_image_by_type(
									role_user.user.photo, "Middle", 'Nurse')
					else:
						context['photo'] = ImageHelper.get_image_by_type(
									role_user.user.photo, "Middle", 'Staff')

					context['staff_type']=_("Office Staff")
					if Office_Manager.objects.filter(user__id=role_user.id).exists():
						context['staff_type']="Office Manager"
				except OfficeStaff.DoesNotExist:
					raise Http404('No provider or staff matches the given query.')

			context['mhluser_id'] =  user_id
			context['mhluser'] =  role_user.user
			context['fullname'] =  get_fullname(role_user.user)
			context['is_favorite'] = is_favorite(request.session['MHL_Users']['MHLUser'],\
						OBJECT_TYPE_FLAG_MHLUSER, user_id)
			context['other_orgs'] = get_other_organizations(user_id)

			context['user_current_site'] = role_user.current_site
			context['sites'] = role_user.sites.all()
			context['practices'] = role_user.practices.all()
			context['user_current_practice'] = role_user.current_practice
			context['practices'] = role_user.practices.all()

			if current_user_mobile and settings.CALL_ENABLE:
				context['call_available'] = bool(role_user.user.mobile_phone)

			if settings.CALL_ENABLE:
				context['pager_available'] = bool(role_user.pager)

	return render_to_response("MHLUsers/user_detail_info.html", context)


def provider_search(request):
	"""Process provider_search view request:  

	:param request: The HTTP GET request
	:type request: django.core.handlers.wsgi.WSGIRequest  
	:returns: django.http.HttpResponse -- the result in an HttpResonse object 
	:raises: None 
	"""
	context = get_context(request)
	context['auto_refresh_time'] = settings.MSGLIST_AUTOREFRESH_TIME
	if (context['is_blackberry']):
			return render_to_response('MHLUsers/provider_search-mobile-bb.html', context)
	return render_to_response("MHLUsers/provider_search-mobile.html", context)


#########################################################################################
# TODO: move code below: click2call, xfer, paging, response, verify, etc. to own module #
#########################################################################################

def _getOrCreateClick2Call_Log(caller, caller_number, called_user, called_number, source, csite, callid):
	"""
	get existing Click2Call_Log based on callid or create it
	"""
	logger.debug('_getOrCreateClick2Call_Log is called with Caller %s number %s, Called %s '
		'number %s source %s SID %s' % (caller, caller_number, called_user, 
			called_number, source, callid))
	c2clog_qs = Click2Call_Log.objects.filter(callid=callid)
	if (c2clog_qs.exists()):
		c2clog = c2clog_qs.get()
		# we update everything
		logger.debug('_getOrCreateClick2Call_log exists with caller %s number %s called %s number %s' % (
			c2clog.caller, c2clog.caller_number, c2clog.called_user, c2clog.called_number))
		with transaction.commit_manually():
			try:
				c2clog.caller = caller
				c2clog.caller_number = caller_number
				c2clog.called_user = called_user
				c2clog.called_number = called_number
				c2clog.source = source
				c2clog.current_site = csite
				c2clog.save()
				transaction.commit()
			except:
				transaction.rollback()
				raise
	else:
		with transaction.commit_manually():
			try:
				c2clog = Click2Call_Log.objects.create(caller=caller, 
						caller_number=caller_number, called_user=called_user,
					called_number=called_number, source=source, current_site=csite,
					callid=callid)  # call.sid
				c2clog.save()
				transaction.commit()
			except:
				transaction.rollback()
				raise
	return c2clog


def click2call_initiate(request, *args, **kwargs):
	"""
	Initiate click2call - depending on state of callee start new call
	or transfer call in progress.
	Uses logged in provider's mdcom_phone to decide if we do click2call or click2xfer.
	Ok, this is ugly -- some of the parameters from twilio have changed
	- phone numbers have +country code in front so we have to convert to search for the number
	in our db.
	- call['Caller'] is changed to call['from'] in 2010 twilio
	- Sid -> sid, etc
	"""
	from MHLogin.DoctorCom.IVR.utils import get_active_call, _makeUSNumber, \
		TYPE_CALLED, TYPE_CALLER
	logger.debug('%s: click2call_initiate POST %s' % 
		(request.session.session_key, str(request.POST)))

	resp = None
	if 'Provider' in request.session['MHL_Users']:
		prov = request.session['MHL_Users']['Provider']
		mhphone = prov.mdcom_phone
		mbphone = prov.mobile_phone
		logger.debug('%s: click2call_initiate mdcomphone %s mobilephone %s' % 
			(request.session.session_key, mhphone, mbphone))
		call = get_active_call(mhphone, ctype=TYPE_CALLER)
		if call:
			# Twilio 2008 can't redirect 2nd leg calls, only xfer inbound currently:
			# http://www.twilio.com/docs/api/2010-04-01/changelog#second-leg-call-sid
			resp = errlib.err5xx(request, SERVICE_UNAVAILABLE, _("There is an "
				"active call from your DoctorCom number to %s, please finish "
				"before proceeding." % call['Called']))
		else:
			call = get_active_call(mhphone, ctype=TYPE_CALLED)
			if call:
				if ((settings.TWILIO_PHASE == 2) and call['from'] == _makeUSNumber(prov.mobile_phone)) or \
					((settings.TWILIO_PHASE < 2) and call['Caller'] == prov.mobile_phone):
					resp = errlib.err5xx(request, SERVICE_UNAVAILABLE, _("There is "
						"an active call from your mobile phone to your DoctorCom "
						"number, please finish before proceeding."))
				else:
					# check if there are any calls to the mobile phone currently 
					# active (that is to be transferred)
					if not request.user.has_perm('MHLUsers.can_call_transfer'):
						resp = errlib.err5xx(request, SERVICE_UNAVAILABLE, _("To "
							"transfer incoming calls you must have can_call_transfer "
							"permission enabled, please contact your support admin."))
					else:
						resp = click2call_xfer(request, mhphone, call, *args, **kwargs)
			else:
				# checking active calls to mobile
				call = get_active_call(mbphone, ctype=TYPE_CALLED)
				if call:
#					import pdb; pdb.set_trace()
					# must have parent_call_sid which will be the call we will transfer
					if not request.user.has_perm('MHLUsers.can_call_transfer'):
						resp = errlib.err5xx(request, SERVICE_UNAVAILABLE, _("To "
							"transfer incoming calls you must have can_call_transfer "
							"permission enabled, please contact your support admin."))
					else:
						logger.debug('%s: click2call_initiate transfer as click2call_response call '
							'%s mdphone %s cell %s' % (request.session.session_key, 
								call, mhphone, mbphone))
						# we don't forward, we end the current call and reconnect
						resp = click2call_origin_xfer(request, mhphone, call, *args, **kwargs)
	return resp or click2call_call(request, *args, **kwargs)


def click2call_origin_xfer(request, mhphone, call, *args, **kwargs):
	"""
	doing a call transfer to preferred number (not mdcom number) from original click2call number
	Connects:  caller --> called (request.user) --> xfer --> click2call recip
	Note: we have 2 call SIDs to modify because we have to reconnect the original 
	'parent_call_sid' but use the current data
	without overwriting existing click2call_log record since callSID is unique
	"""
	from MHLogin.DoctorCom.IVR.utils import get_preferred_prov_number, _makeUSNumber
	# http://www.twilio.com/docs/api/2008-08-01/rest/change-call-state
	if (settings.TWILIO_PHASE == 2):
		# get the originating call sid
		psid = call['parent_call_sid']
		sid = call['sid']
		logger.debug('%s: click2call_origin_xfer POST %s call sid %s psid %s' % 
			(request.session.session_key, str(request.POST), sid, psid))
		c2clog_qs = Click2Call_Log.objects.filter(callid=psid)
		if (c2clog_qs.exists()):
			plog = c2clog_qs.get()
		else:
			# no parent sid log exist
			plog = None
	else:
		return errlib.err5xx(request, SERVICE_UNAVAILABLE, _("Transfer of "
			"click2call calls is not supported in this version."))
	called, called_number = None, None
	if 'called_id' in kwargs:
		called = get_object_or_404(MHLUser, id=kwargs['called_id'])
		called_number = get_preferred_prov_number(user_is_provider(called)) \
			if user_is_provider(called) else called.mobile_phone
	elif 'called_number' in request.GET:
		called_number = request.GET['called_number']
	elif 'called_practice' in request.GET:  # called_practice appears to be provider in:
		# userInfo2.html --> <a href="/Call/Practice/?called_practice={{ provider.id }}">
		called = get_object_or_404(Provider, id=request.GET['called_practice']).user
		called_number = get_preferred_prov_number(called)
	# setting up data for the twilio call - mhphone is actually wrong here; but we use the number in click2call_log
	auth, uri = client.auth, client.account_uri
	abs_uri = '://'.join([settings.SERVER_PROTOCOL, settings.SERVER_ADDRESS])
	url = reverse('MHLogin.DoctorCom.views.click2xfer_origin_response')
	d = {
		'From': _makeUSNumber(mhphone),
		'To': _makeUSNumber(called_number),
		'CurrentUrl': urljoin(abs_uri, url),
		'Method': 'POST',
		'Timeout': str(120),
	}
	logger.debug('%s: click2call_origin_xfer new from %s to %s url %s' % (
		request.session.session_key, mhphone, called_number, url))
	context = get_context(request)
	context['click2call_xfer'] = True
	try:
		# moved up per issue/2076
		caller = get_object_or_404(MHLUser, id=request.user.id)
		# we save the click2call log based on current; but actually modifying the psid
		if plog:
			# flip the log entries so we know who to forward the call to
			clog = _getOrCreateClick2Call_Log(caller=plog.caller, caller_number=plog.caller_number, 
				called_user=plog.called_user, called_number=plog.called_number, 
					source=plog.source, csite=plog.current_site, callid=sid)
			# olog is actually the original plog - updated here with the right caller/called
			olog = _getOrCreateClick2Call_Log(caller=plog.caller, caller_number=plog.caller_number, 
				called_user=called, called_number=called_number, source='WEB', csite=None, callid=psid)
			logger.debug('%s: click2call_origin_xfer setting caller %s called %s' % (
				request.session.session_key, mhphone, called_number))
		else:
			clog = _getOrCreateClick2Call_Log(caller=caller, caller_number=mhphone, called_user=called,
				called_number=called_number, source='WEB', csite=None, callid=sid)

		resp = make_twilio_request('POST', uri + '/Calls/' + psid, auth=auth, data=d)
		content = json.loads(resp.content)
		logger.debug('%s: click2call_origin_xfer sid %s content %s' % (
			request.session.session_key, psid, content))
		# terminate the log call
		d2 = {'Status': 'completed'}
		resp2 = make_twilio_request('POST', uri + '/Calls/' + sid, auth=auth, data=d2)
		content2 = json.loads(resp2.content)
		logger.debug('%s: click2call_origin_xfer sid %s content %s' % (
			request.session.session_key, sid, content2))
		context['called'] = called_number
		context['called_person'] = called or called_number
	except TwilioRestException as re:
		logger.critical('Unable to transfer call: %s' % re.msg)
		context['called'] = '<unable to transfer call>'
		context['called_person'] = '<N/A>'
		context['err_msg'] = 'Unable to transfer call'

	return render_to_response("DoctorCom/call_in_progress.html", context)


@TwilioAuthentication()
def click2xfer_origin_response(request):
	"""
	Process click2xfer_origin_response view request:
	Similar to click2xfer_response except different caller and called based on 2 call sids
	We set who to dial here based on Click2Call_Log
	"""
#	import pdb; pdb.set_trace()
	from MHLogin.DoctorCom.IVR.utils import _getUSNumber
	logger.debug('%s: click2xfer_origin_response POST %s' % 
		(request.session.session_key, str(request.POST)))
	r = twilio.Response()
	try:
		if (settings.TWILIO_PHASE == 2):
			# who twilio POST['called'] was original caller before call xfer
			logger.debug('click2xfer_origin_response callsid %s from %s to %s' % (
				request.POST['CallSid'], request.POST['From'], request.POST['To']))
			log = Click2Call_Log.objects.get(callid=request.POST['CallSid'])
		else:
			log = Click2Call_Log.objects.get(callid=request.POST['CallSid'])
		r.append(twilio.Pause(length=1))
		r.append(tts(_("Transferring your call, one moment please.")))
		abs_uri = '://'.join([settings.SERVER_PROTOCOL, settings.SERVER_ADDRESS])
		url = reverse('MHLogin.DoctorCom.views.click2call_cleanup')
		logger.debug('%s: click2xfer_origin_response found log caller %s to %s url %s' % (
			request.session.session_key, log.caller_number, log.called_number, url))
		r.append(twilio.Dial(log.called_number, action=urljoin(abs_uri, url),
			callerId=log.caller_number, timeout=120))
	except ObjectDoesNotExist:
		r.append(tts(_("Unable to transfer, please call back.")))

	return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)


def click2call_xfer(request, mhphone, call, *args, **kwargs):
	"""
	doing a call transfer directly to preferred number (not mdcom number)
	Connects:  caller --> called (request.user) --> xfer --> click2call recip
	"""
	from MHLogin.DoctorCom.IVR.utils import get_preferred_prov_number, _makeUSNumber
	# http://www.twilio.com/docs/api/2008-08-01/rest/change-call-state
	logger.debug('%s: click2call_xfer POST %s' % 
		(request.session.session_key, str(request.POST)))
	if (settings.TWILIO_PHASE == 2):
		sid = call['sid']
	else:
		sid = call['Sid']
	called, called_number = None, None
	caller = get_object_or_404(MHLUser, id=request.user.id)
	if 'called_id' in kwargs:
		called = get_object_or_404(MHLUser, id=kwargs['called_id'])
		called_number = get_preferred_prov_number(user_is_provider(called)) \
			if user_is_provider(called) else called.mobile_phone
	elif 'called_number' in request.GET:
		called_number = request.GET['called_number']
	elif 'called_practice' in request.GET:  # called_practice appears to be provider in:
		# userInfo2.html --> <a href="/Call/Practice/?called_practice={{ provider.id }}">
		called = get_object_or_404(Provider, id=request.GET['called_practice']).user
		called_number = get_preferred_prov_number(called)

	if (settings.TWILIO_PHASE == 2):
		auth, uri = client.auth, client.account_uri
		abs_uri = '://'.join([settings.SERVER_PROTOCOL, settings.SERVER_ADDRESS])
		url = reverse('MHLogin.DoctorCom.views.click2xfer_response')
		logger.debug('%s: click2call_xfer new from %s to %s url %s' % (
			request.session.session_key, mhphone, called_number, url))
		d = {
			'From': _makeUSNumber(mhphone),
			'To': _makeUSNumber(called_number),
			'CurrentUrl': urljoin(abs_uri, url),
			'Method': 'POST',
			'Timeout': str(120),
		}
	else:
		auth, uri = client2008.auth, client2008.account_uri
		abs_uri = '://'.join([settings.SERVER_PROTOCOL, settings.SERVER_ADDRESS])
		url = reverse('MHLogin.DoctorCom.views.click2xfer_response')
		logger.debug('%s: click2call_xfer from %s to %s url %s' % (
			request.session.session_key, mhphone, called_number, url))
		d = {
			'Caller': mhphone,
			'Called': called_number,
			'CurrentUrl': urljoin(abs_uri, url),
			'Method': 'POST',
			'Timeout': str(120),
		}
	context = get_context(request)
	context['click2call_xfer'] = True
	try:
		_getOrCreateClick2Call_Log(caller=caller, caller_number=mhphone, called_user=called, 
			called_number=called_number, source='WEB', csite=None, callid=sid)
		resp = make_twilio_request('POST', uri + '/Calls/' + sid, auth=auth, data=d)
#		import pdb; pdb.set_trace()
		content = json.loads(resp.content)
		if (settings.TWILIO_PHASE == 2):
			callId = content['sid']
		else:
			callId = content['TwilioResponse']['Call']['Sid']
		if sid != callId:
			msg = "sid mismatch: %s, from twilio: %s\n\n\n%s" % (sid, callId, repr(request))
			mail_admins("Call xfer sid mismatch", msg)
		context['called'] = called_number
		context['called_person'] = called or called_number
	except TwilioRestException as re:
		logger.critical('Unable to transfer call: %s' % re.msg)
		context['called'] = '<unable to transfer call>'
		context['called_person'] = '<N/A>'
		context['err_msg'] = 'Unable to transfer call'

	return render_to_response("DoctorCom/call_in_progress.html", context)


@TwilioAuthentication()
def click2xfer_response(request):
	"""Process click2xfer_response view request:

	:param request: The HTTP GET request
	:type request: django.core.handlers.wsgi.WSGIRequest
	:returns: django.http.HttpResponse -- the result in an HttpResonse object
	:raises: None
	"""
#	import pdb; pdb.set_trace()
	from MHLogin.DoctorCom.IVR.utils import _getUSNumber
	logger.debug('%s: click2xfer_response POST %s' % 
		(request.session.session_key, str(request.POST)))
	r = twilio.Response()
	try:
		# who twilio POST['called'] was original caller before call xfer
		if (settings.TWILIO_PHASE == 2):
			# who twilio POST['called'] was original caller before call xfer
			callernum = _getUSNumber(request.POST['To'])
			logger.debug('click2xfer_response callsid %s caller %s' % (request.POST['CallSid'], callernum))
			log = Click2Call_Log.objects.get(callid=request.POST['CallSid'],
				caller_number=callernum)
		else:
			log = Click2Call_Log.objects.get(callid=request.POST['CallSid'],
				caller_number=_getUSNumber(request.POST['Called']))
		r.append(twilio.Pause(length=1))
		r.append(tts(_("Transferring your call, one moment please.")))
		abs_uri = '://'.join([settings.SERVER_PROTOCOL, settings.SERVER_ADDRESS])
		url = reverse('MHLogin.DoctorCom.views.click2call_cleanup')
		logger.debug('%s: click2xfer_response found log caller %s to %s url %s' % (
			request.session.session_key, log.caller_number, log.called_number, url))
		r.append(twilio.Dial(log.called_number, action=urljoin(abs_uri, url),
			callerId=log.caller_number, timeout=120))
	except ObjectDoesNotExist as odne:
		post_sid, post_called = request.POST['CallSid'], request.POST['Called']
		msg = "query fail, sid: %s, post_called: %s, exception: %s" % \
			(post_sid, post_called, str(odne))
		mail_admins("Unable to transfer", "%s\n\n%s" % (msg, repr(request)))
		r.append(tts(_("Unable to transfer, please call back.")))

	return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)


def click2call_call(request, *args, **kwargs):
	"""
	Process click2call_initiate view request:
	1. we call the user logged in at his preferred number to verify it is not a machine doing Click2Call
	2. user has to type in 1 -> response is processed by click2call_caller_verify
	3. we connect the call in click2call_response; called has to accept call
	4. call is connected

	:param request: The HTTP GET request
	:type request: django.core.handlers.wsgi.WSGIRequest  
	:returns: django.http.HttpResponse -- the result in an HttpResonse object 
	:raises: None 
	"""
	from MHLogin.DoctorCom.IVR.utils import _makeUSNumber
	if not settings.CALL_ENABLE:
		return errlib.err403(request)

	# figure out caller, called and if caller can call
	caller = request.session['MHL_Users']['MHLUser']
	caller_mgr = request.session['MHL_Users']['Office_Manager'] \
		if 'Office_Manager' in request.session['MHL_Users'] else None
	caller_provider = request.session['MHL_Users']['Provider'] \
		if 'Provider' in request.session['MHL_Users'] else None
	called, called_number, current_site = None, None, None

	if 'called_id' in kwargs:
		called = get_object_or_404(MHLUser, id=kwargs['called_id'])
		called_number = called.mobile_phone
	elif 'called_number' in request.GET:
		called_number = request.GET['called_number']
	elif 'called_practice' in request.GET:
		called_practice = get_object_or_404(PracticeLocation, id=request.GET['called_practice'])
		called_number = called_practice.practice_phone
		if called_practice.backline_phone:
			called_number = called_practice.backline_phone
	logger.debug('%s: click2call_call from %s mgr %s prov %s called %s' % (
		request.session.session_key, caller, caller_mgr, caller_provider, called_number))

	if not caller.mobile_phone and not caller_mgr:
		return errlib.err500(request, err_msg=_("You do not have a mobile phone number "
					"in your profile. Please enter one to use this function."))
	# Make this more sophisticated. If called party is a Provider then let it go.
	if called and not user_is_provider(called) and not called.mobile_phone:
		return errlib.err500(request, err_msg=_("The person you are "
			"trying to call doesn't have a phone number listed."))

	# TODO: When confirmation gets figured out, generate an appropriate error message here.
	if caller_mgr and not caller_provider:
		try:
			staff = OfficeStaff.objects.get(user=caller)
		except ObjectDoesNotExist:  # but error if MultipleObjectsReturned 
			return errlib.err500(request, err_msg=_("You do not have a mobile phone "
				"number in your profile. Please enter one to use this function."))
		if staff.caller_anssvc == 'MO':
			caller_phone = staff.user.mobile_phone
		elif staff.caller_anssvc == 'OF':
			caller_phone = staff.office_phone
		elif staff.caller_anssvc == 'OT':
			caller_phone = staff.user.phone
		else:
			return errlib.err500(request, err_msg=_("You do not have a mobile phone "
				"number in your profile. Please enter one to use this function."))
		current_site = staff.current_site
	else:
		caller_phone = caller.mobile_phone
		current_site = caller_provider.current_site if caller_provider else None

# we want to hide provider's mdcom number from external when possible
#	if caller_provider:
#		mdfrom = caller_provider.mdcom_phone
#	else:
#		should be practice's mdcom number if caller_mgr
	mdfrom = settings.TWILIO_CALLER_ID

	if (settings.TWILIO_PHASE == 2):
		auth, uri = client.auth, client.account_uri
		abs_uri = '://'.join([settings.SERVER_PROTOCOL, settings.SERVER_ADDRESS])
		url = reverse('MHLogin.DoctorCom.views.click2call_caller_verify')
		statusurl = reverse('MHLogin.DoctorCom.IVR.views_provider_v2.ProviderIVR_Status')
		logger.debug('%s: click2call_call new from %s to %s url %s staturl %s' % (
			request.session.session_key, settings.TWILIO_CALLER_ID, caller_phone, url, statusurl))
		d = {
			'From': _makeUSNumber(mdfrom),
			'To': _makeUSNumber(caller_phone),
			'Url': urljoin(abs_uri, url),
			'Method': 'POST',
			'StatusCallback': urljoin(abs_uri, statusurl),
			'Timeout': str(120),
		}
	else:
		auth, uri = client2008.auth, client2008.account_uri
		abs_uri = '://'.join([settings.SERVER_PROTOCOL, settings.SERVER_ADDRESS])
		url = reverse('MHLogin.DoctorCom.views.click2call_caller_verify')
		logger.debug('%s: click2call_call from %s to %s url %s' % (
			request.session.session_key, settings.TWILIO_CALLER_ID, caller_phone, url))
		d = {
			'Caller': mdfrom,
			'Called': caller_phone,
			'Url': urljoin(abs_uri, url),
			'Method': 'POST',
			'Timeout': str(120),
		}
	context = get_context(request)
	try:
		resp = make_twilio_request('POST', uri + '/Calls', auth=auth, data=d)
		content = json.loads(resp.content)
		if (settings.TWILIO_PHASE == 2):
			callId = content['sid']
		else:
			callId = content['TwilioResponse']['Call']['Sid']
		_getOrCreateClick2Call_Log(caller=caller, caller_number=settings.TWILIO_CALLER_ID, called_user=called, 
			called_number=called_number, source='WEB', csite=current_site, callid=callId)
		if called:
			context['called'] = '%s %s' % (called.first_name, called.last_name)
		elif (called_number[0] == '1'):
			context['called'] = '(%s) %s-%s' % (called_number[1:4],
						called_number[4:7], called_number[7:11])
		else:
			context['called'] = '(%s) %s-%s' % (called_number[0:3],
						called_number[3:6], called_number[6:10])
	except TwilioRestException as re:
		context['called'] = '<unable to make call>'
		context['err_msg'] = re.msg

	return render_to_response("DoctorCom/call_in_progress.html", context)


@TwilioAuthentication()
def click2call_caller_verify(request):
	"""Process click2call_caller_verify view request:  

	:param request: The HTTP GET request
	:type request: django.core.handlers.wsgi.WSGIRequest  
	:returns: django.http.HttpResponse -- the result in an HttpResonse object 
	:raises: None 
	"""
	# Save debugging data
	logger.debug('%s: click2call_caller_verify POST %s' % 
		(request.session.session_key, str(request.POST)))
	sid = request.POST['CallSid']
	status = request.POST['CallStatus']
	log = Click2Call_Log.objects.get(callid=sid)
	log.save()

	# We don't care about which session this is associated with as all
	# verification is the same across all sessions.
	r = twilio.Response()
	if (status != 'completed'):
		abs_uri = '://'.join([settings.SERVER_PROTOCOL, settings.SERVER_ADDRESS])
		url = reverse('MHLogin.DoctorCom.views.click2call_response')

		gather = twilio.Gather(action=urljoin(abs_uri, url), numDigits=1, finishOnKey='')
		gather.append(tts(_("Please press the one key to confirm "
			"you are not a machine."), voice=twilio.Say.MAN, language=twilio.Say.ENGLISH))
		r.append(gather)
		logger.debug('%s: click2call_caller_verify -- url %s' % (
			request.session.session_key, url))

	return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)


@TwilioAuthentication()
def click2call_response(request):
	""" Conditions under which is run:

	Callers:
		- Non-Providers
			* With a mobile phone defined  (show general DC number; set up in callerID setup)
				(required: without a mobile phone defined won't get this far)

		- Providers
			* With a mobile phone defined (required -- won't get this far without)
			* With a DoctorCom number (show user DC number; set up in callerID setup; 
				set up by ProviderIVR_OutsideInit)
			* Without a DoctorCom number (show general DC number; set up in callerID setup)
	Calleds:
		- Providers
			* With DoctorCom Number (forward through IVR)
			* Without DoctorCom Number
			* With Mobile Phone
			* Without mobile phone (Error condition?)
		- Non-Providers
			* as of 2/2011 we can make calles to office managers with cell phones on file
	"""
	# Todo: SID is currently unclean -- we need to sanitize it.
	logger.debug('%s: click2call_response POST %s' % 
		(request.session.session_key, str(request.POST)))
	sid = request.POST['CallSid']

	log = Click2Call_Log.objects.get(callid=sid)
	log.save()

	r = twilio.Response()
	r.append(tts(_("Connecting the other party."), voice=twilio.Say.MAN, language=twilio.Say.ENGLISH))

	# Find the called party's desired number
	called_number = None

	# Set up caller ID
	caller_id = settings.TWILIO_CALLER_ID
	caller_provider = user_is_provider(log.caller)
	if (caller_provider and caller_provider.mdcom_phone):
		caller_id = caller_provider.mdcom_phone

	caller_mgrs = Office_Manager.objects.filter(user__user=log.caller)
	if caller_mgrs:
		caller_mgr = caller_mgrs[0]
		if caller_mgr and caller_mgr.user.current_practice and \
				caller_mgr.user.current_practice.mdcom_phone:
			caller_id = caller_mgr.user.current_practice.mdcom_phone

	provider_qs = Provider.objects.filter(mobile_phone=log.called_number)
	if(not log.called_user and provider_qs):
		log.called_user = provider_qs.get()
		log.save()

	called_manager = False
	if (not log.called_user):
		called_number = log.called_number
	else:
		called_provider = user_is_provider(log.called_user)
		if (not called_provider):
		#office managers can get phone calls too, but they must have mobile phone
			manager_info = OfficeStaff.objects.filter(user=log.called_user)
			if (manager_info.count() > 0 and manager_info[0].user.mobile_phone):
				called_manager = manager_info[0]
#		if (not log.called_user.mobile_phone):
#			if not (called_provider and called_provider.mdcom_phone):
#				# Error -- this call cannot be routed correctly. The called
#				# party must be a user at this point, but doesn't have a mobile
#				# phone number and isn't a provider.
#				subject = 'click2call_response Error Condition'
#				message = 'click2call_response  encountered an error condition where 
#				caller %i calling %i .'%(log.caller.id, log.called_user.id)
#				mail_admins(subject=subject, message=message, fail_silently=False)
#			else:
#				called_number = called_provider.mdcom_phone
#		else:
#			called_number = log.called_user.mobile_phone
		if (called_provider):
			# Send the call through the IVR - old and new way
			if (settings.TWILIO_PHASE == 2):
				# new twilio
				from IVR.views_provider_v2 import ProviderIVR_ForwardCall_New, ProviderIVR_OutsideInit_New
				# Don't send the caller's callerID -- just send the mobile phone
				# number. The OutsideInit function will deal with obfuscating
				# the caller's ID.
				request.session['Caller'] = caller_id
				ProviderIVR_OutsideInit_New(request, log.caller.mobile_phone, called_provider, log)
				logger.debug('%s: Sending call to ProviderIVR_ForwardCall_New called_number %s '
					'caller %s mobile %s' % (request.session.session_key, called_number, 
						caller_id, log.caller.mobile_phone))

				return ProviderIVR_ForwardCall_New(request)
			else:
				from IVR.views_provider import ProviderIVR_ForwardCall, ProviderIVR_OutsideInit
				# Don't send the caller's callerID -- just send the mobile phone
				# number. The OutsideInit function will deal with obfuscating
				# the caller's ID.
				ProviderIVR_OutsideInit(request, log.caller.mobile_phone, called_provider, log)
				request.session['Caller'] = caller_id
				logger.debug('%s: Sending call to ProviderIVR_ForwardCall called_number %s caller %s mobile %s' % (
					request.session.session_key, called_number, caller_id, log.caller.mobile_phone))
			return ProviderIVR_ForwardCall(request)
		elif (called_manager):
			# Send the call through the IVR - old and new way
			if (settings.TWILIO_PHASE == 2):
				# new twilio 2010
				from IVR.views_practice_v2 import PracticeIVR_ForwardCall_New, PracticeIVR_OutsideInit_New
				# Don't send the caller's callerID -- just send the mobile phone
				# number. The OutsideInit function will deal with obfuscating
				# the caller's ID, in case of office managers, it will be floating mdcom number
				request.session['click2call'] = True
				request.session['Caller'] = caller_id
				PracticeIVR_OutsideInit_New(request, log.caller.mobile_phone, called_manager, log)
				logger.debug('%s: Sending call to PracticeIVR_ForwardCall_New called_number %s caller %s mgr %s mobile %s' % (
					request.session.session_key, called_number, caller_id, called_manager, log.caller.mobile_phone))
				return PracticeIVR_ForwardCall_New(request)
			else:
				from IVR.views_practice import PracticeIVR_ForwardCall, PracticeIVR_OutsideInit
				# Don't send the caller's callerID -- just send the mobile phone
				# number. The OutsideInit function will deal with obfuscating
				# the caller's ID, in case of office managers, it will be floating mdcom number
				request.session['click2call'] = True
				request.session['Caller'] = caller_id
				PracticeIVR_OutsideInit(request, log.caller.mobile_phone, called_manager, log)
				logger.debug('%s: Sending call to PracticeIVR_ForwardCall called_number %s '
					'caller %s mgr %s mobile %s' % (request.session.session_key, 
						called_number, caller_id, called_manager, log.caller.mobile_phone))
				return PracticeIVR_ForwardCall(request)
		else:
			raise Exception(_('User isn\'t a provider or office manager with business '
					'cell phone. We aren\'t handling this situation at the moment.'))

	abs_uri = '://'.join([settings.SERVER_PROTOCOL, settings.SERVER_ADDRESS])
	url = reverse('MHLogin.DoctorCom.views.click2call_cleanup')

	dial = twilio.Dial(called_number,
				action=urljoin(abs_uri, url),
				callerId=caller_id,
				timeout=120)
	r.append(dial)

	log.save()

	return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)


@TwilioAuthentication()
def click2call_cleanup(request):
	"""Process click2call_cleanup view request:  

	:param request: The HTTP GET request
	:type request: django.core.handlers.wsgi.WSGIRequest  
	:returns: django.http.HttpResponse -- the result in an HttpResonse object 
	:raises: None 
	"""
	# Todo: SID is currently unclean -- we need to sanitize it.
	logger.debug('%s: click2call_cleanup POST %s' % 
		(request.session.session_key, str(request.POST)))
	sid = request.POST['CallSid']
	log = Click2Call_Log.objects.get(callid=sid)
	# if we got here, we assume its connected this is only for smartphone click2call connections
#	log.connected = True
	log.save()

	r = twilio.Response()

	return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)


def click2call_home(request):	
	"""Process click2call_home view request:  

	:param request: The HTTP GET request
	:type request: django.core.handlers.wsgi.WSGIRequest  
	:returns: django.http.HttpResponse -- the result in an HttpResonse object 
	:raises: None 
	"""
	return HttpResponseRedirect('/')


def page_callbackcheck(request, paged_id):
	"""Process page_callbackcheck view request:  

	:param request: The HTTP GET request
	:type request: django.core.handlers.wsgi.WSGIRequest  
	:returns: django.http.HttpResponse -- the result in an HttpResonse object 
	:raises: None 
	"""
	#before checking if this provider exist, if paged is office staff, get it
	q = OfficeStaff.objects.filter(user__id=paged_id)
	if (q.count() == 1):
		paged = q[0]
	else:
		paged = get_object_or_404(Provider, id=paged_id)

	if (not paged.pager):
		return errlib.err500(request, err_msg=_("The person you are trying to page "
						"doesn't have a pager number listed."))
	if (request.POST):
		form = PageCallbackForm(request.POST)
		if (form.is_valid()):
			# Great, the form is valid. Now, check to see if the user changed their input.
			if (form.cleaned_data['callbackNumber'] == request.session['page_callback']):
				# execute the page.
				callback = request.session['page_callback']
				pager = request.session['pager']
				paged = request.session['paged']

				# clear session data
				request.session.pop('paged_id', None)
				request.session.pop('pager', None)
				request.session.pop('paged', None)
				request.session.pop('page_callback', None)

				return page_execute(request, pager, paged, callback)
			else:
				request.session['page_callback'] = form.cleaned_data['callbackNumber']
				context = get_context(request)
				context['paged'] = request.session['paged']
				context['callback_form'] = PageCallbackForm(
						initial={'callbackNumber': form.cleaned_data['callbackNumber']})
				context['form_action'] = reverse('MHLogin.DoctorCom.views.page_callbackcheck',
								kwargs={'paged_id': int(paged_id)})
				return render_to_response("DoctorCom/page_callback_verify.html", context)
		else:
			context = get_context(request)
			context['paged'] = request.session['paged']
			context['callback_form'] = form
			context['form_action'] = reverse('MHLogin.DoctorCom.views.page_callbackcheck',
								kwargs={'paged_id': int(paged_id)})

			return render_to_response("DoctorCom/page_callback_check.html", context)
	else:
		# This is a new request.
		# First, check if this is a valid user. One who can receive pages.
		paged = Provider.objects.filter(id=paged_id) 
		if (paged.count() != 1):
			paged = OfficeStaff.objects.filter(user__id=paged_id)  # note difference in office 
			# and provider that mhluser is NOT inherited in OfficeStaff
			if (paged.count() != 1):
				paged = None
			else:
				paged = paged[0]
		else:
			paged = paged[0]

		# pager is the one requesting the page.
		pager = MHLUser.objects.get(id=request.user.id)
		#check if pager is office staff, only office managers log in for now
		office_staff = None
		if ('OfficeStaff' in request.session['MHL_UserIDs']):
			office_staff = request.session['MHL_Users']['OfficeStaff']

		if ((not paged) or (not paged.pager)):  # FIXME: pager_confirmed is ignored until
			#we get verification working. or (not paged.pager_confirmed)):
			request.session.pop('paged_id', None)
			request.session.pop('pager', None)
			request.session.pop('paged', None)
			request.session.pop('page_callback', None)
			raise Http404

		request.session['pager'] = pager
		request.session['paged'] = paged
		request.session['paged_id'] = paged_id
		if (office_staff):
			request.session['page_callback'] = office_staff.current_practice.practice_phone
		else:
			request.session['page_callback'] = pager.mobile_phone

		context = get_context(request)
		context['paged'] = paged

		#if pager is the logged in user, see if is office staff
		#office staff, get object to get office number
		if (office_staff):
			practice_phone = office_staff.current_practice.practice_phone
			if office_staff.current_practice.backline_phone:
				practice_phone = office_staff.current_practice.backline_phone
			context['callback_form'] = PageCallbackForm(initial={'callbackNumber': practice_phone})
		else:
			context['callback_form'] = PageCallbackForm(initial={'callbackNumber': pager.mobile_phone})
		context['form_action'] = reverse('MHLogin.DoctorCom.views.page_callbackcheck',
						kwargs={'paged_id': int(paged_id)})

		return render_to_response("DoctorCom/page_callback_check.html", context)


def send_page(pager, paged, callback):
	"""
	Pager and paged are expected to be Provider or OfficeStaff objects.

	:param pager: Person paging
	:param paged: The person being paged
	:param callback: The callback number
	:returns: PagerLog -- the pager log 
	:raises: None but mails admins if reply fails
	"""
	abs_uri = '://'.join([settings.SERVER_PROTOCOL, settings.SERVER_ADDRESS])
	url = reverse('MHLogin.DoctorCom.views.call_hangup')
	# Caller and Called should work with 2010 api but deprecated
	# need to change when we're fully on 2010 api
	d = {
		'Caller': settings.TWILIO_CALLER_ID,
		'Called': paged.pager,
		'Url': urljoin(abs_uri, url),
		'Method': 'POST',
		'SendDigits': 'wwwwww%swwww%s' % (paged.pager_extension, callback),
	}
	try:  # TODO: Test
		auth, uri = client.auth, client.account_uri 
		make_twilio_request('POST', uri + '/Calls', auth=auth, data=d)
	except Exception as e:
		mail_admins("page from %s to %s failed" % (str(pager), str(paged)), repr(e))

	log = PagerLog()
	if (hasattr(pager, 'user')):
		log.pager = pager.user
	else:
		log.pager = pager
	log.paged = paged.user
	log.callback = callback

	log.save()
	return log


def page_execute(request, pager, paged, callback, test_flag=False):
	"""
	:param request: the http request object
	:param pager: Person paging
	:param paged: The person being paged
	:param callback: The callback number
	:param test_flag: 
	:returns: PagerLog -- the pager log 
	:raises: None 
	"""
	log = send_page(pager, paged, callback)	
	context = get_context(request)
	context['paged'] = paged

	if (test_flag):
		return log
	return render_to_response("DoctorCom/page_in_progress.html", context)


@TwilioAuthentication()
def call_hangup(request):
	"""Twilio needs a URL to hang up on a call. This will perform that task.

	:param request: The HTTP request, either GET or GET with filter key argument
	:returns: django.http.HttpResponse -- the result in an HttpResonse object 
	:raises: None 
	"""
	r = twilio.Response()
	r.append(twilio.Hangup())
	return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)


@TwilioAuthentication()
def inbound_call(request):
	"""
	:param request: The HTTP request, either GET or GET with filter key argument
	:returns: django.http.HttpResponse -- the result in an HttpResonse object 
	:raises: None 
	"""
	r = twilio.Response()
	r.append(tts(_("You have called an inactive phone number affiliated with "
		"doctorcom ink. Please visit us online at w w w dot m d com dot com. Good bye.")))
	return HttpResponse(str(r), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)

