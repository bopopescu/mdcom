import datetime
import json

from django.core.urlresolvers import reverse
from django.http import HttpRequest
from django.test.testcases import TestCase

from MHLogin.MHLCallGroups.Scheduler.models import EventEntry
from MHLogin.MHLCallGroups.Scheduler.utils import SessionHelper
from MHLogin.MHLCallGroups.Scheduler.views import checkeUserInCallGroup
from MHLogin.MHLCallGroups.models import CallGroup, CallGroupMember
from MHLogin.MHLPractices.models import PracticeLocation
from MHLogin.MHLUsers.models import Office_Manager, OfficeStaff, Provider
from MHLogin.utils.tests import create_user
from MHLogin.utils.tests.tests import clean_db_datas


#add by xlin 121221 to test display_scheduler
class Display_schedulerTest(TestCase):
	@classmethod
	def setUpClass(cls):
		clean_db_datas()
		cls.user = create_user('practicemgr1', 'lin', 'xing', 'demo', '', '', '', '',)

		call_group = CallGroup(description='test', team='team')
		call_group.save()
		cls.call_group = call_group

		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',
								call_group=call_group,)
		practice.save()
		practice.call_groups.add(call_group)
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
		data403 = {}
		staff = OfficeStaff(user=self.user)
		staff.save()
		response = self.client.get(reverse('MHLogin.MHLCallGroups.Scheduler.views.display_scheduler', 
			args=(self.call_group.id,)), data=data403)
		self.assertEqual(response.status_code, 403)

	#a staff or manager login url
	def test_display_scheduler_emptydata(self):
		dataEmpty = {}
		staff = OfficeStaff(user=self.user)
		staff.save()
		staff.practices.add(self.practice)
		manager = Office_Manager(user=staff, practice=self.practice, manager_role=2)
		manager.save()

		response = self.client.get(reverse('MHLogin.MHLCallGroups.Scheduler.views.display_scheduler', 
			args=(self.call_group.id,)), data=dataEmpty)
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'schedule.html')
		self.assertEqual(-1, response.content.find('fc-event-inner'))  # event tag


#add by xlin 121221 to test getEvents
class GetEventsTest(TestCase):
	@classmethod
	def setUpClass(cls):
		clean_db_datas()
		cls.user = create_user('practicemgr1', 'lin', 'xing', 'demo', '', '', '', '',)

		call_group = CallGroup(description='test', team='team')
		call_group.save()
		cls.call_group = call_group

		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',
								call_group=call_group,)
		practice.save()
		practice.call_groups.add(call_group)
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
		successDate = {'fromDate': datetime.datetime(2012, 12, 12), 
			'toDate': datetime.datetime(2012, 12, 17)}

		#get method
		response = self.client.get(reverse('MHLogin.MHLCallGroups.Scheduler.views.getEvents', 
			args=(self.call_group.id,)), data=successDate)
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'DateEntry.html')

		#error data
		response = self.client.post(reverse('MHLogin.MHLCallGroups.Scheduler.views.getEvents', 
			args=(self.call_group.id,)), data=errData)
		self.assertEqual(response.status_code, 403)

		#success data and find 0 event
		response = self.client.post(reverse('MHLogin.MHLCallGroups.Scheduler.views.getEvents', 
			args=(self.call_group.id,)), data=successDate)
		self.assertEqual(response.status_code, 200)
		data = json.loads(response.content)
		self.assertEqual(data['redoSize'], 0)
		self.assertEqual(data['undoSize'], 0)
		self.assertEqual(data['datas'], '[]')

		#success data and find 0 event and call group in form
		successDateForm = {'fromDate': datetime.datetime(2012, 12, 12), 
			'toDate': datetime.datetime(2012, 12, 17), 'callGroup': self.call_group.id}
		response = self.client.post(reverse('MHLogin.MHLCallGroups.Scheduler.views.getEvents', 
			args=(self.call_group.id,)), data=successDateForm)
		self.assertEqual(response.status_code, 200)
		data = json.loads(response.content)
		self.assertEqual(data['redoSize'], 0)
		self.assertEqual(data['undoSize'], 0)
		self.assertEqual(data['datas'], '[]')

		#success data and find 1 event
		event = EventEntry(creator=self.user,
						oncallPerson=self.user,
						callGroup=self.call_group,
						startDate=datetime.datetime(2012, 12, 1),
						endDate=datetime.datetime(2012, 12, 30),
						title='test event',
						oncallLevel='0',
						eventStatus=1,
						checkString='abc'
						)
		event.save()

		response = self.client.post(reverse('MHLogin.MHLCallGroups.Scheduler.views.getEvents', 
			args=(self.call_group.id,)), data=successDate)
		self.assertEqual(response.status_code, 200)
		data = json.loads(response.content)
		self.assertEqual(data['redoSize'], 0)
		self.assertEqual(data['undoSize'], 0)
		d = json.loads(data['datas'])
		self.assertEqual(len(d), 1)
		self.assertEqual(d[0]['pk'], event.pk)

		#error call group
		call_group2 = CallGroup(description='test', team='team')
		call_group2.save()
		response = self.client.post(reverse('MHLogin.MHLCallGroups.Scheduler.views.getEvents', 
			args=(call_group2.id,)), data=errData)
		self.assertEqual(response.status_code, 403)


