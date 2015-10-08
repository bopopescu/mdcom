package com.doctorcom.physician.utils;

import android.content.Context;
import android.view.View;
import android.widget.ImageView;

import com.doctorcom.android.R;
import com.doctorcom.physician.AppValues;
import com.doctorcom.physician.net.ImageDownload;

public class PreferLogo {
	public static void showPreferLogo(Context context, ImageView image){
		AppValues appValues = new AppValues(context);
		String preferLogoPath = appValues.getPreferLogoPath();
		if ("".equals(preferLogoPath)) {
			image.setVisibility(View.INVISIBLE);
		} else {
			ImageDownload download = new ImageDownload(
					context, AppValues.PREFER_LOGO,
					image,
					R.drawable.avatar_male_small);
			download.execute(appValues.getServerURL()
					+ preferLogoPath);
			image.setVisibility(View.VISIBLE);
		}
	}
}
