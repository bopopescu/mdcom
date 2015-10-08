
from django.core.paginator import Paginator
from django.shortcuts import render_to_response
from django.http import HttpResponseBadRequest

from MHLogin.utils.templates import get_context

from MHLogin.Logs.models import LogFiles
from MHLogin.Logs.utils import LogFilesManager, LOG_FILES_PAGINATE_LINES


class LogFileChangeList(object):
	""" mainly for opts, rest to make admin template happy """
	def __init__(self, opts, result_cnt=0, full_result_cnt=0):
		self.opts = opts
		self.result_count = result_cnt
		self.full_result_count = full_result_cnt
		self.date_hierarchy = 0
		self.paginator = 0
		self.page_num = 0
		self.show_all = 0
		self.multi_page = 0
		self.can_show_all = 0


def logfiles_list(request, root_path):
	"""Lists Log Files in settings directory"""
	context = get_context(request)
	manager = LogFilesManager()
	files_tup = manager.list_logfiles()
	file_list = {}
	count = 0
	if files_tup:
		for ftup in files_tup:
			file_list[str(count)] = ftup
			count += 1

	context['cl'] = LogFileChangeList(getattr(LogFiles, '_meta'), count, count)
	context['files_list'] = file_list
	context['app_label'] = getattr(LogFiles, '_meta').app_label
	context['root_path'] = root_path
	context['title'] = 'Select Logfile to view'

	return render_to_response('logfile_change_list.html', context)


def logfile_view(request, logfile_id, root_path):
	""" return list of log file contents paged by main regexp"""
	context = get_context(request)
	manager = LogFilesManager()
	try:
		page = int(request.GET['page']) if 'page' in request.GET else 1
	except ValueError:
		page = 1

	files_tup = manager.list_logfiles()
	try:
		filename = files_tup[int(logfile_id)][0]
	except Exception as e:
		return HttpResponseBadRequest(str(e))

	paginator = Paginator(manager.get_file_lines_count(open(filename, 'rb')), 
						LOG_FILES_PAGINATE_LINES)

	paged_lines = paginator.page(page)
	first_line = paged_lines.object_list[0] if paged_lines.object_list else 0

	paged_lines.object_list = manager.parse_log_file(filename, first_line)
	header_list = manager.compile_header_from_regexp()
	context['cl'] = LogFileChangeList(getattr(LogFiles, '_meta'))
	context['header_list'] = header_list
	context['file_name'] = filename
	context['file_id'] = logfile_id
	context['paginator'] = paged_lines
	context['page'] = page
	context['app_label'] = getattr(LogFiles, '_meta').app_label
	context['root_path'] = root_path
	context['title'] = 'Logfile contents'

	return render_to_response('logfile_change_form.html', context)

