
import datetime
import json

from django.core import serializers
from django.core.urlresolvers import reverse
from django.http import HttpRequest
from django.test.testcases import TestCase
from django.utils.translation import ugettext as _

from MHLogin.MHLCallGroups.Scheduler.models import EventEntry
from MHLogin.MHLCallGroups.Scheduler.utils import SessionHelper, \
	checkDSEventConsistency, checkSchedulerView
from MHLogin.MHLCallGroups.Scheduler.views_multicallgroup import \
	joinCallGroup, validateNewEvent, getPenddings
from MHLogin.MHLCallGroups.models import CallGroup, CallGroupMember, Specialty, \
	CallGroupMemberPending
from MHLogin.MHLPractices.models import PracticeLocation
from MHLogin.MHLUsers.models import Office_Manager, OfficeStaff, Provider
from MHLogin.MHLUsers.utils import user_is_mgr_of_practice
from MHLogin.utils.tests import create_user
from MHLogin.utils.tests.tests import clean_db_datas


class MCDisplaySchedulerTest(TestCase):
	@classmethod
	def setUpClass(cls):
		clean_db_datas()
		cls.user = create_user('practicemgr1', 'lin', 'xing', 'demo', '', '', '', '',)

		group = CallGroup(description='test', team='team')
		group.save()
		cls.group = group

		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice.save()
		practice.call_groups.add(group)
		cls.practice = practice

	@classmethod
	def tearDownClass(cls):
		clean_db_datas()

	def setUp(self):
		self.client.post('/login/', {'username': self.user.username, 'password': 'demo'})

	def tearDown(self):
		self.client.logout()

	#not a staff or manager login url
	def test_display_scheduler_403(self):
		staff = OfficeStaff(user=self.user)
		staff.save()
		staff.practices.add(self.practice)
		data403 = {}
		response = self.client.post(reverse('MHLogin.MHLCallGroups.Scheduler.'\
			'views_multicallgroup.display_scheduler', 
				args=(self.practice.id, self.group.id)), data=data403)
		self.assertEqual(response.status_code, 403)

	def test_display_scheduler_403_group(self):
		dataEmpty = {}
		staff = OfficeStaff(user=self.user)
		staff.save()
		staff.practices.add(self.practice)
		manager = Office_Manager(user=staff, practice=self.practice, manager_role=2)
		manager.save()

		group = CallGroup(description='test', team='team')
		group.save()
		response = self.client.post(reverse('MHLogin.MHLCallGroups.Scheduler.'\
			'views_multicallgroup.display_scheduler', 
				args=(self.practice.id, group.id)), data=dataEmpty)
		self.assertEqual(response.status_code, 403)

	#a staff or manager login url
	def test_display_scheduler_emptydata(self):
		dataEmpty = {}
		staff = OfficeStaff(user=self.user)
		staff.save()
		staff.practices.add(self.practice)
		manager = Office_Manager(user=staff, practice=self.practice, manager_role=2)
		manager.save()

		response = self.client.get(reverse('MHLogin.MHLCallGroups.Scheduler.'\
			'views_multicallgroup.display_scheduler', 
				args=(self.practice.id, self.group.id)), data=dataEmpty)
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'schedule_multicallgroup.html')
		self.assertGreater(response.content.find('Current call group:'), 0)  # find tag
		self.assertEqual(-1, response.content.find('fc-event-inner'))  # event tag

	#a staff or manager login url
	#no call group associated with your practice
	def test_display_scheduler_nopractice(self):
		dataEmpty = {}
		staff = OfficeStaff(user=self.user)
		staff.save()
		staff.practices.add(self.practice)
		manager = Office_Manager(user=staff, practice=self.practice, manager_role=2)
		manager.save()
		practice2 = PracticeLocation(practice_name='test2',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice2.save()
		manager.practice = practice2
		manager.save()
		response = self.client.get(reverse('MHLogin.MHLCallGroups.Scheduler.'\
			'views_multicallgroup.display_scheduler', args=(practice2.id, 0)), data=dataEmpty)
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'error_multicallgroup.html')

	#a staff or manager login url
	#login and session has value
	def test_display_scheduler_session(self):
		dataEmpty = {}
		staff = OfficeStaff(user=self.user)
		staff.save()
		staff.practices.add(self.practice)
		manager = Office_Manager(user=staff, practice=self.practice, manager_role=2)
		manager.save()

		self.client.session[SessionHelper.CURRENT_CALLGROUP_ID] = self.group.id
		self.client.session.save()
		response = self.client.get(reverse('MHLogin.MHLCallGroups.Scheduler.'\
			'views_multicallgroup.display_scheduler', args=(self.practice.id, 0)), data=dataEmpty)
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'schedule_multicallgroup.html')

	#a staff or manager login url
	#success login and add find one spcialty tag in page and specialty_name length <80
	def test_display_scheduler_spec(self):
		dataEmpty = {}
		staff = OfficeStaff(user=self.user)
		staff.save()
		staff.practices.add(self.practice)
		manager = Office_Manager(user=staff, practice=self.practice, manager_role=2)
		manager.save()

		specialty_name = 'Specialty A'
		specialty1 = Specialty()
		specialty1.name = specialty_name
		specialty1.practice_location = self.practice
		specialty1.number_selection = 3
		specialty1.save()
		specialty1.call_groups.add(self.group)

		response = self.client.get(reverse('MHLogin.MHLCallGroups.Scheduler.'\
			'views_multicallgroup.display_scheduler', 
				args=(self.practice.id, self.group.id)), data=dataEmpty)
		self.assertEqual(response.status_code, 200)
		self.assertGreater(response.content.find(specialty_name), 0)

	#a staff or manager login url
	#success login and add find one spcialty tag in page and specialty_name length >80
	def test_display_scheduler_namelength(self):
		dataEmpty = {}
		staff = OfficeStaff(user=self.user)
		staff.save()
		staff.practices.add(self.practice)
		manager = Office_Manager(user=staff, practice=self.practice, manager_role=2)
		manager.save()

		specialty_name_80 = 'abcdefghjyabcdefghjyabcdefghjyabcdefghjyabcdefghjyabcdefghjyabcdefghjyabcdefghjy123456'
		specialty2 = Specialty()
		specialty2.name = specialty_name_80
		specialty2.practice_location = self.practice
		specialty2.number_selection = 3
		specialty2.save()
		specialty2.call_groups.add(self.group)

		response = self.client.get(reverse('MHLogin.MHLCallGroups.Scheduler.views_multicallgroup.display_scheduler', 
			args=(self.practice.id, self.group.id)), data=dataEmpty)
		self.assertEqual(response.status_code, 200)
		self.assertGreater(response.content.find(specialty_name_80[0:80]), 0)

	#a staff or manager login url
	#success login and add 256 spcialty in page
	def test_display_scheduler_256spec(self):
		staff = OfficeStaff(user=self.user)
		staff.save()
		staff.practices.add(self.practice)

		manager = Office_Manager(user=staff, practice=self.practice, manager_role=2)
		manager.save()

		dataEmpty = {}

		for i in range(257):
			specialty_name = 'Specialty' + str(i)
			specialty = Specialty()
			specialty.name = specialty_name
			specialty.practice_location = self.practice
			specialty.number_selection = 3
			specialty.save()
			specialty.call_groups.add(self.group)

		response = self.client.get(reverse('MHLogin.MHLCallGroups.Scheduler.'\
			'views_multicallgroup.display_scheduler', 
				args=(self.practice.id, self.group.id)), data=dataEmpty)
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'error_multicallgroup.html')


