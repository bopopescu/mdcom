
import datetime
import logging
import json

from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.core.exceptions import ValidationError
from django.conf import settings
from django.db.models import Q
from django.core import serializers
from django.contrib.auth.models import User

from MHLogin.utils.errlib import err403
from MHLogin.utils.templates import get_context
from MHLogin.MHLUsers.models import MHLUser, Provider
from MHLogin.MHLUsers.utils import get_fullname
from MHLogin.utils.decorators import no_cache

# CallGroups Imports
from MHLogin.MHLCallGroups.models import CallGroup, CallGroupMember
from MHLogin.MHLCallGroups.utils import canAccessCallGroup, \
	canAccessMultiCallGroup

# Scheduler imports
from MHLogin.MHLCallGroups.Scheduler.models import EventEntry
from MHLogin.MHLCallGroups.Scheduler.forms import DateEntryForm, BulkEventForm
from MHLogin.MHLCallGroups.Scheduler.utils import rulesCheckInternal, SessionHelper, \
	export_schedule_to_pdf, checkDSEventConsistency, checkSchedulerView, validateNewEvent

from MHLogin.utils.mh_logging import get_standard_logger 

# Setting up logging
logger = get_standard_logger('%s/MHLCallGroups/Scheduler/views.log' % 
	(settings.LOGGING_ROOT), 'MHLCallGroups.Scheduler.views', logging.DEBUG)


def display_scheduler(request, callgroup_id):
	if (not canAccessCallGroup(request.user, long(callgroup_id))):
		return err403(request)

	context = get_context(request)
	return render_to_response("schedule.html", context)


# NOTE:
# all the operations on Scheduler is for specific CallGroup which needs to be passed in, 
# or use the user/requestor's all the list of oncall users, etc, should be restricted to
# members of the callgroup -- TO BE IMPLEMENTED!  We need to provide a way to call some 
# of these functionalities directly without forms/http requests (server calls)
#def home(request):
#	context = get_context(request)
#	return render_to_response("scheduler_home.html", context)


@no_cache
def getEvents(request, callgroup_id=None):
	"""
		gets events associated with a callgroup
		retuns eventList serialized in json format
	"""
	if (not canAccessCallGroup(request.user, long(callgroup_id))):
		return err403(request)

	fromDateTmp = datetime.date.today() - datetime.timedelta(days=15)  # defaults
	toDateTmp = datetime.date.today() + datetime.timedelta(days=30)
	eventList = []
	if request.method == 'POST':
		form = DateEntryForm(request.POST)
		# ok - checking for is_valid() on the form is buggy with DateTime - it seems?!
		if form.is_valid():
		# get fromDate and toDate and fetch the events
			fromDateTmp = form.cleaned_data['fromDate']
			logger.debug('fromDate from request is %s' % 
				(fromDateTmp))
			toDateTmp = form.cleaned_data['toDate']
			logger.debug('toDate from request is %s' % 
				(toDateTmp))
			if ('callGroup' in form.cleaned_data):
				callGroupId = form.cleaned_data['callGroup']
			else:
				callGroupId = callgroup_id
			logger.debug('callGroupId from request is %d' % 
				int(callGroupId))

			user = MHLUser.objects.get(pk=request.user.pk)
			# get the user's callGroup id?
			# need to check if user is office manager or physician in the callGroup
			if (user):
				eventList = EventEntry.objects.filter(
					Q(eventStatus='1'), Q(callGroup=callGroupId),
					startDate__lt=toDateTmp, endDate__gt=fromDateTmp
				)
			else:
				raise Exception('Only users can view scheduled events')	

			data = serializers.serialize("json", eventList, fields=('oncallPerson', 
				'oncallPerson__user', 'eventType', 'startDate', 'endDate', 'checkString'))

			addData = json.loads(data)
			members = CallGroupMember.objects.filter(
				call_group__id=callgroup_id).values_list('member__user__id')
			for d in addData:
				id = d['fields']['oncallPerson']
				user = MHLUser.objects.get(id=id)
				d['fields']['fullname'] = get_fullname(user)
				if (long(id),) in members:
					d['fields']['hasDeleted'] = 0
				else:
					d['fields']['hasDeleted'] = 1

			data = json.dumps(addData)
			logger.debug('user %s - got back %d events' % 
				(user, eventList.count()))
			SessionHelper.clearSessionStack(request, SessionHelper.SCHEDULE_UNDOSTACK_NAME)
			SessionHelper.clearSessionStack(request, SessionHelper.SCHEDULE_REDOSTACK_NAME)
			return HttpResponse(content=json.dumps({'datas': data,
				'undoSize': 0,
				'redoSize': 0}),
				mimetype='application/json')
		else:
			r = HttpResponse()
			r.status_code = 403
			return r
	else: 
		form = DateEntryForm(initial={'fromDate': fromDateTmp, 'toDate': toDateTmp, })
		return render_to_response("DateEntry.html", {'form': form, })


