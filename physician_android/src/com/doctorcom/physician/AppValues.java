package com.doctorcom.physician;

import java.util.Locale;

import android.content.Context;
import android.content.SharedPreferences;

import com.doctorcom.physician.net.NetConstantValues;
import com.doctorcom.physician.settings.AppSettings;
import com.doctorcom.physician.settings.Preference;
import com.doctorcom.physician.utils.AESEncryptDecrypt;
import com.doctorcom.physician.utils.AESEncryptDecrypt.AESEncryptDecryptException;
import com.doctorcom.physician.utils.DocLog;

public class AppValues {

	private Context mContext;
	private AppSettings setting;

	public AppValues(Context con) {
		mContext = con;
		setting = new AppSettings(mContext);
	}

	public static final String DCOM_DEVICE_ID = "dcom_id";
	private static String dcomDeviceId = "";
	private static String secret = "";
	public static final String aeskey = "kd@u789shiWdI8@jd_dDk";
	public static final String secretKey = "/sk.key";

	public static final int ENGLISH_SERVER = 0;
	public static final int DE_SERVER = 1;
	public static final int DEV_SERVER = 2;
	public static final int MY_SERVER = 3;
	public static final int ROLE_DEVELOP_VERSION = 0;
	public static final int ROLE_PRODUCT_VERSION = 1;

	public static final String PLATFORM = "Android";

	public static final int PROVIDER = 1;
	public static final int PRACTICE_MANAGER = 100;
	public static final int STAFF = 101;

	private static String mdcomNumber = "";

	public static final int PAGE_COUNT = 25;

	public static final int REFRESH = 2, LOAD_MORE = 1, INIT = 0;

	public static final int BACKGROUND_REFRESH = 1, NO_BACKGROUND_REFRESH = 0;

	public static final int EMAIL_VALIDATE = 1, MESSAGE_VALIDATE = 2,
			PAGER_VALIDATE = 3;

	private static String projectId = null;
	private static String serverURL = "";

	private static String timezone = "";
	public static final int USE_24HOUR = 0;
	public static final int USE_12HOUR = 1;
	private static int timeFormat = -1;
	private static String preferLogoPath = "";
	public static final String PREFER_LOGO = "prefer_logo";
	private static boolean logined = false;
	private static boolean showPreferLogo = false;
	private static boolean isEncrypted = false;
	private static int currentUserId;
	private static String currentUserName;

	public String getCurrentUserName() {
		if (currentUserName == null || currentUserName.equals(""))
			currentUserName = setting.getSettingString("real_name", "");
		return currentUserName;
	}

	public void setCurrentUserName(String currentUserName) {
		String[] arr = currentUserName.split(" ");
		String targetStr = arr[1] + " " + arr[0];
		setting.setSettingsString("real_name", targetStr);
		AppValues.currentUserName = currentUserName;
	}

	public int getCurrentUserId() {
		if (currentUserId == 0)
			currentUserId = setting.getSettingInt("user_id", 0);
		return currentUserId;
	}

	public void setCurrentUserId(int currentUserId) {
		setting.setSettingsInt("user_id", currentUserId);
		AppValues.currentUserId = currentUserId;
	}

	public boolean isEncrypted() {
		isEncrypted = setting.getSettingBoolean("is_encrypted", false);
		return isEncrypted;
	}

	public void setEncrypted(boolean isEncrypted) {
		setting.setSettingsBoolean("is_encrypted", isEncrypted);
	}

	public boolean isShowPreferLogo() {
		showPreferLogo = setting.getSettingBoolean("show_prefer_logo", false);
		return showPreferLogo;
	}

	public void setShowPreferLogo(boolean showPreferLogo) {
		setting.setSettingsBoolean("show_prefer_logo", showPreferLogo);
	}

	public boolean isLogined() {
		logined = setting.getSettingBoolean("logined", false);
		return logined;
	}

	public void setLogined(boolean logined) {
		setting.setSettingsBoolean("logined", logined);
	}

