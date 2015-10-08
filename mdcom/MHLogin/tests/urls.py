
try:
	from django.conf.urls import patterns
except ImportError:  # remove when django 1.5 fully integrated
	from django.conf.urls.defaults import patterns


urlpatterns = patterns('MHLogin.tests',
	(r'^$', 'views.home'),

	# Twilio Tests
	(r'Twilio/CallGather/', 'views.Twilio_callGather_initiate'),
	(r'TwilioResponse/CallGather/Gather/', 'views.Twilio_callGather'),
	(r'TwilioResponse/CallGather/HangUp/', 'views.Twilio_callGather_complete'),

	(r'Twilio/Record/', 'views.Twilio_record_initiate'),
	(r'TwilioResponse/Record/Complete/', 'views.Twilio_record_complete'),
	(r'TwilioResponse/Record/', 'views.Twilio_record'),

	# Convergent Tests
	#(r'Convergent/', 'views.Twilio_callGather_initiate'),

	# DoctorCom Tests
	(r'DoctorCom/Confirm/', 'views.confirm_test'),
	(r'DoctorCom/Click2Call/', 'views.DCom_C2C_test'),
	(r'DoctorCom/Pager/', 'views.DCom_Page_test'),
	# The below is disabled because it's going to be a pain to implement.
	# (r'DoctorCom/SMS/', 'views.DCom_SMS_test'),
)