# rule to check: make sure 24x7 coverage on medical on call for next 14 days
@no_cache
def rulesCheck(request, callgroup_id=None):
	"""
		checks for holes in oncall coverage in eventEntry records for the next 14 days
		calls utils rulesCheckInternal(callGroupId, fromDateTmp, toDateTmp)
		returns eventEntry list and list of holes in coverage
	"""
	# get all the events for next 2 weeks
	fromDateTmp = datetime.datetime.now()
	toDateTmp = fromDateTmp + datetime.timedelta(days=14)
	if request.method == 'POST':
		form = DateEntryForm(request.POST)
		# datestring is needed for the rulesCheckInternal
		fromDateStr = fromDateTmp.strftime("%Y-%m-%d %H:%M:%S")
		toDateStr = toDateTmp.strftime("%Y-%m-%d %H:%M:%S")
		eventList, errorList = rulesCheckInternal(callgroup_id, fromDateStr, toDateStr)
		logger.debug('returned result %d error %d' % (len(eventList), len(errorList)))
		data = serializers.serialize("json", eventList)
		response = {'data': data, 'error': errorList}
		logger.debug('rulescheck result %s' % (response))
		# TODO: need to dump out response
		return HttpResponse(content=json.dumps(errorList), mimetype='application/json')
	else: 
		form = DateEntryForm(initial={'fromDate': fromDateTmp, 'toDate': toDateTmp, })
		return render_to_response("DateEntry.html", {'form': form, })


# assume for now the scheduler will pass new events with pk = null, checkString NOT null
@no_cache
def bulkNewEvents(request, callgroup_id=None):
	"""
		bulk add eventEntry
		returns result of eventEntries saved and any errors/warnings
	"""
	if (not canAccessCallGroup(request.user, long(callgroup_id))):
		return err403(request)

	user = request.user
	if request.method == 'POST':
		form = BulkEventForm(request.POST)
		data = request.POST['data']
		view = request.POST['view']
		errorlist = []  # this contains errors/warnings 
		operateList = []		
		count = 0  # count how many events we got
		newPks = dict()
		logger.debug('data from request is %s' % (data))

		if checkSchedulerView(view):
			for newdsEventObj in serializers.deserialize("json", data):
				count = count + 1
				# set defaults
				newdsEventObj.object.callGroup_id = int(callgroup_id)
				newdsEventObj.object.notifyState = 2
				newdsEventObj.object.whoCanModify = 1
				newdsEventObj.object.eventStatus = 1
				if validateNewEvent(newdsEventObj):
					# we are ok to save this new object
					newdsEventObj.object.creator = user
					newdsEventObj.object.creationdate = datetime.datetime.now()
					newdsEventObj.object.lastupdate = datetime.datetime.now()
					newdsEventObj.object.title = 'scheduled_event'
					try:
						# validate the EventEntry 
						newdsEventObj.object.clean_fields()	
						newdsEventObj.save()
						newPks[newdsEventObj.object.checkString] = newdsEventObj.object.pk

						operateList.append({
							'type': "2",
							"view": view,
							"pk": newdsEventObj.object.pk,
							'data': serializers.serialize("json", [newdsEventObj.object],
									fields=('oncallPerson', 'eventType', 
										'startDate', 'endDate', 'checkString'))})	
					except ValidationError:
						errorlist.append('Validate error saving new object: %s' % 
							(serializers.serialize("json", [newdsEventObj.object],
								fields=('oncallPerson', 'eventType', 'startDate',
									'endDate', 'checkString'))))
				else:
					errorlist.append('%s, error saving new object' % (newdsEventObj.object.checkString))
		else:
			errorlist.append("invalid view")

		SessionHelper.pushSessionStack(request, SessionHelper.SCHEDULE_UNDOSTACK_NAME, operateList)		
		SessionHelper.clearSessionStack(request, SessionHelper.SCHEDULE_REDOSTACK_NAME)					
		response = {'data': newPks, 'error': errorlist, 'count': count,
				'undoSize': SessionHelper.getSessionStackSize(request, 
					SessionHelper.SCHEDULE_UNDOSTACK_NAME),
				'redoSize': SessionHelper.getSessionStackSize(request, 
					SessionHelper.SCHEDULE_REDOSTACK_NAME)}
		logger.debug('returned result %s' % (response))
		return HttpResponse(content=json.dumps(response), mimetype='application/json')
	else:
		form = BulkEventForm()
		return render_to_response("bulkOperation.html", {'form': form, })


