package com.doctorcom.physician.net.http;

import java.io.DataOutputStream;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.SocketTimeoutException;
import java.net.URL;
import java.net.URLEncoder;
import java.util.Iterator;
import java.util.Map;

import javax.net.ssl.HttpsURLConnection;

import org.json.JSONException;
import org.json.JSONObject;

import android.content.Context;
import android.content.Intent;
import android.os.AsyncTask;
import android.os.Build;
import android.widget.Toast;

import com.doctorcom.android.R;
import com.doctorcom.physician.AppValues;
import com.doctorcom.physician.activity.login.LoginActivity;
import com.doctorcom.physician.activity.setting.PhoneInputActivity;
import com.doctorcom.physician.net.FakeX509TrustManager;
import com.doctorcom.physician.net.NetConstantValues;
import com.doctorcom.physician.utils.CallBack;
import com.doctorcom.physician.utils.DocLog;
import com.doctorcom.physician.utils.Utils;
import com.google.android.gcm.GCMRegistrar;

public class NetConncet extends AsyncTask<Void, Integer, String> {

	private final String TAG = "NetConncet";
	private String postAddress = "";
	private Map<String, String> param;
	protected Context context;
	public static final int HTTP_GET = 0;
	public static final int HTTP_POST = 1;
	private String httpMethod = "POST";
	private AppValues appValues;
	final static long connect_expire_time = 6000;
	final static int retry_time = 10;
	public static int activeConnections = 0;

	public NetConncet(Context context, String urlPath) {
		this.context = context;
		appValues = new AppValues(context);
		postAddress = appValues.getServerURL() + NetConstantValues.APP_URL
				+ urlPath;
	}

	public NetConncet(Context context, String urlPath, Map<String, String> map) {
		this.context = context;
		appValues = new AppValues(context);
		postAddress = appValues.getServerURL() + NetConstantValues.APP_URL
				+ urlPath;
		param = map;
	}

	@Override
	protected String doInBackground(Void... params) {
		NetConncet.activeConnections++;
		DocLog.d(TAG, "ActiveConnections:" + NetConncet.activeConnections);
		String result = connect(0);
		NetConncet.activeConnections--;
		DocLog.d(TAG, "ActiveConnections:" + NetConncet.activeConnections);
		return result;
	}

	public String connect(int loop) {
		// HTTP connection reuse which was buggy pre-froyo
		// This code will fix a android 2.1 - version bugs
		if (Build.VERSION.SDK_INT < Build.VERSION_CODES.FROYO) {
			System.setProperty("http.keepAlive", "false");
		}

		long startTime = System.currentTimeMillis();
		Utils utils = new Utils(context);
		if (!utils.checkNetworkAvailable()) {
			return context.getString(R.string.network_not_available);
		}
		String result = "";
		try {

			URL url = new URL(postAddress);
			DocLog.d(TAG, "post address >> " + postAddress);
			HttpURLConnection conn;
			if (url.getProtocol().equals("https")) {
				if (appValues.getCurrent_version() == AppValues.ROLE_DEVELOP_VERSION) {
					// No need to verify the server-side certificate.
					FakeX509TrustManager.allowAllSSL();
				}
				conn = (HttpsURLConnection) url.openConnection();
			} else {
				conn = (HttpURLConnection) url.openConnection();
			}
			conn.setReadTimeout(60000);
			conn.setConnectTimeout(15000);
			conn.setDoInput(true);
			conn.setRequestProperty("DCOM_DEVICE_ID",
					appValues.getDcomDeviceId());
			DocLog.d(TAG, "DCOM_DEVICE_ID:" + appValues.getDcomDeviceId());
			conn.setRequestMethod(httpMethod);
			if (param != null) {
				conn.setDoOutput(true);
				DataOutputStream out = new DataOutputStream(
						conn.getOutputStream());
				Iterator<Map.Entry<String, String>> iter = param.entrySet()
						.iterator();
				StringBuffer sb = new StringBuffer();
				while (iter.hasNext()) {
					Map.Entry<String, String> entry = iter.next();
					String key = entry.getKey();
					String val = entry.getValue();
					sb.append(key + "=" + URLEncoder.encode(val) + "&");
				}
				if (sb.length() > 0) {
					sb = sb.deleteCharAt(sb.length() - 1);
					DocLog.d(TAG, "params:" + sb.toString());
					out.writeBytes(sb.toString());
					out.flush();
				}
				out.close();
			}
			int response = conn.getResponseCode();
			DocLog.d(TAG, "response code: " + String.valueOf(response));
			if (response == HttpURLConnection.HTTP_OK) {
				InputStream is = conn.getInputStream();
				int i = 0;
				String mime = null;
				while (true) {
					mime = conn.getHeaderField(i);
					if (mime == null)
						break;
					DocLog.i(TAG, "key:" + conn.getHeaderFieldKey(i)
							+ " value:" + mime);
					i++;
				}
				result = Utils.stream2String(is);
				is.close();
			} else {
				if (response <= 0) {
					long currentTime = System.currentTimeMillis();
					if ((currentTime - startTime) < NetConncet.connect_expire_time) {
						loop++;
						if (loop < NetConncet.retry_time) {
							DocLog.i(TAG, "Retry: (" + loop + ") times.");
							return connect(loop);
						}
					}

					result = context.getString(R.string.get_data_error);
				} else if (response < 400) {
					InputStream is = conn.getInputStream();
					result = Utils.stream2String(is);
					is.close();
				} else {
					InputStream is = conn.getErrorStream();
					result = Utils.stream2String(is);
					is.close();
				}
			}

		} catch (SocketTimeoutException e) {
			DocLog.e(TAG, "SocketTimeoutException", e);
			result = context.getString(R.string.get_data_error_socket);

			long currentTime = System.currentTimeMillis();
			if ((currentTime - startTime) < NetConncet.connect_expire_time) {
				loop++;
				if (loop < NetConncet.retry_time) {
					DocLog.i(TAG, "Retry: (" + loop + ") times.");
					return connect(loop);
				}
			}
		} catch (Exception e) {
			DocLog.e(TAG, "Exception", e);
			result = context.getString(R.string.get_data_error_exception);
		}
		DocLog.d(TAG, result);
		return result;

	}

