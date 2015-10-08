package com.doctorcom.physician.net;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.SocketTimeoutException;
import java.net.URL;

import javax.net.ssl.HttpsURLConnection;

import android.content.Context;
import android.content.res.Resources;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.os.AsyncTask;
import android.widget.ImageView;

import com.doctorcom.android.R;
import com.doctorcom.physician.AppValues;
import com.doctorcom.physician.utils.AESEncryptDecrypt;
import com.doctorcom.physician.utils.DocLog;
import com.doctorcom.physician.utils.FileUtil;
import com.doctorcom.physician.utils.Utils;

public class ImageDownload extends AsyncTask<String, Integer, Bitmap> {

	private String TAG = "ImageDownload";
	private Context mContext;
	private String id;
	private ImageView mImageView;
	final static long connect_expire_time = 6000;
	final static int retry_time = 10;

	public ImageDownload(Context con, String id, ImageView imageView,
			int defaultImage) {
		mContext = con;
		this.id = id;
		mImageView = imageView;
	}

	@Override
	protected Bitmap doInBackground(String... params) {
		return connect(0, params[0]);
	}

	public Bitmap connect(int loop, String params) {
		Bitmap bitmap = readDefaultImage(mContext, params);
		if (bitmap != null) {
			return bitmap;
		}
		long startTime = System.currentTimeMillis();
		String result = "";
		String parent = FileUtil.getAppPath(mContext);
		if (parent == null) {
			try {
				return streamBitmap(params);
			} catch (IOException e) {
				long currentTime = System.currentTimeMillis();
				if ((currentTime - startTime) < connect_expire_time) {
					loop++;
					if (loop < retry_time) {
						DocLog.i(TAG, "Retry: (" + loop + ") times.");
						return connect(loop, params);
					}
				}
				DocLog.e(TAG, "IOException", e);
				return null;
			}
		}
		InputStream is = null;
		String absFilePath, originalFilePath = null;
		File originalFile = null;
		try {
			URL url = new URL(params);
			absFilePath = parent + "/" + id
					+ params.substring(params.lastIndexOf("/") + 1);
			AESEncryptDecrypt decrypt = new AESEncryptDecrypt(AppValues.aeskey,
					mContext.getCacheDir().getAbsolutePath()
							+ AppValues.secretKey);
			File file = new File(absFilePath);
			originalFilePath = file.getParent() + "/des" + file.getName();
			originalFile = new File(originalFilePath);
			if (System.currentTimeMillis() - file.lastModified() > (15 * 60 * 1000)) {
				file.delete();
			}
			if (!file.exists()) {
				DocLog.d(TAG, "down load file " + originalFilePath);
				HttpURLConnection conn;
				if (url.getProtocol().equals("https")) {
					conn = (HttpsURLConnection) url.openConnection();
				} else {
					conn = (HttpURLConnection) url.openConnection();
				}
				conn.setDoInput(true);
				conn.setUseCaches(false);
				conn.setReadTimeout(60000 /* milliseconds */);
				conn.setConnectTimeout(15000 /* milliseconds */);
				DocLog.d(TAG, url.toString());
				int response = conn.getResponseCode();
				DocLog.d(TAG, "status: " + response);
				if (response != HttpsURLConnection.HTTP_OK) {
					if (response <= 0) {
						long currentTime = System.currentTimeMillis();
						if ((currentTime - startTime) < connect_expire_time) {
							loop++;
							if (loop < retry_time) {
								DocLog.i(TAG, "Retry: (" + loop + ") times.");
								return connect(loop, params);
							}
						}

						result = mContext.getString(R.string.get_data_error_exception);
					} else if (response < 400) {
						InputStream inputStream = conn.getInputStream();
						result = Utils.stream2String(inputStream);
						inputStream.close();
					} else {
						InputStream inputStream = conn.getErrorStream();
						result = Utils.stream2String(inputStream);
						inputStream.close();
					}
					DocLog.e(TAG, "error: " + result);
					return null;
				}
				is = conn.getInputStream();
				if (is == null)
					return null;
				try {
					byte buffer[] = new byte[1024 * 4];
					int len = 0;
					FileOutputStream fos = new FileOutputStream(
							originalFilePath);
					while ((len = is.read(buffer)) != -1) {
						fos.write(buffer, 0, len);
					}
					fos.close();
					// Encrypt
					decrypt.encrypt(originalFile, file);
				} catch (IOException e) {
					DocLog.e(TAG, "write to sd card fail", e);
					return streamBitmap(url);
				}
			} else {
				decrypt.decrypt(file, originalFile);
			}
		} catch (SocketTimeoutException e) {
			DocLog.e(TAG, "SocketTimeoutException", e);
			result = mContext.getString(R.string.get_data_error_socket);

			long currentTime = System.currentTimeMillis();
			if ((currentTime - startTime) < connect_expire_time) {
				loop++;
				if (loop < retry_time) {
					DocLog.i(TAG, "Retry: (" + loop + ") times.");
					return connect(loop, params);
				}
			}
		} catch (Exception e) {
			DocLog.e(TAG, "Exception", e);

			return null;
		} finally {
			if (is != null) {
				try {
					is.close();
				} catch (IOException e) {
					DocLog.e(TAG, "IOException", e);
				}
			}
		}
		bitmap = BitmapFactory.decodeFile(originalFilePath);
		originalFile.delete();
		return bitmap;
	}

