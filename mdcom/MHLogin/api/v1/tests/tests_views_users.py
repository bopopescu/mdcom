import json

from django.core.urlresolvers import reverse

from MHLogin.MHLUsers.models import  Provider, OfficeStaff
from MHLogin.api.v1.errlib import err_GE002
from MHLogin.api.v1.utils import HttpJSONSuccessResponse
from MHLogin.api.v1.tests.utils import create_user, create_office_staff,\
	get_random_username, APITest

class SearchTest(APITest):
	def testSearchProviders(self):
		response = self.client.post(reverse('MHLogin.api.v1.views_users.searchProviders'), **self.extra)
		self.assertEqual(response.status_code, 200, response.status_code)

		response = self.client.get(reverse('MHLogin.api.v1.views_users.searchProviders'), **self.extra)
		self.assertEqual(response.content, err_GE002().content, response.status_code)

	def testSearchStaff(self):
		response = self.client.post(reverse('MHLogin.api.v1.views_users.searchStaff'), **self.extra)
		self.assertEqual(response.status_code, 200, response.status_code)

		response = self.client.get(reverse('MHLogin.api.v1.views_users.searchStaff'), **self.extra)
		self.assertEqual(response.content, err_GE002().content, response.status_code)
#
	def testProviderInfo(self):
		user = create_user(get_random_username(), "tian1", "thj1", "demo", "555 Bryant St.",
								"Palo Alto", "CA", uklass=Provider)
		user.mdcom_phone = '9001234124'
		user.save()

		response = self.client.post(reverse('MHLogin.api.v1.views_users.providerInfo', args=(user.id,)), **self.extra)
		self.assertEqual(response.status_code, 200, response.status_code)

	def testStaffInfo(self):
		user = create_office_staff(get_random_username(), "tian1", "thj1", "demo", "555 Bryant St.",
								"Palo Alto", "CA", uklass=OfficeStaff)
		user.mdcom_phone = '9001234125'
		user.save()

		response = self.client.post(reverse('MHLogin.api.v1.views_users.staffInfo', args=(user.user.id,)), **self.extra)
		self.assertEqual(response.status_code, 200, response.status_code)

class CreateUserTest(APITest):
	def testCreateProvider(self):
		data = {
			'username':get_random_username(),
			'first_name':'c',
			'last_name':'tian',
			'mobile_phone':9001111111,
			'gender':'M',
			'email':'cprovider1@suzhoukada.com',
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

		response = self.client.post(reverse('MHLogin.api.v1.views_users.createProvider'), data, **self.extra)
		self.assertEqual(response.status_code, 200, response.status_code)
		self.assertEqual(response.content, HttpJSONSuccessResponse().content, response.status_code)

		response = self.client.post(reverse('MHLogin.api.v1.views_users.createProvider'), **self.extra)
		self.assertEqual(json.loads(response.content)['errno'], 'GE031', response.status_code)
	
		response = self.client.get(reverse('MHLogin.api.v1.views_users.createProvider'), data, **self.extra)
		self.assertEqual(response.content, err_GE002().content, response.status_code)
	
	def testCreateOfficeStaff(self):
		data = {
			'username':get_random_username(),
			'first_name':'c',
			'last_name':'tian',
			'mobile_phone':9001111111,
			'gender':'M',
			'email':'cprovider1@suzhoukada.com',
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
			'staff_type':3,
		}

		response = self.client.post(reverse('MHLogin.api.v1.views_users.createOfficeStaff'), data, **self.extra)
		self.assertEqual(response.status_code, 200, response.status_code)
		self.assertEqual(response.content, HttpJSONSuccessResponse().content, response.status_code)

		response = self.client.post(reverse('MHLogin.api.v1.views_users.createOfficeStaff'), **self.extra)
		self.assertEqual(json.loads(response.content)['errno'], 'GE031', response.status_code)
	
		response = self.client.get(reverse('MHLogin.api.v1.views_users.createOfficeStaff'), data, **self.extra)
		self.assertEqual(response.content, err_GE002().content, response.status_code)

	def testCreateBroker(self):
		data = {
			'username':get_random_username(),
			'first_name':'c',
			'last_name':'tian',
			'mobile_phone':9001111111,
			'gender':'M',
			'email':'cprovider1@suzhoukada.com',
			'lat':41.885805, 
			'longit':-87.6229106, 
			'address1':'address1', 
			'address2':'address2', 
			'city':'Chicago', 
			'state':'IL', 
			'zip':60601
		}

		response = self.client.post(reverse('MHLogin.api.v1.views_users.createBroker'), data, **self.extra)
		self.assertEqual(response.status_code, 200, response.status_code)
		self.assertEqual(response.content, HttpJSONSuccessResponse().content, response.status_code)

		response = self.client.post(reverse('MHLogin.api.v1.views_users.createBroker'), **self.extra)
		self.assertEqual(json.loads(response.content)['errno'], 'GE031', response.status_code)
	
		response = self.client.get(reverse('MHLogin.api.v1.views_users.createBroker'), data, **self.extra)
		self.assertEqual(response.content, err_GE002().content, response.status_code)
