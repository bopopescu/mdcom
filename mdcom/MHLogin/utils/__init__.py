

import logging

from django.conf import settings

from MHLogin.utils.mh_logging import get_standard_logger 

# Standard logger for speech
logger = get_standard_logger('%s/utils/utils.log' % (settings.LOGGING_ROOT),
							'utils', logging.WARN)


