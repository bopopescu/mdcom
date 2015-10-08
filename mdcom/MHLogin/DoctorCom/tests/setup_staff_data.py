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

if __name__ == '__main__':
	#generate 101 office staff
	practice = PracticeLocation.objects.get(id=1)
	chars = 'abcdefghijklmnopqrstuvwxyz0123456789'
	for i in range(101):
		username = ''.join([random.choice(chars) for x in range(6)])
		first_name = ''.join([random.choice(chars) for x in range(3)])
		last_name = ''.join([random.choice(chars) for x in range(3)])
		user = MHLUser(username=username, first_name=first_name, last_name=last_name, password='demo')
		user.save()
		staff = OfficeStaff(user=user)
		staff.save()
		staff.practices.add(practice)
	
	#generate 1 nurse
	username = ''.join([random.choice(chars) for x in range(6)])
	first_name = ''.join([random.choice(chars) for x in range(3)])
	last_name = ''.join([random.choice(chars) for x in range(3)])
	nurseUser = MHLUser(username=username, first_name=first_name, last_name=last_name, password='demo')
	nurse = Nurse(user=nurseUser)
	nurse.save()
	nurse.practices.add(practice)
	
	#generate 1 dietitian
	username = ''.join([random.choice(chars) for x in range(6)])
	first_name = ''.join([random.choice(chars) for x in range(3)])
	last_name = ''.join([random.choice(chars) for x in range(3)])
	dietUser = MHLUser(username=username, first_name=first_name, last_name=last_name, password='demo')
	dietician = Dietician(user=dietUser)
	dietician.save()
	dietician.practices.add(practice)
	
