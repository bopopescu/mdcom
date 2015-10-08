package com.doctorcom.physician.utils.camera;

import java.util.ArrayList;
import java.util.Collections;
import java.util.Iterator;
import java.util.List;

import com.doctorcom.physician.utils.DocLog;

import android.annotation.TargetApi;
import android.app.Activity;
import android.content.Context;
import android.content.res.Configuration;
import android.graphics.PixelFormat;
import android.hardware.Camera;
import android.os.Build;
import android.view.Surface;
import android.view.SurfaceHolder;
import android.view.SurfaceView;

public class CameraPreview extends SurfaceView implements SurfaceHolder.Callback {

	private SurfaceHolder mHolder;
	private Camera mCamera;
	private Context mContext;
	private String TAG = "CameraPreview";
	private int cameraId = 0;
	private boolean isFrontCamera = false;

	public CameraPreview(Context context, Camera camera, int cameraId) {
		super(context);
		mContext = context;
		mCamera = camera;
        // Install a SurfaceHolder.Callback so we get notified when the
        // underlying surface is created and destroyed.
        mHolder = getHolder();
        mHolder.addCallback(this);
        // deprecated setting, but required on Android versions prior to 3.0
        mHolder.setType(SurfaceHolder.SURFACE_TYPE_PUSH_BUFFERS);
        if (cameraId > 0) {
        	this.cameraId = cameraId;
        }
	}

	@Override
	public void surfaceChanged(SurfaceHolder holder, int format, int width,
			int height) {
		DocLog.d(TAG, "surfaceChanged");
        // If your preview can change or rotate, take care of those events here.
        // Make sure to stop the preview before resizing or reformatting it.
        if (mHolder.getSurface() == null){
          // preview surface does not exist
          return;
        }

        // stop preview before making changes
        try {
            mCamera.stopPreview();
            Camera.Parameters param = mCamera.getParameters();
            
			List<Camera.Size> sizeList = param.getSupportedPreviewSizes();
			List<Camera.Size> pictureSize = param.getSupportedPictureSizes();
			List<Integer> size = new ArrayList<Integer>();;
			for (int i = 0, length = pictureSize.size(); i < length; i++) {
				size.add(pictureSize.get(i).height * pictureSize.get(i).width);
			}
			int sum = Collections.max(size);
			int index = 0;
			for (int i = 0, length = pictureSize.size(); i < length; i++) {
				if (sum == pictureSize.get(i).height * pictureSize.get(i).width) {
					index = i;
					break;
				}
			}
			int bestWidth = 0;
			int bestHeight = 0;
			if (sizeList.size() > 1) {
				Iterator<Camera.Size> itor = sizeList.iterator();
				while (itor.hasNext()) {
					Camera.Size cur = itor.next();
					if (cur.width > bestWidth && cur.height > bestHeight
							&& cur.width < width && cur.height < height) {
						bestWidth = cur.width;
						bestHeight = cur.height;
					}
				}
			}
			int orientation = 0;
			if (android.os.Build.VERSION.SDK_INT < 9) {
				if (getResources().getConfiguration().orientation == Configuration.ORIENTATION_LANDSCAPE) {
					orientation = 0;
				} else {
					orientation = 90;
				}
			} else {
	            orientation = getCameraDisplayOrientation((Activity) mContext, cameraId, mCamera);
			}
			mCamera.setDisplayOrientation(orientation);
			if (isFrontCamera) {
				param.setRotation(orientation + 180);
			} else {
				param.setRotation(orientation);
			}
            if (orientation == 0) {
            	param.setPictureSize(pictureSize.get(index).height, pictureSize.get(index).width);
				if (bestWidth != 0 && bestHeight != 0) {
					param.setPreviewSize(bestHeight, bestWidth);
				}
            } else {
            	param.setPictureSize(pictureSize.get(index).width, pictureSize.get(index).height);
				if (bestWidth != 0 && bestHeight != 0) {
					param.setPreviewSize(bestWidth, bestHeight);
				}
            }
            param.setPictureFormat(PixelFormat.JPEG);
			mCamera.setParameters(param);
	        // start preview with new settings
            mCamera.setPreviewDisplay(mHolder);
            mCamera.startPreview();
        } catch (Exception e){
          // ignore: tried to stop a non-existent preview
        	DocLog.e(TAG, "Exception", e);
        }
		
	}
	
	@TargetApi(Build.VERSION_CODES.GINGERBREAD)
	@Override
	public void surfaceCreated(SurfaceHolder holder) {
		DocLog.d(TAG, "surfaceCreated");
        // The Surface has been created, now tell the camera where to draw the preview.
        try {
            mCamera.setPreviewDisplay(holder);
            mCamera.startPreview();
        } catch (Exception e) {
            DocLog.e(TAG, "Error setting camera preview: ");
        }
        if (Build.VERSION.SDK_INT > Build.VERSION_CODES.FROYO) {
			android.hardware.Camera.CameraInfo info = new android.hardware.Camera.CameraInfo();
			android.hardware.Camera.getCameraInfo(cameraId, info);
			if (info.facing == Camera.CameraInfo.CAMERA_FACING_FRONT) {
				isFrontCamera = true;
			}
		}
	}

	@Override
	public void surfaceDestroyed(SurfaceHolder holder) {
		DocLog.d(TAG, "surfaceDestroyed");
		// empty. Take care of releasing the Camera preview in your activity.
	}

	@TargetApi(9)
	public int getCameraDisplayOrientation(Activity activity,
			int cameraId, android.hardware.Camera camera) {
		android.hardware.Camera.CameraInfo info = new android.hardware.Camera.CameraInfo();
		android.hardware.Camera.getCameraInfo(cameraId, info);
		int rotation = activity.getWindowManager().getDefaultDisplay()
				.getRotation();
		int degrees = 0;
		switch (rotation) {
		case Surface.ROTATION_0:
			degrees = 0;
			break;
		case Surface.ROTATION_90:
			degrees = 90;
			break;
		case Surface.ROTATION_180:
			degrees = 180;
			break;
		case Surface.ROTATION_270:
			degrees = 270;
			break;
		}

		int result;
		if (isFrontCamera) {
			result = (info.orientation + degrees) % 360;
			result = (360 - result) % 360; // compensate the mirror
		} else { // back-facing
			result = (info.orientation - degrees + 360) % 360;
		}
		return (result);
	}

}
