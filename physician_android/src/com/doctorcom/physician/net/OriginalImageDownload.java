package com.doctorcom.physician.net;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.UnsupportedEncodingException;
import java.net.HttpURLConnection;
import java.net.SocketTimeoutException;
import java.net.URL;

import javax.net.ssl.HttpsURLConnection;

import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.os.AsyncTask;

import com.doctorcom.android.R;
import com.doctorcom.physician.utils.DocLog;
import com.doctorcom.physician.utils.FileUtil;
import com.doctorcom.physician.utils.Utils;

public class OriginalImageDownload extends AsyncTask<String, Integer, Bitmap>  {
	
	private String TAG = "ImageDownload";
	private Context mContext;
	private String id;
	final static long connect_expire_time = 6000;
	final static int retry_time = 10;
	
	public interface OrinialImageDownloadFinishListener{
		public void onOrinialImageDownloadFinish(Bitmap result);
	}

	public OriginalImageDownload(Context con, String id) {
		mContext = con;
		this.id = id;
	}

	@Override
	protected Bitmap doInBackground(String... params) {
		return connect(0, params[0]);
	}
	
	public Bitmap connect(int loop, String params) {
//		params = toUNICODE(params);
		try {
			params =  new String(params.getBytes("UTF-8"));
			DocLog.i(TAG, params);
		} catch (UnsupportedEncodingException e1) {
			// TODO Auto-generated catch block
			DocLog.e(TAG, "UnsupportedEncodingException", e1);
		}
		Bitmap bitmap = null;
		long startTime = System.currentTimeMillis();
		String result = "";
		String parent = FileUtil.getAppPath(mContext);
		if (parent == null) {
			try {
				return streamBitmap(params);
			} catch (IOException e) {
				long currentTime = System.currentTimeMillis();
				if((currentTime - startTime) < connect_expire_time)
				{
					loop ++;
					if(loop<retry_time)
					{
						DocLog.i(TAG, "Retry: ("+loop+") times.");
						return connect(loop, params);
					}
				}
				DocLog.e(TAG, "IOException", e);
				return null;
			}
		}
	    InputStream is = null;
	    String absFilePath = null;
	    try {
			URL url = new URL(params);
			absFilePath = parent + "/des" + id + params.substring(params.lastIndexOf("/") + 1);
			File file = new File(absFilePath);
		    if (System.currentTimeMillis() - file.lastModified() > (15 *60 *1000)){
		    	file.delete();
		    }
			if (!file.exists()) {
				DocLog.d(TAG, "down load file " + absFilePath);
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
					if (response <=0) {
						long currentTime = System.currentTimeMillis();
						if((currentTime - startTime) < connect_expire_time)
						{
							loop ++;
							if(loop<retry_time)
							{
								DocLog.i(TAG, "Retry: ("+loop+") times.");
								return connect(loop, params);
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
					DocLog.e(TAG, "error: " + result);
					return null;
				}
				is = conn.getInputStream();
				if (is == null)
					return null;
				try {
					byte buffer[] = new byte[1024 * 4];
					int len = 0;			
					FileOutputStream fos = new FileOutputStream(absFilePath);
					while ((len = is.read(buffer)) != -1) {
						fos.write(buffer, 0, len);
					}
					fos.close();					
			    } catch (IOException e) {
			    	DocLog.e(TAG, "write to sd card fail", e);
			    	return streamBitmap(url);
			    }
			}
		} catch (SocketTimeoutException e) {
			DocLog.e(TAG, "SocketTimeoutException", e);
			result = mContext.getString(R.string.get_data_error_socket);
			
			long currentTime = System.currentTimeMillis();
			if((currentTime - startTime) < connect_expire_time)
			{
				loop ++;
				if(loop<retry_time)
				{
					DocLog.i(TAG, "Retry: ("+loop+") times.");
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
	    bitmap = BitmapFactory.decodeFile(absFilePath);
	    File file = new File(absFilePath);
	    file.delete();
	    return bitmap;
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
		((OrinialImageDownloadFinishListener)mContext).onOrinialImageDownloadFinish(result);
	}
    public static byte[] getBytesFromInputStream(InputStream is) throws IOException {
        ByteArrayOutputStream outstream = new ByteArrayOutputStream();
        byte[] buffer = new byte[1024];
        int len = -1;
        while ((len = is.read(buffer)) != -1) {
            outstream.write(buffer, 0, len);
        }
        outstream.close();
        return outstream.toByteArray();
    }
    
    public static String toUNICODE(String s) {
		StringBuffer sb = new StringBuffer();
		for (int i = 0; i < s.length(); i++) {

			if (s.charAt(i) >= 256)// ASC11表中的字符码值不够4位,补00
			{
				sb.append("\\u");
				// System.out.println(Integer.toHexString(s.charAt(i)));
				sb.append(Integer.toHexString(s.charAt(i)));
			} else
				sb.append(s.charAt(i));
		}
		return sb.toString();
	}
}
