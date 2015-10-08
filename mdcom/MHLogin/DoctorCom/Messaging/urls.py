
try:
	from django.conf.urls import patterns, url
except ImportError:  # remove when django 1.5 fully integrated
	from django.conf.urls.defaults import patterns, url


urlpatterns = patterns('MHLogin.DoctorCom.Messaging',
	url(r'^New/$', 'views.message_edit'),
	url(r'^NewMulti/$', 'views.message_edit_multi'),

	url(r'^Upload/$', 'views_upload.upload'),
	url(r'^Upload/UploadProgress/$', 'views_upload.uploadProgress'),
	url(r'^Upload/DeleteAttachment/$', 'views_upload.deleteAttachment'),

	url(r'^Edit/(?P<message_id>[0-9a-f]{32})/$', 'views.message_edit'),
	url(r'^AJAX/Edit/Check/$', 'views.message_edit_check'),
	url(r'^(?P<message_id>[0-9a-f]{32})/View/$', 'views.message_view'),
	url(r'^(?P<message_id>[0-9a-f]{32})/View/Attachment/(?P<attachment_id>[0-9a-f]{32})/?(\..*)?$', 'views.download_attachment', name="messaging-download_attachment"),
	url(r'^(?P<message_id>[0-9a-f]{32})/Check/Attachment/(?P<attachment_id>[0-9a-f]{32})/?(\..*)?$', 'views.check_attachment', name="messaging-check_attachment"),

	url(r'^(?P<message_id>[0-9a-f]{32})/ViewDicomJPG/Attachment/(?P<attachment_id>[0-9a-f]{32})/(?P<index>\d+)/$', 'views_dicom.dicom_view_jpg', name="messaging-dicom_view_jpg"),
	# reserved
#	url(r'^(?P<message_id>[0-9a-f]{32})/ViewDicomXML/Attachment/(?P<attachment_id>[0-9a-f]{32})/?(\..*)?$', 'views_dicom.dicom_view_xml', name="messaging-dicom_view_xml"),
	url(r'^(?P<message_id>[0-9a-f]{32})/ViewDicom/Attachment/(?P<attachment_id>[0-9a-f]{32})/?(\..*)?$', 'views_dicom.dicom_view', name="messaging-dicom_view"),
	url(r'^(?P<message_id>[0-9a-f]{32})/CheckDicom/Attachment/(?P<attachment_id>[0-9a-f]{32})/?(\..*)?$', 'views_dicom.dicom_check', name="messaging-dicom_check"),

	url(r'AJAX/(?P<message_id>[0-9a-f]{32})/(?P<type>(received|sent))/$', 'views_ajax.message_view'),

	url(r'AJAX/(?P<message_id>[0-9a-f]{32})/Update/$', 'views_ajax.update_message'),
	url(r'AJAX/(?P<type>(Received|Sent))/$', 'views_ajax.get_messages'),
	url(r'AJAX/UnreadMsgCount/$', 'views_ajax.get_unread_count'),

	url(r'^Refer/$', 'views_refer.refer_home'),
	url(r'^Refer/(?P<refer_id>[0-9a-f]{32})/Update/$', 'views_refer.update_refer'),	
	url(r'^Refer/PDF/(?P<refer_id>[0-9a-f]{32})/$', 'views_refer.download_pdf'),
	url(r'^Refer/Ajax/RefreshPracticeInfo/$', 'views_refer.refresh_practice_info'),
	url(r'^Refer/ProceedSave/$', 'views_refer.proceed_save_refer'),
	url(r'^Refer/CheckSendRefer/$', 'views_refer.check_send_refer'),
)

