
import datetime
import json
import logging
from os.path import join

from django.conf import settings
from django.core import serializers
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template.loader import render_to_string

from MHLogin.MHLCallGroups.Scheduler.models import EventEntry
from MHLogin.MHLCallGroups.utils import isCallGroupMember
from MHLogin.MHLUsers.models import Provider
from MHLogin.utils.mh_logging import get_standard_logger
from MHLogin.utils.decorators import no_cache
from MHLogin.utils.templates import get_context
from MHLogin.utils.timeFormat import time_format


# Setting up logging
logger = get_standard_logger('%s/MHLCallGroups/Scheduler/utils.log' % 
	(settings.LOGGING_ROOT), 'MHLCallGroups.Scheduler.utils', logging.DEBUG)


# I check the event object exists with valid id and call utils checkEventConsistency
def checkDSEventConsistency(dsevent):
	"""
		checks if an existing deserialized event is valid
		calls checkEventConsistency
		returns boolean - if eventEntry is valid or not
	"""
	isValid = 1
	if (dsevent):
		if (dsevent.object.id == None):
			isValid = 0
		else:
			isValid = checkEventConsistency(dsevent.object)
	else:
		isValid = 0
	return isValid


def checkSchedulerView(view):
	validViews = ["month", "agendaWeek", "agendaDay"]
	vobj = json.loads(view)
	name = vobj["name"]	
	start = vobj["start"]	
	end = vobj["end"]	
	if not name in validViews:
		return False
	try:
		datetime.datetime.strptime(start, "%Y-%m-%d %H:%M:%S")
		datetime.datetime.strptime(end, "%Y-%m-%d %H:%M:%S")
	except ValueError:
		return False	
	return True


def checkEventConsistency(event):
	"""
		checks event start > event end, and oncall person is member of call group
		retuns boolean for validity of event 
	"""
	isValid = 1
	if (event):
		if (event.startDate >= event.endDate):
			isValid = 0
		if (not (isCallGroupMember(event.oncallPerson, event.callGroup.pk))):
			isValid = 0
	else:
		isValid = 0
	return isValid


def export_schedule_to_pdf(request, callgroup):
	from weasyprint import HTML
	context = get_context(request)

	context['site'] = callgroup.description
	month, year = int(request.GET.get('month', 1)), int(request.GET.get('year', 9999))
	weekstart = int(request.GET.get('weekstart', 0))
	monthstart = datetime.date(year, month, day=1)
	context['month'] = monthstart.strftime("%B %Y")
	monthstart = monthstart - datetime.timedelta(days=monthstart.day - 1)
	# make sure we start on a sunday (or monday if weekstart=1)
	monthstart = monthstart - datetime.timedelta(days=(monthstart.isoweekday() % 7)) + \
		datetime.timedelta(weekstart)
	user = request.session['MHL_Users']['MHLUser']
	context['weeks'] = generateOnCallList(callgroup, monthstart, weekstart, user)
	context['days'] = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
	for _ in range(weekstart):
		context['days'].append(context['days'].pop(0))
	# load template with context and static root for pdf renderer, generate pdf buffer
	static_root = settings.STATICFILES_DIRS[0]
	html = render_to_string('pdf_schedule.html', {'STATIC_ROOT': static_root}, context)
	weasyhtml = HTML(string=html)
	schedcss = join(static_root, 'css', 'pdf_schedule.css')
	pdf = weasyhtml.write_pdf(stylesheets=[schedcss])  # ,target='/tmp/test.pdf') 
	# prepare response, append &nopdf to GET url for test
	response = HttpResponse(pdf, mimetype="application/pdf")
	response["Cache-Control"] = "no-cache"
	response["Accept-Ranges"] = "none"
	response["Content-Disposition"] = "attachment; filename=schedule-%d-%d.pdf" % (year, month)
	return response if 'nopdf' not in request.GET else \
		render_to_response("pdf_schedule.html", context)


@no_cache
def getCurrentDate(request, callgroup_id=None):
	if request.method == 'GET':
		today = datetime.date.today()
		today = datetime.datetime(today.year, today.month, today.day)
		response = {'currentDate': today.strftime('%Y-%m-%d %H:%M')}
		return HttpResponse(content=json.dumps(response), mimetype='application/json')				


# here, I check that that everything is valid for new event
# how do we pass errors?
def validateNewEvent(dsevent):
	"""
		checks if a newly created deserialized event is valid
		calls checkEventConsistency; also sets creationdate and lastupdate
		returns boolean - if eventEntry is valid or not
	"""
	isValid = 1
	if (dsevent):  
		dsevent.object.creationdate = datetime.datetime.today()
		dsevent.object.lastupdate = datetime.datetime.today()
		if (dsevent.object.pk > 0):
			dsevent.object.pk = None
		isValid = checkEventConsistency(dsevent.object)
		return isValid
	else:
		return 0


