
import sys
import datetime

from django.core.management.base import BaseCommand
from django.contrib.sessions.models import Session
from django.utils.translation import ugettext


class Command(BaseCommand):
	"""
	manage_django_sessions does either three things:
		dump_all - dumps all active and inactive(expired) sessions
		dump_expired - dumps all inactive(expired) sessions
		purge_expired - purge inactive(expired) sessions
	"""
	def __init__(self):
		super(Command, self).__init__()
		self.help = ugettext('Help: Manage, show, or purge current Django sessions.\n')
		self.args = ['dump_all', 'dump_expired', 'purge_expired']

	def handle(self, *args, **options):
		if (len(args) != 1):
			self.print_help(sys.argv[1], "")
		elif (args[0] not in self.args):
			self.stdout.write("\nInvalid argument: %s\n" % (args[0]))
			self.print_help(sys.argv[1], "")
		else:
			recs = 0
			if (args[0] == "dump_all"):
				self.stdout.write("\n")
				sessions = Session.objects.all()
				recs = len(sessions)
				for session in sessions:
					self.stdout.write("\nkey: %s\n" % session.session_key)
					self.stdout.write("data: %s\n" % str(session.get_decoded()))
					self.stdout.write("expires: %s\n" % str(session.expire_date))
				self.stdout.write("\nDumped %d record(s).\n" % recs)
				self.stdout.write("\n%s DONE\n" % sys.argv[1])
			elif (args[0] == "dump_expired"):
				self.stdout.write("\n")
				sessions = Session.objects.filter(expire_date__lt=datetime.datetime.now())
				recs = len(sessions)
				for session in sessions:
					self.stdout.write("\nkey: %s\n" % session.session_key)
					self.stdout.write("data: %s\n" % str(session.get_decoded()))
					self.stdout.write("expires: %s\n" % str(session.expire_date))
				self.stdout.write("\nDumped %d expired record(s).\n" % recs)
				self.stdout.write("\n%s DONE\n" % sys.argv[1])
			elif (args[0] == "purge_expired"):
				purge_expired_sessions(int(options['verbosity']), self.stdout)


def purge_expired_sessions(verbosity=0, output=sys.stderr):
	""" Shared helper to purge expired sessions 

		:returns: number of records purged 
	"""
	sessions = Session.objects.filter(expire_date__lt=datetime.datetime.now())
	recs = len(sessions)
	sessions.delete()
	if verbosity > 1:
		output.write("\nPurged %d record(s).\n" % recs)
		output.write("\n%s DONE\n" % sys.argv[1])

	return recs