class MCGetEventsTest(TestCase):
	@classmethod
	def setUpClass(cls):
		clean_db_datas()
		cls.user = create_user('practicemgr', 'lin', 'xing', 'demo', '', '', '', '',)

		group = CallGroup(description='test', team='team')
		group.save()
		cls.group = group

		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice.save()
		practice.call_groups.add(group)
		cls.practice = practice

	@classmethod
	def tearDownClass(cls):
		clean_db_datas()

	def setUp(self):
		self.client.post('/login/', {'username': self.user.username, 'password': 'demo'})

	def tearDown(self):
		self.client.logout()

	def test_getEvents(self):
		staff = OfficeStaff(user=self.user)
		staff.save()
		staff.practices.add(self.practice)

		manager = Office_Manager(user=staff, practice=self.practice, manager_role=2)
		manager.save()

		errData = {}
		successDate = {'fromDate': datetime.datetime(2012, 12, 12), 'toDate': datetime.datetime(2012, 12, 17)}

		#get method
		response = self.client.get(reverse('MHLogin.MHLCallGroups.Scheduler.'\
			'views_multicallgroup.getEvents', args=(self.practice.id, self.group.id)), data=successDate)
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'DateEntry.html')

		#error data
		response = self.client.post(reverse('MHLogin.MHLCallGroups.Scheduler.views_multicallgroup.getEvents', 
			args=(self.practice.id, self.group.id)), data=errData)
		self.assertEqual(response.status_code, 403)

		#error call group
		group2 = CallGroup(description='test', team='team')
		group2.save()
		response = self.client.post(reverse('MHLogin.MHLCallGroups.Scheduler.views_multicallgroup.getEvents', 
			args=(self.practice.id, group2.id)), data=errData)
		self.assertEqual(response.status_code, 403)

		#success data and find 0 event
		response = self.client.post(reverse('MHLogin.MHLCallGroups.Scheduler.views_multicallgroup.getEvents', 
			args=(self.practice.id, self.group.id)), data=successDate)
		self.assertEqual(response.status_code, 200)
		data = json.loads(response.content)
		self.assertEqual(data['redoSize'], 0)
		self.assertEqual(data['undoSize'], 0)
		self.assertEqual(data['datas'], '[]')

		#success data and find 1 event
		event = EventEntry(creator=self.user,
						oncallPerson=self.user,
						callGroup=self.group,
						startDate=datetime.datetime(2012, 12, 1),
						endDate=datetime.datetime(2012, 12, 30),
						title='test event',
						oncallLevel='0',
						eventStatus=1,
						checkString='abc'
						)
		event.save()

		response = self.client.post(reverse('MHLogin.MHLCallGroups.Scheduler.views_multicallgroup.getEvents', 
			args=(self.practice.id, self.group.id)), data=successDate)
		self.assertEqual(response.status_code, 200)
		data = json.loads(response.content)
		self.assertEqual(data['redoSize'], 0)
		self.assertEqual(data['undoSize'], 0)
		d = json.loads(data['datas'])
		self.assertEqual(len(d), 1)
		self.assertEqual(d[0]['pk'], event.pk)


class MCCheckoutUserManagerTest(TestCase):
	@classmethod
	def setUpClass(cls):
		clean_db_datas()

	def test_checkoutUserManager(self):
		practice = PracticeLocation(practice_name='test', practice_longit='0.1', practice_lat='0.0',)
		practice.save()
		user = create_user('staff', 'lin', 'xing', 'demo', '', '', '', '',)
		staff = OfficeStaff(user=user)
		staff.save()
		staff.practices.add(practice)

		provider = Provider.objects.create(username='healmeister', first_name='heal',
			last_name='meister', address1="555 Bryant St.", city="Palo Alto", state="CA", 
			lat=0.0, longit=0.0, office_lat=0.0, office_longit=0.0, is_active=True, 
			tos_accepted=True, mobile_confirmed=True, mdcom_phone='123', mobile_phone='456')
		provider.user = provider  # for our unique prov-user reln
		provider.save()

		# try provider
		result = user_is_mgr_of_practice(provider, practice)
		self.assertEqual(False, result)

		# try just staff
		result = user_is_mgr_of_practice(staff.user, practice)
		self.assertEqual(False, result)

		# now office manager (make staff an OM)
		om = Office_Manager.objects.create(user=staff, practice=practice, manager_role=1)
		result = user_is_mgr_of_practice(om.user.user, practice)
		self.assertEqual(True, result)
		result = user_is_mgr_of_practice(staff.user, practice)
		self.assertEqual(True, result)


