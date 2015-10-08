
import datetime
import calendar
import time
import math
import logging
import json
from copy import deepcopy
from django.utils.translation import ugettext as _

from django.db.models import Q
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template.loader import get_template

from MHLogin.MHLUsers.decorators import RequireAdministrator
from MHLogin.MHLUsers.models import MHLUser, Provider, Physician
from MHLogin.MHLUsers.models import OfficeStaff, Office_Manager, Administrator
from MHLogin.MHLSites.models import Site
from MHLogin.MHLPractices.models import PracticeLocation
from MHLogin.utils.constants import SPECIALTY_CHOICES
from MHLogin.utils.errlib import err5xx
from MHLogin.utils.mh_logging import get_standard_logger
from MHLogin.utils.management.commands.set_user_coords import geocode_try_recover_lost_users
from MHLogin.utils.templates import get_context

from MHLogin.Invites.models import Invitation, InvitationLog
from MHLogin.DoctorCom.models import Click2Call_Log, PagerLog
from MHLogin.DoctorCom.IVR.models import callLog

from MHLogin.analytics.forms import MonthForm
from MHLogin.analytics.models import PagerDailySummary, Click2CallDailySummary,\
	MessageDailySummary, InviteDailySummary
from MHLogin.analytics.utils import populatePagerSummary, populateMessageSummary,\
	populateClick2CallSummary, populateInviteSummary, extract_start_end_dates, \
	getSiteAnalyticsTopThree


# Setting up logging
logger = get_standard_logger('%s/analytics/views.log' % (settings.LOGGING_ROOT),
							'analytics.views', logging.INFO)

PERIOD_STRFORMAT = _('Week of %B %d, %Y')
SPECIALTIES = dict(SPECIALTY_CHOICES)


@RequireAdministrator
def home(request):
	"""The main  analytics page with links to specific analytic topics

	:param request: The HTTP request
	:type request: django.core.handlers.wsgi.WSGIRequest
	:returns: django.http.HttpResponse -- the result in an HttpResonse object
	:raises: None
	"""
	return render_to_response("analytics/home.html", get_context(request))


def get_top_n(counts, index, n):
	"""Counts must be a dictionary with list values. This function will sort the dictionary's values
	at the passed-in index, then return a list of lists, comprised of key, value pairs, where value
	is the /counts/ value at /index/. (got it?)

	:param counts: Dictionary with list values where length(counts[key]) > index.
	:param index: Index of the dictionary value list that we should be sorting on and returning.
	:param n: The number of pairs to return. (e.g., 10 will give you a top-ten list)

	:returns:
		List of lists. Outer list contains results in nested list pairs. Inner list contains the
		dictionary key at [0] and the value at /index/ in [1].

	PS, this function exemplifies exactly why I love Python. What would ordinarily be a pain in a
	LOT of other languages is do-able in two SLOCs here.
	"""
	listified_counts = [[key, counts[key][index]] for key in counts.keys()]
	listified_counts.sort(lambda x, y: cmp(x[1], y[1]), reverse=True)
	listified_counts = listified_counts[:n]

	return_data = []
	for entry in listified_counts:
		if (entry[0] == 0):
			return_data.append(['Outside', entry[1]])
		else:
			return_data.append([MHLUser.objects.get(id=entry[0]), entry[1]])

	return return_data


def click2call_caller_called_counts(calls):
	"""Returns counts of click2call callers and called, by user ID.

	:param calls: Click2Call_Log queryset object, filtered as desired. Order doesn't
		matter as it gets lost.
	:returns:
		Dictionary of lists. Dictionary is keyed on user ID. Values are a list, with
		the first value ([0]) being the count of calls initiated, and the second
		value ([1]) being the count of calls received.
		Note that ID 0 reflects an outbound call.
	"""
	results = dict()

	for call in calls:
		# first up, called
		if (call.called_number):
			if not ('outside_call' in results):
				results[0] = [0, 1]
			else:
				results[0][1] += 1
		else:
			if (call.called_user):
				if call.called_user.id not in results:
					results[call.called_user.id] = [0, 1]
				else:
					results[call.called_user.id][1] += 1
			else:
				logger.warn("Called user for this call is empty: "
						"call id: %s, caller: %s" % (call.callid, str(call.caller)))

		# next up, caller
		if (call.caller):
			if call.caller.id not in results:
				results[call.caller.id] = [1, 0]
			else:
				results[call.caller.id][0] += 1
		else:
			logger.warn("No caller for this call: call id: %s" % (call.callid))

	return results


