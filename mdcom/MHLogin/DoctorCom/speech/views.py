
import os

from django.conf import settings
from django.http import HttpResponse
from django.core.servers.basehttp import FileWrapper

from MHLogin.DoctorCom.speech import logger
from MHLogin.DoctorCom.speech.models import VoiceClip
from MHLogin.MHLUsers.decorators import RequireAdministrator
from MHLogin.utils.decorators import TwilioAuthentication
#from MHLogin.utils.storage import get_file #TODO


@TwilioAuthentication(allow_get=True)
def get_voice_clip(request, confname=None, filename=None):
	try:
		vc = VoiceClip.objects.get(config__name=confname, filename=filename)

		filename = os.path.join(settings.MEDIA_ROOT, 'tts', confname, filename)

		# fix is related to issue 1361 use FileWrapper - stream file in configurable
		# chunks to webserver rather than read() which does whatever it wants.  Default
		# read was causing problems with the Django Server but Apache worked fine,
		# possibly by accident.  Long term solution is use something like this in
		# utils/storage.py as an option for large data. We can experiment where Django
		# server has problems, FileWrapper default blksize is 8192 bytes.
		resp = HttpResponse(FileWrapper(open(filename)),
                           mimetype='audio/%s' % vc.get_encoding_string())

		resp['Content-Length'] = os.path.getsize(filename)
		resp['Content-Disposition'] = "attachment; filename=%s" % os.path.basename(filename)
		vc.access_count += 1
		vc.save()
		logger.info("Sending audio file to requester: %s" % filename)
	except (Exception), e:
		logger.critical("Problems in voice clip retrieval: %s" % str(e))
		fetch_err = os.path.join(settings.MEDIA_ROOT, 'audio', 'fetch_error.wav')
		with open(fetch_err, "rb") as f:
			resp = HttpResponse(f.read(), mimetype='audio/wav')

	return resp


@RequireAdministrator
def debug(request):
	""" Hook into debug our code remotely """
	logger.warn("Debug - set trace to localhost")
	import pydevd; pydevd.settrace("localhost")

	return HttpResponse("Set trace on - localhost", mimetype='text/html')