class MCCheckProviderInCallGroupTest(TestCase):
	@classmethod
	def setUpClass(cls):
		clean_db_datas()

		user = create_user('practicemgr2', 'lin', 'xing', 'demo', '', '', '', '',)
		cls.user = user

		group = CallGroup(description='test', team='team', number_selection=0)
		group.save()
		cls.group = group

		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice.save()
		practice.call_groups.add(group)
		cls.practice = practice

	def setUp(self):
		self.client.post('/login/', {'username': self.user.username, 'password': 'demo'})

	@classmethod
	def tearDownClass(cls):
		clean_db_datas()

	def test_checkProviderInCallGroup(self):
		staff = OfficeStaff(user=self.user)
		staff.save()
		staff.practices.add(self.practice)
		manager = Office_Manager(user=staff, practice=self.practice, manager_role=1)
		manager.save()

		#1 provider in practice
		provider = Provider(username='provider', first_name='tes', last_name="meister", email='aa@ada.com',
					office_lat=0.0, office_longit=0.0)
		provider.save()
		dataProv = {'id': provider.id}
		response = self.client.post(reverse('MHLogin.MHLCallGroups.Scheduler.'\
			'views_multicallgroup.checkProviderInCallGroup', 
				args=(self.practice.id, self.group.id)), data=dataProv)
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.content, '"inpracitce"')

		#1 provider in call group
		provider2 = Provider(username='provider2', first_name='tes', last_name="meister", email='aa2@ada.com',
					office_lat=0.0, office_longit=0.0)
		provider2.save()
		cgm = CallGroupMember(call_group=self.group, member=provider2, alt_provider=1)
		cgm.save()
		data2 = {'id': provider2.id}
		response = self.client.post(reverse('MHLogin.MHLCallGroups.Scheduler.'\
			'views_multicallgroup.checkProviderInCallGroup', 
				args=(self.practice.id, self.group.id)), data=data2)
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.content, '"member"')

		#1 provider in pending list
		provider3 = Provider(username='provider3', first_name='tes', last_name="meister", email='aa3@ada.com',
					office_lat=0.0, office_longit=0.0)
		provider3.save()
		pending = CallGroupMemberPending(from_user=self.user, to_user=provider3, 
			practice=self.practice, call_group=self.group, 
				accept_status=0, created_time=datetime.datetime.now())
		pending.save()
		data3 = {'id': provider3.id}
		response = self.client.post(reverse('MHLogin.MHLCallGroups.Scheduler.'\
			'views_multicallgroup.checkProviderInCallGroup', 
				args=(self.practice.id, self.group.id)), data=data3)
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.content, '"pending"')

		#1 provider not in practcie or call group
		practice2 = PracticeLocation(practice_name='teste',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice2.save()
		provider4 = Provider(username='provider4', first_name='tes', last_name="meister", 
			email='aa4@ada.com', office_lat=0.0, office_longit=0.0)
		provider4.save()
		provider4.practices.add(practice2)
		data4 = {'id': provider4.id}
		response = self.client.post(reverse('MHLogin.MHLCallGroups.Scheduler.'\
			'views_multicallgroup.checkProviderInCallGroup', 
				args=(self.practice.id, self.group.id)), data=data4)
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.content, '"ok"')


class MCAddProviderInGroupTest(TestCase):
	@classmethod
	def setUpClass(cls):
		clean_db_datas()

		cls.user = create_user('practicemgr', 'lin', 'xing', 'demo', '', '', '', '',)

		group = CallGroup(description='test', team='team')
		group.save()
		cls.group = group

		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice.save()
		practice.call_groups.add(group)
		cls.practice = practice

	def setUp(self):
		self.client.post('/login/', {'username': self.user.username, 'password': 'demo'})

	@classmethod
	def tearDownClass(cls):
		clean_db_datas()

	def test_addProviderInGroup(self):
		staff = OfficeStaff(user=self.user)
		staff.save()
		staff.practices.add(self.practice)
		staff.current_practice = self.practice
		staff.save()
		manager = Office_Manager(user=staff, practice=self.practice, manager_role=1)
		manager.save()

		provider1 = Provider(username='provider1', first_name='tes provider1', 
			last_name="meister", email='aaaxs@ada.com', office_lat=0.0, office_longit=0.0)
		provider1.save()
		data1 = {'to_user': provider1.id}
		msg1 = '''This user is not in your practice now. We have sent an invitation to 
		him/her for confirm to join this call group.
		(He/She will not join your practice by accept this invitation.)'''

		#provider1 not in practice
		response = self.client.post(reverse('MHLogin.MHLCallGroups.Scheduler.views_multicallgroup.addProviderInGroup', 
			args=(self.practice.id, self.group.id)), data=data1)
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(msg['err'], msg1)

		#add provider2 in practice in this case
		provider2 = Provider(username='provider2', first_name='tes provider2', 
			last_name="meister", email='aa2@ada.com', office_lat=0.0, office_longit=0.0)
		provider2.save()
		provider2.practices.add(self.practice)
		provider2.current_practice = self.practice
		provider2.save()
		data2 = {'to_user': provider2.id}
		msg2 = 'Congratulations! We have added this member to call group. You can:'

		response = self.client.post(reverse('MHLogin.MHLCallGroups.Scheduler.views_multicallgroup.addProviderInGroup', 
			args=(self.practice.id, self.group.id)), data=data2)
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(msg['err'], msg2)


#repeate method
class MCAddPrvoderInTest(TestCase):
	@classmethod
	def setUpClass(cls):
		clean_db_datas()

		cls.user = create_user('practicemgr5', 'lin', 'xing', 'demo', '', '', '', '',)

		group = CallGroup(description='test', team='team')
		group.save()
		cls.group = group

		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice.save()
		practice.call_groups.add(group)
		cls.practice = practice

	def setUp(self):
		self.client.post('/login/', {'username': self.user.username, 'password': 'demo'})

	@classmethod
	def tearDownClass(cls):
		clean_db_datas()

	def test_addPrvoderIn(self):
		prov = Provider(username='prov', first_name='tes', last_name="meister", email='aa@ada.com',
					office_lat=0.0, office_longit=0.0)
		prov.save()
		staff = OfficeStaff(user=self.user)
		staff.save()
		staff.practices.add(self.practice)
		staff.current_practice = self.practice
		staff.save()
		manager = Office_Manager(user=staff, practice=self.practice, manager_role=1)
		manager.save()

		data = {'to_user': prov.id}
		response = self.client.post(reverse('MHLogin.MHLCallGroups.Scheduler.views_multicallgroup.addPrvoderIn', 
			args=(self.practice.id, self.group.id)), data=data)
		msg = json.loads(response.content)
		self.assertEqual(response.status_code, 200)
		self.assertEqual(0, msg['err'].find('Congratulations'))