@RequireAdministrator
def click2call(request):
	"""
	Simple analytics for now generate click to call report based on date range or all

	:param request: The HTTP request
	:type request: django.core.handlers.wsgi.WSGIRequest
	:returns: django.http.HttpResponse -- the result in an HttpResonse object
	"""
	context = get_context(request)
	context['call_total'] = 0
	context['period'] = _('Empty')

	# Overall stats from beginning of time
	if (request.method == 'POST'):
		calls = Click2Call_Log.objects.exclude(caller__id=-1).\
					exclude(called_user__id=-1)
		if request.POST and ('start_date' and 'end_date' in request.POST):
			start, end = extract_start_end_dates(
					request.POST['start_date'], request.POST['end_date'])
			if start and end:
				context['period'] = _('From %(start_date)s to %(end_date)s' % {
						"start_date":request.POST['start_date'], \
						"end_date":request.POST['end_date']})
				queryset = calls.filter(timestamp__range=(start, end))
			else:
				queryset = calls.none()
		else:  # empty post from form means query all
			context['period'] = _('All')
			queryset = calls.all()

		context['call_total'] = queryset.count()
		counts = click2call_caller_called_counts(queryset)
		context['top10_callers'] = get_top_n(counts, 0, 10)
		context['top10_called'] = get_top_n(counts, 1, 10)
		context['calls_detail'] = [[c.caller, _('Outside') if c.called_number else
								c.called_user if c.called_user else "<unknown>",
								c.timestamp.date(), c.timestamp.time()]
								for c in queryset]

	form_html = get_template('analytics/date_form.html')
	context['date_form'] = form_html.render(context)
	return render_to_response('analytics/click2call.html', context)


def pages_pager_paged_counts(pages):
	"""Returns counts of page pager and paged, by user ID.

	:param pages:
		PagerLog queryset object, filtered as desired. Order doesn't matter as it gets lost.

	:returns:
		Dictionary of lists. Dictionary is keyed on user ID. Values are a list, with the first
		value ([0]) being the count of pages sent, and the second value ([1]) being the count
		of pages received.
	"""
	results = dict()

	for page in pages:
		# first up, called
		if (page.paged):
			if page.paged.id not in results:
				results[page.paged.id] = [0, 1]
			else:
				results[page.paged.id][1] += 1
		else:
			logger.warn("No paged for this page: page id: %s" % (page.id))

		if (page.pager):
			# next up, caller
			if page.pager.id not in results:
				results[page.pager.id] = [1, 0]
			else:
				results[page.pager.id][0] += 1
		else:
			logger.warn("No pager for this page: page id: %s" % (page.id))

	return results


@RequireAdministrator
def pages(request):
	"""
	Simple analytics for now generate pages report based on date range or all

	:param request: The HTTP request
	:type request: django.core.handlers.wsgi.WSGIRequest
	:returns: django.http.HttpResponse -- the result in an HttpResonse object
	"""
	context = get_context(request)
	context['page_total'] = 0
	context['period'] = _('Empty')

	# Overall stats from beginning of time
	if (request.method == 'POST'):
		if request.POST and ('start_date' and 'end_date' in request.POST):
			start, end = extract_start_end_dates(
					request.POST['start_date'], request.POST['end_date'])
			if start and end:
				context['period'] = _('From %(start_date)s to %(end_date)s' %\
						{"start_date":request.POST['start_date'], \
						"end_date":request.POST['end_date']})
				queryset = PagerLog.objects.filter(timestamp__range=(start, end))
			else:
				queryset = PagerLog.objects.none()
		else:  # empty post from form means query all
			context['period'] = _('All')
			queryset = PagerLog.objects.all()

		context['page_total'] = queryset.count()
		counts = pages_pager_paged_counts(queryset)
		context['top10_pagers'] = get_top_n(counts, 0, 10)
		context['top10_paged'] = get_top_n(counts, 1, 10)
		context['pages_detail'] = [[p.pager, p.paged, p.timestamp.date(),
							p.timestamp.time()] for p in queryset]

	form_html = get_template('analytics/date_form.html')
	context['date_form'] = form_html.render(context)
	return render_to_response('analytics/pages.html', context)


