from django.test import TestCase

from MHLogin.apps.smartphone.v1.tests.utils import generateHttpRequest
from MHLogin.apps.smartphone.v1.views_server import info


#add by xlin in 130125 to test info
class infoTest(TestCase):
	def test_info(self):
		request = generateHttpRequest()
		result = info(request)
		self.assertEqual(result.status_code, 200)

