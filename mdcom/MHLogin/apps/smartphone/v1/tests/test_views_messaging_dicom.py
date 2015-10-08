
import json

from django.test import TestCase

from MHLogin.apps.smartphone.v1.tests.utils import generateHttpRequest
from MHLogin.apps.smartphone.v1.views_messaging_dicom import dicom_view


#add by xlin in 130131 to test dicom_view
class dicom_viewTest(TestCase):
	def test_dicom_view(self):
		message_id = 0
		attachment_id = 0
		request = generateHttpRequest()

		#get method
		request.method = 'GET'
		result = dicom_view(request, message_id, attachment_id)
		self.assertEqual(result.status_code, 400)
		msg = json.loads(result.content)
		self.assertEqual(msg['errno'], 'GE002')

		#post method
		request.method = 'POST'

		#invalid form data
		request.POST['secret'] = 'abc'
		result = dicom_view(request, message_id, attachment_id)
		self.assertEqual(result.status_code, 400)
		msg = json.loads(result.content)
		self.assertEqual(msg['errno'], 'GE031')

		#valid form data
		request.POST['secret'] = 'cb1996537e304e47baf12cc5acaaada6'
		try:
			result = dicom_view(request, message_id, attachment_id)
		except:
			self.assertEqual(result.status_code, 400)

#		need to add method of generate attachment for unittest
		#MessageAttachment
#		attchment = MessageAttachment()
#		attchment.save()
#		result = dicom_view(request, message_id, attchment.uuid)
#		self.assertEqual(result.status_code,200)

