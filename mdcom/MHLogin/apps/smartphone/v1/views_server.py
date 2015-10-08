
import json
from django.conf import settings
from django.http import HttpResponse

from MHLogin.apps.smartphone.v1.decorators import AppAuthentication
from MHLogin.utils.mh_logging import get_standard_logger 


# Setting up logging
logger = get_standard_logger('%s/apps/smartphone/v1/views_server.log' % (settings.LOGGING_ROOT), 
							'DCom.apps.smartphone.v1.views_server', settings.LOGGING_LEVEL)


@AppAuthentication
def info(request):
	response = {
		'warnings': {},
	}
	return HttpResponse(content=json.dumps(response), mimetype='application/json')

