
try:
	from django.conf.urls import patterns, url
except ImportError:  # remove when django 1.5 fully integrated
	from django.conf.urls.defaults import patterns, url


urlpatterns = patterns('MHLogin.DoctorCom.IVR',
	url(r'^Provider/$', 'views_provider.ProviderIVR_Main', name='ProviderIVR_Main'),
	url(r'^Practice/$', 'views_practice.PracticeIVR_Main', name='PracticeIVR_Main'),
	url(r'^ProviderV2/$', 'views_provider_v2.ProviderIVR_Main_New', name='ProviderIVR_Main_New'),
	url(r'^PracticeV2/$', 'views_practice_v2.PracticeIVR_Main_New', name='PracticeIVR_Main_New'),
#	url(r'^TestPractice/$', 'views_test.TestPracticeIVR_Main', name='TestPracticeIVR_Main'),

	# Provider views
	url(r'^Provider/CallForward/$', 'views_provider.ProviderIVR_ForwardCall', name='ProviderIVR_ForwardCall'),
	url(r'^Provider/CallForward/VetAnswer/$', 'views_provider.ProviderIVR_ForwardCall_VetAnswer', name='ProviderIVR_ForwardCall_VetAnswer'),
	url(r'^Provider/LeaveMessage/$', 'views_provider.ProviderIVR_LeaveMsg', name='ProviderIVR_LeaveMsg'),
	url(r'^Provider/Options/$', 'views_provider.ProviderIVR_Options', name='ProviderIVR_Options'),
	url(r'^Provider/Setup/$', 'views_provider.ProviderIVR_Setup', name='ProviderIVR_Setup'),
	url(r'^Provider/TreeRoot/$', 'views_provider.ProviderIVR_TreeRoot', name='ProviderIVR_TreeRoot'),
#	url(r'^Provider/VMStep1/$', 'views_provider.ProviderIVR_VMStep1', name='ProviderIVR_VMStep1'),

	# new V2 provider views
	url(r'^ProviderV2/CallForward/$', 'views_provider_v2.ProviderIVR_ForwardCall_New', name='ProviderIVR_ForwardCall_New'),
	url(r'^ProviderV2/CallForward/Vet/$', 'views_provider_v2.ProviderIVR_ForwardCall_Vet', name='ProviderIVR_ForwardCall_Vet'),
	url(r'^ProviderV2/LeaveMessage/$', 'views_provider_v2.ProviderIVR_LeaveMsg_New', name='ProviderIVR_LeaveMsg_New'),
	url(r'^ProviderV2/LeaveMessage/1/$', 'views_provider_v2.ProviderIVR_LeaveMsg_Action', name='ProviderIVR_LeaveMsg_Action'),
	url(r'^ProviderV2/Options/$', 'views_provider_v2.ProviderIVR_Options_New', name='ProviderIVR_Options_New'),
	url(r'^ProviderV2/Options/1/$', 'views_provider_v2.ProviderIVR_Options_Actions', name='ProviderIVR_Options_Actions'),
	url(r'^ProviderV2/Setup/$', 'views_provider_v2.ProviderIVR_Setup_New', name='ProviderIVR_Setup_New'),
	url(r'^ProviderV2/TreeRoot/$', 'views_provider_v2.ProviderIVR_TreeRoot_New', name='ProviderIVR_TreeRoot_New'),
	url(r'^ProviderV2/TreeRoot/1/$', 'views_provider_v2.ProviderIVR_TreeRoot_Actions', name='ProviderIVR_TreeRoot_Actions'),
	url(r'^ProviderV2/Status/$', 'views_provider_v2.ProviderIVR_Status', name='ProviderIVR_Status'),

	# Practice views
	url(r'^Practice/Setup/$', 'views_practice.PracticeIVR_Setup', name='PracticeIVR_Setup'),
	url(r'^Practice/TreeRoot/$', 'views_practice.PracticeIVR_TreeRoot', name='PracticeIVR_TreeRoot'),
	url(r'^Practice/LeaveMsg/$', 'views_practice.PracticeIVR_LeaveUrgentMsg', name='PracticeIVR_LeaveUrgentMsg'),
	url(r'^Practice/LeaveTextMsg/$', 'views_practice.PracticeIVR_LeaveRegularMsg', name='PracticeIVR_LeaveRegularMsg'),
	url(r'^Practice/Options/$', 'views_practice.PracticeIVR_Options', name='PracticeIVR_Options'),
	url(r'^Practice/CallForward/$', 'views_practice.PracticeIVR_ForwardCall', name='PracticeIVR_ForwardCall'),
	url(r'^Practice/CallForward/VetAnswer/$', 'views_practice.PracticeIVR_ForwardCall_VetAnswer', name='PracticeIVR_ForwardCall_VetAnswer'),

	# new V2 practice views
	url(r'^PracticeV2/Setup/$', 'views_practice_v2.PracticeIVR_Setup_New', name='PracticeIVR_Setup_New'),
	url(r'^PracticeV2/TreeRoot/$', 'views_practice_v2.PracticeIVR_TreeRoot_New', name='PracticeIVR_TreeRoot_New'),
	url(r'^PracticeV2/LeaveMsg/$', 'views_practice_v2.PracticeIVR_LeaveUrgentMsg_New', name='PracticeIVR_LeaveUrgentMsg_New'),
	url(r'^PracticeV2/LeaveTextMsg/$', 'views_practice_v2.PracticeIVR_LeaveRegularMsg_New', name='PracticeIVR_LeaveRegularMsg_New'),
	url(r'^PracticeV2/Options/$', 'views_practice_v2.PracticeIVR_Options_New', name='PracticeIVR_Options_New'),
	url(r'^PracticeV2/Options/1/$', 'views_practice_v2.PracticeIVR_Options_Actions', name='PracticeIVR_Options_Actions'),
	url(r'^PracticeV2/CallForward/$', 'views_practice_v2.PracticeIVR_ForwardCall_New', name='PracticeIVR_ForwardCall_New'),
	url(r'^PracticeV2/CallForward/Vet/$', 'views_practice_v2.PracticeIVR_ForwardCall_Vet', name='PracticeIVR_ForwardCall_Vet'),
	url(r'^PracticeV2/CallerResponse/$', 'views_practice_v2.PracticeIVR_CallerResponse_New', name='PracticeIVR_CallerResponse_New'),
	url(r'^PracticeV2/CallerResponse/1/$', 'views_practice_v2.PracticeIVR_CallerResponse_Action', name='PracticeIVR_CallerResponse_Action'),
	url(r'^PracticeV2/Status/$', 'views_practice_v2.PracticeIVR_Status', name='PracticeIVR_Status'),

	# Generic/Utility views
	url(r'^SignIn/$', 'views_generic.authenticateSession', name='authenticateSession'),
	url(r'^ChangeGreeting/$', 'views_generic.changeGreeting', name='changeGreeting'),
	url(r'^ChangeName/$', 'views_generic.changeName', name='changeName'),
	url(r'^ChangePin/$', 'views_generic.changePin', name='changePin'),
	url(r'^GetRecording/$', 'views_generic.getRecording', name='getRecording'),
	url(r'^GetQuickRecording/$', 'views_generic.getQuickRecording', name='getQuickRecording'),
	url(r'^PlayMessages/$', 'views_generic.playMessages', name='playMessages'),
	url(r'^Unaffiliated/$', 'views_generic.UnaffiliatedNumber', name='unaffiliated'),
	url(r'^GetCallBackNumber/$', 'views_generic.getCallBackNumber', name='getCallBackNumber'),
	url(r'^FetchRecording/(?P<uuid>[0-9a-f]{32})/$', 'views_generic.fetchRecording', name='fetchRecording'),
	#(r'^Test/$', 'views_generic.sessionTest'),

	# generic utility v2 views
	url(r'^SignInV2/$', 'views_generic_v2.authenticateSessionNew', name='authenticateSessionNew'),
	url(r'^ChangeGreetingV2/1/$', 'views_generic_v2.changeGreetingConfirm', name='changeGreetingConfirm'),
	url(r'^ChangeNameV2/1/$', 'views_generic_v2.changeNameConfirm', name='changeNameConfirm'),
	url(r'^ChangePinV2/$', 'views_generic_v2.changePinNew', name='changePinNew'),
	url(r'^ChangePinV2/1/$', 'views_generic_v2.changePinStep1', name='changePinStep1'),
	url(r'^ChangePinV2/2/$', 'views_generic_v2.changePinStep2', name='changePinStep2'),
	url(r'^GetRecordingV2/$', 'views_generic_v2.getRecordingNew', name='getRecordingNew'),
	url(r'^GetRecordingV2/1/$', 'views_generic_v2.getRecordingAction', name='getRecordingAction'),
	url(r'^GetRecordingV2/2/$', 'views_generic_v2.getRecordingConfirm', name='getRecordingConfirm'),
	url(r'^GetQuickRecordingV2/$', 'views_generic_v2.getQuickRecordingNew', name='getQuickRecordingNew'),
	url(r'^GetQuickRecordingV2/1/$', 'views_generic_v2.getQuickRecordingAction', name='getQuickRecordingAction'),
	url(r'^PlayMessagesV2/$', 'views_generic_v2.playMessagesNew', name='playMessagesNew'),
	url(r'^PlayMessagesV2/1/$', 'views_generic_v2.playMessagesAction', name='playMessagesAction'),
	url(r'^GetCallBackNumberV2/$', 'views_generic_v2.getCallBackNumberNew', name='getCallBackNumberNew'),
	url(r'^GetCallBackNumberV2/1/$', 'views_generic_v2.getCallBackNumberAction', name='getCallBackNumberAction'),

)

