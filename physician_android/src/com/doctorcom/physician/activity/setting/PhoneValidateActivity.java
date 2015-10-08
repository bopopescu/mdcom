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
import android.os.Handler;
import android.text.Html;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ImageView;
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
import com.doctorcom.physician.utils.PreferLogo;
import com.doctorcom.physician.utils.cache.CacheService;

public class PhoneValidateActivity extends Activity {
	private final String TAG = "PhoneValidateActivity";
	private int send_waiting_time, send_remain_count,
			settings_send_code_waiting_time, settings_validate_lock_time;
	private boolean validate_locked, has_code;
	private Button resendButton, submitButton;
	private TextView  resendInfoTextView, validateInfoTextView;
	private String number = "";
	private ImageView ivPreferLogoImageView;
	
	@Override
	protected void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
		setContentView(R.layout.activity_mobilephone_validate);
		ivPreferLogoImageView = (ImageView)findViewById(R.id.ivPreferLogo);
		PreferLogo.showPreferLogo(this, ivPreferLogoImageView);
		resendInfoTextView = (TextView)findViewById(R.id.tvResendInfo);
		validateInfoTextView = (TextView)findViewById(R.id.tvValidateInfo);
		resendButton = (Button)findViewById(R.id.btResend);
		submitButton = (Button)findViewById(R.id.btSubmit);
		setParameter(getIntent().getStringExtra("result"));
		
