
import traceback

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.translation import ugettext_lazy as _

from MHLogin.DoctorCom.IVR.models import AnsSvcDLFailure
from MHLogin.DoctorCom.IVR.utils import resolve_download_failure
from MHLogin.utils.admin_utils import mail_admins


@transaction.commit_manually
class Command(BaseCommand):
	args = ''
	help = ''

	def handle(self, *args, **kwargs):
		msgs = AnsSvcDLFailure.objects.filter(resolved=False)
		if (len(msgs)):
			successes = []
			failures = []
			for msg in msgs:
				try:
					resolution_success = resolve_download_failure(msg)
				except Exception:
					failures.append(msg.call_sid)
					mail_admins(_("Failed to retry Ans. Svc. DL Failure"),
							traceback.format_exc())
					transaction.rollback()
				else:
					if (resolution_success):
						successes.append(msg.call_sid)
						mail_admins(_("Ans. Svc. DL Failure Retry Success"),
								msg.call_sid)
						transaction.commit()
					else:
						failures.append(msg.call_sid)
						mail_admins(_("Failed to retry Ans. Svc. DL Failure"),
								traceback.format_exc())
						transaction.rollback()

			mail_admins(_('IVR Message Automatic Retry Status'),
					_('Successes: %(successes)s\nFailures: %(failures)s') %
					{'successes': ', '.join(successes), 'failures': ', '.join(failures), }
				)

