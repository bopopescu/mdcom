package com.doctorcom.physician.activity.task;

import java.util.Calendar;
import java.util.HashMap;
import java.util.TimeZone;

import android.app.ProgressDialog;
import android.content.Intent;
import android.os.Bundle;
import android.support.v4.app.DialogFragment;
import android.support.v4.app.FragmentActivity;
import android.text.Html;
import android.view.View;
import android.widget.Button;
import android.widget.CheckBox;
import android.widget.EditText;
import android.widget.RadioGroup;
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

public class TaskNewActivity extends FragmentActivity implements DatePickerFragment.DateSelectedListener {

	private final String TAG  ="TaskNewActivity";
	private TextView dueTextView;
	private long due;
	private EditText descriptionEditText, noteEditText;
	private RadioGroup priorityRadioGroup;
	private CheckBox isDoneCheckBox;
	@SuppressWarnings("unused")
	private boolean isEdit, messageTask = false;;
	private TaskItem item;
	AppValues appValues;

	@Override
	protected void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
		setContentView(R.layout.activity_task_new);
		
		dueTextView = (TextView) findViewById(R.id.tvDue);
		descriptionEditText = (EditText) findViewById(R.id.etSubject);
		noteEditText = (EditText) findViewById(R.id.etContent);
		priorityRadioGroup = (RadioGroup) findViewById(R.id.rgPriority);
        isDoneCheckBox = (CheckBox) findViewById(R.id.cbDone);
		appValues = new AppValues(this);

        Intent intent = getIntent();
        messageTask = intent.getBooleanExtra("isMessageTask", false);
		item = (TaskItem) intent.getSerializableExtra("task");
		if (item != null) {
			due = item.getDueTimeStamp() * 1000;
			dueTextView.setText(Utils.getDateFormat(due, appValues.getTimezone()));
			String description = item.getDescription();
			descriptionEditText.setText(description);
			descriptionEditText.setSelection(description.length());
			noteEditText.setText(item.getNote());
			setPriority(item.getPriority());
			TextView titleTextView = (TextView) findViewById(R.id.tvTitle);
			titleTextView.setText(R.string.edit_task);
			isEdit = true;
			isDoneCheckBox.setChecked(item.isDone());
		} else {
			Calendar mCalendar = Calendar.getInstance(TimeZone.getTimeZone(appValues.getTimezone()));
			mCalendar.set(Calendar.HOUR_OF_DAY, 23);
			mCalendar.set(Calendar.MINUTE, 59);
			mCalendar.set(Calendar.SECOND, 59);
			due = mCalendar.getTimeInMillis();
			dueTextView.setText(Utils.getDateFormat(due, appValues.getTimezone()));
			isEdit = false;
			findViewById(R.id.trDone).setVisibility(View.GONE);
			findViewById(R.id.ivLine).setVisibility(View.GONE);
			
			String description = intent.getStringExtra("description");
			String note = intent.getStringExtra("note");
			if (description!= null && !description.equals("")) {
				String strDescription = getString(R.string.task_on) + description;
				descriptionEditText.setText(strDescription);
				descriptionEditText.setSelection(strDescription.length());
				noteEditText.setText(note);
			}
		}
		dueTextView.setOnClickListener(new View.OnClickListener() {
			
			@Override
			public void onClick(View v) {
				DialogFragment newFragment = new DatePickerFragment();
				Bundle args = new Bundle();
				args.putLong("timestamp", due);
				newFragment.setArguments(args);
				newFragment.show(getSupportFragmentManager(), "datePicker");
				
			}
		});
		
