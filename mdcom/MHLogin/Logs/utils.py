
import os.path
import re
import linecache

from datetime import datetime
from django.conf import settings

LOG_FILES_PAGINATE_LINES = 100

"""			
Below our regex matches our logging format:
	%(asctime)s - %(filename)s:%(lineno)d(%(funcName)s) - %(levelname)s - %(message)s
And one sample log:	
	2012-10-10 12:50:26,627 - tests.py:29(setUpClass) - DEBUG - Set up test class for speech tests
"""
LOG_FILES_RE = '(?P<Date>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})\s-\s'\
			'(?P<Filename>[a-zA-Z0-9_\.:\(\)]+)\s-\s'\
			'(?P<Level>\w+)\s-\s'\
			'(?P<Message>.+)'
log_re = re.compile(LOG_FILES_RE)

LOG_FILENAMES_RE = '.+\\.log$|.+\\.log\\.[0-9]+$'
log_filenames_re = re.compile(LOG_FILENAMES_RE)


class LogFilesManager(object):
	def list_logfiles(self, path=settings.LOGGING_ROOT):
		""" Returns list of .log files recursed into logfile dir """
		file_list = []
		# List only files
		for root, _, files in os.walk(path):
			for f in files:  # build list of log files based on regex
				if log_filenames_re.match(f):
					filename = os.path.join(root, f)
					modtime = datetime.fromtimestamp(os.path.getmtime(filename)).\
							strftime("%m/%d/%Y %H:%M:%S")
					file_list.append([filename, modtime])
		return file_list

	def get_file_lines_count(self, logfile):
		""" Returns array of counts for pagination """
		line_counts = []
		count = 0
		for _ in logfile:
			line_counts.append(count)
			count += 1
		# if file was empty return empty array 
		if line_counts:
			line_counts.append(count)

		return line_counts

	def parse_log_file(self, logfile, from_line=0, to_line=LOG_FILES_PAGINATE_LINES, full=False):
		""" Parse the log file based on LOG_FILES_RE, return a list 
			of 4-tuples each 4-tuple being one entry in the log file.
		"""
		file_dict = []
		# Reading amount of lines
		line_num = from_line
		if full:
			file_obj = open(logfile, 'rb')
			to_line = self.get_file_lines_count(file_obj).__len__()
		for _ in range(to_line):
			try:
				line = linecache.getline(logfile, line_num)
				matches_set = log_re.findall(str(line))
				file_dict.append(matches_set)
				line_num += 1
			except IndexError:
				# log file is shorter then LOG_FILES_PAGINATE_LINES or
				# amount of lines smaller then from_line left
				pass
		return file_dict

	def compile_header_from_regexp(self, regexp=None):
		""" Create log header from regex """
		header_length = log_re.groups
		header_list = []
		if log_re.groupindex:
			for number in range(header_length):
				header_list.append(number)
			for group_name, index in log_re.groupindex.iteritems():
				header_list[int(index) - 1] = group_name
		return header_list