#add by xlin 121221 to test scheduleEvent
class NewEventsTest(TestCase):
	@classmethod
	def setUpClass(cls):
		clean_db_datas()
		cls.user = create_user('practicemgr5', 'lin', 'xing', 'demo', '', '', '', '',)

		call_group = CallGroup(description='test', team='team')
		call_group.save()
		cls.call_group = call_group

		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',
								call_group=call_group,)
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
		response = self.client.get(reverse('MHLogin.MHLCallGroups.Scheduler.views.bulkNewEvents', 
			args=(self.call_group.id,)))
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, "bulkOperation.html")

		#post method

		#not save new event,provider is not in the call group
		provider = Provider(username='provider-1', first_name='tes', last_name="meister", 
			email='aa12@ada.com', office_lat=0.0, office_longit=0.0)
		provider.save()
		checkString = 'Ca69J2X6l8'
		newEventInvalidData = {'data': '[{"pk":null,"model":"Scheduler.evententry","fields":{"oncallPerson":"' + \
			str(provider.id) + '","eventType":"0","startDate":"2012-12-19 08:00:00",\
				"endDate":"2012-12-20 08:00:00","checkString":"' + checkString + '"}}]',
					'view': '{"name": "month","start": "2012-12-01 00:00:00","end": "2013-01-01 00:00:00"}'}

		response = self.client.post(reverse('MHLogin.MHLCallGroups.Scheduler.views.bulkNewEvents', 
			args=(self.call_group.id,)), data=newEventInvalidData)
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(msg['error'][0], checkString + ', error saving new object')

		#save new event, provider is in the call group
		provider2 = Provider(username='provider2', first_name='tes', last_name="meister", email='aa2@ada.com',
					office_lat=0.0, office_longit=0.0)
		provider2.save()

		cgm = CallGroupMember(call_group=self.call_group, member=provider2, alt_provider=1)
		cgm.save()

		checkString = 'Ca69J2X6l8'
		newEventInvalidData = {'data': '[{"pk":null,"model":"Scheduler.evententry","fields":{"oncallPerson":"' +
			str(provider2.id) + '","eventType":"0","startDate":"2012-12-19 08:00:00",\
				"endDate":"2012-12-20 08:00:00","checkString":"' + checkString + '"}}]',
			'view': '{"name":"month","start":"2012-12-01 00:00:00","end":"2013-01-01 00:00:00"}'}

		response = self.client.post(reverse('MHLogin.MHLCallGroups.Scheduler.views.bulkNewEvents', 
			args=(self.call_group.id,)), data=newEventInvalidData)
		self.assertEqual(response.status_code, 200)
		self.assertEqual(EventEntry.objects.count(), 1)

		#403
		call_group2 = CallGroup(description='test2', team='team')
		call_group2.save()

		response = self.client.post(reverse('MHLogin.MHLCallGroups.Scheduler.views.bulkNewEvents', 
			args=(call_group2.id,)), data=newEventInvalidData)
		self.assertEqual(response.status_code, 403)


