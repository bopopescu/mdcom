#add by xlin 130107 to generate http request
import base64
import os
import random

from django.http import HttpRequest
from django.test import Client

from Crypto.Cipher import XOR
from MHLogin.KMS.utils import split_user_key, strengthen_key
from MHLogin.MHLPractices.models import OrganizationType, OrganizationSetting, \
	PracticeLocation
from MHLogin.MHLUsers.models import Provider
from MHLogin.apps.smartphone.models import SmartPhoneAssn
from MHLogin.utils.tests import create_user
from MHLogin.utils.constants import RESERVED_ORGANIZATION_TYPE_ID_PRACTICE


def generateHttpRequest():
	# Fix for 2030 - should rename function, it does more than just generate request 
	# TODO: for requests should use Django's test Client(), see IVR unittests for 
	# example of view unittests using Django's test client request handling features.
	env = Client()._base_environ()
	user = create_mhluser()

	request = HttpRequest()
	request.META['REMOTE_ADDR'] = env['REMOTE_ADDR']

	key = strengthen_key('demo')
	split1, split2 = split_user_key('demo')
	db_key = os.urandom(32)
	xor = XOR.new(base64.b64decode(split2))
	dbsplit = base64.b64encode(xor.encrypt(db_key))

	assn = SmartPhoneAssn(
		user=user,
		device_serial='',
		version='1.22',
		platform='iPad',
		user_type=1,
	)
	assn.save(request)
	assn.update_secret(split1, key)
	assn.update_db_secret(dbsplit, db_key)

	request.REQUEST = {}
	request.META['HTTP_DCOM_DEVICE_ID'] = request.REQUEST['DCOM_DEVICE_ID'] = assn.device_id
	request.session = dict()

	request.user = user

	providers = Provider.objects.filter(user=user)
	if not providers:
		provider = Provider(user=request.user, office_lat=0.0, office_longit=0.0)
		provider.save()
		request.provider = provider
		request.role_user = provider
	return request


def create_mhluser():
	chars = 'abcdefghijklmnopqrstuvwxyz0123456789'
	username = ''.join([random.choice(chars) for _ in range(8)])
	firstname = ''.join([random.choice(chars) for _ in range(6)])
	lastname = ''.join([random.choice(chars) for _ in range(6)])

	return create_user(username, firstname, lastname, 'demo')


def create_org_type(org_setting=None):
	if not org_setting:
		org_setting = OrganizationSetting() 
		org_setting.save()
	type_name = "Test Org Type"
	organization_type = OrganizationType(name=type_name, organization_setting=org_setting)
	# force id for test - MySQL UT's don't re-use ids after cleanup 
	organization_type.id = RESERVED_ORGANIZATION_TYPE_ID_PRACTICE
	# TODO: issue 2030, reserved id's is a hazardous approach, the UT's 
	# were working with SQLlite but not with MySQL, DB engines recycle
	# id's differently and we should not rely on reserved id fields.  This 
	# should be addressed in a separate Redmine as model changes may occur.
	organization_type.save()
	return organization_type


def ct_practice(name, organization_type):
	"""
	create test practice
	now this is also as organization
	"""
	practices = PracticeLocation.objects.filter(practice_name=name)
	if practices:
		return practices[0]
	practice = PracticeLocation(practice_name='name',
							practice_longit='0.1',
							practice_lat='0.0',
							mdcom_phone='8005550085',
							organization_type=organization_type)
	practice.save()

	return practice

