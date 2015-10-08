from django.core.management.base import BaseCommand
from django.utils.translation import ugettext
from MHLogin.DoctorCom.Messaging.models import Message, MessageBodyUserStatus,\
	MessageActionHistory

class Command(BaseCommand):
	"""
	Initialize message action history.
	"""
	def __init__(self):
		super(Command, self).__init__()
		self.help = ugettext('Help: Initialize message action history.\n')

	def handle(self, *args, **options):
		print 'Initialize message action history ---- start.\n'
		print '1. Initialize message read history.\n'
		mbuss = MessageBodyUserStatus.objects.filter(read_flag=True)\
			.order_by('read_timestamp')
		for mbus in mbuss:
			msg = mbus.msg_body.message
			mah = MessageActionHistory.create_read_history(msg, mbus.user, timestamp=mbus.read_timestamp)
			print ".",

		print '\n2. Initialize message resolve history.\n'
		msgs = Message.objects.exclude(_resolved_by=None).exclude(_resolved_by=0)\
			.order_by('resolution_timestamp')
		for msg in msgs:
			mah = MessageActionHistory.create_resolve_history(msg, msg._resolved_by, timestamp=msg.resolution_timestamp)
			print ".",
		print '\nInitialize message action history ---- end.\n'


