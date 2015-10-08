
from django.conf import settings
from MHLogin.utils.mh_logging import get_standard_logger

# logger for tech_admin package
logger = get_standard_logger('%s/Administration/tech_admin.log'%(settings.LOGGING_ROOT),
							'tech_admin', settings.LOGGING_LEVEL)