		Button saveButton = (Button) findViewById(R.id.btSave);
		if (isEdit) {
			saveButton.setOnClickListener(new TaskEdit());
		} else {
			saveButton.setOnClickListener(new TaskSave());
		}
		Button closeButton = (Button) findViewById(R.id.btClose);
		closeButton.setOnClickListener(new View.OnClickListener() {
			
			@Override
			public void onClick(View v) {
				closeActivity();
				
			}
		});
	}

	class TaskSave implements View.OnClickListener {

		@Override
		public void onClick(View v) {
			String description = descriptionEditText.getText().toString();
			if (description.equals("")) {
				Toast.makeText(TaskNewActivity.this, R.string.description_empty, Toast.LENGTH_LONG).show();
				descriptionEditText.requestFocus();
				return;
			}
			String note = noteEditText.getText().toString();
			int priority = getPriority();
			final ProgressDialog progress = ProgressDialog.show(TaskNewActivity.this, "", getString(R.string.process_text));
			HashMap<String, String> params = new HashMap<String, String>();
			params.put(NetConstantValues.FOLLOWUPS_NEW.PARAM_DESCRIPTION, description); 
			params.put(NetConstantValues.FOLLOWUPS_NEW.PARAM_DUE, String.valueOf(due / 1000)); 
			params.put(NetConstantValues.FOLLOWUPS_NEW.PARAM_NOTE, note); 
			params.put(NetConstantValues.FOLLOWUPS_NEW.PARAM_PRIORITY, String.valueOf(priority)); 

			NetConncet netConncet = new NetConncet(TaskNewActivity.this,NetConstantValues.FOLLOWUPS_NEW.PATH, params) {

				@Override
				protected void onPostExecute(String result) {
					super.onPostExecute(result);
					progress.dismiss();
					if (JsonErrorProcess.checkJsonError(result, TaskNewActivity.this)) {
						Toast.makeText(TaskNewActivity.this,R.string.saved_successfully,Toast.LENGTH_SHORT).show();
						Cache.resetFollowupTaskList();
						setResult(RESULT_OK);
						finish();						
					}
				}
			};
			netConncet.execute();
		}
		
	}
	
	class TaskEdit implements View.OnClickListener {

		@Override
		public void onClick(View v) {
			final String description = descriptionEditText.getText().toString();
			if (description.equals("")) {
				descriptionEditText.setError(Html.fromHtml(getString(R.string.cannot_be_empty)));
				return;
			}
			final String note = noteEditText.getText().toString();
			final int priority = getPriority();
			final boolean isDone = isDoneCheckBox.isChecked();
			final ProgressDialog progress = ProgressDialog.show(TaskNewActivity.this, "", getString(R.string.process_text));
			HashMap<String, String> params = new HashMap<String, String>();
			params.put(NetConstantValues.FOLLOWUPS_NEW.PARAM_DESCRIPTION, description); 
			params.put(NetConstantValues.FOLLOWUPS_NEW.PARAM_DUE, String.valueOf(due / 1000)); 
			params.put(NetConstantValues.FOLLOWUPS_NEW.PARAM_NOTE, note); 
			params.put(NetConstantValues.FOLLOWUPS_NEW.PARAM_PRIORITY, String.valueOf(priority)); 
			params.put(NetConstantValues.FOLLOWUPS_UPDATE.PARAM_DONE,Boolean.toString(isDone));
			NetConncet netConncet = new NetConncet(TaskNewActivity.this,NetConstantValues.FOLLOWUPS_UPDATE.getPath(String.valueOf(item.getId())), params) {

				@Override
				protected void onPostExecute(String result) {
					super.onPostExecute(result);
					progress.dismiss();
					if (JsonErrorProcess.checkJsonError(result, TaskNewActivity.this)) {
						Toast.makeText(TaskNewActivity.this,R.string.saved_successfully,Toast.LENGTH_SHORT).show();
						Cache.resetFollowupTaskList();
						Intent intent = new Intent();
						item.setDescription(description);
						item.setNote(note);
						item.setPriority(priority);
						item.setDone(isDone);
						item.setDueTimeStamp(due / 1000);
						intent.putExtra("task", item);
						setResult(RESULT_OK, intent);
						DocLog.d(TAG, "edit " + item.getId());
						finish();
					}
				}
			};
			netConncet.execute();
			
		}
		
	}
	
	private int getPriority(){
		int prioritySelect = priorityRadioGroup.getCheckedRadioButtonId();
		int priority;
		switch (prioritySelect) {
		case R.id.rHigh:
			priority =TaskItem.TASK_PRIORITY_HIGH;
			break;
		case R.id.rMed:
			priority =TaskItem.TASK_PRIORITY_MIDDLE;
			break;
		case R.id.rLow:
			priority =TaskItem.TASK_PRIORITY_LOW;
			break;
		default:
			priority = TaskItem.TASK_PRIORITY_MIDDLE;
			break;
		}
		return priority;
	}

	private void setPriority(int priority) {
		switch(priority) {
		case TaskItem.TASK_PRIORITY_HIGH:
			priorityRadioGroup.check(R.id.rHigh);
			break;
		case TaskItem.TASK_PRIORITY_MIDDLE:
			priorityRadioGroup.check(R.id.rMed);
			break;
		case TaskItem.TASK_PRIORITY_LOW:
			priorityRadioGroup.check(R.id.rLow);
			break;
		}
	}	
	
	@Override
	public void onBackPressed() {
		super.onBackPressed();
		overridePendingTransition(0, R.anim.down);
	}
	public void closeActivity() {
		finish();
		overridePendingTransition(0, R.anim.down);
	}

	@Override
	public void onDateSelectedFinish(long timestamp) {
		due = timestamp;
		dueTextView.setText(Utils.getDateFormat(timestamp, appValues.getTimezone()));
	}

}
