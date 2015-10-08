package com.doctorcom.physician.utils.camera;

import java.io.File;
import java.io.FileOutputStream;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

import android.annotation.TargetApi;
import android.app.Activity;
import android.content.Intent;
import android.hardware.Camera;
import android.hardware.Camera.PictureCallback;
import android.hardware.Camera.ShutterCallback;
import android.media.AudioManager;
import android.media.MediaPlayer;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.os.Handler;
import android.view.View;
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.Toast;

import com.doctorcom.android.R;
import com.doctorcom.physician.utils.DocLog;
import com.doctorcom.physician.utils.FileUtil;

public class CameraActivity extends Activity {
	
	protected static final String TAG = "CameraActivity";
	private Camera mCamera;
	private CameraPreview mPreview;
	private String photo;
	private Button captureButton, closeButton, acceptButton, deleteButton;
	private byte[] byteData;
	private boolean busy = false;
	private LinearLayout llLoading, llContent;
	private int cameraId;

	@Override
	public void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
		setContentView(R.layout.camera_preview);
		llLoading = (LinearLayout) findViewById(R.id.llLoading);
		llContent = (LinearLayout) findViewById(R.id.llContent);
		llLoading.setVisibility(View.VISIBLE);
		llContent.setVisibility(View.GONE);
		cameraId = getIntent().getIntExtra("cameraId", -1);
		// Add a listener to the Capture button
		captureButton = (Button) findViewById(R.id.button_capture);
		captureButton.setOnClickListener(new View.OnClickListener() {
			@Override
			public void onClick(View v) {
				if (!FileUtil.isSdcardAvailable()) {
					Toast.makeText(CameraActivity.this, R.string.sdcard_unavailable, Toast.LENGTH_LONG).show();
					return;
				}
				if (busy) return;
				busy = true;
				// get an image from the camera
				mCamera.takePicture(new ShutterCallback() {

					@Override
					public void onShutter() {
						Uri sound = Uri.parse("/system/media/audio/ui/camera_click.ogg");
						MediaPlayer mediaPlayer = new MediaPlayer();
						mediaPlayer.setAudioStreamType(AudioManager.STREAM_MUSIC);
						try {
							mediaPlayer.setDataSource(getApplicationContext(), sound);
							mediaPlayer.prepare();
							mediaPlayer.start();
						} catch (Exception e) {
							DocLog.e(TAG, "Exception", e);
						}
						}}, null, mPicture);
			}
		});
		closeButton = (Button)findViewById(R.id.btClose);
		closeButton.setOnClickListener(new View.OnClickListener() {

			@Override
			public void onClick(View v) {
				busy = false;
				Intent intent = new Intent();
				intent.putExtra("image", photo);
				setResult(RESULT_OK, intent);
				finish();
			}
		});
		
