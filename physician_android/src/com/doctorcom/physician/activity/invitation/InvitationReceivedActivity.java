package com.doctorcom.physician.activity.invitation;

import java.util.HashMap;
import java.util.Map;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import android.app.Activity;
import android.app.ProgressDialog;
import android.content.Intent;
import android.net.http.SslError;
import android.os.Bundle;
import android.view.View;
import android.webkit.SslErrorHandler;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.LinearLayout;
import android.widget.Toast;

import com.doctorcom.android.R;
import com.doctorcom.physician.net.NetConstantValues;
import com.doctorcom.physician.net.http.NetConncet;
import com.doctorcom.physician.utils.DocLog;
import com.doctorcom.physician.utils.JsonErrorProcess;
import com.doctorcom.physician.utils.cache.Cache;
import com.doctorcom.physician.utils.cache.CacheService;

public class InvitationReceivedActivity extends Activity {
	private final String TAG = "InvitationReceivedActivity";
	private int length, index;
	private JSONArray array;
	private WebView contentWebView;
	private String type, pendingId;
	private LinearLayout llContent, llLoading;

	@Override
	protected void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
		setContentView(R.layout.activity_invitation_received);
		contentWebView = (WebView) findViewById(R.id.webview_content);
		llContent = (LinearLayout) findViewById(R.id.llContent);
		llLoading = (LinearLayout) findViewById(R.id.llLoading);
		llContent.setVisibility(View.GONE);
		llLoading.setVisibility(View.VISIBLE);
		try {
			String result = getIntent().getStringExtra("result");
			JSONObject jData = new JSONObject(result);
			JSONArray call_group_penddings = null;
			if (!jData.isNull("call_group_penddings"))
				call_group_penddings = jData
						.getJSONArray("call_group_penddings");
			JSONArray invitations = jData.getJSONArray("invitations");
			joinIntoArray(call_group_penddings, invitations);
			// array = jData.getJSONArray("invitations");
			length = array.length();
			index = 0;
			showDetail(array.optJSONObject(index));
		} catch (JSONException e) {
			DocLog.e(TAG, "JSONException", e);
			finish();
		}

	}

	private void joinIntoArray(JSONArray call_group_penddings,
			JSONArray invitations) {
		// TODO Auto-generated method stub
		JSONArray tempArray = new JSONArray();
		if (null != call_group_penddings) {
			for (int i = 0; i < call_group_penddings.length(); i++) {
				try {
					tempArray.put(call_group_penddings.getJSONObject(i));
				} catch (JSONException e) {
					// TODO Auto-generated catch block
					DocLog.e(TAG, "JSONException", e);
				}
			}
		}
		for (int i = 0; i < invitations.length(); i++) {
			try {
				tempArray.put(invitations.getJSONObject(i));
			} catch (JSONException e) {
				// TODO Auto-generated catch block
				DocLog.e(TAG, "JSONException", e);
			}
		}
		array = tempArray;

	}

	protected void showDetail(JSONObject detail) {
		llContent.setVisibility(View.GONE);
		llLoading.setVisibility(View.VISIBLE);
		try {
			type = detail.getString("type");
			pendingId = detail.getString("pending_id");
			String content = detail.getString("content");
			contentWebView.setWebViewClient(new WebViewClient() {

				@Override
				public void onReceivedSslError(WebView view,
						SslErrorHandler handler, SslError error) {
					handler.proceed();
				}

				@Override
				public void onPageFinished(WebView view, String url) {
					llContent.setVisibility(View.VISIBLE);
					llLoading.setVisibility(View.GONE);
				}

			});
			contentWebView.loadDataWithBaseURL(null, content, "text/html",
					"utf-8", null);
		} catch (JSONException e) {
			showNextDetail();
			DocLog.e(TAG, "JSONException", e);
		}
	}

	public void OnRefuse(View view) {
		final ProgressDialog progressDialog = ProgressDialog.show(this, "",
				getString(R.string.process_text));
		Map<String, String> params = new HashMap<String, String>();
		params.put(NetConstantValues.INVITATIONS.INVITE_TYPE, type);
		NetConncet conncet = new NetConncet(this,
				NetConstantValues.INVITATIONS.getRefusePath(pendingId), params) {

			@Override
			protected void onPostExecute(String result) {

				String declineSuccess = "";
				super.onPostExecute(result);
				progressDialog.dismiss();
				try {
					JSONObject jObj = new JSONObject(result);
					if (JsonErrorProcess.checkJsonError(result,
							InvitationReceivedActivity.this)) {
						JSONObject jData = jObj.getJSONObject("data");
						if (!jData.isNull("message"))
							declineSuccess = jData.getString("message");
						else
							declineSuccess = getResources().getString(
									R.string.action_successed);

						Toast.makeText(InvitationReceivedActivity.this,
								declineSuccess, Toast.LENGTH_SHORT).show();
					}
				} catch (JSONException e) {
					// TODO Auto-generated catch block
					DocLog.e(TAG, "JSON ERROR!", e);
				}
				showNextDetail();
			}

		};
		conncet.execute();
	}

	public void OnAccept(View view) {
		final ProgressDialog progressDialog = ProgressDialog.show(this, "",
				getString(R.string.process_text));
		Map<String, String> params = new HashMap<String, String>();
		params.put(NetConstantValues.INVITATIONS.INVITE_TYPE, type);
		NetConncet conncet = new NetConncet(this,
				NetConstantValues.INVITATIONS.getAcceptPath(pendingId), params) {

			@Override
			protected void onPostExecute(String result) {
				String acceptSuccess = "";
				super.onPostExecute(result);
				progressDialog.dismiss();
				try {
					JSONObject jObj = new JSONObject(result);
					if (JsonErrorProcess.checkJsonError(result,
							InvitationReceivedActivity.this)) {
						if (type.equalsIgnoreCase("org")) {
							Intent intent = new Intent(
									CacheService.CACHE_SERVICE);
							intent.putExtra("cmd", 4);
							startService(new Intent(intent));

						} else {
							Intent intent = new Intent(
									CacheService.CACHE_SERVICE);
							intent.putExtra("cmd", 3);
							startService(new Intent(intent));

						}
						Cache.cleanListCache(String.valueOf(Cache.CACHE_USER_TABS), NetConstantValues.USER_TABS.PATH, InvitationReceivedActivity.this.getApplicationContext());
						JSONObject jData = jObj.getJSONObject("data");
						if (!jData.isNull("message"))
							acceptSuccess = jData.getString("message");
						else
							acceptSuccess = getResources().getString(
									R.string.action_successed);
						Toast.makeText(InvitationReceivedActivity.this,
								acceptSuccess, Toast.LENGTH_SHORT).show();
					}
				} catch (JSONException e) {
					// TODO Auto-generated catch block
					DocLog.e(TAG, "JSON ERROR!", e);
				}
				showNextDetail();
			}

		};
		conncet.execute();
	}

	private void showNextDetail() {
		index++;
		if (index < length) {
			showDetail(array.optJSONObject(index));
		} else {
			finish();
		}
	}
}
