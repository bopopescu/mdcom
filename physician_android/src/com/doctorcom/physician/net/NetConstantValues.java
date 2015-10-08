package com.doctorcom.physician.net;

import java.net.URLEncoder;

public class NetConstantValues {
	/**
	 * 
	 */
	public static final String APP_URL = "/app/smartphone/v1";
	public static String DOCTORCOM_SITES_ADDRESSES[][] = {
			{ "https://client.mdcom.com" , "https://de.mdcom.com", "https://dev-maint.mdcom.com", "" },
			{ "https://client.mdcom.com", "https://de.mdcom.com" } };

	public final static class DEVICE_CHECK_IN {
		public final static String PATH = "/Device/Check_In/";
		public final static String PARAM_KEY = "key";// optional
		public final static String PARAM_RX_TIMESTAMP = "rx_timestamp";// optional
		public final static String PARAM_TX_TIMESTAMP = "tx_timestamp";// optional
	}

	/**
	 * This establishes an association between a user and the device. Path:
	 * /Device/Associate/
	 **/
	public final static class DEVICE_ASSOCIATE {
		public final static String PATH = "/Device/Associate/";
		public final static String PARAM_USERNAME = "username";
		public final static String PARAM_PASSWORD = "password";
		public final static String PARAM_DEVICE_ID = "device_id";
		public final static String PARAM_NAME = "name";
		public final static String PARAM_APP_VERSION = "app_version";
		public final static String PARAM_PLATFORM = "platform";
		public final static String PARAM_ALLOW_STAFF_LOGIN = "allow_staff_login";
	}
	
	/**
	 * Dissociates the device from the DoctorCom system Path:
	 * /Device/Dissociate/
	 */
	public final static class DEVICE_DISSOCIATE {
		public final static String PATH = "/Device/Dissociate/";
	}
	
	/**
	 * Gets the user's mobile number
	 * And Calling Path: /Account/GetMobilePhone/
	 */
	public final static class PHONE_NUMBER {
		public final static String PATH = "/Account/GetMobilePhone/";
		public final static String UPDATE_PATH = "/Account/UpdateMobilePhone/";
		public final static String MOBILE_PHONE = "mobile_phone";
	}
	
	public final static class VALIDATIONS {
		public final static String PATH = "/Validations/SendCode/";
		public final static String VALIDATIONS_PATH = "/Validations/Validate/";
		public final static String RECIPIENT = "recipient";
		public final static String TYPE = "type";
		public final static String INIT = "init";
		public final static String CODE = "code"; 
	}
	/**
	 * Ask for Arbitrary Number and Calling Path: /Call/Arbitrary/
	 */
	public final static class CALL_ARBITRARY {
		public final static String PATH = "/Call/Arbitrary/";
		public final static String PARAM_NUMBER = "number";
		public final static String PARAM_CALLER_NUMBER = "caller_number";
	}
	/**
	 * Ask for User Number and calling Path: /Call/User/<user_id>/
	 */
	public final static class CALL_USER {
		private final static String PATH = "/Call/User/";
		public final static String PARAM_CALLER_NUMBER = "caller_number";
		public final static String getPath(String userId) {
			return PATH + URLEncoder.encode(userId) + "/";
		}
	}
	/**
	 * Ask for Practice Number and calling Path: /Call/Practice/<practice_id>/
	 */
	public final static class CALL_PRACTICE {
		private final static String PATH = "/Call/Practice/";
		public final static String PARAM_CALLER_NUMBER = "caller_number";
		public final static String getPath(String Id) {
			return PATH + URLEncoder.encode(Id) + "/";
		}
	}
	/**
	 * Paging user and Calling Path: /Page/<user_id>/
	 */
	public final static class PAGE_USER {
		public final static String PATH = "/Page/";
		public final static String PARAM_NUMBER = "number";

		public final static String getPath(String userId) {
			return PATH + URLEncoder.encode(userId) + "/";
		}
	}

	/**
	 * Gets summary/listing information for all received messages in the
	 * requested time frame. If from time frame is given, this will return the
	 * 20 (or count) most recent messages. Path: /Messaging/List/Received/
	 * 
	 */
	public final static class MESSAGING_LIST_RECEIVED {
		public final static String PATH = "/Messaging/List/Received/";
		public final static String PARAM_FROM = "from_timestamp";
		public final static String PARAM_TO = "to_timestamp";
		public final static String PARAM_COUNT = "count";
		public final static String PARAM_RESOLVED = "resolved";
		public final static String PARAM_EXCLUDE_ID = "exclude_id";
	}
	/**
	 * Gets summary/listing information for all received messages in the
	 * requested time frame. If from time frame is given, this will return the
	 * 20 (or count) most recent messages. Path: /Messaging/List/Sent/
	 */
	public final static class MESSAGING_LIST_SENT {
		public final static String PATH = "/Messaging/List/Sent/";
		public final static String PARAM_FROM = "from_timestamp";
		public final static String PARAM_TO = "to_timestamp";
		public final static String PARAM_COUNT = "count";
		public final static String PARAM_RESOLVED = "resolved";		
		public final static String PARAM_EXCLUDE_ID = "exclude_id";
	}
	
