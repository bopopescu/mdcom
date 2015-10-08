from django.db import models

from MHLogin.MHLUsers.models import MHLUser
from MHLogin.utils.fields import MHLPhoneNumberField
class SenderLookup(models.Model):
	# "Owner" of this lookup table entry -- original outbound message sender
	user = models.ForeignKey(MHLUser, related_name="User whose mobile phone this mapping belongs to")
	
	# Person/number to which this mapping points -- inbound reply messages will
	# be from this person
	mapped_user = models.ForeignKey(MHLUser, null=True, related_name='User for whom this mapping points to')
	
	# The number that the mapping uses.
	number = MHLPhoneNumberField(blank=True, db_index=True)
	
	timestamp = models.DateTimeField(auto_now=True)
	
	def __unicode__(self):
		return 'SMS Map between %s %s and %s %s'%(self.user.first_name, self.user.last_name, self.mapped_user.first_name, self.mapped_user.last_name)
	
	class Meta:
		unique_together = (('mapped_user', 'number'),)

