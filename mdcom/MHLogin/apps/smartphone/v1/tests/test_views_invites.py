import json

from django.http import Http404
from django.test import TestCase

from MHLogin.Invites.models import Invitation
from MHLogin.MHLPractices.models import PracticeLocation
from MHLogin.MHLUsers.models import OfficeStaff
from MHLogin.apps.smartphone.models import SmartPhoneAssn
from MHLogin.apps.smartphone.v1.tests.utils import generateHttpRequest, \
	create_org_type, ct_practice
from MHLogin.apps.smartphone.v1.views_invites import list_invites, new_invite, \
	resend_invite, cancel_invite
from MHLogin.utils.tests.tests import clean_db_datas


#add by xlin in 130128 to test views_invites
class ViewsInvitesTest(TestCase):
	def setUp(self):
		clean_db_datas()

	def test_views_invites(self):
		request = generateHttpRequest()

		#an office staff login
		staff = OfficeStaff(user=request.user)
		staff.save()
		assn = SmartPhoneAssn.all_objects.get(device_id=request.REQUEST['DCOM_DEVICE_ID'])
		assn.user_type = 101
		assn.save(request)

		result = list_invites(request)
		self.assertEqual(result.status_code, 403)

		#a provider login
		assn = SmartPhoneAssn.all_objects.get(device_id=request.REQUEST['DCOM_DEVICE_ID'])
		assn.user_type = 1
		assn.save(request)

		#find 0 invitation
		result = list_invites(request)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		self.assertEqual(len(msg['data']['invitations']), 0)

		usertype = 1
		#invite has assignPractice
		organization_type = create_org_type()
		practice =  ct_practice('name', organization_type)
		code = '12345'
		email = 'test2@suzhoukada.com'
		invite = Invitation(code=code, sender=request.user, recipient=email, 
			userType=usertype, assignPractice=practice)
		invite.save()
		result = list_invites(request)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		self.assertEqual(len(msg['data']['invitations']), 1)


#add by xlin in 130129 to test new_invite
class NewInviteTest(TestCase):
	def setUp(self):
		clean_db_datas()

	def test_new_invite(self):
		usertype = 1
		email = 'test@suzhoukada.com'
		email2 = 'test2@suzhoukada.com'
		email3 = 'test2@suzhoukada.com'
		email4 = 'test2@suzhoukada.com'
		request = generateHttpRequest()

		#get method
		request.method = 'GET'
		result = new_invite(request)
		self.assertEqual(result.status_code, 400)
		msg = json.loads(result.content)
		self.assertEqual(msg['errno'], 'GE002')

		#post method
		request.method = 'POST'

		#an office staff login
		staff = OfficeStaff(user=request.user)
		staff.save()
		assn = SmartPhoneAssn.all_objects.get(device_id=request.REQUEST['DCOM_DEVICE_ID'])
		assn.user_type = 101
		assn.save(request)

		result = new_invite(request)
		self.assertEqual(result.status_code, 403)

		#a provider login
		assn = SmartPhoneAssn.all_objects.get(device_id=request.REQUEST['DCOM_DEVICE_ID'])
		assn.user_type = 1
		assn.save(request)

		#invalid form data
		request.POST['email'] = email
		request.POST['note'] = '2sxc'
		request.POST['invite_user_type'] = usertype
		request.POST['invite_type'] = 'sfsdf'

		result = new_invite(request)
		self.assertEqual(result.status_code, 400)
		msg = json.loads(result.content)
		self.assertEqual(msg['errno'], 'GE031')

		#valid form data but invite type is 2
		request.POST['email'] = email
		request.POST['note'] = 'test'
		request.POST['invite_user_type'] = usertype
		request.POST['invite_type'] = 2

		result = new_invite(request)
		self.assertEqual(result.status_code, 403)

		request.user.email = email
		request.user.save()
		#valid form data but user not exist
		request.POST['invite_type'] = 1
		result = new_invite(request)
		self.assertEqual(result.status_code, 400)
		msg = json.loads(result.content)
		self.assertEqual(msg['errno'], 'IN002')

		#valid form data and not exist email
		request.POST['email'] = 'abc@test.com'
		result = new_invite(request)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		id = Invitation.objects.all()[0].id
		self.assertEqual(msg['data']['id'], id)

		#manager and has current practice
		assn = SmartPhoneAssn.all_objects.get(device_id=request.REQUEST['DCOM_DEVICE_ID'])
		assn.user_type = 100
		assn.save(request)
		request.POST['invite_type'] = 2
		request.POST['email'] = email2
		organization_type = create_org_type()
		practice = PracticeLocation(practice_name='test',
								practice_longit='0.1',
								practice_lat='0.0',
								mdcom_phone='8005550085',
								organization_type=organization_type)
		practice.save()
		user = OfficeStaff.objects.get(user=request.user)
		user.current_practice = practice
		user.save()
		result = new_invite(request)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		id = Invitation.objects.get(recipient=email2).id
		self.assertEqual(msg['data']['id'], id)

		#resend invitation
		invite = Invitation(sender=request.user, recipient=email, userType=usertype)
		invite.save()
		request.POST['email'] = email3
		result = new_invite(request)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		id = Invitation.objects.get(recipient=email3).id
		self.assertEqual(msg['data']['id'], id)

		#user time setting
		request.POST['use_time_setting'] = True
		request.POST['email'] = email4
		result = new_invite(request)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		id = Invitation.objects.get(recipient=email4).id
		self.assertEqual(msg['data']['id'], id)


