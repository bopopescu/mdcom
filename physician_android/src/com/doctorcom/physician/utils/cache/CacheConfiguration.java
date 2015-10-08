package com.doctorcom.physician.utils.cache;

import java.util.HashMap;
import java.util.Map;

import com.doctorcom.physician.net.NetConstantValues;

/**
 * 
 * @author zhu
 * @version v1.0
 * 
 */
public class CacheConfiguration {
	private CacheConfiguration() {

	}

	private static CacheConfiguration cacheConfiguration;

	public static CacheConfiguration getCacheConfigurationInstance() {
		if (cacheConfiguration == null) {
			cacheConfiguration = new CacheConfiguration();
		}
		return cacheConfiguration;
	}

	private static Map<String, Values> cacheConfigMap;

	private Map<String, Values> getInstance() {
		if (cacheConfigMap == null) {
			cacheConfigMap = new HashMap<String, Values>();

			Values value = new Values(60, true, false);
			cacheConfigMap.put("/Messaging/List/Received/", value);

			value = new Values(60, true, false);
			cacheConfigMap.put("/Messaging/List/Sent/", value);

			value = new Values(60, true, false);
			cacheConfigMap.put("/Followups/List/", value);

			value = new Values(60, true, false);
			cacheConfigMap.put("/Messaging/Threading/List/", value);
			
			value = new Values(60, true, false);
			cacheConfigMap.put("/Messaging/Threading/Body/", value);
			
			value = new Values(60, true, false);
			cacheConfigMap.put(NetConstantValues.RECEIVED_LIST_BODY.PATH, value);
			
			value = new Values(60, true, false);
			cacheConfigMap.put(NetConstantValues.SENT_LIST_BODY.PATH, value);

			value = new Values(60, true, false);
			cacheConfigMap.put("/User_Lists/My_Site/Providers/", value);

			value = new Values(60, true, false);
			cacheConfigMap.put("/User_Lists/My_Site/Staff/", value);

			value = new Values(60, true, false);
			cacheConfigMap.put("/User_Lists/My_Practice/Providers/", value);

			value = new Values(60, true, false);
			cacheConfigMap.put("/User_Lists/My_Practice/Staff/", value);

			value = new Values(60, true, false);
			cacheConfigMap.put("/User_Lists/Community/Providers/", value);

			value = new Values(60, true, false);
			cacheConfigMap.put("/User_Lists/My_Site/Med_Students/", value);

			value = new Values(60, true, false);
			cacheConfigMap.put("/Practice_Lists/LocalOffice/", value);

			value = new Values(0, false, false);
			cacheConfigMap.put("/User/Search/", value);

			value = new Values(60 * 60, true, false);
			cacheConfigMap.put("/User/*/Profile/", value);

			value = new Values(24 * 60 * 60, true, false);
			cacheConfigMap.put("/Practice/*/Profile/", value);

			value = new Values(-1, true, false);
			cacheConfigMap.put("/Messaging/Message/*/", value);

			value = new Values(60 * 60, true, false);
			cacheConfigMap.put("/Invitations/List/", value);

			value = new Values(15 * 60, true, false);
			cacheConfigMap.put("/Site/", value);

			value = new Values(15 * 60, true, false);
			cacheConfigMap.put("/Practice/", value);

			value = new Values(15 * 60, true, false);
			cacheConfigMap.put("/Account/CallForwarding/", value);

			value = new Values(15 * 60, true, false);
			cacheConfigMap.put("/Account/AnsweringService/", value);

			value = new Values(15 * 60, true, false);
			cacheConfigMap.put("/Account/Preference/", value);

			value = new Values(10 * 60, true, false);
			cacheConfigMap.put("/Tab/GetUserTabs/", value);

			value = new Values(60, true, false);
			cacheConfigMap.put("/Org/*/Users/", value);

			value = new Values(60, true, false);
			cacheConfigMap.put("/MyFavorite/", value);

			value = new Values(-1, true, false);
			cacheConfigMap.put("/Messaging/Message/*/DicomInfo/*/", value);
		}
		return cacheConfigMap;

	}

	public Values getValues(String name) {
		if (cacheConfigMap == null) {
			cacheConfigMap = getInstance();
		}
		return cacheConfigMap.get(name);
	}

	public int getExpiredTime(String name) {
		Values value = getValues(name);
		if (value != null) {
			return value.getExpiredTime();
		}
		return -1;
	}

	public boolean getBackgroundRefresh(String name) {
		Values value = getValues(name);
		if (value != null) {
			return value.isBackgroundRefresh();
		}
		return false;
	}

	public static class Values {
		int expiredTime;
		boolean backgroundRefresh;
		boolean requiredBackgroundRefresh;

		public Values() {

		}

		public Values(int expiredTime, boolean backgroundRefresh, boolean requiredBackgroundRefresh) {
			this.expiredTime = expiredTime;
			this.backgroundRefresh = backgroundRefresh;
			this.requiredBackgroundRefresh = requiredBackgroundRefresh;
		}

		public int getExpiredTime() {
			return expiredTime;
		}

		public void setExpiredTime(int expiredTime) {
			this.expiredTime = expiredTime;
		}

		public boolean isBackgroundRefresh() {
			return backgroundRefresh;
		}

		public void setBackgroundRefresh(boolean backgroundRefresh) {
			this.backgroundRefresh = backgroundRefresh;
		}

		public boolean isRequiredBackgroundRefresh() {
			return requiredBackgroundRefresh;
		}

		public void setRequiredBackgroundRefresh(
				boolean requiredBackgroundRefresh) {
			this.requiredBackgroundRefresh = requiredBackgroundRefresh;
		}

	}
}