# invites analytics - from invites.invitation and invites.invitationlog
@RequireAdministrator
def invites(request):
	"""Invite analytics request, collect and return 7 day analytics

	:param request: The HTTP request
	:type request: django.core.handlers.wsgi.WSGIRequest
	:returns: django.http.HttpResponse -- the result in an HttpResonse object
	:raises: None
	"""
	context = get_context(request)
	context['period'] = _('Empty')
	# Overall stats from beginning of time
	invitation_count = Invitation.objects.all().count()
	invitationLog_count = InvitationLog.objects.all().count()
	context['invites_total'] = invitation_count
	context['invites_overall'] = invitation_count + invitationLog_count
	# Overall stats from beginning of time
	context['invitelogs_canceled'] = InvitationLog.objects.exclude(canceller=None).count()
	context['invitelogs_accepted'] = InvitationLog.objects.filter(canceller=None).count()

	if (request.method == 'POST'):
		# first, sanitize input.
		if 'end_date' in request.POST and request.POST['end_date']:
			lastdayofcalc = datetime.datetime.strptime(request.POST['end_date'], "%m-%d-%Y")
		else:
			lastdayofcalc = datetime.datetime.now()
		# count top inviters by sender_id and count -- and possibly date range?
		# invite stats by day for last 7 days
		daterange = 0
		# loop for last 7 days, calculate pager summary
		while daterange < 7:
			# calculate for days in the range
			datecalc = lastdayofcalc - datetime.timedelta(days=daterange)
			try:
				invitesum = InviteDailySummary.objects.get(dateoflog=datecalc)
				if (invitesum.dateoflog == invitesum.calcdate.date()):
					# cache hit but out of date, need refresh to get full day of stats
					populateInviteSummary(datecalc)
			except ObjectDoesNotExist:
				# InviteDailySummary not in cache, populate it
				populateInviteSummary(datecalc)
			# next day
			daterange = daterange + 1

		# now we get the results
		inviteResult = InviteDailySummary.objects.\
			filter(dateoflog__range=(datecalc, lastdayofcalc)).order_by('dateoflog')
		context['start_date'] = datecalc
		context['end_date'] = lastdayofcalc
		context['period'] = _('From %(datecalc)s To %(lastdayofcalc)s' \
							% {"datecalc":datecalc.strftime("%m-%d-%Y"),
										"lastdayofcalc":lastdayofcalc.strftime("%m-%d-%Y")})
		context['invites_summary_detail'] = [[i.dateoflog, i.countTotal,
											i.countCanceled] for i in inviteResult]

	return render_to_response('analytics/invites.html', context)


@RequireAdministrator
def summary(request):
	"""Process detailed summary request:  Will render the page by default when no arguments
	given.  If request is a POST validates and processes form input.
	Actually gets a date - if none, defaults to today - 1

	:param request: The HTTP request
	:type request: django.core.handlers.wsgi.WSGIRequest
	:returns: django.http.HttpResponse -- the result in an HttpResonse object
	:raises: None
	"""
	context = get_context(request)
	context['period'] = _('Empty')

	if (request.method == 'POST'):
		# first, sanitize input.
		if 'end_date' in request.POST and request.POST['end_date']:
			lastdayofcalc = datetime.datetime.strptime(request.POST['end_date'], "%m-%d-%Y")
		else:
			lastdayofcalc = datetime.datetime.now()

		# get last 14 days' summary from summary table (not including today?)
		# if no values, we recalculate from raw logs and update the table
		# for now, assume we have no date entered, set dayofcalc to today if no date specified
		daterange = 0
		siteAnalyticsResult = []
		# loop for last 14 days, calculate pager summary
		while daterange < 14:
			# calculate for days in the range
			delta = datetime.timedelta(days=daterange)
			datecalc = lastdayofcalc - delta
			# calculate pagelog
			try:
				pagesum = PagerDailySummary.objects.get(dateoflog=datecalc)
				# need recalc to get full day's worth of stats
				if (pagesum.dateoflog == pagesum.calcdate.date()):
					populatePagerSummary(datecalc)
			except ObjectDoesNotExist:
				populatePagerSummary(datecalc)

			#calculate messagelog
			try:
				messagesum = MessageDailySummary.objects.get(dateoflog=datecalc)
				# need recalc to get full day's worth of stats
				if (messagesum.dateoflog == messagesum.calcdate.date()):
					populateMessageSummary(datecalc)
			except ObjectDoesNotExist:
				populateMessageSummary(datecalc)

			#calculate click2call log
			try:
				click2callsum = Click2CallDailySummary.objects.get(dateoflog=datecalc)
				# need recalc to get full day's worth of stats
				if (click2callsum.dateoflog == click2callsum.calcdate.date()):
					populateClick2CallSummary(datecalc)
			except ObjectDoesNotExist:
				populateClick2CallSummary(datecalc)

			# get siteAnalytics for date and collect
			try:
				siteAnalyticsDays = list(getSiteAnalyticsTopThree(datecalc))
				for sad in siteAnalyticsDays:
					siteAnalyticsResult.append(sad)
			except ObjectDoesNotExist:
				continue
			daterange = daterange + 1  # next day

		context['period'] = _('From %(datecalc)s To %(lastdayofcalc)s' \
							% {"datecalc":datecalc.strftime("%m-%d-%Y"),
										"lastdayofcalc":lastdayofcalc.strftime("%m-%d-%Y")})
		# return summary with analytics data
		rc = summaryDisplay(request, context, datecalc, lastdayofcalc, siteAnalyticsResult)
	else:
		rc = render_to_response("analytics/summary.html", context)

	return rc


