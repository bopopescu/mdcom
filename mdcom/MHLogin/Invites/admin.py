
from MHLogin.Invites.models import Invitation, InvitationLog

from MHLogin.Administration.tech_admin import sites, options


class InvitationAdmin(options.TechAdmin):
	list_display = ('sender', 'code', 'recipient', 'userType', 'typeVerified',
				'requestTimestamp')
	search_fields = ('sender__username', 'sender__first_name', 'sender__last_name', 'code')


class InvitationLogAdmin(options.TechAdmin):
	list_display = ('sender', 'code', 'recipient', 'userType', 'typeVerified',
				'requestTimestamp', 'canceller')
	search_fields = ('sender__username', 'sender__first_name', 'sender__last_name', 'code')


sites.register(Invitation, InvitationAdmin)
sites.register(InvitationLog, InvitationLogAdmin)

