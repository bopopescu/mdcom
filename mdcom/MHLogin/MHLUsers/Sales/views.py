
import json
import datetime
import urllib2
from httplib import SERVICE_UNAVAILABLE

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.mail import send_mass_mail
from django.core.urlresolvers import reverse
from django.db.utils import IntegrityError
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.utils.encoding import force_unicode
from django.utils.translation import ugettext as _

from MHLogin.utils.templates import get_context
from MHLogin.utils.mh_logging import get_standard_logger
from MHLogin.Invites.forms import multiUserSendForm
from MHLogin.Invites.models import Invitation, InvitationLog

from MHLogin.MHLUsers.models import MHLUser, Salesperson, Administrator
from MHLogin.MHLUsers.Sales.models import SalesLeads, SalesProduct, SALES_STAGES, SALES_SOURCE
from MHLogin.MHLUsers.Sales.forms import SalesPersonForm

from MHLogin.utils import ImageHelper
from MHLogin.utils.timeFormat import time_format, convert_dt_to_utz
from MHLogin.utils.errlib import err5xx

# Setting up logging
logger = get_standard_logger('%s/MHLUsers/Sales/views.log' % (settings.LOGGING_ROOT),
							'MHLUser.Sales.views', settings.LOGGING_LEVEL)
fullLeadAccess = lambda request: ('Administrator' in request.session['MHL_Users'] or \
			request.user.has_perm('MHLUsers.sales_executive'))


def dashboard(request):
	context = get_context(request)
	user = request.session['MHL_Users']['MHLUser']
	unanswered = Invitation.objects.filter(sender=request.user)
	result = []
	for un in unanswered:
		obj = {}
		obj['recipient'] = un.recipient
		obj['requestTimestamp'] = time_format(user, 
				convert_dt_to_utz(
				un.requestTimestamp, user, context['current_practice']))
		obj['code'] = un.code
		obj['pk'] = un.pk
		result.append(obj)

	context['unanswered_invites'] = result

	answered = InvitationLog.objects.filter(sender=request.user).filter(createdUser__isnull=False)
	result = []
	for an in answered:
		obj = {}
		obj['first_name'] = an.createdUser.first_name
		obj['last_name'] = an.createdUser.last_name
		obj['username'] = an.createdUser.username
		obj['email'] = an.createdUser.email
		obj['requestTimestamp'] = time_format(user, 
				convert_dt_to_utz(
				an.requestTimestamp, user, context['current_practice']))
		obj['responseTimestamp'] = time_format(user, 
				convert_dt_to_utz(
				an.responseTimestamp, user, context['current_practice']))
		result.append(obj)

	context['answered_invites'] = result

	cancelled = InvitationLog.objects.filter(sender=request.user).filter(createdUser__isnull=True)
	result = []
	for ca in cancelled:
		obj = {}
		obj['recipient'] = ca.recipient
		obj['requestTimestamp'] = time_format(user, 
				convert_dt_to_utz(
				ca.requestTimestamp, user, context['current_practice']))
		obj['responseTimestamp'] = time_format(user, 
				convert_dt_to_utz(
				ca.responseTimestamp, user, context['current_practice']))
		result.append(obj)
	context['cancelled_invites'] = result

	return render_to_response('dashboard.html', context)


