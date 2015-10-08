# -*- coding: utf-8 -*
#!/usr/bin/python
#
# Notice:
# this script is used to generate
# some data for multi callgroup development

__author__ = ''

from django.core.management import setup_environ
import MHLogin.settings as settings
setup_environ(settings)

from django.db.models.loading import cache as model_cache
from MHLogin.MHLUsers.models import *
from MHLogin.MHLPractices.models import *
from MHLogin.MHLCallGroups.models import *
from MHLogin.utils.fields import *

if not model_cache.loaded:
	model_cache.get_models()

if __name__=='__main__':
	practice1 = PracticeLocation()
	practice1.practice_name = 'San Jose Practice'
	practice1.practice_address1 = 'McKee Rd'
	practice1.practice_city = 'San Jose'
	practice1.practice_state = 'CA'
	practice1.practice_phone = '8002464123'
	practice1.practice_lat = '37.358765'
	practice1.practice_longit = '-121.860021'
	practice1.time_zone = "US/Pacific"
	practice1.save()

	practice2 = PracticeLocation()
	practice2.practice_name = 'San Diego Practice'
	practice2.practice_address1 = 'Middle way Rd'
	practice2.practice_city = 'San Diego'
	practice2.practice_state = 'CA'
	practice2.practice_phone = '8002464113'
	practice2.practice_lat = '33.358765'
	practice2.practice_longit = '-121.810021'
	practice2.time_zone = "US/Pacific"
	practice2.save()

	callgroup1 = CallGroup(description="Team A", team="Team A", number_selection=7)
	callgroup1.save()
	
	callgroup2 = CallGroup(description="Team B", team="Team B", number_selection=6)
	callgroup2.save()
	
	callgroup3 = CallGroup(description="Team C", team="Team C", number_selection=5)
	callgroup3.save()
	
	callgroup4 = CallGroup(description="Team D", team="Team D", number_selection=3)
	callgroup4.save()
	
	callgroup5 = CallGroup(description="Team E", team="Team E", number_selection=2)
	callgroup5.save()
	

		
	if (Provider.objects.count()>=20):
		providers1 = Provider.objects.all()[0:10]
		i=0
		for provider in providers1:
			provider.practices.add(practice1)
			cgm = CallGroupMember()
			cgm.member=provider
			cgm.alt_provider=1
			if i<3:
				cgm.call_group = callgroup1
			elif i<6:
				cgm.call_group = callgroup2
			else:
				cgm.call_group = callgroup3
			cgm.save()
			i+=1
		
		i=0	
		providers2 = Provider.objects.all()[10:20]	
		for provider in providers2:
			provider.practices.add(practice2)
			cgm = CallGroupMember()
			cgm.member=provider
			cgm.alt_provider=1
			if i<5:
				cgm.call_group = callgroup4
			else:
				cgm.call_group = callgroup5
			cgm.save()
			i+=1
	else:
		practice1.delete()
		practice2.delete()
		print "Have you run your dump sql?"
		exit()
	

	
	specialty1 = Specialty()
	specialty1.name = "Specialty A"
	specialty1.practice_location = practice1
	specialty1.number_selection = 3
	specialty1.save()
	specialty1.call_groups.add(callgroup1)
	specialty1.call_groups.add(callgroup2)
	specialty1.save()
	
	specialty2 = Specialty()
	specialty2.name = "Specialty B"
	specialty2.practice_location = practice1
	specialty2.number_selection = 5
	specialty2.save()
	specialty2.call_groups.add(callgroup3)
	specialty2.save()
	
	specialty3 = Specialty()
	specialty3.name = "Specialty C"
	specialty3.practice_location = practice2
	specialty3.number_selection = 7
	specialty3.save()
	specialty3.call_groups.add(callgroup4)
	specialty3.save()

	specialty4 = Specialty()
	specialty4.name = "Specialty D"
	specialty4.practice_location = practice2
	specialty4.number_selection = 6
	specialty4.save()
	specialty4.call_groups.add(callgroup5)
	specialty4.save()

	practice1.call_groups.add(callgroup1)
	practice1.call_groups.add(callgroup2)
	practice1.call_groups.add(callgroup3)
	practice1.save()
	
	
	practicemgr = MHLUser.objects.get(username='practicemgr')
	office_staff = OfficeStaff.objects.get(user=practicemgr)
	office_staff.current_practice = practice1
	office_staff.practices.add(practice1)
	office_staff.practices.add(practice2)
	office_staff.save()
	
	office_manager = Office_Manager()
	office_manager.manager_role = 1
	office_manager.user = office_staff
	office_manager.practice = practice1
	office_manager.save()
	
	
	
	
	
	print "Practices Number: %d" % PracticeLocation.objects.count()
	print "Call Groups Number:%d" % CallGroup.objects.count()
	print "Specialty Number:%d" % Specialty.objects.count()