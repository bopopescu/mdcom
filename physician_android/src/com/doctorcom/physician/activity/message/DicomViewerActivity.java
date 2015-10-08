package com.doctorcom.physician.activity.message;

import java.io.DataOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.lang.ref.WeakReference;
import java.net.HttpURLConnection;
import java.net.MalformedURLException;
import java.net.URL;
import java.net.URLEncoder;
import java.util.HashMap;

import javax.net.ssl.HttpsURLConnection;

import org.json.JSONException;
import org.json.JSONObject;

import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.graphics.Bitmap;
import android.graphics.Bitmap.Config;
import android.graphics.BitmapFactory;
import android.graphics.Canvas;
import android.graphics.ColorMatrix;
import android.graphics.ColorMatrixColorFilter;
import android.graphics.Paint;
import android.graphics.drawable.BitmapDrawable;
import android.os.AsyncTask;
import android.os.Bundle;
import android.os.Handler;
import android.os.Message;
import android.view.View;
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.PopupWindow;
import android.widget.ProgressBar;
import android.widget.ScrollView;
import android.widget.SeekBar;
import android.widget.TableRow;
import android.widget.TextView;
import android.widget.Toast;

import com.doctorcom.android.R;
import com.doctorcom.physician.AppValues;
import com.doctorcom.physician.net.NetConstantValues;
import com.doctorcom.physician.net.http.NetConncet;
import com.doctorcom.physician.utils.AESEncryptDecrypt;
import com.doctorcom.physician.utils.DocLog;
import com.doctorcom.physician.utils.FileUtil;
import com.doctorcom.physician.utils.cache.Cache;


public class DicomViewerActivity extends Activity implements Cache.CacheFinishListener {
	private String TAG = "DicomViewerActivity";
	private AppValues appValues;
	private ImageView dicomImageView;
	private TextView framesTextView;
	private TextView windowLevelTextView;
	private TextView windowWidthTextView;
	private TextView infoTextView;
	private TextView pictureLoadingTextView;
	private SeekBar framesSeekBar;
	private SeekBar windowLevelSeekBar;
	private SeekBar windowWidthSeekBar;
	private ProgressBar loadingProgressBar;
	private LinearLayout contentLinearLayout;
	private FrameLayout pictureloadingFrameLayout, loadingFrameLayout;
	private Button playButton;
	private TableRow framesTableRow;
	private CircleProgress loadingCircleProgress;
	private String messageId, attachmentId, fileName;
	private String appPath;
	private int count, windowLevelMax, windowWidthMax, windowLevelOriginal, windowWidthOriginal;
	private int imgHeight, imgWidth;
	private float brightness = 1, contrast = 1;
	private boolean isPlaying, dragPlaying;
	private Bitmap srcBitmap;
	private PopupWindow popupWindow;
	
	@Override
	protected void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
		setContentView(R.layout.activity_dicom_viewer);
		appValues = new AppValues(this);
		appPath = FileUtil.getAppPath(this);
		if (appPath == null) {
			Toast.makeText(this, R.string.sdcard_unavailable, Toast.LENGTH_LONG).show();
			finish();
		}
		dicomImageView = (ImageView) findViewById(R.id.imageview_dicom);
		framesTextView = (TextView) findViewById(R.id.textview_frames);
		windowLevelTextView = (TextView) findViewById(R.id.textview_window_level);
		windowWidthTextView = (TextView) findViewById(R.id.textview_window_width);
		infoTextView = (TextView) findViewById(R.id.tvInfo);
		framesSeekBar = (SeekBar) findViewById(R.id.seekbar_frames);
		windowLevelSeekBar = (SeekBar) findViewById(R.id.seekbar_window_level);
		windowWidthSeekBar = (SeekBar) findViewById(R.id.seekbar_window_width);
		contentLinearLayout = (LinearLayout) findViewById(R.id.llContent);
		pictureloadingFrameLayout = (FrameLayout) findViewById(R.id.framelayout_loading);
		loadingFrameLayout = (FrameLayout) findViewById(R.id.frameLoading);
		loadingProgressBar = (ProgressBar) findViewById(R.id.pb);
		loadingCircleProgress = (CircleProgress) findViewById(R.id.circleProgress_loading);
		playButton = (Button) findViewById(R.id.button_dicom_play_pause);
		framesTableRow = (TableRow) findViewById(R.id.tablerow_frames);
		pictureLoadingTextView = (TextView) findViewById(R.id.textview_load);
		
