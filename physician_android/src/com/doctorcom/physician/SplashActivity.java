package com.doctorcom.physician;

import org.json.JSONException;
import org.json.JSONObject;

import android.app.Activity;
import android.app.AlertDialog;
import android.app.AlertDialog.Builder;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager.NameNotFoundException;
import android.os.Bundle;
import android.text.Html;

import com.crittercism.app.Crittercism;
import com.doctorcom.android.R;
import com.doctorcom.physician.activity.login.LoginActivity;
import com.doctorcom.physician.activity.main.NavigationActivity;
import com.doctorcom.physician.net.NetConstantValues;
import com.doctorcom.physician.net.http.NetConncet;
import com.doctorcom.physician.settings.AppSettings;
import com.doctorcom.physician.utils.DocLog;

public class SplashActivity extends Activity {

	private final String TAG = "SplashActivity";
	private int mRoleVersion = AppValues.ROLE_DEVELOP_VERSION;
	private AppValues appValues;

	@Override
	public void onCreate(Bundle savedInstanceState) {
//		setTheme(android.R.style.Theme_Light_NoTitleBar_Fullscreen);
		super.onCreate(savedInstanceState);
//		setContentView(R.layout.activity_splash);
		Crittercism.init(getApplicationContext(), "50528e32c8f974548c000001");		
		//
		// mRoleVersion = AppValues.ROLE_PRODUCT_VERSION;
		appValues = new AppValues(this);
		if (!appValues.isEncrypted()) {
			String dcomDeviceId = appValues.getDcomDeviceId();
			String secret = appValues.getSecret();
			appValues.setDcomDeviceId(dcomDeviceId);
			appValues.setSecret(secret);
			appValues.setEncrypted(true);
			DocLog.i(TAG, "encrypt all properties");
		}
		try {
			autoLogin();
		} catch (Exception e) {
			DocLog.e(TAG, "Exception", e);
			startLogin();
		}
	}

	private void showNewFeatureDialog() {
		Intent intent = new Intent(this, NewFeatureDialog.class);
		startActivity(intent);
		finish();

	}

	private boolean ifShowNewFeature() {
		boolean isShowNewFeature = false;
		AppSettings appSettings = new AppSettings(this);
		boolean isNewFeatureShow = appSettings.getSettingBoolean(
				"is_new_feature_show", false);
		String versionName = appSettings.getSettingString(
				"feature_version_name", "");
		PackageInfo info = null;
		try {
			info = getPackageManager().getPackageInfo(getPackageName(), 0);
		} catch (NameNotFoundException e1) {
			try {
				info = getPackageManager().getPackageInfo(getPackageName(), 0);
			} catch (NameNotFoundException e) {
				// TODO Auto-generated catch block
				DocLog.e(TAG, "Get version name error", e);
			}
		}
		if (versionName.equals("")
				|| (info != null && !versionName.equals(info.versionName))) {
			isShowNewFeature = true;
		} else if (!isNewFeatureShow) {
			isShowNewFeature = true;
		}
		return isShowNewFeature;

	}

	public void autoLogin() {
		setLog(mRoleVersion);
		appValues.setCurrent_version(mRoleVersion);
		AppSettings appSettings = new AppSettings(this);
		final AppSettings setting = appSettings;
		//check if show new features dialog
		if (ifShowNewFeature()) {
			showNewFeatureDialog();
			return;
		}
		if (appSettings.getSettingBoolean("dcom_is_first_run", true)) {
			AlertDialog.Builder builder = new Builder(this);
			builder.setTitle(R.string.license_title);
			builder.setMessage(Html
					.fromHtml(getString(R.string.license_content)));
			builder.setPositiveButton(R.string.agree,
					new DialogInterface.OnClickListener() {
						@Override
						public void onClick(DialogInterface dialog, int which) {
							setting.setSettingsBoolean("dcom_is_first_run",
									false);
							startLogin();
						}
					});
			builder.setNegativeButton(R.string.disagree,
					new DialogInterface.OnClickListener() {
						@Override
						public void onClick(DialogInterface dialog, int which) {
							finish();
						}
					});
			builder.setOnCancelListener(new DialogInterface.OnCancelListener() {
				@Override
				public void onCancel(DialogInterface dialog) {
					finish();
				}
			});
			builder.create().show();
		} else {

			// we need check whether it is a logout user			
			if (appValues.isDcomDeviceIdEmpty()) {
				startLogin();
			} else {
				if (mRoleVersion == AppValues.ROLE_PRODUCT_VERSION) {
					int server = appValues.getCurrent_server();
					if (server == AppValues.DEV_SERVER
							|| server == AppValues.MY_SERVER) {
						startLogin();
						return;
					}
				}
				NetConncet netConnect = new NetConncet(this,
						NetConstantValues.DEVICE_CHECK_IN.PATH) {
					@Override
					protected void onPostExecute(String result) {
						super.onPostExecute(result);
						try {
							JSONObject jsonObj = new JSONObject(result);
							if (jsonObj.isNull("errno")) {
								login(result);
							} else {
								startLogin();
							}
						} catch (JSONException e) {
							startLogin();
							DocLog.e(TAG, "JSONException", e);
						}
					}

				};
				netConnect.execute();
			}
		}

	}

	void login(String result) throws JSONException {
		JSONObject jsonObj = new JSONObject(result);
		boolean callEnable = jsonObj.getJSONObject("settings").getBoolean(
				"CALL_ENABLE");
		appValues.setCallEnable(callEnable);
		String status = jsonObj.getJSONObject("data").getString("status");
		if (status.equalsIgnoreCase("ok")) {
			AppSettings setting = new AppSettings(this);
			setting.setSettingsBoolean("call_enable", callEnable);
			setting.setSettingsInt("current_version",
					appValues.getCurrent_version());
			Intent intent = new Intent(SplashActivity.this,
					NavigationActivity.class);
			startActivity(intent);
			finish();
		} else {
			startLogin();
		}
	}

	public void startLogin() {
		AppSettings setting = new AppSettings(this);
		setting.setSettingsBoolean("dcom_is_first_run", false);
		Intent intent = new Intent(this, LoginActivity.class);
		startActivity(intent);
		finish();

	}

	public void setLog(int version) {
		if (version == AppValues.ROLE_DEVELOP_VERSION) {
			DocLog.setmLogShowable(true);
		} else {
			DocLog.setmLogShowable(false);
		}
	}

	@Override
	public void onBackPressed() {
	}
}
