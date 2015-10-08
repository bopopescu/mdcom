package com.doctorcom.physician.activity.more;

import android.app.Activity;
import android.app.AlertDialog;
import android.app.NotificationManager;
import android.app.ProgressDialog;
import android.content.Context;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager.NameNotFoundException;

import com.doctorcom.android.R;
import com.doctorcom.physician.AppValues;
import com.doctorcom.physician.activity.login.LoginActivity;
import com.doctorcom.physician.net.NetConstantValues;
import com.doctorcom.physician.net.http.NetConncet;
import com.doctorcom.physician.settings.AppSettings;
import com.doctorcom.physician.utils.CallBack;
import com.doctorcom.physician.utils.DocLog;
import com.doctorcom.physician.utils.cache.CacheService;
import com.google.android.gcm.GCMRegistrar;

public class CommonMoreMethods {
	private static final String TAG = "CommonMoreMethods";

	public static void logout(final Context context) {
		AlertDialog.Builder builder = new AlertDialog.Builder(context);
		builder.setTitle(R.string.dissociate_warning_title).setMessage(
				R.string.dissociate_warning_message);
		builder.setCancelable(true);
		builder.setNegativeButton(R.string.cancel,
				new DialogInterface.OnClickListener() {
					@Override
					public void onClick(DialogInterface dialog, int which) {
						dialog.dismiss();
					}
				});
		builder.setPositiveButton(R.string.ok,
				new DialogInterface.OnClickListener() {
					@Override
					public void onClick(DialogInterface dialog, int which) {
						dialog.dismiss();
						final ProgressDialog progress = ProgressDialog.show(
								context, "",
								context.getString(R.string.process_text));
						NetConncet netConnect = new NetConncet(context,
								NetConstantValues.DEVICE_DISSOCIATE.PATH) {

							@Override
							protected void onPostExecute(String result) {
								progress.dismiss();
								NotificationManager nm = (NotificationManager) context
										.getSystemService(Context.NOTIFICATION_SERVICE);
								nm.cancel(R.string.app_name);
								AppSettings setting = new AppSettings(context);
								AppValues appValues = new AppValues(context);
								int cv = appValues.getCurrent_version();
								setting.clearPreferences();
								if (!context.stopService(new Intent(
										"com.doctorcom.physician.message"))) {
									GCMRegistrar.unregister(context);
								}
								CallBack.callerNumber = null;
								Intent intent = new Intent(
										CacheService.CACHE_SERVICE);
								intent.putExtra("cmd", CacheService.CACHE_CLEAN);
								context.startService(intent);
								appValues.setCurrent_version(cv);
								appValues.setDcomDeviceId("");
								appValues.setLogined(false);
								setting.setSettingsBoolean("dcom_is_first_run",
										false);
								appValues.setEncrypted(true);
								setNewFeatureConfig(context);
								((Activity) context)
										.setResult(Activity.RESULT_OK);
								((Activity) context).finish();
								((Activity) context).startActivity(new Intent(
										context, LoginActivity.class)
										.setFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP));
							}
						};
						netConnect.execute();

					}
				});
		builder.show();
	}
	public static void setNewFeatureConfig(Context context){
		AppSettings appSettings = new AppSettings(context);
		appSettings.setSettingsBoolean(
				"is_new_feature_show", true);
		PackageInfo info = null;
		try {
			info = context.getPackageManager().getPackageInfo(context.getPackageName(), 0);
		} catch (NameNotFoundException e1) {
			try {
				info = context.getPackageManager().getPackageInfo(context.getPackageName(), 0);
			} catch (NameNotFoundException e) {
				// TODO Auto-generated catch block
				DocLog.e(TAG, "Get version name error", e);
			}
		}
		if(info != null)
			appSettings.setSettingsString(
				"feature_version_name",info.versionName);
	}
}


