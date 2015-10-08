package com.doctorcom.physician.service;

import java.lang.ref.WeakReference;
import java.util.HashMap;

import org.json.JSONArray;
import org.json.JSONObject;

import android.annotation.TargetApi;
import android.app.Notification;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.content.res.Resources;
import android.os.Handler;
import android.os.IBinder;
import android.os.Message;
import android.support.v4.content.LocalBroadcastManager;

import com.doctorcom.android.R;
import com.doctorcom.physician.AppValues;
import com.doctorcom.physician.activity.main.NavigationActivity;
import com.doctorcom.physician.net.NetConstantValues;
import com.doctorcom.physician.net.http.NetConncet;
import com.doctorcom.physician.utils.DocLog;
import com.doctorcom.physician.utils.Utils;

public class MessageService extends Service {
	private final static String TAG = "MessageService";
	private Handler mHandler = null;
	private final static int MESSAGE_UNREAD = -10;
	private final static int MESSAGE_NOTICE = -11;
	private final static int MESSAGE_OVERDUE_DEVICE = -12;

	private final static int REFRESH_TIME = 1000 * 60; // 60s
	private final static int OVERDUE_TIME = 1000 * 60 * 60 * 24; // 1 day

	private long checkTime = 0;
	private int totalUnread, unReadCount;

	@Override
	public void onCreate() {
		super.onCreate();
		DocLog.d(TAG, "MessageService create!");
		AppValues appValues = new AppValues(this);
		String secret = appValues.getSecret();
		initParams(secret);
	}
	
	// init params, and process messages.
	public boolean initParams(String secret) {
		if (secret == null || "".equals(secret)) {
			stopSelf();
			return false;
		} else {
			mHandler = new MessageServiceHandler(this);
			// unread
			Message messageUnread = mHandler.obtainMessage(MESSAGE_UNREAD);
			mHandler.sendMessageDelayed(messageUnread, REFRESH_TIME);
			// overDue
			Message messageOverDue = mHandler.obtainMessage(MESSAGE_OVERDUE_DEVICE);
			mHandler.sendMessageDelayed(messageOverDue, OVERDUE_TIME);
		}
		return true;
	}

	@Override
	public int onStartCommand(Intent intent, int flags, int startId) {
		super.onStart(intent, startId);
		DocLog.d(TAG, "MessageService start!");
		return START_STICKY;
	}

	@Override
	public void onDestroy() {
		DocLog.d(TAG, "MessageService destory!");
		if (mHandler != null) {
			mHandler.removeMessages(MESSAGE_UNREAD);
			mHandler.removeMessages(MESSAGE_NOTICE);
			mHandler.removeMessages(MESSAGE_OVERDUE_DEVICE);
		}
		super.onDestroy();
	}

	@Override
	public IBinder onBind(Intent intent) {
		return null;
	}

	public void checkNewMessage() {
		HashMap<String, String> params = new HashMap<String, String>();
		DocLog.d(TAG, "checkNewMessage checkTime :" + checkTime);
		String fromTime = Long.toString(checkTime + 1L);

		if (checkTime != 0) {
			params.put(NetConstantValues.MESSAGING_LIST_RECEIVED.PARAM_FROM, fromTime);
		}
		params.put(NetConstantValues.MESSAGING_LIST_RECEIVED.PARAM_COUNT, "9999");
		NetConncet netConncet = new NetConncet(this, NetConstantValues.MESSAGING_LIST_RECEIVED.PATH, params) {
			@Override
			protected void onPostExecute(String result) {
				try {
					JSONObject jsonObj = new JSONObject(result);
					if (!jsonObj.isNull("errno")) {
						if (Utils.isDeviceDissociated(result) || Utils.isMobilePhoneValidated(result)) {
							stopSelf();
						}
					} else {
						totalUnread = jsonObj.getJSONObject("data").getInt("unread_message_count");
						unReadCount = 0;
						JSONArray jsonArr = jsonObj.getJSONObject("data").getJSONArray("messages");
						if (jsonArr != null) {
							int length = jsonArr.length();
							for (int i = 0; i < length; i++) {
								JSONObject jsonOpt = jsonArr.optJSONObject(i);
								boolean readFlag = jsonOpt.getBoolean("read_flag");
								if (readFlag == false) {
									unReadCount++;
								}
								// update the newest date time for the checkTime
								try {
									// Date date = new
									// Date(jsonOpt.getString("timestamp"));
									// long newDate = date.getTime() / 1000;
									long newDate = jsonOpt.getLong("send_timestamp");
									if (newDate > checkTime) {
										checkTime = newDate;
									}
								} catch (Exception dateEx) {
									DocLog.e(TAG, "checkNewMessage Date convert Exception", dateEx);
								}

							}
						}
						DocLog.d(TAG, "checkNewMessage unReadCount:"
								+ unReadCount);
						// if there is a message unRead, then set the
						// message.obj= true. default false....
						Message message = mHandler.obtainMessage(MESSAGE_NOTICE, false);
						if (unReadCount > 0) {
							message.obj = true;
						}
						mHandler.dispatchMessage(message);
					}

				} catch (Exception ex) {
					DocLog.e(TAG, "checkNewMessage JSONException", ex);
				}
			}
		};

		// if it is first called, then currentTime -60.
		// then next time will call it again after 1 min,
		// make sure the checkTime within 1 min
		// long longToDate = System.currentTimeMillis()/1000;
		// checkTime = longToDate - 61; //61s,fix delay.

		//
		netConncet.execute();

		// WakeLockHelper.acquireStaticLock(getApplicationContext());

	}

