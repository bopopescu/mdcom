package com.doctorcom.physician.utils;

import java.io.DataOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.MalformedURLException;
import java.net.SocketTimeoutException;
import java.net.URL;
import java.net.URLEncoder;

import javax.net.ssl.HttpsURLConnection;

import android.annotation.TargetApi;
import android.content.Context;
import android.content.DialogInterface;
import android.os.AsyncTask;
import android.os.Build;
import android.os.Bundle;
import android.os.PowerManager;
import android.support.v4.app.DialogFragment;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;

import com.doctorcom.android.R;
import com.doctorcom.physician.AppValues;
import com.doctorcom.physician.net.NetConstantValues;
import com.doctorcom.physician.utils.AESEncryptDecrypt.AESEncryptDecryptException;

public class ProgressCancelDialog extends DialogFragment {

	private Button cancelButton;
	private ProgressBar pb;
	private TextView progressTextview, infoTextView;
	private URL url;
	private String fileName, secret, deviceId, messageId, attchmentId;
	private long fileSize;
	private Download downLoad;
	String TAG = "ProgressDialog";
	private String appPath;
	final static long connect_expire_time = 10000;
	final static int retry_time = 3;
	PowerManager powerManager = null;
	PowerManager.WakeLock wakeLock = null;
	public String type = "";
	public Object downloadInterface;

	public interface DownloadFinishListener {
		void onFinishDownload(String result);
	}

	public ProgressCancelDialog() {

	}

