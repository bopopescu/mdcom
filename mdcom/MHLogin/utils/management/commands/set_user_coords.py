
import logging

from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from optparse import make_option

from MHLogin.utils.geocode import geocode2
from MHLogin.utils.mh_logging import get_standard_logger 

# Setting up logging
logger = get_standard_logger('%s/utils/management/commands/command.log' % (settings.LOGGING_ROOT), 
							'set_user_coords', logging.INFO)


@transaction.commit_manually
class Command(BaseCommand):
	"""
	set_user_coords: This command will update user coordinates.
	For each MHLUser:
		If MHLUser has valid address and no longit/lat it will set longit/lat
		else If MHLUser has no valid address/longit/lat check if they are Provider, 
			Office_Staff, Office_Manager, Broker, etc..
			Find out which and check if they have a valid office_addres and longit/lat
			then copy those values into MHLUser address fields
	"""
	option_list = BaseCommand.option_list + (
		make_option('-s', '--show-only', action='store_true', dest='show',
				default=False, help='Only show what will be done, dont modify database.'),)

	def __init__(self):
		super(Command, self).__init__()
		self.help = 'Update MHLUser address and coordinates.\n'

	def handle(self, *args, **kwargs):
		""" Entry point for set_user_coordinates management command """
		pass
######### TBI #########  
#		show = kwargs['show']
#
#		if (len(args) != 0):
#			self.print_help(sys.argv[1], "")
#			sys.exit(1)
#
#		for u in MHLUser.objects.all():
#			# check if no long/lat set
#			if ((u.lat == 0.0 and u.longit == 0.0) or 
#				(u.lat == None and u.longit == None)):
#				data = geocode2(u.address1, u.city, u.state, u.zip)
#				o.lat = o.longit = 0.0
#				if (data['Error'] == 0): # if no error record coords
#					o.lat = data['Results'][0]['latitude']
#					o.longit = data['Results'][0]['longitude']
#					self.save_it(o, data, int(kwargs['verbosity']))
#				else:
#					self.stderr.write("\nError: %s for %s\n" % (data['ErrorMessage'], str(o)))


def geocode_try_recover_lost_users(lostusers):
	""" Given an arry of lost MHLUsers lookup their address

	:param users: array of MHLUsers
	:returns: none
	 """
	# verify lost users, this extra call is questionable	 
	lostusers = lostusers.filter(Q(lat=0.0, longit=0.0) | Q(lat=None, longit=None))
	for u in lostusers:
		result = geocode2(u.address1, u.city, u.state, u.zip)

		if (result['lat'] != 0.0 and result['lng'] != 0.0):
			u.lat = result['lat'] 
			u.longit = result['lng']
			try:
				u.save()
			except (ValidationError, Exception), ve:
				logger.warn("Error saving user with new coords: %s-%s" %
						(ve.__class__.__name__, str(ve)))


# So we can call set_user_coords from within MHLogin app
def set_user_coords():
	"""
	So we can call set_user_coords from within MHLogin app
	"""
	Command().run_from_argv(["manage", "set_user_coords"])

