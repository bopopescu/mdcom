
import random
import uuid

from django.test import TestCase
from django.test.client import Client

from MHLogin.MHLUsers.models import MHLUser, Administrator, OfficeStaff, \
	Provider
from MHLogin.utils.geocode import geocode2
from MHLogin.MHLSites.models import Site
from MHLogin.MHLPractices.models import PracticeLocation
from MHLogin.utils.tests.tests import clean_db_datas
from MHLogin.KMS.models import UserPrivateKey, OwnerPublicKey
from MHLogin.KMS.utils import create_default_keys
from MHLogin.DoctorCom.IVR.models import VMBox_Config
from MHLogin.DoctorCom.Messaging.models import MessageBodyUserStatus,\
	MessageBody, Message, MessageAttachmentDicom, MessageAttachment, MessageCC,\
	MessageRecipient, MessageRefer, MessageActionHistory


class APITest(TestCase):
	@classmethod
	def setUpClass(cls):
		clean_db_datas()
		cls.user = create_user(get_random_username(), "tian", "thj", "demo", 
			"555 Bryant St.", "Palo Alto", "CA", "", uklass=Provider)
		cls.user.mdcom_phone = '9001234123'
		cls.user.save()

		cls.client = Client()

		cls.extra = {
			'HTTP_MDCOM_API_KEY': 'TODO_OAUTH',  # TODO: update with OAuth, #2049
			'HTTP_MDCOM_USER_UUID': cls.user.uuid,
			'REMOTE_ADDR': '10.200.0.222',
		}

	@classmethod
	def tearDownClass(cls):
		MessageBodyUserStatus.objects.all().delete()
		MessageBody.objects.all().delete()
		MessageAttachmentDicom.objects.all().delete()
		MessageAttachment.objects.all().delete()
		MessageCC.objects.all().delete()
		MessageRecipient.objects.all().delete()
		MessageRefer.objects.all().delete()
		MessageActionHistory.objects.all().delete()
		Message.objects.all().delete()
		VMBox_Config.objects.all().delete()
		UserPrivateKey.objects.all().delete()
		OwnerPublicKey.objects.all().delete()
		Provider.objects.all().delete()
		clean_db_datas()


def create_user(username, first_name, last_name, password, 
			addr="", city="", state="", zipcode="", uklass=MHLUser):
	user = uklass(username=username, first_name=first_name, last_name=last_name)
	user.address1 = addr 
	user.city = city
	user.state = state
	user.zip = zipcode
	user.is_active = user.is_staff = user.tos_accepted = user.mobile_confirmed = True
	user.set_password(password)
	user.mobile_phone = random.randint(9001000000, 9009999999)

	if uklass == Administrator:
		user.is_superuser = True

	result = geocode2(user.address1, user.city, user.state, user.zip)
	user.lat = result['lat']
	user.longit = result['lng']

	if uklass != MHLUser:
		user.office_lat = 0.0
		user.office_longit = 0.0
	user.save()

	mhluser = user
	if uklass != MHLUser:
		user.user = MHLUser.objects.get(username=username)
		mhluser = MHLUser.objects.get(username=username)
		user.user = mhluser
		user.save()

	create_default_keys(mhluser)

	if uklass == Provider:
		# Generating the user's voicemail box configuration
		config = VMBox_Config(pin='')
		config.owner = user
		config.save()

	return user


def create_office_staff(username, first_name, last_name, password, 
			addr="", city="", state="", zipcode="", uklass=MHLUser):
	user = create_user(username, first_name, last_name, password, addr, city, state, zipcode, uklass=MHLUser)
	office_staff = OfficeStaff()
	office_staff.user = user
	office_staff.office_lat = 0.0
	office_staff.office_longit = 0.0
	office_staff.save()
	return office_staff


def get_random_username():
	return 'tian' + uuid.uuid4().hex[0:24]


def create_site():
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
	return site


def create_practice():
	practice = PracticeLocation(
			practice_name='USA practice',
			practice_address1='555 Pleasant Pioneer Grove',
			practice_address2='Trailer Q615',
			practice_city='Mountain View',
			practice_state='CA',
			practice_zip='94040-4104',
			practice_lat=37.36876,
			practice_longit=-122.081864)
	practice.save()
	return practice