#add by xlin 121221 to test bulkUpdateEvents
class BulkUpdateEventsTest(TestCase):
	@classmethod
	def setUpClass(cls):
		clean_db_datas()
		cls.user = create_user('practicemgr5', 'lin', 'xing', 'demo', '', '', '', '',)

		call_group = CallGroup(description='test', team='team')
		call_group.save()
		cls.call_group = call_group

		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',
								call_group=call_group)
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
		response = self.client.get(reverse('MHLogin.MHLCallGroups.Scheduler.views.bulkUpdateEvents', 
			args=(self.call_group.id,)))
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, "bulkOperation.html")

		#post method

		#not save new event,provider is not in the call group
		newEventInvalidData = {'data': '[{"pk":' + str(event.pk) + 
			',"model":"Scheduler.evententry","fields":{"oncallPerson":"' + 
				str(provider.id) + '","eventType":"0","startDate":"2012-12-19 08:00:00",\
				"endDate":"2012-12-20 08:00:00","checkString":"' + checkString + '"}}]',
			'view': '{"name":"month","start":"2012-12-01 00:00:00","end":"2013-01-01 00:00:00"}'}

		response = self.client.post(reverse('MHLogin.MHLCallGroups.Scheduler.views.bulkUpdateEvents', 
			args=(self.call_group.id,)), data=newEventInvalidData)
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(msg['error'][0].find(str(event.pk) + 
			', error updating object ' + checkString + ' obj '), 0)

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
					"endDate":"2012-12-20 08:00:00","checkString":"' + checkString + '"}}]',
			'view': '{"name":"month","start":"2012-12-01 00:00:00","end":"2013-01-01 00:00:00"}'}

		response = self.client.post(reverse('MHLogin.MHLCallGroups.Scheduler.views.bulkUpdateEvents', 
			args=(self.call_group.id,)), data=newEventInvalidData)
		self.assertEqual(response.status_code, 200)
		self.assertEqual(EventEntry.objects.count(), 1)

		#403
		call_group2 = CallGroup(description='test2', team='team')
		call_group2.save()

		response = self.client.post(reverse('MHLogin.MHLCallGroups.Scheduler.views.bulkUpdateEvents', 
			args=(call_group2.id,)), data=newEventInvalidData)
		self.assertEqual(response.status_code, 403)

		#invlid checkstring event update
		checkString = 'xxxxxxs'
		newEventInvalidData = {'data': '[{"pk":' + str(event.pk) + 
			',"model":"Scheduler.evententry","fields":{"oncallPerson":"' + 
				str(provider2.id) + '","eventType":"0","startDate":"2012-12-19 08:00:00",\
					"endDate":"2012-12-20 08:00:00","checkString":"' + checkString + '"}}]',
			'view': '{"name":"month","start":"2012-12-01 00:00:00","end":"2013-01-01 00:00:00"}'}

		response = self.client.post(reverse('MHLogin.MHLCallGroups.Scheduler.views.bulkUpdateEvents', 
			args=(self.call_group.id,)), data=newEventInvalidData)
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(msg['error'][0].find(str(event.pk) + 
			', update failed - invalid checkString xxxxxxs obj'), 0)	


#add by xlin 121221 to test rulesCheck
class RulesCheckTest(TestCase):
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

		provider = Provider(username='provider', first_name='tes', last_name="meister", email='aa@ada.com',
					office_lat=0.0, office_longit=0.0)
		provider.save()
		checkString = 'Ca69J2X6l8'
		#init a schecule event
		startDate = datetime.datetime.now() + datetime.timedelta(days=2)
		endDate = datetime.datetime.now() + datetime.timedelta(days=3)
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
		response = self.client.get(reverse('MHLogin.MHLCallGroups.Scheduler.views.rulesCheck', 
			args=(self.call_group.id,)))
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'DateEntry.html')

		#post method
		data = {'fromDate': '2012-12-10 12:00:00', 'toDate': '2012-12-14 12:00:00'}
		response = self.client.post(reverse('MHLogin.MHLCallGroups.Scheduler.views.rulesCheck', 
			args=(self.call_group.id,)), data=data)
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(msg[0].find('warning hole in coverage '), 0)


