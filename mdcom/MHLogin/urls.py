
from django.conf import settings
from django.conf.urls import include, patterns
from django.contrib import admin

# autodiscover and set default root_path
admin.autodiscover()
admin.site.root_path = "/admin/"


urlpatterns = patterns('',
	#Public Facing
	(r'^$', 'MHLogin.MHLogin_Main.views.main'),
	(r'^DicomCalling/$', 'MHLogin.DoctorCom.Messaging.views_dicom.dicom_calling'),

	(r'^login/$', 'MHLogin.MHLogin_Main.views.login_user'),
	(r'^logout/$', 'MHLogin.MHLogin_Main.views.logout_user'),

	(r'^terms/$', 'MHLogin.MHLogin_Main.views.terms'),
	(r'^eula/$', 'MHLogin.MHLogin_Main.views.eula'),
	(r'^TermsAgreement/$', 'MHLogin.MHLogin_Main.views.terms_acceptance'),
	(r'^privacy/$', 'MHLogin.MHLogin_Main.views.privacy'),
	(r'^learn_more/$', 'MHLogin.MHLogin_Main.views.learn_more'),
	(r'^user_agent/$', 'MHLogin.MHLogin_Main.views.user_agent'),
	(r'^toggle_mobile/$', 'MHLogin.MHLogin_Main.views.toggle_mobile'),

	# New user registration
	(r'^signup/', include('MHLogin.MHLSignup.urls')),

	# User self-management
	(r'^Profile/', include('MHLogin.MHLUsers.urls')),
	(r'^ForgotPassword/', include('MHLogin.MHLUsers.forgotpassword.urls')),

	# User self-management - Support
	(r'^Support/FAQs/$', 'MHLogin.MHLogin_Main.views.faqs'),
	(r'^Support/iphoneFAQs/$', 'MHLogin.MHLogin_Main.views.iphoneFAQs'),
	(r'^Support/androidFAQs/$', 'MHLogin.MHLogin_Main.views.androidFAQs'),
	(r'^Support/Contact/$', 'MHLogin.MHLogin_Main.views.contact'),
	(r'^Support/videoTutorial/$', 'MHLogin.MHLogin_Main.views.videoTutorial'),
	(r'^Support/AJAX/Contact/$', 'MHLogin.MHLogin_Main.views.contact_ajax'),
	(r'^Support/ContactConfirm/$', 'MHLogin.MHLogin_Main.views.contact_confirm'),

	(r'^Profile/SecurityQuestions/$', 'MHLogin.MHLUsers.views.security_questions'),
	(r'^Profile/UpdateSecurityQuestions/$', 'MHLogin.MHLUsers.views.update_security_questions'),
	# User self-management - Practices and Sites
	(r'^Profile/Practices/$', 'MHLogin.MHLUsers.views_practices.practicesHome'),
	(r'^Profile/Practices/AJAX/', include('MHLogin.MHLUsers.urls_ajax')),
	(r'^Profile/Sites/$', 'MHLogin.MHLSites.views.manage_sites'),
	(r'^Profile/ChangeCurrentSite/$', 'MHLogin.MHLSites.views.change_current_site'),

	# User Search
	(r'^Search/User/AJAX/', include('MHLogin.MHLUsers.urls_ajax')),
	(r'^Specialty/Get/', 'MHLogin.MHLUsers.views_ajax.getSpecialtyOptions'),

	# DoctorCom
	(r'^Messages/', include('MHLogin.DoctorCom.Messaging.urls')),
	(r'^speech/', include('MHLogin.DoctorCom.speech.urls')),

	(r'^Provider_View/$', 'MHLogin.DoctorCom.views.provider_view'),
	(r'^User_View/$', 'MHLogin.DoctorCom.views.user_view'),
	(r'^Provider_Info/Provider/$', 'MHLogin.DoctorCom.views.provider_info'),
	(r'^Provider_Info/Office_Staff/$', 'MHLogin.DoctorCom.views.office_staff_info'),
	(r'^Provider_Info/Practice/$', 'MHLogin.DoctorCom.views.practice_info'),

	(r'^Call/$', 'MHLogin.DoctorCom.views.click2call_home'),  # redirects to '/'
	# these 3 need merging
	(r'^Call/(?P<called_id>\d+?)/$', 'MHLogin.DoctorCom.views.click2call_initiate'),
	(r'^Call/User/(?P<called_id>\d+?)/$', 'MHLogin.DoctorCom.views.click2call_initiate'),
	(r'^Call/Number/$', 'MHLogin.DoctorCom.views.click2call_initiate'),
	(r'^Call/Practice/$', 'MHLogin.DoctorCom.views.click2call_initiate'),
	# Paging
	(r'^Page/(?P<paged_id>\d+?)/$', 'MHLogin.DoctorCom.views.page_callbackcheck'),
	(r'^Page/(?P<paged_id>\d+?)/Finish/$', 'MHLogin.DoctorCom.views.page_execute'),

	# Number Provision
	(r'^ProvisionNumber/$', 'MHLogin.DoctorCom.NumberProvisioner.views.provisionLocalNumber'),
	(r'^ProvisionNumber/AJAX/LocalNumber/$', 
		'MHLogin.DoctorCom.NumberProvisioner.views.AJAX_provisionLocalNumber'),

	# DoctorCom Number Forwarding
	# These urlconfs ONLY handle inbound connections from Twilio. Use of the
	# MHLogin.utils.decorators.TwilioAuthentication decorator is REQUIRED for all
	# functions intended strictly for connections from Twilio.
	(r'^Twilio/Inbound/$', 'MHLogin.DoctorCom.views.inbound_call'),
	(r'^Twilio/Hangup/$', 'MHLogin.DoctorCom.views.call_hangup'),
	(r'^Twilio/C2C/Verify/$', 'MHLogin.DoctorCom.views.click2call_caller_verify'),
	(r'^Twilio/C2C/CallResp/$', 'MHLogin.DoctorCom.views.click2call_response'),
	(r'^Twilio/C2C/XferResp/$', 'MHLogin.DoctorCom.views.click2xfer_response'),
	(r'^Twilio/C2C/OXferResp/$', 'MHLogin.DoctorCom.views.click2xfer_origin_response'),
	(r'^Twilio/C2C/Cleanup/$', 'MHLogin.DoctorCom.views.click2call_cleanup'),
	(r'^Twilio/SMS/Status/$', 'MHLogin.DoctorCom.SMS.views.twilioSMS_statusResponse'),
	(r'^Twilio/SMS/Incoming/$', 'MHLogin.DoctorCom.SMS.views.twilioSMS_incoming'),
	(r'^IVR/', include('MHLogin.DoctorCom.IVR.urls')),

	# Administrative
	(r'^analytics/', include('MHLogin.analytics.urls')),
	(r'^tests/', include('MHLogin.tests.urls')),

	# Sales
	(r'^Sales/', include('MHLogin.MHLUsers.Sales.urls')),

	(r'^Validations/', include('MHLogin.Validates.urls')),
	# Invitations
	(r'^Invitations/$', 'MHLogin.Invites.views.inviteHome'),
	(r'^Invitations/Check/$', 'MHLogin.Invites.views.invitation_check_by_id'),
	(r'^Invitations/New/$', 'MHLogin.Invites.views.issueInvite'),
	(r'^Invitations/Cancel/(?P<inviteID>\d+)/$', 'MHLogin.Invites.views.cancelInvite'),
	(r'^Invitations/Resend/(?P<inviteID>\d+)/$', 'MHLogin.Invites.views.resendInvite'),
	(r'^Invitations/CheckWithEmail/$', 'MHLogin.Invites.views.invitation_check_with_email'),

	#Followups
	(r'^FollowUps/', include('MHLogin.followup.urls')),

	#Admin
	(r'^dcAdmin/', include('MHLogin.Administration.urls')),  # MHLogin admin
	#(r'^SitesAdmin/$', 'MHLogin.MHLSites.views.site_admin'),
	#(r'^SitesAdmin/Add/$', 'MHLogin.MHLSites.views.site_add'),
	#(r'^SitesAdmin/Edit/(?P<siteID>\d+)/$', 'MHLogin.MHLSites.views.site_edit'),
	#(r'^SitesAdmin/Add/Hospitals/$', 'MHLogin.utils.hosp.hosp_add'),

	# Practice (office) management by office manager
	(r'^Practice/', include('MHLogin.MHLPractices.urls')),

	# Call Groups
	(r'^CallGroup/(?P<callgroup_id>\d+)/', include('MHLogin.MHLCallGroups.urls')),
	# Multi Call Groups
	(r'^Practice/(?P<practice_id>\d+)/CallGroup/(?P<callgroup_id>\d*)/', 
		include('MHLogin.MHLCallGroups.urls_multicallgroup')),
	(r'^CallGroup/AJAX/getPenddings', 'MHLogin.MHLCallGroups.Scheduler.views_multicallgroup.getPenddings'),
	(r'^CallGroup/AJAX/joinCallGroup/(?P<type>(Reject|Accept))/', 
		'MHLogin.MHLCallGroups.Scheduler.views_multicallgroup.joinCallGroup'),

	# Scheduler management
	(r'^Scheduler/', include('MHLogin.MHLCallGroups.Scheduler.urls')),

	(r'^app/', include('MHLogin.apps.urls')),
	# active account
	(r'^Active/$', 'MHLogin.MHLPractices.views.active_account'),
	(r'^getDoctorNumber/$', 'MHLogin.MHLPractices.views.getDoctorNumber'),
	(r'^getDoctorNumberSucess/$', 'MHLogin.MHLPractices.views.getDoctorNumberSucess'),
	(r'^sucessActive/$', 'MHLogin.MHLPractices.views.sucessActive'),

	(r'^EmailExist/$', 'MHLogin.MHLUsers.views_ajax.emailExist'),
	(r'^ValidateEmailAndPhone/$', 'MHLogin.MHLUsers.views_ajax.validate_email_and_phone'),

	#added
	(r'^billing/', include('MHLogin.genbilling.urls')),
	(r'^CheckUserName/(?P<userName>\w+?)/$', 'MHLogin.MHLUsers.views.check_user_name'),

	(r'^changeCurrentPractice/', 'MHLogin.MHLPractices.views_ajax.changeCurrentPractice'),

	(r'^api/', include('MHLogin.api.urls')),

	#add by xlin 121011
	(r'^searchSites/', 'MHLogin.MHLSites.views.searchSites'),
	(r'^searchStates/', 'MHLogin.MHLUsers.views_ajax.searchStates'),

	#Organization
	(r'^Organization/', include('MHLogin.MHLOrganization.urls')),
	#Favorite
	(r'^MyFavorite/', include('MHLogin.MHLFavorite.urls')),

)

if settings.DEBUG:
	urlpatterns += patterns('',
		(r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
	)