def getPrimaryOnCall(callGroup, timestamp):
	"""
		Gets the primary on call Provider given a callgroup and current datetime 
		timestamp (using the right tz). Also, alerts the office managers of any error 
		conditions, and how the call was handled.

		Arguments:
			callGroup: The (integer/string) pk of the CallGroup in question, OR the an 
			actual CallGroup instance itself.
			timestamp: A datetime object representing the date and time 
			(using the correct timezone) you want to get the list of on-calls for.

		Returns:
			An (unexecuted) queryset of Providers who are currently on call. This
			 nominally contains one Provider. However, it may contain more than one or 
			 none if that is the current state of the schedule -- these error conditions 
			 are *not* handled.
	"""
	currentEvent_qs = EventEntry.objects.filter(
		callGroup=callGroup, eventStatus='1', oncallLevel='0',
		startDate__lte=timestamp, endDate__gte=timestamp
		).order_by("-startDate").values_list('oncallPerson', flat=True)
	providers = Provider.objects.filter(user__pk__in=currentEvent_qs)
	return [providers.get(user=u) for u in currentEvent_qs]


def getLastPrimaryOnCall(callGroup, timestamp):
	"""
		Gets the last (or current one, if one is defined) on call Provider given a 
		callgroup and current datetime timestamp (using the right tz). Also, alerts 
		the office managers of any error conditions, and how the call was handled.

		Arguments:
			callGroup: The (integer/string) pk of the CallGroup in question, OR the 
			an actual CallGroup instance itself.
			timestamp: A datetime object representing the date and time (using the 
			correct timezone) you want to get the list of on-calls for.

		Returns:
			An (unexecuted) queryset returning the set of Providers who were most 
			recently on call. This nominally contains one Provider. However, it may 
			contain none if no providers have ever been on-call.
	"""
	currentEvent_qs = EventEntry.objects.filter(
		callGroup=callGroup, eventStatus='1', oncallLevel='0',
		endDate__lte=timestamp
	).order_by('-startDate').values_list('oncallPerson', flat=True)
	providers = Provider.objects.filter(user__pk__in=currentEvent_qs)
	return [providers.get(user=u) for u in currentEvent_qs][:1]


def rulesCheckInternal(callGroupId, fromDate, toDate):
	"""
		checks events for given callgroup and date range to make sure that the time period 
		is covered by a primary oncall returns list of events and errorlist containing the 
		holes of coverage in that time range
	"""
	errorList = []
	# valid, medical on call - eventType '0' for primary on call - oncallLevel 0 only
	eventList = EventEntry.objects.filter(
		Q(eventStatus='1'), Q(callGroup=callGroupId), Q(eventType='0'), Q(oncallLevel=0),
		Q(startDate__range=(fromDate, toDate)) | Q(endDate__range=(fromDate, toDate))
	).order_by('startDate')

	prevDate = datetime.datetime.strptime(fromDate, "%Y-%m-%d %H:%M:%S")
	myendDate = datetime.datetime.strptime(toDate, "%Y-%m-%d %H:%M:%S")

	logger.debug('Initialize prevDate %s ' % (prevDate))

	# ok, this doesn't really account for overlapping primary oncall events
	for eventEntry in eventList:
		# check start date and end date range is covered
		logger.debug('Event start and end is %s - %s' % 
			(eventEntry.startDate, eventEntry.endDate))
		if (eventEntry.startDate > prevDate):
			errorList.append('warning hole in coverage %s - %s' % 
				(prevDate, eventEntry.startDate))
			logger.debug('Hole %s - %s' % (prevDate, eventEntry.startDate))
		prevDate = eventEntry.endDate

	if (prevDate < myendDate):
		errorList.append('warning hole in coverage %s - %s' % (prevDate, myendDate))
	return eventList, errorList


def generateOnCallList(callgroup, startday, weekstart, user):
	weeks = [[] for i in xrange(6)]
	oncall_qs = EventEntry.objects.filter(
		callGroup=callgroup,
		startDate__lt=startday + datetime.timedelta(42),
		endDate__gte=startday,
		eventStatus=1
	).order_by('startDate')
	helper = EventHelper(oncall_qs, weekstart)
	slots = [EventEntry(startDate=datetime.datetime(1, 1, 1), 
					endDate=datetime.datetime(1, 1, 1))] * 10

	for i, week in enumerate(weeks):
		week.extend({} for i in xrange(7))
		for j, day in enumerate(week):
			day['date'] = startday + datetime.timedelta(weeks=i, days=j)
			day['events'] = []
			for event in helper.filter(day['date']):
				name = ' '.join([event.oncallPerson.first_name, event.oncallPerson.last_name])
				e = {
					'name': name,
					'starttime': time_format(user, event.startDate),
					'endtime': time_format(user, event.endDate),
					'color': _getColor(name),
				} 
				#24 hours = 100%, 12 = 50%, etc.
				delta = event.endDate - event.startDate
				width = delta.days * 100.0 + delta.seconds / 3600.0 * 100 / 24
				e['left'] = event.startDate.hour * 100.0 / 24 + \
					event.startDate.minute / 60.0 * 100 / 24
				e['width'] = width
				try:
					e['status'] = 1 if isCallGroupMember(
						event.oncallPerson, event.callGroup.id) else 0
				except:
					e['status'] = 0

				for k, _ in enumerate(slots):
					date = event.startDate - datetime.timedelta(hours=event.startDate.hour, 
							minutes=event.startDate.minute)
					if (event.startDate >= slots[k].endDate and 'top' not in e):
						newslot = k

						for l, slot in enumerate(slots[:k + 1]):
							if slot.startDate >= date and event.startDate >= slot.endDate:
								newslot = l
						e['top'] = -19 * (len(day['events']) - newslot)

						slots[newslot] = event
						day['events'].append(e)
						break

			day['date'] = day['date'].strftime('%d')
	return weeks

