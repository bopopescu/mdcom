#-*- coding: utf-8 -*-
'''
Created on 2013-5-28

@author: wxin
'''
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.db import models

from MHLogin.MHLUsers.models import MHLUser

class Favorite(models.Model):
	object_type = models.ForeignKey(ContentType, verbose_name="The favorite object type.")
	object_id = models.IntegerField()
	object = generic.GenericForeignKey('object_type', 'object_id')

	owner = models.ForeignKey(MHLUser)

	def __unicode__(self):
		return "%s %s : %s - %d" % (self.owner.first_name, self.owner.last_name, 
					self.object_type.model, self.object_id)

	class Meta():
		db_table = 'MHLFavorite_favorite'
		unique_together = (("object_type", "object_id", "owner"),)
