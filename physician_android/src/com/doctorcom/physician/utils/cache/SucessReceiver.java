package com.doctorcom.physician.utils.cache;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.widget.Toast;

import com.doctorcom.android.R;

public class SucessReceiver extends BroadcastReceiver {

	@Override
	public void onReceive(Context context, Intent intent) {
		Toast.makeText(context, R.string.clean_cache_suceffuly, Toast.LENGTH_LONG).show();

	}

}
