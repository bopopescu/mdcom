import re
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

phone_regex = re.compile(r'^[0-9]{10}$')
def validate_phone(phone):
	if(not phone_regex.match(phone) and settings.CALL_ENABLE):
		raise ValidationError(_("Please enter only digits. (e.g., 8005555555)"))
	return phone
