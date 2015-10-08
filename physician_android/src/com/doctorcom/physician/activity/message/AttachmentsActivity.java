package com.doctorcom.physician.activity.message;

import java.io.File;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import android.app.AlertDialog;
import android.app.ProgressDialog;
import android.content.Context;
import android.content.DialogInterface;
import android.content.DialogInterface.OnCancelListener;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.content.pm.ResolveInfo;
import android.media.AudioManager;
import android.media.MediaPlayer;
import android.media.MediaPlayer.OnCompletionListener;
import android.os.AsyncTask;
import android.os.Bundle;
import android.support.v4.app.FragmentActivity;
import android.support.v4.app.FragmentManager;
import android.telephony.PhoneStateListener;
import android.telephony.TelephonyManager;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.AdapterView;
import android.widget.BaseAdapter;
import android.widget.Button;
import android.widget.ImageView;
import android.widget.ListView;
import android.widget.TextView;
import android.widget.Toast;

import com.doctorcom.android.R;
import com.doctorcom.android.document.pdf.PdfViewerActivity;
import com.doctorcom.physician.AppValues;
import com.doctorcom.physician.utils.AESEncryptDecrypt;
import com.doctorcom.physician.utils.AESEncryptDecrypt.AESEncryptDecryptException;
import com.doctorcom.physician.utils.DocLog;
import com.doctorcom.physician.utils.FileUtil;
import com.doctorcom.physician.utils.PreferLogo;
import com.doctorcom.physician.utils.ProgressCancelDialog;
import com.doctorcom.physician.utils.ProgressCancelDialog.DownloadFinishListener;
import com.doctorcom.physician.utils.Utils;

public class AttachmentsActivity extends FragmentActivity implements DownloadFinishListener {

	private final String TAG = "AttachmentsActivity";
	private ListView mListView;
	private AttachmentsAdapter adapter;
	private MediaPlayer mediaPlayer;
	private int curPosition, lastPosition = -1;
	private AudioManager am = null;
	private TelephonyManager mTelephonyMgr = null;
	private TeleListener mTeleListener = null;
	private List<File> desFileList;
	private boolean[] retryDownloadFile;
	private String messageId;
	private ImageView ivPreferLogoImageView;
	@Override
	protected void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
		setContentView(R.layout.activity_attachments);
	    ivPreferLogoImageView = (ImageView)findViewById(R.id.ivPreferLogo);
	    PreferLogo.showPreferLogo(this, ivPreferLogoImageView);
		am = (AudioManager) getSystemService(Context.AUDIO_SERVICE);
		mTelephonyMgr = (TelephonyManager)getSystemService(Context.TELEPHONY_SERVICE);
		// Registers a listener object to receive notification of changes in specified telephony states
		mTeleListener = new TeleListener();
		mTelephonyMgr.listen(mTeleListener, PhoneStateListener.LISTEN_CALL_STATE);
		Intent intent = getIntent();
		String attachments = intent.getStringExtra("attachments");
		messageId = intent.getStringExtra("messageId");
		mListView = (ListView) findViewById(R.id.lvAttachments);
		adapter = new AttachmentsAdapter(this, messageId);
		mediaPlayer = new MediaPlayer();
		mediaPlayer.setOnCompletionListener(new OnCompletionListener() {
			
			@Override
			public void onCompletion(MediaPlayer mp) {
				Map<String, String> map = adapter.getItem(curPosition);
				map.put("isPlaying", "no");
				adapter.notifyDataSetChanged();
				
			}
		});
		
