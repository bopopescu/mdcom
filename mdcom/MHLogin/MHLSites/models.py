
#-*- coding: utf-8 -*-
from django.db import models

from MHLogin.utils.constants import STATE_CHOICES


class Site(models.Model):
	name = models.CharField(max_length=100)
	address1 = models.CharField(max_length=200)
	address2 = models.CharField(max_length=200, blank=True)
	city = models.CharField(max_length=200, blank=True)
	state = models.CharField(max_length=2, choices=STATE_CHOICES, blank=True)
	zip = models.CharField(max_length=10, blank=True)  # 10 for zip and zip+4
	lat = models.FloatField(blank=True)
	longit = models.FloatField(blank=True)
	#lat_old = models.CharField(max_length=20, blank=True)
	#long_old = models.CharField(max_length=20, blank=True)
	short_name = models.CharField(max_length=30, blank=True)

	def __unicode__(self):
		return self.name

	class Meta:
			ordering = ['name', ]


class Hospital(Site):
	pass

