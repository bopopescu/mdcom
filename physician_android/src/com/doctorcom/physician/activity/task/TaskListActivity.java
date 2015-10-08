package com.doctorcom.physician.activity.task;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import android.content.Intent;
import android.os.Bundle;
import android.support.v4.app.FragmentActivity;
import android.support.v4.app.ListFragment;
import android.view.LayoutInflater;
import android.view.Menu;
import android.view.MenuInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ListView;
import android.widget.ProgressBar;
import android.widget.TextView;

import com.doctorcom.android.R;
import com.doctorcom.physician.AppValues;
import com.doctorcom.physician.activity.main.NavigationActivity.RefreshListener;
import com.doctorcom.physician.net.NetConstantValues;
import com.doctorcom.physician.net.http.NetConncet;
import com.doctorcom.physician.utils.DocLog;
import com.doctorcom.physician.utils.JsonErrorProcess;
import com.doctorcom.physician.utils.cache.Cache;

public class TaskListActivity extends FragmentActivity {
	
	public static class TaskListFragment extends ListFragment implements Cache.CacheFinishListener, RefreshListener {
		private final String TAG = "TaskListFragment";
		private ProgressBar refreshProgressBar;
		private LinearLayout llContent, llLoading;
		private long due_timestamp = 0L, creation_timestamp = 0L;
		private boolean hasMore;
		private String tid = "", done_from = "";
		private List<TaskItem> taskList;
		private TaskAdapter adapter;
		private View loadMoreView;
		private ListView mListView;
		private int operate = AppValues.INIT;
		private boolean cached = false;
		private List<TaskItem> cacheResult = null;
		private final int PAGE_COUNT = AppValues.PAGE_COUNT;
		public final int TASK_NEW = 1;
		public final int TASK_EDIT = 2;
		
		@Override
		public void onCreate(Bundle savedInstanceState) {
			super.onCreate(savedInstanceState);
			setHasOptionsMenu(true);
		}

		@Override
		public View onCreateView(LayoutInflater inflater, ViewGroup container,
				Bundle savedInstanceState) {
			View view = inflater.inflate(R.layout.fragment_task_list, container, false);
			refreshProgressBar = (ProgressBar) view.findViewById(R.id.pbRefresh);
			llContent = (LinearLayout) view.findViewById(R.id.llContent);
			llLoading = (LinearLayout) view.findViewById(R.id.llLoading);
			llLoading.setVisibility(View.VISIBLE);
			llContent.setVisibility(View.GONE);

			Button newButton = (Button) view.findViewById(R.id.btNew);
			newButton.setOnClickListener(new View.OnClickListener() {
				
				@Override
				public void onClick(View v) {
					Intent intent = new Intent(TaskListFragment.this.getActivity(), TaskNewActivity.class);
					startActivityForResult(intent, TASK_NEW);
					TaskListFragment.this.getActivity().overridePendingTransition(R.anim.up, R.anim.hold);
					
				}
			});
			return view;
		}

		@Override
		public void onActivityCreated(Bundle savedInstanceState) {
			super.onActivityCreated(savedInstanceState);
			init();
			getData();
		}
		
		private void getData() {
			refreshProgressBar.setVisibility(View.VISIBLE);
			HashMap<String, String> params = new HashMap<String, String>();
			params.put(NetConstantValues.FOLLOWUPS_LIST.PARAM_COUNT,String.valueOf(PAGE_COUNT));
			params.put(NetConstantValues.FOLLOWUPS_LIST.PARAM_DUE_FROM_TIMESTAP,"" + due_timestamp);
			params.put(NetConstantValues.FOLLOWUPS_LIST.PARAM_CREATION_FROM_TIMESTAM,"" + creation_timestamp);
			params.put(NetConstantValues.FOLLOWUPS_LIST.PARAM_EXCLUDE_ID, tid);
			params.put(NetConstantValues.FOLLOWUPS_LIST.PARAM_DONE_FROM, done_from);
			Cache cache = new Cache(getActivity(), NetConncet.HTTP_POST);
			cache.setHowSearch(Cache.SEARCH_MEMORY_ONLY);
			cache.useCache(this, NetConstantValues.FOLLOWUPS_LIST.PATH, null, params);
		}
		
		@Override
		public void onResume() {
			super.onResume();
		}
		