#add by xlin in 130129 to test resend_invite
class ResendInviteTest(TestCase):
	def test_resend_invite(self):
		email = 'test@suzhoukada.com'
		invitation_id = 0
		request = generateHttpRequest()

		#get method
		request.method = 'GET'
		result = resend_invite(request, invitation_id)
		self.assertEqual(result.status_code, 400)
		msg = json.loads(result.content)
		self.assertEqual(msg['errno'], 'GE002')

		#post method
		request.method = 'POST'
		#an office staff login
		staff = OfficeStaff(user=request.user)
		staff.save()
		assn = SmartPhoneAssn.all_objects.get(device_id=request.REQUEST['DCOM_DEVICE_ID'])
		assn.user_type = 101
		assn.save(request)
		result = resend_invite(request, invitation_id)
		self.assertEqual(result.status_code, 403)

		#a provider login
		assn = SmartPhoneAssn.all_objects.get(device_id=request.REQUEST['DCOM_DEVICE_ID'])
		assn.user_type = 1
		assn.save(request)

		#invalid invitation id
		note = 'test'
		request.POST['note'] = note
		try:
			resend_invite(request, invitation_id)
		except Http404:
			self.assertRaises(Http404())

		usertype = 1
		#another email
		errEmail = 'err@suzhoukada.com'
		code = '12345'
		invite = Invitation(code=code, sender=request.user, recipient=errEmail, 
			userType=usertype)
		invite.save()
		result = resend_invite(request, invite.pk)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		self.assertEqual(msg['data']['id'], invite.id)

		#use time setting
		request.POST['use_time_setting'] = True
		errEmail = 'err3@suzhoukada.com'
		code = '12wsxs'
		invite = Invitation(code=code, sender=request.user, recipient=errEmail, 
			userType=usertype)
		invite.save()
		result = resend_invite(request, invite.pk)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		self.assertEqual(msg['data']['id'], invite.id)


#add by xlin in 130130 to test cancel_invite
class cancel_inviteTest(TestCase):
	def test_cancel_invite(self):
		invitation_id = 0
		email = 'test@suzhoukada.com'
		request = generateHttpRequest()

		#an office staff login
		staff = OfficeStaff(user=request.user)
		staff.save()
		assn = SmartPhoneAssn.all_objects.get(device_id=request.REQUEST['DCOM_DEVICE_ID'])
		assn.user_type = 101
		assn.save(request)
		result = cancel_invite(request, invitation_id)
		self.assertEqual(result.status_code, 403)

		#a provider login
		assn = SmartPhoneAssn.all_objects.get(device_id=request.REQUEST['DCOM_DEVICE_ID'])
		assn.user_type = 1
		assn.save(request)

		#404 not found invitation
		try:
			cancel_invite(request, invitation_id)
		except Http404:
			self.assertRaises(Http404())

		code = 'abcdefg'
		usertype = 1
		invite = Invitation(code=code, sender=request.user, recipient=email, 
			userType=usertype)
		invite.save()
		result = cancel_invite(request, invite.pk)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		self.assertEqual(msg['data'], {})
		self.assertEqual(Invitation.objects.count(), 0)