		acceptButton = (Button)findViewById(R.id.btAccept);
		acceptButton.setOnClickListener(new View.OnClickListener() {
			
			@Override
			public void onClick(View v) {
				if (FileUtil.isSdcardAvailable()) {
		   			File pictureFile = getOutputMediaFile(MEDIA_TYPE_IMAGE);
					if (pictureFile == null) {
						return;
					}

					try {
						FileOutputStream fos = new FileOutputStream(pictureFile);
						fos.write(byteData);
						fos.close();
						photo = pictureFile.getAbsolutePath();
						closeButton.performClick();
					} catch (Exception e) {
						Toast.makeText(CameraActivity.this, R.string.write_sdcard_fail, Toast.LENGTH_LONG).show();
						DocLog.d(TAG, "Exception", e);
					}
//					mCamera.startPreview();
//					acceptButton.setVisibility(View.GONE);
//					deleteButton.setVisibility(View.GONE);
//					captureButton.setVisibility(View.VISIBLE);
//					closeButton.setVisibility(View.VISIBLE);
				} else {
					Toast.makeText(CameraActivity.this, R.string.sdcard_unavailable, Toast.LENGTH_LONG).show();
				}

			}
		});
		deleteButton = (Button)findViewById(R.id.btDelete);
		deleteButton.setOnClickListener(new View.OnClickListener() {
			
			@Override
			public void onClick(View v) {
				busy = false;
                mCamera.startPreview();
    			acceptButton.setVisibility(View.GONE);
    			deleteButton.setVisibility(View.GONE);
				captureButton.setVisibility(View.VISIBLE);
				closeButton.setVisibility(View.VISIBLE);
			}
		});
	}
	
	@Override
	protected void onResume() {
		final Handler handler = new Handler();
		final Runnable runnable = new Runnable() {
			
			@Override
			public void run() {
				// Create our Preview view and set it as the content of our activity.
				mPreview = new CameraPreview(CameraActivity.this, mCamera, cameraId);
				FrameLayout preview = (FrameLayout) findViewById(R.id.camera_preview);
				preview.addView(mPreview);
				llLoading.setVisibility(View.GONE);
				llContent.setVisibility(View.VISIBLE);
				
			}
		};

		new Thread() {

			@Override
			public void run() {
				// Create an instance of Camera
				mCamera = getCameraInstance(cameraId);
				handler.post(runnable);
			}
			
		}.start();
		super.onResume();
	}

	@Override
	protected void onPause() {
		super.onPause();
		releaseCamera(); // release the camera immediately on pause event
	}

	@Override
	public void onBackPressed() {
		closeButton.performClick();
	}

	private void releaseCamera() {
		byteData = null;
		if (mCamera != null) {
			mCamera.setPreviewCallback(null) ;
			mCamera.stopPreview();
			mCamera.release(); // release the camera for other applications
			mCamera = null;
			finish();
		}
	}

	private PictureCallback mPicture = new PictureCallback() {

		@Override
		public void onPictureTaken(byte[] data, Camera camera) {
			byteData = data;
			captureButton.setVisibility(View.GONE);
			closeButton.setVisibility(View.GONE);
			acceptButton.setVisibility(View.VISIBLE);
			deleteButton.setVisibility(View.VISIBLE);
		}
	};

	@TargetApi(Build.VERSION_CODES.GINGERBREAD)
	public static Camera getCameraInstance(int id) {
		Camera c = null;
		try {
			//attempt to get a Camera instance
			if (id > -1 && Build.VERSION.SDK_INT > Build.VERSION_CODES.FROYO) {
				c = Camera.open(id);
			} else {
				c = Camera.open();
			}
		} catch (Exception e) {
			// Camera is not available (in use or does not exist)
		}
		return c; // returns null if camera is unavailable
	}

	public static final int MEDIA_TYPE_IMAGE = 1;
	public static final int MEDIA_TYPE_VIDEO = 2;

	/** Create a File for saving an image or video */
	protected File getOutputMediaFile(int type) {
		File mediaStorageDir = getExternalFilesDir(Environment.DIRECTORY_PICTURES);
		// This location works best if you want the created images to be shared
		// between applications and persist after your app has been uninstalled.

		// Create the storage directory if it does not exist
		if (!mediaStorageDir.exists()) {
			if (!mediaStorageDir.mkdirs()) {
				DocLog.d(TAG, "failed to create directory");
				return null;
			}
		}

		// Create a media file name
		String timeStamp = new SimpleDateFormat("yyyyMMdd_HHmmss", Locale.US)
				.format(new Date());
		File mediaFile;
		if (type == MEDIA_TYPE_IMAGE) {
			mediaFile = new File(mediaStorageDir.getPath() + File.separator
					+ "IMG_" + timeStamp + ".jpg");
		} else if (type == MEDIA_TYPE_VIDEO) {
			mediaFile = new File(mediaStorageDir.getPath() + File.separator
					+ "VID_" + timeStamp + ".mp4");
		} else {
			return null;
		}

		return mediaFile;
	}

}
