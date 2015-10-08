
from datetime import datetime

from django.core.management.base import BaseCommand

from ...models import EventEntry

from django.utils.translation import ugettext_lazy as _

from MHLogin.utils.admin_utils import mail_admins


class Command(BaseCommand):
	help = _('Sends something of a database dump of all events to the administrators list.')

	def handle(self, *args, **options):
		#table_name = 'Scheduler_evententry'
		#cursor = connection.cursor()

		#cursor.execute(' '.join(['SELECT * from', table_name]))
		#raw_dump = cursor.fetchall()

		qs = EventEntry.objects.all().order_by('id')
		body = '\n'.join([repr(e) for e in qs])

		mail_admins(''.join(['Events Dump (', datetime.now().strftime('%Y.%m.%d@%H:%M'), ')']), body)

