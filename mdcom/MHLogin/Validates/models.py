from django.contrib.auth.models import User
from django.db import models

VALIDATION_TYPE_CHOICES = (
	(1, 'E-Mail'),
	(2, 'Mobile Phone'),
	(3, 'Pager'),
)

class Validation(models.Model):
	code = models.CharField(max_length=8, blank=False, null=False)
	type = models.IntegerField(choices=VALIDATION_TYPE_CHOICES)	
	applicant = models.CharField(max_length=200, blank=False, null=False)
	recipient = models.CharField(max_length=200, blank=False, null=False)
	is_active = models.BooleanField(default=True)
	sent_time = models.DateTimeField(auto_now_add=True)
	validate_locked_time = models.DateTimeField(null=True)
	validate_success_time = models.DateTimeField(null=True)

	def __unicode__(self):
		return 'Validation for %s : %s - %s, %s'%(self.recipient, self.applicant, self.type, self.sent_time)

class ValidationLog(models.Model):
	validation = models.ForeignKey(Validation, null=True, blank=True)
	code_input = models.CharField(max_length=8, blank=False, null=False)
	validate_time = models.DateTimeField()

	def __unicode__(self):
		return 'Validation log for %s : %s - %s'%(self.pk, self.validation.id, self.validate_time)