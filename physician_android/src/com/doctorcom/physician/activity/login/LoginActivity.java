package com.doctorcom.physician.activity.login;

import java.util.HashMap;
import java.util.Locale;
import java.util.Map;
import java.util.Timer;
import java.util.TimerTask;

import org.json.JSONException;
import org.json.JSONObject;

import android.app.Activity;
import android.app.ProgressDialog;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.SharedPreferences.Editor;
import android.os.Bundle;
import android.provider.Settings.Secure;
import android.text.Editable;
import android.text.Html;
import android.text.TextWatcher;
import android.view.View;
import android.view.inputmethod.InputMethodManager;
import android.widget.AdapterView;
import android.widget.ArrayAdapter;
import android.widget.EditText;
import android.widget.Spinner;
import android.widget.Toast;

import com.doctorcom.android.R;
import com.doctorcom.physician.AppValues;
import com.doctorcom.physician.activity.main.NavigationActivity;
import com.doctorcom.physician.net.NetConstantValues;
import com.doctorcom.physician.net.http.NetConncet;
import com.doctorcom.physician.settings.AppSettings;
import com.doctorcom.physician.settings.Preference;
import com.doctorcom.physician.utils.CallBack;
import com.doctorcom.physician.utils.DocLog;
import com.doctorcom.physician.utils.Utils;

public class LoginActivity extends Activity {

	private String TAG = "LoginActivity";
	public static final int USER_NAME_CANNOT_EMPTY = 0x01;
	public static final int PASSWORD_CANNOT_EMPTY = 0x01 << 1;
	public static final int INVALID_URL_OR_IP = 0x01 << 2;
	public static final int CORRECT_INPUT = 0x01 << 3;

	protected ProgressDialog progress;
	private AppValues appValues;
	private Preference prdfterence;
	private Spinner spinner;
	private EditText myServerEditText;
	private int bottom, top, right, left;
	private boolean clickLogin;

	@Override
	protected void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
		setContentView(R.layout.activity_login);
		Timer timer = new Timer();
		timer.schedule(new TimerTask() {
			@Override
			public void run() {
				((InputMethodManager) getSystemService(INPUT_METHOD_SERVICE))
						.toggleSoftInput(0, InputMethodManager.HIDE_NOT_ALWAYS);
			}

		}, 1000);
		appValues = new AppValues(this);
		prdfterence = new Preference(this);
		spinner = (Spinner) findViewById(R.id.spn_server_select);
		myServerEditText = (EditText) findViewById(R.id.edit_my_server);
		myServerEditText.setVisibility(View.GONE);
		bottom = myServerEditText.getPaddingBottom();
		top = myServerEditText.getPaddingTop();
		right = myServerEditText.getPaddingRight();
		left = myServerEditText.getPaddingLeft();
		ArrayAdapter<CharSequence> adapter;
		clickLogin = false;
		int mRoleVersion = appValues.getCurrent_version();
		if (mRoleVersion == AppValues.ROLE_DEVELOP_VERSION) {
			adapter = ArrayAdapter.createFromResource(this,
					R.array.select_server_dev,
					R.layout.custom_simple_spinner_item);
		} else {
			adapter = ArrayAdapter.createFromResource(this,
					R.array.select_server, R.layout.custom_simple_spinner_item);
		}
		adapter.setDropDownViewResource(R.layout.custom_simple_spinner_dropdown_item);
		spinner.setAdapter(adapter);
		if (mRoleVersion == AppValues.ROLE_DEVELOP_VERSION) {
			spinner.setSelection(AppValues.DEV_SERVER);
		} else {
			if (Locale.getDefault().getLanguage().contains("de")) {
				spinner.setSelection(AppValues.DE_SERVER);
			} else {
				spinner.setSelection(AppValues.ENGLISH_SERVER);
			}
		}