def summaryDisplay(request, context, datecalc, lastdayofcalc, siteAnalyticsResult):
	"""Helper to display summary called by detailSummary.

	:param request: The HTTP request
	:type request: django.core.handlers.wsgi.WSGIRequest
	:param context: context object
	:type context:
	:param datecalc: datecalc object
	:type datecalc:
	:param lastdayofcalc: lastdayofcalc object
	:type lastdayofcalc:
	:param siteAnalyticsResult: siteAnalyticsResult object
	:type siteAnalyticsResult:

	:returns: django.http.HttpResponse -- the result in an HttpResonse object
	:raises: Exception
	"""
	pageResult = PagerDailySummary.objects.filter(
		dateoflog__range=(datecalc, lastdayofcalc)).order_by('dateoflog')
	messageResult = MessageDailySummary.objects.filter(
		dateoflog__range=(datecalc, lastdayofcalc)).order_by('dateoflog')
	click2callResult = Click2CallDailySummary.objects.filter(
		dateoflog__range=(datecalc, lastdayofcalc)).order_by('dateoflog')

	context['pages_summary_detail'] = [[
		calendar.timegm(p.dateoflog.timetuple()) * 1000, p.countSuccess,
			p.dateoflog] for p in pageResult]
	context['messages_summary_detail'] = [[
		calendar.timegm(m.dateoflog.timetuple()) * 1000, m.countSuccess,
			m.countFailure, m.dateoflog] for m in messageResult]
	context['click2call_summary_detail'] = [[
		calendar.timegm(c.dateoflog.timetuple()) * 1000,
			c.countSuccess, c.countFailure, c.dateoflog] for c in click2callResult]
	context['siteAnalytics_detail'] = [[
		calendar.timegm(s.dateoflog.timetuple()) * 1000, s.site, s.totalForSite,
			s.dateoflog, s.countPage, s.countMessage, s.countClick2Call]
									for s in siteAnalyticsResult]

	return render_to_response("analytics/summary.html", context)


