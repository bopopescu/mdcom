package com.doctorcom.physician.activity.setting;

import android.app.ListActivity;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ListView;
import android.widget.TextView;

import com.doctorcom.android.R;
import com.doctorcom.physician.AppValues;
import com.doctorcom.physician.utils.PreferLogo;
import com.doctorcom.physician.utils.cache.Cache;

public abstract class OptionalActivity extends  ListActivity implements Cache.CacheFinishListener  {

	protected ListView mListView;
	private LinearLayout llContent, llLoading;
	protected TextView titleTextView;
	public AppValues appValues;
	private ImageView ivPreferLogoImageView;

	@Override
	protected void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
		setContentView(R.layout.activity_spca_list);
		ivPreferLogoImageView = (ImageView)findViewById(R.id.ivPreferLogo);
		PreferLogo.showPreferLogo(this, ivPreferLogoImageView);
		mListView = getListView();
		appValues = new AppValues(this);
		titleTextView = (TextView) findViewById(R.id.tvTitle);
		llContent = (LinearLayout) findViewById(R.id.llContent);
		llLoading = (LinearLayout) findViewById(R.id.llLoading);
		llLoading.setVisibility(View.VISIBLE);
		llContent.setVisibility(View.GONE);

		Button backButton = (Button) findViewById(R.id.btBack);
		backButton.setOnClickListener(new View.OnClickListener() {
			
			@Override
			public void onClick(View v) {
				finish();
				
			}
		});
		
	}
	
	@Override
	public void onCacheFinish(String result, boolean updated) {
		llLoading.setVisibility(View.GONE);
		llContent.setVisibility(View.VISIBLE);
	}
}