class MCJoinCallGroupTest(TestCase):
	@classmethod
	def setUpClass(cls):
		clean_db_datas()

	def test_joincallgroup(self):
		from_user = Provider(username='from', first_name='tes', last_name="meister", 
			email='aax@ada.com', office_lat=0.0, office_longit=0.0)
		from_user.save()

		to_user = Provider(username='to', first_name='tes3', last_name="meister3", 
			email='a2a@ada.com', office_lat=0.0, office_longit=0.0)
		to_user.save()

		call_group_team = 'team'

		call_group = CallGroup(description='test', team=call_group_team)
		call_group.save()

		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice.save()
		practice.call_groups.add(call_group)

		#init http request
		request = HttpRequest()
		request.session = dict()
		request.session['MHL_Users'] = {}
		request.session['MHL_UserIDs'] = 'OfficeStaff'

		#test get method
		request.method = 'GET'

		#test get method and accept type
		type = 'Accept'
		response = joinCallGroup(request, type)
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.content, '"err"')

		#test get method and reject type
		type = 'Reject'
		response = joinCallGroup(request, type)
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.content, '"err"')

		#test method post
		request.method = 'POST'
		accept_group = CallGroupMemberPending(from_user=from_user,
			to_user=to_user,
			practice=practice,
			call_group=call_group,
			created_time=datetime.datetime.now())
		accept_group.save()

		request.POST['id'] = accept_group.id
		request.session['MHL_Users']['Provider'] = to_user

		#accept 1 provider in call group
		type = 'Accept'
		response = joinCallGroup(request, type)
		self.assertEqual(response.status_code, 200)
		ret_data = json.loads(response.content)
		self.assertEqual(ret_data["success"], True)
		self.assertEqual(ret_data["message"], \
					_('You have successfully joined %s call group.')\
					%(call_group_team))
		cgm = CallGroupMemberPending.objects.get(pk=accept_group.id)
		self.assertEqual(cgm.accept_status, 1)

		#reject 1 provider in call group
		cgmReject = CallGroupMemberPending(from_user=from_user, to_user=to_user, 
			practice=practice, call_group=call_group, created_time=datetime.datetime.now())
		cgmReject.save()
		request.POST['id'] = cgmReject.id

		type = 'Reject'
		response = joinCallGroup(request, type)
		self.assertEqual(response.status_code, 200)
		ret_data = json.loads(response.content)
		self.assertEqual(ret_data["success"], True)
		self.assertEqual(ret_data["message"], \
					_('You have declined %s\'s invitation.')\
					%(call_group_team))
		cgm = CallGroupMemberPending.objects.get(pk=cgmReject.id)
		self.assertEqual(cgm.accept_status, 2)


#add by xlin 121214 to test bulkNewEvents method in view_multicallgroup
class MCBulkNewEventsTest(TestCase):
	@classmethod
	def setUpClass(cls):
		clean_db_datas()

		cls.user = create_user('practicemgr5', 'lin', 'xing', 'demo', '', '', '', '',)

		call_group = CallGroup(description='test', team='team')
		call_group.save()
		cls.call_group = call_group

		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice.save()
		practice.call_groups.add(call_group)
		cls.practice = practice

	def setUp(self):
		self.client.post('/login/', {'username': self.user.username, 'password': 'demo'})

	@classmethod
	def tearDownClass(cls):
		clean_db_datas()

	def test_new_event(self):
		staff = OfficeStaff(user=self.user)
		staff.save()
		staff.practices.add(self.practice)
		staff.current_practice = self.practice
		staff.save()
		manager = Office_Manager(user=staff, practice=self.practice, manager_role=1)
		manager.save()

		#get method
		response = self.client.get(reverse('MHLogin.MHLCallGroups.Scheduler.views_multicallgroup.bulkNewEvents', 
			args=(self.practice.id, self.call_group.id)))
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, "bulkOperation.html")

		#post method

		#not save new event,provider is not in the call group
		provider = Provider(username='provider', first_name='tes', last_name="meister", 
			email='aa@ada.com', office_lat=0.0, office_longit=0.0)
		provider.save()
		checkString = 'Ca69J2X6l8'
		newEventInvalidData = {'data': '[{"pk":null,"model":"Scheduler.evententry","fields":'\
			'{"oncallPerson":"' + str(provider.id) + '","eventType":"0",'\
				'"startDate":"2012-12-19 08:00:00","endDate":"2012-12-20 08:00:00",'\
					'"checkString":"' + checkString + '"}}]',
			'view': '{"name":"month","start":"2012-12-01 00:00:00","end":"2013-01-01 00:00:00"}'}

		response = self.client.post(reverse('MHLogin.MHLCallGroups.Scheduler.views_multicallgroup.bulkNewEvents', 
			args=(self.practice.id, self.call_group.id)), data=newEventInvalidData)
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(msg['error'][0], checkString + ', error saving new object')

		#save new event, provider is in the call group
		provider2 = Provider(username='provider2', first_name='tes', last_name="meister", 
			email='aa2@ada.com', office_lat=0.0, office_longit=0.0)
		provider2.save()

		cgm = CallGroupMember(call_group=self.call_group, member=provider2, alt_provider=1)
		cgm.save()

		checkString = 'Ca69J2X6l8'
		newEventInvalidData = {'data': '[{"pk":null,"model":"Scheduler.evententry","fields":{"oncallPerson":"' + 
			str(provider2.id) + '","eventType":"0","startDate":"2012-12-19 08:00:00","endDate":"2012-12-20 08:00:00",\
				"checkString":"' + checkString + '"}}]',
				'view': '{"name":"month","start":"2012-12-01 00:00:00","end":"2013-01-01 00:00:00"}'}

		response = self.client.post(reverse('MHLogin.MHLCallGroups.Scheduler.views_multicallgroup.bulkNewEvents', 
			args=(self.practice.id, self.call_group.id)), data=newEventInvalidData)
		self.assertEqual(response.status_code, 200)
		self.assertEqual(EventEntry.objects.count(), 1)

		#403
		call_group2 = CallGroup(description='test2', team='team')
		call_group2.save()

		response = self.client.post(reverse('MHLogin.MHLCallGroups.Scheduler.views_multicallgroup.bulkNewEvents', 
			args=(self.practice.id, call_group2.id)), data=newEventInvalidData)
		self.assertEqual(response.status_code, 403)


