
import datetime

from django.db import models
from django.db.models import F

from MHLogin.MHLSites.models import Site
from MHLogin.MHLUsers.models import MHLUser

from MHLogin.utils.fields import MHLPhoneNumberField
from django.utils.translation import ugettext_lazy as _

# I'd like to migrate to using this table for DoctorCom delivery preferences, in
# the interest of trying to properly isolate/segregate Django applications in
# the way we should have been doing from the start.
#class DoctorCom_Preferences(models.Model):
#	user = models.ForeignKey(User)
#
#	# Call forwarding preferences
#	forward_mobile = models.BooleanField(default=True)
#	forward_office = models.BooleanField(default=False)
#	forward_other = models.BooleanField(default=False)
#	forward_vmail = models.BooleanField(default=False)
#
#	# Message delivery preferences
#	message_delivery_sms = models.BooleanField(default=False)
#	message_delivery_email = models.BooleanField(default=False)
#	message_delivery_voice = models.BooleanField(default=False)
#
#	# Message notification preferences
#	message_notification_sms = models.BooleanField(default=True)
#	message_notification_email = models.BooleanField(default=True)
#
#	# Voicemail notification preferences
#	vmail_notification_sms = models.BooleanField(default=True)
#	vmail_notification_email = models.BooleanField(default=True)


#class Message(models.Model):
	# Recipients are listed here, as well as in the MessageLog objects. The
	# reason for this is because we want to preserve the sender's exact
	# message sending intentions.
#	user_recipients = models.ManyToManyField(MHLUser, related_name="Message recipients", editable=False)
	#group_recipients = models.ManyToManyField(User, related_name="Message recipients")

#	sender = models.ForeignKey(MHLUser, related_name="Message sender", editable=False)
#	body = models.TextField(editable=False)
#	timestamp = models.DateTimeField(auto_now_add=True, editable=False)

	# this field will be used as message IDs if we implement message replies
#	reply_id = models.CharField(max_length=10, editable=False)

	##def __unicode__(self):
	#	return self.body


class MessageTemp(models.Model):
	"""This is a temporary message table that holds messages while end-users are
	working on them. We should write a crontab script that removes messages
	associated with expired sessions."""

	# session data
	#session = models.ForeignKey(Session) # Unfortunately, as far as I can tell, 
	#there's no easy way to get at this.
	user = models.ForeignKey(MHLUser)

	# Recipients are listed here, as well as in the MessageLog objects. The
	# reason for this is because we want to preserve the sender's exact
	# message sending intentions.
	user_recipients = models.ManyToManyField(MHLUser, 
			related_name="temp_user_recipients", blank=True, null=True)
	#group_recipients = models.ManyToManyField(User, related_name="Message recipients")

	body = models.CharField(max_length=140, blank=True)
	timestamp = models.DateTimeField(auto_now=True)

	def __unicode__(self):
		return self.body

	class Meta:
		db_table = 'DoctorCom_messagetemp'

TWILIO_SMS_STATUS_CHOICES = (
	('SE', _('Sending')),
	('SU', _('Success')),
	('FA', _('Fail')),
)


class MessageLog(models.Model):
	message = models.ForeignKey(MessageTemp, editable=False, related_name="messagelog_message")
	message_recipient = models.ForeignKey(MHLUser, editable=False, related_name="messagelog_recip")

	# Was the message successfully sent?
	success = models.BooleanField(editable=False)
	# The following field is for message confirmation numbers -- currently,
	# a set of numbers. Unfortunately, errors from the SMS service come back
	# as strings. If the message fails to be sent, we will store the error
	# in this field. Note that the following field is for Convergent Mobile SMS
	# messaging.
	confirmation = models.CharField(max_length=250, blank=True, editable=False)

	# Twilio SMS values
	twilio_sid = models.CharField(max_length=64, blank=True, editable=False, db_index=True)
	twilio_status = models.CharField(max_length=2, choices=TWILIO_SMS_STATUS_CHOICES)

	body_fragment = models.CharField(max_length=200, blank=True, editable=False)
	resend_of = models.ForeignKey('self', null=True)  # Keep track of message re-sends via this field
	current_site = models.ForeignKey(Site, null=True, blank=True, related_name="messager_current_site")

	tx_number = MHLPhoneNumberField(editable=False)  # we keep this copy since the Sender can be deleted or change their cell number
	rx_number = MHLPhoneNumberField(editable=False)  # we keep this copy since the Recipient can be deleted or change their cell number
	tx_name = models.CharField(max_length=50, editable=False)  # '' or change their name
	rx_name = models.CharField(max_length=50, editable=False)  # '' or change their name

	# Timestamp for when this message send is attempted.
	timestamp = models.DateTimeField(auto_now_add=True, editable=False)

	def save(self, *args, **kwargs):
		# if new record and current_site is defined and not 0, we add count to siteAnalytics
		if ((not self.id) and (self.current_site > 0)):
			try:
				siteStat = SiteAnalytics.objects.get(dateoflog=datetime.date.today(), 
					site=self.current_site)
			except SiteAnalytics.DoesNotExist:
				siteStat = SiteAnalytics(dateoflog=datetime.date.today(), 
					site=self.current_site, countPage=0, countMessage=0, countClick2Call=0)
				siteStat.save()
			siteStat.countMessage = F('countMessage') + 1
			siteStat.save()
		super(MessageLog, self).save(*args, **kwargs)

	def __unicode__(self):
		return "Message fragment from %s to %s" % (self.tx_name, self.rx_name)

	class Meta:
		db_table = 'DoctorCom_messagelog'


