package com.doctorcom.physician.activity.message;

import java.io.File;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;

import org.json.JSONException;
import org.json.JSONObject;

import android.app.Activity;
import android.app.AlertDialog;
import android.app.ProgressDialog;
import android.content.Context;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.DialogInterface.OnCancelListener;
import android.graphics.Typeface;
import android.media.AudioManager;
import android.media.MediaPlayer;
import android.media.MediaPlayer.OnCompletionListener;
import android.os.Bundle;
import android.support.v4.app.FragmentActivity;
import android.support.v4.app.FragmentManager;
import android.telephony.PhoneStateListener;
import android.telephony.TelephonyManager;
import android.text.TextUtils.TruncateAt;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.View;
import android.view.View.OnClickListener;
import android.view.ViewGroup;
import android.view.ViewTreeObserver;
import android.view.ViewTreeObserver.OnGlobalLayoutListener;
import android.widget.BaseAdapter;
import android.widget.Button;
import android.widget.ImageButton;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;

import com.doctorcom.android.R;
import com.doctorcom.physician.AppValues;
import com.doctorcom.physician.activity.doctor.DoctorDetailActivity;
import com.doctorcom.physician.activity.message.AttachmentsActivity.DesFilePlay;
import com.doctorcom.physician.activity.message.ReceivedMessageItem.Attachment;
import com.doctorcom.physician.activity.message.ReceivedMessageItem.Body;
import com.doctorcom.physician.net.ImageDownload;
import com.doctorcom.physician.utils.DocLog;
import com.doctorcom.physician.utils.FileUtil;
import com.doctorcom.physician.utils.ProgressCancelDialog;
import com.doctorcom.physician.utils.Utils;
import com.doctorcom.physician.utils.ProgressCancelDialog.DownloadFinishListener;

