package com.doctorcom.physician.activity.setting;

import java.util.HashMap;

import org.json.JSONException;
import org.json.JSONObject;

import android.app.Activity;
import android.app.AlertDialog;
import android.app.ProgressDialog;
import android.content.DialogInterface;
import android.content.Intent;
import android.os.Bundle;
import android.support.v4.content.LocalBroadcastManager;
import android.text.Html;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.TextView;
import android.widget.Toast;

import com.doctorcom.android.R;
import com.doctorcom.physician.AppValues;
import com.doctorcom.physician.net.NetConstantValues;
import com.doctorcom.physician.net.http.NetConncet;
import com.doctorcom.physician.settings.AppSettings;
import com.doctorcom.physician.utils.CallBack;
import com.doctorcom.physician.utils.DocLog;
import com.doctorcom.physician.utils.JsonErrorProcess;
import com.doctorcom.physician.utils.Utils;
import com.doctorcom.physician.utils.cache.CacheService;

public class PhoneInputActivity extends Activity {

	private final String TAG = "PhoneInputActivity";
	private AppValues appValues;
	private boolean validated;
	
	@Override
	protected void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
		setContentView(R.layout.activity_mobilephone_input);
		appValues = new AppValues(this);
		TextView infoTextView = (TextView) findViewById(R.id.tvInfo);
		Button backButton = (Button) findViewById(R.id.btBack);
		validated = getIntent().getBooleanExtra("validated", false);
		if (validated) {
			backButton.setOnClickListener(new View.OnClickListener() {
				
				@Override
				public void onClick(View v) {
					closeActivity();
					
				}
			});
		} else {
			infoTextView.setText(R.string.phone_validate_info);
			backButton.setVisibility(View.GONE);
		}
		final EditText phoneEditText = (EditText) findViewById(R.id.etPhone);
		final String mobilePhone = CallBack.callerNumber;
		if (!mobilePhone.equals("")) {
			phoneEditText.setText(mobilePhone);
			phoneEditText.setSelection(mobilePhone.length());
		}
		
		Button updateButton = (Button) findViewById(R.id.btUpdate);
		updateButton.setOnClickListener(new View.OnClickListener() {
			
			@Override
			public void onClick(View v) {
				final String number = Utils.getNumberOfPhone(phoneEditText.getText().toString().trim());
				if (number.equals("") && appValues.getUserType() == AppValues.PRACTICE_MANAGER) {
					savePhoneNumber(number);
					return;
				}
				if(!Utils.validatePhone(number)) {
					phoneEditText.setError(Html.fromHtml(PhoneInputActivity.this.getResources().getString(R.string.phone_number_warning_html)));
					return;
				}
				if(number.equals(mobilePhone) && validated) {
					phoneEditText.setError(Html.fromHtml(PhoneInputActivity.this.getResources().getString(R.string.cannot_changed)));
					return;
				}
				if (appValues.isCallEnable()) {
					final ProgressDialog progress = ProgressDialog.show(PhoneInputActivity.this, "", getString(R.string.process_text));
					HashMap<String, String> params = new HashMap<String, String>();
					params.put(NetConstantValues.VALIDATIONS.RECIPIENT, number);
					params.put(NetConstantValues.VALIDATIONS.INIT, String.valueOf(true));
					params.put(NetConstantValues.VALIDATIONS.TYPE, String.valueOf(AppValues.MESSAGE_VALIDATE));
					NetConncet netConncet = new NetConncet(PhoneInputActivity.this, NetConstantValues.VALIDATIONS.PATH, params) {

						@Override
						protected void onPostExecute(String result) {
							super.onPostExecute(result);
							progress.dismiss();
							try {
								JSONObject jsonObj = new JSONObject(result);
								if (!jsonObj.isNull("errno")) {
									AlertDialog.Builder builder = new AlertDialog.Builder(PhoneInputActivity.this);
									builder.setTitle(R.string.error)
											.setMessage(jsonObj.getString("descr"))
											.setCancelable(false)
											.setPositiveButton(R.string.ok,
													new DialogInterface.OnClickListener() {
														public void onClick(DialogInterface dialog, int id) {
															dialog.dismiss();
														}
													});
									builder.create().show();
								} else {
									Intent intent = new Intent(PhoneInputActivity.this, PhoneValidateActivity.class);
									intent.putExtra("result", result);
									intent.putExtra("number", number);
									startActivityForResult(intent, 0);
								}
							} catch (JSONException e) {
								Toast.makeText(PhoneInputActivity.this, R.string.error_occur, Toast.LENGTH_LONG).show();
								DocLog.e(TAG, "JSONException", e);
							}
						}

					};
					netConncet.execute();
				} else {
					savePhoneNumber(number);
				}

			}
		});
	}
	
	@Override
	protected void onActivityResult(int requestCode, int resultCode, Intent data) {
		if (resultCode == RESULT_OK) {
			if (requestCode == 0) {
				LocalBroadcastManager.getInstance(this).sendBroadcast(new Intent("newMessageReceiver"));
				finish();
			}
		}
	}
	
	private void savePhoneNumber(final String number) {
		final ProgressDialog progress = ProgressDialog.show(PhoneInputActivity.this, "", getString(R.string.process_text));
		HashMap<String, String> params = new HashMap<String, String>();
		params.put(NetConstantValues.PHONE_NUMBER.MOBILE_PHONE, number);
		NetConncet netConncet = new NetConncet(PhoneInputActivity.this, NetConstantValues.PHONE_NUMBER.UPDATE_PATH, params) {
			@Override
			protected void onPostExecute(String result) {
				super.onPostExecute(result);
				progress.dismiss();
				if (JsonErrorProcess.checkJsonError(result, PhoneInputActivity.this)) {
					Toast.makeText(PhoneInputActivity.this, R.string.action_successed, Toast.LENGTH_SHORT).show();
					CallBack.callerNumber = number;
					if (number == null || number.equals("")) {
						AppSettings setting = new AppSettings(PhoneInputActivity.this);
						setting.setSettingsBoolean("hasMobilePhone", false);
						Intent intent = new Intent(CacheService.CACHE_SERVICE);
						intent.putExtra("cmd", CacheService.UPDATE_CALL_BACK_MESSAGE);
						startService(new Intent(intent));
					}
					finish();
				}
			} 
		};
		netConncet.execute();	
	}

	@Override
	public void onBackPressed() {
		if (validated) {
			super.onBackPressed();
		} else {
			Toast.makeText(this, R.string.phone_validate_info, Toast.LENGTH_SHORT).show();
		}
	}
	
	public void closeActivity() {
		if (validated) {
			finish();
		} else {
			Toast.makeText(this, R.string.phone_validate_info, Toast.LENGTH_SHORT).show();
		}
		
	}

}