usedColors = {}
lastColor = 1


def _getColor(name):
	global lastColor
	global usedColors
	if(name not in usedColors):
		usedColors[name] = '-'.join(['clr', str(lastColor)])
		lastColor = lastColor % 24 + 1
	return usedColors[name]


class EventHelper(object):
	def __init__(self, events, weekstart=0):
		self.events = list(events)
		self.weekstart = weekstart
		self.done = [False for i in range(len(events))]

	def filter(self, day):
		nextday = day + datetime.timedelta(days=1)
		nextday = datetime.datetime(day=nextday.day, month=nextday.month, year=nextday.year)

		day = datetime.datetime(day=day.day, month=day.month, year=day.year) 
		offset = 7 - day.isoweekday() + self.weekstart

		if (offset == 0):
			offset = 7
		endofweek = day + datetime.timedelta(days=offset)
		startofweek = endofweek - datetime.timedelta(days=7)
		events = []
		for i, event in enumerate(self.events):
			if (self.done[i] or event.startDate > nextday or event.endDate <= day):
				pass
			elif (event.startDate < startofweek):
				if(day == startofweek):
					fakeevent = EventEntry(oncallPerson=event.oncallPerson)
					fakeevent.startDate = max(startofweek, event.startDate)
					fakeevent.endDate = min(endofweek, event.endDate)
					if(endofweek >= event.endDate):
						self.done[i] = True
					events.append(fakeevent)
			elif (event.endDate > endofweek and event.startDate >= day and 
					event.startDate < endofweek):
				fakeevent = EventEntry(oncallPerson=event.oncallPerson)
				fakeevent.startDate = max(day, event.startDate)
				fakeevent.endDate = min(endofweek, event.endDate)
				fakeevent._createdday = day
				if(endofweek >= event.endDate):
					self.done[i] = True
				events.append(fakeevent)
			elif (event.startDate >= day and event.startDate < nextday):
				#if(event.startDate >= day and event.startDate <= nextday):
				events.append(event)

		return events


class SessionHelper(object):
	SCHEDULE_UNDOSTACK_NAME = "schedule_undoStack"
	SCHEDULE_REDOSTACK_NAME = "schedule_redoStack"
	SCHEDULE_LASTVIEW = "schedule_lastView"
	CURRENT_CALLGROUP_ID = "current_callgroup_id"

	@staticmethod
	def pushSessionStack(request, stackName, obj):
		sessionStack = []
		if (stackName in request.session):
			sessionStack = request.session[stackName]
		else:
			sessionStack = []

		max_depth = settings.SCHEDULE_EVENT_UNDO_DEPTH	
		length = len(sessionStack)	
		if (length >= max_depth):
			sessionStack = sessionStack[-(length - 1):]

		sessionStack.append(obj)	
		request.session[stackName] = sessionStack

	@staticmethod
	def popSessionStack(request, stackName):
		if (stackName not in request.session):
			return None
		sessionStack = request.session[stackName]	
		if (len(sessionStack) == 0):
			return None
		return sessionStack.pop()

	@staticmethod
	def getSessionStackSize(request, stackName):
		if (stackName not in request.session):
			return 0
		sessionStack = request.session[stackName]	
		return len(sessionStack)

	@staticmethod
	def clearSessionStack(request, stackName):
		request.session[stackName] = []

	@staticmethod
	def clearAllSessionStack(request):
		stack_all_list = [
			SessionHelper.SCHEDULE_UNDOSTACK_NAME,
			SessionHelper.SCHEDULE_REDOSTACK_NAME,
			SessionHelper.SCHEDULE_LASTVIEW
		]
		for name in stack_all_list:
			SessionHelper.clearSessionStack(request, name)

	@staticmethod
	def checkSessionStack(request, stackName, oldPk, newPK):
		if (stackName not in request.session):
			return
		sessionStack = request.session[stackName]		

		for operateList in sessionStack:
			for operateItem in operateList:		
				type = operateItem["type"]
				data = operateItem["data"]
				pk = operateItem["pk"]	

				if (pk == oldPk):
					operateItem["pk"] = newPK
					eventObj = serializers.deserialize("json", data).next()
					eventObj.object.pk = newPK
					eventObj.object.id = newPK
					operateItem["data"] = serializers.serialize("json", [eventObj.object], 
						fields=('oncallPerson', 'eventType', 'startDate', 'endDate', 'checkString'))

		request.session[stackName] = sessionStack	

