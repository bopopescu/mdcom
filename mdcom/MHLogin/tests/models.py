from django.db import models

from MHLogin.DoctorCom.models import Click2Call_Log, MessageLog, PagerLog
from MHLogin.MHLUsers.models import MHLUser


class TwilioCallGatherTest(models.Model):
	tester = models.ForeignKey(MHLUser)
	callid = models.CharField(max_length=34, blank=True, null=True)

	debug_data = models.TextField()
	success = models.CharField(max_length=100)

	timestamp = models.DateTimeField(auto_now_add=True, editable=False)


class TwilioRecordTest(models.Model):
	tester = models.ForeignKey(MHLUser)
	callid = models.CharField(max_length=34, blank=True, null=True)
	recordingurl = models.TextField(blank=True, null=True)

	debug_data = models.TextField()

	timestamp = models.DateTimeField(auto_now_add=True, editable=False)


class ConvergentTest(models.Model):
	tester = models.ForeignKey(MHLUser)
	message = models.TextField(blank=True)
	confirmations = models.CharField(max_length=250)

	success = models.IntegerField(default=0)  # 0 for fail/unknown, 1 for success.

	timestamp = models.DateTimeField(auto_now_add=True, editable=False)


class DoctorComC2CTest(models.Model):
	tester = models.ForeignKey(MHLUser)
	call = models.ForeignKey(Click2Call_Log, null=True)

	success = models.IntegerField(default=0)  # 0 for fail/unknown, 1 for success.

	timestamp = models.DateTimeField(auto_now_add=True, editable=False)


class DoctorComPagerTest(models.Model):
	tester = models.ForeignKey(MHLUser)
	page = models.ForeignKey(PagerLog, null=True)

	success = models.IntegerField(default=0)  # 0 for fail/unknown, 1 for success.

	timestamp = models.DateTimeField(auto_now_add=True, editable=False)


class DoctorComSMSTest(models.Model):
	tester = models.ForeignKey(MHLUser)
	message = models.ForeignKey(MessageLog, null=True)

	success = models.IntegerField(default=0)  # 0 for fail/unknown, 1 for success.

	timestamp = models.DateTimeField(auto_now_add=True, editable=False)

