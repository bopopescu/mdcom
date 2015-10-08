package com.doctorcom.physician.utils;

import java.io.IOException;
import java.io.InputStream;
import java.util.Calendar;
import java.util.TimeZone;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import org.json.JSONException;
import org.json.JSONObject;

import android.annotation.TargetApi;
import android.content.Context;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.content.pm.PackageManager.NameNotFoundException;
import android.net.ConnectivityManager;
import android.net.NetworkInfo;
import android.os.Build;
import android.util.SparseArray;

import com.doctorcom.physician.AppValues;

public class Utils {
	
	private final static String TAG = "Utils";
	private Context context;
	public Utils(Context context) {
		this.context = context;
	}

	public static boolean isDeviceDissociated(String result) throws JSONException {
		JSONObject jsonObj = new JSONObject(result);
		if (jsonObj.has("errno")) {
			if (jsonObj.getString("errno").equalsIgnoreCase("dm003")) {
				return true;
			}
		}
		return false;

	}
	
	public static boolean isMobilePhoneValidated(String result) throws JSONException {
		JSONObject jsonObj = new JSONObject(result);
		if (jsonObj.has("errno")) {
			if (jsonObj.getString("errno").equalsIgnoreCase("ge005")) {
				return true;
			}
		}
		return false;
		
	}
	public static String stream2String(InputStream is) {
		StringBuffer sb = new StringBuffer();
		try {
			int i = -1;
			byte[] b = new byte[1024];
			while ((i = is.read(b)) != -1) {
				sb.append(new String(b, 0, i));
			}
		} catch (IOException e) {
			e.printStackTrace();
			return "";
		}
		return sb.toString();

	}
	
	public static String getVersion(Context context) {
		String versionName = "1.0.0001";
		PackageManager pm = context.getPackageManager();
		PackageInfo pi;
		try {
			pi = pm.getPackageInfo(context.getPackageName(), PackageManager.GET_ACTIVITIES);
			versionName = pi.versionName;
		} catch (NameNotFoundException e) {
			DocLog.e(TAG, "exception when check new version",e);
		}
		return versionName;
	}
	
	public static boolean validatePhone(String phone) {
		if (phone.equals("") || phone == null) {
			return false;
		}
		Pattern pat = Pattern.compile("(?<!\\d{1})(?<!\\+)(((\\+?1)[\\s,-]{1})?(\\(\\d{3}\\)|\\d{3})[\\s,-]{1}\\d{3}[\\s,-]\\d{4}|(\\+?1)?\\d{10})(?!\\d{1})", Pattern.CASE_INSENSITIVE);

		Matcher matcher = pat.matcher(phone);
		if (matcher.matches()) {
			return true;
		} else {
			return false;
		}
	}
	
	public static boolean validateEmail(String email){
		if(email.equals("") || email==null) {
			return false;
		}
		Pattern pat = Pattern.compile("^[A-Za-z0-9+]+[A-Za-z0-9\\.\\_\\-+]*@([A-Za-z0-9\\-]+\\.)+[A-Za-z0-9]+$", Pattern.CASE_INSENSITIVE);
	     
		Matcher matcher = pat.matcher(email);
		if(matcher.matches()) {
			return true;
		}
		else{
			return false;
		}
	}
	
	public static boolean validateURLIP(String url) {
		if (url == null || "".equals(url)) {
			return false;
		}
		Pattern pat = Pattern.compile(
			"^(http[s]{0,1}://)?((([\\w-]+\\.)+((com)|(net)|(org)|(gov\\.cn)|(info)|(cc)|(com\\.cn)|(net\\.cn)|(org\\.cn)|(name)|(biz)|(tv)|(cn)|(mobi)|(name)|(sh)|(ac)|(io)|(tw)|(com\\.tw)|(hk)|(com\\.hk)|(ws)|(travel)|(us)|(tm)|(la)|(me\\.uk)|(org\\.uk)|(ltd\\.uk)|(plc\\.uk)|(in)|(eu)|(it)|(jp)))|(((25[0-5])|(2[0-4]\\d)|(1\\d\\d)|([1-9]\\d)|\\d)(\\.((25[0-5])|(2[0-4]\\d)|(1\\d\\d)|([1-9]\\d)|\\d)){3}))(:([0-9]|[1-9]\\d|[1-9]\\d{2}|[1-9]\\d{3}|[1-5]\\d{4}|6[0-4]\\d{3}|65[0-4]\\d{2}|655[0-2]\\d|6553[0-5]))?/?$",
						Pattern.CASE_INSENSITIVE);

		Matcher matcher = pat.matcher(url);
		if(matcher.matches()) {
			return true;
		}
		else{
			return false;
		}

	}

	public static String getNumberOfPhone(String phone) {
		return phone.replaceAll("\\(","").replaceAll("\\) ","").replaceAll("-","");
	}
	
	public static String getDateTimeFormat(long timeStamp, int timeFormat, String timezone) {
		TimeZone timeZone = TimeZone.getTimeZone(timezone);
		Calendar calendar = Calendar.getInstance();
		calendar.setTimeInMillis(timeStamp);
		calendar.setTimeZone(timeZone);
		CharSequence dateTime;
		if (timeFormat == AppValues.USE_12HOUR) {
			dateTime = android.text.format.DateFormat.format("MM/dd/yyyy hh:mm aa", calendar);
		} else {
			dateTime = android.text.format.DateFormat.format("MM/dd/yyyy kk:mm", calendar);
		}
		return dateTime.toString();
	}
	
	public static String getDateFormat(long timeStamp, String timezone) {
		TimeZone timeZone = TimeZone.getTimeZone(timezone);
		Calendar calendar = Calendar.getInstance();
		calendar.setTimeInMillis(timeStamp);
		calendar.setTimeZone(timeZone);
		CharSequence dateTime;
		dateTime = android.text.format.DateFormat.format("MM/dd/yyyy", calendar);
		return dateTime.toString();
	}
	
	public boolean checkNetworkAvailable() {
		ConnectivityManager connMgr = (ConnectivityManager) context.getSystemService(Context.CONNECTIVITY_SERVICE);
		NetworkInfo networkInfo = connMgr.getActiveNetworkInfo();
		if (networkInfo != null && networkInfo.isConnected()) {
			return true;
		} else {
			return false;
		}

	}
	static public SparseArray<String> getNumbers(String content) {
		SparseArray<String> digitList = new SparseArray<String>();
		Pattern p = Pattern.compile("(?<!\\d{1})(?<!\\+)(((\\+?1)[\\s,-]{1})?(\\(\\d{3}\\)|\\d{3})[\\s,-]{1}\\d{3}[\\s,-]\\d{4}|(\\+?1)?\\d{10})(?!\\d{1})", Pattern.CASE_INSENSITIVE);
		Matcher m = p.matcher(content);
		while (m.find()) {
			int start = m.start();
			String find = m.group().toString();
			digitList.put(start, find);
		}
		return digitList;
	}
	
	@SuppressWarnings("deprecation")
	@TargetApi(Build.VERSION_CODES.HONEYCOMB)
	public void copy(String txt) {
		if(Build.VERSION.SDK_INT < Build.VERSION_CODES.HONEYCOMB) {
			android.text.ClipboardManager mClipboardManager = (android.text.ClipboardManager) context.getSystemService(Context.CLIPBOARD_SERVICE);
			mClipboardManager.setText(txt);
		} else {
			android.content.ClipboardManager clipboard = (android.content.ClipboardManager) context.getSystemService(Context.CLIPBOARD_SERVICE);
			clipboard.setPrimaryClip(android.content.ClipData.newPlainText("simple text",txt));
		}

	}
}
