package com.doctorcom.physician.activity.message;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;

import android.content.Context;
import android.content.Intent;
import android.graphics.Typeface;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.view.ViewTreeObserver;
import android.view.View.OnClickListener;
import android.view.ViewTreeObserver.OnGlobalLayoutListener;
import android.widget.BaseAdapter;
import android.widget.ImageButton;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.TextView;

import com.doctorcom.android.R;
import com.doctorcom.physician.AppValues;
import com.doctorcom.physician.activity.doctor.DoctorDetailActivity;
import com.doctorcom.physician.activity.message.SentMessageItem.Body;
import com.doctorcom.physician.net.ImageDownload;
import com.doctorcom.physician.utils.Utils;

public class SentMessageAdapter extends BaseAdapter {
	protected Context context;
	private LayoutInflater mInflater;
	private List<SentMessageItem> mData;
	private int index = 0;
	@SuppressWarnings("unused")
	private AppValues appValues;

	public SentMessageAdapter(Context context) {
		this.context = context;
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
	public SentMessageItem getItem(int position) {
		if (mData == null) {
			return null;
		}
		return mData.get(position);
	}

	public void addItem(SentMessageItem item) {
		if (mData == null) {
			mData = new ArrayList<SentMessageItem>();
		}
		mData.add(item);
	}

	public void addItems(List<SentMessageItem> items) {
		index = this.getCount();
		for (int i = 0, length = items.size(); i < length; i++) {
			SentMessageItem item = items.get(i);
			addItem(item);
		}
	}

	public void setThreadingBody(ArrayList<Body> list) {
		int size = mData.size();
		for (int i = index; i < size; i++) {
			Body itemBody = list.get(i - index);
			String id = itemBody.getId();
			SentMessageItem item = getItem(i);

			// imitational codes
			// **************************************************************
			String jsonStrMessageDetail;
			if (item.getRefer().equals(""))
				jsonStrMessageDetail = CommonMessageMethods
						.getJsonStrMessageDetail(false, context);
			else
				jsonStrMessageDetail = CommonMessageMethods
						.getJsonStrMessageDetail(true, context);
			itemBody.setJsonStrMessageDetail(jsonStrMessageDetail);
			// **************************************************************

			if (id.equals(item.getId()))
				item.setBody(itemBody);
			else {
				setThreadingBody2(list);
				return;
			}
		}
	}

	public void setThreadingBody2(ArrayList<Body> list) {
		HashMap<String, SentMessageItem> messageMap = getThreadingMap();
		int length = list.size();
		for (int i = 0; i < length; i++) {
			Body itemBody = list.get(i);
			String id = itemBody.getId();
			SentMessageItem item = messageMap.get(id);

			// imitational codes
			// **************************************************************
			String jsonStrMessageDetail;
			if (item.getRefer().equals(""))
				jsonStrMessageDetail = CommonMessageMethods
						.getJsonStrMessageDetail(false, context);
			else
				jsonStrMessageDetail = CommonMessageMethods
						.getJsonStrMessageDetail(true, context);
			itemBody.setJsonStrMessageDetail(jsonStrMessageDetail);
			// **************************************************************

			item.setBody(itemBody);
		}
	}

	public HashMap<String, SentMessageItem> getThreadingMap() {
		int size = mData.size();
		HashMap<String, SentMessageItem> threadingMap = new HashMap<String, SentMessageItem>();
		for (int i = 0; i < size; i++) {
			SentMessageItem item = mData.get(i);
			String id = item.getId();
			threadingMap.put(id, item);
		}
		return threadingMap;

	}

	public void addTopItems(List<SentMessageItem> items) {
		if (mData == null) {
			mData = new ArrayList<SentMessageItem>();
		}
		for (int i = items.size(); i > 0; i--) {
			SentMessageItem item = items.get(i - 1);
			mData.add(0, item);
		}
	}

	public void initItems(List<SentMessageItem> items) {
		index = 0;
		if (mData != null) {
			mData.clear();
			mData = null;
		} else {
			mData = new ArrayList<SentMessageItem>();
		}
		if (items != null) {
			addItems(items);
		}
	}

	@Override
	public long getItemId(int position) {
		return position;
	}

	@Override
	public View getView(int position, View convertView, ViewGroup parent) {
		SentMessageItem item = getItem(position);
		MessageViewHolder holder;
		if (convertView == null) {
			convertView = mInflater.inflate(R.layout.cell_threading_to, null);
			holder = new MessageViewHolder();
			holder.txtSubject = (TextView) convertView
					.findViewById(R.id.tvTitle);
			holder.txtUser = (TextView) convertView.findViewById(R.id.tvName);
			holder.txtTimestamp = (TextView) convertView
					.findViewById(R.id.tvDate);
			holder.imageAttchment = (ImageView) convertView
					.findViewById(R.id.ivAttach);
			holder.imageImportant = (ImageView) convertView
					.findViewById(R.id.ivImportant);
			holder.resolvedImageView = (ImageView) convertView
					.findViewById(R.id.imageview_resolved);
			holder.ivAvatar = (ImageView) convertView
					.findViewById(R.id.ivAvatar);
			holder.threadingNumberTextView = (TextView) convertView
					.findViewById(R.id.textview_threading_number);
			holder.txtBody = (TextView) convertView.findViewById(R.id.tvBody);
			holder.llchatContainer = (LinearLayout) convertView
					.findViewById(R.id.llchart_container);
			holder.sohButton = (ImageButton) convertView
					.findViewById(R.id.show_or_hide_detail);
			convertView.setTag(holder);
		} else {
			holder = (MessageViewHolder) convertView.getTag();
		}
		if (item == null)
			return convertView;
		final TextView tvBody = holder.txtBody;
		final ImageButton showOrHideButton = holder.sohButton;
		final SentMessageItem viewItem = item;
		holder.sohButton.setOnClickListener(new OnClickListener() {
			boolean flag_show = true;

			@Override
			public void onClick(View v) {
				// TODO Auto-generated method stub
				if (flag_show) {
					String text = viewItem.getBody().getBody();
					tvBody.setText(text);
					showOrHideButton.setImageResource(R.drawable.arrow_up);
					flag_show = !flag_show;
				} else {
					int lineEndIndex = tvBody.getLayout().getLineEnd(4);
					String text = tvBody.getText().subSequence(0,
							lineEndIndex - 3)
							+ "...";
					tvBody.setText(text);
					showOrHideButton.setImageResource(R.drawable.arrow_down);
					flag_show = !flag_show;
				}

			}
		});
		ViewTreeObserver vto = tvBody.getViewTreeObserver();
		vto.addOnGlobalLayoutListener(new OnGlobalLayoutListener() {
			boolean ifInit = true;

			public void onGlobalLayout() {
				if (getLines() > 5) {
					if (ifInit) {
						int lineEndIndex = tvBody.getLayout().getLineEnd(4);
						String text = tvBody.getText().subSequence(0,
								lineEndIndex - 3)
								+ "...";
						tvBody.setText(text);
						showOrHideButton
								.setImageResource(R.drawable.arrow_down);
						ifInit = false;
					}
					showOrHideButton.setVisibility(View.VISIBLE);
				} else {
					showOrHideButton.setVisibility(View.GONE);
				}

			}

			public int getLines() {
				int totalWidth = (int) tvBody.getPaint().measureText(
						viewItem.getBody().getBody());
				int lineWidth = tvBody.getMeasuredWidth();
				int count = totalWidth / lineWidth;
				if (totalWidth % lineWidth != 0) {
					count++;
				}
				return count;
			}

		});

		ImageDownload download = new ImageDownload(this.context,
				String.valueOf(item.getId()), holder.ivAvatar,
				R.drawable.avatar_male_small);
		AppValues appValues = new AppValues(this.context);
		download.execute(appValues.getServerURL() + item.getSender().getPhoto());
		final int userId = item.getSender().getId();
		final String userName = item.getSender().getName();
		holder.ivAvatar.setOnClickListener(new View.OnClickListener() {

			@Override
			public void onClick(View v) {
				Intent intent = new Intent(context, DoctorDetailActivity.class);
				intent.putExtra("userId", userId);
				intent.putExtra("name", userName);
				context.startActivity(intent);

			}
		});
		holder.txtBody.setText(item.getBody().getBody());
		holder.txtUser.setText(item.getSender().getName());
		holder.txtSubject.setText(item.getSubject());
		holder.txtTimestamp.setText(Utils.getDateTimeFormat(
				item.getTimeStamp() * 1000, appValues.getTimeFormat(),
				appValues.getTimezone()));
		if (item.isHasAttachements()) {
			holder.imageAttchment.setVisibility(View.VISIBLE);
		} else {
			holder.imageAttchment.setVisibility(View.GONE);
		}
		if (item.isUrgent()) {
			holder.imageImportant.setVisibility(View.VISIBLE);
		} else {
			holder.imageImportant.setVisibility(View.GONE);
		}
		if (item.isResolved()) {
			holder.resolvedImageView.setVisibility(View.VISIBLE);
		} else {
			holder.resolvedImageView.setVisibility(View.GONE);
		}
		Typeface typeBold = Typeface.create(Typeface.DEFAULT, Typeface.BOLD);
		Typeface typeNormal = Typeface
				.create(Typeface.DEFAULT, Typeface.NORMAL);
		if (item.isRead()) {
			holder.txtSubject.setTypeface(typeNormal);
			holder.txtSubject.setTextColor(context.getResources().getColor(
					R.color.white));
		} else {
			holder.txtSubject.setTypeface(typeBold);
		}
		if (item.getRefer().equalsIgnoreCase("NO"))
			holder.txtSubject.setTextColor(context.getResources().getColor(
					R.color.red));
		int threadingCount = item.getThreadingCount();
		if (threadingCount <= 1) {
			holder.threadingNumberTextView.setVisibility(View.GONE);
		} else {
			if (threadingCount < 1000) {
				holder.threadingNumberTextView.setText(String
						.valueOf(threadingCount));
			} else {
				holder.threadingNumberTextView.setText("999+");
			}
			holder.threadingNumberTextView.setVisibility(View.VISIBLE);
		}
		return convertView;
	}

	static class MessageViewHolder {
		public LinearLayout llchatContainer;
		public TextView txtUser;
		public TextView txtSubject;
		public TextView txtBody;
		public TextView txtTimestamp;
		public ImageView imageAttchment;
		public ImageView imageImportant;
		public ImageView resolvedImageView;
		public ImageView ivAvatar;
		public TextView threadingNumberTextView;
		public ImageButton sohButton;
	}

}
