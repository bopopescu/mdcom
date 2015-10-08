
from django.db import models


class PagerDailySummary(models.Model):
	"""PagerDailySummary class database model 
	"""
	dateoflog = models.DateField(auto_now=False, auto_now_add=False, primary_key=True)
	countSuccess = models.IntegerField()
	calcdate = models.DateTimeField(auto_now=True, editable=False)


class Click2CallDailySummary(models.Model):
	"""Click2CallDailySummary class database model 
	"""
	dateoflog = models.DateField(auto_now=False, auto_now_add=False, primary_key=True)
	countSuccess = models.IntegerField()
	countFailure = models.IntegerField()
	calcdate = models.DateTimeField(auto_now=True, editable=False)


class MessageDailySummary(models.Model):
	"""MessageDailySummary class database model 
	"""
	dateoflog = models.DateField(auto_now=False, auto_now_add=False, primary_key=True)
	countSuccess = models.IntegerField()
	countFailure = models.IntegerField()
	calcdate = models.DateTimeField(auto_now=True, editable=False)


class InviteDailySummary(models.Model):
	"""InviteDailySummary class database model 
	"""
	dateoflog = models.DateField(auto_now=False, auto_now_add=False, primary_key=True)
	countTotal = models.IntegerField()
	countCanceled = models.IntegerField()
	calcdate = models.DateTimeField(auto_now=True, editable=False)

