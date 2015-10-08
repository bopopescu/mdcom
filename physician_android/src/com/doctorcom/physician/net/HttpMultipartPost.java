package com.doctorcom.physician.net;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.io.UnsupportedEncodingException;
import java.nio.charset.Charset;
import java.util.Iterator;
import java.util.Map;

import javax.net.ssl.HostnameVerifier;
import javax.net.ssl.HttpsURLConnection;

import org.apache.http.Header;
import org.apache.http.HttpResponse;
import org.apache.http.HttpVersion;
import org.apache.http.client.ClientProtocolException;
import org.apache.http.client.HttpClient;
import org.apache.http.client.methods.HttpPost;
import org.apache.http.conn.params.ConnManagerParams;
import org.apache.http.conn.ssl.SSLSocketFactory;
import org.apache.http.conn.ssl.X509HostnameVerifier;
import org.apache.http.entity.mime.HttpMultipartMode;
import org.apache.http.entity.mime.content.FileBody;
import org.apache.http.entity.mime.content.StringBody;
import org.apache.http.impl.client.DefaultHttpClient;
import org.apache.http.message.BasicHeader;
import org.apache.http.message.BasicNameValuePair;
import org.apache.http.params.BasicHttpParams;
import org.apache.http.params.HttpConnectionParams;
import org.apache.http.params.HttpParams;
import org.apache.http.params.HttpProtocolParams;
import org.apache.http.protocol.BasicHttpContext;
import org.apache.http.protocol.HTTP;
import org.apache.http.protocol.HttpContext;

import android.content.Context;
import android.os.AsyncTask;

import com.doctorcom.android.R;
import com.doctorcom.physician.AppValues;
import com.doctorcom.physician.utils.DocLog;
import com.doctorcom.physician.utils.FileUtil;
import com.doctorcom.physician.utils.Utils;

public class HttpMultipartPost extends AsyncTask<Void, Integer, String> {

	private String TAG = "HttpMultipartPost";
	private Context context;
	private String postAddress;
	private AppValues appValues;
	private long totalSize;
	private int READ_MAX_LENGTH = 512;
	private Map<String, String> params;
	
	public HttpMultipartPost(Context c, String postAddress) {
		this.context = c;
		appValues = new AppValues(c);
		this.postAddress = appValues.getServerURL() + NetConstantValues.APP_URL + postAddress;

	}

