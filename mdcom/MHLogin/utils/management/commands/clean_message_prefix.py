from django.core.management.base import BaseCommand
from django.utils.translation import ugettext
from MHLogin.DoctorCom.Messaging.models import Message
from MHLogin.DoctorCom.Messaging.utils import MSG_SUBJECT_PREFIXS,\
	clean_subject_prefix, MSG_SUBJECT_PREFIX_RE, MSG_SUBJECT_PREFIX_FW
from optparse import make_option
from MHLogin.utils.mh_logging import get_standard_logger
from django.conf import settings

# Setting up logging
logger = get_standard_logger('%s/utils/management/commands/clean_message_prefix.log' % (settings.LOGGING_ROOT), 
							'utils.management.commands.clean_message_prefix', "INFO")

class Command(BaseCommand):
	"""
	Clean message subject prefix.
	"""
	option_list = BaseCommand.option_list + (
		make_option('--persistence',
			action='store_true', dest='persistence', default=False,
			help='Tells Django to apply these change to the database.'),
	)
	def __init__(self):
		super(Command, self).__init__()
		self.help = ugettext('Help: Clean message subject prefix.\n')

	def handle(self, *args, **options):
		Command.persistence = options.pop('persistence', True)

		print_log("==========================================================")

		msgs_re_c = Message.objects.filter(
						subject__istartswith=MSG_SUBJECT_PREFIX_RE).count()
		msgs_fw_c = Message.objects.filter(
						subject__istartswith=MSG_SUBJECT_PREFIX_FW).count()
		print_log('The number of message its subject start with \"%s\": %d.\n'\
					%(MSG_SUBJECT_PREFIX_RE, msgs_re_c))
		print_log('The number of message its subject start with \"%s\": %d.\n'\
					%(MSG_SUBJECT_PREFIX_FW, msgs_fw_c))

		print_log('Clean message subject ---- start.\n')
		msgs = Message.objects.all()
		changed_num = 0
		for msg in msgs:
			subject = msg.subject
			if subject and len(subject) >= 3 \
				and subject[0:3].upper() in (MSG_SUBJECT_PREFIXS):
				new_subject = clean_subject_prefix(subject)
				if not subject == new_subject:
					changed_num += 1
					if Command.persistence:
						Message.objects.filter(id=msg.id).update(subject=new_subject)

					print_log('Clean message [id -- %d] subject prefix.\n'%(msg.id))
					print_log('    From: %s \n'%(subject))
					print_log('    To:   %s \n'%(new_subject))
		print_log('Changed %d message(s).\n'%(changed_num))
		print_log('Clean message subject ---- end.\n')

		msgs_re_c = Message.objects.filter(
						subject__istartswith=MSG_SUBJECT_PREFIX_RE).count()
		msgs_fw_c = Message.objects.filter(
						subject__istartswith=MSG_SUBJECT_PREFIX_FW).count()
		print_log('The number of message its subject start with \"%s\": %d.\n'\
					%(MSG_SUBJECT_PREFIX_RE, msgs_re_c))
		print_log('The number of message its subject start with \"%s\": %d.\n'\
					%(MSG_SUBJECT_PREFIX_FW, msgs_fw_c))

def print_log(str):
	print str
	logger.info(str)
	
