
import datetime
import json
import mock

from django.http import Http404
from django.test import TestCase

from MHLogin.MHLPractices.models import Pending_Association
from MHLogin.apps.smartphone.v1.tests.utils import generateHttpRequest,\
	create_org_type, ct_practice
from MHLogin.apps.smartphone.v1.views_my_invitations import getMyInvitations, \
	acceptOrgInvitation, refuseOrgInvitation, acceptPracticeInvitation, \
	refusePracticeInvitation
from MHLogin.utils.tests import create_user
from MHLogin.utils.tests.tests import clean_db_datas
from MHLogin.utils.constants import RESERVED_ORGANIZATION_TYPE_ID_PRACTICE,\
	RESERVED_ORGANIZATION_TYPE_ID_GROUPPRACTICE
from MHLogin.MHLOrganization.tests.utils import create_organization


#add by xlin in 130117 to test getMyInvitations
class getMyInvitationsTest(TestCase):
	def setUp(self):
		clean_db_datas()

	def test_getMyInvitations(self):
		request = generateHttpRequest()

		#find 0
		result = getMyInvitations(request)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		self.assertEqual(len(msg['data']['invitations']), 0)

		#find 1
		pends = create_org_pending(request.user)
		result = getMyInvitations(request)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		self.assertEqual(len(msg['data']['invitations']), 1)


#add by xlin in 130118 to test acceptOrgInvitation
class AcceptOrgInvitationTest(TestCase):
	def setUp(self):
		clean_db_datas()

	@mock.patch('MHLogin.Invites.utils.thread.start_new_thread', autospec=True)
	def test_acceptOrgInvitation(self, start_thread):
		request = generateHttpRequest()

		#invalid org id
		org_id = 0
		try:
			acceptOrgInvitation(request, org_id)
		except Http404:
			self.assertRaises(Http404('No Pending_Organization matches the given query.'))

		#valid org id
		pending = create_org_pending(request.user, org_type_id=RESERVED_ORGANIZATION_TYPE_ID_PRACTICE)
		result = acceptOrgInvitation(request, pending.pk)
		self.assertEqual(result.status_code, 200)
		self.assertEqual(len(request.role_user.practices.all()), 1)
		self.assertEqual(request.role_user.current_practice, pending.practice_location)

	@mock.patch('MHLogin.Invites.utils.thread.start_new_thread', autospec=True)
	def test_acceptOrgInvitation_not_practice(self, start_thread):
		request = generateHttpRequest()

		#invalid org id
		org_id = 0
		try:
			acceptOrgInvitation(request, org_id)
		except Http404:
			self.assertRaises(Http404('No Pending_Organization matches the given query.'))

		#valid org id
		pending = create_org_pending(request.user, org_type_id=RESERVED_ORGANIZATION_TYPE_ID_GROUPPRACTICE)
		result = acceptOrgInvitation(request, pending.pk)
		self.assertEqual(result.status_code, 200)
		self.assertEqual(len(request.role_user.practices.all()), 1)
		self.assertIsNone(request.role_user.current_practice)


#add by xlin in 130123 to test refuseOrgInvitation
class RefuseOrgInvitationTest(TestCase):
	def setUp(self):
		clean_db_datas()

	def test_refuseOrgInvitation(self):
		request = generateHttpRequest()

		#404 find no invitation
		pending_id = 0
		try:
			refuseOrgInvitation(request, pending_id)
		except Http404:
			self.assertRaises(Http404('No Pending_Organization matches the given query.'))

		#refuse invitation success
		pending = create_org_pending(request.user)
		result = refuseOrgInvitation(request, pending.pk)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		self.assertEqual(msg['data'], {})
		self.assertEqual(len(request.role_user.practices.all()), 0)


#add by xlin in 130123 to test acceptPracticeInvitation
@mock.patch('MHLogin.Invites.utils.thread.start_new_thread', autospec=True)
class acceptPracticeInvitationTest(TestCase):
	def setUp(self):
		clean_db_datas()

	def test_acceptPracticeInvitation(self, start_thread):
		request = generateHttpRequest()

		#404
		pending_id = 0
		try:
			acceptPracticeInvitation(request, pending_id)
		except Http404:
			self.assertRaises(Http404('No Pending_Organization matches the given query.'))

		#success accpet a
		organization_type = create_org_type()
		practice = ct_practice('name', organization_type)
		pend = Pending_Association(from_user=request.user, to_user=request.user, 
			practice_location=practice, created_time=datetime.datetime.now())
		pend.save()
		result = acceptPracticeInvitation(request, pend.pk)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		self.assertEqual(msg['data'], {})


#add by xlin 130125 to test refusePracticeInvitation
class RefusePracticeInvitationTest(TestCase):
	def setUp(self):
		clean_db_datas()

	def test_refusePracticeInvitation(self):
		request = generateHttpRequest()

		#404
		try:
			pending_id = 0
			refusePracticeInvitation(request, pending_id)
		except Http404:
			self.assertRaises(Http404('No Pending_Organization matches the given query.'))

		#refuse success
		organization_type = create_org_type()
		practice = ct_practice('name', organization_type)
		pend = Pending_Association(from_user=request.user, to_user=request.user, 
			practice_location=practice, created_time=datetime.datetime.now())
		pend.save()

		result = refusePracticeInvitation(request, pend.pk)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		self.assertEqual(msg['data'], {})


def create_org_pending(to_user, org_type=None, org_type_id=None):
	org = create_organization(org_type=org_type, org_type_id=org_type_id)
	from_user = create_user('tset', 'abc', 'def', 'demo')
	pending = Pending_Association(from_user=from_user, to_user=to_user, 
		practice_location=org, created_time=datetime.datetime.now())
	pending.save()
	return pending