	@Override
	protected String doInBackground(Void... p) {
		Utils utils = new Utils(context);
		if (!utils.checkNetworkAvailable()) {
			return context.getString(R.string.network_not_available);
		}
		String reslut = "";
		HttpParams httpParams = new BasicHttpParams();
		HttpProtocolParams.setVersion(httpParams, HttpVersion.HTTP_1_1);
		HttpProtocolParams.setContentCharset(httpParams, HTTP.UTF_8);
		HttpProtocolParams.setUseExpectContinue(httpParams, true);
		HttpProtocolParams.setUserAgent(httpParams,
				"DoctorCom Android Application");

		HttpClient httpClient = new DefaultHttpClient(httpParams);
		if (appValues.getCurrent_version() == AppValues.ROLE_DEVELOP_VERSION) {
			HostnameVerifier hostnameVerifier = org.apache.http.conn.ssl.SSLSocketFactory.ALLOW_ALL_HOSTNAME_VERIFIER;
			SSLSocketFactory socketFactory = SSLSocketFactory
					.getSocketFactory();
			socketFactory
					.setHostnameVerifier((X509HostnameVerifier) hostnameVerifier);
			HttpsURLConnection.setDefaultHostnameVerifier(hostnameVerifier);
		}
		HttpContext httpContext = new BasicHttpContext();
		HttpPost httpPost = new HttpPost(postAddress);
		// post multipart data
		// set Header
		Header header = new BasicHeader("DCOM_DEVICE_ID",
				appValues.getDcomDeviceId());
		httpPost.setHeader(header);

		CustomMultiPartEntity multipartContent = new CustomMultiPartEntity(HttpMultipartMode.BROWSER_COMPATIBLE, null, Charset.forName("UTF-8"),
				new CustomMultiPartEntity.ProgressListener() {
					@Override
					public void transferred(long num) {
						publishProgress((int) ((num / (float) totalSize) * 100));
						
					}
				}) {

			@Override
			public void writeTo(OutputStream outstream) throws IOException {
				super.writeTo(new CountingOutputStream(outstream, this.listener) {

					@Override
					public void write(byte[] b, int off, int len)
							throws IOException {
						if (isCancelled())
							return;
						super.write(b, off, len);
					}

					@Override
					public void write(int b) throws IOException {
						if (isCancelled())
							return;
						super.write(b);
					}

				});
			}
		};
		if (params != null) {
			Iterator<Map.Entry<String, String>> iter = params.entrySet().iterator();
			while (iter.hasNext()) {
				Map.Entry<String, String> entry = iter.next();
				String name = entry.getKey();
				String value = entry.getValue();
				File uploadFile = new File(value);
				if (uploadFile.isFile()) {
					FileBody fileBody = new FileBody(uploadFile, FileUtil.getMIMEType(uploadFile), "UTF-8");
					multipartContent.addPart(name, fileBody);
					DocLog.d(TAG, "Param > File " + name + " : " + value);
				} else {
					try {
						StringBody strBody = new StringBody(value, Charset.forName("UTF-8"));
						multipartContent.addPart(name, strBody);
						DocLog.d(TAG, "Param > String " + name + " : " + value);
					} catch (UnsupportedEncodingException ex) {
						DocLog.e(TAG, "getRequestEntityParams on POST_TYPE_MULTIPART error", ex);
					}
				}
			}
		}
		totalSize = multipartContent.getContentLength();

		// Send it
		httpPost.setEntity(multipartContent);
		HttpResponse response = null;
		try {
			HttpParams postParams = httpPost.getParams();
			ConnManagerParams.setTimeout(postParams, 1000);
			HttpConnectionParams.setConnectionTimeout(postParams, 15000);
			HttpConnectionParams.setSoTimeout(postParams, 60000);
			response = httpClient.execute(httpPost, httpContext);
		} catch (ClientProtocolException e) {
			DocLog.d(TAG, "ClientProtocolException", e);
		} catch (IOException e) {
			DocLog.d(TAG, "IOException", e);
		}
		if (response != null) {
			int statusCode = response.getStatusLine().getStatusCode();
			DocLog.d(TAG, "StatusCode > " + statusCode);
			// set the status unexpected json string
			// if (statusCode != 200) {
			// if (statusCode == 404) {
			// return DoctorComConn.JSONERROR_404;
			// } else if (statusCode == 500) {
			// return DoctorComConn.JSONERROR_500;
			// }
			// }

			InputStream input = null;
			try {
				input = response.getEntity().getContent();

				// read as text
				ByteArrayOutputStream outputStream = new ByteArrayOutputStream();
				byte[] buffer = new byte[READ_MAX_LENGTH];
				int len = -1;
				while ((len = input.read(buffer)) != -1) {
					outputStream.write(buffer, 0, len);
				}
				byte[] data = outputStream.toByteArray();
				reslut = new String(data, HTTP.UTF_8);
				outputStream.close();
				input.close();
			} catch (IllegalStateException e) {
				DocLog.e(TAG, "IllegalStateException", e);
			} catch (IOException e) {
				DocLog.e(TAG, "IOException", e);
			}
		}
		try {
			if (httpClient != null)
				httpClient.getConnectionManager().shutdown();
		} catch (Exception ex) {
			DocLog.e(TAG, "ConnectionManager shutdown Exception", ex);
		}
		// if(reslut == null || reslut.length() <= 0){
		// reslut = DoctorComConn.JSONERROR_UNKOWN;
		// }
		DocLog.d(TAG, "Reslut > " + reslut);
		return reslut;
	}
	
	protected Header getDoctorHeader(BasicNameValuePair... params) {
		Header header = null;
		int length = params.length;
		for (int i = 0; i < length; i++) {
			String name = params[i].getName();
			String value = params[i].getValue();
			if ("DCOM_DEVICE_ID".equals(name)) {
				DocLog.d(TAG, "Head > String " + name + " : " + value);
				header = new BasicHeader(name, value);
				break;
			}
		}
		return header;
	}

	public Map<String, String> getParams() {
		return params;
	}

	public void setParams(Map<String, String> params) {
		this.params = params;
	}

}