# The click2call session and logs are separated so that we can 1) provide
# greater protection to the log, and 2) allow the session table to express
# additional information if it's needed in the future.
CLICK2CALL_SOURCES = (
	('IVR', _('IVR')),
	('APP', _('Smartphone app')),
	('WEB', _('Website')),
)


class Click2Call_Log(models.Model):
	callid = models.CharField(max_length=34)
	caller = models.ForeignKey(MHLUser, related_name="click2call_log_caller")
	caller_number = MHLPhoneNumberField(blank=True)
	called_user = models.ForeignKey(MHLUser, blank=True, null=True, related_name="click2call_log_called")
	called_number = MHLPhoneNumberField(blank=True)
	source = models.CharField(max_length=3, choices=CLICK2CALL_SOURCES)
	connected = models.BooleanField(default=False)

	current_site = models.ForeignKey(Site, null=True, blank=True, related_name="click2caller_current_site")

	timestamp = models.DateTimeField(auto_now=True, editable=False)

	def save(self, *args, **kwargs):
		# if new record and current_site is defined and not 0, we add count to siteAnalytics
		if ((not self.id) and (self.current_site > 0)):
			try:
				siteStat = SiteAnalytics.objects.get(dateoflog=datetime.date.today(), site=self.current_site)
			except SiteAnalytics.DoesNotExist:
				siteStat = SiteAnalytics(dateoflog=datetime.date.today(), site=self.current_site, 
					countPage=0, countMessage=0, countClick2Call=0)
				siteStat.save()
			siteStat.countClick2Call = F('countClick2Call') + 1
			siteStat.save()
		super(Click2Call_Log, self).save(*args, **kwargs)

	class Meta:
		db_table = 'DoctorCom_click2call_log'


class Click2Call_ActionLog(models.Model):
	click2call_log = models.ForeignKey(Click2Call_Log)
	action = models.CharField(max_length=50)

	class Meta:
		db_table = 'doctorcom_click2call_actionlog'


class PagerLog(models.Model):
	pager = models.ForeignKey(MHLUser, related_name="pagerlog_pager", null=True)
	paged = models.ForeignKey(MHLUser, related_name="pagerlog_paged")
	current_site = models.ForeignKey(Site, null=True, blank=True, related_name="pager_current_site")

	callback = MHLPhoneNumberField()

	timestamp = models.DateTimeField(auto_now=True, editable=False)

	def save(self, *args, **kwargs):
		# if new record and current_site is defined and not 0, we add count to siteAnalytics
		if ((not self.id) and (self.current_site > 0)):
			try:
				siteStat = SiteAnalytics.objects.get(dateoflog=datetime.date.today(), 
						site=self.current_site)
			except SiteAnalytics.DoesNotExist:
				siteStat = SiteAnalytics(dateoflog=datetime.date.today(), site=self.current_site, 
					countPage=0, countMessage=0, countClick2Call=0)
				siteStat.save()
			siteStat.countPage = F('countPage') + 1
			siteStat.save()
		super(PagerLog, self).save(*args, **kwargs)

	class Meta:
		db_table = 'DoctorCom_pagerlog'


class SiteAnalytics(models.Model):
	dateoflog = models.DateField(auto_now=False, auto_now_add=False)
	site = models.ForeignKey(Site, null=True)
	countPage = models.IntegerField()
	countMessage = models.IntegerField()
	countClick2Call = models.IntegerField()
	lastUpdate = models.DateTimeField(auto_now=True, editable=False)

	class Meta:
		db_table = 'DoctorCom_siteanalytics'
		unique_together = ("dateoflog", "site")
		verbose_name_plural = "Site Analytics"

