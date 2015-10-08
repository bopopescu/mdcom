package com.doctorcom.physician.activity.setting;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import android.app.ProgressDialog;
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

public class CallForwardActivity extends OptionalActivity {

	private final String TAG = "CallForwardActivity";
	private int selectPosition = -1;
	
	@Override
	protected void onResume() {
		super.onResume();
		titleTextView.setText(R.string.call_forwarding);
		Cache cache = new Cache(this, NetConncet.HTTP_GET);
		cache.setCacheType(Cache.CACHE_CALLFORWARDING);
		cache.useCache(this, NetConstantValues.AVAILABLE_SELECTIONS.PATH, null, null);
	}

	@Override
	public void onCacheFinish(String result, boolean updated) {
		super.onCacheFinish(result, updated);
		try {
			JSONObject jsonObj = new JSONObject(result);
			if(JsonErrorProcess.checkJsonError(result, this)) {
				JSONObject jData = jsonObj.getJSONObject("data");
				final String currentselection = jData.getString("current");
				JSONArray valuesJArr = jData.getJSONArray("choices");
				final List<String> choicesList = new ArrayList<String>();
				for (int i = 0, len = valuesJArr.length(); i < len; i++) {
					String value = valuesJArr.getString(i);
					choicesList.add(value);
					if (currentselection.equals(value)) {
						selectPosition = i;
					}
				}
				ArrayAdapter<String> adapter = new ArrayAdapter<String>(this, R.layout.custom_simple_list_item_single_choice, choicesList);
				setListAdapter(adapter);
				mListView.setChoiceMode(ListView.CHOICE_MODE_SINGLE);
				if (selectPosition != -1) {
					mListView.setItemChecked(selectPosition, true);
				}
				mListView.setOnItemClickListener(new AdapterView.OnItemClickListener() {

					@Override
					public void onItemClick(AdapterView<?> parent, View view, int position, long id) {
						if (selectPosition != position) {
							final ProgressDialog progress = ProgressDialog.show(CallForwardActivity.this, "", getString(R.string.process_text));
							HashMap<String, String> params = new HashMap<String, String>();
							params.put(NetConstantValues.AVAILABLE_SELECTIONS.PARAM_NEW_SELECTION, choicesList.get(position));
							NetConncet netConncet = new NetConncet(CallForwardActivity.this, NetConstantValues.AVAILABLE_SELECTIONS.PATH, params) {

								@Override
								protected void onPostExecute(String result) {
									super.onPostExecute(result);
									progress.dismiss();
									if (JsonErrorProcess.checkJsonError(result, CallForwardActivity.this)) {
										Toast.makeText(CallForwardActivity.this,R.string.action_successed,Toast.LENGTH_SHORT).show();
										Cache.cleanListCache(String.valueOf(Cache.CACHE_CALLFORWARDING), NetConstantValues.AVAILABLE_SELECTIONS.PATH, CallForwardActivity.this.getApplicationContext());
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

			}
		} catch (JSONException e) {
			DocLog.d(TAG, "JSONException", e);
			Toast.makeText(this, R.string.error_occur, Toast.LENGTH_SHORT).show();
			finish();
		}
	}

}
