
"""
Tech Admins for models that do not fit into a category or project admin.py file.
"""

from django.contrib.auth.models import Group, User
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION

from MHLogin.Administration.tech_admin.forms import TechAdminGroupForm
from MHLogin.Administration.tech_admin.options import TechAdmin, TechMHLUserAdmin
from MHLogin.Administration.tech_admin.sites import tech_admin_site


class GroupAdmin(TechAdmin):
	filter_horizontal = ['permissions']
	form = TechAdminGroupForm

	techadmin_queryset = lambda self, request, qs: request.user.groups.all()


class LogEntryAdmin(TechAdmin):
	list_display = ('user', 'action_time', 'content_type', 'object_id', 
				'object_repr', '_get_action_flag', 'change_message')

	def _get_action_flag(self, obj):
		action = "Other (%d)" % obj.action_flag
		if (obj.action_flag == ADDITION):
			action = "Addition"
		elif (obj.action_flag == CHANGE):
			action = "Change"
		elif (obj.action_flag == DELETION):
			action = "Deletion"
		return action
	_get_action_flag.short_description = 'Action'


class InvitationAdmin(TechAdmin):
	list_display = ('sender', 'code', 'recipient', 'userType', 'typeVerified',
				'requestTimestamp')


class InvitationLogAdmin(TechAdmin):
	list_display = ('sender', 'code', 'recipient', 'userType', 'typeVerified',
				'requestTimestamp', 'canceller')


class EventEntryAdmin(TechAdmin):
	list_display = ('callGroup', 'oncallPerson', 'creator', 'startDate', 'endDate',
				'oncallLevel', 'eventStatus',)
	list_filter = ('oncallStatus', 'eventStatus', 'startDate', 'endDate',)
	search_fields = ('callGroup__description', 'oncallPerson__last_name',
					'oncallPerson__first_name', 'oncallPerson__username',)


def tech_admin_register():
	"""" Tech Admins for models that do not fit into a category or project admin.py file. """
	tech_admin_site.register(User, TechMHLUserAdmin)
	tech_admin_site.register(Group, GroupAdmin)
	tech_admin_site.register(LogEntry, LogEntryAdmin)