#add by xlin 121214 to test validateNewEvent method in views_multicallgroup
class MCValidateNewEventTest(TestCase):
	@classmethod
	def setUpClass(cls):
		clean_db_datas()

	def test_validateNewEvent(self):
		#invalid data
		eventInvalid = ''
		result = validateNewEvent(eventInvalid)
		self.assertEqual(result, 0)

		#valid data
		call_group = CallGroup(description='test', team='team')
		call_group.save()
		provider = Provider(username='provider', first_name='tes', last_name="meister", 
			email='aa@ada.com', office_lat=0.0, office_longit=0.0)
		provider.save()
		callgm = CallGroupMember(call_group=call_group, member=provider, alt_provider=1)
		callgm.save()

		data = '[{"pk":null,"model":"Scheduler.evententry","fields":{"oncallPerson":"' + \
			str(provider.id) + '","eventType":"0","startDate":"2013-01-01 08:00:00",\
				"endDate":"2013-01-02 08:00:00","checkString":"5xTTV2zUPm"}}]'
		for newdsEventObj in serializers.deserialize("json", data):
			newdsEventObj.object.callGroup_id = call_group.id
			newdsEventObj.object.notifyState = 2
			newdsEventObj.object.whoCanModify = 1
			newdsEventObj.object.eventStatus = 1
		result = validateNewEvent(newdsEventObj)
		self.assertEqual(result, 1)


#add by xlin 121217 to test checkSchedulerView method in views_multicallgroup
class MCcheckSchedulerViewTest(TestCase):
	@classmethod
	def setUpClass(cls):
		clean_db_datas()

	def test_checkSchedulerView(self):
		#invalid view data, lack name
		invalidView = '{"name":"xxxx","start":"2012-12-01 00:00:00","end":"2013-01-01 00:00:00"}'
		result = checkSchedulerView(invalidView)
		self.assertEqual(result, False)

		#invalid start date
		errStartView = '{"name":"month","start":"1234xxx56","end":"2013-01-01 00:00:00"}'
		result = checkSchedulerView(errStartView)
		self.assertEqual(result, False)

		#invliad end date
		errEndView = '{"name":"month","start":"2013-01-01 00:00:00","end":"ws1asdf"}'
		result = checkSchedulerView(errEndView)
		self.assertEqual(result, False)

		#valid date and view month
		validView = '{"name":"month","start":"2013-01-01 00:00:00","end":"2013-01-02 00:00:00"}'
		result = checkSchedulerView(validView)
		self.assertEqual(result, True)

		validView = '{"name":"agendaWeek","start":"2013-01-01 00:00:00","end":"2013-01-02 00:00:00"}'
		result = checkSchedulerView(validView)
		self.assertEqual(result, True)

		validView = '{"name":"agendaDay","start":"2013-01-01 00:00:00","end":"2013-01-02 00:00:00"}'
		result = checkSchedulerView(validView)
		self.assertEqual(result, True)


#add by xlin 121217 to test bulkUpdateEvents method
class MCBulkUpdateEventsTest(TestCase):
	@classmethod
	def setUpClass(cls):
		clean_db_datas()

		cls.user = create_user('practicemgr5', 'lin', 'xing', 'demo', '', '', '', '',)

		call_group = CallGroup(description='test', team='team')
		call_group.save()
		cls.call_group = call_group

		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice.save()
		practice.call_groups.add(call_group)
		cls.practice = practice

	def setUp(self):
		self.client.post('/login/', {'username': self.user.username, 'password': 'demo'})

	@classmethod
	def tearDownClass(cls):
		clean_db_datas()

	def test_bulkUpdateEvents(self):
		staff = OfficeStaff(user=self.user)
		staff.save()
		staff.practices.add(self.practice)
		staff.current_practice = self.practice
		staff.save()
		manager = Office_Manager(user=staff, practice=self.practice, manager_role=1)
		manager.save()

		provider = Provider(username='provider', first_name='tes', last_name="meister", 
			email='aa@ada.com', office_lat=0.0, office_longit=0.0)
		provider.save()
		checkString = 'Ca69J2X6l8'
		#init a schecule event
		event = EventEntry(creator=self.user,
						oncallPerson=provider,
						callGroup=self.call_group,
						startDate=datetime.datetime(2012, 12, 1),
						endDate=datetime.datetime(2012, 12, 30),
						title='test event',
						oncallLevel='0',
						eventStatus=1,
						checkString=checkString
						)
		event.save()

		#get method
		response = self.client.get(reverse('MHLogin.MHLCallGroups.Scheduler.views_multicallgroup.bulkUpdateEvents', 
			args=(self.practice.id, self.call_group.id)))
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, "bulkOperation.html")

		#post method

		#not save new event,provider is not in the call group
		newEventInvalidData = {'data': '[{"pk":' + str(event.pk) + 
			',"model":"Scheduler.evententry","fields":{"oncallPerson":"' + str(provider.id) + 
			'","eventType":"0","startDate":"2012-12-19 08:00:00","endDate":"2012-12-20 08:00:00","checkString":"' + 
				checkString + '"}}]',
				'view': '{"name":"month","start":"2012-12-01 00:00:00","end":"2013-01-01 00:00:00"}'}

		response = self.client.post(reverse('MHLogin.MHLCallGroups.Scheduler.views_multicallgroup.bulkUpdateEvents', 
			args=(self.practice.id, self.call_group.id)), data=newEventInvalidData)
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(msg['error'][0].find(str(event.pk) + ', error updating object ' + checkString + ' obj '), 0)

		#save new event, provider is in the call group
		provider2 = Provider(username='provider2', first_name='tes', last_name="meister", 
			email='aa2@ada.com', office_lat=0.0, office_longit=0.0)
		provider2.save()

		cgm = CallGroupMember(call_group=self.call_group, member=provider2, alt_provider=1)
		cgm.save()

		checkString = 'Ca69J2X6l8'
		newEventInvalidData = {'data': '[{"pk":' + str(event.pk) + 
			',"model":"Scheduler.evententry","fields":{"oncallPerson":"' + 
				str(provider2.id) + '","eventType":"0","startDate":"2012-12-19 08:00:00",\
				"endDate":"2012-12-20 08:00:00","checkString":"' + 
					checkString + '"}}]',
			'view': '{"name":"month","start":"2012-12-01 00:00:00","end":"2013-01-01 00:00:00"}'}

		response = self.client.post(reverse('MHLogin.MHLCallGroups.Scheduler.views_multicallgroup.bulkUpdateEvents', 
			args=(self.practice.id, self.call_group.id)), data=newEventInvalidData)
		self.assertEqual(response.status_code, 200)
		self.assertEqual(EventEntry.objects.count(), 1)

		#403
		call_group2 = CallGroup(description='test2', team='team')
		call_group2.save()

		response = self.client.post(reverse('MHLogin.MHLCallGroups.Scheduler.views_multicallgroup.bulkUpdateEvents', 
			args=(self.practice.id, call_group2.id)), data=newEventInvalidData)
		self.assertEqual(response.status_code, 403)

		#invlid checkstring event update
		checkString = 'xxxxxxs'
		newEventInvalidData = {'data': '[{"pk":' + str(event.pk) + 
			',"model":"Scheduler.evententry","fields":{"oncallPerson":"' + 
				str(provider2.id) + '","eventType":"0","startDate":"2012-12-19 08:00:00","endDate":\
					"2012-12-20 08:00:00","checkString":"' + 
					checkString + '"}}]',
			'view': '{"name":"month","start":"2012-12-01 00:00:00","end":"2013-01-01 00:00:00"}'}

		response = self.client.post(reverse('MHLogin.MHLCallGroups.Scheduler.views_multicallgroup.bulkUpdateEvents', 
			args=(self.practice.id, self.call_group.id)), data=newEventInvalidData)
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(msg['error'][0].find(str(event.pk) + ', update failed - invalid checkString xxxxxxs obj'), 0)