# we need to set: creator, creationdate, lastupdate and crosscheck checkString
@no_cache
def bulkUpdateEvents(request, callgroup_id=None):
	"""
		bulk update eventEntry returns result of eventEntries updated and any 
		errors/warnings if there is a mismatch with checkString
	"""
	if (not canAccessCallGroup(request.user, long(callgroup_id))):
		return err403(request)

	user = request.user
	if request.method == 'POST':
		# form = BulkEventForm(request.POST) # never used.
		errorlist = []
		savelist = []
		operateList = []
		count = 0
		data = request.POST['data']
		view = request.POST['view']

		if checkSchedulerView(view):
			logger.debug('data from request is %s' % (data))
			for eventObj in serializers.deserialize("json", data):
				count = count + 1
				eventObj.object.callGroup_id = int(callgroup_id)
				# necessary for easier access in the admin
				eventObj.object.title = 'scheduled_event-%i' % (eventObj.object.pk,)
				eventObj.object.notifyState = 2
				eventObj.object.whoCanModify = 1
				# we check for pk presence first
				if (eventObj.object.pk == None):
					errorlist.append("0, error updating object - no key present %s %s" %
						(eventObj.object.checkString, eventObj))
				elif checkDSEventConsistency(eventObj):
					# check checkString and fill in creationdate and lastupdate date
					oldEvent = EventEntry.objects.get(id=eventObj.object.pk)
					if (oldEvent.checkString == eventObj.object.checkString):
						# we are ok
						eventObj.object.creator = user
						eventObj.object.creationdate = oldEvent.creationdate
						eventObj.object.lastupdate = datetime.datetime.now()

						try:
							# validate the updated EventEntry 
							eventObj.object.clean_fields()	
							eventObj.save()
							operateList.append({
								'type': eventObj.object.eventStatus,
								"view": view,
								"pk": eventObj.object.pk, 								
								'data': serializers.serialize("json", [oldEvent],
									fields=('oncallPerson', 'eventType', 'startDate',
										'endDate', 'checkString'))})							
							savelist.append('%s, %s' % (eventObj.object.id, 
								eventObj.object.checkString))
						except ValidationError:
							errorlist.append("%d, update failed - validate error %s obj %s" % 
								(eventObj.object.pk, eventObj.object.checkString, eventObj))	
					else:
						errorlist.append("%d, update failed - invalid checkString %s obj %s" % 
							(eventObj.object.pk, eventObj.object.checkString, eventObj))
				else:
					errorlist.append("%d, error updating object %s obj %s" % 
						(eventObj.object.pk, eventObj.object.checkString, eventObj))
		else:
			errorlist.append("invalid view")

		SessionHelper.pushSessionStack(request, SessionHelper.SCHEDULE_UNDOSTACK_NAME, operateList)	
		SessionHelper.clearSessionStack(request, SessionHelper.SCHEDULE_REDOSTACK_NAME)	
		response = {'data': savelist, 'error': errorlist, 'count': count,
			'undoSize': SessionHelper.getSessionStackSize(request, SessionHelper.SCHEDULE_UNDOSTACK_NAME),
			'redoSize': SessionHelper.getSessionStackSize(request, SessionHelper.SCHEDULE_REDOSTACK_NAME)}
		logger.debug('returned result %s' % (response))
		return HttpResponse(content=json.dumps(response), mimetype='application/json')
	else:
		form = BulkEventForm()
		return render_to_response("bulkOperation.html", {'form': form, })


