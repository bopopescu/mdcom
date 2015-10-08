package com.doctorcom.physician.activity.message;

import android.app.AlertDialog;
import android.app.ProgressDialog;
import android.content.Context;
import android.content.Intent;
import android.os.Bundle;
import android.support.v4.app.Fragment;
import android.support.v4.app.FragmentActivity;
import android.support.v4.app.FragmentManager;
import android.support.v4.app.FragmentTransaction;
import android.support.v4.content.LocalBroadcastManager;
import android.view.View;
import android.widget.Button;
import android.widget.TextView;
import android.widget.Toast;

import com.doctorcom.android.R;
import com.doctorcom.physician.activity.message.MessageDetailActivity.MessageDetailFragment.onNeedRefreshListener;
import com.doctorcom.physician.net.NetConstantValues;
import com.doctorcom.physician.net.http.NetConncet;
import com.doctorcom.physician.utils.DocLog;
import com.doctorcom.physician.utils.JsonErrorProcess;
import com.doctorcom.physician.utils.ProgressCancelDialog.DownloadFinishListener;
import com.doctorcom.physician.utils.cache.Cache;

public class MessageActivity extends FragmentActivity implements DownloadFinishListener, onNeedRefreshListener {

	public interface onPlayListener {
		void onPlay(String file);
	}

	public interface onRefreshThreading {
		void onRefresh();
	}

	private String TAG = "MessageActivity";
	private TextView titleTextView;
	private Button previousButton, nextButton, removeButton;
	private int position, count;
	private boolean needRefresh, received;
	private boolean[] allThreading, allRefer, allRead, allResolved;
	private Bundle args;
	private String[] allMessageIds, allThreadingUUID, allMessageSubject;
	private int[] allActionHistoryCounts;
	private final int REFRESH = 1;
	private final int REPLY = 2;
	private String[] allReferStatus;
	private String[] allMessageDetails;

	@Override
	protected void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
		setContentView(R.layout.activity_message);
		Intent intent = getIntent();
		FragmentManager fm = getSupportFragmentManager();
		FragmentTransaction ft = fm.beginTransaction();
		args = new Bundle();
		received = intent.getBooleanExtra("received", true);
		args.putBoolean("received", received);
		position = intent.getIntExtra("position", 0);
		args.putInt("position", position);
		allMessageIds = intent.getStringArrayExtra("allMessageIds");
		args.putStringArray("allMessageIds", allMessageIds);
		allThreadingUUID = intent.getStringArrayExtra("allThreadingUUID");
		args.putStringArray("allThreadingUUID", allThreadingUUID);
		allMessageSubject = intent.getStringArrayExtra("allMessageSubject");
		args.putStringArray("allMessageSubject", allMessageSubject);
		allThreading = intent.getBooleanArrayExtra("allThreading");
		allRefer = intent.getBooleanArrayExtra("allRefer");
		allRead = intent.getBooleanArrayExtra("allRead");
		allActionHistoryCounts = intent.getIntArrayExtra("allActionHistoryCounts");
		allResolved = intent.getBooleanArrayExtra("allResolved");
		count = allMessageIds.length;
		args.putIntArray("allActionHistoryCounts", allActionHistoryCounts);
		args.putBooleanArray("allResolved", allResolved);
		allReferStatus = intent.getStringArrayExtra("allReferStatus");
		allMessageDetails = intent.getStringArrayExtra("allMessageDetails");
		args.putStringArray("allReferStatus", allReferStatus);
		args.putStringArray("allMessageDetails", allMessageDetails);
		args.putBooleanArray("allRefer", allRefer);
		

