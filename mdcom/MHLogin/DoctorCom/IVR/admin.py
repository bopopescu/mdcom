
from MHLogin.Administration.tech_admin import sites, options

from MHLogin.DoctorCom.IVR.models import VMBox_Config, VMMessage, callLog, \
	callEvent, IVR_Prompt, AnsSvcDLFailure


class VMBox_ConfigAdmin(options.TechAdmin):
	list_display = ('owner', 'owner_type', 'config_complete', 'notification_email',
					'notification_sms', 'notification_page')


class VMMessageAdmin(options.TechAdmin):
	list_display = ('owner', 'owner_type', 'callerID', 'read_timestamp',
					'callbacknumber', 'answeringservice')


class CallLogAdmin(options.TechAdmin):
	list_display = ('mdcom_caller', 'caller_number', 'mdcom_called', 'called_number', 'timestamp')


class CallEventAdmin(options.TechAdmin):
	list_display = ('callSID', 'event', 'timestamp')


class AnsSvcDLFailureAdmin(options.TechAdmin):
	list_display = ('practice_id', 'error_timestamp', 'resolved', 'resolution_timestamp',
				'failure_type', 'caller', 'called')

sites.register(VMBox_Config, VMBox_ConfigAdmin)
sites.register(VMMessage, VMMessageAdmin)
sites.register(IVR_Prompt)
sites.register(AnsSvcDLFailure, AnsSvcDLFailureAdmin)


from django.conf import settings
if (settings.DEBUG_MODELS):
	sites.register(callLog, CallLogAdmin)
	sites.register(callEvent, CallEventAdmin)
	# register rest with default admin
	from MHLogin.utils.admin_utils import registerallmodels
	registerallmodels('IVR')