		Button backButton = (Button) findViewById(R.id.btBack);
		backButton.setOnClickListener(new View.OnClickListener() {
			
			@Override
			public void onClick(View v) {
				finish();
				
			}
		});
		number = getIntent().getStringExtra("number");
		submitButton.setOnClickListener(new Submit());
		resendButton.setOnClickListener(new Resend());
	}
	
	class Resend implements View.OnClickListener {

		@Override
		public void onClick(final View v) {
			final ProgressDialog progress = ProgressDialog.show(PhoneValidateActivity.this, "", getString(R.string.process_text));
			HashMap<String, String> params = new HashMap<String, String>();
			params.put(NetConstantValues.VALIDATIONS.RECIPIENT, number);
			params.put(NetConstantValues.VALIDATIONS.INIT, String.valueOf(false));
			params.put(NetConstantValues.VALIDATIONS.TYPE, String.valueOf(AppValues.MESSAGE_VALIDATE));
			NetConncet netConncet = new NetConncet(PhoneValidateActivity.this, NetConstantValues.VALIDATIONS.PATH, params) {
				@Override
				protected void onPostExecute(String result) {
					super.onPostExecute(result);
					if (setParameter(result)) {
						Toast.makeText(PhoneValidateActivity.this, R.string.resend_new_code, Toast.LENGTH_LONG).show();
						v.setEnabled(false);
					}
					progress.dismiss();
				} 
			};

			netConncet.execute();
		}
		
	}
	
	class Submit implements View.OnClickListener {

		@Override
		public void onClick(View v) {
			EditText pinCodeEditText = (EditText)findViewById(R.id.etPinCode);
			String pin = pinCodeEditText.getText().toString();
			if(pin.equals("")) {
				pinCodeEditText.setError(Html.fromHtml(PhoneValidateActivity.this.getString(R.string.cannot_be_empty)));
				return;
			}
			
			final ProgressDialog progress = ProgressDialog.show(PhoneValidateActivity.this, "", getString(R.string.process_text));
			HashMap<String, String> params = new HashMap<String, String>();
			params.put(NetConstantValues.VALIDATIONS.RECIPIENT, number);
			params.put(NetConstantValues.VALIDATIONS.CODE, pin);
			params.put(NetConstantValues.VALIDATIONS.TYPE, String.valueOf(AppValues.MESSAGE_VALIDATE));
			NetConncet netConncet = new NetConncet(PhoneValidateActivity.this, NetConstantValues.VALIDATIONS.VALIDATIONS_PATH, params) {
				@Override
				protected void onPostExecute(String result) {
					super.onPostExecute(result);
					progress.dismiss();
					if (!JsonErrorProcess.checkJsonError(result, PhoneValidateActivity.this)) {
						return;
					}
					try {
						JSONObject jsonObj = new JSONObject(result);
						JSONObject data = jsonObj.getJSONObject("data");
						int flag = data.getInt("flag");
						int settings_validate_lock_time = data.getInt("settings_validate_lock_time");
						AlertDialog.Builder builder = new AlertDialog.Builder(PhoneValidateActivity.this);
						builder.setTitle(R.string.error).setCancelable(false).setPositiveButton(
								R.string.ok,
								new DialogInterface.OnClickListener() {
									public void onClick(DialogInterface dialog, int id) {
										dialog.cancel();

									}
								});
						switch (flag) {
						case 0:
							Toast.makeText(PhoneValidateActivity.this, R.string.action_successed, Toast.LENGTH_LONG).show();
							Intent intent = new Intent();
							CallBack.callerNumber = number;
							AppSettings setting = new AppSettings(PhoneValidateActivity.this);
							setting.setSettingsBoolean("hasMobilePhone", true);
							setResult(RESULT_OK, intent);
							Intent i = new Intent(CacheService.CACHE_SERVICE);
							i.putExtra("cmd", CacheService.UPDATE_CALL_BACK_MESSAGE);
							startService(new Intent(i));
							finish();
							break;
						case 1:
							builder.setMessage(R.string.validate_1).create().show();
							break;
						case 2:
							builder.setMessage(R.string.validate_2).create().show();
							break;
						case 3:
							String errInfo;
							if (send_remain_count <= 0) {
								errInfo = String.format(PhoneValidateActivity.this.getString(R.string.validate_3_5), settings_validate_lock_time);
							} else {
								errInfo = String.format(PhoneValidateActivity.this.getString(R.string.validate_3), settings_validate_lock_time);
							}
							builder.setMessage(errInfo).create().show();
							submitButton.setEnabled(false);
							break;
						case 4:
							builder.setMessage(R.string.validate_4).create().show();
							break;
						}
					} catch (JSONException e) {							
						DocLog.e(TAG, "JSONException" , e);
					}
				} 
			};

			netConncet.execute();					
		}
		
	}

	private boolean setParameter(String result) {
		boolean r = false;
		try {
			final JSONObject jsonObj = new JSONObject(result);
			JSONObject data = jsonObj.getJSONObject("data");
			send_remain_count = data.getInt("send_remain_count");
			validate_locked = data.getBoolean("validate_locked");
			settings_send_code_waiting_time = data.getInt("settings_send_code_waiting_time");
			has_code = data.getBoolean("has_code");
			send_waiting_time = data.getInt("send_waiting_time");
			settings_validate_lock_time = data.getInt("settings_validate_lock_time");
			// set views
			//If you did not receive that message in %d minute(s),please click resend button.
			resendInfoTextView.setText(String.format(getResources().getString(R.string.code_resend_info), settings_send_code_waiting_time));
			if(send_waiting_time > 0) {
				resendButton.setText(getString(R.string.resend) + "(" + getTime(send_waiting_time--) + ")");
				handler.post(runnable);
			} else {
				if(send_remain_count <= 0) {
					validateInfoTextView.setText(R.string.cannot_new_code);
					resendInfoTextView.setVisibility(View.GONE);
					resendButton.setVisibility(View.GONE);
				} else {
					resendButton.setEnabled(true);
				}
			}
			if(has_code == false || validate_locked) {
				submitButton.setEnabled(false);
			}
			if (validate_locked) {
				String errInfo;
				if(send_remain_count <= 0) {
					errInfo = String.format(getString(R.string.validate_3_5), settings_validate_lock_time);
				} else {
					errInfo = String.format(getString(R.string.validate_3), settings_validate_lock_time);
				}
				AlertDialog.Builder builder = new AlertDialog.Builder(this);
				builder.setTitle(R.string.error)
						.setMessage(errInfo)
						.setCancelable(false)
						.setPositiveButton(R.string.ok, new DialogInterface.OnClickListener() {
									public void onClick(DialogInterface dialog, int id) {
										dialog.cancel();

									}
				       });
				builder.create().show();
				
			}
			r = true;
			
		} catch (JSONException e) {
			Toast.makeText(this, R.string.system_request_error, Toast.LENGTH_LONG).show();
			DocLog.e(TAG, "JSONException", e);
		}
		return r;

	}
	
	Handler handler = new Handler();
	Runnable runnable = new Runnable() {

		@Override
		public void run() {
			if(send_waiting_time <= 0) {
				resendButton.setText(getString(R.string.resend));
				if (send_remain_count <= 0) {
					validateInfoTextView.setText(R.string.cannot_new_code);
				} else {
					resendButton.setEnabled(true);
				}
			} else {
				resendButton.setText(getString(R.string.resend) + "(" + getTime(send_waiting_time--) + ")");
				handler.postDelayed(this, 1000);						
			}
		}
		
	};

	public String getTime(int a) {
		if(a ==0) return "";
		int h = 0;
		int m = 0;
		int s = 0;
		String hh = "";
		String mm = "";
		String ss = "";
		h = a / 3600;
		m = (a - h * 3600) / 60;
		s = a - (h * 3600) - (m * 60);
		if (h < 10) {
			hh = "0" + h;
		} else {
			hh = h + "";
		}
		if (m < 10) {
			mm = "0" + m;
		} else {
			mm = m + "";
		}
		if (s < 10) {
			ss = "0" + s;
		} else {
			ss = s + "";
		}
		if (hh.equals("00")) {
			return mm + ":" + ss;
		} else {
			return hh + ":" + mm + ":" + ss;
		}
	}

}
