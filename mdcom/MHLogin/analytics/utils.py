
import datetime
import logging

from django.db.models import Count
from django.conf import settings

from MHLogin.analytics.models import PagerDailySummary, \
	Click2CallDailySummary, MessageDailySummary, InviteDailySummary
from MHLogin.DoctorCom.models import Click2Call_Log, MessageLog, PagerLog, SiteAnalytics
from MHLogin.Invites.models import Invitation, InvitationLog
from MHLogin.utils.mh_logging import get_standard_logger 


# Setting up logging
logger = get_standard_logger('%s/analytics/utils.log' % (settings.LOGGING_ROOT), 
							'analytics.utils', logging.INFO)


def populatePagerSummary(date):
	"""Helper to populate pagerlog summary page

	:param date: Date object
	:type date: datetime.date  
	:returns: plog MHLogin.analytics.models.PagerDailySummary -- the pager log summary 
	:raises: None 
	"""
	# make sure we don't save if date is today since we need to have a full day's worth of data
	plog = PagerDailySummary()
	plog.dateoflog = date
	enddate = date + datetime.timedelta(days=1)  # next day

	#plog.countSuccess = PagerLog.objects.timestamp__range(date,enddate).aggregate(Count('timestamp'))
	qp = PagerLog.objects.filter(timestamp__range=(date, enddate)).aggregate(countSucc=Count('id'))
	if 'countSucc' in qp:
		plog.countSuccess = qp['countSucc']
	else:
		plog.countSuccess = 0
	logger.debug('%d: for %s-%s' % (plog.countSuccess, date.strftime('%B %d, %Y'),
								enddate.strftime('%B %d, %Y')))
	plog.save()

	return plog


def populateMessageSummary(date):
	"""Helper to populate message summary page

	:param date: Date object
	:type date: datetime.date  
	:returns: mlog MHLogin.analytics.models.MessageDailySummary -- the message summary 
	:raises: None 
	"""

	# make sure we don't save if date is today since we need to have a full day's worth of data
	mlog = MessageDailySummary()
	mlog.dateoflog = date
	enddate = date + datetime.timedelta(days=1)  # next day
	qm = MessageLog.objects.filter(timestamp__range=(date, enddate)).\
			filter(success__gte=1).aggregate(countSucc=Count('id'))
	qm2 = MessageLog.objects.filter(timestamp__range=(date, enddate)).\
			filter(success__lte=0).aggregate(countFail=Count('id'))
	if 'countSucc' in qm:
		mlog.countSuccess = qm['countSucc']
	else:
		mlog.countSuccess = 0
	if 'countFail' in qm2:
		mlog.countFailure = qm2['countFail']
	else:
		mlog.countFailure = 0

	logger.debug('Succ %d; Fail %d;for date %s-%s' % (mlog.countSuccess, 
		mlog.countFailure, date.strftime('%B %d, %Y'), enddate.strftime('%B %d, %Y')))
	mlog.save()
	return mlog


def populateClick2CallSummary(date):
	"""Helper to populate click2call summary page

	:param date: Date object
	:type date: datetime.date  
	:returns: clog MHLogin.analytics.models.Click2CallDailySummary -- the message summary 
	:raises: None 
	"""

	# make sure we don't save if date is today since we need to have a full day's worth of data
	clog = Click2CallDailySummary()
	clog.dateoflog = date
	enddate = date + datetime.timedelta(days=1)  # next day
	qc = Click2Call_Log.objects.filter(timestamp__range=(date, enddate)).\
			filter(connected=True).aggregate(countSucc=Count('id'))
	qc2 = Click2Call_Log.objects.filter(timestamp__range=(date, enddate)).\
			filter(connected=False).aggregate(countFail=Count('id'))
	if 'countSucc' in qc:
		clog.countSuccess = qc['countSucc']
	else:
		clog.countSuccess = 0
	if 'countFail' in qc2:
		clog.countFailure = qc2['countFail']
	else:
		clog.countFailure = 0

	logger.debug('Succ %d; Fail %d;for date %s-%s' % (clog.countSuccess, 
		clog.countFailure, date.strftime('%B %d, %Y'), enddate.strftime('%B %d, %Y')))
	clog.save()
	return clog


def populateInviteSummary(date):
	"""Helper to populate invite summary page

	:param date: Date object
	:type date: datetime.date  
	:returns: ilog MHLogin.analytics.models.InviteDailySummary -- the invite summary 
	:raises: None 
	"""

	# make sure we don't save if date is today since we need to have a full day's worth of data
	ilog = InviteDailySummary()
	ilog.dateoflog = date
	enddate = date + datetime.timedelta(days=1)  # next day
	# we get raw totals for Invitations and InvitationLogs by date range
	qi = Invitation.objects.filter(requestTimestamp__range=(date, enddate)).\
			aggregate(countSucc=Count('id'))
	qilog = InvitationLog.objects.filter(requestTimestamp__range=(date, enddate)).\
			aggregate(countSucc=Count('id'))
	if 'countSucc' in qi:
		ilog.countTotal = qi['countSucc']
	else:
		ilog.countTotal = 0
	if 'countSucc' in qilog:
		ilog.countTotal = ilog.countTotal + qilog['countSucc']
	else:
		ilog.countTotal = ilog.countTotal + 0
	# next we get how many invites are canceled -- based on responseTimestamp date, 
	# not requestTimestamp date
	qi2 = InvitationLog.objects.filter(responseTimestamp__range=(date, enddate)).\
			exclude(canceller=None).aggregate(countFail=Count('id'))
	if 'countFail' in qi2:
		ilog.countCanceled = qi2['countFail']
	else:
		ilog.countCanceled = 0

	logger.debug('Succ %d; Fail %d;for date %s-%s' % (ilog.countTotal, ilog.countCanceled, 
		date.strftime('%B %d, %Y'), enddate.strftime('%B %d, %Y')))
	ilog.save()
	return ilog


def extract_start_end_dates(start, end, fmt="%m-%d-%Y"):
	""" Given start end dates in format %m-%d-%Y" validate and return python tuple
	(start,end) or null if validation fails
	"""
	rc = (None, None)
	try:
		if start and end:
			start_date = datetime.datetime.strptime(start, fmt)
			end_date = datetime.datetime.strptime(end, fmt)
			rc = (start_date, end_date)
	except ValueError, err:
		logger.warn("Value error decoding dates %s, %s, error: %s" % (start, end, err))

	return rc


def getSiteAnalyticsTopThree(date):
	"""Process getSiteAnalyticsTopThree view request:  

	:param date: date
	:returns: SiteAnalytics -- array of the top three  
	:raises: None 
	"""
	# tini to test
	siteForDate = SiteAnalytics.objects.filter(dateoflog=date)
	# if results are 3 records or less, we return them; otherwise, we order and filter out top 3
	if (siteForDate.count() > 0):
		siteTop3 = SiteAnalytics.objects.filter(dateoflog=date).extra(
					select={'totalForSite': "countPage+countMessage+countClick2call"})
		siteTop3 = siteTop3.extra(order_by=['-totalForSite'])[:3]
		return siteTop3
	else:
		return []