#add by xlin 121221 to test undo
class UndoTest(TestCase):
	@classmethod
	def setUpClass(cls):
		clean_db_datas()
		cls.user = create_user('practicemgr5', 'lin', 'xing', 'demo', '', '', '', '',)

		call_group = CallGroup(description='test', team='team')
		call_group.save()
		cls.call_group = call_group

		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',
								call_group=call_group)
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
		response = self.client.post(reverse('MHLogin.MHLCallGroups.Scheduler.views.undo', 
			args=(call_group2.id,)))
		self.assertEqual(response.status_code, 403)

		response = self.client.post(reverse('MHLogin.MHLCallGroups.Scheduler.views.undo', 
			args=(self.call_group.id,)))
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(msg['count'], 0)

		#create a new event, and undo
		provider = Provider(username='provider2', first_name='tes', last_name="meister", 
			email='aa2@ada.com', office_lat=0.0, office_longit=0.0, current_practice=self.practice)
		provider.save()
		provider.practices.add(self.practice)
		cgm = CallGroupMember(call_group=self.call_group, member=provider, alt_provider=1)
		cgm.save()
		checkString = 'Ca69J2X6l8'
		newEventInvalidData = {'data': '[{"pk":null,"model":"Scheduler.evententry",\
			"fields":{"oncallPerson":"' + str(provider.id) + '","eventType":"0",\
					"startDate":"2012-12-19 08:00:00","endDate":"2012-12-20 08:00:00","checkString":"' + 
						checkString + '"}}]',
			'view': '{"name":"month","start":"2012-12-01 00:00:00","end":"2013-01-01 00:00:00"}'}

		new_event = self.client.post(reverse('MHLogin.MHLCallGroups.Scheduler.views.bulkNewEvents', 
			args=(self.call_group.id,)), data=newEventInvalidData)

		response = self.client.post(reverse('MHLogin.MHLCallGroups.Scheduler.views.undo', 
			args=(self.call_group.id,)))
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(msg['undoSize'], 0)
		self.assertEqual(msg['redoSize'], 1)
		self.assertEqual(EventEntry.objects.count(), 0)

		#create a new and change event 1 time
		new_event = self.client.post(reverse('MHLogin.MHLCallGroups.Scheduler.views.bulkNewEvents', 
			args=(self.call_group.id,)), data=newEventInvalidData)
		event = EventEntry.objects.get(checkString=checkString)
		#update
		updateEventInvalidData = {'data': '[{"pk":' + str(event.pk) + 
			',"model":"Scheduler.evententry","fields":{"oncallPerson":"' + str(provider.id) + 
				'","eventType":"0","startDate":"2012-12-20 08:00:00","endDate":"2012-12-21 08:00:00",\
					"eventStatus":1,"checkString":"' + checkString + '"}}]',
			'view': '{"name":"month","start":"2012-12-01 00:00:00","end":"2013-01-01 00:00:00"}'}

		response = self.client.post(reverse('MHLogin.MHLCallGroups.Scheduler.views.bulkUpdateEvents', 
			args=(self.call_group.id,)), data=updateEventInvalidData)

		response = self.client.post(reverse('MHLogin.MHLCallGroups.Scheduler.views.undo', 
			args=(self.call_group.id,)))
		msg = json.loads(response.content)
		self.assertEqual(msg['redoSize'], 1)
		self.assertEqual(msg['undoSize'], 1)
		self.assertEqual(msg['operateList'][0]['pk'], event.pk)