		private void init() {
			mListView = getListView();
			taskList = new ArrayList<TaskItem>();
			cacheResult = new ArrayList<TaskItem>();
			adapter = new TaskAdapter(getActivity());
			due_timestamp = 0L;
			creation_timestamp = 0L;
			tid = "";
			done_from = "";
			hasMore = false;

		}
		
		@Override
		public void onCacheFinish(String result, boolean isCache) {
			refreshProgressBar.setVisibility(View.GONE);
			llLoading.setVisibility(View.GONE);
			llContent.setVisibility(View.VISIBLE);
			taskList.clear();
			if (JsonErrorProcess.checkJsonError(result, getActivity())) {
				try {
					JSONObject jsonObj = new JSONObject(result);
					JSONObject jsonData = jsonObj.getJSONObject("data");
					JSONArray jsonTasks = jsonData.getJSONArray("tasks");
					int size = jsonTasks.length();
					for (int i = 0; i < size; i++) {
						TaskItem item = new TaskItem();
						JSONObject task = jsonTasks.getJSONObject(i);
						int id = task.getInt("id");
						item.setId(id);
						item.setDescription(task.getString("description"));
						item.setDone(task.getBoolean("done_flag"));
						item.setNote(task.getString("note"));
						item.setPriority(task.getInt("priority"));					
						due_timestamp = task.getLong("due_timestamp");
						item.setDueTimeStamp(due_timestamp);
						taskList.add(item);
						creation_timestamp = task.getLong("creation_timestamp");
						tid = String.valueOf(id);
						done_from = task.getString("done_flag");
					}
					hasMore = jsonData.getBoolean("limit_hit");
				} catch (JSONException e) {
					DocLog.e(TAG, "JSONException", e);
				} finally {
					addFooterView();			
					switch (operate) {
					case AppValues.INIT:
					case AppValues.REFRESH:
						adapter.initItems(taskList);
						setListAdapter(adapter);
						break;
					case AppValues.LOAD_MORE:
						if (isCache) {
							cached = true;
							for (int i = 0, len = taskList.size(); i < len; i++) {
								cacheResult.add(taskList.get(i));
							}
						} else {
							cached = false;
						}
						adapter.addItems(taskList);
						adapter.notifyDataSetChanged();
						break;
					}

				}
			} else {
				addFooterView();			
				if (cached) {
					adapter.addItems(cacheResult);
					adapter.notifyDataSetChanged();
				}
			}
		}
	
		private void addFooterView() {
			if (loadMoreView != null) {
				mListView.removeFooterView(loadMoreView);
			}
			if (hasMore) {
				loadMoreView = getActivity().getLayoutInflater().inflate(R.layout.load_more, null, false);
				Button loadMore = (Button)loadMoreView.findViewById(R.id.btLoadMore);
				loadMore.setText(R.string.task_get_25_more);
				final ProgressBar pb = (ProgressBar)loadMoreView.findViewById(R.id.pb);
				final TextView loadingTextView = (TextView)loadMoreView.findViewById(R.id.tvLoading);
				loadMore.setOnClickListener(new View.OnClickListener() {
					
					@Override
					public void onClick(View v) {
						v.setVisibility(View.GONE);
						pb.setVisibility(View.VISIBLE);
						loadingTextView.setVisibility(View.VISIBLE);
						operate = AppValues.LOAD_MORE;
						getData();
						
					}
				});
				mListView.addFooterView(loadMoreView);
			}
		}

		@Override
		public void onListItemClick(ListView l, View v, int position, long id) {
			Intent intent =  new Intent(getActivity(), TaskDetailActivity.class);
			TaskItem item = adapter.getItem(position);
			if(null == item)
				return;
			intent.putExtra("task", item);
			startActivityForResult(intent, TASK_EDIT);
			
		}

		@Override
		public void onCreateOptionsMenu(Menu menu, MenuInflater inflater) {
			super.onCreateOptionsMenu(menu, inflater);
			menu.add(0, R.id.iRefresh, 2, R.string.refresh);
		}

		@Override
		public void onActivityResult(int requestCode, int resultCode,
				Intent data) {
			if (resultCode == RESULT_OK) {
				refreshView();
			}
		}

		@Override
		public void onHiddenChanged(boolean hidden) {
			super.onHiddenChanged(hidden);
			refreshView();
			
		}

		@Override
		public void refreshView() {
			init();
			operate = AppValues.REFRESH;
			getData();	
			
		}

		@Override
		public void forceRefreshView() {
			Cache.resetFollowupTaskList();
			refreshView();
		}

	}

}
