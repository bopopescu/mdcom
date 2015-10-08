package com.doctorcom.physician.activity.more;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;

import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.support.v4.app.FragmentActivity;
import android.support.v4.app.FragmentManager;
import android.support.v4.app.ListFragment;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ArrayAdapter;
import android.widget.ImageView;
import android.widget.ListView;
import android.widget.TextView;

import com.doctorcom.android.R;
import com.doctorcom.physician.AppValues;
import com.doctorcom.physician.activity.invitation.InvitationListActivity;
import com.doctorcom.physician.activity.setting.SettingActivity;
import com.doctorcom.physician.utils.PreferLogo;

public class MoreListActivity extends FragmentActivity {

	@Override
	protected void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
		FragmentManager fm = getSupportFragmentManager();

		// Create the list fragment and add it as our sole content.
		if (fm.findFragmentById(android.R.id.content) == null) {
			MoreListFragment list = new MoreListFragment();
			fm.beginTransaction().add(android.R.id.content, list).commit();
		}
	}

	public static class MoreListFragment extends ListFragment {
		private AppValues appValues;
		private String INVITATION;
		private String SETTING;
		private String MDCOM_NUMBER;
		private String LOGOUT;
		private ImageView ivPreferLogoImageView;
		private Context context;

		@Override
		public View onCreateView(LayoutInflater inflater, ViewGroup container,
				Bundle savedInstanceState) {
			View view = inflater.inflate(R.layout.fragment_more, container,
					false);
			ivPreferLogoImageView = (ImageView) view
					.findViewById(R.id.ivPreferLogo);
			PreferLogo.showPreferLogo(getActivity(), ivPreferLogoImageView);
			return view;
		}

		@Override
		public void onActivityCreated(Bundle savedInstanceState) {
			super.onActivityCreated(savedInstanceState);
			context = getActivity();
			appValues = new AppValues(getActivity());
			INVITATION = getString(R.string.invitations);
			SETTING = getString(R.string.settings);
			MDCOM_NUMBER = getString(R.string.call_my_doctorcom_number)
					+ "\r\n" + appValues.getMdcomNumber();
			LOGOUT = getString(R.string.logout);
			List<String> list = new ArrayList<String>();
			int userType = appValues.getUserType();
			switch (userType) {
			case AppValues.PROVIDER:
				list.add(getString(R.string.invitations));
				list.add(getString(R.string.settings));
				if (!appValues.getMdcomNumber().equals("")) {
					list.add(getString(R.string.call_my_doctorcom_number)
							+ "\r\n" + appValues.getMdcomNumber());
				}
				list.add(getString(R.string.logout));
				break;
			case AppValues.PRACTICE_MANAGER:
				list.add(getString(R.string.invitations));
				list.add(getString(R.string.settings));
				list.add(getString(R.string.logout));
				break;
			case AppValues.STAFF:
				list.add(getString(R.string.settings));
				list.add(getString(R.string.logout));
				break;
			}
			MoreListAdapter adapter = new MoreListAdapter(getActivity(),
					R.layout.cell_more, R.id.tvMoreCell, list);
			setListAdapter(adapter);
		}

		@Override
		public void onListItemClick(ListView l, View v, int position, long id) {
			Intent intent;
			HashMap<String, Integer> map = getMap();
			String typeStr = ((MoreListAdapter) this.getListAdapter())
					.getItem(position);
			int type = map.get(typeStr);
			switch (type) {
			case 0:
				intent = new Intent(MoreListFragment.this.getActivity(),
						InvitationListActivity.class);
				startActivity(intent);
				break;
			case 1:
				intent = new Intent(MoreListFragment.this.getActivity(),
						SettingActivity.class);
				startActivity(intent);
				break;
			case 2:
				intent = new Intent(Intent.ACTION_CALL, Uri.parse("tel://"
						+ appValues.getMdcomNumber()));
				startActivity(intent);
				break;
			case 3:
				CommonMoreMethods.logout(context);
				break;
			}

		}

		private HashMap<String, Integer> getMap() {
			HashMap<String, Integer> map = new HashMap<String, Integer>();
			map.put(INVITATION, 0);
			map.put(SETTING, 1);
			map.put(MDCOM_NUMBER, 2);
			map.put(LOGOUT, 3);
			return map;
		}

		@Override
		public void onHiddenChanged(boolean hidden) {
			super.onHiddenChanged(hidden);
			if (!hidden) {
				PreferLogo.showPreferLogo(getActivity(), ivPreferLogoImageView);
			}
		}

		class MoreListAdapter extends ArrayAdapter<String> {
			private LayoutInflater mInflater;
			private int resourceId;

			public MoreListAdapter(Context context, int resource,
					int textViewResourceId, List<String> objects) {
				super(context, resource, textViewResourceId, objects);
				this.resourceId = resource;
				mInflater = LayoutInflater.from(context);
			}

			@Override
			public View getView(int position, View convertView, ViewGroup parent) {
				String content = getItem(position);
				MoreHolder holder;
				if (convertView == null) {
					convertView = mInflater.inflate(resourceId, null);
					holder = new MoreHolder();
					holder.iconImageView = (ImageView) convertView
							.findViewById(R.id.ivMoreCell);
					holder.contentTextView = (TextView) convertView
							.findViewById(R.id.tvMoreCell);
					convertView.setTag(holder);
				} else {
					holder = (MoreHolder) convertView.getTag();
				}
				holder.contentTextView.setText(content);
				HashMap<String, Integer> map = getMap();
				int type = map.get(content);
				switch (type) {
				case 0:
					holder.iconImageView
							.setBackgroundResource(R.drawable.tab_invitations_more);
					break;
				case 1:
					holder.iconImageView
							.setBackgroundResource(R.drawable.tab_settings_more);
					break;
				case 2:
					holder.iconImageView
							.setBackgroundResource(R.drawable.tab_call_more);
					break;
				case 3:
					holder.iconImageView
							.setBackgroundResource(R.drawable.icon_logout);
					break;
				}

				return convertView;
			}

		}

		static class MoreHolder {
			ImageView iconImageView;
			TextView contentTextView;
		}

	}

}
