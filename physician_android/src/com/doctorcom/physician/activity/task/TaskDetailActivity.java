package com.doctorcom.physician.activity.task;

import java.util.HashMap;

import android.app.Activity;
import android.app.AlertDialog;
import android.app.ProgressDialog;
import android.content.Context;
import android.content.DialogInterface;
import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.ImageView;
import android.widget.TextView;
import android.widget.Toast;

import com.doctorcom.android.R;
import com.doctorcom.physician.AppValues;
import com.doctorcom.physician.net.NetConstantValues;
import com.doctorcom.physician.net.http.NetConncet;
import com.doctorcom.physician.utils.DocLog;
import com.doctorcom.physician.utils.JsonErrorProcess;
import com.doctorcom.physician.utils.Utils;
import com.doctorcom.physician.utils.cache.Cache;

public class TaskDetailActivity extends Activity {

	private final String TAG = "TaskDetailActivity";
	public final int TASK_EDIT = 1;
	private TextView descriptionTextView, dueTextView, noteTextView;
	private Button doneButton, editButton, deleteButton;
	private TaskItem item;
	private ImageView priorityImageView, doneImageView;
	
	@Override
	protected void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
		setContentView(R.layout.activity_task_detail);
		
		Intent intent = getIntent();
		item = (TaskItem) intent.getSerializableExtra("task");
		
