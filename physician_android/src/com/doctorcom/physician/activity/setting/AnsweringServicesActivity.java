package com.doctorcom.physician.activity.setting;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import android.app.ProgressDialog;
import android.content.Context;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.AdapterView;
import android.widget.ArrayAdapter;
import android.widget.CheckedTextView;
import android.widget.ListView;
import android.widget.Toast;

import com.doctorcom.android.R;
import com.doctorcom.physician.net.NetConstantValues;
import com.doctorcom.physician.net.http.NetConncet;
import com.doctorcom.physician.utils.DocLog;
import com.doctorcom.physician.utils.JsonErrorProcess;
import com.doctorcom.physician.utils.cache.Cache;

public class AnsweringServicesActivity extends OptionalActivity {

	private final String TAG = "AnsweringServicesActivity";
	private int selectPosition = -1;
	
	@Override
	protected void onResume() {
		super.onResume();
		titleTextView.setText(R.string.answering_services);
		Cache cache = new Cache(this, NetConncet.HTTP_GET);
		cache.setCacheType(Cache.CACHE_ANSWERINGSERVICE);
		cache.useCache(this, NetConstantValues.AVAILABLE_ANSWERING_SERVICE.PATH, null, null);
	}

	@Override
	public void onCacheFinish(String result, boolean updated) {
		super.onCacheFinish(result, updated);
		try {
			JSONObject jsonObj = new JSONObject(result);
			if(JsonErrorProcess.checkJsonError(result, this)) {
				JSONObject jData = jsonObj.getJSONObject("data");
				String currentselection = jData.getString("current");
				JSONArray valuesJArr = jData.getJSONArray("choices");
				final List<String> choicesList = new ArrayList<String>();
				for (int i = 0, len = valuesJArr.length(); i < len; i++) {
					String value = valuesJArr.getString(i);
					choicesList.add(value);
					if (currentselection.equals(value)) {
						selectPosition = i;
					}
				}
				ArrayAdapter<String> adapter = new AnsweringServiceAdapter(this, R.layout.custom_simple_list_item_single_choice, choicesList);
				setListAdapter(adapter);
				mListView.setChoiceMode(ListView.CHOICE_MODE_SINGLE);
				if (selectPosition != -1) {
					mListView.setItemChecked(selectPosition, true);
				}
				mListView.setOnItemClickListener(new AdapterView.OnItemClickListener() {

					@Override
					public void onItemClick(AdapterView<?> parent, View view, int position, long id) {
						if (position < choicesList.size() && selectPosition != position) {
							final ProgressDialog progress = ProgressDialog.show(AnsweringServicesActivity.this, "", getString(R.string.process_text));
							HashMap<String, String> params = new HashMap<String, String>();
							params.put(NetConstantValues.AVAILABLE_ANSWERING_SERVICE.PARAM_NEW_SELECTION, choicesList.get(position));
							NetConncet netConncet = new NetConncet(AnsweringServicesActivity.this, NetConstantValues.AVAILABLE_ANSWERING_SERVICE.PATH, params) {

								@Override
								protected void onPostExecute(String result) {
									super.onPostExecute(result);
									progress.dismiss();
									if (JsonErrorProcess.checkJsonError(result, AnsweringServicesActivity.this)) {
										Toast.makeText(AnsweringServicesActivity.this,R.string.action_successed,Toast.LENGTH_SHORT).show();
										Cache.cleanListCache(String.valueOf(Cache.CACHE_ANSWERINGSERVICE), NetConstantValues.AVAILABLE_ANSWERING_SERVICE.PATH, AnsweringServicesActivity.this.getApplicationContext());
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
						} else {
							mListView.setItemChecked(selectPosition, true);
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
	
	static class AnsweringServiceAdapter extends ArrayAdapter<String> {
		private int layout;
		private LayoutInflater mInflater;
		private Context context;
		private int length = 1;

		public AnsweringServiceAdapter(Context context, int textViewResourceId, List<String> list) {
			super(context, textViewResourceId);
			layout = textViewResourceId;
			mInflater = LayoutInflater.from(context);
			this.context = context;
			setData(list);
		}
		public void setData(List<String> data) {
			clear();
			if (data == null)
				return;
			length = data.size();
			for (int i = 0; i < length; i++) {
				add(data.get(i));

			}
			add(context.getString(R.string.live_operator_backup));

		}
		@Override
		public View getView(int position, View convertView, ViewGroup parent) {
			ViewHolder holder;
			if (convertView == null) {
				convertView = mInflater.inflate(layout, null);
				holder = new ViewHolder();
				holder.answeringCheckedTextView = (CheckedTextView) convertView.findViewById(android.R.id.text1);
				convertView.setTag(holder);

			} else {
				holder = (ViewHolder) convertView.getTag();
			}
			String item = getItem(position);
			holder.answeringCheckedTextView.setText(item);
			//live operator back-up
			if (position == length) {
				holder.answeringCheckedTextView.setTextColor(context.getResources().getColor(R.color.gray));
			} else {
				holder.answeringCheckedTextView.setTextColor(context.getResources().getColor(R.color.black));
			}
			return convertView;
		}
	}
	
	static class ViewHolder {
		CheckedTextView answeringCheckedTextView;
	}
	

}
