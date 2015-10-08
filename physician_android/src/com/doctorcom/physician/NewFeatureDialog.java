package com.doctorcom.physician;

import com.doctorcom.android.R;
import com.doctorcom.physician.settings.AppSettings;
import com.doctorcom.physician.utils.DocLog;
import com.doctorcom.physician.PageControlView;

import android.app.Activity;
import android.content.Intent;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager.NameNotFoundException;
import android.os.Bundle;
import android.view.View;
import android.view.View.OnClickListener;
import android.widget.Button;
import android.widget.ImageView;

public class NewFeatureDialog extends Activity {

	private static final String TAG = "NewFeatureDialog";

	@Override
	protected void onCreate(Bundle savedInstanceState) {
		// TODO Auto-generated method stub
		super.onCreate(savedInstanceState);
		this.setContentView(R.layout.new_feature_dialog);
		ScrollView sv = (ScrollView) findViewById(R.id.scroll);
		
		
		ImageView iv = new ImageView(this);
		iv.setScaleType(ImageView.ScaleType.CENTER);
		iv.setBackgroundResource(R.color.black);
		iv.setImageDrawable(getResources().getDrawable(R.drawable.wizard_mobile_01));
		sv.addView(iv);
		
		ImageView iv2 = new ImageView(this);
		iv2.setScaleType(ImageView.ScaleType.CENTER_INSIDE);
		iv2.setBackgroundResource(R.color.black);
		iv2.setImageDrawable(getResources().getDrawable(R.drawable.wizard_mobile_02));
		sv.addView(iv2);
		
		View iv3 = View.inflate(this, R.layout.new_feature_dialog_end, null);
		Button finishButton = (Button) iv3.findViewById(R.id.btFinish);
		finishButton.setOnClickListener(new OnClickListener(){

			@Override
			public void onClick(View arg0) {
				// TODO Auto-generated method stub
				Intent intent = new Intent(NewFeatureDialog.this, SplashActivity.class);
				startActivity(intent);
				finish();
			}
			
		});
		sv.addView(iv3);
		
		
		PageControlView pageControl = (PageControlView)findViewById(R.id.pageControl);
		pageControl.setMscrollView(sv);
        sv.setOnScreenChangeListener(pageControl);
         
        sv.initPageControlView();
		setNewFeatureConfig();
	}
	
	private void setNewFeatureConfig(){
		AppSettings appSettings = new AppSettings(this);
		appSettings.setSettingsBoolean(
				"is_new_feature_show", true);
		PackageInfo info = null;
		try {
			info = getPackageManager().getPackageInfo(getPackageName(), 0);
		} catch (NameNotFoundException e1) {
			try {
				info = getPackageManager().getPackageInfo(getPackageName(), 0);
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
