

from MHLogin.Administration.tech_admin import sites, options

from MHLogin.Validates.models import Validation, ValidationLog


class ValidationAdmin(options.TechAdmin):
	list_display = ('code', 'type', 'applicant', 'recipient', 'is_active',
					'sent_time', 'validate_locked_time', 'validate_success_time')
	search_fields = ('code', 'applicant', 'recipient')


class ValidationLogAdmin(options.TechAdmin):
	list_display = ('validation', 'code_input', 'validate_time')
	search_fields = ('code_input',)


sites.register(Validation, ValidationAdmin)
sites.register(ValidationLog, ValidationLogAdmin)

