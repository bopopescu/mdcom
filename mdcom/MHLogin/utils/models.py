
import kronos

from MHLogin.utils import logger
from MHLogin.utils.admin_utils import mail_admins
from MHLogin.utils.management.commands.manage_django_sessions import purge_expired_sessions


@kronos.register("@daily") 
def run_purge_expired_sessions():
	"""
	Entry point used by kronos to run_purge_expired_sessions, checks daily.  For django 
	kronos installtasks command to work decorated function must be in python module 
	loaded at startup such as: models, __init__, admin, .cron, etc..
	"""
	try:
		recs = purge_expired_sessions()
		logger.info("kronos purge_expired_sessions: %d purged, DONE." % recs)
	except Exception as e:
		# enclose in try/catch Exception for now, run_purge_expired_sessions()
		# is run daily, code was not active on production until 1.64.00.
		mail_admins("Problems in run_purge_expired_sessions()", str(e))
		logger.error("Problems in run_purge_expired_sessions() %s" % str(e))