	public String getPreferLogoPath() {
		if (null == preferLogoPath || "".equals(preferLogoPath))
			preferLogoPath = setting.getSettingString("prefer_logo_path", "");
		return preferLogoPath;
	}

	public void setPreferLogoPath(String preferLogoPath) {
		setting.setSettingsString("prefer_logo_path", preferLogoPath);
		AppValues.preferLogoPath = preferLogoPath;
	}

	public String getDcomDeviceId() {
		if (dcomDeviceId == null || "".equals(dcomDeviceId.trim())
				|| dcomDeviceId.length() <= 5) {
			String value = setting.getSettingString(AppValues.DCOM_DEVICE_ID,
					"");
			String decryptedValue = "";
			if (!"".equals(value)) {
				AESEncryptDecrypt decrypt = new AESEncryptDecrypt(
						AppValues.aeskey, mContext.getCacheDir()
								.getAbsolutePath() + AppValues.secretKey);
				try {
					decryptedValue = decrypt.decrypt(value);
				} catch (AESEncryptDecryptException e) {
					try {
						decryptedValue = decrypt.decrypt(value);
					} catch (AESEncryptDecryptException e1) {
						DocLog.e("AppSettings", "AESEncryptDecryptException", e);
						// bad preference file
						setting.getShare().edit()
								.remove(AppValues.DCOM_DEVICE_ID).commit();

					}
				}
			}
			dcomDeviceId = decryptedValue;
		}
		return dcomDeviceId;
	}

	public boolean isDcomDeviceIdEmpty() {
		dcomDeviceId = getDcomDeviceId();
		if (dcomDeviceId == null || "".equals(dcomDeviceId.trim())
				|| dcomDeviceId.length() <= 5) {
			return true;
		}
		return false;
	}

	public void setDcomDeviceId(String dcomDeviceId) {
		AESEncryptDecrypt decrypt = new AESEncryptDecrypt(AppValues.aeskey,
				mContext.getCacheDir().getAbsolutePath() + AppValues.secretKey);
		String encrytValue = "";
		try {
			encrytValue = decrypt.encrypt(dcomDeviceId);
		} catch (AESEncryptDecryptException e) {
			try {
				encrytValue = decrypt.encrypt(dcomDeviceId);
			} catch (AESEncryptDecryptException e1) {
				DocLog.e("AppSettings", "AESEncryptDecryptException", e);
			}
		}
		setting.setSettingsString(AppValues.DCOM_DEVICE_ID, encrytValue);
		AppValues.dcomDeviceId = dcomDeviceId;
	}

	public String getSecret() {
		if (secret == null || secret.equals("")) {
			String value = setting.getSettingString("dcom_secret", "");
			String decryptedValue = "";
			if (!"".equals(value)) {
				AESEncryptDecrypt decrypt = new AESEncryptDecrypt(
						AppValues.aeskey, mContext.getCacheDir()
								.getAbsolutePath() + AppValues.secretKey);
				try {
					decryptedValue = decrypt.decrypt(value);
				} catch (AESEncryptDecryptException e) {
					try {
						decryptedValue = decrypt.decrypt(value);
					} catch (AESEncryptDecryptException e1) {
						DocLog.e("AppSettings", "AESEncryptDecryptException", e);
						// bad preference file
						setting.getShare().edit().remove("dcom_secret")
								.commit();

					}
				}
			}
			secret = decryptedValue;
		}
		return secret;
	}

	public void setSecret(String secret) {
		AESEncryptDecrypt decrypt = new AESEncryptDecrypt(AppValues.aeskey,
				mContext.getCacheDir().getAbsolutePath() + AppValues.secretKey);
		String encrytValue = "";
		try {
			encrytValue = decrypt.encrypt(secret);
		} catch (AESEncryptDecryptException e) {
			try {
				encrytValue = decrypt.encrypt(secret);
			} catch (AESEncryptDecryptException e1) {
				DocLog.e("AppSettings", "AESEncryptDecryptException", e);
			}
		}
		setting.setSettingsString("dcom_secret", encrytValue);
		AppValues.secret = secret;
	}

	public boolean isCallEnable() {
		return setting.getSettingBoolean("call_enable", false);
	}

