import sys,os
sys.path.append('/var/django_projects/dev')
os.environ['DJANGO_SETTINGS_MODULE'] ='MHLogin.settings'

from django.core.management import setup_environ

from MHLogin import settings

setup_environ(settings)

from django.contrib.auth.models import User
from MHLogin.MHLSites.models import *
from MHLogin.MHLUsers.models import *

providers = Provider.objects.all()
print "%20s %25s %25s %15s %10s %10s %10s %10s" % ('Name', 'Off_Addr1', 'Off_Addr2', 'Off_City', 'Off_St', 'Off_Zip', 'Off_Lat', 'Off_Longit')
print "------------------------------------------------------------------------------------------------------------------------------------------------------------------------"
for p in providers:
	name = "%s %s" % (p.user.first_name, p.user.last_name)
	if (len(p.user.address1) == 0 or not(p.user.lat)):
		if (p.current_site):
			sname = p.current_site.name
			p.user.address1 = saddress1 = p.current_site.address1
			p.user.address2 = saddress2 = p.current_site.address2
			p.user.city = scity = p.current_site.city
			p.user.state = sstate = p.current_site.state
			p.user.zip = szip = p.current_site.zip
			p.user.lat = slat = p.current_site.lat
			p.user.longit = slongit = p.current_site.longit
			p.save()
			print "SAVED - %20s %25s %25s %15s %10s %10s %10.5f %10.5f" % (name, p.office_address1, p.office_address2, p.office_city, p.office_state, p.office_zip, p.office_lat, p.office_longit)
		else:
			sname = "None"
			saddress1 = "None"
			saddress2 = "None"
			scity = "None"
			sstate = "None"
			szip = "None"
			slat = 0.0
			slongit = 0.0
			print "NO CURRENT SITE for %s" % (name)
	else:
		print "Using Current Office Address - NO SAVE - %20s %25s %25s %15s %10s %10s %10.5f %10.5f" % (name, p.office_address1, p.office_address2, p.office_city, p.office_state, p.office_zip, p.office_lat, p.office_longit)