	public final static class THREADING {
		public final static String PATH = "/Messaging/Threading/List/";
		public final static String PARAM_IS_THREADING = "is_threading";
		public final static String PARAM_THREADING_UUID = "thread_uuid";
	}
	
	public final static class THREADING_BODY{
		public final static String PATH = "/Messaging/Threading/Body/";
		public final static String IDS = "ids";
	}
	
	public final static class RECEIVED_LIST_BODY{
		public final static String PATH = "/Messaging/Body/Received/";
		public final static String IDS = "ids";
	}
	
	public final static class SENT_LIST_BODY{
		public final static String PATH = "/Messaging/Body/Sent/";
		public final static String IDS = "ids";
	}
	/**
	 * Gets the message body. Path: /Messaging/Message/<message_id>/
	 * 
	 */
	public final static class MESSAGING_MESSAGE_BODY {
		public final static String PATH = "/Messaging/Message/";
		public final static String PARAM_SECRET = "secret";
		public final static String getPath(String messageId) {
			return PATH + URLEncoder.encode(messageId) + "/";
		}
	}
	
	public final static class MESSAGE_STATUS_UPDATE {
		public final static String PATH = "/Messaging/Message/";
		public final static String PARAM_RESOLVED = "resolved";
		public final static String getPath(String messageId) {
			return PATH + URLEncoder.encode(messageId) + "/Update/";
		}
	}
	
	/**
	 * Gets a message attachment. Path:
	 * /Messaging/Message/<message_id>/Attachment/<attachment_id>/
	 */
	public final static class MESSAGING_MESSAGE_ATTACHMENT {
		private final static String PATH = "/Messaging/Message/";
		public final static String PARAM_SECRET = "secret";

		public final static String getPath(String messageId, String attachmentId) {
			return PATH + URLEncoder.encode(messageId) + "/Attachment/"
					+ URLEncoder.encode(attachmentId) + "/";
		}
	}

	public final static class MESSAGE_REFER {
		public final static String PATH = "/Messaging/Refer/";
		public final static String STATUS = "status";
		public final static String REFUSE_REASON = "refuse_reason";
		public final static String PARAM_SECRET = "secret";
		public final static String getPath(String referId) {
			return PATH + URLEncoder.encode(referId) + "/Update/";
		}
		public final static String getPDFPath(String id) {
			return PATH + "PDF/" + URLEncoder.encode(id) + "/";
		}
	}

	public final static class MESSAGE_DELETE{
		private final static String PATH = "/Messaging/Message/";
		public final static String PARAM_SECRET = "secret";
		public final static String getPath(String messageId) {
			return PATH + URLEncoder.encode(messageId) + "/Delete/";
		}
	}
	
	/**
	 * Allows users to send a message to another user or outside phone number.
	 * Path: /Messaging/Message/New/
	 */
	public final static class MESSAGING_MESSAGE_NEW {
		public final static String PATH = "/Messaging/Message/New/";
		public final static String PARAM_RECIPIENTS = "recipients";
		public final static String PARAM_CCS = "ccs";// (optional)
		public final static String PARAM_PRACTICE_RECIPIENTS = "practice_recipients";
		public final static String PARAM_ATTACHMENT = "attachment";// (optional)
		public final static String PARAM_SUBJECT = "subject";
		public final static String PARAM_BODY = "body";
		public final static String PARAM_SECRET = "secret";// (optional)
		public final static String PARAM_MESSAGE_ID = "message_id";// (optional)
		public final static String PARAM_ATTACHMENT_IDS = "attachment_ids";// (optional)
		public final static String PARAM_REFER_ID = "refer_id";// (optional)
		public final static String PARAM_THREAD_UUID = "thread_uuid";// (optional)
	}

	public final static class MESSAGEING_MESSAGE_SENDCHECK {
		public final static String PATH = "/Messaging/Message/SendCheck/";
		public final static String PARAM_RECIPIENTS = "recipients";
		public final static String PARAM_CCS = "ccs";// (optional)
		public final static String PARAM_PRACTICE_RECIPIENTS = "practice_recipients";
		public final static String PARAM_ATTACHMENT_COUNT = "attachment_count";
	}
	