	public void setCallEnable(boolean callEnable) {
		setting.setSettingsBoolean("call_enable", callEnable);
	}

	public boolean isCallAvailable() {
		return setting.getSettingBoolean("call_available", false);
	}

	public void setCallAvailable(boolean callAvailable) {
		setting.setSettingsBoolean("call_available", callAvailable);
	}

	public int getCurrent_server() {
		return setting.getSettingInt("current_server", -1);
	}

	public void setCurrent_server(int current_server) {
		setting.setSettingsInt("current_server", current_server);
	}

	public int getCurrent_version() {
		return setting.getSettingInt("current_version", ROLE_DEVELOP_VERSION);
	}

	public void setCurrent_version(int current_version) {
		setting.setSettingsInt("current_version", current_version);
	}

	public String getServerURL() {
		int server = getCurrent_server();
		if (server == -1) {
			SharedPreferences share = mContext.getSharedPreferences("settings",
					Context.MODE_PRIVATE);
			String site = share.getString("site_address", "");
			if (site != null && !site.equals("")) {
				// old version
				return site.substring(0,
						site.indexOf(NetConstantValues.APP_URL));
			} else {
				throw new NullPointerException("server is -1 Exception");
			}
		} else {
			String url = null;
			if (server == MY_SERVER) {
				if (serverURL == null || "".equals(serverURL)) {
					url = (new Preference(mContext))
							.getSettingString("my_server", "").trim()
							.toLowerCase(Locale.US);
					;
					if (url.endsWith("/")) {
						url = url.substring(0, url.length() - 1);
					}
					if (!(url.startsWith("http://") || url
							.startsWith("https://"))) {
						url = "https://" + url;
					}
					serverURL = url;
				} else {
					url = serverURL;
				}
			} else {
				url = NetConstantValues.DOCTORCOM_SITES_ADDRESSES[getCurrent_version()][getCurrent_server()];
			}
			if (url == null || "".equals(url)) {
				throw new NullPointerException("error url");
			}
			return url;
		}
	}

	public void setServerURL(String url) {
		(new Preference(mContext)).setSettingsString("my_server", url);
		url = url.trim().toLowerCase(Locale.US);
		if (url.endsWith("/")) {
			url = url.substring(0, url.length() - 1);
		}
		if (!(url.startsWith("http://") || url.startsWith("https://"))) {
			url = "https://" + url;
		}
		serverURL = url;
	}

	public int getUserType() {
		return setting.getSettingInt("user_type", PROVIDER);
	}

	public void setUserType(int userType) {
		setting.setSettingsInt("user_type", userType);
	}

	public String getMdcomNumber() {
		if (mdcomNumber == null || mdcomNumber.equals("")) {
			mdcomNumber = setting.getSettingString("dcom_number", "");
		}
		return mdcomNumber;
	}

	public void setMdcomNumber(String mdcomNumber) {
		AppValues.mdcomNumber = mdcomNumber;
	}

	public String getProjectId() {
		if (projectId == null || projectId.equals("")) {
			projectId = setting.getSettingString("gcm", "");
			SharedPreferences share = mContext.getSharedPreferences(
					"com.google.android.gcm", Context.MODE_PRIVATE);
			projectId = share.getString("projectId",
					setting.getSettingString("gcm", ""));
		}
		return projectId;
	}

	public void setProjectId(String projectId) {
		AppValues.projectId = projectId;
	}

	public String getTimezone() {
		if (timezone == null || "".equals(timezone)) {
			timezone = setting.getSettingString("timezone", "");
		}
		return timezone;
	}

	public void setTimezone(String timezone) {
		AppValues.timezone = timezone;
		setting.setSettingsString("timezone", timezone);
	}

	public int getTimeFormat() {
		if (timeFormat == -1) {
			timeFormat = setting.getSettingInt("timeformat",
					AppValues.USE_24HOUR);
		}
		return timeFormat;
	}

	public void setTimeFormat(int timeFormat) {
		AppValues.timeFormat = timeFormat;
		setting.setSettingsInt("timeformat", timeFormat);
	}
}