	@TargetApi(11)
	public void NoticeMessage(boolean unReadStatus) {
		NotificationManager nm = (NotificationManager) getSystemService(Context.NOTIFICATION_SERVICE);
		if (unReadStatus == true) {
			Resources res = getResources();
			String contentText;
			if (unReadCount == 1) {
				contentText = res.getQuantityString(R.plurals.unread_messages, 1, 1);
			} else {
				contentText = res.getQuantityString(R.plurals.unread_messages, unReadCount, unReadCount);
			}
			Intent i = new Intent(this, NavigationActivity.class);
			i.setFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP);
			PendingIntent contentIntent = PendingIntent.getActivity(this, R.string.app_name, i, PendingIntent.FLAG_UPDATE_CURRENT);
			if (android.os.Build.VERSION.SDK_INT < 11) {
				Notification notification = new Notification(R.drawable.service_doctorcom, "", System.currentTimeMillis());
				notification.defaults = Notification.DEFAULT_SOUND | Notification.DEFAULT_LIGHTS;
				notification.flags = Notification.FLAG_AUTO_CANCEL;
				notification.number = totalUnread;
				notification.setLatestEventInfo(this, "DoctorCom", contentText, contentIntent);
				nm.notify(R.string.app_name, notification);
			} else {
				Notification.Builder n = new Notification.Builder(this)
						.setDefaults(Notification.DEFAULT_SOUND | Notification.DEFAULT_LIGHTS)
						.setContentTitle("DoctorCom")
						.setContentText(contentText)
						.setSmallIcon(R.drawable.service_doctorcom)
						.setNumber(totalUnread).setAutoCancel(true)
						.setContentIntent(contentIntent);
				nm.notify(R.string.app_name, n.getNotification());
			}
			LocalBroadcastManager.getInstance(this).sendBroadcast(new Intent("newMessageReceiver"));
		}
	}

	public void processOverdueDevice() {
		mHandler.removeMessages(MESSAGE_UNREAD);
		mHandler.removeMessages(MESSAGE_NOTICE);
		mHandler.removeMessages(MESSAGE_OVERDUE_DEVICE);
		this.stopSelf();

	}

	private static class MessageServiceHandler extends Handler {
		WeakReference<MessageService> mService;
		public MessageServiceHandler(MessageService service) {
			mService = new WeakReference<MessageService>(service);
		}
		@Override
		public void handleMessage(Message msg) {
			MessageService service = mService.get();
			switch (msg.what) {
			case MESSAGE_UNREAD:
				DocLog.d(TAG, "MESSAGE_UNREAD process");
				service.checkNewMessage();
				Message message = obtainMessage(MESSAGE_UNREAD);
				sendMessageDelayed(message, REFRESH_TIME);
				break;
			case MESSAGE_NOTICE:
				DocLog.d(TAG, "MESSAGE_NOTICE process");
				service.NoticeMessage((Boolean) msg.obj);
				break;
			case MESSAGE_OVERDUE_DEVICE:
				DocLog.d(TAG, "MESSAGE_OVERDUE_DEVICE process");
				service.processOverdueDevice();
				Message messageOverDue = obtainMessage(MESSAGE_OVERDUE_DEVICE);
				sendMessageDelayed(messageOverDue, OVERDUE_TIME);
				break;
			default:
				super.handleMessage(msg);
				break;
			}
		}

	}

}
