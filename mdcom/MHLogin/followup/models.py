
from MHLogin.utils.validators import validate_unixDateTime
from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import ugettext_lazy as _
# Create your models here.

PRIORITY_CHOICES = (
	(01, _('High')),
	(05, _('Med')),
	(10, _('Low')),
)


class FollowUpManager(models.Manager):
	def get_query_set(self):
		return super(FollowUpManager, self).get_query_set().filter(deleted=False)


class FollowUps(models.Model):
	user = models.ForeignKey(User)
	done = models.BooleanField(default=False)
	priority = models.IntegerField(choices=PRIORITY_CHOICES, blank=False)
	task = models.CharField(max_length=200, blank=False, null=False)
	creation_date = models.DateTimeField(auto_now_add=True)
	due_date = models.DateTimeField(blank=True, null=True, validators=[validate_unixDateTime])
	completion_date = models.DateTimeField(blank=True, null=True)
	deleted = models.BooleanField(default=False)
	note = models.TextField(null=True, blank=True)

	content_type = models.ForeignKey(ContentType, null=True, blank=True)
	object_id = models.PositiveIntegerField(null=True, blank=True)
	msg_object = generic.GenericForeignKey('content_type', 'object_id')

	all_objects = models.Manager()
	objects = FollowUpManager()
	update_timestamp = models.DateTimeField(auto_now=True)

	def __unicode__(self):
		return "%s" % (self.task)

	def sanitize(self):
		from MHLogin.Administration.data_sanitation.generators import genMessage
		self.note = genMessage(len(self.note))

	def delete(self):
		"""
		Tasks should never be deleted. Rather, set the deleted flag, and
		"""
		self.deleted = True
		self.save()

	class Meta:
		ordering = ['done', 'due_date', 'creation_date', 'priority', 'task', ]
		verbose_name_plural = "Followups"