def twilio_stats(request):
	"""Process twilio statics request:  Will render the page by default when no arguments
	given.  If request is a POST validates and processes form input.

	:param request: The HTTP request
	:type request: django.core.handlers.wsgi.WSGIRequest
	:returns: django.http.HttpResponse -- the result in an HttpResonse object
	:raises: Exception
	"""
	date = datetime.date.today()
	if request.method == 'POST':
		# first, sanitize input.
		change_form = MonthForm(request.POST)
		if (change_form.is_valid()):
			date = datetime.date(int(change_form.cleaned_data['year']),
								int(change_form.cleaned_data['month']), 1)
	# start at beginning of week
	date = date.replace(day=1)
	start = date

	if (start.month < 12):
		end = date.replace(month=date.month + 1)
	else:
		end = date.replace(year=date.year + 1, month=1)

	only_vars = ('call_source', 'caller_type__id', 'caller_id', 'caller_number',
				'called_id', 'called_type__id', 'called_number', 'call_duration', 'timestamp')
	logs = callLog.objects.filter(timestamp__gte=start, timestamp__lt=end).\
		select_related('called_type', 'caller_type').only(*only_vars)

	context = get_context(request)
	days = []
	for i in xrange((end - start).days):
		day = start + datetime.timedelta(days=i)
		day = int(time.mktime(day.timetuple())) * 1000
		day = [day, 0]
		days.append(day)

	context['click2calltotal'] = deepcopy(days)
	context['outsidecalltotal'] = deepcopy(days)
	context['answeringservicetotal'] = deepcopy(days)
	context['voicemailtotal'] = deepcopy(days)
	context['callbacktotal'] = deepcopy(days)
	context['total'] = 0
	context['show_change_timeslice'] = 1
	users = {}

	def get_name(thingy, default):
		name = str(type(thingy))  # default
		if(hasattr(thingy, 'first_name')):
			name = ' '.join([thingy.first_name, thingy.last_name])
		elif(hasattr(thingy, 'practice_name')):
			name = thingy.practice_name
		return name

	user_id = 0
	for log in logs:
		user = (0, 0)  # ORLY?
		if(not log.call_duration):
			continue
		if(log.caller_id):
			user = (log.called_type.id, log.called_id)
			if(user not in users):
				users[user] = {
					'click2call': deepcopy(days),
					'outsidecall': deepcopy(days),
					'answeringservice': deepcopy(days),
					'voicemail': deepcopy(days),
					'callback': deepcopy(days),
					'total': 0,
					'name': get_name(log.mdcom_caller, log.caller_number),
					'id': user_id}
				user_id += 1

		elif(log.called_id):
			user = (log.called_type.id, log.called_id)

			if(user not in users):
				users[user] = {
					'click2call': deepcopy(days),
					'outsidecall': deepcopy(days),
					'answeringservice': deepcopy(days),
					'voicemail': deepcopy(days),
					'callback': deepcopy(days),
					'total': 0,
					'name': get_name(log.mdcom_called, log.called_number),
					'id': user_id}
				user_id += 1
		else:
			continue

		day = (log.timestamp.date() - start).days
		if(log.call_source == 'CC'):
			users[user]['click2call'][day][1] += log.call_duration
			context['click2calltotal'][day][1] += log.call_duration
			context['total'] += log.call_duration
		elif(log.call_source == 'OC'):
			users[user]['outsidecall'][day][1] += log.call_duration
			context['outsidecalltotal'][day][1] += log.call_duration
			context['total'] += log.call_duration
		elif(log.call_source == 'AS'):
			context['answeringservicetotal'][day][1] += log.call_duration
			users[user]['answeringservice'][day][1] += log.call_duration
			context['total'] += log.call_duration
		elif(log.call_source == 'VM'):
			context['voicemailtotal'][day][1] += log.call_duration
			users[user]['voicemail'][day][1] += log.call_duration
			context['total'] += log.call_duration
		elif(log.call_source == 'CB'):
			context['callbacktotal'][day][1] += log.call_duration
			users[user]['callback'][day][1] += log.call_duration
			context['total'] += log.call_duration
		else:
			raise Exception(log.call_source)
		users[user]['total'] += log.call_duration

	if(len(users)):
		context['mean'] = context['total'] / len(users)
		context['stdev'] = math.sqrt(sum((user['total'] - context['mean']) ** 2
										for user in users.values()) / len(users))
	users = sorted(users.iteritems(), key=lambda user: user[1]['total'], reverse=True)
	context['users'] = users

	form_html = get_template('analytics/monthly_form.html')
	context['change_form'] = MonthForm(initial={'month': date.month, 'year': date.year})
	context['change_timeslice_form'] = form_html.render(context)

	return render_to_response('analytics/twilio.html', context)