		windowLevelMax = windowLevelSeekBar.getMax();
		windowWidthMax = windowWidthSeekBar.getMax();
		windowLevelOriginal = windowLevelSeekBar.getProgress();
		windowWidthOriginal = windowWidthSeekBar.getProgress();
		contentLinearLayout.setVisibility(View.GONE);
		loadingFrameLayout.setVisibility(View.VISIBLE);
		infoTextView.setVisibility(View.GONE);
		Intent intent = getIntent();
		messageId = intent.getStringExtra("messageId");
		attachmentId = intent.getStringExtra("attachmentId");
		fileName = intent.getStringExtra("fileName");
		isPlaying = false;
		dragPlaying = false;
		framesSeekBar.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener(){

			@Override
			public void onProgressChanged(SeekBar seekBar, int progress,
					boolean fromUser) {
				if (fromUser) {
					if (dragPlaying) {
						dragPlaying = false;
					}
					setFramText(framesTextView, progress + 1, count);
					setFramImage(dicomImageView, attachmentId, fileName, progress);
				}
			}

			@Override
			public void onStartTrackingTouch(SeekBar seekBar) {
				
			}

			@Override
			public void onStopTrackingTouch(SeekBar seekBar) {
				
			}
			
		});
		windowLevelSeekBar.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
			
			@Override
			public void onStopTrackingTouch(SeekBar seekBar) {

			}

			@Override
			public void onStartTrackingTouch(SeekBar seekBar) {

			}
			
			@Override
			public void onProgressChanged(SeekBar seekBar, int progress,
					boolean fromUser) {
				if (srcBitmap != null) {
					brightness = progress - windowLevelOriginal;
					setChangedPicture();
					setwindowLevelText(windowLevelTextView, progress, windowLevelMax);
				}
			}
		});
		windowWidthSeekBar.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {

			@Override
			public void onStartTrackingTouch(SeekBar seekBar) {

			}

			@Override
			public void onStopTrackingTouch(SeekBar seekBar) {
				
			}
			
			@Override
			public void onProgressChanged(SeekBar seekBar, int progress,
					boolean fromUser) {
				if (srcBitmap != null) {
					contrast = (float) ((progress + 51) / 307.0);
					setChangedPicture();
					setwindowWidthText(windowWidthTextView, progress, windowWidthMax);
				}
			}

		});
		checkDicom(0);
	}

	private void setChangedPicture() {
		Bitmap bmp = Bitmap.createBitmap(imgWidth, imgHeight, Config.ARGB_8888);
		ColorMatrix cMatrix = new ColorMatrix();
		cMatrix.set(new float[] {
				contrast, 0, 0, 0, brightness,
				0, contrast, 0, 0, brightness,
				0, 0, contrast, 0, brightness,
				0, 0, 0, 1, 0 });

		Paint paint = new Paint();
		paint.setColorFilter(new ColorMatrixColorFilter(cMatrix));

		Canvas canvas = new Canvas(bmp);
		canvas.drawBitmap(srcBitmap, 0, 0, paint);

		dicomImageView.setImageBitmap(bmp);
		
	}
	
	public void onTitleClick(final View view) {
		switch (view.getId()) {
		case R.id.btBack:
			finish();
			break;
		case R.id.btSelect:
			if (popupWindow != null) {
				popupWindow.showAsDropDown(view, 0, -10);
				view.setBackgroundResource(R.drawable.button_dropup);
				popupWindow.setOnDismissListener(new PopupWindow.OnDismissListener() {

					@Override
					public void onDismiss() {
						view.setBackgroundResource(R.drawable.button_dropdown);
					}
					
				});
			}
			break;
		}
	}

	static class MyHandler extends Handler {

		WeakReference<DicomViewerActivity> mActivity;
		public MyHandler(DicomViewerActivity activity) {
			mActivity = new WeakReference<DicomViewerActivity>(activity);
		}

		@Override
		public void handleMessage(Message msg) {
			DicomViewerActivity activity = mActivity.get();
			int index = (Integer) msg.obj;
			if (index < activity.count) {
				if (activity.isPlaying) {
					if (activity.dragPlaying) {
						activity.framesSeekBar.setProgress(index);
						activity.setFramImage(activity.dicomImageView, activity.attachmentId, activity.fileName, index);
						index ++;
						activity.setFramText(activity.framesTextView, index, activity.count);
						Message message = Message.obtain();
						message.obj = index;
						sendMessageDelayed(message, 500);
					} else {
						index = activity.framesSeekBar.getProgress();
						Message message = Message.obtain();
						message.obj = index;
						activity.playButton.setBackgroundResource(R.drawable.button_dicom_pause_selector);
						activity.dragPlaying = true;
						sendMessageDelayed(message, 200);
					}
				}
			} else {
				activity.playButton.setBackgroundResource(R.drawable.button_dicom_play_selector);
				activity.isPlaying = false;
			}
		}
		
	}
