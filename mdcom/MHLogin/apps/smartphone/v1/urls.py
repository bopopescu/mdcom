
try:
	from django.conf.urls import patterns
except ImportError:  # remove when django 1.5 fully integrated
	from django.conf.urls.defaults import patterns


urlpatterns = patterns('MHLogin.apps.smartphone.v1',

	(r'^Device/CheckUser/$', 'views_device.check_user'),
	(r'^Device/Associate/$', 'views_device.associate'),
	(r'^Device/Dissociate/$', 'views_device.dissociate'),
	(r'^Device/Check_In/$', 'views_device.check_in'),
	(r'^Device/Re-Key/$', 'views_device.re_key'),
	(r'^Device/AppVersionUpdate/$', 'views_device.app_version_update'),
	(r'^Device/UpdatePushToken/$', 'views_device.register_push_token'),

	# Account management
	(r'^Account/GetKey/$', 'views_account.get_key'),
	(r'Practice/$', 'views_account.practice_mgmt'),
	(r'Site/$', 'views_account.site_mgmt'),
	(r'Account/CallForwarding/$', 'views_account.call_fwd_prefs'),
	(r'Account/GetDComNumber/$', 'views_account.get_dcom_number'),
	(r'Account/GetMobilePhone/$', 'views_account.get_mobile_phone'),
	(r'Account/UpdateMobilePhone/$', 'views_account.update_mobile_phone'),
	(r'Account/AnsweringService/$', 'views_account.anssvc_forwarding'),
	(r'Account/Preference/$', 'views_account.preference'),

	(r'^User_Lists/My_Site/Providers/$', 'views_users.site_providers'),
	(r'^User_Lists/My_Site/Staff/$', 'views_users.site_staff'),
	(r'^User_Lists/My_Site/Med_Students/$', 'views_users.site_students'),
	(r'^User_Lists/My_Practice/Providers/$', 'views_users.practice_providers'),
	(r'^User_Lists/My_Practice/Staff/$', 'views_users.practice_staff'),
	(r'^User_Lists/Community/Providers/$', 'views_users.community_providers'),
	(r'^User_Lists/GetProvidersAndStaffs/$', 'views_users.get_all_providers_and_staffs'),

	(r'^User/(?P<user_id>\d+)/Profile/$', 'views_users.user_info'),
	(r'^User/Search/$', 'views_users.user_search'),
	(r'^User/Profile/UpdatePhoto/$', 'views_users.user_update_photo'),

	(r'^Practice_Lists/LocalOffice/$', 'views_practices.local_office'),
	(r'^Practice/(?P<practice_id>\d+)/Profile/$', 'views_practices.practice_info'),

	(r'^Messaging/List/Received/$', 'views_messaging.rx_message_list'),
	(r'^Messaging/List/Sent/$', 'views_messaging.tx_message_list'),
	(r'^Messaging/Threading/List/$', 'views_messaging.rx_message_list'),
	(r'^Messaging/Message/(?P<message_id>[a-z0-9]{32})/Delete/$', 'views_messaging.delete_message'),
	(r'^Messaging/Message/(?P<message_id>[a-z0-9]{32})/Update/$', 'views_messaging.update_message'),
	(r'^Messaging/Message/(?P<message_id>[a-z0-9]{32})/$',
											'views_messaging.get_message'),
	(r'^Messaging/Message/(?P<message_id>[a-z0-9]{32})/Attachment/(?P<attachment_id>[a-z0-9]{32})/$',
											'views_messaging.get_attachment'),
	(r'^Messaging/Message/New/$', 'views_messaging.compose_message'),
#	(r'^Messaging/Refer/New/$', 'views_messaging.compose_refer'),
	(r'^Messaging/Refer/PDF/(?P<refer_id>[a-z0-9]{32})/$', 'views_messaging.get_refer_pdf'),
	(r'^Messaging/Refer/(?P<refer_id>[a-z0-9]{32})/Update/$', 'views_messaging.update_refer'),

	(r'^Messaging/Message/SendCheck/$', 'views_messaging.send_message_check'),
	(r'^Messaging/Message/(?P<message_id>[a-z0-9]{32})/ViewDicom/(?P<attachment_id>[a-z0-9]{32})/$',
											'views_messaging_dicom.dicom_view'),
	(r'^Messaging/Message/(?P<message_id>[a-z0-9]{32})/ViewDicomJPG/(?P<attachment_id>[a-z0-9]{32})/(?P<index>\d+)/$',
											'views_messaging_dicom.dicom_view_jpg'),
	# (reserved)
#	(r'^Messaging/Message/(?P<message_id>[a-z0-9]{32})/ViewDicomXML/(?P<attachment_id>[a-z0-9]{32})/$',
#											'views_messaging_dicom.dicom_view_xml'),
	(r'^Messaging/Message/(?P<message_id>[a-z0-9]{32})/CheckDicom/(?P<attachment_id>[a-z0-9]{32})/$',
											'views_messaging_dicom.check_dicom'),
	(r'^Messaging/Message/(?P<message_id>[a-z0-9]{32})/DicomInfo/(?P<attachment_id>[a-z0-9]{32})/$',
											'views_messaging_dicom.dicom_info'),
	(r'^Messaging/Details/$', 'views_messaging.get_message_details'),

	(r'^Page/(?P<user_id>\d+)/$', 'views_dcom.page_user'),
	(r'^Call/User/(?P<user_id>\d+)/$', 'views_dcom.call'),
	(r'^Call/Practice/(?P<practice_id>\d+)/$', 'views_dcom.call'),
	(r'^Call/Arbitrary/$', 'views_dcom.call'),
	(r'^Call/MessageCallback/(?P<message_id>[a-z0-9]{32})/$', 'views_dcom.message_callback'),
	(r'^Call/Incoming/$', 'views_dcom.connect_call'),
	(r'^Followups/List/$', 'views_followups.list_tasks'),
	(r'^Followups/ListSince/$', 'views_followups.delta_task_list'),
	(r'^Followups/New/$', 'views_followups.new_task'),
	(r'^Followups/(?P<task_id>\d+)/Delete/$', 'views_followups.delete_task'),
	(r'^Followups/(?P<task_id>\d+)/Update/$', 'views_followups.update_task'),

	(r'^Invitations/List/$', 'views_invites.list_invites'),
	(r'^Invitations/New/$', 'views_invites.new_invite'),
	(r'^Invitations/(?P<invitation_id>\d+)/Resend/$', 'views_invites.resend_invite'),
	(r'^Invitations/(?P<invitation_id>\d+)/Cancel/$', 'views_invites.cancel_invite'),

	(r'^Validations/SendCode/$', 'views_validates.sendCode'),
	(r'^Validations/Validate/$', 'views_validates.validate'),

	(r'^ServerInfo/$', 'views_server.info'),

	(r'^MyInvitations/$', 'views_my_invitations.getMyInvitations'),
	(r'^MyInvitations/Org/(?P<pending_id>\d+)/Accept/$', 'views_my_invitations.acceptOrgInvitation'),
	(r'^MyInvitations/Org/(?P<pending_id>\d+)/Refuse/$', 'views_my_invitations.refuseOrgInvitation'),
	(r'^MyInvitations/Practice/(?P<pending_id>\d+)/Accept/$', 'views_my_invitations.acceptPracticeInvitation'),
	(r'^MyInvitations/Practice/(?P<pending_id>\d+)/Refuse/$', 'views_my_invitations.refusePracticeInvitation'),
	(r'^Invitations/$', 'views_my_invitations.getInvitations'),
	(r'^Invitations/(?P<pending_id>\d+)/Accept/$', 'views_my_invitations.acceptInvitation'),
	(r'^Invitations/(?P<pending_id>\d+)/Refuse/$', 'views_my_invitations.refuseInvitation'),

	(r'^Org/MyOrgs/$', 'views_orgs.getMyOrgs'),
	(r'^Org/(?P<org_id>-?\d+)/Users/$', 'views_orgs.getOrgUsers'),
	(r'^Tab/GetUserTabs/$', 'views_orgs.getUserTabs'),

	(r'^Call/GetCapabilityToken/$', 'views_dcom.capability_token'),
	(r'^Call/TwiMLCall/$', 'views_dcom.twiMLCall_callback'),

	(r'^MyFavorite/$', 'views_my_favorite.my_favorite'),
	(r'^MyFavorite/Toggle/$', 'views_my_favorite.toggle_favorite'),
)