#add by xlin 121217 to test checkDSEventConsistency method
class MCCheckDSEventConsistencyTest(TestCase):
	@classmethod
	def setUpClass(cls):
		clean_db_datas()

	def test_checkDSEventConsistency(self):
		#invalid data
		eventInvalid = ''
		result = checkDSEventConsistency(eventInvalid)
		self.assertEqual(result, 0)

		#valid data
		call_group = CallGroup(description='test', team='team')
		call_group.save()
		provider = Provider(username='provider', first_name='tes', last_name="meister", 
			email='aa@ada.com', office_lat=0.0, office_longit=0.0)
		provider.save()
		callgm = CallGroupMember(call_group=call_group, member=provider, alt_provider=1)
		callgm.save()
		checkString = 'Ca69J2X6l8'
		event = EventEntry(creator=provider,
						oncallPerson=provider,
						callGroup=call_group,
						startDate=datetime.datetime(2012, 12, 1),
						endDate=datetime.datetime(2012, 12, 30),
						title='test event',
						oncallLevel='0',
						eventStatus=1,
						checkString=checkString
						)
		event.save()

		data = '[{"pk":' + str(event.pk) + ',"model":"Scheduler.evententry","fields":{"oncallPerson":"' + \
			str(provider.id) + '","eventType":"0","startDate":"2013-01-01 08:00:00", \
				"endDate":"2013-01-02 08:00:00","checkString":"5xTTV2zUPm"}}]'
		for newdsEventObj in serializers.deserialize("json", data):
			newdsEventObj.object.callGroup_id = call_group.id
			newdsEventObj.object.notifyState = 2
			newdsEventObj.object.whoCanModify = 1
			newdsEventObj.object.eventStatus = 1
		result = checkDSEventConsistency(newdsEventObj)
		self.assertEqual(result, 1)


#add by xlin 121217 to test rulesCheck method
class MCRulesCheckTest(TestCase):
	@classmethod
	def setUpClass(cls):
		clean_db_datas()

		cls.user = create_user('practicemgr5', 'lin', 'xing', 'demo', '', '', '', '',)

		call_group = CallGroup(description='test', team='team')
		call_group.save()
		cls.call_group = call_group

		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice.save()
		practice.call_groups.add(call_group)
		cls.practice = practice

	def setUp(self):
		self.client.post('/login/', {'username': self.user.username, 'password': 'demo'})

	@classmethod
	def tearDownClass(cls):
		clean_db_datas()

	def test_rulesCheck(self):
		staff = OfficeStaff(user=self.user)
		staff.save()
		staff.practices.add(self.practice)
		staff.current_practice = self.practice
		staff.save()
		manager = Office_Manager(user=staff, practice=self.practice, manager_role=1)
		manager.save()

		provider = Provider(username='provider', first_name='tes', last_name="meister", 
			email='aa@ada.com', office_lat=0.0, office_longit=0.0)
		provider.save()
		checkString = 'Ca69J2X6l8'
		#init a schecule event
		timenow = datetime.datetime.now()
		startDate = timenow + datetime.timedelta(days=2)
		endDate = timenow + datetime.timedelta(days=3)
		event = EventEntry(creator=self.user,
						oncallPerson=provider,
						callGroup=self.call_group,
						startDate=startDate,
						endDate=endDate,
						title='test event',
						oncallLevel='0',
						eventStatus=1,
						checkString=checkString
						)
		event.save()

		#get method
		response = self.client.get(reverse('MHLogin.MHLCallGroups.Scheduler.views_multicallgroup.rulesCheck', 
			args=(self.practice.id, self.call_group.id)))
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'DateEntry.html')

		#post method
		data = {'fromDate': '2012-12-10 12:00:00', 'toDate': '2012-12-14 12:00:00'}
		response = self.client.post(reverse('MHLogin.MHLCallGroups.Scheduler.views_multicallgroup.rulesCheck', 
			args=(self.practice.id, self.call_group.id)), data=data)
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		start = datetime.datetime.now()
		end = start + datetime.timedelta(days=14)
		self.assertTrue('warning hole in coverage' in msg[0])


