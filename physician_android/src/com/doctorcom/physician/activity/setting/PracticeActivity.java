package com.doctorcom.physician.activity.setting;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import android.app.ProgressDialog;
import android.content.Intent;
import android.support.v4.content.LocalBroadcastManager;
import android.view.View;
import android.widget.AdapterView;
import android.widget.ArrayAdapter;
import android.widget.ListView;
import android.widget.Toast;

import com.doctorcom.android.R;
import com.doctorcom.physician.AppValues;
import com.doctorcom.physician.net.NetConstantValues;
import com.doctorcom.physician.net.http.NetConncet;
import com.doctorcom.physician.utils.DocLog;
import com.doctorcom.physician.utils.JsonErrorProcess;
import com.doctorcom.physician.utils.cache.Cache;
import com.doctorcom.physician.utils.cache.CacheService;

public class PracticeActivity extends OptionalActivity {

	private final String TAG = "PracticeActivity";
	private int selectPosition = -1;
	
	@Override
	protected void onResume() {
		super.onResume();
		titleTextView.setText(R.string.practice);
		Cache cache = new Cache(this, NetConncet.HTTP_GET);
		cache.setCacheType(Cache.CACHE_PRACTICE);
		cache.useCache(this, NetConstantValues.PRACTICE_ASSOCIATION.PATH, null, null);

	}

	@Override
	public void onCacheFinish(String result, boolean updated) {
		super.onCacheFinish(result, updated);
		try {
			JSONObject jsonObj = new JSONObject(result);
			if(JsonErrorProcess.checkJsonError(result, this)) {
				JSONObject practiceJSON = jsonObj.getJSONObject("data");
				final int currentPracticeID;
				if (practiceJSON.isNull("current_practice")) {
					currentPracticeID = 0;
				} else {
					currentPracticeID = practiceJSON.getInt("current_practice");
				}
				JSONArray jsonArr = practiceJSON.getJSONArray("practices");
				List<String> practicesName = new ArrayList<String>();
				final List<Integer> practicesId = new ArrayList<Integer>();
				for (int i = 0, length = jsonArr.length(); i < length; i++) {
					JSONArray practiceinfo = jsonArr.getJSONArray(i);
					int practiceID = practiceinfo.getInt(0);
					if (currentPracticeID == practiceID) {
						selectPosition = i;
					}
					String practiceName = practiceinfo.getString(1);
					practicesId.add(practiceID);
					practicesName.add(practiceName);
				}
				if (appValues.getUserType() == AppValues.STAFF) {
					ArrayAdapter<String> adapter = new ArrayAdapter<String>(this, android.R.layout.simple_list_item_1, new String[]{practicesName.get(selectPosition)});
					setListAdapter(adapter);
					mListView.setEnabled(false);
					return;
				}
				ArrayAdapter<String> adapter = new ArrayAdapter<String>(this, R.layout.custom_simple_list_item_single_choice, practicesName);
				setListAdapter(adapter);
				mListView.setChoiceMode(ListView.CHOICE_MODE_SINGLE);
				if (selectPosition != -1) {
					mListView.setItemChecked(selectPosition, true);
				}
				mListView.setOnItemClickListener(new AdapterView.OnItemClickListener() {

					@Override
					public void onItemClick(AdapterView<?> parent, View view, int position, long id) {
						if (selectPosition != position) {
							final ProgressDialog progress = ProgressDialog.show(PracticeActivity.this, "", getString(R.string.process_text));
							HashMap<String, String> params = new HashMap<String, String>();
							params.put(NetConstantValues.PRACTICE_ASSOCIATION.PARAM_CURRENT_PRACTICE, String.valueOf(practicesId.get(position)));
							NetConncet netConncet = new NetConncet(PracticeActivity.this, NetConstantValues.PRACTICE_ASSOCIATION.PATH, params) {

								@Override
								protected void onPostExecute(String result) {
									super.onPostExecute(result);
									progress.dismiss();
									if (JsonErrorProcess.checkJsonError(result, PracticeActivity.this)) {
										Toast.makeText(PracticeActivity.this,R.string.action_successed,Toast.LENGTH_SHORT).show();
										Cache.cleanListCache(String.valueOf(Cache.CACHE_PRACTICE), NetConstantValues.PRACTICE_ASSOCIATION.PATH, PracticeActivity.this.getApplicationContext());
										Intent intent = new Intent(CacheService.CACHE_SERVICE);
										intent.putExtra("cmd", CacheService.UPDATE_USER_LIST);
										startService(new Intent(intent));
										LocalBroadcastManager broadcastManager = LocalBroadcastManager.getInstance(PracticeActivity.this);
										Intent i = new Intent("refreshAction");
										i.putExtra("cmd", 4);
										broadcastManager.sendBroadcast(i);
//										finish();
										selectPosition = mListView.getCheckedItemPosition();
									} else {
										if (selectPosition != -1) {
											mListView.setItemChecked(selectPosition, true);
										}
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