		titleTextView = (TextView) findViewById(R.id.tvDC);
		previousButton = (Button) findViewById(R.id.btPrevious);
		nextButton = (Button) findViewById(R.id.btNext);
		removeButton = (Button) findViewById(R.id.btRemove);
		initTitle();
		Fragment fragment;
		if (allThreading[position]) {
			fragment = Fragment.instantiate(this, ThreadingListActivity.ThreadingistFragment.class.getName(), args);
		} else {
			fragment = Fragment.instantiate(this, MessageDetailActivity.MessageDetailFragment.class.getName(), args);
		}
		ft.add(R.id.framelayout_contain, fragment);
		ft.commit();
	}
	
	public void onPrevious(View view) {
		if (position > 0) {
			position--;
			args.putInt("position", position);
			Fragment fragment;
			if (allThreading[position]) {
				fragment = Fragment.instantiate(this, ThreadingListActivity.ThreadingistFragment.class.getName(), args);
			} else {
				fragment = Fragment.instantiate(this, MessageDetailActivity.MessageDetailFragment.class.getName(), args);
			}
			FragmentManager fm = getSupportFragmentManager();
			FragmentTransaction ft = fm.beginTransaction();
			ft.replace(R.id.framelayout_contain, fragment);
			ft.commit();
			initTitle();
		}
	}

	public void onNext(View view) {
		if (position < count -1) {
			position++;
			args.putInt("position", position);
			Fragment fragment;
			if (allThreading[position]) {
				fragment = Fragment.instantiate(this, ThreadingListActivity.ThreadingistFragment.class.getName(), args);
			} else {
				fragment = Fragment.instantiate(this, MessageDetailActivity.MessageDetailFragment.class.getName(), args);
			}
			FragmentManager fm = getSupportFragmentManager();
			FragmentTransaction ft = fm.beginTransaction();
			ft.replace(R.id.framelayout_contain, fragment);
			ft.commit();
			initTitle();
		}
	}
	
	public void onRemove(View view) {
		Context mContext = this;
		AlertDialog.Builder builder = new AlertDialog.Builder(
				mContext);
		builder.setMessage(R.string.delete_message_warning)
				.setCancelable(false)
				.setPositiveButton(
						R.string.yes,
						new android.content.DialogInterface.OnClickListener() {
							public void onClick(
									android.content.DialogInterface dialog,
									int id) {

								DocLog.d(TAG, "delete message");

								deleteMessage(allMessageIds[position]);
							}
						})
				.setNegativeButton(
						R.string.no,
						new android.content.DialogInterface.OnClickListener() {
							public void onClick(
									android.content.DialogInterface dialog,
									int id) {
							}
						});
		AlertDialog alert = builder.create();
		alert.show();

	}

	protected void deleteMessage(String messageId) {
		final ProgressDialog progress = ProgressDialog.show(this, "", getString(R.string.message_deleting));
		final NetConncet httpConn = new NetConncet(this, NetConstantValues.MESSAGE_DELETE.getPath(messageId)) {

			@Override
			protected void onPostExecute(String result) {
				super.onPostExecute(result);
				progress.dismiss();
				if (JsonErrorProcess.checkJsonError(result, MessageActivity.this)) {
					Toast.makeText(MessageActivity.this, R.string.delete_successfully, Toast.LENGTH_LONG).show();
					setResult(RESULT_OK);
					finish();
				}
			}
		};
		httpConn.execute();
	}

	private void initTitle() {
		if (position == 0) {
			previousButton.setBackgroundResource(R.drawable.button_previous_disable);
		} else {
			previousButton.setBackgroundResource(R.drawable.button_previous);
		}
		if (position == (count - 1)) {
			nextButton.setBackgroundResource(R.drawable.button_next_disable);
		} else {
			nextButton.setBackgroundResource(R.drawable.button_next);
		}
//		titleTextView.setText(String.valueOf(position + 1) + " " + getString(R.string.of) + " " + count);
		titleTextView.setText(allMessageSubject[position]);
		if (allRefer[position] || allThreading[position]) {
			removeButton.setEnabled(false);
			removeButton.setBackgroundResource(R.drawable.top_button_delete_disable);

		} else {
			removeButton.setEnabled(true);
			removeButton.setBackgroundResource(R.drawable.remove_selector);

		}
		if (!allRead[position]) {
			needRefresh = true;
		}
	}
	
	public void setNeedRefresh() {
		if (needRefresh) {
			Cache.resetThtreaingList();
			Cache.resetReceivedMessageList();
			Cache.resetSentMessageList();
			LocalBroadcastManager.getInstance(this).sendBroadcast(new Intent("refreshAction").putExtra("cmd", 5).putExtra("isRedeived", received));
			setResult(RESULT_OK);
		}
	}
	
	public void onBack(View view) {
		setNeedRefresh();
		finish();
	}

	@Override
	public void onBackPressed() {
		setNeedRefresh();
		super.onBackPressed();
	}

	@Override
	protected void onActivityResult(int requestCode, int resultCode, Intent data) {
		if (resultCode == RESULT_OK) {
			switch(requestCode) {
			case REFRESH:
				needRefresh = true;
				onRefreshThreading f = (onRefreshThreading) getSupportFragmentManager().findFragmentById(R.id.framelayout_contain);
				f.onRefresh();
				break;
			case REPLY:
				needRefresh = true;
				break;
			}
		}
	}

	@Override
	public void onFinishDownload(String result) {
		FragmentManager fm = getSupportFragmentManager();
		Fragment fragment = fm.findFragmentById(R.id.framelayout_contain);
		onPlayListener p = (onPlayListener) fragment;
		p.onPlay(result);
		
	}

	@Override
	public void onNeedRefresh() {
		needRefresh = true;
		
	}
}
