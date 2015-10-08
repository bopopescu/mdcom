package com.doctorcom.physician.activity.invitation;

import java.util.ArrayList;
import java.util.List;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import android.app.AlertDialog;
import android.content.DialogInterface;
import android.content.Intent;
import android.os.Bundle;
import android.support.v4.app.FragmentActivity;
import android.support.v4.app.FragmentManager;
import android.support.v4.app.ListFragment;
import android.view.LayoutInflater;
import android.view.Menu;
import android.view.MenuInflater;
import android.view.MenuItem;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ListView;
import android.widget.ProgressBar;
import android.widget.Toast;

import com.doctorcom.android.R;
import com.doctorcom.physician.AppValues;
import com.doctorcom.physician.activity.main.NavigationActivity.RefreshListener;
import com.doctorcom.physician.net.NetConstantValues;
import com.doctorcom.physician.net.http.NetConncet;
import com.doctorcom.physician.utils.DocLog;
import com.doctorcom.physician.utils.cache.Cache;

public class InvitationListActivity extends FragmentActivity {
	
	@Override
	protected void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
        FragmentManager fm = getSupportFragmentManager();

        // Create the list fragment and add it as our sole content.
        if (fm.findFragmentById(android.R.id.content) == null) {
        	InvitationFragment invitation = new InvitationFragment();
            fm.beginTransaction().add(android.R.id.content, invitation).commit();
        }
	}
	
	public static class InvitationFragment extends ListFragment implements Cache.CacheFinishListener, RefreshListener {
		private String TAG = "InvitationFragment";
		private ProgressBar refreshProgressBar;
		private LinearLayout llContent, llLoading;
		private List<InvitationItem> invitationList;
		private InvitationAdapter adapter;
		

		@Override
		public void onCreate(Bundle savedInstanceState) {
			super.onCreate(savedInstanceState);
			setHasOptionsMenu(true);
		}

		@Override
		public View onCreateView(LayoutInflater inflater, ViewGroup container,
				Bundle savedInstanceState) {
			View view = inflater.inflate(R.layout.fragment_invitation_list, container, false);
			refreshProgressBar = (ProgressBar) view.findViewById(R.id.pbRefresh);
			llContent = (LinearLayout) view.findViewById(R.id.llContent);
			llLoading = (LinearLayout) view.findViewById(R.id.llLoading);
			llLoading.setVisibility(View.VISIBLE);
			llContent.setVisibility(View.GONE);

			invitationList = new ArrayList<InvitationItem>();
			adapter = new InvitationAdapter(getActivity());

			Button newButton = (Button) view.findViewById(R.id.btNew);
			newButton.setOnClickListener(new View.OnClickListener() {
				
				@Override
				public void onClick(View v) {
					final Intent intent = new Intent(getActivity(), InvitationNewActivity.class);
					AppValues appValues = new AppValues(getActivity());
					if (appValues.getUserType() == AppValues.PRACTICE_MANAGER) {
						AlertDialog.Builder builder = new AlertDialog.Builder(getActivity());
						builder.setTitle(R.string.invitations)
								.setItems(R.array.invitation_options, new DialogInterface.OnClickListener(){

									@Override
									public void onClick(DialogInterface dialog, int item) {
										intent.putExtra("type", item);
										startActivity(intent);
										getActivity().overridePendingTransition(R.anim.up, R.anim.hold);
									}
									
								});
						AlertDialog alert = builder.create();
						alert.setCanceledOnTouchOutside(true);
						alert.show();
					} else {
						intent.putExtra("type", -1);
						startActivity(intent);
						getActivity().overridePendingTransition(R.anim.up, R.anim.hold);
					}
					
				}
			});
			
			Button backButton = (Button) view.findViewById(R.id.btBack);
			backButton.setOnClickListener(new View.OnClickListener() {
				
				@Override
				public void onClick(View v) {
					getActivity().finish();
					
				}
			});
			
			return view;
		}

		@Override
		public void onActivityCreated(Bundle savedInstanceState) {
			super.onActivityCreated(savedInstanceState);
		}

		@Override
		public void onResume() {
			super.onResume();
			getData();
		}
		
		private void getData() {
			refreshProgressBar.setVisibility(View.VISIBLE);
			Cache cache = new Cache(getActivity(), NetConncet.HTTP_POST);
			cache.setCacheType(Cache.CACHE_INVITATION_LIST);
			cache.useCache(this, NetConstantValues.GET_OUTSTANDING_INVITATIONS.PATH, null, null);
		}


		@Override
		public void refreshView() {
			getData();
			
		}

		@Override
		public void onListItemClick(ListView l, View v, int position, long id) {
			Intent intent = new Intent(getActivity(), InvitationDetailActivity.class);
			InvitationItem item = adapter.getItem(position);
			intent.putExtra("invitation", item);
			startActivity(intent);
		}

		@Override
		public void onCacheFinish(String result, boolean updated) {
			refreshProgressBar.setVisibility(View.GONE);
			llLoading.setVisibility(View.GONE);
			llContent.setVisibility(View.VISIBLE);
			try {
				JSONObject jsonObj = new JSONObject(result);
				if (!jsonObj.isNull("errno")) {
					String showInfo = jsonObj.getString("descr");
					if(null != showInfo)
						Toast.makeText(getActivity(), jsonObj.getString("descr"), Toast.LENGTH_LONG).show();
					else
						Toast.makeText(getActivity(), this.getString(R.string.error_occur), Toast.LENGTH_LONG).show();
					return;
				}
				JSONArray jsonArr = jsonObj.getJSONObject("data").getJSONArray("invitations");
				invitationList.clear();
				for (int i = 0, length = jsonArr.length(); i < length; i++) {
					JSONObject itemJson = jsonArr.optJSONObject(i);
					int id = itemJson.getInt("id");
					String recipient = itemJson.getString("recipient");
					long due = itemJson.getLong("request_timestamp");
					String summary = itemJson.getString("desc");
					InvitationItem item = new InvitationItem(id, recipient, due * 1000, summary);
					invitationList.add(item);
				}
				adapter.initItems(invitationList);
				setListAdapter(adapter);
			} catch (JSONException e) {
				DocLog.e(TAG, "JSONException", e);
			}
			
			
		}

		@Override
		public void onCreateOptionsMenu(Menu menu, MenuInflater inflater) {
			super.onCreateOptionsMenu(menu, inflater);
			menu.add(0, R.id.iRefresh, 2, R.string.refresh);
		}

		@Override
		public boolean onOptionsItemSelected(MenuItem item) {
			switch(item.getItemId()) {
			case R.id.iRefresh:
				forceRefreshView();
				break;

			}
			return true;
		}

		@Override
		public void forceRefreshView() {
			Cache.cleanListCache(String.valueOf(Cache.CACHE_INVITATION_LIST), NetConstantValues.GET_OUTSTANDING_INVITATIONS.PATH, InvitationFragment.this.getActivity().getApplicationContext());
			refreshView();
			
		}

	}

}
