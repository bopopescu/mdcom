'''
Created on 2011-11-23

@author: mwang
'''
from Crypto.Cipher import AES
from django.conf import settings
import os
import tempfile
import time
import uuid

from MHLogin.utils.mh_logging import get_standard_logger 

# Setting up logging
logger = get_standard_logger('%s/utils/FileHelper.log' % 
		(settings.LOGGING_ROOT), 'utils.FileHelper', settings.LOGGING_LEVEL)


temp_file_prefix = "temp_"
attachments_temp_root = settings.ATTACHMENTS_TEMP_ROOT

if (attachments_temp_root and os.path.exists(attachments_temp_root)):
	tempfile.tempdir = attachments_temp_root


def generateTempFile(str, key=None):
	suffix = "".join(["_", uuid.uuid4().hex])
	temp_file = tempfile.NamedTemporaryFile(prefix=temp_file_prefix, suffix=suffix, delete=False)
	if key:
		padded = str + ' ' * ((16 - (len(str) % 16)) % 16)
		a = AES.new(key)  # TODO: when rm #2212 in use aes_encrypt in kms/utils
		str = a.encrypt(padded) 
	temp_file.write(str)
	path = temp_file.name
	temp_file.close()
	return os.path.split(path)[-1]


def getTempFilePath(file_name):
	return os.path.join(tempfile.gettempdir(), file_name)


def readTempFile(file_name, mode='r', key=None):
	path = getTempFilePath(file_name)
	temp_file = open(path, mode)
	try:
		str = temp_file.read()
		if key:
			a = AES.new(key)  # TODO: when rm #2212 in use aes_decrypt in kms/utils
			str = a.decrypt(str).rstrip()
		return str
	except (IOError):
		raise IOError   
	finally:
		temp_file.close()


def deleteTempFile(file_name):
	path = getTempFilePath(file_name)
	os.remove(path)


def cleanTempFile():
	tempdir = tempfile.gettempdir()
	for infile in os.listdir(tempdir):
		file_full_path = os.path.join(tempdir, infile)
		if infile.startswith(temp_file_prefix) and \
			time.time() - os.stat(file_full_path).st_ctime > settings.ATTACHMENTS_TEMP_TIMEOUT:
			try:
				os.remove(file_full_path)
			except (OSError):
				pass


def get_absolute_path(relative_path):
	absolute_path = "".join([settings.MEDIA_ROOT, "/", relative_path])
	return absolute_path