	/**
	 * Returns profile of selected user geographic radius of the user's office
	 * address. Path: /User/<user_id>/Profile/
	 */
	public final static class USER_PROFILE {
		private final static String PATH = "/User/";
		public final static String getPath(String userId) {
			return PATH + URLEncoder.encode(userId) + "/Profile/";
		}
	}
	
	public final static class USER_STATUS_UPDATE {
		public final static String PATH = "/MyFavorite/Toggle/";
		public final static String PARAM_OBJECT_TYPE_FLAG = "object_type_flag";	
		public final static String PARAM_OBJECT_ID = "object_id";
		public final static String PARAM_IS_FAVOURITE = "is_favorite";
	}

	/**
	 * 
	 */
	public final static class PRACTICE_PROFILE {
		public final static String PATH = "/Practice/";
		public final static String getPath(String Id) {
			return PATH + URLEncoder.encode(Id) + "/Profile/";
		}
	}
	
	/**
	 * Get UserDirectroy by searching name and Calling Path: /Search/User/
	 */
	public final static class SEARCH_USER {
		public final static String PATH = "/User/Search/";
		public final static String PARAM_NAME = "name";
		public final static String PARAM_LIMIT = "limit";
	}

	/**
	 * Gets a listing of all follow-up tasks within the requested time frame. 
	 * If the from argument is omitted, the most recent 20 (or count) tasks will be returned.
	 * Path: /Followups/List/
	 **/
	
	public final static class FOLLOWUPS_LIST{
		public final static String PATH = "/Followups/List/";
		public final static String PARAM_FROM  = "from_timestamp";//A UNIX timestamp for the oldest task to fetch, based on due timestamp.
		public final static String PARAM_TO    = "to_timestamp";
		public final static String PARAM_COUNT = "count";//default 20
		public final static String PARAM_COMPLETED = "completed";//default 20
		public final static String PARAM_DUE_FROM_TIMESTAP = "due_from_timestamp";
		public final static String PARAM_DUE_TO_TIMESTAMP = "due_to_timestamp";
		public final static String PARAM_CREATION_FROM_TIMESTAM = "creation_from_timestamp";
		public final static String PARAM_CREATION_TO_TIMESTAMP = "creation_to_timestamp";
		public final static String PARAM_EXCLUDE_ID = "exclude_id";
		public final static String PARAM_DONE_FROM = "done_from";
	}
	
	/**
	 * Creates a new follow-up task item.
	 * Path: /Followups/New/
	 */
	public final static class FOLLOWUPS_NEW{
		public final static String PATH = "/Followups/New/";
		public final static String PARAM_DUE = "due";//A UNIX timestamp for the due date for this task
		public final static String PARAM_PRIORITY = "priority";//An integer indicating the desired priority of the task.
		public final static String PARAM_DESCRIPTION = "description";//(limit 200) The string that should be displayed for this task. Limited to 200 characters at the moment.
		public final static String PARAM_NOTE = "note";//A longer description, functionally, for the follow-up task. This is a longer field for more detailed information
	}
	/**
	 * Creates a new follow-up task item.
	 * Path: /Followups/<task_id>/Update/
	 */
	public final static class FOLLOWUPS_UPDATE{
		private final static String PATH  ="/Followups/";
		public final static String getPath(String taskId) {
			return PATH + URLEncoder.encode(taskId) + "/Update/";
		}
		public final static String PARAM_DUE = "due"; //A UNIX timestamp for the due date for this task
		public final static String PARAM_PRIORITY = "priority"; //An integer indicating the desired priority of the task.
		public final static String PARAM_DESCRIPTION = "description"; //(limit 200) The string that should be displayed for this task. Limited to 200 characters at the moment.
		public final static String PARAM_NOTE = "note"; //A longer description, functionally, for the follow-up task. This is a longer field for more detailed information
		public final static String PARAM_DONE = "completed"; //A boolean value indicating whether or not the task should be marked complete
	}
	
	/**
	 * Deletes a follow-up task item.
	 * Path: /Followups/<task_id>/Delete/
	 */
	public final static class FOLLOWUPS_DELETE{
		private final static String PATH  ="/Followups/";
		public final static String getPath(String taskId) {
			return PATH + URLEncoder.encode(taskId) + "/Delete/";
		}
	}
	/**
	 * get invitations And Calling Path:/Invitations/List/
	 */
	public final static class GET_OUTSTANDING_INVITATIONS {
		public final static String PATH = "/Invitations/List/";
		public final static String PARAM_FROM = "from_timestamp";
		public final static String PARAM_TO = "to_timestamp";
		public final static String PARAM_COUNT = "count";
	}
	/**
	 * new invitations And Calling Path:/Invitations/New/
	 */
	public final static class NEW_INVITATION {
		public final static String PATH = "/Invitations/New/";
		public final static String PARAM_EMAIL = "email";
		public final static String PARAM_NOTE = "note";
		public final static String PARAM_INVITE_TYPE = "invite_type";
		public final static String PARAM_INVITE_USER_TYPE = "invite_user_type";
	}

