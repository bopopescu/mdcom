
import json

from django.http import HttpResponse

from MHLogin.utils.errlib import err403
from MHLogin.MHLUsers.utils import get_fullname_bystr

from models import CallGroupMember, CallGroupMemberPending
from utils import canAccessCallGroup,checkMultiCallGroupId, canAccessMultiCallGroup
from MHLogin.MHLPractices.models import PracticeLocation

def getMembers(request, practice_id, callgroup_id):
	callgroup_id = checkMultiCallGroupId(practice_id, callgroup_id)
	if (not canAccessMultiCallGroup(request.user, long(callgroup_id), practice_id)):
		return err403(request)
	#sort by first name 180 Chen Hu
	members = list(CallGroupMember.objects.filter(call_group__id=callgroup_id).values_list('member__pk', 'member__user__first_name', 'member__user__last_name','member__user__title').order_by('member__user__last_name'))
	members = [(m[0],m[1],m[2],'drop',get_fullname_bystr(m[1],m[2],m[3])) for m in members]

	pendings = list(CallGroupMemberPending.objects.filter(call_group__id=callgroup_id,accept_status=0).values_list('to_user__pk', 'to_user__user__first_name', 'to_user__user__last_name', 'to_user__user__title').order_by('to_user__user__last_name'))
	pendings = [(p[0],p[1],p[2],'disabled',get_fullname_bystr(p[1],p[2],p[3])) for p in pendings]
	members.extend(pendings)
	
	return HttpResponse(content=json.dumps(members), mimetype='application/json')
