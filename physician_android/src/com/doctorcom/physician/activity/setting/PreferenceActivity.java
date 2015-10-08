package com.doctorcom.physician.activity.setting;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import android.app.Activity;
import android.app.AlertDialog;
import android.app.ProgressDialog;
import android.content.DialogInterface;
import android.content.Intent;
import android.os.Bundle;
import android.support.v4.content.LocalBroadcastManager;
import android.view.View;
import android.widget.ArrayAdapter;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.RadioGroup;
import android.widget.Spinner;
import android.widget.Toast;

import com.doctorcom.android.R;
import com.doctorcom.physician.AppValues;
import com.doctorcom.physician.net.NetConstantValues;
import com.doctorcom.physician.net.NetConstantValues.PREFERENCE;
import com.doctorcom.physician.net.http.NetConncet;
import com.doctorcom.physician.utils.DocLog;
import com.doctorcom.physician.utils.JsonErrorProcess;
import com.doctorcom.physician.utils.cache.Cache;

public class PreferenceActivity extends Activity implements Cache.CacheFinishListener {
	private String TAG = "PreferenceActivity";
	private String practiceTimezone, timezone;
	private boolean hasCache = false;
	private RadioGroup groupRadioGroup;
	private Spinner timezoneSpinner;
	private LinearLayout contentLinearLayout;
	private FrameLayout loadingFrameLayout;
	private List<String> timeZoneIds;
	private List<String> timeZoneValues;
	protected ProgressDialog progress;
	
	@Override
	protected void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
		setContentView(R.layout.activity_preference);
		timezoneSpinner = (Spinner) findViewById(R.id.spn_timezone);
		groupRadioGroup = (RadioGroup) findViewById(R.id.radiogroup_timeformat);
		contentLinearLayout = (LinearLayout) findViewById(R.id.llContent);
		loadingFrameLayout = (FrameLayout) findViewById(R.id.frame_loading);
		contentLinearLayout.setVisibility(View.GONE);
		timeZoneIds = new ArrayList<String>();
		timeZoneValues = new ArrayList<String>();
		getPreference();
	}

	public void onBack(View v) {
		finish();
	}
	
	protected void getPreference() {
		Cache cache = new Cache(this, NetConncet.HTTP_GET);
		cache.useCache(this, PREFERENCE.PATH, null, null);
		
	}
	
	public void onSave(View v) {
		String settingTimezone = timeZoneIds.get(timezoneSpinner.getSelectedItemPosition());
		if ("".equals(settingTimezone) || "".equals(practiceTimezone) || settingTimezone.equalsIgnoreCase(practiceTimezone) || settingTimezone.equals(timezone)) {
			setTime();
		} else {
			AlertDialog.Builder builder= new AlertDialog.Builder(this);
			builder.setTitle(R.string.warning_title).setMessage(R.string.change_timezone_warning)
			.setPositiveButton(R.string.ok, new DialogInterface.OnClickListener() {

				@Override
				public void onClick(DialogInterface dialog, int which) {
					setTime();
				}
				
			})
			.setNegativeButton(R.string.cancel, new DialogInterface.OnClickListener() {

				@Override
				public void onClick(DialogInterface dialog, int which) {
					dialog.dismiss();
					
				}
				
			});
			builder.show();
		}
	}
	
	protected void setTime() {
		progress = ProgressDialog.show(this, "", getString(R.string.process_text));
		final Map<String, String> params = new HashMap<String, String>();
		String value = timeZoneIds.get(timezoneSpinner.getSelectedItemPosition());
		switch (groupRadioGroup.getCheckedRadioButtonId()) {
		case R.id.radio_12h:
			params.put(NetConstantValues.PREFERENCE.PARAM_TIME_SETTING, String.valueOf(AppValues.USE_12HOUR));
			break;
		case R.id.radio_24h:
			params.put(NetConstantValues.PREFERENCE.PARAM_TIME_SETTING, String.valueOf(AppValues.USE_24HOUR));
			break;
		}
		params.put(NetConstantValues.PREFERENCE.PARAM_TIME_ZONE, value);
		NetConncet netConncet = new NetConncet(this, NetConstantValues.PREFERENCE.PATH, params) {

			@Override
			protected void onPostExecute(String result) {
				super.onPostExecute(result);
				progress.dismiss();
				if (JsonErrorProcess.checkJsonError(result, PreferenceActivity.this)) {
					Toast.makeText(PreferenceActivity.this, R.string.action_successed, Toast.LENGTH_LONG).show();
					Cache.cleanListCache(String.valueOf(Cache.CACHE_OTHER), PREFERENCE.PATH, PreferenceActivity.this.getApplicationContext());
					LocalBroadcastManager broadcastManager = LocalBroadcastManager.getInstance(PreferenceActivity.this);
					Intent i = new Intent("refreshAction");
					i.putExtra("cmd", 4);
					broadcastManager.sendBroadcast(i);
					finish();
				}
			}
			
		};
		netConncet.execute();
	}

	protected void setCurrentTimeFormat(int format) {
		switch(format) {
			case AppValues.USE_24HOUR:
				groupRadioGroup.check(R.id.radio_24h);
				break;
			case AppValues.USE_12HOUR:
				groupRadioGroup.check(R.id.radio_12h);
				break;
		}
	}
	
	protected void setCurrentTimeZone(String id) {
		int position = -1;
		for (int i = 0, len = timeZoneIds.size(); i < len; i++) {
			String timezone = timeZoneIds.get(i);
			if (timezone.equals(id)) {
				position = i;
				break;
			}
		}
		timezoneSpinner.setSelection(position, true);
	}
	
	protected void setTimeZones(List<String> ids) {
		ArrayAdapter<String> adapter = new ArrayAdapter<String>(this, R.layout.custom_simple_spinner_item , android.R.id.text1, ids);
		adapter.setDropDownViewResource(R.layout.custom_simple_spinner_dropdown_item);
		timezoneSpinner.setAdapter(adapter);
	}
	
	@Override
	public void onCacheFinish(String result, boolean isCache) {
		loadingFrameLayout.setVisibility(View.GONE);
		contentLinearLayout.setVisibility(View.VISIBLE);
		if (isCache) {
			hasCache = true;
		}
		try {
			JSONObject jsonObj = new JSONObject(result);
			if (jsonObj.isNull("errno")) {
				JSONObject jData = jsonObj.getJSONObject("data");
				JSONArray timeZoneOptions = jData.getJSONArray("time_zone_options");
				int length = timeZoneOptions.length();
				timeZoneIds.clear();
				timeZoneValues.clear();
				for (int i = 0; i < length; i++) {
					JSONArray jsonArray = timeZoneOptions.getJSONArray(i);
					String key = jsonArray.getString(0);
					String value = jsonArray.getString(1);
					timeZoneIds.add(key);
					timeZoneValues.add(value);
				}
				setTimeZones(timeZoneValues);
				timezone = jData.getString("user_time_zone");
				int timeformat = jData.getInt("time_setting");
				practiceTimezone = jData.getString("practice_time_zone");
				setCurrentTimeFormat(timeformat);
				setCurrentTimeZone(timezone);
			} else {
				Toast.makeText(this, jsonObj.getString("descr"), Toast.LENGTH_LONG).show();
				if (!hasCache) {
					finish();
				}
			}
		} catch (JSONException e) {
			Toast.makeText(this, R.string.error_occur, Toast.LENGTH_LONG).show();
			DocLog.e(TAG, "JSONException e", e);
			if (!hasCache) {
				finish();
			}
		}
		
	}
}