@no_cache
def undo(request, callgroup_id=None):
	return undoOrRedo(request, callgroup_id, 
		SessionHelper.SCHEDULE_UNDOSTACK_NAME, SessionHelper.SCHEDULE_REDOSTACK_NAME)


@no_cache
def redo(request, callgroup_id=None):
	return undoOrRedo(request, callgroup_id, 
		SessionHelper.SCHEDULE_REDOSTACK_NAME, SessionHelper.SCHEDULE_UNDOSTACK_NAME)


def undoOrRedo(request, callgroup_id, srcStackName, targetStackName):
	if (not canAccessCallGroup(request.user, long(callgroup_id))):
		return err403(request)

	user = request.user
	if request.method == 'POST':
		operateList = SessionHelper.popSessionStack(request, srcStackName)
		if (operateList is not None and len(operateList) > 0):
			operateList_n = []
			operateList_r = []
			for operateItem in operateList:
				type = operateItem["type"]
				data = operateItem["data"]
				view = operateItem["view"]
				pk = operateItem["pk"]	
				eventObj = serializers.deserialize("json", data).next()
				if ("0" == type):
					# set defaults
					eventObj.object.callGroup_id = int(callgroup_id)
					eventObj.object.notifyState = 2
					eventObj.object.whoCanModify = 1
					eventObj.object.eventStatus = 1
					if validateNewEvent(eventObj):
						# we are ok to save this new object
						eventObj.object.creator = user
						eventObj.object.creationdate = datetime.datetime.now()
						eventObj.object.lastupdate = datetime.datetime.now()
						eventObj.object.title = 'scheduled_event'
						eventObj.save()
						newOperate = {
							'type': "2",
							'view': view,
							"pk": eventObj.object.pk, 									
							'data': serializers.serialize("json", [eventObj.object],
								fields=('oncallPerson', 'eventType', 'startDate',
									'endDate', 'checkString'))}

						SessionHelper.checkSessionStack(request,
							SessionHelper.SCHEDULE_UNDOSTACK_NAME, pk, eventObj.object.pk)
						SessionHelper.checkSessionStack(request,
							SessionHelper.SCHEDULE_REDOSTACK_NAME, pk, eventObj.object.pk)

						operateList_n.append(newOperate)							
						operateList_r.append(newOperate)
				elif ("1" == type or "2" == type):
					# check checkString and fill in creationdate and lastupdate date
					oldEvent = EventEntry.objects.get(id=eventObj.object.pk)
					if (oldEvent.checkString == eventObj.object.checkString):
						newType = ("1" == type and "1" or "0") 

						eventObj.object.callGroup_id = int(callgroup_id)
						# necessary for easier access in the admin
						eventObj.object.title = 'scheduled_event-%i' % (eventObj.object.pk,)
						eventObj.object.notifyState = 2
						eventObj.object.whoCanModify = 1
						eventObj.object.creator = user
						eventObj.object.creationdate = oldEvent.creationdate
						eventObj.object.lastupdate = datetime.datetime.now()
						eventObj.object.eventStatus = newType

						eventObj.save()

						operateList_n.append({
							'type': newType,
							'view': view, 	
							"pk": eventObj.object.pk, 								
							'data': serializers.serialize("json", [oldEvent],
								fields=('oncallPerson', 'eventType', 
									'startDate', 'endDate', 'checkString'))})	
						operateList_r.append({
							'type': newType,
							'view': view, 	
							'pk': pk, 							
							'data': serializers.serialize("json", [eventObj.object],
								fields=('oncallPerson', 'eventType', 
									'startDate', 'endDate', 'checkString'))})
				request.session[SessionHelper.SCHEDULE_LASTVIEW] = view
			SessionHelper.pushSessionStack(request, targetStackName, operateList_n)
			response = {'operateList': operateList_r, 'error': '', 'undoSize': 
				SessionHelper.getSessionStackSize(request, SessionHelper.SCHEDULE_UNDOSTACK_NAME),
					'redoSize': SessionHelper.getSessionStackSize(
						request, SessionHelper.SCHEDULE_REDOSTACK_NAME)}
		else:
			response = {'operateList': [], 'error': '', 'count': 0,
				'undoSize': SessionHelper.getSessionStackSize(
					request, SessionHelper.SCHEDULE_UNDOSTACK_NAME),
				'redoSize': SessionHelper.getSessionStackSize(
					request, SessionHelper.SCHEDULE_REDOSTACK_NAME)}
		return HttpResponse(content=json.dumps(response), mimetype='application/json')


