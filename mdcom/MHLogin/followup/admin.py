

from MHLogin.Administration.tech_admin import sites, options
from MHLogin.followup.models import FollowUps


class FollowUpsAdmin(options.TechAdmin):
	list_display = ('user', 'done', 'priority', 'task', 'creation_date', 
 				'due_date', 'completion_date', 'deleted', 'note')


sites.register(FollowUps, FollowUpsAdmin)

