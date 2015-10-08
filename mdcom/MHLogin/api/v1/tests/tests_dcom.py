# -*- coding: utf-8 -*-
import json

from django.core.urlresolvers import reverse

from MHLogin.MHLUsers.models import  Provider, OfficeStaff, MHLUser
from MHLogin.api.v1.utils import HttpJSONSuccessResponse
from MHLogin.api.v1.tests.utils import create_user, create_office_staff,\
	get_random_username, APITest
from django.conf import settings
from MHLogin.MHLPractices.models import PracticeLocation
from MHLogin.api.v1.errlib import err_GE002


class C2cTest(APITest):
	def testSmartPhoneCall(self):
		response = self.client.get(
			reverse('MHLogin.api.v1.views_dcom.smartPhoneCall'), **self.extra)
		self.assertEqual(response.content, err_GE002().content, response.status_code)

		user_uuid = self.extra['HTTP_MDCOM_USER_UUID']
		user = MHLUser.objects.get(uuid=user_uuid)

		user.mdcom_phone = '123'
		user.save()
		response = self.client.post(
			reverse('MHLogin.api.v1.views_dcom.smartPhoneCall'), **self.extra)
		self.assertEqual(json.loads(response.content)['errno'], 'GE031', response.status_code)

		user.mdcom_phone = '2561234567'
		user.save()
		kwargs = {'user_id': 0}
		data = {'caller_number': '2561234566'}
		response = self.client.post(reverse('MHLogin.api.v1.views_dcom.smartPhoneCall', 
					kwargs=kwargs), data, **self.extra)
		self.assertEqual(json.loads(response.content)['errno'], 'GE010', response.status_code)

		kwargs = {'user_id': user.id}
		data = {'caller_number': '2561234566'}
		return_data = {'number': ''.join(['+1', str(settings.TWILIO_C2C_NUMBER)])}
		response = self.client.post(
			reverse('MHLogin.api.v1.views_dcom.smartPhoneCall', kwargs=kwargs), data, **self.extra)
		self.assertEqual(json.loads(response.content)['data'], return_data, response.status_code)

		kwargs = {'practice_id': 0}
		response = self.client.post(reverse('MHLogin.api.v1.views_dcom.smartPhoneCall', 
			kwargs=kwargs), data, **self.extra)
		self.assertEqual(json.loads(response.content)['errno'], 'GE010', response.status_code)

		practice1 = PracticeLocation(
			practice_name='USA practice',
			practice_address1='555 Pleasant Pioneer Grove',
			practice_address2='Trailer Q615',
			practice_city='Mountain View',
			practice_state='CA',
			practice_zip='94040-4104',
			practice_lat=37.36876,
			practice_phone='2561234568',
			practice_longit=-122.081864)
		practice1.save()
		provider1 = create_user(get_random_username(), 
			"provider_first", "provider_last", "demo", "555 Bryant St.",
				"Palo Alto", "CA", "94306", uklass=Provider)
		provider1.address2 = 'suzhou china'
		provider1.user.save()
		provider1.practices.add(practice1)
		provider1.current_practice = practice1
		provider1.save()
		kwargs = {'practice_id': practice1.id}
		response = self.client.post(
			reverse('MHLogin.api.v1.views_dcom.smartPhoneCall', kwargs=kwargs), data, **self.extra)
		self.assertEqual(json.loads(response.content)['data'], return_data, response.status_code)

		kwargs = {}
		response = self.client.post(
			reverse('MHLogin.api.v1.views_dcom.smartPhoneCall', kwargs=kwargs), data, **self.extra)
		self.assertEqual(json.loads(response.content)['errno'], 'TE003', response.status_code)

	def testSmartPhoneMessageCallbackLogic(self):
		message_id = "00001111222233334444555566667777"
		response = self.client.post(
			reverse('MHLogin.api.v1.views_dcom.smartPhoneMessageCallback', 
				args=(message_id,)), {}, **self.extra)
		self.assertEqual(response.status_code, 404, response.status_code)

	def testPageUser(self):
		response = self.client.get(
			reverse('MHLogin.api.v1.views_dcom.pageUser', args=(0,)), **self.extra)
		self.assertEqual(response.content, err_GE002().content, response.status_code)

		response = self.client.post(
			reverse('MHLogin.api.v1.views_dcom.pageUser', args=(0,)), **self.extra)
		self.assertEqual(json.loads(response.content)['errno'], 'GE031', response.status_code)

		data = {'number': '2561234566'}
		response = self.client.post(
			reverse('MHLogin.api.v1.views_dcom.pageUser', args=(0,)), data, **self.extra)
		self.assertEqual(json.loads(response.content)['errno'], 'GE010', response.status_code)

		provider1 = create_user(get_random_username(), 
			"provider_first", "provider_last", "demo", "555 Bryant St.",
				"Palo Alto", "CA", "94306", uklass=Provider)
		provider1.address2 = 'suzhou china'
		provider1.user.save()
		provider1.save()
		response = self.client.post(reverse('MHLogin.api.v1.views_dcom.pageUser',
			args=(provider1.id,)), data, **self.extra)
		self.assertEqual(json.loads(response.content)['errno'], 'TE002', response.status_code)

		provider1.pager = 2561234567
		provider1.save()
		response = self.client.post(reverse('MHLogin.api.v1.views_dcom.pageUser', 
			args=(provider1.id,)), data, **self.extra)
		self.assertEqual(response.content, HttpJSONSuccessResponse().content, response.status_code)

		staff1 = create_office_staff(get_random_username(), "staff_first1", "staff_last1", 
			"demo", "suzhou china", "suzhou", "AB", "25011", uklass=OfficeStaff)
		staff1.save()
		response = self.client.post(reverse('MHLogin.api.v1.views_dcom.pageUser', 
			args=(staff1.user.id,)), data, **self.extra)
		self.assertEqual(json.loads(response.content)['errno'], 'TE002', response.status_code)

		staff1.pager = 2561234568
		staff1.save()
		response = self.client.post(reverse('MHLogin.api.v1.views_dcom.pageUser',
			args=(staff1.user.id,)), data, **self.extra)
		self.assertEqual(response.content, HttpJSONSuccessResponse().content, response.status_code)

	def testCallLogic(self):
		pass
#