@no_cache
def getViewInfo(request, callgroup_id=None):
	if (not canAccessCallGroup(request.user, long(callgroup_id))):
		return err403(request)
	if request.method == 'GET':
		try:
			view = request.session[SessionHelper.SCHEDULE_LASTVIEW]
			response = {'view': view}
		except KeyError: 
			response = {'view': ''}	
	else:
		response = {'view': ''}
	return HttpResponse(content=json.dumps(response), mimetype='application/json')


@no_cache
def saveViewInfo(request, callgroup_id=None):
	if (not canAccessCallGroup(request.user, long(callgroup_id))):
		return err403(request)
	if request.method == 'POST':
		view = request.POST['view']
		if checkSchedulerView(view):
			request.session[SessionHelper.SCHEDULE_LASTVIEW] = view
			response = {'view': view}
	else:
		response = {'view': ''}
	return HttpResponse(content=json.dumps(response), mimetype='application/json')


def getPrintableSchedule(request, callgroup_id=None):
	callgroup = None

	if ('OfficeStaff' in request.session['MHL_Users']):
		current_practice = request.session['MHL_Users']['OfficeStaff'].current_practice
		if current_practice.uses_original_answering_serice():
			if (not canAccessCallGroup(request.user, long(callgroup_id))):
				return err403(request)
			else:
				callgroup = CallGroup.objects.get(pk=callgroup_id)
		else:
			if  SessionHelper.CURRENT_CALLGROUP_ID in request.session.keys():
				callgroup_id = request.session[SessionHelper.CURRENT_CALLGROUP_ID]
				callgroup = CallGroup.objects.get(pk=callgroup_id)
			if (not canAccessMultiCallGroup(request.user, long(callgroup_id), current_practice.id)):
				return err403(request)
	else:
		return err403(request)

	if not callgroup:
		return err403(request)

	return export_schedule_to_pdf(request, callgroup)


#add by xlin in 20120528 for bug 598 that before save event check user is in call group TODO
def checkeUserInCallGroup(request, callgroup_id=None):
	userId = request.POST['userId']
	user = User.objects.get(pk=userId)
	member = Provider.objects.filter(user=user)
	group = CallGroup.objects.get(pk=callgroup_id)
	if userId and callgroup_id:
		m = CallGroupMember.objects.filter(call_group=group, member=member)
		if len(m) > 0:
			return HttpResponse(json.dumps('ok'))
		else:
			return HttpResponse(json.dumps('err'))

