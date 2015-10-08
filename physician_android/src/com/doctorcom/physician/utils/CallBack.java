package com.doctorcom.physician.utils;

import java.util.HashMap;
import java.util.Map;

import org.json.JSONException;
import org.json.JSONObject;

import android.app.ProgressDialog;
import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import android.widget.Toast;

import com.doctorcom.android.R;
import com.doctorcom.physician.net.NetConstantValues;
import com.doctorcom.physician.net.http.NetConncet;

public class CallBack {
	private final String TAG = "CallBack";
	private ProgressDialog progress;
	public static String callerNumber;
	public static boolean isNumberConfirmed = false;
	private Context context;

	public CallBack(Context context) {
		this.context = context;
	}
	
	public void call(String path, String number) {
		if (callerNumber == null || callerNumber.equals("")) {
			noNumbercall(path, number);
		} else {
			useNumberCall(path, number);
		}
	}
	
	public void noNumbercall(final String path, final String number) {
		progress = ProgressDialog.show(context, "", context.getString(R.string.process_text));
		NetConncet netConncet = new NetConncet(context, NetConstantValues.PHONE_NUMBER.PATH) {

			@Override
			protected void onPostExecute(String result) {
				super.onPostExecute(result);
				try {
					JSONObject obj = new JSONObject(result);
					if (obj.isNull("errno")) {
						callerNumber = obj.getJSONObject("data").getString("mobile_phone");
						isNumberConfirmed = obj.getJSONObject("data").getBoolean("mobile_confirmed");
						DocLog.d(TAG, "callerNumber: " + callerNumber);
						useNumberCall(path, number);
					} else {
						if (progress.isShowing()) {
							progress.dismiss();
						}
						Toast.makeText(context, obj.getString("descr"), Toast.LENGTH_LONG).show();
					}
					
				} catch (JSONException e) {
					if (progress.isShowing()) {
						progress.dismiss();
					}
					Toast.makeText(context, R.string.error_occur, Toast.LENGTH_LONG).show();
					DocLog.e(TAG, "JSONException", e);
				}
			}
			
		};
		netConncet.setHttpMethod(NetConncet.HTTP_GET);
		netConncet.execute();

	}
	
	public void useNumberCall(String path, String number) {
		if (progress == null) {
			progress = ProgressDialog.show(context, "", context.getString(R.string.process_text));
		} else {
			if (!progress.isShowing()) {
				progress.show();
			}
		}
		Map<String, String> params = new HashMap<String, String>();
		if (number != null) {
			params.put(NetConstantValues.CALL_ARBITRARY.PARAM_NUMBER, number);
		}
		params.put(NetConstantValues.CALL_USER.PARAM_CALLER_NUMBER, callerNumber);
		NetConncet connect = new NetConncet(context, path, params){

			@Override
			protected void onPostExecute(String result) {
				super.onPostExecute(result);
				try {
					JSONObject jsonObj = new JSONObject(result);
					if (jsonObj.isNull("errno")) {
						String number = jsonObj.getJSONObject("data").getString("number");
						Intent intent = new Intent(Intent.ACTION_CALL, Uri.parse("tel://" + number));
						context.startActivity(intent);
					} else {
						Toast.makeText(context, jsonObj.getString("descr"), Toast.LENGTH_LONG).show();
					}
				} catch (JSONException e) {
					Toast.makeText(context, R.string.error_occur, Toast.LENGTH_LONG).show();
					DocLog.e(TAG, "JSONException", e);
				} finally {
					if (progress.isShowing()) {
						progress.dismiss();
					}
				}
			}
			
		};
		connect.execute();

	}
	
	public void userPage(String userId, String number) {
		if (number.length() < 10) {
			Toast.makeText(context, R.string.number_enter_warning, Toast.LENGTH_SHORT).show();
		} else {
			final ProgressDialog progress = ProgressDialog.show(context, "", context.getString(R.string.process_text));
			Map<String, String> params = new HashMap<String, String>();
			params.put(NetConstantValues.PAGE_USER.PARAM_NUMBER, number);
			NetConncet netConncet = new NetConncet(context, NetConstantValues.PAGE_USER.getPath(userId), params) {
				@Override
				protected void onPostExecute(String result) {
					super.onPostExecute(result);
					progress.dismiss();
					if (JsonErrorProcess.checkJsonError(result, context)) {
						Toast.makeText(context, R.string.action_successed, Toast.LENGTH_LONG).show();
					}
				}
			};
			netConncet.execute();
		}

	}


}