		descriptionTextView = (TextView) findViewById(R.id.tvDescription);
		dueTextView = (TextView) findViewById(R.id.tvDue);
		noteTextView = (TextView) findViewById(R.id.tvNote);
		doneButton = (Button) findViewById(R.id.btDone);
		editButton = (Button) findViewById(R.id.btEdit);
		deleteButton = (Button) findViewById(R.id.btDelete);
		priorityImageView = (ImageView) findViewById(R.id.ivPriority);
		doneImageView = (ImageView) findViewById(R.id.ivDone);
		init();
	}
	
	private void init() {
		descriptionTextView.setText(item.getDescription());
		AppValues appValues = new AppValues(this);
		dueTextView.setText(Utils.getDateFormat(item.getDueTimeStamp() * 1000, appValues.getTimezone()));
		noteTextView.setText(item.getNote());
		int priority = item.getPriority();
//		Drawable priorityDrawable;
		if (priority == TaskItem.TASK_PRIORITY_HIGH) {
			priorityImageView.setVisibility(View.VISIBLE);
			priorityImageView.setImageResource(R.drawable.icon_arrow_high);
//			priorityDrawable = getResources().getDrawable(R.drawable.icon_arrow_high);
//			priorityDrawable.setBounds(0, 0, priorityDrawable.getMinimumWidth(), priorityDrawable.getMinimumHeight());
//			descriptionTextView.setCompoundDrawables(priorityDrawable, null, null, null);
		} else if (priority == TaskItem.TASK_PRIORITY_LOW) {
			priorityImageView.setVisibility(View.VISIBLE);
			priorityImageView.setImageResource(R.drawable.icon_arrow_low);
//			priorityDrawable = getResources().getDrawable(R.drawable.icon_arrow_low);
//			priorityDrawable.setBounds(0, 0, priorityDrawable.getMinimumWidth(), priorityDrawable.getMinimumHeight());
//			descriptionTextView.setCompoundDrawables(priorityDrawable, null, null, null);
		} else {
			priorityImageView.setVisibility(View.GONE);
		}
		setDoneStatus();
		doneButton.setOnClickListener(new TaskDone(this, item.getId()));
		editButton.setOnClickListener(new View.OnClickListener() {
			
			@Override
			public void onClick(View v) {
				Intent intent = new Intent(TaskDetailActivity.this, TaskNewActivity.class);
				intent.putExtra("task", item);
				startActivityForResult(intent, TASK_EDIT);
				overridePendingTransition(R.anim.up, R.anim.hold);
				
			}
		});
		deleteButton.setOnClickListener(new TaskDelete(this, item.getId()));
		Button backButton = (Button) findViewById(R.id.btBack);
		backButton.setOnClickListener(new View.OnClickListener() {
			
			@Override
			public void onClick(View v) {
				 finish();
				
			}
		});

	}
	
	private void setDoneStatus() {
		if (item.isDone()) {
			doneButton.setText(R.string.undone);
			doneImageView.setVisibility(View.VISIBLE);
		} else {
			doneButton.setText(R.string.done);
			doneImageView.setVisibility(View.GONE);
		}
	
	}
	
	@Override
	protected void onActivityResult(int requestCode, int resultCode, Intent data) {
		if (resultCode == RESULT_OK) {
			switch (requestCode) {
			case TASK_EDIT:
				item = (TaskItem) data.getSerializableExtra("task");
				init();
				setResult(RESULT_OK);
				break;
			}
		}
	}

	class TaskDelete implements View.OnClickListener {

		private Context mContext;
		private int TaskId;
		
		public TaskDelete(Context context, int id) {
			mContext = context;
			TaskId = id;
		}
		
		@Override
		public void onClick(View v) {
			AlertDialog.Builder builder = new AlertDialog.Builder(mContext);
			builder.setTitle(R.string.warning_title)
			.setMessage(getResources().getString(R.string.followup_delete_warning_content) +  getResources().getString(R.string.question_mark))
			.setPositiveButton(R.string.ok, new DialogInterface.OnClickListener() {

				@Override
				public void onClick(DialogInterface dialog, int which) {
					final ProgressDialog progress = ProgressDialog.show(TaskDetailActivity.this, "", getString(R.string.process_text));

					NetConncet netConncet = new NetConncet(mContext,NetConstantValues.FOLLOWUPS_DELETE.getPath(String.valueOf(TaskId))) {

						@Override
						protected void onPostExecute(String result) {
							super.onPostExecute(result);
							progress.dismiss();
							if (JsonErrorProcess.checkJsonError(result, mContext)) {
								Toast.makeText(mContext,R.string.delete_successfully,Toast.LENGTH_SHORT).show();
								Cache.resetFollowupTaskList();
								DocLog.d(TAG, "delete " + TaskId);
								setResult(RESULT_OK);
								finish();
							}
						}
						
					};
					netConncet.execute();
				}
				
			})
			.setNegativeButton(R.string.cancel, new DialogInterface.OnClickListener() {

				@Override
				public void onClick(DialogInterface dialog, int which) {
					dialog.dismiss();
					
				}
				
			});
			builder.show();
		}
		
	}
	
	class TaskDone implements View.OnClickListener {

		private boolean isDone;
		private Context mContext;
		private int TaskId;

		public TaskDone (Context context, int id) {
			mContext = context;
			TaskId = id;
		}
		
		@Override
		public void onClick(View v) {
			isDone = item.isDone();
			final ProgressDialog progress = ProgressDialog.show(mContext, "", getString(R.string.process_text));
			HashMap<String, String> params = new HashMap<String, String>();
			params.put(NetConstantValues.FOLLOWUPS_UPDATE.PARAM_DONE,Boolean.toString(!isDone));

			NetConncet netConncet = new NetConncet(mContext,NetConstantValues.FOLLOWUPS_UPDATE.getPath(String.valueOf(TaskId)), params) {

				@Override
				protected void onPostExecute(String result) {
					super.onPostExecute(result);
					progress.dismiss();
					if (JsonErrorProcess.checkJsonError(result, mContext)) {
						Toast.makeText(mContext,R.string.saved_successfully,Toast.LENGTH_SHORT).show();
						Cache.resetFollowupTaskList();
						item.setDone(!isDone);
						setDoneStatus();
						setResult(RESULT_OK);
					}
				}
			};
			netConncet.execute();
			
		}
		
	}

}