	@Override
	protected void onPostExecute(String result) {
		super.onPostExecute(result);
		try {
			JSONObject jsonObj = new JSONObject(result);
			if (Utils.isDeviceDissociated(result)) {
				GCMRegistrar.unregister(context);
				Toast.makeText(context, jsonObj.getString("descr"),
						Toast.LENGTH_LONG).show();
				if (!postAddress.equals(appValues.getServerURL()
						+ NetConstantValues.APP_URL
						+ NetConstantValues.DEVICE_CHECK_IN.PATH)) {
					Intent intent = new Intent(context, LoginActivity.class);
					intent.setFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP);
					context.startActivity(intent);

				}
			}
			if (Utils.isMobilePhoneValidated(result)) {
				Toast.makeText(context, jsonObj.getString("descr"),
						Toast.LENGTH_LONG).show();
				CallBack.callerNumber = jsonObj.getJSONObject("data")
						.getString("mobile_phone");
				CallBack.isNumberConfirmed = jsonObj.getJSONObject("data")
						.getBoolean("mobile_confirmed");
				GCMRegistrar.unregister(context);
				context.stopService(new Intent(
						"com.doctorcom.physician.message"));
				Intent intent = new Intent(context, PhoneInputActivity.class);
				intent.putExtra("validated", false);
				context.startActivity(intent);
			}
			if (!jsonObj.isNull("settings")) {
				JSONObject settingsJsonObject = jsonObj
						.getJSONObject("settings");
				if (!settingsJsonObject.isNull("current_time_zone")) {
					appValues.setTimezone(settingsJsonObject
							.getString("current_time_zone"));
				}
				if (!settingsJsonObject.isNull("time_setting")) {
					appValues.setTimeFormat(settingsJsonObject
							.getInt("time_setting"));
				}
			}
		} catch (JSONException e) {
			DocLog.e(TAG, "JSONException", e);
		}

	}

	public void setHttpMethod(int httpMethod) {
		if (httpMethod == HTTP_POST) {
			this.httpMethod = "POST";
		} else if (httpMethod == HTTP_GET) {
			this.httpMethod = "GET";
		} else {
			throw new IllegalArgumentException("Method = " + httpMethod + ", "
					+ httpMethod + " " + HTTP_POST + " or " + HTTP_GET);
		}
	}

	public boolean isDcomDeviceIdEmpty() {
		return appValues.isDcomDeviceIdEmpty();
	}

}
