
from django.test import TestCase
from MHLogin.DoctorCom.IVR.models import VMBox_Config
from MHLogin.MHLUsers.models import Provider, MHLUser, OfficeStaff, Office_Manager, Administrator
from MHLogin.MHLPractices.models import PracticeLocation, OrganizationSetting
from MHLogin.MHLCallGroups.models import CallGroup, Specialty
from MHLogin.utils.tests import create_user
from MHLogin.KMS.models import OwnerPublicKey, UserPrivateKey


class TestIVRBase(TestCase):

	def setUp(self):
		# needed at login
		# create a user to login creating a session needed by ivr tests
		self.admin = create_user("ivrguy", "ivr", "guy", "demo",
							"Ocean Avenue", "Carmel", "CA", "93921", uklass=Administrator)
		# one office manager
		self.staff = create_user("bblazejowsky", "bill", "blazejowsky", "demo",
							"Ocean Avenue", "Carmel", "CA", "93921", uklass=OfficeStaff)
		self.staff.mobile_phone = '4085551234'
		PracticeLocation.objects.all().delete()
		# practice location data
		self.practice_data = [{
			"practice_name":"Test practice 1", "practice_address1":"555 Pleasant Pioneer Grove",
			"practice_address2": "Trailer Q615", "practice_city": "Mountain View",
			"practice_state": "CA", "practice_zip": "94040-4104", "mdcom_phone": "4085551111",
			"practice_phone": "4086661111", "time_zone": "US/Pacific", 'practice_lat': '37.36876',
			"practice_longit":"-122.081864"
			},
			{"practice_name":"San Jose Practice", "practice_address1":"123 McKee Road",
			"practice_address2": "", "practice_city": "San Jose",
			"practice_state": "CA", "practice_zip": "94455", "mdcom_phone": "4085552222",
			"practice_phone": "8006662222", "time_zone": "US/Pacific", 'practice_lat': '33.3',
			"practice_longit":"22.08"
			},
			{"practice_name":"Third Specialty Practice", "practice_address1":"123 specialty Road",
			"practice_address2": "", "practice_city": "San Ramon",
			"practice_state": "CA", "practice_zip": "90041", "mdcom_phone": "4085553333",
			"practice_phone": "8006663333", "time_zone": "US/Pacific", 'practice_lat': '23.3',
			"practice_longit":"102.08"
			},
			]
		# provider data
		self.prov_data = [
			{"username":"docA", "first_name":"bill", "last_name":"doc", "email":"docA@doctorcom.com", "password":"demo",
				"addr1":"Ocean Avenue", "addr2":"main drive", "city":"Carmel", "state":"CA", "zipcode":"93921",
				"phone":"4085551111", "mobile_phone":"4085559999",
				"office_address1": "3931 Easy Pioneer Knoll", "office_city": "san jose", "office_zip": "94062-2751",
				"office_phone": "", "office_state": "CA",
				"forward_mobile": True, "forward_other": False, "forward_office": False, "forward_vmail": False,
				"forward_anssvc": "VM", "forward_voicemail": "MO", "status_verified": True, "practices": [],
				"mdcom_phone": "8004664411", "mdcom_phone_sid": "123"
			},
			{"username":"docB", "first_name":"sam", "last_name":"sung", "email":"docB@doctorcom.com", "password":"demo",
				"addr1":"Main Street", "addr2":"main drive", "city":"Carmelita", "state":"CA", "zipcode":"93921",
				"phone":"4085552222", "mobile_phone":"4085558888",
				"office_address1": "1234 Easy Street", "office_city": "santa clara", "office_zip": "94060-2751",
				"office_phone": "", "office_state": "CA",
				"forward_mobile": True, "forward_other": False, "forward_office": False, "forward_vmail": False,
				"forward_anssvc": "VM", "forward_voicemail": "VM", "status_verified": True, "practices": [],
				"mdcom_phone": "8004664422", "mdcom_phone_sid": "321"
			},
			{"username":"docC", "first_name":"tim", "last_name":"tam", "email":"docC@doctorcom.com", "password":"demo",
				"addr1":"willow Street", "addr2":"", "city":"Cupertino", "state":"CA", "zipcode":"91234",
				"phone":"4085553333", "mobile_phone":"4085557777",
				"office_address1": "1234 Easy Street", "office_city": "santa clara", "office_zip": "94060-2751",
				"office_phone": "", "office_state": "CA",
				"forward_mobile": True, "forward_other": False, "forward_office": False, "forward_vmail": False,
				"forward_anssvc": "MO", "forward_voicemail": "MO", "status_verified": True, "practices": [],
				"mdcom_phone": "8004664433", "mdcom_phone_sid": "321"
			}]
		self.providers = []
		self._add_providers()
		self.practices = []
		self._add_practices()
		self.practice = self.practices[0]
		self.practice1 = self.practices[1]
		self.practice2 = self.practices[2]
		self.office_manager = Office_Manager()
		self.office_manager.manager_role = 1
		self.office_manager.user = self.staff
		self.office_manager.practice = self.practice
		self.staff.practices.add(self.practice)
		self.office_manager.save()
		self.client.post('/login/', {'username': self.admin.user.username,
									'password': 'demo'})

	def tearDown(self):
		OfficeStaff.objects.filter(id=self.staff.id).delete()
		PracticeLocation.objects.all().delete()
		CallGroup.objects.all().delete()
		Specialty.objects.all().delete()
		VMBox_Config.objects.all().delete()
		MHLUser.objects.all().delete()
		Provider.objects.all().delete()
		Administrator.objects.all().delete()
		self.client.logout()

	def _add_providers(self):
		for user in self.prov_data:
			self.pusr = None
			self.mhu = None
			self.prov = None
			pusr = Provider(username=user["username"], first_name=user["first_name"], last_name=user["last_name"])
			pusr.is_active = pusr.is_staff = pusr.tos_accepted = True
			pusr.set_password("demo")
			pusr.address1 = user['addr1']
			pusr.address2 = user['addr2']
			pusr.city = user['city']
			pusr.state = user['state']
			pusr.zip = user['zipcode']
			pusr.is_active = pusr.is_staff = pusr.tos_accepted = pusr.mobile_confirmed = pusr.email_confirmed = True
			pusr.phone = user['phone']
			pusr.mobile_phone = user['mobile_phone']
			pusr.skill = ""
			pusr.is_superuser = True
			pusr.office_address = user["office_address1"]
			pusr.office_address2 = ""
			pusr.office_phone = user["office_phone"]
			pusr.office_city = user["office_city"]
			pusr.office_state = user["office_state"]
			pusr.office_zip = user["office_zip"]
			pusr.forward_mobile = user["forward_mobile"]
			pusr.forward_office = user["forward_office"]
			pusr.forward_other = user["forward_other"]
			pusr.forward_vmail = user["forward_vmail"]
			pusr.forward_voicemail = user["forward_voicemail"]
			pusr.forward_anssvc = user["forward_anssvc"]
			pusr.mdcom_phone = user["mdcom_phone"]
			pusr.mdcom_phone_sid = user["mdcom_phone_sid"]
			pusr.status_verified = user["status_verified"]
			pusr.clinical_clerk = ""
			pusr.office_lat = 37.36876
			pusr.office_longit = -122.081864
			pusr.save()
			pusr.user = pusr
			user["id"] = pusr.id
			pusr.practices = user["practices"]
			pusr.save()
			vmbox = VMBox_Config(owner=pusr)
			vmbox.save()
			self.providers.append(pusr)

	def _add_practices(self):
		org_setting = OrganizationSetting(can_have_answering_service=True)
		org_setting.save()
		for pract in self.practice_data:
			practice = PracticeLocation.objects.create(
				practice_name=pract["practice_name"],
				practice_address1=pract["practice_address1"],
				practice_address2=pract["practice_address2"],
				practice_city=pract["practice_city"],
				practice_state=pract["practice_state"],
				practice_zip=pract["practice_zip"],
				mdcom_phone=pract["mdcom_phone"],
				practice_phone=pract["practice_phone"],
				time_zone=pract["time_zone"],
				practice_lat=pract["practice_lat"],
				practice_longit=pract["practice_longit"],
				organization_setting=org_setting)
			practice.save()
			self.practices.append(practice)
		self.callgroup1 = CallGroup(description="Team A", team="Team A", number_selection=2)
		self.callgroup1.save()
		self.callgroup2 = CallGroup(description="Team B", team="Team B", number_selection=3)
		self.callgroup2.save()
		self.callgroup3 = CallGroup(description="Team C", team="Team C", number_selection=4)
		self.callgroup3.save()
		self.callgroup4 = CallGroup(description="Team D", team="Team D", number_selection=5)
		self.callgroup4.save()
		p1 = self.practices[0]
		p1.call_group = self.callgroup1
		p1.save()
		p2 = self.practices[1]
		p2.call_groups.add(self.callgroup2)
		p2.save()
		p3 = self.practices[2]
		p3.call_groups.add(self.callgroup3)
		p3.call_groups.add(self.callgroup4)
		p3.save()
		self.specialty1 = Specialty()
		self.specialty1.name = 'Cardiology'
		self.specialty1.practice_location = self.practices[2]
		self.specialty1.number_selection = 3
		self.specialty1.save()
		self.specialty1.call_groups.add(self.callgroup3)
		self.specialty2 = Specialty()
		self.specialty2.name = 'ENT'
		self.specialty2.practice_location = self.practices[2]
		self.specialty2.number_selection = 4
		self.specialty2.save()
		self.specialty2.call_groups.add(self.callgroup4)
		# also set up practice hours etc

	def cleanup_rsa(self):
		OwnerPublicKey.objects.all().delete()
		UserPrivateKey.objects.all().delete()