# show analytic map view
@RequireAdministrator
def map_view(request):
	"""Process map view request:  Will render the page by default when no arguments
	given.  When mapfilter is present in the GET request it will return a result
	set giving all users or subset depending on the filter.

	:param request: The HTTP request, either GET or GET with filter key argument
	:type request: django.core.handlers.wsgi.WSGIRequest
	:returns: django.http.HttpResponse -- the result in an HttpResonse object
	:raises: None
	"""
	mapfilter = rc = None
	if request.POST:
		if 'locate' in request.POST:
			if 'locate' in request.session:
				logger.warn("Overriding request session key locate: %s with %s" %
							(request.session['locate'], request.POST['locate']))
			request.session['locate'] = request.POST['locate']
		# Store post data in session key and re-direct so map doesn't think it's a
		# form. We get post somewhere else because we don't want locate in the url.
		rc = HttpResponseRedirect(reverse('MHLogin.analytics.views.map_view'))
	else:
		extra = {}
		extra['locate'] = request.session.pop('locate', None)
		if 'filter' in request.GET:
			mapfilter = request.GET['filter']
			if (mapfilter == "all"):
				rc = mapGetUserSet(MHLUser.objects.values_list('id', flat=True))
			elif (mapfilter == "physicians"):
				rc = mapGetUserSet(Physician.objects.values_list('user', flat=True))
			elif (mapfilter == "providers"):
				rc = mapGetUserSet(Provider.objects.values_list('user', flat=True))
			elif (mapfilter == "admin"):
				rc = mapGetUserSet(Administrator.objects.values_list('user', flat=True))
			elif (mapfilter == "managers"):
				rc = mapGetUserSet(Office_Manager.objects.values_list('user__user', flat=True))
			elif (mapfilter == "staff"):
				rc = mapGetUserSet(OfficeStaff.objects.values_list('user', flat=True))
			elif (mapfilter == "sites"):
				rc = mapGetSites()
			elif (mapfilter == "practices"):
				rc = mapGetPractices()
			else:
				rc = err5xx(request, msg=_("Invalid argument: %s" % mapfilter))
		else:
			rc = render_to_response('analytics/map.html', dictionary=extra,
								context_instance=get_context(request))

	return rc


# Helper to get the userset given user id's.
def mapGetUserSet(ids):
	"""Helper to get userset for analytics map based on list of user ids.
	If the user has no or invalid lat/long coordinates they are not returned as
	part of the user list.  A dictionary is returned containing a list of users.

	:param ids: The query set of user ids
	:type ids: django.db.models.query.ValuesListQuerySet
	:returns: django.http.HttpResponse -- the result - inside a dictionary
		return_set consisting of the user list.
	:raises: None
	"""
	# NOTE: value field list must contain at least 4 valid entries and
	# <id>, <lat>, <longit>, <name>
	vals = ("id", "lat", "longit", "username", "first_name", "last_name")

	users = MHLUser.objects.filter(id__in=ids).\
		exclude(Q(lat=0.0, longit=0.0) | Q(lat=None, longit=None)).values_list(*vals)

	return HttpResponse(content=json.dumps({'users': list(users)}),
					mimetype='application/json')


# Helper to get the sites
def mapGetSites():
	"""Helper to get sites for analytics map.

	:returns: django.http.HttpResponse -- the result - inside a dictionary
		return_set consisting of one element: the site list.
	:raises: None
	"""
	# NOTE: value field list must contain at least 4 valid entries and
	# <id>, <lat>, <longit>, <name>
	vals = ("id", "lat", "longit", "name")

	return HttpResponse(content=json.dumps(
			{'sites': list(Site.objects.values_list(*vals))}),
					mimetype='application/json')


# Helper to get the practices
def mapGetPractices():
	"""Helper to get practices for analytics map.

	:returns: django.http.HttpResponse -- the result - inside a dictionary
		return_set consisting of one element: the practice list.
	:raises: None
	"""
	# NOTE: value field list must contain at least 4 valid entries and
	# <id>, <lat>, <longit>, <name>
	vals = ("id", "practice_lat", "practice_longit", "practice_name")

	return HttpResponse(content=json.dumps(
		{'practices': list(PracticeLocation.objects.values_list(*vals))}),
					mimetype='application/json')


@RequireAdministrator
def map_lost(request):
	"""Process map lost request:  Will show lost users

	:param request: The HTTP request, either GET or GET with filter key argument
	:type request: django.core.handlers.wsgi.WSGIRequest
	:returns: django.http.HttpResponse -- the result in an HttpResonse object
	:raises: None
	"""
	return render_to_response('analytics/map_lost.html', get_context(request))


