
from django.db import models
from MHLogin.MHLUsers.models import Provider, MHLUser
from MHLogin.MHLPractices.models import PracticeLocation

from django.utils.translation import ugettext_lazy as _
from MHLogin.utils.constants import ACCEPT_CALL_GROUP_PENDING
#member's of call group status in practice
ALTPROVIDER = (
	(1, _('Associated')),
    (2, _('Alternate')),
)
NUMBER_SELECTION = (
	(2, 'Two'),
    (3, 'Three'),
    (4, 'Four'),
    (5, 'Five'),
    (6, 'Six'),
    (7, 'Seven'),
    (8, 'Eight'),

)


class CallGroup(models.Model):
	"""
		Lst of all groups - they are Many to Many to Practice Locations, once call group can be in mult locations
	"""
	#what practice this entry call group belongs to
	description = models.CharField(max_length=100, blank=True)
#removed inna-
#	specialty = models.CharField(max_length=100, blank=True) # blanks are allowed for single specialty practice, UI check
	team = models.CharField(max_length=200, blank=True) #blanks allowed only for backwards compatibility ,UI will not allow
	number_selection = models.IntegerField(choices=NUMBER_SELECTION, null=True, blank=True)#blanks allowed only for backwards compatibility ,UI will not allow
	
	def __unicode__(self):
		return self.description
		
class Specialty(models.Model):
	"""
		Lst of all groups - they are Many to 1 to Practice Locations, specialty is tied to ONE location
	"""
	#what practice this entry call group belongs to
	name = models.CharField(max_length=100) #no NULL or Blanks allowed, name read in IVR
	#specialty can belong to only ONE location
	practice_location = models.ForeignKey(PracticeLocation, related_name="PracticeLocationForSpecialty") #no NULLS
	#specialty can have mutiple "teams" ie call groups associated with it
	call_groups = models.ManyToManyField('MHLCallGroups.CallGroup', null=True, blank=True, related_name="SpecialtyCallGroup", verbose_name=("List of all of the call groups for this practice"))
	number_selection = models.IntegerField(choices=NUMBER_SELECTION)#no NULL
	
	
	def __unicode__(self):
		return self.name

#a foreign key to Provider, his status( full rights ot alternates) and what group number he belongs to
class CallGroupMember(models.Model):
	"""
		List of providers on call, they are grouped by call group
	"""
	#what practice this entry call group belongs to
	call_group = models.ForeignKey(CallGroup, null=True, blank=True,
					related_name='call_group_member')
	member = models.ForeignKey(Provider, null=True, blank=True,
					related_name='member_provider')

	alt_provider = models.IntegerField(choices=ALTPROVIDER)

	class Meta:
		verbose_name = "Call Group Member"
		ordering = ["call_group"]
		unique_together = (('call_group', 'member',),)

	def __unicode__(self):
		return "%s %s" % (self.member.user.first_name, self.member.user.last_name)

#add by xlin 121122 for pending
class CallGroupMemberPending(models.Model):
	from_user = models.ForeignKey(MHLUser, null=True, blank=True, related_name='from_user_provider')
	to_user = models.ForeignKey(Provider, null=True, blank=True, related_name='to_user_provider')
	practice = models.ForeignKey(PracticeLocation, null=True, blank=True, related_name='practice')
	call_group = models.ForeignKey(CallGroup, null=True, blank=True, related_name='member_provider')
	created_time = models.DateTimeField()
	resent_time = models.DateTimeField(null=True)
	accept_status = models.IntegerField(choices=ACCEPT_CALL_GROUP_PENDING, default=0)
