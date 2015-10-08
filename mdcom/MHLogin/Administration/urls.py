
from django.conf.urls import include, patterns

urlpatterns = patterns('MHLogin.Administration',
	(r'^$', 'views.home'),

	#(r'^Physician/New/$', 'views.newPhysicianPage'),
	#(r'^Provider/New/$', 'views.newProviderPage'),

	(r'^Invitations/$', 'views.inviteHome'),
	(r'^Invitations/New/$', 'views.issueInvite'),
	(r'^Invitations/Cancel/(?P<inviteID>\d+)/$', 'views.cancelInvite'),
	(r'^Invitations/GetAssignPractice/$', 'views.getAssignPractice'),

	(r'^KMS/NewUsersKeyGen/$', 'views.generate_user_keys'),
	#(r'^KMS/$', ''),

	(r'^UserPasswordReset/$', 'views.get_user_for_reset'),
	(r'^UserPasswordReset/(?P<user_pk>\d+)/$', 'views.reset_user_password'),

	(r'^ResetPrivateKeys/$', 'views.reset_private_keys'),

	(r'^ResolveAnsSvcDLFailures/$', 'views.resolve_anssvc_dl_failures'),

	(r'^Sanitation/$', 'data_sanitation.views.cleanDB'),
	(r'^AdminMessage/(?P<userID>\d+)/$', 'views.admin_message_edit'),
	(r'^EmailToAll/$', 'views.send_email_to_all_users'),

	(r'^Brokers/$', 'views_broker.broker_page'),
	(r'^BrokerTracking/$', 'views_broker.broker_tracking'),
	(r'^BrokerStatus/$', 'views_broker.broker_update_active'),
	(r'^Broker/Invitations/Cancel/(?P<inviteID>\d+)/$', 'views_broker.update_broker_invite', 
		{'isCancel': 'True'}),
	(r'^Broker/Invitations/Resend/(?P<inviteID>\d+)/$', 'views_broker.update_broker_invite'),
	(r'^BrokerTracking/Ajax/call/$', 'views_broker.broker_tracking_ajax_call'),
	(r'^BrokerTracking/Ajax/message/$', 'views_broker.broker_tracking_ajax_message'),
	(r'^ReferTracking/$', 'views_broker.refer_tracking'),
	(r'^ReferTracking/Ajax/$', 'views_broker.refer_tracking_ajax'),
	(r'^ReferTrackingDetail/(?P<userID>\d+)$', 'views_broker.refer_tracking_detail'),
	(r'^ReferTrackingDetail/Ajax/(?P<userID>\d+)$', 'views_broker.refer_tracking_detail_ajax'),
	(r'^tech_admin/', include('MHLogin.Administration.tech_admin.urls', namespace='admin')),

	(r'^QATools/$', 'views_qa.qa_tools'),
	(r'^QATools/GenerateUsers/$', 'views_qa.generate_users'),
	(r'^QATools/GeneratePhotos/$', 'views_qa.generate_photos'),
	(r'^QATools/ReGenerateKey/$', 'views_qa.re_generate_key'),
)

urlpatterns += patterns('MHLogin.Administration',
	(r'^OrganizationTypeList/$', 'views_org_type.org_type_list'),
	(r'^OrganizationType/Create/$', 'views_org_type.org_type_create'),
	(r'^OrganizationType/Edit/(?P<org_type_id>[-]?\d+)/$', 'views_org_type.org_type_edit'),
	(r'^OrganizationType/Del/(?P<org_type_id>[-]?\d+)/$', 'views_org_type.org_type_del'),
	(r'^OrganizationType/CheckRemoveSubType/$', 'views_org_type.check_remove_sub_type'),
)
