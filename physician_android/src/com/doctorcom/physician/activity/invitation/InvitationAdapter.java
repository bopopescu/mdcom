package com.doctorcom.physician.activity.invitation;

import java.util.ArrayList;
import java.util.List;

import android.content.Context;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.BaseAdapter;
import android.widget.TextView;

import com.doctorcom.android.R;
import com.doctorcom.physician.AppValues;
import com.doctorcom.physician.utils.Utils;

public class InvitationAdapter extends BaseAdapter {

	protected Context mContext;
	private LayoutInflater mInflater;
	private List<InvitationItem> mData;
	private AppValues appValues;
	
	public InvitationAdapter(Context context) {
		mContext = context;
		appValues = new AppValues(context);
		mInflater = LayoutInflater.from(context);
	}
	
	@Override
	public int getCount() {
		if (mData == null) {
			return 0;
		}
		return mData.size();
	}

	@Override
	public InvitationItem getItem(int position) {
		if (mData == null) {
			return null;
		}
		return mData.get(position);
	}
	public void initItems(List<InvitationItem> items) {
		if (mData != null) {
			mData.clear();
			mData = null;
		}
		mData = new ArrayList<InvitationItem>();

		if (items != null) {
			addItems(items);
		}
	}
	
	public void addItem(InvitationItem item) {
		if (mData == null) {
			mData = new ArrayList<InvitationItem>();
		}
		mData.add(item);
	}
	
	public void addItems(List<InvitationItem> items) {
		for (int i = 0, length = items.size(); i < length; i++ ) {
			InvitationItem item = items.get(i);
			addItem(item);
		}
	}
	
	@Override
	public long getItemId(int position) {
		return position;
	}

	@Override
	public View getView(int position, View convertView, ViewGroup parent) {
		InvitationViewHolder holder;
		if (convertView == null) {
			convertView = mInflater.inflate(R.layout.cell_invitation, null);
			holder = new InvitationViewHolder();
			holder.recipientTextView = (TextView) convertView.findViewById(R.id.tvRecipient);
			holder.dueTextView = (TextView) convertView.findViewById(R.id.tvDue);
			holder.summaryTextView = (TextView) convertView.findViewById(R.id.tvSummary);
			convertView.setTag(holder);
		} else {
			holder = (InvitationViewHolder) convertView.getTag();
		}
		InvitationItem item = getItem(position);
		holder.recipientTextView.setText(item.getRecipient());
		holder.dueTextView.setText(Utils.getDateTimeFormat(item.getDueTimestamp(), appValues.getTimeFormat(), appValues.getTimezone()));
		holder.summaryTextView.setText(item.getSummary());
		return convertView;
	}
	
	static class InvitationViewHolder {
		TextView recipientTextView, dueTextView, summaryTextView;
	}

}