	@Override
	public void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
		int style = DialogFragment.STYLE_NORMAL, theme = 0;
		style = DialogFragment.STYLE_NO_TITLE;
		setStyle(style, theme);
		Bundle bundle = getArguments();
		messageId = bundle.getString("messageId");
		attchmentId = bundle.getString("attchmentId");
		fileName = bundle.getString("fileName");
		AppValues appValues = new AppValues(getActivity());
		if (fileName.equals(".pdf")) {
			try {
				url = new URL(
						appValues.getServerURL()
								+ NetConstantValues.APP_URL
								+ NetConstantValues.MESSAGE_REFER
										.getPDFPath(attchmentId));
			} catch (MalformedURLException e) {
				DocLog.e(TAG, "MalformedURLException", e);
			}
		} else {
			try {
				url = new URL(
						appValues.getServerURL()
								+ NetConstantValues.APP_URL
								+ NetConstantValues.MESSAGING_MESSAGE_ATTACHMENT
										.getPath(messageId, attchmentId));
			} catch (MalformedURLException e) {
				DocLog.e(TAG, "MalformedURLException", e);
			}
		}
		secret = appValues.getSecret();
		deviceId = appValues.getDcomDeviceId();
		fileSize = bundle.getLong("fileSize");
	}

	@Override
	public View onCreateView(LayoutInflater inflater, ViewGroup container,
			Bundle savedInstanceState) {
		View view = inflater.inflate(R.layout.progress, container);
		cancelButton = (Button) view.findViewById(R.id.btCancel);
		downLoad = new Download(getActivity());
		cancelButton.setOnClickListener(new View.OnClickListener() {

			@Override
			public void onClick(View v) {
				dismiss();
			}
		});
		pb = (ProgressBar) view.findViewById(R.id.progressBar);
		progressTextview = (TextView) view.findViewById(R.id.tvProgress);
		infoTextView = (TextView) view.findViewById(R.id.tvinfo);
		powerManager = (PowerManager) getActivity().getSystemService(
				Context.POWER_SERVICE);
		wakeLock = powerManager.newWakeLock(PowerManager.SCREEN_DIM_WAKE_LOCK
				| PowerManager.ON_AFTER_RELEASE, "My Lock");
		return view;
	}

	@Override
	public void onResume() {
		super.onResume();
		if (downLoad != null
				&& downLoad.getStatus() != AsyncTask.Status.RUNNING) {
			downLoad.execute();
			wakeLock.acquire();
		}
	}

	@Override
	public void onDismiss(DialogInterface dialog) {
		if (wakeLock != null) {
			wakeLock.release();
		}
		if (downLoad != null
				&& downLoad.getStatus() == AsyncTask.Status.RUNNING) {
			downLoad.cancel(true);
		}
		super.onDismiss(dialog);
	}
	
	public void setType(String type) {
		this.type = type;
	}

	public void setDownloadInterface(Object obj) {
		this.downloadInterface = obj;
	}

	class Download extends AsyncTask<Void, Integer, String> {

		private String encryptFilePath = "", originalFilePath = "";
		private Context mContext;

		public Download(Context context) {
			mContext = context;

		}

		@Override
		protected void onPreExecute() {
			appPath = FileUtil.getAppPath(mContext);
			if (appPath == null) {
				Toast.makeText(mContext, R.string.sdcard_unavailable,
						Toast.LENGTH_LONG).show();
				cancel(true);
			}
		}

		@Override
		protected String doInBackground(Void... params) {
			return connect(0);

		}

		@TargetApi(Build.VERSION_CODES.GINGERBREAD)
		public String connect(int loop) {
			// HTTP connection reuse which was buggy pre-froyo
			if (Build.VERSION.SDK_INT < Build.VERSION_CODES.FROYO) {
				System.setProperty("http.keepAlive", "false");
			}
			long startTime = System.currentTimeMillis();
			Utils utils = new Utils(mContext);
			if (!utils.checkNetworkAvailable()) {
				return getString(R.string.network_not_available);
			}
			String result = "";
			FileUtil.releaseAttachment(appPath);
			InputStream is = null;
			try {
				originalFilePath = appPath + "/des_tag_" + attchmentId
						+ fileName;
				encryptFilePath = appPath + "/" + attchmentId + fileName;
				HttpURLConnection conn;
				if (url.getProtocol().equals("https")) {
					conn = (HttpsURLConnection) url.openConnection();
				} else {
					conn = (HttpURLConnection) url.openConnection();
				}
				conn.setDoOutput(true);
				conn.setDoInput(true);
				conn.setUseCaches(false);
				conn.setReadTimeout(60000 /* milliseconds */);
				conn.setConnectTimeout(15000 /* milliseconds */);
				conn.setRequestProperty("DCOM_DEVICE_ID", deviceId);
				conn.setRequestMethod("POST");
				String content = NetConstantValues.MESSAGING_MESSAGE_BODY.PARAM_SECRET
						+ "=" + URLEncoder.encode(secret);
				DocLog.d(TAG, url.toString());
				DocLog.d(TAG, "DEVICE_ID >> " + deviceId);
				DocLog.d(TAG, "SECRET >> " + secret);
				DataOutputStream out = new DataOutputStream(
						conn.getOutputStream());
				out.writeBytes(content);
				out.flush();
				out.close();
				if (isCancelled()) {
					return null;
				}
				int response = conn.getResponseCode();
				DocLog.d(TAG, "status: " + response);
				if (response != HttpsURLConnection.HTTP_OK) {
					clear();
					if (response <= 0) {
						long currentTime = System.currentTimeMillis();
						if ((currentTime - startTime) < connect_expire_time) {
							loop++;
							if (loop < retry_time) {
								DocLog.i(TAG, "Retry: (" + loop + ") times.");
								return connect(loop);
							}
						}
						result = mContext.getString(R.string.get_data_error);
					} else if (response < 400) {
						InputStream inputStream = conn.getInputStream();
						result = Utils.stream2String(inputStream);
						inputStream.close();
					} else {
						InputStream inputStream = conn.getErrorStream();
						result = Utils.stream2String(inputStream);
						inputStream.close();
					}
					return result;
				}
				is = conn.getInputStream();
				int i = 0;
				String mime = null;
				while (true) {
					mime = conn.getHeaderField(i);
					if (mime == null)
						break;
					DocLog.i(TAG, "key:" + conn.getHeaderFieldKey(i)
							+ " value:" + mime);
					i++;
				}
				if (is == null)
					return "";
				if (fileSize == -1) {
					if ((fileSize = conn.getContentLength()) == -1) {
						DocLog.e(TAG, "file size unkonw");
						return "";
					}
				}
				File appFile = new File(appPath);
				if (Build.VERSION.SDK_INT > Build.VERSION_CODES.GINGERBREAD) {
					if (appFile.getFreeSpace() < fileSize * 1.2) {
						return "{\"errno\": \""
								+ getString(R.string.insufficient_disk_space)
								+ "\", \"descr\": \""
								+ getString(R.string.insufficient_disk_space)
								+ "\"}";
					}
				}
				byte buffer[] = new byte[1024 * 4];
				int len = 0;
				long hasRead = 0;
				int index = 0;

				FileOutputStream fos = new FileOutputStream(originalFilePath);
				while ((len = is.read(buffer)) != -1) {
					if (isCancelled()) {
						return null;
					}
					hasRead += len;
					index = (int) ((hasRead * 100) / fileSize);
					// Loading
					publishProgress(index, 1);
					fos.write(buffer, 0, len);
				}
				fos.close();
				// Encrypt
				publishProgress(index, 2);
				AESEncryptDecrypt decrypt = new AESEncryptDecrypt(
						AppValues.aeskey, mContext.getCacheDir()
								.getAbsolutePath() + AppValues.secretKey);
				decrypt.encrypt(new File(originalFilePath), new File(
						encryptFilePath));
				if (isCancelled()) {
					return null;
				}
				// Done
				publishProgress(110, 3);
				result = "{\"data\": \"" + originalFilePath
						+ "\", \"descr\": \"load sucess.\"}";
			} catch (SocketTimeoutException e) {
				DocLog.e(TAG, "SocketTimeoutException", e);
				clear();
				result = mContext.getString(R.string.get_data_error_socket);

				long currentTime = System.currentTimeMillis();
				if ((currentTime - startTime) < connect_expire_time) {
					loop++;
					if (loop < retry_time) {
						DocLog.i(TAG, "Retry: (" + loop + ") times.");
						return connect(loop);
					}
				}
			} catch (AESEncryptDecryptException e) {
				File file = new File(encryptFilePath);
				if (file.exists())
					file.delete();
				result = "{\"data\": \"" + originalFilePath
						+ "\", \"descr\": \"load sucess.\"}";
			} catch (Exception e) {
				clear();
				DocLog.e(TAG, "Exception", e);
				return "";
			} finally {
				if (is != null) {
					try {
						is.close();
					} catch (IOException e) {
						DocLog.e(TAG, "IOException", e);
					}
				}
			}
			return result;
		}

		@Override
		protected void onProgressUpdate(Integer... values) {
			if (isCancelled())
				return;
			progressTextview.setText(values[0] * 100 / 110 + "%");
			pb.setProgress(values[0]);
			switch (values[1]) {
			case 1: {
				infoTextView.setText(R.string.loading);
				break;
			}
			case 2: {
				infoTextView.setText(R.string.encrypt);
				break;
			}
			case 3: {
				infoTextView.setText(R.string.done);
				break;
			}
			}
		}

		@Override
		protected void onCancelled() {
			clear();
			super.onCancelled();
		}

		protected void clear() {
			File f = new File(originalFilePath);
			if (f.exists())
				f.delete();
			File file = new File(encryptFilePath);
			if (file.exists())
				file.delete();
		}

		@Override
		protected void onPostExecute(String result) {
			DownloadFinishListener activity;
			if (null != type && !"".equals(type))
				activity = (DownloadFinishListener) downloadInterface;
			else
				activity = (DownloadFinishListener) getActivity();
			if (result == null) {
				dismiss();
			} else {
				if (result.equals("")) {
					infoTextView.setText(R.string.download_file_fail_warning);
					clear();
					// dismiss() -- android 4.0.3
					// java.lang.IllegalStateException: Can not perform this
					// action after onSaveInstanceState
					activity.onFinishDownload("");
				} else {
					dismiss();
					activity.onFinishDownload(result);
				}
			}
		}

	}

}
