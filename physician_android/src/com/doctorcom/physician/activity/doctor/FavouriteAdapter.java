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

public class FavouriteAdapter extends BaseAdapter {
	protected Context context;
	private LayoutInflater mInflater;
	private List<FavoriteItem> mData;
	
	public FavouriteAdapter(Context context) {
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

	public void setItem(List<FavoriteItem> list) {
		mData = new ArrayList<FavoriteItem>();
		for (int i = 0, len = list.size(); i < len; i++) {
			mData.add(list.get(i));
		}
	}
	
	@Override
	public FavoriteItem getItem(int position) {
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
	
	public void addItem(FavoriteItem item) {
		if (mData == null) {
			mData = new ArrayList<FavoriteItem>();
		}
		mData.add(item);
	}
	
	public void addItems(List<FavoriteItem> items) {
		for (int i = 0, length = items.size(); i < length; i++ ) {
			FavoriteItem item = items.get(i);
			addItem(item);
		}
	}
	
	public void initItems(List<FavoriteItem> items) {
		if (mData != null) {
			mData.clear();
			mData = null;
		} else {
			mData = new ArrayList<FavoriteItem>();
		}
		if (items != null) {
			addItems(items);
		}
	}

	@Override
	public View getView(int position, View convertView, ViewGroup parent) {
		DocLog.d("getView", String.valueOf(mData.size()));
		FavouriteViewHolder holder;
		if (convertView == null) {
			convertView = mInflater.inflate(R.layout.cell_favourite, null);
			holder = new FavouriteViewHolder();
			holder.avatarImageView = (ImageView) convertView.findViewById(R.id.ivAvatar);
			holder.PracticePhotoImageView = (ImageView) convertView.findViewById(R.id.ivPracticePhoto);
			holder.nameTextView = (TextView) convertView.findViewById(R.id.tvName);
			holder.TypeDisplayTextView = (TextView) convertView.findViewById(R.id.tvtype_display);
			holder.messageButton = (Button) convertView.findViewById(R.id.btMessage);
			holder.pageButton = (Button) convertView.findViewById(R.id.btPage);
			holder.callButton = (Button) convertView.findViewById(R.id.btCall);
			convertView.setTag(holder);
		} else {
			holder = (FavouriteViewHolder) convertView.getTag();
		}
		final FavoriteItem item = getItem(position);
		if (item == null) return convertView;
		holder.nameTextView.setText(item.getObject_name());
		holder.TypeDisplayTextView.setText(item.getObject_type_display());
		//set message
		holder.messageButton.setOnClickListener(new View.OnClickListener() {
			
			@Override
			public void onClick(View v) {
				Intent intent = new Intent(context, MessageNewActivity.class);
				intent.putExtra("userId", item.getObject_id());
				intent.putExtra("name", item.getObject_name());
				if(item.getObject_type_flag()==2)
					intent.putExtra("dispatcher", DoctorDetailActivity.MESSAGE_DISPATCHER_PRACTICE);
				context.startActivity(intent);
				((Activity)context).overridePendingTransition(R.anim.up, R.anim.hold);

			}
		});
		if (item.isMsg_available()) {
			holder.messageButton.setEnabled(true);
			holder.messageButton.setBackgroundResource(R.drawable.icon_message);
		} else {
			holder.messageButton.setEnabled(false);
			holder.messageButton.setBackgroundResource(R.drawable.icon_message_disable);
		}
		//set page
		if(item.getObject_type_flag()==1){
			if (item.isPager_available()) {
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
												callBack.userPage(String.valueOf(item.getObject_id()), ((EditText)textEntryView.findViewById(R.id.etReason)).getText().toString());
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
		}
		else{
			holder.pageButton.setVisibility(View.GONE);
		}
		
		// set call
		if (item.isCall_available()) {
			holder.callButton.setBackgroundResource(R.drawable.icon_call);
			holder.callButton.setEnabled(true);
			holder.callButton.setOnClickListener(new View.OnClickListener() {
				
				@Override
				public void onClick(View v) {
					CallBack callBack = new CallBack(context);
					callBack.call(NetConstantValues.CALL_USER.getPath(String.valueOf(item.getObject_id())), null);
					
				}
			});
		} else {
			holder.callButton.setBackgroundResource(R.drawable.icon_call_disable);
			holder.callButton.setEnabled(false);
		}
		ImageDownload download = new ImageDownload(context, "favourite" + String.valueOf(item.getObject_id()) + String.valueOf(position), holder.avatarImageView, R.drawable.avatar_male_small);
		AppValues appValues = new AppValues(context);
		download.execute(appValues.getServerURL() + item.getPhoto());
		if (!item.getPrefer_logo().equals("")) {
			ImageDownload practiceImageDownloader = new ImageDownload(context, String.valueOf(item.getObject_id()), holder.PracticePhotoImageView, -1);
			practiceImageDownloader.execute(appValues.getServerURL() + item.getPrefer_logo());
			holder.PracticePhotoImageView.setVisibility(View.VISIBLE);
		} else {
			holder.PracticePhotoImageView.setVisibility(View.GONE);
		}
		
		return convertView;
	}
	
	static class FavouriteViewHolder {
		public ImageView avatarImageView, PracticePhotoImageView;
		public TextView nameTextView, TypeDisplayTextView;
		public Button messageButton, pageButton, callButton;
		
	}

}