	/**
	 * resend invitations And Calling
	 * Path:/Invitations/<invitation_id>/Resend/
	 */
	public final static class RESEND_INVITATION {
		public final static String PATH = "/Invitations/";
		public final static String PARAM_NOTE = "note";

		public final static String getPath(String invitationId) {
			return PATH + URLEncoder.encode(invitationId) + "/Resend/";
		}
	}

	/**
	 * cancel invitations And Calling
	 * Path:/Invitations/<invitation_id>/Cancel/
	 */
	public final static class CANCEL_INVITATION {
		public final static String PATH = "/Invitations/";
		public final static String getPath(String invitationId) {
			return PATH + URLEncoder.encode(invitationId) + "/Cancel/";
		}
	}

	/**
	 * Gets the all available selections for the call forwardig Gets the user's
	 * current forward selection. And Calling Path: /Account/CallForwarding/
	 */

	public final static class AVAILABLE_SELECTIONS {
		public final static String PATH = "/Account/CallForwarding/";
		public final static String PARAM_NEW_SELECTION = "forward";
	}
	public final static class AVAILABLE_ANSWERING_SERVICE {
		public final static String PATH = "/Account/AnsweringService/";
		public final static String PARAM_NEW_SELECTION = "forward";
	}
	/**
	 * Gets the set of all sites that the user provider is affiliated with. Gets
	 * the user's current site. And Calling Path: /Site/
	 */

	public final static class SITE_AFFILIATION {
		public final static String PATH = "/Site/";
		public final static String PARAM_CURRENT_SITE = "current_site";
	}

	/**
	 * Get Practices by Calling Path: /Practice/
	 */
	public final static class PRACTICE_ASSOCIATION {
		public final static String PATH = "/Practice/";
		public final static String PARAM_CURRENT_PRACTICE = "current_practice";
	}

	public final static class  NOTIFICATION {
		public final static String REGISTER = "/Device/UpdatePushToken/";
		public final static String UNREGIITER = "/Device/DeletePushToken/";
		public final static String PARAM_DCOM_DEVICE_ID = "DCOM_DEVICE_ID";
		public final static String TOKEN = "token";
	}
	
	public static final class PREFERENCE {
		public static final String PATH = "/Account/Preference/";
		public static final String PARAM_TIME_SETTING = "time_setting";
		public static final String PARAM_TIME_ZONE = "time_zone";
	}

	public final static class DICOM_SUPPORT {
		private final static String PATH = "/Messaging/Message/";
		public final static String PARAM_SECRET = "secret";
		public final static String PARAM_SEND_IF_NOT_EXIST = "send_if_not_exist";
		public final static String getCheckDicomIofoPath(String messageId, String attachmentId) {
			return PATH + URLEncoder.encode(messageId) + "/CheckDicom/" + URLEncoder.encode(attachmentId) + "/";
		}
		public final static String getDicomIofoPath(String messageId, String attachmentId) {
			return PATH + URLEncoder.encode(messageId) + "/DicomInfo/" + URLEncoder.encode(attachmentId) + "/";
		}
		public static final String getDicom2JPGPath(String messageId, String attachmentId,int index) {
			return PATH + URLEncoder.encode(messageId) + "/ViewDicomJPG/" + URLEncoder.encode(attachmentId) + "/" + index + "/";
		}

	}

	public final static class INVITATIONS {
		public final static String PATH = "/Invitations/";
		public final static String INVITE_TYPE = "invite_type";
		public final static String getAcceptPath(String pendingId) {
			return PATH + pendingId + "/Accept/";
		}
		public final static String getRefusePath(String pendingId) {
			return PATH + pendingId + "/Refuse/";
		}
	}
	
	public final static class USER_TABS {
		public final static String PATH = "/Tab/GetUserTabs/";
		public final static String ONLY_USER_TAB = "is_only_user_tab";
		public final static String SHOW_MY_FAVORITE = "show_my_favorite";
	}
	
	public final static class USER_LIST{
		public final static String FIRST_NAME = "from_first_name";
		public final static String LAST_NAME = "from_last_name";
		public final static String ID = "from_user_id";
		public final static String NAME = "from_name";
		public final static String COUNT = "count";
	}
	
	public final static class UPDATEAVATAR {
		public final static String PATH = "/User/Profile/UpdatePhoto/";
	}

}