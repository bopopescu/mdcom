# -*- coding: utf-8 -*-

try:
	from django.conf.urls import patterns
except ImportError:  # remove when django 1.5 fully integrated
	from django.conf.urls.defaults import patterns

urlpatterns = patterns('MHLogin.api.v1',

	(r'^Hospital/Search/$', 'views_sites.siteSearch'),
	(r'^Hospital/(?P<site_id>\d+)/Profile/$', 'views_sites.siteInfo'),
	(r'^Hospital/(?P<site_id>\d+)/Providers/$', 'views_sites.siteProviders'),
	(r'^Hospital/(?P<site_id>\d+)/Staff/$', 'views_sites.siteStaff'),

	(r'^User_Lists/My_Site/Providers/$', 'views_sites.mySiteProviders'),
	(r'^User_Lists/My_Site/Med_Students/$', 'views_sites.mySiteMedStudents'),
	(r'^User_Lists/My_Site/Staff/$', 'views_sites.mySiteStaff'),

	(r'^Practice/Search/$', 'views_practices.practiceSearch'),
	(r'^Practice/(?P<practice_id>\d+)/Profile/$', 'views_practices.practiceInfo'),
	(r'^Practice/(?P<practice_id>\d+)/Providers/$', 'views_practices.practiceProviders'),
	(r'^Practice/(?P<practice_id>\d+)/Staff/$', 'views_practices.practiceStaff'),
	(r'^Practice/LocalOffice/$', 'views_practices.localOffice'),

	(r'^User_Lists/My_Practice/Providers/$', 'views_practices.myPracticeProviders'),
	(r'^User_Lists/My_Practice/Staff/$', 'views_practices.myPracticeStaff'),

	(r'^User/CreateAccount/Provider/$', 'views_users.createProvider'),
	(r'^User/CreateAccount/OfficeStaff/$', 'views_users.createOfficeStaff'),
	(r'^User/CreateAccount/Broker/$', 'views_users.createBroker'),

	(r'^Providers/Search/$', 'views_users.searchProviders'),
	(r'^Providers/(?P<user_id>\d+)/Profile/$', 'views_users.providerInfo'),
	(r'^Staff/Search/$', 'views_users.searchStaff'),
	(r'^Staff/(?P<user_id>\d+)/Profile/$', 'views_users.staffInfo'),

	(r'^Followups/List/$', 'views_followups.listTasks'),
	(r'^Followups/New/$', 'views_followups.newTask'),
	(r'^Followups/(?P<task_id>\d+)/Delete/$', 'views_followups.deleteTask'),
	(r'^Followups/(?P<task_id>\d+)/Update/$', 'views_followups.updateTask'),

	(r'^Account/Practice/$', 'views_account.practiceManage'),
	(r'^Account/Site/$', 'views_account.siteManage'),
	(r'^Account/CallForwarding/$', 'views_account.callFwdPrefs'),
	(r'^Account/GetDComNumber/$', 'views_account.getDComNumber'),
	(r'^Account/GetMobilePhone/$', 'views_account.getMobilePhone'),
	(r'^Account/UpdateMobilePhone/$', 'views_account.updateMobilePhone'),
	(r'^Account/ChangePassword/$', 'views_account.changePassword'),
	(r'^Account/Profile/$', 'views_account.profile'),

	(r'^SmartPhone/Call/User/(?P<user_id>\d+)/$', 'views_dcom.smartPhoneCall'),
	(r'^SmartPhone/Call/Practice/(?P<practice_id>\d+)/$', 'views_dcom.smartPhoneCall'),
	(r'^SmartPhone/Call/Arbitrary/$', 'views_dcom.smartPhoneCall'),
	(r'^SmartPhone/Call/MessageCallback/(?P<message_id>[a-z0-9]{32})/$', 'views_dcom.smartPhoneMessageCallback'),
#	(r'^SmartPhone/Call/Incoming/$', 'views_dcom.connect_call'),
	(r'^Page/(?P<user_id>\d+)/$', 'views_dcom.pageUser'),

	(r'^Call/User/(?P<called_id>\d+?)/$', 'views_dcom.call'),
	(r'^Call/Practice/(?P<called_practice_id>\d+?)/$', 'views_dcom.call'),
	(r'^Call/Number/$', 'views_dcom.call'),

	(r'^Account/GetMobilePhone/$', 'views_account.getMobilePhone'),
	(r'^Account/UpdateMobilePhone/$', 'views_account.updateMobilePhone'),
	(r'^Account/ChangePassword/$', 'views_account.changePassword'),
	(r'^Account/Profile/$', 'views_account.profile'),

	(r'^Messaging/List/Received/$', 'views_messaging.getReceivedMessages'),
	(r'^Messaging/List/Sent/$', 'views_messaging.getSentMessages'),
	(r'^Messaging/Message/(?P<message_id>[a-z0-9]{32})/$', 'views_messaging.getMessage'),
	(r'^Messaging/Message/(?P<message_id>[a-z0-9]{32})/Delete/$', 'views_messaging.deleteMessage'),
	(r'^Messaging/Message/(?P<message_id>[a-z0-9]{32})/Attachment/(?P<attachment_id>[a-z0-9]{32})/$',
											'views_messaging.getAttachment'),
	(r'^Messaging/Message/New/$', 'views_messaging.composeMessage'),
	(r'^Messaging/Refer/New/$', 'views_messaging.composeRefer'),
	(r'^Messaging/ADS/New/$', 'views_messaging.composeADS'),
	(r'^Messaging/Refer/PDF/(?P<refer_id>[a-z0-9]{32})/$', 'views_messaging.getReferPDF'),
	(r'^Messaging/Refer/(?P<refer_id>[a-z0-9]{32})/Update/$', 'views_messaging.updateRefer'),
	(r'^Messaging/Message/Read/$', 'views_messaging.markMessageRead'),
	(r'^Messaging/Message/Unread/$', 'views_messaging.markMessageUnread'),
	(r'^Messaging/Message/Delete/$', 'views_messaging.deleteMessages'),
)
