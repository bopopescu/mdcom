
from MHLogin.MHLUsers.models import OfficeStaff, Administrator, Office_Manager
from MHLogin.MHLPractices.models import PracticeLocation

from models import CallGroupMember
from MHLogin.MHLCallGroups.models import Specialty


def isCallGroupMember(user, callgroup_pk):
	"""
	Checks to see if the passed user is a member of the passed callgroup.
	
	Returns True if the user is a call group member.
	Returns False if the user is not.
	"""
	return CallGroupMember.objects.filter(call_group__pk=callgroup_pk, member__pk=user.pk).exists()

def isCallGroupStaff(user, callgroup_pk):
	"""
	Checks to see if the passed user is an officeStaff member of a practice that
	is served by the passed callgroup.
	
	Returns True if the user is a call group practice staffer.
	Returns False if the user is not.
	"""
	practice_qs = PracticeLocation.objects.filter(call_group__pk=callgroup_pk)
	return OfficeStaff.objects.filter(user__pk=user.pk, practices__in=practice_qs).exists()

def isCallGroupManager(user, callgroup_pk):
	practice_qs = PracticeLocation.objects.filter(call_group__pk=callgroup_pk)
	return Office_Manager.objects.filter(user__user__pk=user.pk, user__practices__in=practice_qs).exists()


def canAccessCallGroup(user, callgroup):
	"""
	Checks to see if the passed django.contrib.auth.models.User is an 
	officeStaff member of a practice that is served by the passed callgroup.
	Note that the callgroup argument may be the integer callgroup pk, or the actual callgroup object itself.
	
	Returns True if the user is a call group practice staffer.
	Returns False if the user is not.
	"""
	if (Administrator.objects.filter(user__pk=user.pk).exists()):
		# Allow administrators in.
		return True
	if (callgroup.__class__.__name__ != 'long'):
		callgroup = callgroup.pk
	return isCallGroupManager(user, callgroup)


def isMultiCallGroupManager(user, callgroup, practice_id):
	practice_list = []
	practice_qs = PracticeLocation.objects.filter(pk=practice_id, call_group=None)
	for practice in practice_qs:
		for cg in practice.call_groups.all():
			if cg and cg.id == callgroup and practice_id not in practice_list:
				practice_list.append(practice_id)
				break

	specialties = Specialty.objects.filter(practice_location__pk=practice_id).order_by('name')
	for specialty in specialties:
		for cg in specialty.call_groups.all().order_by('team'):
			if cg and cg.id == callgroup and practice_id not in practice_list:
				practice_list.append(practice_id)
				break
	return Office_Manager.objects.filter(user__user__pk=user.pk, user__practices__pk__in=practice_list).exists()

def canAccessMultiCallGroup(user, callgroup, practice_id):
	if (Administrator.objects.filter(user__pk=user.pk).exists()):
		# Allow administrators in.
		return True
	if (callgroup.__class__.__name__ != 'long'):
		callgroup = callgroup.pk
	return isMultiCallGroupManager(user, callgroup, practice_id)

def checkMultiCallGroupId(practice_id, callgroup_id):
	"""
	If calllgroup_id is None, get the default callgroup id
	
	Return callgroup if if available, else None returned.
	"""
	if not callgroup_id or (callgroup_id == '0'):
		try:
			practice = PracticeLocation.objects.get(id=practice_id)
		except:
			raise PracticeLocation.DoesNotExist
		call_groups = practice.call_groups.all()
		if len(call_groups):
			return call_groups[0].id

		specialties = Specialty.objects.filter(practice_location__pk=practice_id)
		for specialty in specialties:
			call_groups = specialty.call_groups.all()
			if len(call_groups):
				return call_groups[0].id
	else:
		return callgroup_id