#add by xlin 121221 to test redo
class RedoTest(TestCase):
	@classmethod
	def setUpClass(cls):
		clean_db_datas()
		cls.user = create_user('practicemgr5', 'lin', 'xing', 'demo', '', '', '', '',)

		call_group = CallGroup(description='test', team='team')
		call_group.save()
		cls.call_group = call_group

		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',
								call_group=call_group)
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
		response = self.client.post(reverse('MHLogin.MHLCallGroups.Scheduler.views.redo', 
			args=(call_group2.id,)))
		self.assertEqual(response.status_code, 403)

		response = self.client.post(reverse('MHLogin.MHLCallGroups.Scheduler.views.redo', 
			args=(self.call_group.id,)))
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(msg['count'], 0)

		#create a new event, and redo
		provider = Provider(username='provider2', first_name='tes', last_name="meister", email='aa2@ada.com',
					office_lat=0.0, office_longit=0.0, current_practice=self.practice)
		provider.save()
		provider.practices.add(self.practice)
		cgm = CallGroupMember(call_group=self.call_group, member=provider, alt_provider=1)
		cgm.save()
		checkString = 'Ca69J2X6l8'
		newEventInvalidData = {'data': '[{"pk":null,"model":"Scheduler.evententry","fields":{"oncallPerson":"' + 
			str(provider.id) + '","eventType":"0","startDate":"2012-12-19 08:00:00",\
			"endDate":"2012-12-20 08:00:00","checkString":"' + checkString + '"}}]',
		 'view': '{"name":"month","start":"2012-12-01 00:00:00","end":"2013-01-01 00:00:00"}'}

		new_event = self.client.post(reverse('MHLogin.MHLCallGroups.Scheduler.views.bulkNewEvents', 
			args=(self.call_group.id,)), data=newEventInvalidData)

		response = self.client.post(reverse('MHLogin.MHLCallGroups.Scheduler.views.redo', 
			args=(self.call_group.id,)))
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(msg['undoSize'], 1)
		self.assertEqual(msg['redoSize'], 0)
		self.assertEqual(EventEntry.objects.count(), 1)

		#create a new and change event 1 time
		event = EventEntry.objects.get(checkString=checkString)
		#update
		updateEventInvalidData = {'data': '[{"pk":' + str(event.pk) + 
			',"model":"Scheduler.evententry","fields":{"oncallPerson":"' + str(provider.id) + 
			'","eventType":"0","startDate":"2012-12-20 08:00:00","endDate":"2012-12-21 08:00:00",\
				"eventStatus":1,"checkString":"' + checkString + '"}}]',
			'view': '{"name":"month","start":"2012-12-01 00:00:00","end":"2013-01-01 00:00:00"}'}

		response = self.client.post(reverse('MHLogin.MHLCallGroups.Scheduler.views.bulkUpdateEvents', 
			args=(self.call_group.id,)), data=updateEventInvalidData)

		response = self.client.post(reverse('MHLogin.MHLCallGroups.Scheduler.views.redo', 
			args=(self.call_group.id,)))
		msg = json.loads(response.content)
		self.assertEqual(msg['redoSize'], 0)
		self.assertEqual(msg['undoSize'], 2)
		self.assertEqual(msg['operateList'], [])


#add by xlin 121221 to test GetViewInfoTest
class GetViewInfoTest(TestCase):
	@classmethod
	def setUpClass(cls):
		clean_db_datas()
		cls.user = create_user('practicemgr5', 'lin', 'xing', 'demo', '', '', '', '',)

		call_group = CallGroup(description='test', team='team')
		call_group.save()
		cls.call_group = call_group

		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',
								call_group=call_group)
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
		response = self.client.post(reverse('MHLogin.MHLCallGroups.Scheduler.views.getViewInfo', 
			args=(self.call_group.id,)))
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(msg['view'], '')

		#get method without session
		response = self.client.get(reverse('MHLogin.MHLCallGroups.Scheduler.views.getViewInfo', 
			args=(self.call_group.id,)))
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(msg['view'], '')

		#403
		call_group2 = CallGroup(description='test2', team='team')
		call_group2.save()

		response = self.client.get(reverse('MHLogin.MHLCallGroups.Scheduler.views.getViewInfo', 
			args=(call_group2.id,)))
		self.assertEqual(response.status_code, 403)

		#get method with session---TODO
		view = '{"name":"agendaWeek","start":"2012-12-16 00:00:00","end":"2012-12-23 00:00:00"}'
		self.client.session[SessionHelper.SCHEDULE_LASTVIEW] = view
		self.client.session.save()
		response = self.client.get(reverse('MHLogin.MHLCallGroups.Scheduler.views.getViewInfo', 
			args=(self.call_group.id,)))
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(msg['view'], '')


