package com.doctorcom.physician.settings;

import android.content.Context;
import android.content.SharedPreferences;
import android.content.SharedPreferences.Editor;

public class Preference {
	Context context;
	SharedPreferences share;
	
	public Preference(Context context) {
		this.context = context;
		share = context.getSharedPreferences("prdfterence", Context.MODE_PRIVATE);
	}

	public boolean setSettingsString(String key, String value) {
		Editor edit = share.edit();
		return edit.putString(key, value).commit();
	}
	
	public boolean setSettingsInt(String key, int value) {
		Editor edit = share.edit();
		return edit.putInt(key, value).commit();
	}
	
	public boolean setSettingsBoolean(String key, boolean value) {
		Editor edit = share.edit();
		return edit.putBoolean(key, value).commit();
	}
	
	public String getSettingString(String key, String defValue) {
		return share.getString(key, defValue);
	}
	
	public int getSettingInt(String key, int defValue) {
		return share.getInt(key, defValue);
	}
	
	public boolean getSettingBoolean(String key, boolean defValue) {
		return share.getBoolean(key, defValue);
	}
	
	public void clearPreferences() {
		share.edit().clear().commit();
	}
}
