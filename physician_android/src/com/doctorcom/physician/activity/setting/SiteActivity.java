package com.doctorcom.physician.activity.setting;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import android.app.ProgressDialog;
import android.content.Intent;
import android.view.View;
import android.widget.AdapterView;
import android.widget.ArrayAdapter;
import android.widget.ListView;
import android.widget.Toast;

import com.doctorcom.android.R;
import com.doctorcom.physician.net.NetConstantValues;
import com.doctorcom.physician.net.http.NetConncet;
import com.doctorcom.physician.utils.DocLog;
import com.doctorcom.physician.utils.JsonErrorProcess;
import com.doctorcom.physician.utils.cache.Cache;
import com.doctorcom.physician.utils.cache.CacheService;

public class SiteActivity extends OptionalActivity {

	private final String TAG = "SiteActivity";
	private int selectPosition = -1;

	@Override
	protected void onResume() {
		super.onResume();
		titleTextView.setText(R.string.site);
		Cache cache = new Cache(this, NetConncet.HTTP_GET);
		cache.setCacheType(Cache.CACHE_SITE);
		cache.useCache(this, NetConstantValues.SITE_AFFILIATION.PATH, null, null);
		
	}

	@Override
	public void onCacheFinish(String result, boolean updated) {
		super.onCacheFinish(result, updated);
		try {
			JSONObject jsonObj = new JSONObject(result);
			if(JsonErrorProcess.checkJsonError(result, this)) {
				JSONObject siteJSON = jsonObj.getJSONObject("data");
				final int currentsiteID;
				if (siteJSON.isNull("current_site")) {
					currentsiteID = 0;
				} else {
					currentsiteID = siteJSON.getInt("current_site");
				}
				JSONArray jsonArr = siteJSON.getJSONArray("sites");
				List<String> sitesName = new ArrayList<String>();
				final List<Integer> sitesId = new ArrayList<Integer>();
				for (int i = 0, length = jsonArr.length(); i < length; i++) {
					JSONArray siteinfo = jsonArr.getJSONArray(i);
					int siteID = siteinfo.getInt(0);
					if (currentsiteID == siteID) {
						selectPosition = i;
					}
					String siteName = siteinfo.getString(1);
					sitesId.add(siteID);
					sitesName.add(siteName);
				}
				ArrayAdapter<String> adapter = new ArrayAdapter<String>(this, R.layout.custom_simple_list_item_single_choice, sitesName);
				setListAdapter(adapter);
				mListView.setChoiceMode(ListView.CHOICE_MODE_SINGLE);
				if (selectPosition != -1) {
					mListView.setItemChecked(selectPosition, true);
				}
				mListView.setOnItemClickListener(new AdapterView.OnItemClickListener() {

					@Override
					public void onItemClick(AdapterView<?> parent, View view, int position, long id) {
						if (selectPosition != position) {
							final ProgressDialog progress = ProgressDialog.show(SiteActivity.this, "", getString(R.string.process_text));
							HashMap<String, String> params = new HashMap<String, String>();
							params.put(NetConstantValues.SITE_AFFILIATION.PARAM_CURRENT_SITE, String.valueOf(sitesId.get(position)));
							NetConncet netConncet = new NetConncet(SiteActivity.this, NetConstantValues.SITE_AFFILIATION.PATH, params) {

								@Override
								protected void onPostExecute(String result) {
									super.onPostExecute(result);
									progress.dismiss();
									if (JsonErrorProcess.checkJsonError(result, SiteActivity.this)) {
										Toast.makeText(SiteActivity.this,R.string.action_successed,Toast.LENGTH_SHORT).show();
										Cache.cleanListCache(String.valueOf(Cache.CACHE_SITE), NetConstantValues.SITE_AFFILIATION.PATH, SiteActivity.this.getApplicationContext());
										Intent intent = new Intent(CacheService.CACHE_SERVICE);
										intent.putExtra("cmd", CacheService.UPDATE_USER_LIST);
										startService(new Intent(intent));
//										finish();
										selectPosition = mListView.getCheckedItemPosition();
									} else {
										if (selectPosition != -1) {
											mListView.setItemChecked(selectPosition, true);
										}
										Toast.makeText(SiteActivity.this, R.string.error_occur, Toast.LENGTH_SHORT).show();

									}
								}
								
							};
							netConncet.execute();
						}
					}
				});
			} else {
				
			}
		} catch (JSONException e) {
			DocLog.d(TAG, "JSONException", e);
			Toast.makeText(this, R.string.error_occur, Toast.LENGTH_SHORT).show();
			finish();
		}
		
	}

}