#add by xlin 121221 to test saveViewInfo
class SaveViewInfoTest(TestCase):
	@classmethod
	def setUpClass(cls):
		clean_db_datas()
		cls.user = create_user('practicemgr5', 'lin', 'xing', 'demo', '', '', '', '',)

		call_group = CallGroup(description='test', team='team')
		call_group.save()
		cls.call_group = call_group

		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',
								call_group=call_group)
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
		response = self.client.get(reverse('MHLogin.MHLCallGroups.Scheduler.views.saveViewInfo', 
			args=(self.call_group.id,)))
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(msg['view'], '')

		#403
		call_group2 = CallGroup(description='test2', team='team')
		call_group2.save()

		response = self.client.post(reverse('MHLogin.MHLCallGroups.Scheduler.views.saveViewInfo', 
			args=(call_group2.id,)))
		self.assertEqual(response.status_code, 403)

		#post method without session
		view = {'view': '{"name":"month", "start":"2012-12-01 00:00:00", "end":"2013-01-01 00:00:00"}'}
		response = self.client.post(reverse('MHLogin.MHLCallGroups.Scheduler.views.saveViewInfo', 
			args=(self.call_group.id,)), data=view)
		self.assertEqual(response.status_code, 200)
		msg = json.loads(response.content)
		self.assertEqual(msg['view'], view['view'])


#add by xlin 121221 to test checkeUserInCallGroup
class CheckeUserInCallGroupTest(TestCase):
	@classmethod
	def setUpClass(cls):
		clean_db_datas()

	def test_checkeUserInCallGroup(self):
		call_group = CallGroup(description='test', team='team')
		call_group.save()
		request = HttpRequest()
		user = create_user('practicemgr1', 'lin', 'xing', 'demo')
		provider = Provider(username='provider', first_name='tes', last_name="meister", email='aa@ada.com',
					user=user, office_lat=0.0, office_longit=0.0)
		provider.save()
		mem = CallGroupMember(call_group=call_group, member=provider, alt_provider=1)
		mem.save()
		request.method = 'POST'
		request.POST['userId'] = user.pk
		response = checkeUserInCallGroup(request, call_group.id)
		self.assertEqual(response.content, '"ok"')

		call_group2 = CallGroup(description='test', team='team')
		call_group2.save()

		response = checkeUserInCallGroup(request, call_group2.id)
		self.assertEqual(response.content, '"err"')


#add by xlin 121224 to test getPrintableSchedule
class GetPrintableScheduleTest(TestCase):
	@classmethod
	def setUpClass(cls):
		clean_db_datas()
		cls.user = create_user('practicemgr5', 'lin', 'xing', 'demo', '', '', '', '',)

		call_group = CallGroup(description='test', team='team')
		call_group.save()
		cls.call_group = call_group

		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',
								call_group=call_group)
		practice.save()
		practice.call_groups.add(call_group)
		cls.practice = practice

	def setUp(self):
		self.client.post('/login/', {'username': self.user.username, 'password': 'demo'})

	@classmethod
	def tearDownClass(cls):
		clean_db_datas()

	def test_getPrintableSchedule(self):
		#not a staff login and call this method
		#a staff login
		staff = OfficeStaff(user=self.user)
		staff.save()
		staff.practices.add(self.practice)
		staff.current_practice = self.practice
		staff.save()
		response = self.client.post(reverse('MHLogin.MHLCallGroups.Scheduler.views.getPrintableSchedule'))
		self.assertEqual(response.status_code, 403)

		#a staff login
#		staff = OfficeStaff(user=self.user)
#		staff.save()
#		staff.practices.add(self.practice)
#		staff.current_practice = self.practice
#		staff.save()
#		manager = Office_Manager(user=staff, practice=self.practice, manager_role=1)
#		manager.save()
#		
#		response = self.client.post(reverse('MHLogin.MHLCallGroups.Scheduler.views.getPrintableSchedule'))
#		self.assertEqual(response.status_code, 200)
