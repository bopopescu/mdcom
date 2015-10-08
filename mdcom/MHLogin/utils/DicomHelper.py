# -*- coding: utf-8 -*-
'''
Created on 2012-11-1

@author: mwang
'''

import urllib2
from django.conf import settings

from MHLogin.utils.MultipartPostHandler import MultipartPostHandler, FileInfo
from MHLogin.utils.admin_utils import mail_admins

DICOM_PARAM_NAME_REVOKE_URL = "revoke_url"
DICOM_PARAM_NAME_TOKEN = "token"
DICOM_PARAM_NAME_DICOM_FILE = "dicom_file"


def sendToDicomServer(dicom_info):
	dicom_name = dicom_info["name"]
	dicom_token = str(dicom_info["token"])
	dicom_content = dicom_info["content"]

	opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(),
									MultipartPostHandler)
	params = { 
				DICOM_PARAM_NAME_REVOKE_URL : settings.DICOM_REVOKE_URL, 
				DICOM_PARAM_NAME_TOKEN : dicom_token,
				DICOM_PARAM_NAME_DICOM_FILE : FileInfo(dicom_name, dicom_content)
			}

	try:
		response = opener.open(settings.DICOM_SERVER_URL, params).read()
		return response
	except Exception as e:
		msg = 'Sending dicom to server failed -- attachment id: %s!' % (dicom_token)
		err_email_body = '\n'.join([
				msg,
				''.join(['Server: ', settings.SERVER_ADDRESS]),
				''.join(['Exception: ', str(e)]),
			])
		mail_admins(msg, err_email_body)
		raise e

