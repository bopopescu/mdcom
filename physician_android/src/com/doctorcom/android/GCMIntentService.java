/*
 * Copyright 2012 Google Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.doctorcom.android;

import java.util.ArrayList;
import java.util.List;

import android.annotation.TargetApi;
import android.app.Notification;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.database.sqlite.SQLiteDatabase;
import android.os.Build;
import android.support.v4.content.LocalBroadcastManager;
import android.util.Log;

import com.doctorcom.physician.AppValues;
import com.doctorcom.physician.activity.main.NavigationActivity;
import com.doctorcom.physician.utils.DocLog;
import com.doctorcom.physician.utils.cache.Cache;
import com.doctorcom.physician.utils.cache.DataBaseHelper;
import com.doctorcom.physician.utils.cache.Cache.CacheSchema;
import com.google.android.gcm.GCMBaseIntentService;
import com.google.android.gcm.GCMRegistrar;

/**
 * IntentService responsible for handling GCM messages.
 */
public class GCMIntentService extends GCMBaseIntentService {

	private static final String TAG = "GCMIntentService";

	public GCMIntentService() {
		// super(SENDER_ID);
	}

	@Override
	protected String[] getSenderIds(Context context) {
		String[] ids = { new AppValues(this).getProjectId() };
		return ids;
	}

	@Override
	protected void onRegistered(Context context, String registrationId) {
		DocLog.i(TAG, "Device registered: regId = " + registrationId);
		ServerUtilities.register(context, registrationId);
	}

	@Override
	protected void onUnregistered(Context context, String registrationId) {
		DocLog.i(TAG, "Device unregistered");
		if (GCMRegistrar.isRegisteredOnServer(context)) {
			ServerUtilities.unregister(context, registrationId);
		} else {
			// This callback results from the call to unregister made on
			// ServerUtilities when the registration to the server failed.
			Log.i(TAG, "Ignoring unregister callback");
		}
	}

	@Override
	protected void onMessage(Context context, Intent intent) {
		DocLog.i(TAG, "Received message");
		List<String> messageNotification = new ArrayList<String>();
		if (intent != null) {
			String body = intent.getStringExtra("body");
			String sbadge = intent.getStringExtra("badge");
			String message = intent.getStringExtra("message");
			String user = intent.getStringExtra("user");
			if (user == null) {
				if (message == null) {
					if (body != null) {
						DocLog.d(TAG, "Received new message");
						try {
							int badge = Integer.parseInt(sbadge);
							if (body != null && !body.equals("") && badge != 0) {
								totalUnread = badge;
								messageNotification.add(body);
								messageNotification
										.add(getString(R.string.gcm_message));
							}
						} catch (NumberFormatException e) {

						}
						if (messageNotification == null
								|| messageNotification.size() == 0) {
							messageNotification
									.add(getString(R.string.gcm_message));
							messageNotification
									.add(getString(R.string.gcm_message));
						}
						// notifies user
						generateNotification(context, messageNotification);
						LocalBroadcastManager.getInstance(context).sendBroadcast(
								new Intent("newMessageReceiver").putExtra("message",
										message));
					}
				} else {
					DocLog.d(TAG, "read ans");
					LocalBroadcastManager.getInstance(context).sendBroadcast(
							new Intent("messageResolvedReceiver").putExtra(
									"message", message));
					LocalBroadcastManager.getInstance(context).sendBroadcast(
							new Intent("newMessageReceiver").putExtra("message",
									message));
				}				
				// if (message != null) {
				// try {
				// JSONObject jsonObject = new JSONObject(message);
				// String uuid = jsonObject.getString("uuid");
				// boolean updateResolved = jsonObject.getBoolean("resolve");
				// MessageDetailActivity.MessageDetailFragment.changeMessageResolvedStatus(context,
				// uuid, updateResolved);
				// } catch (JSONException e) {
				// DocLog.e("MessageResolvedReceiver", "JSONException", e);
				// }
				// }
			} else {
				DataBaseHelper helper = new DataBaseHelper(context);
				SQLiteDatabase db = helper.getWritableDatabase();
				db.delete(CacheSchema.TABLE_NAME, "category = "
						+ Cache.CACHE_USER_TABS, null);
				db.close();
				helper.close();
				DocLog.i(TAG, "delete user tab list!");
				LocalBroadcastManager.getInstance(context).sendBroadcast(
						new Intent("updateUserTabs"));
			}
		}
	}

	@Override
	protected void onDeletedMessages(Context context, int total) {
		DocLog.i(TAG, "Received deleted messages notification");
	}

	@Override
	public void onError(Context context, String errorId) {
		DocLog.i(TAG, "Received error: " + errorId);
	}

	@Override
	protected boolean onRecoverableError(Context context, String errorId) {
		// log message
		DocLog.i(TAG, "Received recoverable error: " + errorId);
		return super.onRecoverableError(context, errorId);
	}

	/**
	 * Issues a notification to inform the user that server has sent a message.
	 */
	private int totalUnread = 0;

	@TargetApi(Build.VERSION_CODES.HONEYCOMB)
	private void generateNotification(Context context, List<String> message) {
		if (totalUnread == 0)
			return;
		NotificationManager nm = (NotificationManager) getSystemService(NOTIFICATION_SERVICE);
		Intent notificationIntent = new Intent(context,
				NavigationActivity.class);
		// set intent so it does not start a new activity
		notificationIntent.setFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP
				| Intent.FLAG_ACTIVITY_SINGLE_TOP);
		notificationIntent.putExtra("clearCache", true);
		PendingIntent intent = PendingIntent.getActivity(context,
				R.string.app_name, notificationIntent, 0);

		if (android.os.Build.VERSION.SDK_INT < 11) {
			Notification notification = new Notification(
					R.drawable.service_doctorcom, message.get(0).toString(),
					System.currentTimeMillis());
			notification.defaults = Notification.DEFAULT_SOUND
					| Notification.DEFAULT_LIGHTS;
			notification.flags = Notification.FLAG_AUTO_CANCEL;
			notification.number = totalUnread;
			notification.setLatestEventInfo(this, "DoctorCom", message.get(1)
					.toString(), intent);
			nm.notify(R.string.app_name, notification);

		} else {
			Notification.Builder n = new Notification.Builder(context)
					.setDefaults(
							Notification.DEFAULT_SOUND
									| Notification.DEFAULT_LIGHTS)
					.setContentTitle("DoctorCom")
					.setContentText(message.get(1).toString())
					.setTicker(message.get(0).toString())
					.setSmallIcon(R.drawable.service_doctorcom)
					.setNumber(totalUnread).setAutoCancel(true)
					.setContentIntent(intent);
			nm.notify(R.string.app_name, n.getNotification());
		}

	}

}