def new_invites(request):
	context = get_context(request)

	if (request.method == 'POST'):
		context['form'] = multiUserSendForm(request.POST, request.user)
		if (context['form'].is_valid()):
			mass_mail_msgs = []
			test_flag = False
			if ('test' in context['form'].cleaned_data):
				test_flag = context['form'].cleaned_data['test']

			for addr in context['form'].cleaned_data['emailAddresses']:
				invit = Invitation.objects.filter(sender=request.user, recipient=addr, 
					userType=context['form'].cleaned_data['userType'])
				if invit:
					i = invit[0]
					i.requestTimestamp = datetime.datetime.now()
				else:
					i = Invitation(
							sender=request.user,
							recipient=addr,
							userType=context['form'].cleaned_data['userType'],
							testFlag=test_flag,
						)
					i.generate_code()
				i.save()
				#msg_tuple = i.massmail_tuple(context['mhl_user_displayName'], 
					#context['form'].cleaned_data['msg'])
				msg_tuple = i.massmail_tuple(context['form'].cleaned_data['msg'])
				if (msg_tuple):
					mass_mail_msgs.append(msg_tuple)

			if len(mass_mail_msgs):
				send_mass_mail(mass_mail_msgs, fail_silently=False)
				return HttpResponseRedirect(reverse('Sales_Dashboard'))
	else:
		context['form'] = multiUserSendForm()
	return render_to_response('invite_issue.html', context)


def resend_invite(request, invite_pk):
	context = get_context(request)
	err = ''
	context['invite'] = get_object_or_404(Invitation, pk=invite_pk)

	if (request.method == 'GET'):
		if ('action' in request.GET):
			if (request.GET['action'] == 'confirm'):
				if not User.objects.filter(email=context['invite'].recipient):
					context['invite'].resend_invite()
					return HttpResponseRedirect(reverse('Sales_Dashboard'))
				else:
					err = _('At least one email address is already registered.')
	context['err'] = err
	return render_to_response('invite_resend.html', context)


def cancel_invite(request, invite_pk):
	context = get_context(request)
	context['invite'] = get_object_or_404(Invitation, pk=invite_pk)

	if (request.method == 'GET'):
		if ('action' in request.GET):
			if (request.GET['action'] == 'confirm'):
				#context['invite'].delete(send_notice=True)
				context['invite'].cancel_invitation()
				return HttpResponseRedirect(reverse('Sales_Dashboard'))

	return render_to_response('invite_cancel.html', context)


def profile(request):
	"""
	Return Sales profile view

	:param request: The HTTP request, POST with with argument
	:type request: django.core.handlers.wsgi.WSGIRequest
	:returns: django.http.HttpResponse -- the result data in html format
	"""
	context = get_context(request)

	user = MHLUser.objects.get(username=request.user)
	context['user'] = user

	context['photo'] = ImageHelper.get_image_by_type(user.photo, size='Middle', type='Provider')

	return render_to_response('sales_profile_view.html', context)


def profile_edit_sales(request):
	""" This function allows for salespersons to edit their profiles.
	"""

	context = get_context(request)
	# First, get the relevant user's profile. Everything requires it.
	user = MHLUser.objects.get(username=request.user)

	if (request.method == "POST"):
		# First, deal with user form stuff
		salesperson_form = SalesPersonForm(request.POST, request.FILES, instance=user)

		if (salesperson_form.is_valid()):
			salesperson_form.save()

			return HttpResponseRedirect(reverse('MHLogin.MHLUsers.Sales.views.profile'))

		else:  # if not (user_form.is_valid()):
			context['user_form'] = salesperson_form
	else:  # if (request.method != "POST"):
		context['user'] = user
		context['user_form'] = SalesPersonForm(instance=user)

	return render_to_response('sales_profile_edit.html', context)


# show sales leads view for admin/sales - ACL Rules apply: Administrator and Salesperson
def sales_view(request):
	"""Process sales lead view request

	:param request: The HTTP request, POST with with argument
	:type request: django.core.handlers.wsgi.WSGIRequest
	:returns: django.http.HttpResponse -- the result in an HttpResonse object
	:raises: None
	"""
	context = get_context(request)
	# add our own sales display name and id
	context['sales_display_rep_name'] = request.user.first_name + " " + request.user.last_name
	context['sales_display_rep_id'] = request.user.pk
	context['fullLeadAccess'] = fullLeadAccess(request)
	context['stages'] = json.dumps(SALES_STAGES)
	context['sources'] = json.dumps(SALES_SOURCE)
	if hasattr(settings, 'SALES_LEADS_EXPORT_URL'):
		context['export_support'] = 'supported' 

	return render_to_response('workbooks.html', context)