#add by xlin 121217 to test GetViewInfo method
class MCGetViewInfoTest(TestCase):
	@classmethod
	def setUpClass(cls):
		clean_db_datas()

		cls.user = create_user('practicemgr5', 'lin', 'xing', 'demo', '', '', '', '',)

		call_group = CallGroup(description='test', team='team')
		call_group.save()
		cls.call_group = call_group

		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice.save()
		practice.call_groups.add(call_group)
		cls.practice = practice

	def setUp(self):
		self.client.post('/login/', {'username': self.user.username, 'password': 'demo'})

	@classmethod
	def tearDownClass(cls):
		clean_db_datas()

	def test_getViewInfo(self):
		staff = OfficeStaff(user=self.user)
		staff.save()
		staff.practices.add(self.practice)
		staff.current_practice = self.practice
		staff.save()
		manager = Office_Manager(user=staff, practice=self.practice, manager_role=1)
		manager.save()

		#post method
		response = self.client.post(reverse('MHLogin.MHLCallGroups.Scheduler.views_multicallgroup.getViewInfo', 
			args=(self.practice.id, self.call_group.id)))
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(msg['view'], '')

		#get method without session
		response = self.client.get(reverse('MHLogin.MHLCallGroups.Scheduler.views_multicallgroup.getViewInfo', 
			args=(self.practice.id, self.call_group.id)))
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(msg['view'], '')

		#403
		call_group2 = CallGroup(description='test2', team='team')
		call_group2.save()

		response = self.client.get(reverse('MHLogin.MHLCallGroups.Scheduler.views_multicallgroup.getViewInfo', 
			args=(self.practice.id, call_group2.id)))
		self.assertEqual(response.status_code, 403)

		#get method with session---TODO
		view = '{"name":"agendaWeek","start":"2012-12-16 00:00:00","end":"2012-12-23 00:00:00"}'
		self.client.session[SessionHelper.SCHEDULE_LASTVIEW] = view
		self.client.session.save()
		response = self.client.get(reverse('MHLogin.MHLCallGroups.Scheduler.views_multicallgroup.getViewInfo', 
			args=(self.practice.id, self.call_group.id)))
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(msg['view'], '')


#add by xlin 121218 to test saveViewInfo method
class MCSaveViewInfoTest(TestCase):
	@classmethod
	def setUpClass(cls):
		clean_db_datas()

		cls.user = create_user('practicemgr5', 'lin', 'xing', 'demo', '', '', '', '',)

		call_group = CallGroup(description='test', team='team')
		call_group.save()
		cls.call_group = call_group

		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice.save()
		practice.call_groups.add(call_group)
		cls.practice = practice

	def setUp(self):
		self.client.post('/login/', {'username': self.user.username, 'password': 'demo'})

	@classmethod
	def tearDownClass(cls):
		clean_db_datas()

	def test_saveViewInfo(self):
		staff = OfficeStaff(user=self.user)
		staff.save()
		staff.practices.add(self.practice)
		staff.current_practice = self.practice
		staff.save()
		manager = Office_Manager(user=staff, practice=self.practice, manager_role=1)
		manager.save()

		#get method
		response = self.client.get(reverse('MHLogin.MHLCallGroups.Scheduler.views_multicallgroup.saveViewInfo', 
			args=(self.practice.id, self.call_group.id)))
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(msg['view'], '')

		#403
		call_group2 = CallGroup(description='test2', team='team')
		call_group2.save()

		response = self.client.post(reverse('MHLogin.MHLCallGroups.Scheduler.views_multicallgroup.saveViewInfo', 
			args=(self.practice.id, call_group2.id)))
		self.assertEqual(response.status_code, 403)

		#post method without session
		view = {'view': '{"name": "month", "start": "2012-12-01 00:00:00", "end": "2013-01-01 00:00:00"}'}
		response = self.client.post(reverse('MHLogin.MHLCallGroups.Scheduler.views_multicallgroup.saveViewInfo', 
			args=(self.practice.id, self.call_group.id)), data=view)
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(msg['view'], view['view'])


#add by xlin 121218 to test undo method
class MCUndoTest(TestCase):
	@classmethod
	def setUpClass(cls):
		clean_db_datas()

		cls.user = create_user('practicemgr5', 'lin', 'xing', 'demo', '', '', '', '',)

		call_group = CallGroup(description='test', team='team')
		call_group.save()
		cls.call_group = call_group

		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice.save()
		practice.call_groups.add(call_group)
		cls.practice = practice

	def setUp(self):
		self.client.post('/login/', {'username': self.user.username, 'password': 'demo'})

	@classmethod
	def tearDownClass(cls):
		clean_db_datas()

	def test_undo(self):
		staff = OfficeStaff(user=self.user)
		staff.save()
		staff.practices.add(self.practice)
		staff.current_practice = self.practice
		staff.save()
		manager = Office_Manager(user=staff, practice=self.practice, manager_role=1)
		manager.save()

		#403
		call_group2 = CallGroup(description='test2', team='team')
		call_group2.save()
		response = self.client.post(reverse('MHLogin.MHLCallGroups.Scheduler.views_multicallgroup.undo', 
			args=(self.practice.id, call_group2.id)))
		self.assertEqual(response.status_code, 403)

		response = self.client.post(reverse('MHLogin.MHLCallGroups.Scheduler.views_multicallgroup.undo', 
			args=(self.practice.id, self.call_group.id)))
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(msg['count'], 0)

		#create a new event, and undo
		provider = Provider(username='provider2', first_name='tes', last_name="meister", email='aa2@ada.com',
					office_lat=0.0, office_longit=0.0, current_practice=self.practice)
		provider.save()
		provider.practices.add(self.practice)
		cgm = CallGroupMember(call_group=self.call_group, member=provider, alt_provider=1)
		cgm.save()
		checkString = 'Ca69J2X6l8'
		newEventInvalidData = {'data': '[{"pk":null,"model":"Scheduler.evententry", "fields":{"oncallPerson":"' + \
			str(provider.id) + '","eventType":"0","startDate":"2012-12-19 08:00:00",\
				"endDate":"2012-12-20 08:00:00","checkString":"' + checkString + '"}}]',
					'view': '{"name":"month","start":"2012-12-01 00:00:00","end":"2013-01-01 00:00:00"}'}

		new_event = self.client.post(reverse('MHLogin.MHLCallGroups.Scheduler.views_multicallgroup.bulkNewEvents', 
			args=(self.practice.id, self.call_group.id)), data=newEventInvalidData)

		response = self.client.post(reverse('MHLogin.MHLCallGroups.Scheduler.views_multicallgroup.undo', 
			args=(self.practice.id, self.call_group.id)))
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(msg['undoSize'], 0)
		self.assertEqual(msg['redoSize'], 1)
		self.assertEqual(EventEntry.objects.count(), 0)

		#create a new and change event 1 time
		new_event = self.client.post(reverse('MHLogin.MHLCallGroups.Scheduler.'\
			'views_multicallgroup.bulkNewEvents', 
				args=(self.practice.id, self.call_group.id)), data=newEventInvalidData)
		event = EventEntry.objects.get(checkString=checkString)
		#update
		updateEventInvalidData = {'data': '[{"pk":' + str(event.pk) + ',"model":"Scheduler.evententry","fields":{"oncallPerson":"' + 
			str(provider.id) + '","eventType":"0","startDate":"2012-12-20 08:00:00","endDate":"2012-12-21 08:00:00",\
				"eventStatus":1,"checkString":"' + checkString + '"}}]',
			'view': '{"name":"month","start":"2012-12-01 00:00:00","end":"2013-01-01 00:00:00"}'}

		response = self.client.post(reverse('MHLogin.MHLCallGroups.Scheduler.views_multicallgroup.bulkUpdateEvents', 
			args=(self.practice.id, self.call_group.id)), data=updateEventInvalidData)

		response = self.client.post(reverse('MHLogin.MHLCallGroups.Scheduler.views_multicallgroup.undo', 
			args=(self.practice.id, self.call_group.id)))
		msg = json.loads(response.content)
		self.assertEqual(msg['redoSize'], 1)
		self.assertEqual(msg['undoSize'], 1)
		self.assertEqual(msg['operateList'][0]['pk'], event.pk)


