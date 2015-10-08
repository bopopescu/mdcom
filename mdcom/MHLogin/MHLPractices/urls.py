
try:
	from django.conf.urls import patterns
except ImportError:  # remove when django 1.5 fully integrated
	from django.conf.urls.defaults import patterns


urlpatterns = patterns('MHLogin.MHLPractices',
	(r'^Profile/$', 'views.practice_profile_view'),
	(r'^Profile/Edit/$', 'views.practice_profile_edit'),
	(r'^Profile/IVRAccess/$', 'views.practice_edit_access_numbers'),
	(r'^Profile/ForwardingAnsweringSetting/$', 'views.anssvc_caller'),
	(r'^Hours/$', 'views.practice_manage_hours'),
	(r'^Holidays/$', 'views.practice_manage_holidays'),
	(r'^Holidays/Edit/(?P<holidayid>\d+)$', 'views.practice_edit_holidays'),

	(r'^getPenddings/$', 'views.getPenddings'),

	(r'^Staff/$', 'views.staffHome'),
	(r'^Staff/newProvider/$', 'views.newProvider'),
	(r'^Staff/newStaff/$', 'views.newStaff'),
	(r'AJAX/addAssociation/$', 'views_ajax.addAssociation'),
	(r'AJAX/resendAssociation/$', 'views_ajax.resendAssociation'),
	(r'AJAX/removeAssociation/$', 'views_ajax.removeAssociation'),
	(r'AJAX/rejectAssociation/$', 'views_ajax.rejectAssociation'),
	(r'AJAX/addProviderToPractice/$', 'views_ajax.addProviderToPractice'),
	(r'AJAX/removeProvider/$', 'views_ajax.removeProvider'),
	(r'AJAX/changeSmartphonePermission/$', 'views_ajax.changeSmartphonePermission'),
	# add by xlin 20120301 to add new view to remove staff, change role, get provider, etc	
	(r'AJAX/cancelInvitation/', 'views_ajax.cancelInvitation'),
	(r'AJAX/cancelExistInvitation/', 'views_ajax.cancelExistInvitation'),
	(r'AJAX/sendNewProviderEmail/', 'views_ajax.sendNewProviderEmail'),
	# done xlin 
	(r'AJAX/checkPenddingExist/', 'views_ajax.checkPenddingExist'),
	(r'^$', 'views.practice_main_view'),

	(r'AJAX/getProviderByEmailOrNameInCallGroup/', 'views_ajax.getProviderByEmailOrNameInCallGroup'),
)
