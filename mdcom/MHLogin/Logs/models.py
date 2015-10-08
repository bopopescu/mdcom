
from django.contrib.auth.models import User
from django.db import models


class Event(models.Model):
	timestamp = models.DateTimeField(auto_now=True)

	class Meta:
		abstract = True

	# The below is a hack workaround for an issue with Django. If you set a
	# model field as editable=False, it does NOT appear in the admin interface.
	# By over-riding the method with a non-standard argument to get it to save,
	# we can protect it while still displaying the contents.
	def save(self, edit=False):
		if (edit):
			super(models.Model, self).save()

	# The following are NOT allowed
	def delete(self):
		pass

	def __unicode__(self):
		return self.timestamp


class LoginEvent(Event):
	username = models.CharField(max_length=50)
	remote_ip = models.CharField(max_length=15)
	success = models.BooleanField()

	# for successful logins only
	user = models.ForeignKey(User, null=True)

	# FIXME: CustomInit is a hack to work around issues with the admin site and
	# over-riding the __init__ method.
	def customInit(self, username=None, remote_ip=None, success=False, user=None):
		self.username = username
		self.remote_ip = remote_ip
		self.success = success
		self.user = user
		self.save(edit=True)

	# The below is a hack workaround for an issue with Django. If you set a
	# model field as editable=False, it does NOT appear in the admin interface.
	# By over-riding the method with a non-standard argument to get it to save,
	# we can protect it while still displaying the contents.
	def save(self, edit=False):
		if (edit):
			super(LoginEvent, self).save()

	# The following are NOT allowed
	def delete(self):
		pass

	def __unicode__(self):
		success = "Successful"
		if (not self.success):
			success = "Unsuccessful"
		return "%s login attempt by %s" % (success, self.username)


class LogoutEvent(Event):
	user = models.ForeignKey(User)

	# FIXME: CustomInit is a hack to work around issues with the admin site and
	# over-riding the __init__ method.
	def customInit(self, user=None):
		self.user = user
		self.save(edit=True)

	# The below is a hack workaround for an issue with Django. If you set a
	# model field as editable=False, it does NOT appear in the admin interface.
	# By over-riding the method with a non-standard argument to get it to save,
	# we can protect it while still displaying the contents.
	def save(self, edit=False):
		if (edit):
			super(LogoutEvent, self).save()

	# The following are NOT allowed
	def delete(self):
		pass

	def __unicode__(self):
		return "Logout by %s" % (self.user.username)


class LogFiles(LogoutEvent):  # inherit from a non-abstract model
	""" Empty proxy model so we show up in admin then customize our admin interface """
	class Meta:
		proxy = True
		verbose_name = 'Log File'
		verbose_name_plural = 'Log Files'

