
import traceback  # DEBUG

from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from MHLogin.MHLCallGroups.models import CallGroup
from MHLogin.utils.mh_logging import get_standard_logger 
from MHLogin.utils.admin_utils import mail_admins


# Setting up logging
logger = get_standard_logger('%s/MHLCallGroups/Scheduler/models.log' % 
	(settings.LOGGING_ROOT), 'MHLCallGroups.Scheduler.models', settings.LOGGING_LEVEL)


EVENT_TYPE_CHOICES = (
	('0', _('Medical on-call')),
	('1', _('Administrative on-call')),
)

ONCALL_LEVEL_CHOICES = (
	('0', _('Primary')),
	('1', _('Secondary')),
)

ONCALL_STATUS_CHOICES = (
	('0', _('unconfirmed')),
	('1', _('tentative')),
	('2', _('confirmed')),
)

# decides if the event is to be shown or not depending on status
EVENT_STATUS_CHOICES = (
	('0', _('deleted')),
	('1', _('scheduled')),
)

# decides when an event is scheduled, to notify the on calls of schedule and/or changes
EVENT_NOTIFICATION_CHOICES = (
	('0', _('no notification')),
	('1', _('notify primary')),
	('2', _('notify all')),
)

# decides if the event is scheduled, who can modify the EventEntry
EVENT_MODIFICATION_CHOICES = (
	('0', _('OfficeManagerOnly')),
	('1', _('OfficeManagerAndPrimary')),
	('2', _('Everyone')),
)


class EventEntryManager(models.Manager):
	def get_query_set(self):
		return super(EventEntryManager, self).get_query_set().filter(eventStatus='1')


# actual event scheduled - we use timezone of the OFFICE, so we don't store it in the eventEntry
class EventEntry(models.Model):
	"""
		event entry represents scheduled events from the scheduler e.g. who is on call when
	"""
	id = models.AutoField(primary_key=True)
	callGroup = models.ForeignKey(CallGroup)
	title = models.CharField(max_length=255)
	startDate = models.DateTimeField(auto_now=False, auto_now_add=False)
	endDate = models.DateTimeField(auto_now=False, auto_now_add=False)
	eventType = models.CharField(max_length=1, choices=EVENT_TYPE_CHOICES)
	oncallPerson = models.ForeignKey(User, related_name="oncall")
	oncallLevel = models.CharField(max_length=1, choices=ONCALL_LEVEL_CHOICES, default='0')
	oncallStatus = models.CharField(max_length=1, choices=ONCALL_STATUS_CHOICES, default='0')
	creator = models.ForeignKey(User)  # should be OfficeManager
	creationdate = models.DateTimeField(auto_now_add=True)
	lastupdate = models.DateTimeField(auto_now=True)
	eventStatus = models.CharField(max_length=1, choices=EVENT_STATUS_CHOICES)
	# do we need to store any extra display attributes such as color?
	notifyState = models.CharField(max_length=1, choices=EVENT_NOTIFICATION_CHOICES)
	whoCanModify = models.CharField(max_length=1, choices=EVENT_MODIFICATION_CHOICES)
	checkString = models.CharField(max_length=10, blank=True)

	# Custom manager
	objects = EventEntryManager()
	all_objects = models.Manager()

	def delete(self):
		"""
		Disallow direct deletion of this object. Also, report all calls to delete 
		on this object as a DEBUG step.
		"""
		self.eventStatus = 0
		self.save()

		# DEBUG
		context = {
			'call_stack': ''.join(traceback.format_stack()),
			'event': self,
			'server_addr': settings.SERVER_ADDRESS,
		}
		body = render_to_string('MHLCallGroups/Scheduler/email_delete_event.txt', context)
		mail_admins(_('Event Deletion Attempt!'), body)

	def __unicode__(self):
		return self.title

	def __repr__(self):
		# attribute's value is found using exec(''.join(['self.', str(key)]))
		keys = self.__dict__.keys()
		# Strip out 'id' from keys so that it can be added at the start.
		keys.remove('id')

		# Strip out the _state key
		keys.remove('_state')

		attributes = [''.join([key, ':', str(self.__dict__[key]), ',']) for key in keys]
		attributes.insert(0, self.__class__.__name__)
		attributes.insert(1, '(')
		attributes.insert(2, ''.join(['id:', str(self.id), ',']))
		attributes.append(')')
		return ''.join(attributes)


# questions:
# do we need to handle recurring oncall scheduling? yes, eventually
# e.g. every x days or week - same doctor is on call?
# if so, we may need a RecurringEntry class

# this is going directly to callgroup so we don't need a separate scheduler class
# there is one per office - this keeps the office calendar schedule
#Class Scheduler(models.Model):
#	id = models.AutoField(primary_key=True)  # do we need ID or will the officeID do?
#	officeId = models.ForeignKey(Office)
#	events = models.ManyToManyField(EventEntry, blank=True)

# this denotes default preferences for the scheduler e.g. who can modify, state notification
#Class Preferences(models.Model):
#	pass

