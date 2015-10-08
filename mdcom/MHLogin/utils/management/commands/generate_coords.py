
import sys
import urllib
import urllib2
import json

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from optparse import make_option
from MHLogin.MHLUsers.models import MHLUser
from MHLogin.MHLSites.models import Site
from MHLogin.MHLPractices.models import PracticeLocation
from MHLogin.utils.geocode import geocode_format_request

URL = "http://where.yahooapis.com/geocode"


@transaction.commit_manually
class Command(BaseCommand):
	"""
	generate_coords: generate or re-generate coordinates for users, practices, or sites
	having invalid or no longitude or latitude values set.  This command is typically
	run only once or on older databases or older code in which users, sites, and 
	practices didn't have their longitude or latitude values set correctly.
	"""
	option_list = BaseCommand.option_list + (
		make_option('-f', '--force', action='store_true', dest='force',
				default=False, help='Force resetting geo coordinates even if already set.'),
		make_option('-l', '--lost', action='store_true', dest='lost',
				default=False, help='Show lost users, sites, or practices but change nothing.'),
		make_option('-g', '--generate_random_phone', action='store', dest='generate',
				default=-1, help='Generate random unique user phone numbers, '\
					'starting at base 800555, -g 800555 for example generates 8005550000, "\
					8005550001, etc...  Use only for test.'))

	obj_dict = {"users": MHLUser.objects.all(), "sites": Site.objects.all()}

	def __init__(self):
		super(Command, self).__init__()
		self.help = 'generates user coordinates if not currently in the database.\n'
		self.args = ['users', 'sites', 'practices']

	def handle(self, *args, **kwargs):
		if (len(args) != 1):
			self.print_help(sys.argv[1], "")
		elif (args[0] not in self.args):
			self.stdout.write("\nInvalid argument: %s\n" % (args[0]))
			self.print_help(sys.argv[1], "")
		elif (args[0] == "users" or args[0] == "sites"):
			if (int(kwargs['generate']) >= 0):
				self.generate_random_numbers(int(kwargs['generate']))
			if (kwargs['lost'] == True):
				self.stdout.write("\nLost %s:\n\n" % (args[0]))
				for o in self.obj_dict[args[0]]:
					if ((o.lat == 0.0 and o.longit == 0.0) or
						(o.lat == None and o.longit == None)):
						self.stdout.write(str(o) + "\n")
			else:		
				for o in self.obj_dict[args[0]]:
					if (kwargs['force'] == True or (
										(o.lat == 0.0 and o.longit == 0.0) or 
										(o.lat == None and o.longit == None))):
						data = get_geo_location(o.address1, o.city, o.state, o.zip)

						o.lat = o.longit = 0.0
						if (data['Error'] == 0):  # if no error record coords
							o.lat = data['Results'][0]['latitude']
							o.longit = data['Results'][0]['longitude']
							self.save_it(o, data, int(kwargs['verbosity']))
						else:
							self.stderr.write("\nError: %s for %s\n" % (data['ErrorMessage'], str(o)))
		elif (args[0] == "practices"):
			if (kwargs['lost'] == True):
				self.stdout.write("\nLost %s:\n\n" % (args[0]))
				for p in PracticeLocation.objects.all():
					if ((p.practice_lat == 0.0 and p.practice_longit == 0.0) or
						(p.practice_lat == None and p.practice_longit == None)):
						self.stdout.write(str(p) + "\n")
			else:
				for p in PracticeLocation.objects.all():
					if (kwargs['force'] == True or (
										(p.practice_lat == 0.0 and p.practice_longit == 0.0) or 
										(p.practice_lat == None and p.practice_longit == None))):
						data = get_geo_location(p.practice_address1, p.practice_city, 
											p.practice_state, p.practice_zip)

						p.practice_lat = p.practice_longit = 0.0
						if (data['Error'] == 0):  # if no error record coords
							p.practice_lat = data['Results'][0]['latitude']
							p.practice_longit = data['Results'][0]['longitude']
							self.save_it(p, data, int(kwargs['verbosity']))
						else:
							self.stderr.write("\nError: %s for %s\n" % (data['ErrorMessage'], str(p)))

		if (int(kwargs['verbosity']) > 1):
			self.stdout.write("\n%s DONE\n" % sys.argv[1])

	# helper to save object and report error if any 
	def save_it(self, obj, data, verbosity=1):
		if (verbosity > 1):
			self.stdout.write("\nGeo results for %s: %s\n" % (obj, data['Results'][0]))
		try:
			obj.save()
		except Exception, e:
			self.stderr.write("\n\nProblems saving: %s\n%s" % (obj, e))

	# generate random unique user phone numbers, use only for test
	def generate_random_numbers(self, base_phone):
		start = 0
		for u in MHLUser.objects.all():
			u.mobile_phone = "%d%04d" % (base_phone, start)
			start += 1
			u.save()


# helper to get geo location coordinates
def get_geo_location(addr, city, state, zipcode): 
	get_data = {'appid': settings.YAHOO_APP_ID, 'flags': 'JT'}
	geocode_format_request(addr, city, state, zipcode, get_data)
	url_data = urllib.urlencode(get_data)
	full_url = ''.join([URL, '?', url_data])
	response = urllib2.urlopen(full_url)
	return json.loads(response.read())['ResultSet']


