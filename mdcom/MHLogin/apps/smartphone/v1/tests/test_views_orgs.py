import json

from django.http import Http404
from django.test.testcases import TestCase

from MHLogin.apps.smartphone.v1.tests.utils import generateHttpRequest
from MHLogin.apps.smartphone.v1.views_orgs import getMyOrgs, getOrgUsers
from MHLogin.MHLPractices.models import PracticeLocation, OrganizationSetting,\
	OrganizationType
from MHLogin.MHLOrganization.tests.utils import create_organization


#add by xlin in 130116 to test getMyOrgs
class getMyOrgsTest(TestCase):
	def setUp(self):
		PracticeLocation.objects.all().delete()
		OrganizationType.objects.all().delete()
		OrganizationSetting.objects.all().delete()

	def test_getMyOrgs(self):
		request = generateHttpRequest()

		#0 find
		result = getMyOrgs(request)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		self.assertEqual(len(msg['data']['organizations']), 0)

		#1 find
		_organization = create_organization()
		request.role_user.practices.add(_organization)
		request.role_user.save()

		result = getMyOrgs(request)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		self.assertEqual(len(msg['data']['organizations']), 1)


#add by xlin in 130116 to test getOrgUsers
class getOrgUsersTest(TestCase):
	def setUp(self):
		PracticeLocation.objects.all().delete()
		OrganizationType.objects.all().delete()
		OrganizationSetting.objects.all().delete()

	def test_getOrgUsers(self):
		request = generateHttpRequest()

		#404
		org_id = 1
		try:
			result = getOrgUsers(request, org_id)
		except Http404:
			self.assertRaises(Http404('No Organization matches the given query.'))

		_organization = create_organization()
		request.provider.practices.add(_organization)
		request.provider.save()

		result = getOrgUsers(request, _organization.pk)
		self.assertEqual(result.status_code, 200)
		msg = json.loads(result.content)
		self.assertEqual(len(msg['data']['users']), 1)
		self.assertEqual(msg['data']['users'][0]['first_name'], request.user.first_name)

