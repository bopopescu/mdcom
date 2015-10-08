
import boto
import os

from django.conf import settings

from MHLogin.utils import logger

if(settings.AWS_ACCESS_KEY_ID):
	_connection = boto.connect_s3(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
else:
	_connection = None

class S3Storage:
	@classmethod
	def get_file(cls, name):
		bucket = _connection.get_bucket(settings.S3_BUCKET_NAME)
		key = bucket.get_key(name)
		if(key):
			return S3Storage(key)
		return None
	@classmethod
	def create_file(cls, name):
		bucket = _connection.get_bucket(settings.S3_BUCKET_NAME)
		key = bucket.get_key(name)
		if(not key):
			key = bucket.new_key(name)
		return S3Storage(key)

	def __init__(self, key):
		self.key = key

	def read(self):
		return self.key.read()

	def set_contents(self, contents):
		self.key.set_contents_from_string(contents)
	
	def delete(self):
		self.key.delete()

	def close(self):
		self.key.close()		

class LocalStorage:
	@classmethod
	def get_file(cls, name):
		try:
			path = os.path.join(settings.MEDIA_ROOT, name)
			return LocalStorage(open(path, "rb"), path)
		except (IOError, OSError) as ioe:
			logger.error("Unable to get file %s, exception: %s" %
						(name, str(ioe)))
			return None

	@classmethod
	def create_file(cls, name):
		try:
			path = os.path.join(settings.MEDIA_ROOT, name)
			if (not os.path.exists(os.path.dirname(path))):
				os.makedirs(os.path.dirname(path))
			return LocalStorage(open(path, "wb"), path)
		except (IOError, OSError), ioe:
			logger.error("Unable to create file %s, exception: %s" %
						(name, str(ioe)))
			return None
	def __init__(self, fp, path):
		self.fp = fp
		self.path = path

	def read(self):
		return self.fp.read()
	def set_contents(self, contents):
		self.fp.seek(0)
		self.fp.truncate()
		self.fp.write(contents)
		self.fp.flush()

	def close(self):
		self.fp.close()

	def delete(self):
		os.remove(self.path)



_readbackends = (
	LocalStorage,
	S3Storage,
)
_writebackends = (
	S3Storage,
	LocalStorage,
)

def get_file(name):
	for backend in _readbackends:
		try:
			f = backend.get_file(name)
			if(f):
				return f
		except:
			pass
	return None

def create_file(name):
	for backend in _writebackends:
		try:
			return backend.create_file(name)
		except:
			pass
	return None