# called by client when retrieving product data
def sales_getproductdata(request):
	""" Process a get product data request from client

	:param request: The HTTP request, POST with with argument
	:type request: django.core.handlers.wsgi.WSGIRequest
	:returns: django.http.HttpResponse -- the result data in xml format
	"""
	sales_id = request.GET['id']
	sl = SalesLeads.objects.get(id=sales_id)

	if (fullLeadAccess(request) or request.session['MHL_UserIDs']['MHLUser'] == sl.rep.pk):
		prods = SalesProduct.objects.filter(lead=sl.id)
		data = list(prods)
		for d in data:
			d.is_active = "1" if d.is_active == True else "0"

		resp = render_to_response('sales_getproductdata.xml',
			{'data': data, 'total': prods.count(), 'pos': 0},
				mimetype='text/xml', context_instance=get_context(request))
	else:
		resp = render_to_response('sales_getproductdata.xml',
			{'data': [], 'total': 0, 'pos': 0},
				mimetype='text/xml', context_instance=get_context(request))

	return resp


# called by client when retrieving all sales leads
def sales_getdata(request):
	"""
	Return grid data in XML format

	:param request: The HTTP request, POST with with argument
	:type request: django.core.handlers.wsgi.WSGIRequest
	:returns: django.http.HttpResponse -- the result data in xml format
	"""
	try:
		if fullLeadAccess(request):
			saleleads = SalesLeads.objects.all()
		elif 'Salesperson' in request.session['MHL_Users']:
			saleleads = SalesLeads.objects.filter(rep=request.user)
		else:
			raise StandardError("Invalid user rights")

		# from DHTMLX grid, extract offset and quantity from GET
		if 'posStart' in request.GET and 'count' in request.GET:
			offset = request.GET['posStart']
			data = list(saleleads[offset:(offset + request.GET['count'])])
		else:
			offset = 0
			data = list(saleleads)

		for d in data:
			# convert dates to strings formated as client grid expects
			d.date_contact = d.date_contact.strftime('%m/%d/%Y')
			d.date_appt = d.date_appt.strftime('%m/%d/%Y')

			d.isLocked = d.style = ""
			# for regular Salespersons make other rows locked, prices unavailable, and red
			if d.rep and request.session['MHL_UserIDs']['MHLUser'] != d.rep.pk:
				if not fullLeadAccess(request):
					d.isLocked = "true"
					d.price = "0.00"
					d.style = "color:#AA0000;"

		resp = render_to_response('sales_getdata.xml',
			{'data': data, 'total': saleleads.count(), 'pos': offset},
				mimetype='text/xml', context_instance=get_context(request))
	except StandardError, error:
		# retrieving
		errmsg = "Problems retrieving from database: %s" % (str(error))
		logger.warn(errmsg)
		resp = sale_error(request, errmsg)

	return resp


# Called when sales leads rows are changed or deleted
def sales_updatedata(request):
	"""
	Updates sales data row and return status

	:param request: The HTTP request, POST with with argument
	:type request: django.core.handlers.wsgi.WSGIRequest
	:returns: django.http.HttpResponse -- the result data in xml format
	"""
	stat = request.GET['!nativeeditor_status']
	if (stat == 'inserted'):
		# create sales products and link them to new sales lead
		sl = SalesLeads()
		resp = update_sale(request, sl)
		log_sales_lead_action(request.user, sl, ADDITION)
	elif (stat == 'updated'):
		sl = SalesLeads.objects.get(id=request.GET['gr_id'])
		if (fullLeadAccess(request) or 
				request.session['MHL_UserIDs']['MHLUser'] == sl.rep.pk):
			resp = update_sale(request, sl)
			log_sales_lead_action(request.user, sl, CHANGE)
		else:  # insufficient privilege
			resp = sale_error(request, _("Not owner of this sales lead"))
	elif (stat == 'deleted'):
		try:
			sl = SalesLeads.objects.get(id=request.GET['gr_id'])
			if (fullLeadAccess(request) or 
					request.session['MHL_UserIDs']['MHLUser'] == sl.rep.pk):

				log_sales_lead_action(request.user, sl, DELETION)
				sl.delete()  # delete the SalesLead object
				resp = render_to_response('sales_updatedata.xml',
					{'action': 'delete', 'tid': request.GET['gr_id'],
						'sid': request.GET['gr_id']}, mimetype='text/xml',
							context_instance=get_context(request))
			else:
				resp = sale_error(request, _("Not owner of this sales lead"))
		except ObjectDoesNotExist, ode:
			errmsg = _("Problems deleting, entry not found: %s") % (str(ode))
			logger.warn(errmsg)
			resp = sale_error(request, errmsg)
	else:
		errmsg = _("Unhandled stat: %s") % (stat)
		logger.warn(errmsg)
		resp = sale_error(request, errmsg)

	return resp


