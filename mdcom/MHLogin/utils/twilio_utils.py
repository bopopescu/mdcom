
import re

from django.conf import settings

from twilio.rest import TwilioRestClient
from twilio.util import RequestValidator

# For twilio management, communication, config details, etc.
client = TwilioRestClient(account=settings.TWILIO_ACCOUNT_SID, 
						token=settings.TWILIO_ACCOUNT_TOKEN, version=settings.TWILIO_API_VERSION)
# used for requests that need 2008 api
client2008 = TwilioRestClient(account=settings.TWILIO_ACCOUNT_SID, 
						token=settings.TWILIO_ACCOUNT_TOKEN, version=settings.TWILIO_API_2008)

# For twilio validation
validator = RequestValidator(settings.TWILIO_ACCOUNT_TOKEN)

# Sanity check the sid (in json now, no more xml)
validate_sid = lambda sid: True if re.match('CA[0-9a-f]{32}', sid) else False

# Put these in twilio_h.py
TWILIO_ACCT_NOT_ACTIVE = 10001  # Account is not active
TWILIO_NOT_SUPPORTED_IN_TRIAL = 10002  # Trial account does not support this feature
TWILIO_INC_CALL_REJ_INACTIV_ACCT = 10003  # Incoming call rejected due to inactive account
TWILIO_IVALID_URL_FORMATTRIAL = 11100  # Invalid URL format
TWILIO_HTTP_RETRIEVAL_FAILURE = 11200  # HTTP retrieval failure
TWILIO_HTTP_CONNECTION_FAILURE = 11205  # HTTP connection failure
TWILIO_HTTP_PROTOCOL_VIOLATION = 11206  # HTTP protocol violation
TWILIO_HTTP_BAD_HOST_NAME = 11210  # HTTP bad host name
TWILIO_HTTP_TOO_MANY_REDIRECTS = 11215  # HTTP too many redirects
TWILIO_INVALID_TEMPLATE_URL = 11300  # Invalid template URL
TWILIO_INVALID_TEMPLATE_TOKEN = 11310  # Invalid template token
TWILIO_INVALID_TEMPLATE_UNCLOSED_BRACKETS = 11320  # Invalid template unclosed brackets
TWILIO_DOCUMENT_PARSE_FAILURE = 12100  # Document parse failure
TWILIO_INVALID_MARKUP_XM = 12101  # Invalid Twilio Markup XML version
TWILIO_ROOT_ELEMENT_NOT_RESPONSE = 12102  # The root element must be Response
TWILIO_SCHEMA_VALIDATION_WARNING = 12200  # Schema validation warning
TWILIO_INVALID_CONTENT_TYPEAL = 12300  # Invalid Content-Type
TWILIO_INTERNAL_FAILURE_TRIAL = 12400  # Internal Failure
TWILIO_DIAL_OUT_FROM_CALL_SEG = 13201  # Dial  # Cannot Dial out from a Dial Call Segment
TWILIO_DIAL_INVALI_METHOD_VALUE = 13210  # Dial  # Invalid method value
TWILIO_DIAL_INVALID_IF_MACHINE_VALUE = 13211  # Dial  # Invalid ifMachine value
TWILIO_DIAL_INVALID_TIMEOUT_VALUE = 13212  # Dial  # Invalid timeout value
TWILIO_DIAL_INVALID_HANGUP_ON_STAR = 13213  # Dial  # Invalid hangupOnStar value
TWILIO_DIAL_INVALID_CALL_ID_VALUEX = 13214  # Dial  # Invalid callerId value
TWILIO_DIAL_INVALID_NESTED_SEGMENT = 13215  # Dial  # Invalid nested element
TWILIO_DIAL_INVALID_TIMELIMIT_VALUE = 13216  # Dial  # Invalid timeLimit value
TWILIO_DIAL_INVALID_RECORD_VALUE = 13217  # Dial  # Invalid record value
TWILIO_DIAL_INVALID_METHOD_VALUE = 13221  # Dial->Number  # Invalid method value
TWILIO_DIAL_INVALID_SEND_DIGITS = 13222  # Dial->Number  # Invalid sendDigits value
TWILIO_DIAL_INVALID_PHONE_FORMAT = 13223  # Dial  # Invalid phone number format
TWILIO_DIAL_INVALID_PHONE_NUMBER = 13224  # Dial  # Invalid phone number
TWILIO_DIAL_FORBIDDEN_PHONE_NUMBER = 13225  # Dial  # Forbidden phone number
TWILIO_DIAL_INVALID_COUNTRY_CODE = 13226  # Dial  # Invalid country code
TWILIO_DIAL_NO_INTERNATIONAL_AUTH = 13227  # Dial  # No International Authorization
TWILIO_DIAL_CONF_INVALID_MUTE_VALUE = 13230  # Dial->Conference  # Invalid muted value
TWILIO_DIAL_CONF_INVALID_ENDL = 13231  # Dial->Conference  # Invalid endConferenceOnExit value
TWILIO_DIAL_CONF_INVALID_START = 13232  # Dial->Conference  # Invalid startConferenceOnEnter value
TWILIO_DIAL_CONF_INVALID_WAIT_URLL = 13233  # Dial->Conference  # Invalid waitUrl value
TWILIO_DIAL_CONF_INVALID_WAIT_METHOD = 13234  # Dial->Conference  # Invalid waitMethod value
TWILIO_DIAL_CONF_INVALID_BEEP_VALUE = 13235  # Dial->Conference  # Invalid beep value
TWILIO_DIAL_CONF_INVALID_CONF_SID = 13236  # Dial->Conference  # Invalid Conference Sid value
TWILIO_DIAL_CONF_INVALID_NAME = 13237  # Dial->Conference  # Invalid conference name
TWILIO_DIAL_CONF_INVALID_VERB_WAIT = 13238  # Dial->Conference  # Invalid verb for waitUrl TwiML
TWILIO_DIAL_SIP_INVALID_METHOD = 13241  # Dial->SIP  # Invalid method value
TWILIO_DIAL_SIP_INVALID_SENDDIGITS = 13242  # Dial->SIP  # Invalid sendDigits value
TWILIO_DIAL_SIP_INVALID_URI = 13243  # Dial->SIP  # Invalid SIP URI
TWILIO_DIAL_NO_SIP_AUTHORIZATION = 13244  # Dial  # No SIP Authorization
TWILIO_GATHER_INVALID_FINISH = 13310  # Gather  # Invalid finishOnKey value
TWILIO_GATHER_INVALID_FINISH2 = 13311  # Gather  # Invalid finishOnKey value
TWILIO_GATHER_SUPPORTED_IN_TRIAL = 13312  # Gather  # Invalid method value
TWILIO_GATHER_INVALID_TIMEOUT = 13313  # Gather  # Invalid timeout value
TWILIO_GATHER_INVALID_NUMDIGITS = 13314  # Gather  # Invalid numDigits value
TWILIO_GATHER_INVALID_NESTED_VERB = 13320  # Gather  # Invalid nested verb
TWILIO_GATHER_SAY_INVALID_VOICE = 13321  # Gather->Say  # Invalid voice value
TWILIO_GATHER_SAY_INVALID_LOOP = 13322  # Gather->Say  # Invalid loop value
TWILIO_GATHER_PLAY_INVALID_CONTENT = 13325  # Gather->Play  # Invalid Content-Type
TWILIO_PLAY_INVALID_LOOPTRIAL = 13410  # Play  # Invalid loop value
TWILIO_PLAY_INVALID_CONTENT_TYPE = 13420  # Play  # Invalid Content-Type
TWILIO_SAY_INVALID_LOOP_TRIAL = 13510  # Say  # Invalid loop value
TWILIO_SAY_INVALID_VOICETRIAL = 13511  # Say  # Invalid voice value
TWILIO_SAY_INVALID_TEXT_TRIAL = 13520  # Say  # Invalid text
TWILIO_RECORD_INVALID_METHODL = 13610  # Record  # Invalid method value
TWILIO_RECORD_INVALID_TIMEOUT = 13611  # Record  # Invalid timeout value
TWILIO_RECORD_INVALID_MAX_LENGTH = 13612  # Record  # Invalid maxLength value
TWILIO_RECORD_INVALID_FINSIHL = 13613  # Record  # Invalid finishOnKey value
TWILIO_RECORD_INVALID_TRANSCRIBE = 13614  # Record  # Invalid transcribe value
TWILIO_RECORD_MAXLEN_TOO_HIGH = 13615  # Record  # maxLength too high for transcription
TWILIO_RECORD_PLAYBEEP_NOT_BOOLEAN = 13616  # Record  # playBeep must be true or false
TWILIO_REDIRECT_INVALID_METHOD = 13710  # Redirect  # Invalid method value
TWILIO_PAUSE_INVALID_LENGTHAL = 13910  # Pause  # Invalid length value
TWILIO_TO_ATTRIBUTE_INVALIDAL = 14101  # "To" Attribute is Invalid
TWILIO_SMS_FROM_INVALID_TRIAL = 14102  # SMS "From" Attribute is Invalid
TWILIO_SMS_INVALID_BODY_TRIAL = 14103  # SMS Invalid Body
TWILIO_SMS_METHOD_ATTRIBUTE_INVALID = 14104  # SMS method attribute invalid
TWILIO_SMS_VERB_ATTRIBUTE_INVALID = 14105  # Sms Verb statusCallback attribute Invalid
TWILIO_SMS_REPLY_DOC_LIMIT_REACHED = 14106  # SMS Reply TwiML document retrieval limit reached
TWILIO_SMS_RATE_MESSAGE_LIMIT_REACHED = 14107  # SMS Rate message limit exceeded
TWILIO_SMS_FROM_PHONE_SMS_NOT_SUPPORTED = 14108  # SMS "From" Phone Number not SMS capable
TWILIO_SMS_REPLY_MESSAGE_LIMIT_REACHED = 14109  # SMS Reply message limit exceeded
TWILIO_INVALID_VERB_FOR_SMS_REPLY = 14110  # Invalid Verb for SMS Reply
TWILIO_INVALID_TO_PHONE_FOR_TRIAL = 14111  # Invalid To phone number for Trial mode
TWILIO_UNKNOWN_PARAMETERS = 20001  # Unknown parameters
TWILIO_INVALID_FRIENDLY_NAME = 20002  # Invalid FriendlyName
TWILIO_PERMISSION_DENIED = 20003  # Permission Denied
TWILIO_METHOD_NOT_ALLOWED = 20004  # Method not allowed
TWILIO_ACCOUNT_NOT_ACTIVE = 20005  # Account not active
TWILIO_ACCESS_DENIED = 20006  # Access Denied
TWILIO_ACCOUNTS_RESOURCE = 21100  # Accounts Resource
TWILIO_CALLS_RESOURCEIN_TRIAL = 21200  # Calls Resource
TWILIO_NO_TO_NUMBER_SPECIFIED = 21201  # No 'To' number specified
TWILIO_TO_NUMBER_IS_PREMIUM = 21202  # 'To' number is a premium number
TWILIO_INTERNATIONAL_CALLING_DISABLED = 21203  # International calling not enabled
TWILIO_CALL_ALREADY_INITIATED = 21204  # Call already initiated
TWILIO_INVALID_URL = 21205  # Invalid URL
TWILIO_INVALID_SEND_DIGITS = 21206  # Invalid SendDigits
TWILIO_INVALID_IF_MACHINE = 21207  # Invalid IfMachine
TWILIO_INVALID_TIMEOUTN = 21208  # Invalid Timeout
TWILIO_INVALID_METHOD = 21209  # Invalid Method
TWILIO_FROM_PHONE_NOT_VERIFIED = 21210  # 'From' phone number not verified
TWILIO_INVALID_TO_PHONE_NUMBER = 21211  # Invalid 'To' Phone Number
TWILIO_INVALID_FROM_PHONE_NUMBER = 21212  # Invalid 'From' Phone Number
TWILIO_FROM_PHONE_REQUIREDIAL = 21213  # 'From' phone number is required
TWILIO_TO_PHONE_UNREACHABLE = 21214  # 'To' phone number cannot be reached
TWILIO_ACCT_NOT_AUTH_TO_CALL_NUMBER = 21215  # Account not authorized to call phone number
TWILIO_ACCT_NOT_ALLOWED_TO_CALL_NUMBER = 21216  # Account not allowed to call phone number
TWILIO_PHONE_NUMBER_INVALID = 21217  # Phone number does not appear to be valid
TWILIO_INVALID_APP_SID = 21218  # Invalid ApplicationSid
TWILIO_TO_PHONE_NUMBER_NOT_VERIFIED = 21219  # 'To' phone number not verified
TWILIO_INVALID_CALL_STATE = 21220  # Invalid call state
TWILIO_INVALID_PHONE_NUMBER = 21401  # Invalid Phone Number
TWILIO_INVALID_URL2 = 21402  # Invalid URL
TWILIO_INVALID_METHOD2 = 21403  # Invalid Method
TWILIO_INBOUND_PHONE_NUMS_UNAVAIL_TO_TRIAL = 21404  # Inbound phone numbers not available to trial accounts
TWILIO_CANNOT_SET_VOICEFALLBACK_URL = 21405  # Cannot set VoiceFallbackUrl without setting Url
TWILIO_CANNOT_SET_SMS_FALLBACKXXXXX = 21406  # Cannot set SmsFallbackUrl without setting SmsUrl
TWILIO_PHONE_NUMBER_TYPE_HAS_NO_SMS = 21407  # This Phone Number type does not support SMS
TWILIO_SMS_SEND_PERMISSION_DISABLED = 21408  # Permission to send an SMS has not been enabled for the region indicated by the 'To' number
TWILIO_APPLICATION_SID_UNACCESSABLE = 21420  # ApplicationSid is not accessible
TWILIO_PHONE_NUMBER_INVALID = 21421  # PhoneNumber is invalid
TWILIO_PHONE_NUMBER_NOT_AVAILABLE_FOR_PURCHASE = 21422  # PhoneNumber is not available for purchase
TWILIO_PHONE_ALREADY_VERIFIED = 21450  # Phone number already verified for your account
TWILIO_INVALID_AREA_CODE = 21451  # Invalid area code
TWILIO_NO_PHONE_NUMBERS_IN_AREA_CODE = 21452  # No phone numbers found in area code
TWILIO_PHONE_NUMBER_ALREADY_VERIFIED = 21453  # Phone number already verified for another account
TWILIO_INVALID_CALL_DELAY = 21454  # Invalid CallDelay
TWILIO_INVALID_PLAY_URL = 21455  # Invalid PlayUrl
TWILIO_INVALID_CALLBACK_URL = 21456  # Invalid CallbackUrl
TWILIO_AREACODE_PARAMETER_NOT_SUPPORTED = 21457  # AreaCode Parameter not Supported
TWILIO_PHONE_PROVISIONING_MISMATCH = 21458  # PhoneNumber Provisioning Type Mismatch
TWILIO_INVALID_ACCOUNT_SID = 21470  # Invalid AccountSid
TWILIO_ACCOUNT_DOES_NOT_EXIST = 21471  # Account does not exist
TWILIO_ACCOUNT_NOT_ACTIVE = 21472  # Account is not active
TWILIO_ACCOUNT_SID_NOT_RELATED = 21473  # AccountSid you are transferring to is not related to the originating owner of the phone number
TWILIO_MUST_BE_PARENT_TO_TRANSFER = 21474  # API User must be the parent account to transfer phone numbers.
TWILIO_UNABLE_TO_UPDATE_STATUS_INVALID = 21475  # Unable to update Status, invalid Status.
TWILIO_UNABLE_TO_UPDATE_STATUS_FOR_SUB_ACCT = 21476  # Unable to update Status for subaccount, parent account is suspended.
TWILIO_UNABLE_TO_UPDATE_STATUS_FOR_PARENT_ACT = 21477  # Unable to update Status for parent accounts
TWILIO_UNABLE_TO_UPDATE_STATUS_FOR_SUB_ACCT2 = 21478  # Unable to update Status for subaccount, subaccount has been suspended by Twilio
TWILIO_UNABLE_TO_UPDATE_STATUS_FOR_SUB_ACCT3 = 21479  # Unable to update Status for subaccount, subaccount has been closed.
TWILIO_MAX_SUB_ACCTS_REACHED = 21480  # Reached maximum number of subaccounts
TWILIO_RESOURCE_NOT_AVAILABLE = 21501  # Resource not available
TWILIO_INVALID_CALLBACK_URL = 21502  # Invalid callback url
TWILIO_INVALID_TRANSACTION_TYPE = 21503  # Invalid transcription type
TWILIO_RECORDING_SID_REQUIRED = 21504  # RecordingSid is required.
TWILIO_INVALID_SMS_INBOUND_NUMBER = 21601  # Phone number is not a valid SMS-capable inbound phone number
TWILIO_SMS_MESSAGE_BODY_REQUIRED = 21602  # Message 'Body' is required to send an SMS
TWILIO_SMS_PHONE_NUMBER_REQUIRED = 21603  # 'From' phone number is required to send an SMS
TWILIO_SMS_TO_PHONE_REQUIRED = 21604  # 'To' phone number is required to send an SMS
TWILIO_SMS_MAX_BODY_REACHED = 21605  # Maximum body length is 160 characters
TWILIO_SMS_FROM_NUMBER_INVALID = 21606  # The 'From' phone number provided is not a valid, SMS-capable Twilio phone number.
TWILIO_SANDBOX_TRIAL_FROM_MUST_BE_IN_SANDBOX = 21607  # The 'From' number must be the Sandbox phone number for trial accounts
TWILIO_SANDBOX_CAN_ONLY_SEND_TO_VERIFIED = 21608  # The Sandbox number can send SMS messages only to verified numbers
TWILIO_INVALID_STATUS_CALLBACK_URL = 21609  # Invalid StatusCallback url
TWILIO_SMS_CANT_BE_SENT_NO_STOP = 21610  # SMS cannot be sent to the 'To' number because the customer has replied with STOP
TWILIO_FROM_NUMBER_MAX_MSG_QUEUE_REACHED = 21611  # This 'From' number has exceeded the maximum number of queued messages
TWILIO_SMS_TO_PHONE_UNREACHABLE = 21612  # The 'To' phone number is not currently reachable via SMS
TWILIO_PHONE_REQUIRES_CERTIFICATION = 21613  # PhoneNumber Requires Certification
TWILIO_NOT_A_VALID_MOBILE_NUMBER = 21614  # 'To' number is not a valid mobile number
TWILIO_FROM_NUMBER_MATCHES_MULTIPLE = 21616  # The 'From' number matches multiple numbers for your account
TWILIO_MESSAGE_BODY_CANT_BE_SENT = 21618  # The message body cannot be sent