		TextWatcher textWatcher = new TextWatcher() {

			@Override
			public void onTextChanged(CharSequence s, int start, int before,
					int count) {
				myServerEditText.setBackgroundResource(R.drawable.login_input);
				myServerEditText.setPadding(left, top, right, bottom);

			}

			@Override
			public void beforeTextChanged(CharSequence s, int start, int count,
					int after) {

			}

			@Override
			public void afterTextChanged(Editable s) {

			}
		};
		myServerEditText.addTextChangedListener(textWatcher);
		spinner.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener() {

			@Override
			public void onItemSelected(AdapterView<?> parent, View view,
					int position, long id) {
				if (position == AppValues.MY_SERVER) {
					myServerEditText.setVisibility(View.VISIBLE);
					myServerEditText
							.setBackgroundResource(R.drawable.login_input);
					myServerEditText.setPadding(left, top, right, bottom);
					myServerEditText.setText(prdfterence.getSettingString(
							"my_server", ""));
					myServerEditText.requestFocus();
					myServerEditText.setSelection(myServerEditText.getText()
							.toString().length());
				} else {
					myServerEditText.setVisibility(View.GONE);
				}

			}

			@Override
			public void onNothingSelected(AdapterView<?> parent) {
				// nothing to do

			}
		});

	}

	// When click login button
	public void login(View v) {
		if (clickLogin) {
			return;
		}
		clickLogin = true;
		final EditText userEdit = (EditText) findViewById(R.id.user);
		final EditText passwordEdit = (EditText) findViewById(R.id.password);
		switch (checkData(userEdit.getText().toString(), passwordEdit.getText()
				.toString())) {
		case USER_NAME_CANNOT_EMPTY:
			userEdit.setError(Html
					.fromHtml(getString(R.string.cannot_be_empty)));
			clickLogin = false;
			break;
		case PASSWORD_CANNOT_EMPTY:
			passwordEdit.setError(Html
					.fromHtml(getString(R.string.cannot_be_empty)));
			clickLogin = false;
			break;
		case INVALID_URL_OR_IP:
			Toast.makeText(this, R.string.invalid_url, Toast.LENGTH_LONG)
					.show();
			clickLogin = false;
			break;
		case CORRECT_INPUT:
			appValues.setCurrent_server(spinner.getSelectedItemPosition());
			associate(userEdit.getText().toString().trim(), passwordEdit
					.getText().toString().trim());
			break;
		}
	}

	public int checkData(String user, String password) {
		if (user == null || user.trim().equals("")) {
			return USER_NAME_CANNOT_EMPTY;
		} else if (password == null || password.trim().equals("")) {
			return PASSWORD_CANNOT_EMPTY;
		} else {
			if (spinner.getSelectedItemPosition() == AppValues.MY_SERVER) {
				String input = myServerEditText.getText().toString();
				String url = input.trim().toLowerCase(Locale.US);
				if (url.endsWith("/")) {
					url = url.substring(0, url.length() - 1);
				}
				if (!(url.startsWith("http://") || url.startsWith("https://"))) {
					url = "https://" + url;
				}
				if (Utils.validateURLIP(url)) {
					appValues.setServerURL(input);
					return CORRECT_INPUT;
				} else {
					myServerEditText.requestFocus();
					myServerEditText
							.setBackgroundResource(R.drawable.login_input_red);
					myServerEditText.setPadding(left, top, right, bottom);
					return INVALID_URL_OR_IP;
				}
			} else {
				return CORRECT_INPUT;
			}
		}
	}

	public void associate(String username, String password) {

		final Map<String, String> params = new HashMap<String, String>();
		params.put(NetConstantValues.DEVICE_ASSOCIATE.PARAM_USERNAME, username);
		params.put(NetConstantValues.DEVICE_ASSOCIATE.PARAM_PASSWORD, password);
		params.put(NetConstantValues.DEVICE_ASSOCIATE.PARAM_APP_VERSION,
				Utils.getVersion(this));
		params.put(NetConstantValues.DEVICE_ASSOCIATE.PARAM_PLATFORM,
				AppValues.PLATFORM);
		params.put(NetConstantValues.DEVICE_ASSOCIATE.PARAM_ALLOW_STAFF_LOGIN,
				String.valueOf(true));
		String id = Secure.getString(getContentResolver(), Secure.ANDROID_ID);
		if (id == null || "".equals(id)) {
			id = "no_device_id";
		}
		params.put(NetConstantValues.DEVICE_ASSOCIATE.PARAM_DEVICE_ID, id);
		final NetConncet connect = new NetConncet(this,
				NetConstantValues.DEVICE_ASSOCIATE.PATH, params) {
			// Begin to associate
			@Override
			protected void onPostExecute(String result) {
				clickLogin = false;
				progress.dismiss();
				try {
					JSONObject jsonObj = new JSONObject(result);
					if (!jsonObj.isNull("errno")) {
						Toast.makeText(context, jsonObj.getString("descr"),
								Toast.LENGTH_LONG).show();
					} else {
						JSONObject obj = jsonObj.getJSONObject("data");
						JSONObject settings = jsonObj.getJSONObject("settings");
						boolean callEnable = settings.getBoolean("CALL_ENABLE");
						if (!settings.isNull("prefer_logo")) {
							String preferLogoPath = settings
									.getString("prefer_logo");
							appValues.setPreferLogoPath(preferLogoPath);
							preferLogoPath = appValues.getPreferLogoPath();
							DocLog.i(TAG, "current prefer logo path is:"
									+ preferLogoPath);
						}

						appValues.setCallEnable(callEnable);
						boolean callAvailable = false;
						if (obj.has("call_available")) {
							callAvailable = obj.getBoolean("call_available");
						}
						appValues.setCallAvailable(callAvailable);
						String projectId = "";
						if (obj.has("gcm_project_id")) {
							projectId = obj.getString("gcm_project_id");
							appValues.setProjectId(projectId);
						}
						String dcomDeviceId = obj.getString("mdcom_id");
						appValues.setDcomDeviceId(dcomDeviceId);
						String secret = obj.getString("secret");
						appValues.setSecret(secret);
						int userType = AppValues.PROVIDER;
						if (obj.isNull("user_type")) {
							appValues.setUserType(userType);
						} else {
							userType = obj.getInt("user_type");
							appValues.setUserType(userType);
						}
						String mdcomNumber = obj.getString("mdcom_number");
						appValues.setMdcomNumber(mdcomNumber);
						AppSettings setting = new AppSettings(
								LoginActivity.this);
						String callNumber = "";
						if (obj.has("mobile_phone")) {
							callNumber = obj.getString("mobile_phone");
						}
						if (callNumber == null || callNumber.equals("")) {
							setting.setSettingsBoolean("hasMobilePhone", false);
						} else {
							setting.setSettingsBoolean("hasMobilePhone", true);
						}
						CallBack.callerNumber = callNumber;
						// save user info
//						setting.setSettingsString(AppValues.DCOM_DEVICE_ID,
//								dcomDeviceId);
						appValues.setDcomDeviceId(dcomDeviceId);
//						setting.setSettingsString("dcom_secret", secret);
						appValues.setSecret(secret);
						setting.setSettingsInt("user_type", userType);
						setting.setSettingsString("dcom_number", mdcomNumber);
						SharedPreferences share = context.getSharedPreferences(
								"com.google.android.gcm", Context.MODE_PRIVATE);
						Editor edit = share.edit();
						edit.putString("projectId", projectId).commit();
						setting.setSettingsString("gcm", projectId);
						setting.setSettingsBoolean("call_enable", callEnable);
						setting.setSettingsBoolean("call_available",
								callAvailable);
						appValues.setLogined(true);
						appValues.setShowPreferLogo(true);
						startNavigation();
					}
				} catch (JSONException e) {
					DocLog.e(TAG, "onPostExecute JSONException", e);
					Toast.makeText(LoginActivity.this,
							R.string.not_valid_server, Toast.LENGTH_LONG)
							.show();
				}
			}

		};
		progress = ProgressDialog.show(this, "",
				getString(R.string.process_text));

		connect.execute();

	}

	@Override
	protected void onActivityResult(int requestCode, int resultCode, Intent data) {
		if (resultCode == RESULT_CANCELED) {
			if (requestCode == 0) {
				finish();
			}
		}
	}

	public void startNavigation() {
		Intent intent = new Intent(LoginActivity.this, NavigationActivity.class);
		startActivityForResult(intent, 0);
		// finish();

	}
}