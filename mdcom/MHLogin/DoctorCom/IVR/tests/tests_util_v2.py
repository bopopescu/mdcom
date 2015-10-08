from django.test import TestCase
from MHLogin.DoctorCom.IVR.utils import _sanityCheckNumber, _matchUSNumber, _getUSNumber, _makeUSNumber
from MHLogin.MHLUsers.models import MHLUser, Administrator
from MHLogin.utils.tests import create_user

class TestIVRUtil(TestCase):

	def setUp(self):
		# http://code.djangoproject.com/ticket/10899
		self.client.post('/login/', {'username': self.admin.user.username,
									'password': 'demo'})
#		settings.SESSION_ENGINE = 'django.contrib.sessions.backends.file'
#		engine = importlib.import_module('django.contrib.sessions.backends.file')
#		store = engine.SessionStore()
#		store.save()

#		self.session = store
#		self.client.cookies[settings.SESSION_COOKIE_NAME] = store.session_key

	@classmethod
	def setUpClass(cls):
		# create a user to login creating a session needed by ivr tests
		cls.admin = create_user("ivrguy", "ivr", "guy", "demo",
			"Ocean Avenue", "Carmel", "CA", "93921", uklass=Administrator)

	@classmethod
	def tearDownClass(cls):
		Administrator.objects.all().delete()
		MHLUser.objects.all().delete()

	def tearDown(self):
#		store = self.session
#		os.unlink(store._key_to_file())
		self.client.logout()

	def test_sanityCheckNumber(self):
		num1 = '123456'
		num2 = '+120394'
		num3 = 'ab123400'
		num4 = ''
		self.assertEquals(_sanityCheckNumber(num1), True)
		self.assertEquals(_sanityCheckNumber(num2), True)
		self.assertEquals(_sanityCheckNumber(num3), False)
		self.assertEquals(_sanityCheckNumber(num4), False)

	def test_matchUSNumber(self):
		num1 = '+14085551234'
		num2 = '+652552928171'
		num3 = '14082345982'
		self.assertEquals(_matchUSNumber(num1), True)
		self.assertEquals(_matchUSNumber(num2), False)
		self.assertEquals(_matchUSNumber(num3), False)

	def test_getUSNumber(self):
		num1 = '+14085551234'
		num2 = '+652552928171'
		num3 = '4082345982'
		self.assertEquals(_getUSNumber(num1), '4085551234')
		self.assertEquals(_getUSNumber(num2), '652552928171')
		self.assertEquals(_getUSNumber(num3), '4082345982')

	def test_makeUSNumber(self):
		num1 = '4085551234'
		num2 = '+14085551234'
		num3 = '14082345912'
		self.assertEquals(_makeUSNumber(num1), '+14085551234')
		self.assertEquals(_makeUSNumber(num2), '+14085551234')
		self.assertEquals(_makeUSNumber(num3), '+114082345912')
