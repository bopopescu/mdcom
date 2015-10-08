package com.doctorcom.physician.activity.task;

import java.util.ArrayList;
import java.util.List;

import android.content.Context;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.BaseAdapter;
import android.widget.ImageView;
import android.widget.TextView;

import com.doctorcom.android.R;
import com.doctorcom.physician.AppValues;
import com.doctorcom.physician.utils.Utils;

public class TaskAdapter extends BaseAdapter {

	protected Context context;
	private LayoutInflater mInflater;
	private List<TaskItem> mData;
	
	public TaskAdapter(Context context) {
		mInflater = LayoutInflater.from(context);
		this.context = context;
	}
	
	@Override
	public int getCount() {
		if (mData == null) {
			return 0;
		}
		return mData.size();
	}

	@Override
	public TaskItem getItem(int position) {
		if (mData == null) {
			return null;
		}
		if(position >= mData.size())
			return null;
		else
			return mData.get(position);
	}
	public void addItem(TaskItem item) {
		if (mData == null) {
			mData = new ArrayList<TaskItem>();
		}
		mData.add(item);
	}
	
	public void addItems(List<TaskItem> items) {
		for (int i = 0, length = items.size(); i < length; i++ ) {
			TaskItem item = items.get(i);
			addItem(item);
		}
	}
	
	public void addTopItems(List<TaskItem> items) {
		if (mData == null) {
			mData = new ArrayList<TaskItem>();
		}
		for (int i = items.size(); i > 0; i-- ) {
			TaskItem item = items.get(i -1);
			mData.add(0, item);
		}	
	}
	
	public void initItems(List<TaskItem> items) {
		if (mData != null) {
			mData.clear();
			mData = null;
		}
		mData = new ArrayList<TaskItem>();

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
		TaskViewHolder holder;
		if (convertView == null) {
			convertView = mInflater.inflate(R.layout.cell_task, null);
			holder = new TaskViewHolder();
			holder.descriptionTextView = (TextView) convertView.findViewById(R.id.tvDescription);
			holder.dueTextView = (TextView) convertView.findViewById(R.id.tvDue);
			holder.noteTextView = (TextView) convertView.findViewById(R.id.tvNote);
			holder.priorityImageView = (ImageView) convertView.findViewById(R.id.ivPriority);
			holder.doneImageView = (ImageView) convertView.findViewById(R.id.ivDone);
			convertView.setTag(holder);
		} else {
			holder = (TaskViewHolder) convertView.getTag();
		}
		TaskItem item = getItem(position);
		if (item == null) return convertView;
		if (item.getPriority() == TaskItem.TASK_PRIORITY_HIGH) {
			holder.priorityImageView.setVisibility(View.VISIBLE);
			holder.priorityImageView.setImageResource(R.drawable.task_priority_high_selector);
		} else if (item.getPriority() == TaskItem.TASK_PRIORITY_LOW) {
			holder.priorityImageView.setVisibility(View.VISIBLE);
			holder.priorityImageView.setImageResource(R.drawable.task_priority_low_selector);
		} else {
			holder.priorityImageView.setVisibility(View.INVISIBLE);
		}
		if (item.isDone()) {
			holder.doneImageView.setVisibility(View.VISIBLE);
			holder.descriptionTextView.setTextColor(context.getResources().getColor(R.color.message_time_selector));
			holder.dueTextView.setTextColor(context.getResources().getColor(R.color.message_time_selector));
			holder.noteTextView.setTextColor(context.getResources().getColor(R.color.message_time_selector));
		} else {
			holder.doneImageView.setVisibility(View.INVISIBLE);
			holder.descriptionTextView.setTextColor(context.getResources().getColor(R.color.message_name_selector));
			holder.dueTextView.setTextColor(context.getResources().getColor(R.color.message_title_selector));
			holder.noteTextView.setTextColor(context.getResources().getColor(R.color.message_title_selector));
		}
		holder.descriptionTextView.setText(item.getDescription());
		
        AppValues appValues = new AppValues(context);       
        holder.dueTextView.setText(Utils.getDateFormat(item.getDueTimeStamp() * 1000, appValues.getTimezone()));
		holder.noteTextView.setText(item.getNote());
		return convertView;
	}
	
	static class TaskViewHolder {
		public TextView descriptionTextView, dueTextView, noteTextView;
		public ImageView priorityImageView, doneImageView;
	}

}