# Called when client sends us updates for product data
def sales_updateproductdata(request):
	"""
	Updates sales product data row and return status

	:param request: The HTTP request, POST with with argument
	:type request: django.core.handlers.wsgi.WSGIRequest
	:returns: django.http.HttpResponse -- the result data in xml format
	"""
	stat = request.GET['!nativeeditor_status']
	if (stat == 'updated'):
		sp = SalesProduct.objects.get(id=request.GET['gr_id'])
		sp.is_active = False if request.GET['c0'] == "0" else True
		sp.quoted_price = request.GET['c3']
		sp.save()

		resp = render_to_response('sales_updatedata.xml',
			{'action': 'insert', 'tid': sp.id, 'sid': request.GET['gr_id']},
			mimetype='text/xml', context_instance=get_context(request))
	else:
		errmsg = _("Unhandled stat: %s") % (stat)
		logger.warn(errmsg)
		resp = sale_error(request, errmsg)

	return resp


# Called when client wants us to copy product data from one sales lead to another
def sales_copyproductdata(request):
	"""
	Client wants to copy product data to another duplicate lead.  First query the
	SalesProducts using Sales Rep as the Fkey for both source and destination.  Then
	copy the product values from source to destination.

	:param request: The HTTP request with GET containing the source and dest SalesLead ids
	:type request: django.core.handlers.wsgi.WSGIRequest
	:returns: django.http.HttpResponse -- the result data in xml format
	"""
	srcId = request.GET['srcId']
	srcprods = SalesProduct.objects.filter(lead=srcId)

	dstId = request.GET['dstId']
	dstprods = SalesProduct.objects.filter(lead=dstId)
	# for each SalesProducts copy values from src to dst
	for src in srcprods:
		dst = dstprods.get(product=src.product)
		dst.is_active = src.is_active
		dst.quoted_price = src.quoted_price
		dst.save()

	return HttpResponse(_("OK, copied %(srcId)s to %(dstId)s") %
					{'srcId': srcId, 'dstId': dstId})