#add by xlin 121218 to test redo method
class MCRedoTest(TestCase):
	@classmethod
	def setUpClass(cls):
		clean_db_datas()

		cls.user = create_user('practicemgr5', 'lin', 'xing', 'demo', '', '', '', '',)

		call_group = CallGroup(description='test', team='team')
		call_group.save()
		cls.call_group = call_group

		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice.save()
		practice.call_groups.add(call_group)
		cls.practice = practice

	def setUp(self):
		self.client.post('/login/', {'username': self.user.username, 'password': 'demo'})

	@classmethod
	def tearDownClass(cls):
		clean_db_datas()

	def test_redo(self):
		staff = OfficeStaff(user=self.user)
		staff.save()
		staff.practices.add(self.practice)
		staff.current_practice = self.practice
		staff.save()
		manager = Office_Manager(user=staff, practice=self.practice, manager_role=1)
		manager.save()

		#403
		call_group2 = CallGroup(description='test2', team='team')
		call_group2.save()
		response = self.client.post(reverse('MHLogin.MHLCallGroups.Scheduler.views_multicallgroup.redo', 
			args=(self.practice.id, call_group2.id)))
		self.assertEqual(response.status_code, 403)

		response = self.client.post(reverse('MHLogin.MHLCallGroups.Scheduler.views_multicallgroup.redo', 
			args=(self.practice.id, self.call_group.id)))
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(msg['count'], 0)

		#create a new event, and redo
		provider = Provider(username='provider2', first_name='tes', last_name="meister", 
			email='aa2@ada.com', office_lat=0.0, office_longit=0.0, current_practice=self.practice)
		provider.save()
		provider.practices.add(self.practice)
		cgm = CallGroupMember(call_group=self.call_group, member=provider, alt_provider=1)
		cgm.save()
		checkString = 'Ca69J2X6l8'
		newEventInvalidData = {'data': '[{"pk":null,"model":"Scheduler.evententry","fields":{"oncallPerson":"' + 
			str(provider.id) + '","eventType":"0","startDate":"2012-12-19 08:00:00","endDate":"2012-12-20 08:00:00",\
			"checkString":"' + checkString + '"}}]',
				'view': '{"name":"month","start":"2012-12-01 00:00:00","end":"2013-01-01 00:00:00"}'}

		new_event = self.client.post(reverse('MHLogin.MHLCallGroups.Scheduler.views_multicallgroup.bulkNewEvents', 
			args=(self.practice.id, self.call_group.id)), data=newEventInvalidData)

		response = self.client.post(reverse('MHLogin.MHLCallGroups.Scheduler.views_multicallgroup.redo', 
			args=(self.practice.id, self.call_group.id)))
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(msg['undoSize'], 1)
		self.assertEqual(msg['redoSize'], 0)
		self.assertEqual(EventEntry.objects.count(), 1)

		#create a new and change event 1 time
		event = EventEntry.objects.get(checkString=checkString)
		#update
		updateEventInvalidData = {'data': '[{"pk":' + str(event.pk) + 
			',"model":"Scheduler.evententry","fields":{"oncallPerson":"' + 
			str(provider.id) + '","eventType":"0","startDate":"2012-12-20 08:00:00",\
			"endDate":"2012-12-21 08:00:00","eventStatus":1,"checkString":"' + 
				checkString + '"}}]',
				'view': '{"name":"month","start":"2012-12-01 00:00:00","end":"2013-01-01 00:00:00"}'}

		response = self.client.post(reverse('MHLogin.MHLCallGroups.Scheduler.views_multicallgroup.bulkUpdateEvents', 
			args=(self.practice.id, self.call_group.id)), data=updateEventInvalidData)

		response = self.client.post(reverse('MHLogin.MHLCallGroups.Scheduler.views_multicallgroup.redo', 
			args=(self.practice.id, self.call_group.id)))
		msg = json.loads(response.content)
		self.assertEqual(msg['redoSize'], 0)
		self.assertEqual(msg['undoSize'], 2)
		self.assertEqual(msg['operateList'], [])


#add by xlin 121224 to test getPenddings
class MCGetPenddingsTest(TestCase):
	@classmethod
	def setUpClass(cls):
		clean_db_datas()

	def test_getPenddings(self):
		request = HttpRequest()
		user = create_user('practicemgr1', 'lin', 'xing', 'demo')
		call_group = CallGroup(description='test', team='team')
		call_group.save()
		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',)
		practice.save()

		from_user = create_user('from user', 'lin', 'xing', 'demo')
		to_user = create_user('to user', 'lin', 'xing', 'demo')
		to_user = Provider(username='to_user', first_name='tes3', last_name="meister3", 
			email='a2a@ada.com', user=to_user, office_lat=0.0, office_longit=0.0)
		to_user.save()

		#0 pending find
		request.user = to_user

		response = getPenddings(request)
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 0)

		#1 pending find
		pend = CallGroupMemberPending(from_user=from_user,
									to_user=to_user,
									practice=practice,
									call_group=call_group,
									accept_status=0,
									created_time=datetime.datetime.now())
		pend.save()
		request.user = to_user

		response = getPenddings(request)
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(len(msg), 1)
