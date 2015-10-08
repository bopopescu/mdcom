
import os
import datetime

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadhandler import MemoryFileUploadHandler, StopUpload

import logging
import logging.handlers

from MHLogin.utils.mh_logging import get_standard_logger 


# Setting up logging
LOG_FILENAME = '%s/utils/UploadHandlers.log'%(settings.LOGGING_ROOT,)

# Set up a specific logger with our desired output level
if (not 'logger' in locals()):
    logger = get_standard_logger('%s/utils/UploadHandlers.log'%(settings.LOGGING_ROOT), 
								'utils.UploadHandlers', settings.LOGGING_LEVEL)

class UploadProgressCachedHandler(MemoryFileUploadHandler):
    """
    Tracks progress for file uploads.
    The http post request must contain a query parameter, 'X-Progress-ID',
    which should contain a unique string to identify the upload to be tracked.
    """

    def __init__(self, request=None):
        super(UploadProgressCachedHandler, self).__init__(request)
        self.progress_id = None
        self.cache_key = None
        logging.debug("UploadProgressCachedHandler: __init__ " + str(datetime.datetime.now()))

    def handle_raw_input(self, input_data, META, content_length, boundary, encoding=None):
        self.content_length = content_length
        if 'X-Progress-ID' in self.request.GET:
            self.progress_id = self.request.GET['X-Progress-ID']
        if self.progress_id:
            self.cache_key = "%s_%s" % (self.request.META['REMOTE_ADDR'], self.progress_id )
            cache.set(self.cache_key, {
                'state': 'uploading',
                'size': self.content_length,
                'received': 0
            })
            logging.debug("UploadProgressCachedHandler: handle_raw_input " + str(datetime.datetime.now())) 
        if type(settings.MAX_UPLOAD_SIZE) == type(1) and settings.MAX_UPLOAD_SIZE > 0 and content_length > settings.MAX_UPLOAD_SIZE*1024*1024:
            raise StopUpload(connection_reset=True)

    def new_file(self, field_name, file_name, content_type, content_length, charset=None):
        logging.debug("UploadProgressCachedHandler: new_file") 
        pass

    def receive_data_chunk(self, raw_data, start):
        if self.cache_key:
            data = cache.get(self.cache_key)
            if data:
                data['received'] += self.chunk_size
                cache.set(self.cache_key, data)
                logging.debug("UploadProgressCachedHandler: receive_data_chunk received: %s" % cache.get(self.cache_key)['received'] + ' ' + str(datetime.datetime.now())) 
        return raw_data
    
    def file_complete(self, file_size):
        logging.debug("UploadProgressCachedHandler: file_complete " + str(datetime.datetime.now())) 
        pass

    def upload_complete(self):
        if self.cache_key:
            cache.delete(self.cache_key)
        logging.debug("UploadProgressCachedHandler: upload_complete " + str(datetime.datetime.now())) 