# helper to update one sales record
def update_sale(req, sl):
	"""
	Helper to update sales leads table.  If there is an error during update we
	catch Validation and ObjectDoesNotExist exceptions and log and return back
	to client the error message.

	:param req: The HTTP req, POST with with argument
	:type req: django.core.handlers.wsgi.WSGIRequest
	:param sl: The sales leads database model
	:type sl: models. MHLogin.MHLUsers.Sales.models.SalesLeads
	:returns: django.http.HttpResponse -- the result data in xml format
	"""
	try:
		sl.practice = req.GET['c0']
		sl.region = req.GET['c1']
		sl.salestype = req.GET['c2']
		# cell c3 is subgrid for products and handled differently
		sl.price = req.GET['c4']
		sl.contact = req.GET['c5']
		sl.phone = req.GET['c6']
		sl.email = req.GET['c7']
		sl.website = req.GET['c8']
		try:  # adhere to DHTMLXGrid date format, TODO better to negotiate format
			sl.date_contact = datetime.datetime.strptime(req.GET['c9'], '%m/%d/%Y')
		except ValueError, ve:
			logger.warn("Invalid date format: %s" % (str(ve)))
		try:  # adhere to DHTMLXGrid date format, TODO better to negotiate format
			sl.date_appt = datetime.datetime.strptime(req.GET['c10'], '%m/%d/%Y')
		except ValueError, ve:
			logger.warn("Invalid date format: %s" % (str(ve)))
		sl.stage = req.GET['c11']
		sl.source = req.GET['c12']
		sl.notes = req.GET['c13']
		sl.address = req.GET['c14']
		sl.rep = MHLUser.objects.get(pk=int(req.GET['c15']))
		sl.save()
		resp = render_to_response('sales_updatedata.xml',
					{'action': 'insert', 'tid': sl.id, 'sid': req.GET['gr_id']},
					mimetype='text/xml', context_instance=get_context(req))
	except (ValidationError, ObjectDoesNotExist, IntegrityError), e:
		errmsg = "Problems during update, details: %s" % (str(e))
		logger.error(errmsg)
		resp = sale_error(req, errmsg)

	return resp


# helper to return xml user list for combo box in sales lead worksheet
def sales_getuser_list(request):
	"""
	Returns a json list of all users for use in the sales lead worksheet

	:param request: The HTTP request, POST with with argument
	:type request: django.core.handlers.wsgi.WSGIRequest
	:returns: django.http.HttpResponse -- the result data in json format
	"""
	vals = ("id", "first_name", "last_name")
	# Sales user rep list contains Sales and Admin with no dupes
	ids = list(Salesperson.objects.values_list('user', flat=True))
	ids.extend(list(Administrator.objects.values_list('user', flat=True)))
	users = list(MHLUser.objects.filter(id__in=set(ids)).values_list(*vals))

	return HttpResponse(content=json.dumps(users), mimetype='application/json')


def sales_region_list(request):
	"""
	Returns a json list of all unique regions in sales table

	:param request: The HTTP request
	:type request: django.core.handlers.wsgi.WSGIRequest
	:returns: django.http.HttpResponse -- the result data in json format
	"""
	regions = list(SalesLeads.objects.values_list('region', flat=True).distinct())
	return HttpResponse(content=json.dumps(regions), mimetype='application/json')


# Helper to send error with message and request context back to client
def sale_error(request, msg):
	"""
	Helper to send error with message and request context back to client
	"""
	resp = render_to_response('sales_update_error.xml', {'msg': msg},
		mimetype='text/xml', context_instance=get_context(request))

	return resp


def sales_generate_excel(request):
	""" Foward xml grid to internal php handler, send results back to client """
	if hasattr(settings, 'SALES_LEADS_EXPORT_URL'): 
		try:
			body = request.raw_post_data
			result = urllib2.urlopen(settings.SALES_LEADS_EXPORT_URL, body, timeout=60)
			resp = HttpResponse(result.read())
			# copy specific headers from php server's response
			if 'content-disposition' in result.headers:
				resp['content-disposition'] = result.headers['content-disposition']
			if 'content-type' in result.headers:
				resp['content-type'] = result.headers['content-type']
			if 'cache-control' in result.headers:
				resp['cache-control'] = result.headers['cache-control']
		except (Exception, urllib2.URLError) as e:
			resp = err5xx(request, code=SERVICE_UNAVAILABLE, msg="Error: " + str(e))
	else:
		resp = err5xx(request, code=SERVICE_UNAVAILABLE, 
					msg="Error: SALES_LEADS_EXPORT_URL not defined")
	return resp


def log_sales_lead_action(user, sl, action_flag):
	''' Helper to log sales leads actions.  We can't put in signals because
	signals don't have access to user currently. '''

	LogEntry.objects.log_action(user_id=user.pk,
		content_type_id=ContentType.objects.get_for_model(sl).pk,
		object_id=sl.pk, object_repr=force_unicode(sl),
		action_flag=action_flag)

