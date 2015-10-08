
import os
import sys
import logging.handlers

from django.conf import settings


def get_standard_logger(logfile, logger_name, level=settings.LOGGING_LEVEL, maxbytes=2097152,
	fmt="%(asctime)s - %(filename)s:%(lineno)d(%(funcName)s) - %(levelname)s - %(message)s"):
	"""
	Standard logger initialization, override defaults as needed.  Typically there is
	one logger per module but loggers can be created and removed as needed.
	Note: if logfile contains filename and directory the directory must already exist
	and have appropriate permissions for file creation and modification.  If there is
	an exception an error is generated to stderr and StreamHandler is used.

	:param logfile: The file and path of the file to log messages to
	:type logfile: string  
	:param logger_name: The name of the logger, usually the module name
	:type logger_name: string  
	:param level: Severity level of this logger, can be changed
	:type level: int  
	:param maxbytes: Maximum number of bytes in logfile before rotation begins
	:type maxbytes: int  
	:param fmt: Format of the log message uses well known tags such as asctime, filename, etc.
	:type fmt: string  

	:returns: logger -- the newly created logger 
	"""
	# Set up a specific logger with our desired output level
	logger = logging.getLogger(logger_name)

	try:
		if (not os.path.exists(os.path.dirname(logfile))):
			# attempt to create directory, IOError if unable or no permissions
			os.makedirs(os.path.dirname(logfile))

		# Add the log message handler to the logger
		handler = logging.handlers.RotatingFileHandler(
							logfile, maxBytes=maxbytes, backupCount=5)
	except (IOError, OSError), io:
		sys.stderr.write("ERROR creating log handler: %s\n" % str(io))
		# log to std error 
		handler = logging.StreamHandler()

	# Add a formatter
	handler.setFormatter(logging.Formatter(fmt))
	# add handler to logger
	logger.addHandler(handler)
	logger.setLevel(level)
	# Don't propagate, see comments in DoctorCom.NumberProvisioner.tests if you see 
	# unexpected console logging.  It may relate to some packages outside our control adding 
	# handlers to the root logger.  There may also be a distant side-effect related to our 
	# non-standard logging setup, we do not match Django 1.5's startproject logging config.
	# see: https://redmine.mdcom.com/issues/2209

	return logger