public class ReceivedMessageAdapter extends BaseAdapter implements
		DownloadFinishListener {
	protected Context context;
	private LayoutInflater mInflater;
	private List<ReceivedMessageItem> mData;
	private int index = 0;
	@SuppressWarnings("unused")
	private AppValues appValues;
	private boolean speakOn = true;
	private AudioManager am = null;
	protected int curPosition;
	private final String TAG = "ReceivedMessageAdapter";
	private boolean[] retryDownloadFile;
	private List<File> desFileList;
	private MediaPlayer mediaPlayer;
	private int lastPosition;
	private TelephonyManager mTelephonyMgr;
	private com.doctorcom.physician.activity.message.ReceivedMessageAdapter.TeleListener mTeleListener;
	private final int MAX_LINES = 100;
	private final int COMMON_LINES = 5;

	public ReceivedMessageAdapter(Context context) {
		this.context = context;
		appValues = new AppValues(context);
		mInflater = LayoutInflater.from(context);
		am = (AudioManager) context.getSystemService(Context.AUDIO_SERVICE);
		mediaPlayer = new MediaPlayer();
		mediaPlayer.setOnCompletionListener(new OnCompletionListener() {

			@Override
			public void onCompletion(MediaPlayer mp) {
				ReceivedMessageItem item = getItem(curPosition);
				item.setIsPlaying("no");
				notifyDataSetChanged();

			}
		});
		mTelephonyMgr = (TelephonyManager) context
				.getSystemService(Context.TELEPHONY_SERVICE);
		// Registers a listener object to receive notification of changes in
		// specified telephony states
		mTeleListener = new TeleListener();
		mTelephonyMgr.listen(mTeleListener,
				PhoneStateListener.LISTEN_CALL_STATE);

	}

	@Override
	public int getCount() {
		if (mData == null) {
			return 0;
		}
		return mData.size();
	}

	@Override
	public ReceivedMessageItem getItem(int position) {
		if (mData == null) {
			return null;
		}
		return mData.get(position);
	}

	public void addItem(ReceivedMessageItem item) {
		if (mData == null) {
			mData = new ArrayList<ReceivedMessageItem>();
		}
		mData.add(item);
	}

	public void addItems(List<ReceivedMessageItem> items) {
		index = getCount();
		for (int i = 0, length = items.size(); i < length; i++) {
			ReceivedMessageItem item = items.get(i);
			addItem(item);
		}
		boolean[] tempRetryDownloadFile = new boolean[retryDownloadFile.length
				+ items.size()];
		boolean[] addRetryDownloadFile = new boolean[items.size()];
		for (int i = 0, len = addRetryDownloadFile.length; i < len; i++) {
			addRetryDownloadFile[i] = false;
		}
		System.arraycopy(retryDownloadFile, 0, tempRetryDownloadFile, 0,
				retryDownloadFile.length);
		System.arraycopy(addRetryDownloadFile, 0, tempRetryDownloadFile,
				retryDownloadFile.length, addRetryDownloadFile.length);
		retryDownloadFile = tempRetryDownloadFile;
		tempRetryDownloadFile = null;
		addRetryDownloadFile = null;
	}

	public void setMessageBody(ArrayList<Body> list) {
		int size = mData.size();
		for (int i = index; i < size; i++) {
			Body itemBody = list.get(i - index);
			String id = itemBody.getId();
			ReceivedMessageItem item = getItem(i);

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
				setMessageBody2(list);
				return;
			}
		}
	}

	public void setMessageBody2(ArrayList<Body> list) {
		HashMap<String, ReceivedMessageItem> messageMap = getMessageMap();
		int length = list.size();
		for (int i = 0; i < length; i++) {
			Body itemBody = list.get(i);
			String id = itemBody.getId();
			ReceivedMessageItem item = messageMap.get(id);

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

	public HashMap<String, ReceivedMessageItem> getMessageMap() {
		int size = mData.size();
		HashMap<String, ReceivedMessageItem> messageMap = new HashMap<String, ReceivedMessageItem>();
		for (int i = 0; i < size; i++) {
			ReceivedMessageItem item = mData.get(i);
			String id = item.getId();
			messageMap.put(id, item);
		}
		return messageMap;

	}

	public void addTopItems(List<ReceivedMessageItem> items) {
		if (mData == null) {
			mData = new ArrayList<ReceivedMessageItem>();
		}
		for (int i = items.size(); i > 0; i--) {
			ReceivedMessageItem item = items.get(i - 1);
			mData.add(0, item);
		}
	}

	public void initItems(List<ReceivedMessageItem> items) {
		index = 0;
		if (mData != null) {
			mData.clear();
			mData = null;
		} else {
			mData = new ArrayList<ReceivedMessageItem>();
		}
		if (items != null) {
			retryDownloadFile = new boolean[items.size()];
			for (int i = 0, len = retryDownloadFile.length; i < len; i++) {
				retryDownloadFile[i] = false;
			}
			desFileList = new ArrayList<File>();
			addItems(items);
		}

	}

	@Override
	public long getItemId(int position) {
		return position;
	}

	void checkAndPlay(String messageId) {
		String appPath = FileUtil.getAppPath(context);
		if (appPath == null) {
			Toast.makeText(context, R.string.sdcard_unavailable,
					Toast.LENGTH_LONG).show();
			return;
		}
		ReceivedMessageItem item = getItem(curPosition);
		Attachment attach = item.getBody().getAttachments()[0];
		String attchmentId = attach.getId();
		String attchmentFileName = attach.getFilename();
		long fileSize = attach.getFilesize();

		File file = new File(appPath, attchmentId + attchmentFileName);
		if (file.exists()) {
			startMediaPlayer(file.getAbsolutePath());
		} else {
			startDownload(messageId, attchmentId, attchmentFileName, fileSize);
		}
	}

	public void startDownload(String messageId, String attchmentId,
			String attchmentFileName, long fileSize) {
		FragmentManager fm = ((FragmentActivity) context)
				.getSupportFragmentManager();
		ProgressCancelDialog pd = new ProgressCancelDialog();
		pd.setType("not none");
		pd.setDownloadInterface(this);
		Bundle args = new Bundle();
		args.putString("messageId", messageId);
		args.putString("attchmentId", attchmentId);
		args.putString("fileName", attchmentFileName);
		args.putLong("fileSize", fileSize);
		pd.setArguments(args);
		pd.show(fm, TAG);

	}

	@Override
	public void onFinishDownload(String result) {
		try {
			JSONObject obj = new JSONObject(result);
			if (!obj.isNull("errno")) {
				File originalFilePath = new File(obj.getString("data"));
				retryDownload(originalFilePath);
				if (Utils.isDeviceDissociated(result)) {
					Toast.makeText(context, obj.getString("descr"),
							Toast.LENGTH_LONG).show();
					((Activity) context).finish();
				}
			} else {
				play(new File(obj.getString("data")));
			}

		} catch (JSONException e) {
			String appPath = FileUtil.getAppPath(context);
			ReceivedMessageItem item = getItem(curPosition);
			Attachment attach = item.getBody().getAttachments()[0];
			String attchmentId = attach.getId();
			String attchmentFileName = attach.getFilename();
			if (appPath != null) {
				retryDownload(new File(appPath + "/des_tag_" + attchmentId
						+ attchmentFileName));
			} else {
				Toast.makeText(context, R.string.sdcard_unavailable,
						Toast.LENGTH_LONG).show();
			}
		}

	}

	private void retryDownload(File originalFilePath) {
		if (originalFilePath.exists())
			originalFilePath.delete();
		File encryptFilePath = new File(originalFilePath.getParent(),
				originalFilePath.getName().substring("des_tag_".length()));
		if (encryptFilePath.exists())
			encryptFilePath.delete();
		// bad file, download again
		ReceivedMessageItem item = getItem(curPosition);
		final String messageId = item.getId();
		Attachment attach = item.getBody().getAttachments()[0];
		final String attchmentId = attach.getId();
		final String attchmentFileName = attach.getFilename();
		final long fileSize = attach.getFilesize();

		if (retryDownloadFile[curPosition]) {
			AlertDialog.Builder builder = new AlertDialog.Builder(context);
			builder.setTitle(R.string.error)
					.setMessage(R.string.load_failed_retry)
					.setPositiveButton(R.string.yes,
							new DialogInterface.OnClickListener() {

								@Override
								public void onClick(DialogInterface dialog,
										int which) {
									dialog.dismiss();
									retryDownloadFile[curPosition] = false;
									startDownload(messageId, attchmentId,
											attchmentFileName, fileSize);
								}
							})
					.setNegativeButton(R.string.no,
							new DialogInterface.OnClickListener() {

								@Override
								public void onClick(DialogInterface dialog,
										int which) {
									dialog.dismiss();

								}
							}).show();
		} else {
			retryDownloadFile[curPosition] = true;
			startDownload(messageId, attchmentId, attchmentFileName, fileSize);
		}

	}

	private void startMediaPlayer(String encryptFileName) {
		final File encryptFilePath = new File(encryptFileName);
		final String originalFileName = encryptFilePath.getParent().toString()
				+ "/des_tag_" + encryptFilePath.getName();
		final File originalFilePath = new File(originalFileName);
		if (originalFilePath.exists()) {
			play(originalFilePath);
		} else {
			final ProgressDialog progress = ProgressDialog.show(context, "",
					context.getString(R.string.decrypting_file));
			final DesFilePlay desFilePlay = new DesFilePlay(encryptFileName,
					originalFileName, context) {

				@Override
				protected void onPostExecute(final String result) {
					progress.dismiss();
					if (result == null || result.equals("")) {
						retryDownload(originalFilePath);
					} else {
						play(originalFilePath);
					}
				}

			};

			progress.setCancelable(true);
			progress.setOnCancelListener(new OnCancelListener() {

				@Override
				public void onCancel(DialogInterface dialog) {
					if (!desFilePlay.isCancelled()) {
						desFilePlay.cancel(true);
					}
				}
			});
			desFilePlay.execute();
		}

	}

	private void play(File originalFilePath) {
		desFileList.add(originalFilePath);
		try {
			if (mediaPlayer.isPlaying()) {
				if (curPosition == lastPosition) {
					mediaPlayer.stop();
					ReceivedMessageItem item = getItem(curPosition);
					item.setIsPlaying("no");
					notifyDataSetChanged();
				} else {
					for (int i = 0, count = getCount(); i < count; i++) {
						getItem(i).setIsPlaying("no");
					}
					mediaPlayer.reset();
					mediaPlayer.setDataSource(originalFilePath
							.getAbsolutePath());
					mediaPlayer.prepare();
					mediaPlayer.start();
					ReceivedMessageItem item = getItem(curPosition);
					item.setIsPlaying("yes");
					notifyDataSetChanged();
					lastPosition = curPosition;
				}
			} else {
				mediaPlayer.reset();
				mediaPlayer.setDataSource(originalFilePath.getAbsolutePath());
				mediaPlayer.prepare();
				mediaPlayer.start();
				ReceivedMessageItem item = getItem(curPosition);
				item.setIsPlaying("yes");
				notifyDataSetChanged();
				lastPosition = curPosition;
			}
		} catch (Exception e) {
			retryDownload(originalFilePath);
			DocLog.d(TAG, "Exception", e);
		}
	}

	private void setVoiceHolder(MessageViewHolder holder, View convertView) {
		holder.rlVoiceBody = (LinearLayout) convertView
				.findViewById(R.id.voice_body);
		holder.playButton = (Button) convertView.findViewById(R.id.btPlay);
		holder.speakSwichButton = (Button) convertView
				.findViewById(R.id.btSpeak_on_off);
		holder.callBackNumber = (TextView) convertView
				.findViewById(R.id.call_back_number);
		holder.callbackButton = (Button) convertView.findViewById(R.id.btCallBack);
	}

	private void setCommonHolder(MessageViewHolder holder, View convertView) {
		holder.llchatContainer = (LinearLayout) convertView
				.findViewById(R.id.llchart_container);
		holder.txtSubject = (TextView) convertView.findViewById(R.id.tvTitle);
		holder.txtUser = (TextView) convertView.findViewById(R.id.tvName);
		holder.txtTimestamp = (TextView) convertView.findViewById(R.id.tvDate);
		holder.imageAttchment = (ImageView) convertView
				.findViewById(R.id.ivAttach);
		holder.imageImportant = (ImageView) convertView
				.findViewById(R.id.ivImportant);
		holder.resolvedImageView = (ImageView) convertView
				.findViewById(R.id.imageview_resolved);
		holder.ivAvatar = (ImageView) convertView.findViewById(R.id.ivAvatar);
		holder.threadingNumberTextView = (TextView) convertView
				.findViewById(R.id.textview_threading_number);
		holder.sohButton = (ImageButton) convertView
				.findViewById(R.id.show_or_hide_detail);
	}

	@Override
	public View getView(int position, View convertView, ViewGroup parent) {
		ReceivedMessageItem item = getItem(position);
		MessageViewHolder holder = new MessageViewHolder();
		if (item == null)
			return convertView;
		boolean isVoice = item.getMessage_type().equalsIgnoreCase("VM")
				|| item.getMessage_type().equalsIgnoreCase("ANS");
		if (isVoice) {
			convertView = mInflater.inflate(R.layout.cell_message_voice, null);
			this.setVoiceHolder(holder, convertView);
		} else {
			convertView = mInflater.inflate(R.layout.cell_threading_from, null);
			holder.txtBody = (TextView) convertView.findViewById(R.id.tvBody);

		}
		this.setCommonHolder(holder, convertView);
		if (!isVoice) {
			final TextView tvBody = holder.txtBody;
			final ImageButton showOrHideButton = holder.sohButton;
			final ReceivedMessageItem viewItem = item;
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
						showOrHideButton
								.setImageResource(R.drawable.arrow_down);
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

		}
		ImageDownload download = new ImageDownload(this.context, item.getId(),
				holder.ivAvatar, R.drawable.avatar_male_small);
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
		if (item.getMessage_type().equalsIgnoreCase("VM")
				|| item.getMessage_type().equalsIgnoreCase("ANS")) {
			Attachment[] attachments = item.getBody().getAttachments();
			if (attachments.length < 1) {
				holder.rlVoiceBody.setVisibility(View.INVISIBLE);
			} else {
				holder.rlVoiceBody.setVisibility(View.VISIBLE);
				if (attachments.length == 1) {
					final int pos = position;

					// will be recovered
					// **************************************************************
					// final String messageId = item.getId();
					// **************************************************************

					// imitational codes
					// **************************************************************
					final String messageId = "36765ed3c686412f8419b505aa86a2cf";
					// **************************************************************
					holder.playButton.setOnClickListener(new OnClickListener() {

						@Override
						public void onClick(View arg0) {
							curPosition = pos;
							checkAndPlay(messageId);
						}

					});
					CommonMessageMethods.setLinkString(holder.callBackNumber, item.getCallback_number());
					boolean callBackAvailable = true;
					try {
						callBackAvailable = new JSONObject(item.getBody().getJsonStrMessageDetail()).getJSONObject("data").getBoolean("callback_available");
					} catch (JSONException e) {
					}
					
					CommonMessageMethods.setCallBackButton(holder.callbackButton, context, item.getCallback_number(), callBackAvailable);
					if (item.getIsPlaying().equals("yes")) {
						holder.playButton
								.setBackgroundResource(R.drawable.chat_button_stop);
					} else {
						holder.playButton
								.setBackgroundResource(R.drawable.chat_button_play);
					}

					if (speakOn) {
						am.setSpeakerphoneOn(true);
						am.setMode(AudioManager.MODE_NORMAL);
						((Activity) context)
								.setVolumeControlStream(AudioManager.STREAM_MUSIC);
						holder.speakSwichButton
								.setBackgroundResource(R.drawable.chat_speak_on);
					} else {
						am.setSpeakerphoneOn(false);
						am.setMode(AudioManager.MODE_IN_CALL);
						holder.speakSwichButton
								.setBackgroundResource(R.drawable.chat_speak_off);
					}
					holder.speakSwichButton
							.setOnClickListener(new View.OnClickListener() {

								@Override
								public void onClick(View v) {
									speakOn = !speakOn;
									notifyDataSetChanged();

								}
							});
				} else {
					// error
					holder.rlVoiceBody.setVisibility(View.GONE);
				}
			}
		} else
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
			holder.llchatContainer
					.setBackgroundResource(R.drawable.chatfrom_read);
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
		public TextView txtUser;
		public TextView txtSubject;
		public TextView txtBody;
		public TextView txtTimestamp;
		public ImageView imageAttchment;
		public ImageView imageImportant;
		public ImageView resolvedImageView;
		public ImageView ivAvatar;
		public TextView threadingNumberTextView;
		public LinearLayout rlVoiceBody;
		public Button playButton;
		public Button speakSwichButton;
		public TextView callBackNumber;
		public LinearLayout llchatContainer;
		public ImageButton sohButton;
		public Button callbackButton;
	}

	class TeleListener extends PhoneStateListener {

		@Override
		public void onCallStateChanged(int state, String incomingNumber) {
			super.onCallStateChanged(state, incomingNumber);
			switch (state) {
			case TelephonyManager.CALL_STATE_IDLE: {
				DocLog.d(TAG, "CALL_STATE_IDLE" + incomingNumber);
				break;
			}
			case TelephonyManager.CALL_STATE_OFFHOOK: {
				DocLog.d(TAG, "CALL_STATE_OFFHOOK" + incomingNumber);
				if (mediaPlayer != null && mediaPlayer.isPlaying()) {
					mediaPlayer.stop();
					for (int i = 0, count = getCount(); i < count; i++) {
						getItem(i).setIsPlaying("no");
					}
					notifyDataSetChanged();
				}
				break;
			}
			case TelephonyManager.CALL_STATE_RINGING: {
				DocLog.d(TAG, "CALL_STATE_RINGING" + incomingNumber);
				if (mediaPlayer != null && mediaPlayer.isPlaying()) {
					mediaPlayer.stop();
					for (int i = 0, count = getCount(); i < count; i++) {
						getItem(i).setIsPlaying("no");
					}
					notifyDataSetChanged();
				}
				break;
			}
			default:
				break;
			}
		}

	}

	public void clean() {
		if (desFileList != null)
			for (int i = 0, len = desFileList.size(); i < len; i++) {
				desFileList.get(i).delete();
			}
		if (am != null)
			am.setMode(AudioManager.MODE_NORMAL);
		if (mediaPlayer != null) {
			mediaPlayer.release();
			mediaPlayer = null;
		}
		if (mTeleListener != null)
			mTelephonyMgr.listen(mTeleListener, PhoneStateListener.LISTEN_NONE);
	}

}
