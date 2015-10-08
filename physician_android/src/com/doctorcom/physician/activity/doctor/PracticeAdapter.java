package com.doctorcom.physician.activity.doctor;

import java.util.ArrayList;
import java.util.List;

import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.BaseAdapter;
import android.widget.Button;
import android.widget.ImageView;
import android.widget.TextView;

import com.doctorcom.android.R;
import com.doctorcom.physician.AppValues;
import com.doctorcom.physician.activity.message.MessageNewActivity;
import com.doctorcom.physician.net.ImageDownload;
import com.doctorcom.physician.net.NetConstantValues;
import com.doctorcom.physician.utils.CallBack;

public class PracticeAdapter extends BaseAdapter {
	protected Context context;
	private LayoutInflater mInflater;
	private List<PracticeItem> mData;
	
	public PracticeAdapter(Context context) {
		this.context = context;
		mInflater = LayoutInflater.from(context);
	}

	@Override
	public int getCount() {
		if (mData == null) {
			return 0;
		}
		return mData.size();
	}
	
	public void setItem(List<PracticeItem> list) {
		mData = list;
	}
	

	@Override
	public PracticeItem getItem(int position) {
		if (mData == null) {
			return null;
		}
		if(position >= mData.size())
			return null;
		else
			return mData.get(position);
	}

	@Override
	public long getItemId(int position) {
		return position;
	}
	
	public void addItem(PracticeItem item) {
		if (mData == null) {
			mData = new ArrayList<PracticeItem>();
		}
		mData.add(item);
	}
	
	public void addItems(List<PracticeItem> items) {
		for (int i = 0, length = items.size(); i < length; i++ ) {
			PracticeItem item = items.get(i);
			addItem(item);
		}
	}
	
	public void initItems(List<PracticeItem> items) {
		if (mData != null) {
			mData.clear();
			mData = null;
		} else {
			mData = new ArrayList<PracticeItem>();
		}
		if (items != null) {
			addItems(items);
		}
	}


	@Override
	public View getView(int position, View convertView, ViewGroup parent) {
		PracticeViewHolder holder;
		if (convertView == null) {
			convertView = mInflater.inflate(R.layout.cell_practice, null);
			holder = new PracticeViewHolder();
			holder.PracticePhotoImageView = (ImageView) convertView.findViewById(R.id.ivPracticePhoto);
			holder.nameTextView = (TextView) convertView.findViewById(R.id.tvName);
			holder.messageButton = (Button) convertView.findViewById(R.id.btMessage);
			holder.callButton = (Button) convertView.findViewById(R.id.btCall);
			convertView.setTag(holder);
		} else {
			holder = (PracticeViewHolder) convertView.getTag();
		}
		final PracticeItem item = getItem(position);
		holder.nameTextView.setText(item.getPracticeName());
		//set message
		holder.messageButton.setOnClickListener(new View.OnClickListener() {
			
			@Override
			public void onClick(View v) {
				Intent intent = new Intent(context, MessageNewActivity.class);
				intent.putExtra("userId", item.getId());
				intent.putExtra("name", item.getPracticeName());
				intent.putExtra("dispatcher", DoctorDetailActivity.MESSAGE_DISPATCHER_PRACTICE);
				context.startActivity(intent);
				((Activity)context).overridePendingTransition(R.anim.up, R.anim.hold);

			}
		});
		if (item.isHasManager()) {
			holder.messageButton.setEnabled(true);
			holder.messageButton.setBackgroundResource(R.drawable.icon_message);
		} else {
			holder.messageButton.setEnabled(false);
			holder.messageButton.setBackgroundResource(R.drawable.icon_message_disable);
		}
		// set call
		if (item.isHasMobile()) {
			holder.callButton.setBackgroundResource(R.drawable.icon_call);
			holder.callButton.setEnabled(true);
			holder.callButton.setOnClickListener(new View.OnClickListener() {
				
				@Override
				public void onClick(View v) {
					CallBack callBack = new CallBack(context);
					callBack.call(NetConstantValues.CALL_USER.getPath(String.valueOf(item.getId())), null);
					
				}
			});
		} else {
			holder.callButton.setBackgroundResource(R.drawable.icon_call_disable);
			holder.callButton.setEnabled(false);
		}
		if (!item.getPracticePhoto().equals("")) {
			ImageDownload practiceImageDownloader = new ImageDownload(context, "org" + String.valueOf(item.getId()), holder.PracticePhotoImageView, -1);
			AppValues appValues = new AppValues(context);
			practiceImageDownloader.execute(appValues.getServerURL()
							+ item.getPracticePhoto());
			holder.PracticePhotoImageView.setVisibility(View.VISIBLE);
		} else {
			holder.PracticePhotoImageView.setVisibility(View.GONE);
		}

		return convertView;
	}
	
	static class PracticeViewHolder {
		public ImageView  PracticePhotoImageView;
		public TextView nameTextView;
		public Button messageButton, callButton;
		
	}

}