//	Handler handler = new Handler(){
//
//		@Override
//		public void handleMessage(Message msg) {
//			int index = (Integer) msg.obj;
//			if (index < count) {
//				if (isPlaying) {
//					if (dragPlaying) {
//						framesSeekBar.setProgress(index);
//						setFramImage(dicomImageView, attachmentId, fileName, index);
//						index ++;
//						setFramText(framesTextView, index, count);
//						Message message = Message.obtain();
//						message.obj = index;
//						handler.sendMessageDelayed(message, 500);
//					} else {
//						index = framesSeekBar.getProgress();
//						Message message = Message.obtain();
//						message.obj = index;
//						playButton.setBackgroundResource(R.drawable.button_dicom_pause_selector);
//						dragPlaying = true;
//						handler.sendMessageDelayed(message, 200);
//					}
//				}
//			} else {
//				playButton.setBackgroundResource(R.drawable.button_dicom_play_selector);
//				isPlaying = false;
//			}
//		}
//		
//	};
	public void onPlayFrames(View view) {
		if (isPlaying) {
			playButton.setBackgroundResource(R.drawable.button_dicom_play_selector);
			isPlaying = false;
			dragPlaying = false;
		} else {
			int index = framesSeekBar.getProgress();
			if (index == count - 1) {
				index = 0;
			}
			Message message = Message.obtain();
			message.obj = index;
			playButton.setBackgroundResource(R.drawable.button_dicom_pause_selector);
			isPlaying = true;
			dragPlaying = true;
			new MyHandler(this).sendMessage(message);
		}
	}
	
	protected void checkDicom(final int loop) {
		HashMap<String, String> params = new HashMap<String, String>();
		params.put(NetConstantValues.DICOM_SUPPORT.PARAM_SECRET, appValues.getSecret());
		params.put(NetConstantValues.DICOM_SUPPORT.PARAM_SEND_IF_NOT_EXIST, String.valueOf(true));
		NetConncet netConncet = new NetConncet(this, NetConstantValues.DICOM_SUPPORT.getCheckDicomIofoPath(messageId, attachmentId), params) {

			@Override
			protected void onPostExecute(String result) {
				super.onPostExecute(result);
				try {
					JSONObject jsonObj = new JSONObject(result);
					if (!jsonObj.isNull("errno")) {
						if (loop < 3) {
							Thread.sleep(500);
							checkDicom(loop + 1);
						} else {
							showError(jsonObj.getString("descr"));
						}
					} else {
						boolean exist = jsonObj.getJSONObject("data").getBoolean("exist");
						if (exist) {
							getDicomInfo();
						} else {
							// show text: "Dicom viewer is not ready, please try it later."
							if (loop < 3) {
								Thread.sleep(500);
								checkDicom(loop + 1);
							} else {
								showError(getString(R.string.dicom_viewer_not_ready));
							}
						}
					}
				} catch (JSONException e) {
					DocLog.e(TAG, "JSONException", e);
					showError(getString(R.string.error_occur));
				} catch (InterruptedException e) {
					DocLog.e(TAG, "InterruptedException", e);
				}
			}
		};
		netConncet.execute();
	}
	
	protected void getDicomInfo() {
		HashMap<String, String> params = new HashMap<String, String>();
		params.put(NetConstantValues.DICOM_SUPPORT.PARAM_SECRET, appValues.getSecret());
		Cache cache = new Cache(this, NetConncet.HTTP_POST);
		cache.setCacheType(Cache.CACHE_OTHER);
		cache.useCache(this, NetConstantValues.DICOM_SUPPORT.getDicomIofoPath(messageId, attachmentId), "/Messaging/Message/*/DicomInfo/*/", params);

	}
	@Override
	public void onCacheFinish(String result, boolean isCache) {
		try {
			JSONObject jsonObj = new JSONObject(result);
			if (jsonObj.isNull("errno")) {
				JSONObject jData = jsonObj.getJSONObject("data");
				count = jData.getInt("jpg_count");
				if (count == 1) {
					framesTableRow.setVisibility(View.GONE);
					loadingCircleProgress.setVisibility(View.GONE);
				} else {
					framesSeekBar.setMax(count - 1);
					loadingCircleProgress.setmMaxProgress(count -1);
				}
				getPopupWindow(result);
				download(count);
			} else {
				showError(jsonObj.getString("descr"));
			}
		} catch (JSONException e) {
			DocLog.e(TAG, "JSONException", e);
			showError(getString(R.string.error_occur));
		}
		
	}

	protected void download(final int count) {
		 AsyncTask<Void, Integer, Integer> asyncTask = new AsyncTask<Void, Integer, Integer>() {

			@Override
			protected void onPreExecute() {
				initLevelWidth();
			}

			@Override
			protected Integer doInBackground(Void... params) {
				Context context = DicomViewerActivity.this;
				AppValues appValues = new AppValues(context);
				String secret = appValues.getSecret();
				String deviceId = appValues.getDcomDeviceId();

				for (int i = 0; i < count; i++) {
					
					URL url = null;
					try {
						url = new URL(appValues.getServerURL() + NetConstantValues.APP_URL + NetConstantValues.DICOM_SUPPORT.getDicom2JPGPath(messageId, attachmentId, i));
					} catch (MalformedURLException e1) {
						DocLog.e(TAG, "MalformedURLException", e1);
						throw new RuntimeException("MalformedURLException");
					}
					String parent = appPath + "/dicom";
					File fi = new File(parent);
					if (!fi.exists()) {
						fi.mkdirs();
					}
					String originalFilePath = parent + "/des_tag_" + attachmentId + fileName + i + ".jpg";
					String encryptFilePath = parent + "/" + attachmentId + fileName + i + ".jpg";
					File originalFile = new File(originalFilePath), encryptFile = new File(encryptFilePath);
					if (hasOriginalFile(attachmentId, fileName, i)) {
						publishProgress(i, count);
						DocLog.d(TAG, "find originalFile: " + originalFilePath);
						continue;
					}
					AESEncryptDecrypt decrypt = new AESEncryptDecrypt(AppValues.aeskey, context.getCacheDir().getAbsolutePath() + AppValues.secretKey);
					if (hasCryptographicFile(attachmentId, fileName, i)) {
						try {
							decrypt.decrypt(encryptFile, originalFile);
							publishProgress(i, count);
							DocLog.d(TAG, "find encryptFile: " + encryptFilePath);
							continue;
						} catch (Exception e) {
							DocLog.e(TAG, "Exception", e);
						}
					}
					HttpURLConnection conn;
					try {
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
						String content = NetConstantValues.MESSAGING_MESSAGE_BODY.PARAM_SECRET + "=" + URLEncoder.encode(secret);
						DataOutputStream out = new DataOutputStream(conn.getOutputStream());
						out.writeBytes(content);
						out.flush();
						out.close();
						
						int response = conn.getResponseCode();
						if (response != HttpsURLConnection.HTTP_OK) {
						}
						InputStream is = conn.getInputStream();
						byte buffer[] = new byte[1024 * 4];
						int len = 0;
						
						FileOutputStream fos = new FileOutputStream(originalFilePath);
						while ((len = is.read(buffer)) != -1) {
							fos.write(buffer, 0, len);
						}
						publishProgress(i, count);
						fos.close();
						DocLog.d(TAG, "down load " + originalFilePath);
						//Encrypt
						decrypt.encrypt(new File(originalFilePath), new File(encryptFilePath));
						DocLog.d(TAG, "encrypt finish " + encryptFilePath);
					} catch (Exception e) {
						DocLog.e(TAG, "Exception", e);
						publishProgress(i, count);
					}
				}
				return count;
			}

			@Override
			protected void onProgressUpdate(Integer... values) {
				super.onProgressUpdate(values);
				if (values[0] == 0) {
					if (values[1] == 1) {
						pictureloadingFrameLayout.setVisibility(View.GONE);
					}
					showViewer();
				}
				setFramImage(dicomImageView, attachmentId, fileName, values[0]);
				setFramText(framesTextView, values[0] + 1, count);
				framesSeekBar.setProgress(values[0]);
				loadingCircleProgress.setMainProgress(values[0]);
				if (values[1] != 1) {
					pictureLoadingTextView.setText(String.format(DicomViewerActivity.this.getString(R.string.loading_picture), values[0] + 1));
				}
			}

			@Override
			protected void onPostExecute(Integer result) {
				super.onPostExecute(result);
				setFramImage(dicomImageView, attachmentId, fileName, 0);
				setFramText(framesTextView, 1, count);
				framesSeekBar.setProgress(0);
				pictureloadingFrameLayout.setVisibility(View.GONE);
			}

		};
		asyncTask.execute();
	}
	
	protected void showViewer() {
		contentLinearLayout.setVisibility(View.VISIBLE);
		loadingFrameLayout.setVisibility(View.GONE);

	}
	
	protected void showError(String errorMessage) {
		contentLinearLayout.setVisibility(View.GONE);
		loadingFrameLayout.setVisibility(View.VISIBLE);
		infoTextView.setVisibility(View.VISIBLE);
		loadingProgressBar.setVisibility(View.GONE);
		infoTextView.setText(errorMessage);

	}
	
	protected void setFramImage(ImageView imageView, String attachmentId, String fileName, int index) {
		File file = new File(appPath + "/dicom" + "/des_tag_" + attachmentId + fileName + index + ".jpg");
		if (file.exists()) {
			srcBitmap = decodeBitmapFromFile(file.getAbsolutePath(), 480, 800);
			if (srcBitmap != null) {
				imgHeight = srcBitmap.getHeight();
				imgWidth = srcBitmap.getWidth();
				setChangedPicture();
			}
		} else {
			srcBitmap = null;
			imageView.setImageDrawable(null);
		}
	}
	
	protected void setFramText(TextView textView, int index, int count) {
		if (textView != null) {
			if (index <= count) {
				textView.setText(index + " / " + count);
			}
		}
	}
	
	protected void setwindowLevelText(TextView textView, int index, int count) {
		if (textView != null) {
			if (index <= count) {
				textView.setText("L:" + (index - 25) + " / " + (count - 25));
			}
		}		
	}
	
	protected void setwindowWidthText(TextView textView, int index, int count) {
		if (textView != null) {
			if (index <= count) {
				textView.setText("W:" + (index + 1)+ " / " + (count + 1));
			}
		}		
	}
	
	protected void initLevelWidth() {
		setwindowLevelText(windowLevelTextView, windowLevelOriginal, windowLevelMax);
		setwindowWidthText(windowWidthTextView, windowWidthOriginal, windowWidthMax);
		windowLevelSeekBar.setProgress(windowLevelOriginal);
		windowWidthSeekBar.setProgress(windowWidthOriginal);
	}

	protected boolean hasOriginalFile(String attachmentId, String fileName, int i) {
		File file = new File(appPath + "/dicom" + "/des_tag_" + attachmentId + fileName + i + ".jpg");
		if (file.exists()) {
			return true;
		}
		return false;
	}
	
	protected boolean hasCryptographicFile(String attachmentId, String fileName, int i) {
		File file = new File(appPath + "/dicom" + "/" + attachmentId + fileName + i + ".jpg");
		if (file.exists()) {
			return true;
		}
		return false;
	}

	private void getPopupWindow(String result) {
		if (null != popupWindow) {
			popupWindow.dismiss();
			return;
		} else {
			initPopuptWindow(result);
		}
	}
	
	private void initPopuptWindow(String result) {
		try {
			JSONObject jsonObj = new JSONObject(result);
			JSONObject jData = jsonObj.getJSONObject("data");
			JSONObject dcm = jData.getJSONObject("dcm");
			StringBuilder stringBuilder = new StringBuilder();
			String studyId = dcm.getString("study_id");
			if (!"".equals(studyId)) {
				stringBuilder.append(String.format(getString(R.string.dicom_study_id), studyId) + "\r\n");
			}
			String studyDescription = dcm.getString("study_description");
			if (!"".equals(studyDescription)) {
				stringBuilder.append(String.format(getString(R.string.dicom_study_description), studyDescription) + "\r\n");
			}
			String seriesDescription = dcm.getString("series_description");
			if (!"".equals(seriesDescription)) {
				stringBuilder.append(String.format(getString(R.string.dicom_series_description), seriesDescription) + "\r\n");
			}
			String acquisitionDate = dcm.getString("acquisition_date");
			if (!"".equals(acquisitionDate)) {
				stringBuilder.append(String.format(getString(R.string.dicom_acquisition_date), acquisitionDate) + "\r\n");
			}
			String acquisitionTime = dcm.getString("acquisition_time");
			if (!"".equals(acquisitionTime)) {
				stringBuilder.append(String.format(getString(R.string.dicom_acquisition_time), acquisitionTime) + "\r\n");
			}
			String sliceLocation = dcm.getString("slice_location");
			if (!"".equals(sliceLocation)) {
				stringBuilder.append(String.format(getString(R.string.dicom_slice_location), sliceLocation) + "\r\n");
			}
			JSONObject patient = jData.getJSONObject("patient");
			String id = patient.getString("id");
			if (!"".equals(id)) {
				stringBuilder.append(String.format(getString(R.string.dicom_patientId), id) + "\r\n");
			}
			String name = patient.getString("name");
			if (!"".equals(name)) {
				stringBuilder.append(String.format(getString(R.string.dicom_name), name) + "\r\n");
			}
			String sex = patient.getString("sex");
			if (!"".equals(sex)) {
				stringBuilder.append(String.format(getString(R.string.dicom_sex), sex) + "\r\n");
			}
			String birthday = patient.getString("birthday");
			if (!"".equals(birthday)) {
				stringBuilder.append(String.format(getString(R.string.dicom_birthday), birthday) + "\r\n");
			}
			String weight = patient.getString("weight");
			if (!"".equals(weight)) {
				stringBuilder.append(String.format(getString(R.string.dicom_weight), weight) + "\r\n");
			}
			View popupWindowView = getLayoutInflater().inflate(R.layout.dropdown_dicom_info, null, false);
			ScrollView contenScrollView = (ScrollView) popupWindowView.findViewById(R.id.scrollview_content);
			TextView view = new TextView(this);
			view.setText(stringBuilder);
			view.setTextColor(getResources().getColor(R.color.white));
			contenScrollView.addView(view);
			popupWindow = new PopupWindow(popupWindowView, 240, 240, true);
			popupWindow.setBackgroundDrawable(new BitmapDrawable());
		} catch (JSONException e) {
			DocLog.e(TAG, "JSONException", e);
			showError(getString(R.string.error_occur));
		}

	}
	
	public static Bitmap decodeBitmapFromFile(String pathName, int reqWidth, int reqHeight) {

		// First decode with inJustDecodeBounds=true to check dimensions
		final BitmapFactory.Options options = new BitmapFactory.Options();
		options.inJustDecodeBounds = true;
		BitmapFactory.decodeFile(pathName, options);

		// Calculate inSampleSize
		options.inSampleSize = calculateInSize(options, reqWidth, reqHeight);

		// Decode bitmap with inSampleSize set
		options.inJustDecodeBounds = false;
		return BitmapFactory.decodeFile(pathName, options);
	}

	public static int calculateInSize(BitmapFactory.Options options, int reqWidth, int reqHeight) {
		// Raw height and width of image
		final int height = options.outHeight;
		final int width = options.outWidth;
		int inSampleSize = 1;

		if (height > reqHeight || width > reqWidth) {

			// Calculate ratios of height and width to requested height and
			// width
			final int heightRatio = Math.round((float) height
					/ (float) reqHeight);
			final int widthRatio = Math.round((float) width / (float) reqWidth);

			// Choose the smallest ratio as inSampleSize value, this will
			// guarantee
			// a final image with both dimensions larger than or equal to the
			// requested height and width.
			inSampleSize = heightRatio < widthRatio ? heightRatio : widthRatio;
		}

		return inSampleSize;
	}
	
	@Override
	protected void onDestroy() {
		for (int i = 0; i < count; i++) {
			File file = new File(appPath + "/dicom" + "/des_tag_" + attachmentId + fileName + i + ".jpg");
			if (file.exists()) {
				file.delete();
			}
		}
		super.onDestroy();
	}

}