	static public Bitmap readDefaultImage(Context context, String url) {
		Resources resources = null;
		if (context == null)
			DocLog.e("TEST HAHHA.....", "CONTEXT IS NULL");
		else
			resources = context.getResources();
		if (url != null && context != null) {
			if (url.endsWith("images/photos/avatar2.png")) {
				return BitmapFactory.decodeResource(resources,
						R.drawable.avatar2);
			} else if (url.endsWith("images/photos/hospital_icon.jpg")) {
				return BitmapFactory.decodeResource(resources,
						R.drawable.hospital_icon);
			} else if (url.endsWith("images/photos/staff_icon.jpg")) {
				return BitmapFactory.decodeResource(resources,
						R.drawable.staff_icon);
			} else if (url.endsWith("images/photos/broker.jpg")) {
				return BitmapFactory.decodeResource(resources,
						R.drawable.broker);
			} else if (url.endsWith("images/photos/nurse.jpg")) {
				return BitmapFactory
						.decodeResource(resources, R.drawable.nurse);
			} else if (url.endsWith("images/photos/avatar_male_small.png")){
				return BitmapFactory
						.decodeResource(resources, R.drawable.avatar_male_small);
			}else if (url.endsWith("images/photos/face_01.png")){
				return BitmapFactory
						.decodeResource(resources, R.drawable.face_01);
			}else if (url.endsWith("images/photos/face_02.png")){
				return BitmapFactory
						.decodeResource(resources, R.drawable.face_02);
			}else if (url.endsWith("images/photos/face_03.png")){
				return BitmapFactory
						.decodeResource(resources, R.drawable.face_03);
			}
		}
		return null;
	}

	public static Bitmap streamBitmap(URL url) throws IOException {
		byte[] data = getBytesFromInputStream(url.openStream());
		return BitmapFactory.decodeByteArray(data, 0, data.length);

	}

	public static Bitmap streamBitmap(String url) throws IOException {
		byte[] data = getBytesFromInputStream(new URL(url).openStream());
		return BitmapFactory.decodeByteArray(data, 0, data.length);

	}

	@Override
	protected void onPostExecute(Bitmap result) {
		if (result != null) {
			mImageView.setScaleType(ImageView.ScaleType.CENTER_INSIDE);
			mImageView.setImageBitmap(result);
		}
	}

	public static byte[] getBytesFromInputStream(InputStream is)
			throws IOException {
		ByteArrayOutputStream outstream = new ByteArrayOutputStream();
		byte[] buffer = new byte[1024];
		int len = -1;
		while ((len = is.read(buffer)) != -1) {
			outstream.write(buffer, 0, len);
		}
		outstream.close();
		return outstream.toByteArray();
	}
}
