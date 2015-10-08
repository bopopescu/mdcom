
import json

from django.http import HttpResponse

from MHLogin.utils.errlib import err403
from MHLogin.MHLUsers.utils import get_fullname_bystr

from models import CallGroupMember
from utils import canAccessCallGroup

def getMembers(request, callgroup_id):
	if (not canAccessCallGroup(request.user, long(callgroup_id))):
		return err403(request)
	#sort by first name 180 Chen Hu
	members = CallGroupMember.objects.filter(call_group__id=callgroup_id).values_list('member__pk', 'member__user__first_name','member__user__last_name','member__user__title').order_by('member__user__last_name')
	members = [(m[0],m[1],m[2],get_fullname_bystr(m[1],m[2],m[3])) for m in members]
	
	return HttpResponse(content=json.dumps(list(members)), mimetype='application/json')
