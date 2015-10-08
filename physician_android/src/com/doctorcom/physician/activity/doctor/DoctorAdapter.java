package com.doctorcom.physician.activity.doctor;

import java.util.ArrayList;
import java.util.List;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Context;
import android.content.Intent;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.BaseAdapter;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ImageView;
import android.widget.TextView;

import com.doctorcom.android.R;
import com.doctorcom.physician.AppValues;
import com.doctorcom.physician.activity.message.MessageNewActivity;
import com.doctorcom.physician.net.ImageDownload;
import com.doctorcom.physician.net.NetConstantValues;
import com.doctorcom.physician.utils.CallBack;
import com.doctorcom.physician.utils.DocLog;

public class DoctorAdapter extends BaseAdapter {
	protected Context context;
	private LayoutInflater mInflater;
	private List<DoctorItem> mData;
	
	public DoctorAdapter(Context context) {
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

	public void setItem(List<DoctorItem> list) {
		mData = new ArrayList<DoctorItem>();
		for (int i = 0, len = list.size(); i < len; i++) {
			mData.add(list.get(i));
		}
	}
	
	@Override
	public DoctorItem getItem(int position) {
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
	
	public void addItem(DoctorItem item) {
		if (mData == null) {
			mData = new ArrayList<DoctorItem>();
		}
		mData.add(item);
	}
	
	public void addItems(List<DoctorItem> items) {
		for (int i = 0, length = items.size(); i < length; i++ ) {
			DoctorItem item = items.get(i);
			addItem(item);
		}
	}
	
	public void initItems(List<DoctorItem> items) {
		if (mData != null) {
			mData.clear();
			mData = null;
		} else {
			mData = new ArrayList<DoctorItem>();
		}
		if (items != null) {
			addItems(items);
		}
	}

	@Override
	public View getView(int position, View convertView, ViewGroup parent) {
		DocLog.d("getView", String.valueOf(mData.size()));
		DoctorViewHolder holder;
		if (convertView == null) {
			convertView = mInflater.inflate(R.layout.cell_doctor, null);
			holder = new DoctorViewHolder();
			holder.avatarImageView = (ImageView) convertView.findViewById(R.id.ivAvatar);
			holder.PracticePhotoImageView = (ImageView) convertView.findViewById(R.id.ivPracticePhoto);
			holder.nameTextView = (TextView) convertView.findViewById(R.id.tvName);
			holder.specialtyTextView = (TextView) convertView.findViewById(R.id.tvSpecialty);
			holder.messageButton = (Button) convertView.findViewById(R.id.btMessage);
			holder.pageButton = (Button) convertView.findViewById(R.id.btPage);
			holder.callButton = (Button) convertView.findViewById(R.id.btCall);
			convertView.setTag(holder);
		} else {
			holder = (DoctorViewHolder) convertView.getTag();
		}
		final DoctorItem item = getItem(position);
		if (item == null) return convertView;
//		holder.nameTextView.setText(item.getLastName() + " " + item.getFirstName());
		holder.nameTextView.setText(item.getFullname());
		holder.specialtyTextView.setText(item.getSpecialty());
		//set message
		holder.messageButton.setOnClickListener(new View.OnClickListener() {
			
			@Override
			public void onClick(View v) {
				Intent intent = new Intent(context, MessageNewActivity.class);
				intent.putExtra("userId", item.getId());
				intent.putExtra("name", item.getFirstName() + " " + item.getLastName());
				context.startActivity(intent);
				((Activity)context).overridePendingTransition(R.anim.up, R.anim.hold);

			}
		});
		//set page
		if (item.isHasPager()) {
			holder.pageButton.setBackgroundResource(R.drawable.icon_page);
			holder.pageButton.setEnabled(true);
			holder.pageButton.setOnClickListener(new View.OnClickListener() {
				
				@Override
				public void onClick(View v) {
		            LayoutInflater factory = LayoutInflater.from(context);
		            final View textEntryView = factory.inflate(R.layout.alert_dialog_text_entry, null);
		            ((TextView) textEntryView.findViewById(R.id.tvTitle)).setText(R.string.leave_your_number_here);
		            AlertDialog.Builder builder = new AlertDialog.Builder(context);
					builder.setTitle(R.string.page_title).setView(textEntryView)
							.setPositiveButton(R.string.ok,
									new android.content.DialogInterface.OnClickListener() {
										public void onClick(android.content.DialogInterface dialog, int id) {
											CallBack callBack = new CallBack(context);
											callBack.userPage(String.valueOf(item.getId()), ((EditText)textEntryView.findViewById(R.id.etReason)).getText().toString());
										}
									})
							.setNegativeButton(R.string.cancel,
									new android.content.DialogInterface.OnClickListener() {
										public void onClick(android.content.DialogInterface dialog,
												int id) {
											dialog.cancel();
										}
									});
					AlertDialog alert = builder.create();
					alert.show();

				}
			});
		} else {
			holder.pageButton.setBackgroundResource(R.drawable.icon_page_disable);
			holder.pageButton.setEnabled(false);
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
		ImageDownload download = new ImageDownload(this.context, String.valueOf(item.getId()), holder.avatarImageView, R.drawable.avatar_male_small);
		AppValues appValues = new AppValues(this.context);
		download.execute(appValues.getServerURL() + item.getThumbnail());
		if (item.getPrefer_logo() != null && !item.getPrefer_logo().equals("")) {
			ImageDownload practiceImageDownloader = new ImageDownload(this.context, "user_org"+String.valueOf(item.getId()), holder.PracticePhotoImageView, -1);
			practiceImageDownloader.execute(appValues.getServerURL() + item.getPrefer_logo());
			holder.PracticePhotoImageView.setVisibility(View.VISIBLE);
		} else {
			holder.PracticePhotoImageView.setVisibility(View.GONE);
		}
		
		return convertView;
	}
	
	static class DoctorViewHolder {
		public ImageView avatarImageView, PracticePhotoImageView;
		public TextView nameTextView, specialtyTextView;
		public Button messageButton, pageButton, callButton;
		
	}

}
