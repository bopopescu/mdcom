
import datetime
import mock

from django.contrib.auth.models import User
from django.test.testcases import TestCase

from MHLogin.MHLCallGroups.Scheduler.models import EventEntry
from MHLogin.MHLCallGroups.models import CallGroup
from MHLogin.MHLPractices.models import PracticeLocation, OrganizationType,\
	OrganizationSetting
from MHLogin.MHLPractices.utils import get_practices_by_position, \
	mail_managers, _mail_managers_context_update, \
	get_level_by_staff, checkUserCrossDay, getCurrentPractice, \
	getNewCreateCode, changeCurrentPracticeForStaff
from MHLogin.MHLUsers.models import OfficeStaff, Office_Manager, Provider, \
	MHLUser
from MHLogin.utils.tests import create_user
from MHLogin.utils.constants import RESERVED_ORGANIZATION_TYPE_ID_PRACTICE
from MHLogin.utils.tests.tests import clean_db_datas


#add by xlin 121225 to test get_practices_by_position
class Get_practices_by_positionTest(TestCase):

	def setUp(self):
		clean_db_datas()

	def test_get_practices_by_position(self):
		lat = 0.0
		longit = 0.0
		distance = None
		result = get_practices_by_position(lat, longit, distance)
		self.assertEqual(len(result), 0)
		
		lat = 12.1
		longit = 12.0
		distance = 2
		result = get_practices_by_position(lat, longit, distance)
		self.assertEqual(len(result), 0)

		try:
			org_type = OrganizationType.objects.get(pk=RESERVED_ORGANIZATION_TYPE_ID_PRACTICE)
		except OrganizationType.DoesNotExist:
			setting= OrganizationSetting()
			setting.save()
			org_type = OrganizationType(pk=RESERVED_ORGANIZATION_TYPE_ID_PRACTICE, organization_setting=setting)
			org_type.save()

		location = PracticeLocation(
			practice_address1='555 Pleasant Pioneer Grove',
			practice_address2='Trailer Q615',
			practice_city='Mountain View',
			practice_state='CA',
			practice_zip='94040-4104',
			practice_lat=37.36876,
			practice_longit= -122.081864,
			organization_type=org_type)
		location.save()
		
		lat = 37
		longit = -122.0
		distance = None
		result = get_practices_by_position(lat, longit, distance)
		self.assertEqual(len(result), 1)
		
#add by xlin 121225 to test mail_managers
class Mail_managersTest(TestCase):
	def test_mail_managers(self):
		practice = PracticeLocation(
			practice_address1='555 Pleasant Pioneer Grove',
			practice_address2='Trailer Q615',
			practice_city='Mountain View',
			practice_state='CA',
			practice_zip='94040-4104',
			practice_lat=37.36876,
			practice_longit= -122.081864)
		practice.save()
		subject = 'abc'
		body = 'test'
		sender = None
		
		result = mail_managers(practice, subject, body, sender)
		self.assertIsNone(result)
		
		sender = 'xlin@suzhoukada.com'
		result = mail_managers(practice, subject, body, sender)
		self.assertIsNone(result)

#add by xlin 121225 to test _mail_managers_context_update
class Mail_managers_context_updateTest(TestCase):
	def test_mail_managers_context_update(self):
		context = dict()
		manager = 'ab'
		result = _mail_managers_context_update(context, manager)
		self.assertEqual(result['manager'],'ab')

#add by xlin 121225 to test get_level_by_staff
class GetLevelByStaffTest(TestCase):
	def test_getLevelByStaff(self):
		practice = PracticeLocation(
			practice_address1='555 Pleasant Pioneer Grove',
			practice_address2='Trailer Q615',
			practice_city='Mountain View',
			practice_state='CA',
			practice_zip='94040-4104',
			practice_lat=37.36876,
			practice_longit= -122.081864)
		practice.save()
		user = create_user('practicemgr1', 'lin', 'xing', 'demo')
		
		#not a manager login
		result = get_level_by_staff(user, practice)
		self.assertEqual(result, 0)
		
		staff = OfficeStaff(user=user)
		staff.save()
		
		manager = Office_Manager(user=staff, practice=practice, manager_role=2)
		manager.save()
		
		#a manager login
		result = get_level_by_staff(staff.id, practice)
		self.assertEqual(result, 2)

#add by xlin 121225 to test checkUserCrossDay
class CheckUserCrossDayTest(TestCase):
	def test_checkUserCrossDay(self):
		call_group = CallGroup(description='test', team='team')
		call_group.save()
		
		user = User(username='xlin', email='a@a.cn', password='demo', first_name='li', last_name='ds')
		user.save()
		
		result = checkUserCrossDay(user)
		self.assertEqual(result, True)
		startDate = datetime.datetime.now() + datetime.timedelta(days= -10)
		endDate = datetime.datetime.now() + datetime.timedelta(days=10)
		event = EventEntry(creator=user,
						oncallPerson=user,
						callGroup=call_group,
						startDate=startDate,
						endDate=endDate,
						title='test event',
						oncallLevel='0',
						eventStatus=1,
						checkString='abc'
						)
		event.save()
		result = checkUserCrossDay(user)
		self.assertEqual(result, False)

#add by xlin 121225 to test getCurrentPractice
class GetCurrentPracticeTest(TestCase):
	def test_getCurrentPractice(self):
		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice.save()
		user = create_user('practicemgr1', 'lin', 'xing', 'demo')
		
		#a mhluser login and call this method
		result = getCurrentPractice(user)
		self.assertEqual(result, '')
		
		#a provider login and call this method
		provider = Provider(username='provider', first_name='tes', last_name="meister", email='aa@ada.com',
					user=user, office_lat=0.0, office_longit=0.0)
		provider.current_practice = practice
		provider.save()
		
		result = getCurrentPractice(user)
		self.assertEqual(result, 'test')
		
		#a staff login and call this method
		staff = OfficeStaff(user=user)
		staff.current_practice = practice
		staff.save()
		result = getCurrentPractice(user)
		self.assertEqual(result, 'test')
#add by xlin in 121225 to test getNewCreateCode
class GetNewCreateCodeTest(TestCase):
	def test_getNewCreateCode(self):
		username = 'xlin'
		result = getNewCreateCode(username)
		self.assertEqual(len(result), 50)

#add by xlin 121225 to test changeCurrentPracticeForStaff
class ChangeCurrentPracticeForStaffTest(TestCase):
	@mock.patch('MHLogin.apps.smartphone.v1.views_account.thread.start_new_thread', autospec=True)
	def test_changeCurrentPracticeForStaff(self, start_thread):
		practice = PracticeLocation(
			practice_address1='555 Pleasant Pioneer Grove',
			practice_address2='Trailer Q615',
			practice_city='Mountain View',
			practice_state='CA',
			practice_zip='94040-4104',
			practice_lat=37.36876,
			practice_longit= -122.081864)
		practice.save()
		user = create_user('practicemgr1', 'lin', 'xing', 'demo')
		staff = OfficeStaff(user=user)
		staff.save()
		result = changeCurrentPracticeForStaff(practice.id, user.pk)
		self.assertEqual(result, practice)
		
		try:
			changeCurrentPracticeForStaff(0, user.pk)
		except:
			PracticeLocation.DoesNotExist
		try:
			result = changeCurrentPracticeForStaff(practice.id, 0)
		except:
			MHLUser.DoesNotExist