		mListView.setOnItemClickListener(new AdapterView.OnItemClickListener() {

			@Override
			public void onItemClick(AdapterView<?> parent, View view, int position, long id) {
				curPosition = position;
				checkAndPlay(messageId);
			}
		});
		Button btBack = (Button) findViewById(R.id.btBack);
		btBack.setOnClickListener(new View.OnClickListener() {
			
			@Override
			public void onClick(View v) {
				finish();
				
			}
		});
		setList(attachments);
		desFileList = new ArrayList<File>();
	}
	
	public void setList(String attachments) {
		ArrayList<Map<String, String>> list = new ArrayList<Map<String, String>>();
		try {
			JSONObject jObj = new JSONObject(attachments);
			JSONArray jArr = jObj.getJSONArray("attachments");
			for (int i = 0, len = jArr.length(); i < len; i++) {
				Map<String, String> map = new HashMap<String, String>();
				JSONObject jsonOpt = jArr.optJSONObject(i);
				String strAttchmentId = jsonOpt.getString("id");
				String strAttchmentfileName = jsonOpt.getString("filename");
				String fileSize = jsonOpt.getString("filesize");
				map.put("attchmentId", strAttchmentId);
				map.put("attchmentFileName", strAttchmentfileName);
				map.put("fileSize", fileSize);
				map.put("isPlaying", "no");
				list.add(map);
			}
			adapter.init(list);
			retryDownloadFile = new boolean[list.size()];
			for (int i = 0, len = retryDownloadFile.length; i < len; i++) {
				retryDownloadFile[i] = false;
			}
			mListView.setAdapter(adapter);
			
		} catch (JSONException e) {
			DocLog.e(TAG, "JSONException", e);
			Toast.makeText(this, R.string.attachments_cannot_load, Toast.LENGTH_SHORT).show();
			finish();
		}
	}

	class AttachmentsAdapter extends BaseAdapter {
		protected Context context;
		private LayoutInflater mInflater;
		private List<Map<String, String>> mData;
		private String messageId;
		private boolean speakOn = true;

		public AttachmentsAdapter(Context context, String messageId) {
			this.context = context;
			this.messageId = messageId;
			mInflater = LayoutInflater.from(context);
		}
		@Override
		public int getCount() {
			return mData.size();
		}

		@Override
		public Map<String, String> getItem(int position) {
			return mData.get(position);
		}

		@Override
		public long getItemId(int position) {
			return position;
		}
		
		public void init(List<Map<String, String>> list) {
			mData = list;
		}

		@Override
		public View getView(final int position, View convertView, ViewGroup parent) {
			AttachmentsHolder holder;
			if (convertView == null) {
				convertView = mInflater.inflate(R.layout.cell_attachment, null);
				holder = new AttachmentsHolder();
				holder.fileTypeImageView = (ImageView) convertView.findViewById(R.id.ivFileType);
				holder.fileNameTextView = (TextView) convertView.findViewById(R.id.tvFileName);
				holder.fileSizeTextView = (TextView) convertView.findViewById(R.id.tvFileSize);
				holder.playButton = (Button) convertView.findViewById(R.id.btPlay);
				holder.speakSwichButton = (Button) convertView.findViewById(R.id.btSpeak_on_off);
				convertView.setTag(holder);
			} else {
				holder = (AttachmentsHolder) convertView.getTag();
			}
			Map<String, String> map = getItem(position);
			final String attchmentFileName = map.get("attchmentFileName");
			final long fileSize = Long.parseLong(map.get("fileSize"));
			
			String fileType = FileUtil.getMIMEType(attchmentFileName);
			if (fileType.contains("audio")) {
				holder.fileTypeImageView.setImageResource(R.drawable.icon_video_file);
				holder.playButton.setVisibility(View.VISIBLE);
				holder.speakSwichButton.setVisibility(View.VISIBLE);
				if (map.get("isPlaying").equals("yes")) {
					holder.playButton.setBackgroundResource(R.drawable.button_stop);
				} else {
					holder.playButton.setBackgroundResource(R.drawable.button_play);
				}
				
				if (speakOn) {
					am.setSpeakerphoneOn(true);
					am.setMode(AudioManager.MODE_NORMAL);
					setVolumeControlStream(AudioManager.STREAM_MUSIC);
					holder.speakSwichButton.setBackgroundResource(R.drawable.button_speaker_on);
					holder.speakSwichButton.setText(R.string.speaker_on);
				} else {
					am.setSpeakerphoneOn(false);
					am.setMode(AudioManager.MODE_IN_CALL);
					holder.speakSwichButton.setBackgroundResource(R.drawable.button_speaker_off);
					holder.speakSwichButton.setText(R.string.speaker_off);
				}
				holder.speakSwichButton.setOnClickListener(new View.OnClickListener() {
					
					@Override
					public void onClick(View v) {
						speakOn = !speakOn;
						notifyDataSetChanged();
						
					}
				});
			} else {
				if (fileType.contains("image")) {
					holder.fileTypeImageView.setImageResource(R.drawable.icon_img_file);
				} else {
					holder.fileTypeImageView.setImageResource(R.drawable.icon_other_file);
				}
				holder.playButton.setVisibility(View.GONE);
				holder.speakSwichButton.setVisibility(View.GONE);
			}
			holder.fileNameTextView.setText(attchmentFileName);
			holder.fileSizeTextView.setText(FileUtil.getFileSize(fileSize));
			holder.playButton.setOnClickListener(new View.OnClickListener() {
				
				@Override
				public void onClick(View v) {
					curPosition = position;
					checkAndPlay(messageId);
					
				}
			});
			
			return convertView;
		}
		
		class AttachmentsHolder {
			public ImageView fileTypeImageView;
			public TextView fileNameTextView, fileSizeTextView;
			public Button playButton, speakSwichButton;
			
		}

	}
	
	public void startDownload(String messageId, String attchmentId, String attchmentFileName, long fileSize) {
		FragmentManager fm = getSupportFragmentManager();
		ProgressCancelDialog pd = new ProgressCancelDialog();
		Bundle args = new Bundle();
		args.putString("messageId", messageId);
		args.putString("attchmentId", attchmentId);
		args.putString("fileName",attchmentFileName);
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
					Toast.makeText(this, obj.getString("descr"), Toast.LENGTH_LONG).show();
					finish();
				}
			} else {
				play(new File(obj.getString("data")));
			}

		} catch (JSONException e) {
			String appPath = FileUtil.getAppPath(this);
			Map<String, String> map = adapter.getItem(curPosition);
			String attchmentId = map.get("attchmentId");
			String attchmentFileName = map.get("attchmentFileName");
			if (appPath != null) {
				retryDownload(new File(appPath + "/des_tag_" + attchmentId + attchmentFileName));
			} else {
				Toast.makeText(this, R.string.sdcard_unavailable, Toast.LENGTH_LONG).show();
			}
		}
		
	}

	private void startMediaPlayer(String encryptFileName) {
		final File encryptFilePath = new File(encryptFileName);
		final String originalFileName = encryptFilePath.getParent().toString() + "/des_tag_" + encryptFilePath.getName();
		final File originalFilePath = new File(originalFileName);
		if (originalFilePath.exists()) {
			play(originalFilePath);
		} else {
			final ProgressDialog progress = ProgressDialog.show(this, "", getString(R.string.decrypting_file));
			final DesFilePlay desFilePlay = new DesFilePlay(encryptFileName, originalFileName, this) {

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
		String type = FileUtil.getMIMEType(originalFilePath);
		if (type.contains("audio")) {
			try {
				if (mediaPlayer.isPlaying()) {
					if (curPosition == lastPosition) {
						mediaPlayer.stop();
						Map<String, String> map = adapter.getItem(curPosition);
						map.put("isPlaying", "no");
						adapter.notifyDataSetChanged();
					} else {
						for (int i = 0, count = adapter.getCount(); i< count; i++) {
							adapter.getItem(i).put("isPlaying", "no");
						}
						mediaPlayer.reset();
						mediaPlayer.setDataSource(originalFilePath.getAbsolutePath());
						mediaPlayer.prepare();
						mediaPlayer.start();
						Map<String, String> map = adapter.getItem(curPosition);
						map.put("isPlaying", "yes");
						adapter.notifyDataSetChanged();
						lastPosition = curPosition;
					}
				} else {				
					mediaPlayer.reset();
					mediaPlayer.setDataSource(originalFilePath.getAbsolutePath());
					mediaPlayer.prepare();
					mediaPlayer.start();
					Map<String, String> map = adapter.getItem(curPosition);
					map.put("isPlaying", "yes");
					adapter.notifyDataSetChanged();
					lastPosition = curPosition;
				}
			} catch (Exception e) {
				retryDownload(originalFilePath);
				DocLog.d(TAG, "Exception", e);
			}
		} else if (type.contains("pdf")) {
			Intent openIntent = new Intent(this, PdfViewerActivity.class);
			openIntent.putExtra("pdf_document", originalFilePath.getAbsolutePath());
			startActivity(openIntent);
		} else {
			Intent fileOpenIntent = FileUtil.getOpenFileIntent(originalFilePath);
			PackageManager packageManager = getPackageManager();
			List<ResolveInfo> activities = packageManager.queryIntentActivities(fileOpenIntent, 0);
			boolean isIntentSafe = activities.size() > 0;
			if (isIntentSafe) {
				startActivity(fileOpenIntent);
			} else {
				Toast.makeText(this, R.string.not_support_file_type, Toast.LENGTH_LONG).show();
			}
		}
	}

	void checkAndPlay(String messageId) {
		String appPath = FileUtil.getAppPath(this);
		if (appPath == null) {
			Toast.makeText(this, R.string.sdcard_unavailable, Toast.LENGTH_LONG).show();
			return;
		}
		Map<String, String> map = adapter.getItem(curPosition);
		String attchmentId = map.get("attchmentId");
		String attchmentFileName = map.get("attchmentFileName");
		long fileSize = Long.parseLong(map.get("fileSize"));

		File file = new File(appPath, attchmentId + attchmentFileName);
		if (FileUtil.getMIMEType(file).contains("dicom")) {
			Intent openIntent = new Intent(this, DicomViewerActivity.class);
			openIntent.putExtra("messageId", messageId);
			openIntent.putExtra("attachmentId", attchmentId);
			openIntent.putExtra("fileName", attchmentFileName);
			startActivity(openIntent);
			return;
		}
		if (file.exists()) {
			startMediaPlayer(file.getAbsolutePath());
		} else {
			startDownload(messageId, attchmentId, attchmentFileName, fileSize);	
		}
	}
	private void retryDownload(File originalFilePath) {
		if (originalFilePath.exists()) originalFilePath.delete();
		File encryptFilePath = new File(originalFilePath.getParent(), originalFilePath.getName().substring("des_tag_".length()));
		if (encryptFilePath.exists()) encryptFilePath.delete();
		// bad file, download again
		Map<String, String> map = adapter.getItem(curPosition);
		final String attchmentId = map.get("attchmentId");
		final String attchmentFileName = map.get("attchmentFileName");
		final long fileSize = Long.parseLong(map.get("fileSize"));

		if (retryDownloadFile[curPosition]) {
			AlertDialog.Builder builder = new AlertDialog.Builder(this);
			builder.setTitle(R.string.error).setMessage(R.string.load_failed_retry)
			.setPositiveButton(R.string.yes, new DialogInterface.OnClickListener() {
				
				@Override
				public void onClick(DialogInterface dialog, int which) {
					dialog.dismiss();
					retryDownloadFile[curPosition] = false;
					startDownload(messageId, attchmentId, attchmentFileName, fileSize);
				}
			})
			.setNegativeButton(R.string.no, new DialogInterface.OnClickListener() {
				
				@Override
				public void onClick(DialogInterface dialog, int which) {
					dialog.dismiss();
					
				}
			})
			.show();
		} else {
			retryDownloadFile[curPosition] = true;
			startDownload(messageId, attchmentId, attchmentFileName, fileSize);
		}

	}

	public static class DesFilePlay extends AsyncTask<String, Integer, String> {
		private File originalFilePath = null, encryptFilePath = null;
		private Context context;

		public DesFilePlay(String path, String desFileName, Context con) {
			encryptFilePath = new File(path);
			originalFilePath = new File(desFileName);
			context = con;
		}

		@Override
		protected String doInBackground(String... params) {
			try {
				AESEncryptDecrypt fileDes = new AESEncryptDecrypt(AppValues.aeskey, context.getCacheDir().getAbsolutePath() + AppValues.secretKey);
				fileDes.decrypt(encryptFilePath, originalFilePath);
				return originalFilePath.getAbsolutePath();
			} catch (AESEncryptDecryptException e) {
				deleteFilePlay();
				return "";
			}
		}

		private void deleteFilePlay() {
			if (originalFilePath.exists()) originalFilePath.delete();
			if (encryptFilePath.exists()) encryptFilePath.delete();
		}

		@Override
		protected void onCancelled() {
			deleteFilePlay();
			super.onCancelled();
		}
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
				if(mediaPlayer != null && mediaPlayer.isPlaying()) {
					mediaPlayer.stop();
					for (int i = 0, count = adapter.getCount(); i< count; i++) {
						adapter.getItem(i).put("isPlaying", "no");
					}
					adapter.notifyDataSetChanged();
				}
				break;
			}
			case TelephonyManager.CALL_STATE_RINGING: {
				DocLog.d(TAG, "CALL_STATE_RINGING" + incomingNumber);
				if(mediaPlayer != null && mediaPlayer.isPlaying()) {
					mediaPlayer.stop();
					for (int i = 0, count = adapter.getCount(); i< count; i++) {
						adapter.getItem(i).put("isPlaying", "no");
					}
					adapter.notifyDataSetChanged();
				}
				break;
			}
			default:
				break;
			}
		}

	}

	@Override
	protected void onStop() {
		super.onStop();
	}

	@Override
	protected void onDestroy() {
		super.onDestroy();
		for (int i = 0, len = desFileList.size();i < len; i++) {
			desFileList.get(i).delete();
		}
		am.setMode(AudioManager.MODE_NORMAL);
		if (mediaPlayer != null) {
			mediaPlayer.release();
			mediaPlayer = null;
		}
		if (mTeleListener != null)
			mTelephonyMgr.listen(mTeleListener, PhoneStateListener.LISTEN_NONE);
	}
}