@RequireAdministrator
def map_get_lost_list(request):
	""" Process the get lost list request from client

	:param request: The HTTP request, either GET or GET with filter key argument
	:type request: django.core.handlers.wsgi.WSGIRequest
	:returns: JSON formated list of all lost users
	"""
	vals = ("first_name", "last_name", "mobile_phone", "phone", "email", "lat", "longit", "id")

	# check if this is a geocode request, if so we send geocode requests to google or yahoo
	isGeocode = request.GET['geocode'].lower() == "true" if 'geocode' in request.GET else False

	lost = MHLUser.objects.filter(Q(lat=0.0, longit=0.0) | Q(lat=None, longit=None))

	if (isGeocode == True):
		# Note: lost is a QuerySet so any users who become unlost will be removed
		geocode_try_recover_lost_users(lost)

	lost = lost.values_list(*vals)
	return HttpResponse(content=json.dumps({'lost': list(lost),
						'count': lost.count()}), mimetype='application/json')


@RequireAdministrator
def map_get_content_info(request):
	""" Given GET parameters with id and type for user or office return content list

		:returns: content string for the user, site, or practice
	"""
	req_type = request.GET.get("type", None)
	req_type_id = request.GET.get("id", None)

	# helper to generate link to user
	def generate_member_html(user):
		return "<a href='javascript:findAndBounceUser(\"%s\")'>"\
			"%s %s</a>" % (user.username, user.first_name, user.last_name)

	if (req_type and req_type_id):
		content = ""
		try:
			if (req_type == "user"):
				user = MHLUser.objects.get(id=req_type_id)
				content = "%s %s\n%s\n%s, %s  %s\n" \
					"Mobile: %s\nPrimary: %s\nEmail: %s\nLast Login: %s" % \
						(user.first_name, user.last_name, user.address1, user.city, user.state,
						user.zip, user.mobile_phone, user.phone, user.email, user.last_login)

				if Provider.objects.filter(user=user).exists():
					prov = Provider.objects.filter(user=user)[0]
					practices = ',\n'.join([p.practice_name for p in prov.practices.all()])
					content += "\nPractices: %s" % (practices)
				# not elif, rest checks other types since Provider inherits MHLUser
				if Physician.objects.filter(user__user=user).exists():
					phys = Physician.objects.filter(user__user=user)[0]
					content += "\nSpecialty: %s" % (SPECIALTIES[phys.specialty]
							if phys.specialty in SPECIALTIES else phys.specialty)
				elif OfficeStaff.objects.filter(user=user).exists():
					staff = OfficeStaff.objects.filter(user=user)[0]
					practices = ',\n'.join([p.practice_name for p in staff.practices.all()])
					content += "\nStaff Practices: %s" % (practices)
				elif Office_Manager.objects.filter(user__user=user).exists():
					mgr = Office_Manager.objects.filter(user__user=user)[0]
					practices = ',\n'.join([p.practice_name for p in mgr.user.practices.all()])
					content += "\nStaff Practices: %s" % (practices)
			elif (req_type == "site"):
				site = Site.objects.get(id=req_type_id)
				content = "%s\n%s\n%s, %s  %s" % \
						(site.name, site.address1, site.city, site.state, site.zip)

				result = list(OfficeStaff.objects.filter(sites=site).\
								values_list('user', flat=True))
				result.extend(list(Provider.objects.filter(sites=site).\
									values_list('user', flat=True)))
				users = MHLUser.objects.filter(id__in=set(result)).distinct()
				members = ', '.join([generate_member_html(u) for u in  users])
				content += "\nMembers: %s" % (members)
			elif (req_type == "practice"):
				pract = PracticeLocation.objects.get(id=req_type_id)
				content = "%s\n%s\n%s, %s  %s\n" \
					"Phone: %s\nDoctorCom phone: %s" % \
						(pract.practice_name, pract.practice_address1,
						pract.practice_city, pract.practice_state,
						pract.practice_zip, pract.practice_phone, pract.mdcom_phone)

				result = list(OfficeStaff.objects.filter(practices=pract).\
								values_list('user', flat=True))
				result.extend(list(Provider.objects.filter(practices=pract).\
									values_list('user', flat=True)))
				users = MHLUser.objects.filter(id__in=set(result)).distinct()
				members = ', '.join([generate_member_html(u) for u in  users])
				content += "\nMembers: %s" % (members)
			else:
				content = "Unsupported request_type: %s" % req_type
		except (ObjectDoesNotExist), ode:
			content = "Element content not found for marker " \
				"type/id (exception): %s/%s (%s)" % (req_type, req_type_id, str(ode))

		content = "<br />".join(content.split("\n"))
	else:
		content = _("Content info request must contain valid type and id")

	return HttpResponse(content=content, mimetype='text/html')

