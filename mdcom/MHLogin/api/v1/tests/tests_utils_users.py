
import mock

from django.http import Http404
from django.test.testcases import TestCase

from MHLogin.MHLUsers.models import Provider, Physician, OfficeStaff, \
	Office_Manager, Nurse, NP_PA
from MHLogin.api.v1.tests.utils import create_user, get_random_username, \
	create_office_staff
from MHLogin.api.v1.utils_users import getUserInfo, setOfficeStaffResultList, \
	setSubProviderResultList, setProviderResultList, getStaffList, getProviderList
from MHLogin.MHLPractices.models import PracticeLocation
from MHLogin.MHLSites.models import Site
from MHLogin.MHLOrganization.utils import get_custom_logos


class UtilsUsersTest(TestCase):

	def tearDown(self):
		Provider.objects.all().delete()
		Physician.objects.all().delete()
		OfficeStaff.objects.all().delete()
		Office_Manager.objects.all().delete()
		Nurse.objects.all().delete()
		NP_PA.objects.all().delete()
		PracticeLocation.objects.all().delete()

	@classmethod
	def mock_geocode(cls, addr, city, state, zipcode):
		""" Mock geocode so we don't go out to network.  Return well-known
		coordinates for providers in testGetProviderList(). """
		cords = {'94306': (37.4177563, -122.1235054), 
				'94307': (48.4401399, 38.8180129),
				'43523': (41.3416799, -83.99869),
				'25010': (37.4483533, -122.1590441),
				'25011': (31.2650381, 121.0791538),				
				}
		return {'lat': cords[zipcode][0], 'lng': cords[zipcode][1], 'msg': ''}

	@mock.patch('MHLogin.api.v1.tests.utils.geocode2', 
		new_callable=lambda: UtilsUsersTest.mock_geocode)
	def testGetProviderList(self, mockgeo):
		practice1 = PracticeLocation(
			practice_name='USA practice',
			practice_address1='555 Pleasant Pioneer Grove',
			practice_address2='Trailer Q615',
			practice_city='Mountain View',
			practice_state='CA',
			practice_zip='94040-4104',
			practice_lat=37.36876,
			practice_longit=-122.081864)
		practice1.save()

		practice2 = PracticeLocation(
			practice_name='China practice',
			practice_address1='jiangsu',
			practice_address2='beijing',
			practice_city='suzhou',
			practice_state='JS',
			practice_zip='94040-4104',
			practice_lat=37.36876,
			practice_longit=-122.081864)
		practice2.save()

		site1 = Site(
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
		site1.save()

		site2 = Site(
				name='doctorcom',
				address1='555 Pleasant Pioneer Grove',
				address2='Trailer Q615',
				city='Mountain View',
				state='CA',
				zip='94040-4104',
				lat=37.36876,
				longit=-122.081864,
				short_name='MSite'
			)
		site2.save()

		provider1 = create_user("prov1", "provider_first", 
			"provider_last", "demo", "555 Bryant St.", "Palo Alto", "CA", 
			"94306", uklass=Provider)
		provider1.address2 = 'suzhou china'
		provider1.user.save()
		provider1.sites.add(site1)
		provider1.sites.add(site2)
		provider1.current_site = site1
		provider1.practices.add(practice1)
		provider1.practices.add(practice2)
		provider1.current_practice = practice1
		provider1.save()
		provider2 = create_user("prov2", "provider_first1", "provider_last1", 
				"demo", "suzhou china", "suzhou", "AB", "94307", uklass=Provider)
		provider2.sites.add(site2)
		provider2.current_site = site2
		provider2.practices.add(practice2)
		provider2.current_practice = practice2
		provider2.save()

		condition_dicts = [
					{'name':u'provider', 'result':2, 'result_failed':'name failed'},
					{'name':u'last1 first1', 'result':1, 'result_failed':'name failed'},
					{'name':u'abc', 'result':0, 'result_failed':'name failed'},
					{'address':u'Bryant', 'result':1, 'result_failed':'address failed'},
					{'address':u'suzhou china', 'result':2, 'result_failed':'address failed'},
					{'address':u'abc', 'result':0, 'result_failed':'address failed'},
					{'city':u'Palo', 'result':1, 'result_failed':'city failed'},
					{'city':u'suzhou', 'result':1, 'result_failed':'city failed'},
					{'city':u'abc', 'result':0, 'result_failed':'city failed'},
					{'state':u'CA', 'result':1, 'result_failed':'state failed'},
					{'state':u'AB', 'result':1, 'result_failed':'state failed'},
					{'state':u'abc', 'result':0, 'result_failed':'state failed'},
  					{'zip':provider1.zip, 'result':1, 'result_failed':'zip failed1'},
  					{'zip':provider2.zip, 'result':1, 'result_failed':'zip failed2'},
  					{'zip':provider2.zip, 'distance':5000, 'result':1, 'result_failed':'zip failed3'},
  					{'zip':u'43523', 'result':0, 'result_failed':'zip failed'},
					{'current_hospital':u'doctorcom', 'result':1, 'result_failed':'current_hospital failed'},
					{'current_hospital':u'mysite', 'result':1, 'result_failed':'current_hospital failed'},
					{'current_hospital':u'22222', 'result':0, 'result_failed':'current_hospital failed'},
					{'hospital':u'mysite', 'result':1, 'result_failed':'hospital failed'},
					{'hospital':u'doctorcom', 'result':2, 'result_failed':'hospital failed'},
					{'hospital':u'abc', 'result':0, 'result_failed':'hospital failed'},
					{'current_practice':u'USA practice', 'result':1, 'result_failed':'current_practice failed'},
					{'current_practice':u'China practice', 'result':1, 'result_failed':'current_practice failed'},
					{'current_practice':u'abc', 'result':0, 'result_failed':'current_practice failed'},
					{'practice':u'USA practice', 'result':1, 'result_failed':'practice failed'},
					{'practice':u'China practice', 'result':2, 'result_failed':'practice failed'},
					{'practice':u'abc', 'result':0, 'result_failed':'practice failed'},
					{'limit':0, 'result':2, 'result_total':2, 'result_failed':'limit failed'},
					{'limit':1, 'result':1, 'result_total':2, 'result_failed':'limit failed'},
					{'limit':2, 'result':2, 'result_total':2, 'result_failed':'limit failed'},
					{
						'name':u'provider', 'address':u'suzhou china', 'city':u'suzhou', 'state':u'AB',
						'current_hospital':u'doctorcom',
						'hospital':u'doctorcom', 'current_practice':u'China practice',
						'limit':1, 'result':1, 'result_total':1, 'result_failed':'all failed'
					},
					{
						'name':u'abc', 'address':u'suzhou china', 'city':u'suzhou', 'state':u'AB',
						'zip':provider2.zip, 'current_hospital':u'doctorcom',
						'hospital':u'doctorcom', 'current_practice':u'China practice',
						'limit':1, 'result':0, 'result_total':0, 'result_failed':'all failed'
					},
			]

		with mock.patch('MHLogin.api.v1.utils_users.geocode2', 
						new_callable=lambda: UtilsUsersTest.mock_geocode):
			for d in condition_dicts:
				result = getProviderList(d)
				if 'result_total' not in d:
					d['result_total'] = d['result']
				self.assertEqual(d['result_total'], result['total_count'], d['result_failed'])
				self.assertEqual(d['result'], len(result['results']), d['result_failed'])

		phy2 = Physician(user=provider1)
		phy2.specialty = 'AC'
		phy2.save()

		nppa = NP_PA(user=provider2)
		nppa.save()

		condition_dicts = [
					{'specialty':u'AC', 'result':1, 'result_failed':'specialty failed'},
					{'specialty':u'NP/PA/Midwife', 'result':1, 'result_failed':'specialty failed'},
					{'specialty':u'abc', 'result':2, 'result_failed':'specialty failed'},
		]
		for d in condition_dicts:
			result = getProviderList(d)
			if 'result_total' not in d:
				d['result_total'] = d['result']
			self.assertEqual(d['result_total'], result['total_count'], d['result_failed'])
			self.assertEqual(d['result'], len(result['results']), d['result_failed'])

	@mock.patch('MHLogin.api.v1.tests.utils.geocode2', 
 		new_callable=lambda: UtilsUsersTest.mock_geocode)
	def testGetStaffList(self, mockgeo):
		practice1 = PracticeLocation(
			practice_name='USA practice',
			practice_address1='555 Pleasant Pioneer Grove',
			practice_address2='Trailer Q615',
			practice_city='Mountain View',
			practice_state='CA',
			practice_zip='94040-4104',
			practice_lat=37.36876,
			practice_longit=-122.081864)
		practice1.save()

		practice2 = PracticeLocation(
			practice_name='China practice',
			practice_address1='jiangsu',
			practice_address2='beijing',
			practice_city='suzhou',
			practice_state='JS',
			practice_zip='94040-4104',
			practice_lat=37.36876,
			practice_longit=-122.081864)
		practice2.save()

		site1 = Site(
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
		site1.save()

		site2 = Site(
				name='doctorcom',
				address1='555 Pleasant Pioneer Grove',
				address2='Trailer Q615',
				city='Mountain View',
				state='CA',
				zip='94040-4104',
				lat=37.36876,
				longit=-122.081864,
				short_name='MSite'
			)
		site2.save()

		staff1 = create_office_staff(get_random_username(), "staff_first", "staff_last", 
				"demo", "555 Bryant St.", "Palo Alto", "CA", "25010", uklass=OfficeStaff)
		staff1.user.address2 = 'suzhou china'
		staff1.user.save()
		staff1.sites.add(site1)
		staff1.sites.add(site2)
		staff1.current_site = site1
		staff1.practices.add(practice1)
		staff1.practices.add(practice2)
		staff1.current_practice = practice1
		staff1.save()
		staff2 = create_office_staff(get_random_username(), "staff_first1", "staff_last1", 
				"demo", "suzhou china", "suzhou", "AB", "25011", uklass=OfficeStaff)
		staff2.sites.add(site2)
		staff2.current_site = site2
		staff2.practices.add(practice2)
		staff2.current_practice = practice2
		staff2.save()

		condition_dicts = [
				{'name':u'staff', 'result':2, 'result_failed':'name failed'},
				{'name':u'last1 first1', 'result':1, 'result_failed':'name failed'},
				{'name':u'abc', 'result':0, 'result_failed':'name failed'},
				{'address':u'Bryant', 'result':1, 'result_failed':'address failed'},
				{'address':u'suzhou china', 'result':2, 'result_failed':'address failed'},
				{'address':u'abc', 'result':0, 'result_failed':'address failed'},
				{'city':u'Palo', 'result':1, 'result_failed':'city failed'},
				{'city':u'suzhou', 'result':1, 'result_failed':'city failed'},
				{'city':u'abc', 'result':0, 'result_failed':'city failed'},
				{'state':u'CA', 'result':1, 'result_failed':'state failed'},
				{'state':u'AB', 'result':1, 'result_failed':'state failed'},
				{'state':u'abc', 'result':0, 'result_failed':'state failed'},
				{'zip':staff1.user.zip, 'result':1, 'result_failed':'zip failed'},
				{'zip':staff2.user.zip, 'result':1, 'result_failed':'zip failed'},
				{'zip':u'22222', 'result':0, 'result_failed':'zip failed'},
				{'current_hospital':u'doctorcom', 'result':1, 'result_failed':'current_hospital failed'},
				{'current_hospital':u'mysite', 'result':1, 'result_failed':'current_hospital failed'},
				{'current_hospital':u'22222', 'result':0, 'result_failed':'current_hospital failed'},
				{'hospital':u'mysite', 'result':1, 'result_failed':'hospital failed'},
				{'hospital':u'doctorcom', 'result':2, 'result_failed':'hospital failed'},
				{'hospital':u'abc', 'result':0, 'result_failed':'hospital failed'},
				{'current_practice':u'USA practice', 'result':1, 'result_failed':'current_practice failed'},
				{'current_practice':u'China practice', 'result':1, 'result_failed':'current_practice failed'},
				{'current_practice':u'abc', 'result':0, 'result_failed':'current_practice failed'},
				{'practice':u'USA practice', 'result':1, 'result_failed':'practice failed'},
				{'practice':u'China practice', 'result':2, 'result_failed':'practice failed'},
				{'practice':u'abc', 'result':0, 'result_failed':'practice failed'},
				{'limit':0, 'result':2, 'result_total':2, 'result_failed':'limit failed'},
				{'limit':1, 'result':1, 'result_total':2, 'result_failed':'limit failed'},
				{'limit':2, 'result':2, 'result_total':2, 'result_failed':'limit failed'},
				{
					'name':u'staff', 'address':u'suzhou china', 'city':u'suzhou', 'state':u'AB',
					'zip':staff2.user.zip, 'current_hospital':u'doctorcom',
					'hospital':u'doctorcom', 'current_practice':u'China practice',
					'limit':1, 'result':1, 'result_total':1, 'result_failed':'all failed'
				},
				{
					'name':u'abc', 'address':u'suzhou china', 'city':u'suzhou', 'state':u'AB',
					'zip':staff2.user.zip, 'current_hospital':u'doctorcom',
					'hospital':u'doctorcom', 'current_practice':u'China practice',
					'limit':1, 'result':0, 'result_total':0, 'result_failed':'all failed'
				},
			]

		for d in condition_dicts:
			result = getStaffList(d)
			if 'result_total' not in d:
				d['result_total'] = d['result']
			self.assertEqual(d['result_total'], result['total_count'], d['result_failed'])
			self.assertEqual(d['result'], len(result['results']), d['result_failed'])

	def testSetProviderResultList(self):
		provider = create_user(get_random_username(), "nppa", "thj", "demo", 
							"555 Bryant St.", "Palo Alto", "CA", "", uklass=Provider)
		provider.save()
		nppa = NP_PA(user=provider)
		nppa.save()

		provider1 = create_user(get_random_username(), "physician", "thj", "demo", 
							"555 Bryant St.", "Palo Alto", "CA", "", uklass=Provider)
		provider1.save()
		phy = Physician(user=provider1)
		phy.specialty = 'AC'
		phy.save()

		practice = PracticeLocation(
			practice_address1='555 Pleasant Pioneer Grove',
			practice_address2='Trailer Q615',
			practice_city='Mountain View',
			practice_state='CA',
			practice_zip='94040-4104',
			practice_lat=37.36876,
			practice_longit=-122.081864)
		practice.save()

		provider2 = create_user(get_random_username(), "nppa", "thj", "demo", 
							"555 Bryant St.", "Palo Alto", "CA", "", uklass=Provider)
		provider2.practices.add(practice)
		provider2.current_practice = practice
		provider2.save()
		nppa2 = NP_PA(user=provider2)
		nppa2.save()

		provider3 = create_user(get_random_username(), "physician", "thj", "demo", 
							"555 Bryant St.", "Palo Alto", "CA", "", uklass=Provider)
		provider3.practices.add(practice)
		provider3.current_practice = practice
		provider3.save()
		phy2 = Physician(user=provider3)
		phy2.specialty = 'AC'
		phy2.save()

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

		provider4 = create_user(get_random_username(), "nppa", "thj", "demo", 
							"555 Bryant St.", "Palo Alto", "CA", "", uklass=Provider)
		provider4.sites.add(site)
		provider4.current_site = site
		provider4.save()
		nppa3 = NP_PA(user=provider4)
		nppa3.save()

		provider5 = create_user(get_random_username(), "physician", "thj", "demo", 
							"555 Bryant St.", "Palo Alto", "CA", "", uklass=Provider)
		provider5.sites.add(site)
		provider5.current_site = site
		provider5.save()
		phy3 = Physician(user=provider5)
		phy3.specialty = 'AC'
		phy3.save()

		self.assertEqual(0, len(setProviderResultList([])), 'test failed for setProviderResultList')
		self.assertEqual(1, len(setProviderResultList([nppa.user], phy.user)), 
						'test failed for setProviderResultList')
		self.assertEqual(1, len(setProviderResultList([phy.user])), 'test failed for setProviderResultList')
		self.assertEqual(1, len(setProviderResultList([nppa2.user])), 'test failed for setProviderResultList')
		self.assertEqual(1, len(setProviderResultList([phy2.user])), 'test failed for setProviderResultList')
		self.assertEqual(1, len(setProviderResultList([nppa3.user])), 'test failed for setProviderResultList')
		self.assertEqual(1, len(setProviderResultList([phy3.user])), 'test failed for setProviderResultList')
		self.assertEqual(6, len(setProviderResultList([nppa.user, phy.user, nppa2.user, phy2.user,
				nppa3.user, phy3.user])), 'test failed for setProviderResultList')

	def testSetSubProviderResultList(self):
		provider = create_user(get_random_username(), "provider", "thj", "demo", 
							"555 Bryant St.", "Palo Alto", "CA", "", uklass=Provider)
		provider.save()
		nppa = NP_PA(user=provider)
		nppa.save()

		provider1 = create_user(get_random_username(), "physician", "thj", "demo", 
							"555 Bryant St.", "Palo Alto", "CA", "", uklass=Provider)
		provider1.save()
		phy = Physician(user=provider1)
		phy.specialty = 'AC'
		phy.save()

		self.assertEqual(0, len(setSubProviderResultList([], phy)), 
						'test failed for setSubProviderResultList')
		self.assertEqual(1, len(setSubProviderResultList([nppa], phy)), 
						'test failed for setSubProviderResultList')
		self.assertEqual(2, len(setSubProviderResultList([nppa, phy])), 
						'test failed for setSubProviderResultList')

	def testSetOfficeStaffResultList(self):
# 		create office staff
		staff = create_office_staff(get_random_username(), "staff", "thj", "demo",
						"555 Bryant St.", "Palo Alto", "CA", "", uklass=OfficeStaff)
		staff2 = create_office_staff(get_random_username(), "nurse", "thj", "demo",
						"555 Bryant St.", "Palo Alto", "CA", "", uklass=OfficeStaff)
		nurse = Nurse(user=staff2)
		nurse.save()
		staff3 = create_office_staff(get_random_username(), "maneger", "thj", "demo",
						"555 Bryant St.", "Palo Alto", "CA", "", uklass=OfficeStaff)
		mgr = Office_Manager(user=staff3)
		practice = PracticeLocation(
			practice_address1='555 Pleasant Pioneer Grove',
			practice_address2='Trailer Q615',
			practice_city='Mountain View',
			practice_state='CA',
			practice_zip='94040-4104',
			practice_lat=37.36876,
			practice_longit=-122.081864)
		practice.save()
		mgr.manager_role = 1
		mgr.practice = practice
		mgr.save()

		mhlu = create_user(get_random_username(), "mhluser", "thj", "demo", 
						"555 Bryant St.", "Palo Alto", "CA", "")
		mhlu.mdcom_phone = '9002000001'
		mhlu.save()

		self.assertEqual(0, len(setOfficeStaffResultList([])), 
						'test failed for setOfficeStaffResultList null')
		self.assertEqual(1, len(setOfficeStaffResultList([staff])), 
						'test failed for setOfficeStaffResultList staff')
# 		self.assertEqual(1, len(setOfficeStaffResultList([nurse])), 
						#'test failed for setOfficeStaffResultList nurse')
		self.assertEqual(1, len(setOfficeStaffResultList([mgr])), 
						'test failed for setOfficeStaffResultList mgr')
		self.assertEqual(3, len(setOfficeStaffResultList([staff, nurse.user, mgr])), 
						'test failed for setOfficeStaffResultList')
		self.assertEqual(3, len(setOfficeStaffResultList([staff, nurse.user, mgr], staff)), 
						'test failed for setOfficeStaffResultList')

	def testGetUserInfo(self):
		mhlu = create_user(get_random_username(), "mhluser", "thj", "demo", "555 Bryant St.", 
						"Palo Alto", "CA", "")
		mhlu.mdcom_phone = '9002000001'
		mhlu.save()
		mhlu_id = mhlu.id

		return_data1 = {'last_name': u'thj', 'office_address1': u'555 Bryant St.',
					'office_address2': u'', 'photo': '/media/images/photos/generic_128.png',
					'specialty': '', 'mdcom_phone': '', 'office_city': u'Palo Alto',
					'accepting_patients': False, 'id': mhlu_id, 'custom_logos': get_custom_logos(mhlu_id),
					'first_name': u'mhluser', 'office_state': u'CA', 'office_zip': u'', 'staff_type': ''}
		self.assertEqual(Http404, getUserInfo(mhlu_id + 1, None), 'test failed for getUserInfo')
		self.assertEqual(return_data1, getUserInfo(mhlu_id), 'test failed for getUserInfo mhluser')

		# create provider for test
		provider = create_user(get_random_username(), "provider", "thj", "demo",
							"555 Bryant St.", "Palo Alto", "CA", "", uklass=Provider)
		provider.mdcom_phone = '9002000002'
		provider.save()

		return_data2 = {'last_name': u'thj', 'office_address1': u'555 Bryant St.',
					'office_address2': u'', 'photo': '/media/images/photos/avatar2.png',
					'specialty': 'NP/PA/Midwife', 'mdcom_phone': u'9002000002', 'office_city': u'Palo Alto',
					'accepting_patients': False, 'id': provider.user.id,
					'custom_logos': get_custom_logos(mhlu_id), 'first_name': u'provider',
					'office_state': u'CA', 'office_zip': u'', 'staff_type': ''}
		self.assertEqual(return_data2, getUserInfo(provider.user.id), 'test failed for getUserInfo provider')

		# create physician
		provider1 = create_user(get_random_username(), "physician", "thj", "demo", "555 Bryant St.",
							"Palo Alto", "CA", "", uklass=Provider)
		provider1.mdcom_phone = '9002000002'
		provider1.save()
		phy = Physician(user=provider1)
		phy.specialty = 'AC'
		phy.save()
		return_data3 = {'last_name': u'thj', 'office_address1': u'555 Bryant St.',
					'office_address2': u'', 'photo': '/media/images/photos/avatar2.png',
					'specialty': u'Acupuncture', 'mdcom_phone': u'9002000002',
					'office_city': u'Palo Alto', 'accepting_patients': True,
					'id': phy.user.user.id, 'custom_logos': get_custom_logos(mhlu_id),
					'first_name': u'physician', 'office_state': u'CA', 'office_zip': u'',
					'staff_type': ''}
		self.assertEqual(return_data3, getUserInfo(phy.user.user.id), 'test failed for getUserInfo physician')

# 		create office staff
		staff = create_office_staff(get_random_username(), "staff", "thj", "demo", "555 Bryant St.",
					"Palo Alto", "CA", "", uklass=OfficeStaff)
		return_data4 = {'last_name': u'thj', 'office_address1': u'555 Bryant St.',
					'office_address2': u'', 'photo': '/media/images/photos/staff_icon.jpg',
					'specialty': '', 'mdcom_phone': '', 'office_city': u'Palo Alto',
					'accepting_patients': False, 'id': staff.user.id,
					'custom_logos': get_custom_logos(mhlu_id), 'first_name': u'staff',
					'office_state': u'CA', 'office_zip': u'', 'staff_type': 'Office Staff'}
		self.assertEqual(return_data4, getUserInfo(staff.user.id), 'test failed for getUserInfo staff')

# 		create nurse
		staff2 = create_office_staff(get_random_username(), "nurse", "thj", "demo",
					"555 Bryant St.", "Palo Alto", "CA", "", uklass=OfficeStaff)
		nurse = Nurse(user=staff2)
		nurse.save()
		return_data5 = {'last_name': u'thj', 'office_address1': u'555 Bryant St.',
				'office_address2': u'', 'photo': '/media/images/photos/nurse.jpg',
				'specialty': '', 'mdcom_phone': '', 'office_city': u'Palo Alto',
				'accepting_patients': False, 'id': nurse.user.user.id,
				'custom_logos': get_custom_logos(mhlu_id), 'first_name': u'nurse',
				'office_state': u'CA', 'office_zip': u'', 'staff_type': 'Office Staff'}
		self.assertEqual(return_data5, getUserInfo(nurse.user.user.id), 'test failed for getUserInfo nurse')

# 		create office staff
		staff3 = create_office_staff(get_random_username(), "maneger", "thj", "demo",
				"555 Bryant St.", "Palo Alto", "CA", "", uklass=OfficeStaff)
		mgr = Office_Manager(user=staff3)

		practice = PracticeLocation(
			practice_address1='555 Pleasant Pioneer Grove',
			practice_address2='Trailer Q615',
			practice_city='Mountain View',
			practice_state='CA',
			practice_zip='94040-4104',
			practice_lat=37.36876,
			practice_longit=-122.081864)
		practice.save()
		mgr.manager_role = 1
		mgr.practice = practice
		mgr.save()
		return_data5 = {'last_name': u'thj', 'office_address1': u'555 Bryant St.',
				'office_address2': u'', 'photo': '/media/images/photos/staff_icon.jpg',
				'specialty': '', 'mdcom_phone': '', 'office_city': u'Palo Alto',
				'accepting_patients': False, 'id': mgr.user.user.id,
				'custom_logos': get_custom_logos(mhlu_id), 'first_name': u'maneger',
				'office_state': u'CA', 'office_zip': u'', 'staff_type': 'Office Manager'}
		self.assertEqual(return_data5, getUserInfo(mgr.user.user.id), 'test failed for getUserInfo maneger')

