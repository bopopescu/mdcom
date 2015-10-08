'''
Created on 2013-5-28

@author: pyang
'''
import json
from MHLogin.api.v1.tests.utils import APITest, get_random_username
from django.core.urlresolvers import reverse
from MHLogin.MHLPractices.models import PracticeLocation
from MHLogin.MHLSites.models import Site
from MHLogin.MHLUsers.models import Office_Manager, OfficeStaff, Physician
from MHLogin.utils.tests.tests import create_user
from MHLogin.apps.smartphone.v1.errlib import err_GE002
from MHLogin.KMS.models import RSAKeyPair, IVR_RSAKeyPair
from django.conf import settings
from MHLogin.KMS.utils import strengthen_key
class PracticeManageTest(APITest):
	def testPracticeManage(self):
		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice.save()
		self.user.current_practice = practice
		self.user.practices.add(practice)
		self.user.save()
		response = self.client.get(reverse\
				('MHLogin.api.v1.views_account.practiceManage'), **self.extra)
		self.assertEqual(response.status_code, 200, response.status_code)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 2)
		
		response = self.client.post(reverse\
				('MHLogin.api.v1.views_account.practiceManage'), **self.extra)
		self.assertEqual(response.status_code, 200, response.status_code)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 2)
		
		response = self.client.post(reverse\
				('MHLogin.api.v1.views_account.practiceManage'), data={'current_practice':practice.id}, **self.extra)
		self.assertEqual(response.status_code, 200, response.status_code)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 2)
		
class SiteManageTest(APITest):
	def testSiteManage(self):
		site = Site(
				name='mysite',
				address1='555 Pleasant Pioneer Grove',
				address2='Trailer Q615',
				city='Mountain View',
				state='CA',
				zip='94040-4104',
				lat=37.36876,
				longit=-122.081864,
				short_name='MSite'
			)
		site.save()
		self.user.current_site = site
		self.user.sites.add(site)
		self.user.save()
		response = self.client.get(reverse\
				('MHLogin.api.v1.views_account.siteManage'), **self.extra)
		self.assertEqual(response.status_code, 200, response.status_code)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 2)
		
		response = self.client.post(reverse\
				('MHLogin.api.v1.views_account.siteManage'), **self.extra)
		self.assertEqual(response.status_code, 200, response.status_code)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 2)

		response = self.client.post(reverse\
				('MHLogin.api.v1.views_account.siteManage'), data={'current_site':site.id}, **self.extra)
		self.assertEqual(response.status_code, 200, response.status_code)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 2)


class CallFwdPrefsTest(APITest):
	def testCallFwdPrefs(self):
		self.user.office_phone = '9001234124'
		self.user.phone = '9001234134'
		self.user.save()
		response = self.client.get(reverse\
				('MHLogin.api.v1.views_account.callFwdPrefs'), **self.extra)
		self.assertEqual(response.status_code, 200, response.status_code)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 2)
		
		response = self.client.post(reverse\
				('MHLogin.api.v1.views_account.callFwdPrefs'),data={'forward':'Mobile'}, **self.extra)
		self.assertEqual(response.status_code, 200, response.status_code)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 2)
		
		response = self.client.post(reverse\
				('MHLogin.api.v1.views_account.callFwdPrefs'),data={'forward':'Office'}, **self.extra)
		self.assertEqual(response.status_code, 200, response.status_code)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 2)
		
		response = self.client.post(reverse\
				('MHLogin.api.v1.views_account.callFwdPrefs'),data={'forward':'Other'}, **self.extra)
		self.assertEqual(response.status_code, 200, response.status_code)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 2)
		
		response = self.client.post(reverse\
				('MHLogin.api.v1.views_account.callFwdPrefs'),data={'forward':'Voicemail'}, **self.extra)
		self.assertEqual(response.status_code, 200, response.status_code)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 2)
		
class GetDComNumberTest(APITest):
	def testGetDComNumber(self):
		user = create_user(get_random_username(), "tian", "thj", "demo", "555 Bryant St.",
								"Palo Alto", "CA", "", uklass=OfficeStaff)
		user.mdcom_phone = '9001234123'
		user.save()
		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice.save()
		mgr = Office_Manager(user=user, practice=practice, manager_role=2)
		mgr.save()
		response = self.client.get(reverse\
				('MHLogin.api.v1.views_account.getDComNumber'), **self.extra)
		self.assertEqual(response.status_code, 200, response.status_code)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 2)
		
class GetMobilePhoneTest(APITest):
	def testGetMobilePhone(self):
		response = self.client.get(reverse\
				('MHLogin.api.v1.views_account.getMobilePhone'), **self.extra)
		self.assertEqual(response.status_code, 200, response.status_code)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 2)
	
	def testUpdateMobilePhone(self):	
		response = self.client.get(reverse\
				('MHLogin.api.v1.views_account.updateMobilePhone'), **self.extra)
		self.assertEqual(response.content, err_GE002().content, response.status_code)
		
		response = self.client.post(reverse\
				('MHLogin.api.v1.views_account.updateMobilePhone'), data={'mobile_phone':9001234124}, **self.extra)
		self.assertEqual(response.status_code, 200, response.status_code)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 2)
		
class ChangePasswordTest(APITest):
	def testChangePassword(self):
		response = self.client.get(reverse\
				('MHLogin.api.v1.views_account.changePassword'), **self.extra)
		self.assertEqual(response.content, err_GE002().content, response.status_code)
		
		response = self.client.post(reverse\
				('MHLogin.api.v1.views_account.changePassword'), **self.extra)
		self.assertEqual(response.status_code, 400, response.status_code)
	def testChangePassword_form(self):
		data = {'old_password':'demo',
			'new_password1':'123456',
			'new_password2':'123456'}
		response = self.client.post(reverse\
				('MHLogin.api.v1.views_account.changePassword'), data, **self.extra)
		self.assertEqual(response.status_code, 200, response.status_code)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 2)
		
class ProfileTest(APITest):
	def testProfile(self):
		phys = Physician(user = self.user)
		phys.save()
		data = {
			'username':get_random_username(),
			'first_name':'c',
			'last_name':'tian',
			'mobile_phone':9001111111,
			'gender':'M',
			'old_email':'cprovider1@suzhoukada.com',
			'email':'testp@suzhoukada.com',
			'lat':0.0, 
			'longit':0.0, 
			'address1':'address1', 
			'address2':'address2', 
			'city':'Chicago', 
			'state':'IL', 
			'zip':60601,
			'user_type':1,
			'office_lat':41.885805,
			'office_longit':-87.6229106,
		}

		response = self.client.post(reverse\
				('MHLogin.api.v1.views_account.profile'), data,**self.extra)
		self.assertEqual(response.status_code, 200, response.status_code)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 2)
		
		site = Site(
				name='mysite',
				address1='555 Pleasant Pioneer Grove',
				address2='Trailer Q615',
				city='Mountain View',
				state='CA',
				zip='94040-4104',
				lat=37.36876,
				longit=-122.081864,
				short_name='MSite'
			)
		site.save()
		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice.save()
		self.user.current_site = site
		self.user.current_practice = practice
		self.user.save()
		response = self.client.get(reverse\
				('MHLogin.api.v1.views_account.profile'), data,**self.extra)
		self.assertEqual(response.status_code, 200, response.status_code)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 2)
		