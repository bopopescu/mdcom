package com.doctorcom.physician.activity.doctor;

import java.util.List;

import com.doctorcom.android.R;

import android.content.Context;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ArrayAdapter;
import android.widget.TextView;

public class TabListAdapter extends ArrayAdapter<DoctorTabItem> {
	private LayoutInflater mInflater;
	private int resourceId;
	public TabListAdapter(Context context, int resource,
			int textViewResourceId, List<DoctorTabItem> objects) {
		super(context, resource, textViewResourceId, objects);
		this.resourceId = resource;
		mInflater = LayoutInflater.from(context);
	}

	@Override
	public View getView(int position, View convertView, ViewGroup parent) {
		DoctorTabItem item = getItem(position);
		TabHolder holder;
		if (convertView == null) {
			convertView = mInflater.inflate(resourceId, null);
			holder = new TabHolder();
			holder.tabTextView = (TextView) convertView.findViewById(R.id.textview_users_select);
			convertView.setTag(holder);
		} else {
			holder = (TabHolder) convertView.getTag();
		}
		holder.tabTextView.setText(item.getName());
		if (item.isSelected()) {
			holder.tabTextView.setBackgroundResource(R.drawable.dropdown_center_active);
		} else {
			holder.tabTextView.setBackgroundResource(R.drawable.dropdown_center);
		}
		return convertView;
	}

	static class TabHolder {
		TextView tabTextView;
	}

}
