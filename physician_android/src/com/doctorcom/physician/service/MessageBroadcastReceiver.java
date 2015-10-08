package com.doctorcom.physician.service;

import android.accounts.Account;
import android.accounts.AccountManager;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

import com.doctorcom.physician.utils.DocLog;
import com.google.android.gcm.GCMRegistrar;

public class MessageBroadcastReceiver extends BroadcastReceiver {
	private static final String ACTION = Intent.ACTION_BOOT_COMPLETED;
	private static final String TAG = "MessageBroadcastReceiver";

	@Override
	public void onReceive(Context context, Intent intent) {
		if (intent.getAction().equals(ACTION)) {
			DocLog.d(TAG, "intent Action = " + intent.getAction());
			try {
				GCMRegistrar.checkDevice(context);
			} catch (UnsupportedOperationException e) {
				Intent i = new Intent("com.doctorcom.physician.message");
				context.startService(i);
				return;
			}
			int level = android.os.Build.VERSION.SDK_INT;
			if (level < 16 && level >= 8) {
				AccountManager accountManager = AccountManager.get(context);
				Account[] account = accountManager.getAccountsByType("com.google");
				if (account == null || account.length <= 0) {
					Intent i = new Intent("com.doctorcom.physician.message");
					context.startService(i);
				}
			}
		}

	}
}
