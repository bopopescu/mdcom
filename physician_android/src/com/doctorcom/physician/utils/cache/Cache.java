package com.doctorcom.physician.utils.cache;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;

import org.json.JSONException;
import org.json.JSONObject;

import android.content.ContentValues;
import android.content.Context;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.os.AsyncTask;

import com.doctorcom.physician.AppValues;
import com.doctorcom.physician.net.NetConstantValues;
import com.doctorcom.physician.net.http.NetConncet;
import com.doctorcom.physician.utils.AESEncryptDecrypt;
import com.doctorcom.physician.utils.AESEncryptDecrypt.AESEncryptDecryptException;
import com.doctorcom.physician.utils.DocLog;

public class Cache {

	private final String TAG = "cache class";
	public static final int CACHE_OTHER = 0;
	/**
	 * path: /User_Lists/My_Site/Providers/; /User_Lists/My_Site/Staff/;
	 * /User_Lists/My_Practice/Providers/; /User_Lists/My_Practice/Staff/;
	 * /User_Lists/Community/Providers/; /User_Lists/My_Site/Med_Students/;
	 * /Practice_Lists/LocalOffice/
	 */
	public static final int CACHE_USER_LIST = 1;
	/** path: /User/~/Profile/ */
	public static final int CACHE_USER_PROFILE = 2;
	/** path: /Practice/~/Profile/ */
	public static final int CACHE_PRACTICE_PROFILE = 3;
	/** path: /Messaging/Message/~/ */
	public static final int CACHE_MESSAGE_BODY = 4;
	/** path: /Invitations/List/ */
	public static final int CACHE_INVITATION_LIST = 5;
	/** path: /Site/ */
	public static final int CACHE_SITE = 6;
	/** path: /Practice/ */
	public static final int CACHE_PRACTICE = 7;
	/** path: /Account/CallForwarding/ */
	public static final int CACHE_CALLFORWARDING = 8;
	/** path: /Account/AnsweringService/ */
	public static final int CACHE_ANSWERINGSERVICE = 9;
	public static final int CACHE_USER_TABS = 11;
	public static final int CACHE_MESSAGE_RECEIVED_LIST = 100;
	public static final int CACHE_MESSAGE_SENT_LIST = 101;
	public static final int CACHE_THREADING_LIST = 102;
	public static final int CACHE_THREADING_BODY = 103;

	public int cacheType = CACHE_OTHER;

	private Context context;
	private final int DATABASE_COUNT = 1000;
	private final int MEMORY_COUNT = 100;
	private String result = "";
	private String postAddress;
	private String strParams;
	private int memoryIndex = -1;
	private String url;
	private HashMap<String, String> ps;
	private int method = NetConncet.HTTP_POST;// post
	private Object activity;
	private AppValues appValues;
	private CacheConfiguration cacheConfiguration;
	private String selection;

	public final int STATUS_NO_FIND = 0;
	public final int STATUS_OVERDUE = 1;
	public final int STATUS_NORMAL = -1;
	private int cacheStatus = STATUS_NO_FIND;

	public final int BACKGROUND_REFRESH = 1;
	public final int NO_BACKGROUND_REFRESH = 0;
	private int backgroundRefresh = NO_BACKGROUND_REFRESH;

	private boolean requiredBackgroundRefresh = false;

	private boolean doBackgroundRefresh = false;

	private static List<RequestList> memoryRequestList = null;

	private final int MEMORY_TIME = 60;
	public final static int SEARCH_MEMORY_ONLY = 1;
	public final static int SEARCH_DATABASE_ONLY = 1 << 1;
	private int howSearch = SEARCH_DATABASE_ONLY;

	public interface CacheFinishListener {
		void onCacheFinish(String result, boolean isCache);
	}

	public Cache(Context context, int method) {
		this.context = context;
		this.method = method;
		if(context == null)
			return;
		appValues = new AppValues(context);
		cacheConfiguration = CacheConfiguration.getCacheConfigurationInstance();
	}

	public void setCacheType(int cacheType) {
		this.cacheType = cacheType;
	}

	public void setHowSearch(int howSearch) {
		this.howSearch = howSearch;
	}

	public void useCache(Object activity, String urlPath, String asterisk,
			HashMap<String, String> params) {
		if (urlPath == null)
			return;
		postAddress = appValues.getServerURL() + NetConstantValues.APP_URL
				+ urlPath;
		// message, task list
		strParams = pair2String(params);
		DocLog.d(TAG, urlPath);
		DocLog.d(TAG, strParams);
		this.activity = activity;

		if (asterisk == null) {
			selection = urlPath;
		} else {
			selection = asterisk;
		}
		url = urlPath;
		getCacheStatus(urlPath, asterisk, params);
	}

	private void getCacheStatus(String urlPath, String asterisk,
			HashMap<String, String> params) {
		if (cacheConfiguration.getValues(selection) != null) {
			if (cacheConfiguration.getBackgroundRefresh(selection)) {
				backgroundRefresh = BACKGROUND_REFRESH;
			} else {
				backgroundRefresh = NO_BACKGROUND_REFRESH;
			}
			if (cacheConfiguration.getValues(selection)
					.isRequiredBackgroundRefresh())
				requiredBackgroundRefresh = true;
			else
				requiredBackgroundRefresh = false;
			cacheStatus = STATUS_NO_FIND;
			if (howSearch == SEARCH_MEMORY_ONLY) {
				if (memoryRequestList == null) {
					memoryRequestList = new ArrayList<RequestList>();
					// no cache
				} else {
					for (int i = 0, length = memoryRequestList.size(); i < length; i++) {
						RequestList ml = memoryRequestList.get(i);
						if (postAddress.equals(ml.getUrl())
								&& strParams.equals(ml.getParams())) {
							long insertTime = ml.getInsertTime();
							memoryIndex = i;
							result = ml.getResult();
							if (((System.currentTimeMillis() / 1000 - insertTime) < MEMORY_TIME)) {
								// use cache
								cacheStatus = STATUS_NORMAL;
							} else {
								// cache overdue
								cacheStatus = STATUS_OVERDUE;
							}
							break;
						}
					}
				}
				returnResult(activity);
				this.ps = params;
				if (requiredBackgroundRefresh || cacheStatus == STATUS_NO_FIND
						|| cacheStatus == STATUS_OVERDUE) {
					refresh(urlPath, ps);
				}

			} else if (howSearch == SEARCH_DATABASE_ONLY) {
				this.ps = params;
				CaCheHandle mCaCheHandle = new CaCheHandle();
				mCaCheHandle.execute(urlPath, asterisk);
			}

		} else {
			// error
			DocLog.e(TAG, "error:no cache configuration found");
			refresh(urlPath, params);
		}

	}

	private void returnResult(Object activity) {
		if (activity != null) {
			CacheFinishListener act = (CacheFinishListener) activity;
			switch (cacheStatus) {
			case STATUS_NO_FIND:
				DocLog.d(TAG, "no cache");
				break;
			case STATUS_OVERDUE:
				DocLog.d(TAG, "cache overdue");
				try {
					JSONObject job = new JSONObject(result);
					if (backgroundRefresh == this.BACKGROUND_REFRESH) {
						if (job.isNull("errno")) {
							act.onCacheFinish(result, true);
							doBackgroundRefresh = true;
						} else
							doBackgroundRefresh = false;
					}
				} catch (JSONException e) {
					doBackgroundRefresh = false;
					DocLog.e(TAG, "JSONException", e);
				}
				break;
			case STATUS_NORMAL:
				DocLog.d(TAG, "use cache");
				try {
					JSONObject job = new JSONObject(result);
					if (job.isNull("errno"))
						act.onCacheFinish(result, true);
					else
						refresh(url, ps);
				} catch (JSONException e) {
					refresh(url, ps);
					DocLog.e(TAG, "JSONException", e);
				}
				break;
			default:
				DocLog.d(TAG, "error:no cache status");
				try {
					JSONObject job = new JSONObject(result);
					if (job.isNull("errno"))
						act.onCacheFinish(result, true);
					else
						refresh(url, ps);
				} catch (JSONException e) {
					refresh(url, ps);
					DocLog.e(TAG, "JSONException", e);
				}
			}

		}
	}

	private void refresh(String path, HashMap<String, String> params) {
		NetConncet netConncet = new NetConncet(context, path, params) {

			@Override
			protected void onPostExecute(final String result) {
				super.onPostExecute(result);
				try {
					JSONObject jsonObj = new JSONObject(result);
					AppValues appValues = new AppValues(context);
					JSONObject settings = jsonObj.getJSONObject("settings");
					if (!settings.isNull("prefer_logo")) {
						String preferLogoPath = settings
								.getString("prefer_logo");
						appValues.setPreferLogoPath(preferLogoPath);
					}
					if(!settings.isNull("real_name")){
						appValues.setCurrentUserName(settings.getString("real_name"));
					}
				} catch (JSONException e) {
					DocLog.e(TAG, "onPostExecute JSONException", e);
				}
				if (doBackgroundRefresh) {
					if (Cache.this.result.equals(result))
						return;
				}
				Cache.this.result = result;
				CacheFinishListener act = (CacheFinishListener) activity;
				try {
					JSONObject jsonObj = new JSONObject(result);
					if (!jsonObj.isNull("errno")) {
						act.onCacheFinish(result, false);
						return;
					}
				} catch (JSONException e) {
					act.onCacheFinish(result, false);
					return;
				}
				if (cacheStatus == STATUS_NO_FIND) {
					if (howSearch == SEARCH_MEMORY_ONLY) {
						if (memoryRequestList.size() > MEMORY_COUNT) {
							memoryRequestList.clear();
						}
						memoryRequestList.add(new RequestList(postAddress,
								strParams, result,
								System.currentTimeMillis() / 1000));
					} else {
						new Thread() {

							@Override
							public void run() {
								super.run();
								AESEncryptDecrypt decrypt = new AESEncryptDecrypt(
										AppValues.aeskey, context.getCacheDir()
												.getAbsolutePath()
												+ AppValues.secretKey);
								final DataBaseHelper helper = new DataBaseHelper(
										context);
								final SQLiteDatabase wb = helper
										.getWritableDatabase();
								ContentValues values = new ContentValues();
								try {
									values.put(CacheSchema.URL,
											decrypt.encrypt(postAddress));
									values.put(CacheSchema.PARAMS,
											decrypt.encrypt(strParams));
									values.put(CacheSchema.RESULT,
											decrypt.encrypt(result));
									values.put(CacheSchema.CATEGORY, cacheType);
									values.put(CacheSchema.INSERT_TIME,
											System.currentTimeMillis() / 1000);
									wb.insert(CacheSchema.TABLE_NAME, null,
											values);
								} catch (Exception e) {
									DocLog.e(TAG, "Exception", e);
								} finally {
									wb.close();
									helper.close();
								}
								// DocLog.d(TAG,
								// "INSERT INTO cache_schema (url, params, result, category, insert_time)"
								// + " VALUES ( '" + postAddress + "','"
								// + strParams + "','"+ result + "'," +
								// cacheType + ","+ System.currentTimeMillis() /
								// 1000 + " );");
							}

						}.start();
					}
				} else {
					if (howSearch == SEARCH_MEMORY_ONLY) {
						if (memoryRequestList.size() <= memoryIndex) {
							// cache was cleared outside
							memoryRequestList.clear();
							memoryRequestList.add(new RequestList(postAddress,
									strParams, result, System
											.currentTimeMillis() / 1000));
						} else {
							memoryRequestList.set(memoryIndex,
									new RequestList(postAddress, strParams,
											result,
											System.currentTimeMillis() / 1000));
						}
					} else {
						new Thread() {

							@Override
							public void run() {
								super.run();
								AESEncryptDecrypt decrypt = new AESEncryptDecrypt(
										AppValues.aeskey, context.getCacheDir()
												.getAbsolutePath()
												+ AppValues.secretKey);
								final DataBaseHelper helper = new DataBaseHelper(
										context);
								final SQLiteDatabase wb = helper
										.getWritableDatabase();
								ContentValues values = new ContentValues();
								try {
									values.put(CacheSchema.RESULT,
											decrypt.encrypt(result));
									values.put(CacheSchema.INSERT_TIME,
											System.currentTimeMillis() / 1000);
									wb.update(
											CacheSchema.TABLE_NAME,
											values,
											CacheSchema.URL + "=? and "
													+ CacheSchema.PARAMS + "=?",
											new String[] {
													decrypt.encrypt(postAddress),
													decrypt.encrypt(strParams) });
								} catch (Exception e) {
									DocLog.e(TAG, "Exception", e);
								} finally {
									wb.close();
									helper.close();
								}
							}

						}.start();
					}

				}
				act.onCacheFinish(result, false);
			}

		};

		if (method == NetConncet.HTTP_GET) {
			netConncet.setHttpMethod(NetConncet.HTTP_GET);
		}
		netConncet.execute();
	}

	// private void getInvitation(final String path,
	// final HashMap<String, String> params) {
	// NetConncet netConncet = new NetConncet(context,
	// NetConstantValues.INVITATIONS.PATH) {
	//
	// @Override
	// protected void onPostExecute(String result) {
	// try {
	// JSONObject jsonObj = new JSONObject(result);
	// JSONObject jData = jsonObj.getJSONObject("data");
	// JSONArray invitations = jData.getJSONArray("invitations");
	// if (!jData.isNull("call_group_penddings")) {
	// JSONArray call_group_penddings = jData
	// .getJSONArray("call_group_penddings");
	// if (invitations.length() > 0
	// || call_group_penddings.length() > 0) {
	// Intent intent = new Intent(context,
	// InvitationReceivedActivity.class);
	// intent.putExtra("result", jData.toString());
	// context.startActivity(intent);
	// }
	// } else {
	// if (invitations.length() > 0) {
	// Intent intent = new Intent(context,
	// InvitationReceivedActivity.class);
	// intent.putExtra("result", jData.toString());
	// context.startActivity(intent);
	// }
	// }
	// } catch (JSONException e) {
	// DocLog.e("invitation", "JSONException", e);
	// }
	// refresh(path, params);
	// }
	//
	// };
	// netConncet.execute();
	// }

	private class CaCheHandle extends AsyncTask<String, Void, String> {
		@Override
		protected String doInBackground(String... params) {
			AESEncryptDecrypt decrypt = new AESEncryptDecrypt(AppValues.aeskey,
					context.getCacheDir().getAbsolutePath()
							+ AppValues.secretKey);
			final DataBaseHelper helper = new DataBaseHelper(context);
			final SQLiteDatabase db = helper.getReadableDatabase();
			final SQLiteDatabase wdb = helper.getWritableDatabase();
			if (cacheConfiguration.getValues(selection) != null) {
				if (cacheConfiguration.getBackgroundRefresh(selection)) {
					backgroundRefresh = BACKGROUND_REFRESH;
				} else {
					backgroundRefresh = NO_BACKGROUND_REFRESH;
				}
				int expiredTime = cacheConfiguration.getExpiredTime(selection);
				Cursor curCount = db.query(CacheSchema.TABLE_NAME,
						new String[] { "count(*)" }, null, null, null, null,
						null);
				curCount.moveToFirst();
				int count = curCount.getInt(0);
				curCount.close();
				if (count > DATABASE_COUNT) {
					// delete 3% record
					wdb.delete(CacheSchema.TABLE_NAME, CacheSchema.INSERT_TIME
							+ " in (select " + CacheSchema.INSERT_TIME
							+ " from " + CacheSchema.TABLE_NAME + " order by "
							+ CacheSchema.INSERT_TIME + " limit 0,"
							+ DATABASE_COUNT * 0.03 + ");", null);
				}
				try {
					String encryptPostAddress = decrypt.encrypt(postAddress);
					String encryptParams = decrypt.encrypt(strParams);
					Cursor cur = db.query(CacheSchema.TABLE_NAME, new String[] {
							CacheSchema.RESULT, CacheSchema.INSERT_TIME },
							CacheSchema.URL + "=? and " + CacheSchema.PARAMS
									+ "=?", new String[] { encryptPostAddress,
									encryptParams }, null, null, null);
					// DocLog.d(TAG,
					// "SELECT result, insert_time FROM cache_schema WHERE url="
					// + postAddress + " AND params=" + strParams);
					if (cur.getCount() == 1) {
						cur.moveToFirst();
						int insertTime = Integer.parseInt(cur.getString(1));
						try {
							result = decrypt.decrypt(cur.getString(0));
							if (((System.currentTimeMillis() / 1000 - insertTime) < expiredTime)
									|| (expiredTime < 0)) {
								// use cache
								cacheStatus = STATUS_NORMAL;
							} else {
								// cache overdue
								cacheStatus = STATUS_OVERDUE;
							}
						} catch (AESEncryptDecryptException e) {
							cacheStatus = STATUS_NO_FIND;
							// delete bad cache
							wdb.delete(CacheSchema.TABLE_NAME, CacheSchema.URL
									+ "=? and " + CacheSchema.PARAMS + "=?",
									new String[] { encryptPostAddress,
											encryptParams });
							// DocLog.d(TAG,
							// "delete from cache_schema where url=" +
							// postAddress + " and params=" + strParams);
						}
					} else {
						// no cache or error occur
						// delete bad cache
						if (cur.getCount() > 1) {
							wdb.delete(CacheSchema.TABLE_NAME, CacheSchema.URL
									+ "=? and " + CacheSchema.PARAMS + "=?",
									new String[] { encryptPostAddress,
											encryptParams });
						}
						cacheStatus = STATUS_NO_FIND;
					}
					cur.close();
				} catch (Exception e) {
					DocLog.e(TAG, "Exception", e);
				}

			} else {
				// error
				DocLog.e(TAG, "error:no cache configuration in sqlite");
			}
			db.close();
			wdb.close();
			return params[0];// urlPath
		}

		@Override
		protected void onPostExecute(final String urlPath) {
			returnResult(activity);
			if (cacheStatus == STATUS_NO_FIND || cacheStatus == STATUS_OVERDUE) {
				refresh(urlPath, ps);
			}
		}

	}

	public static String pair2String(HashMap<String, String> params) {
		if (params == null)
			return "";
		Iterator<Map.Entry<String, String>> iter = params.entrySet().iterator();
		StringBuffer sb = new StringBuffer("&");
		while (iter.hasNext()) {
			Map.Entry<String, String> entry = iter.next();
			String key = entry.getKey();
			String val = entry.getValue();
			sb.append(key + "=" + val + "&");
		}
		return sb.toString();
	}

	public static void updateRefer(Context ctx, String post, String params,
			String status) {
		AESEncryptDecrypt decrypt = new AESEncryptDecrypt(AppValues.aeskey, ctx
				.getCacheDir().getAbsolutePath() + AppValues.secretKey);
		final DataBaseHelper helper = new DataBaseHelper(ctx);
		final SQLiteDatabase db = helper.getReadableDatabase();

		try {
			Cursor cur = db.query(
					CacheSchema.TABLE_NAME,
					new String[] { CacheSchema.RESULT },
					CacheSchema.URL + "=? and " + CacheSchema.PARAMS + "=?",
					new String[] { decrypt.encrypt(post),
							decrypt.encrypt(params) }, null, null, null);
			DocLog.d("Cache", "select result from cache_schema where url='"
					+ post + "' and params='" + params + "';");
			if (cur.getCount() == 1) {
				cur.moveToFirst();
				try {
					JSONObject jObj = new JSONObject(decrypt.decrypt(cur
							.getString(0)));
					JSONObject jRefer = jObj.getJSONObject("data")
							.getJSONObject("refer");
					jRefer.put("status", status);

					SQLiteDatabase wb = helper.getWritableDatabase();
					ContentValues values = new ContentValues();
					values.put(CacheSchema.RESULT,
							decrypt.encrypt(jObj.toString()));
					values.put(CacheSchema.INSERT_TIME,
							System.currentTimeMillis() / 1000);
					wb.update(
							CacheSchema.TABLE_NAME,
							values,
							CacheSchema.URL + "=? and " + CacheSchema.PARAMS
									+ "=?",
							new String[] { decrypt.encrypt(post),
									decrypt.encrypt(params) });
					DocLog.d(
							"Cache",
							"update cache_schema set result='"
									+ jObj.toString() + "' , insert_time='"
									+ System.currentTimeMillis() / 1000
									+ "' where url='" + post + "' and params='"
									+ params + "';");
					wb.close();
				} catch (JSONException e) {
					DocLog.e("CaChe", "JSONException", e);
				}
			} else {
				DocLog.e("error", "no find");
			}
		} catch (Exception e1) {
			DocLog.e("CaChe", "Exception", e1);
		}
		db.close();
		helper.close();
	}

	public static boolean updateMessageStatus(Context ctx, String post,
			String params, boolean status) {
		boolean success = false;
		AESEncryptDecrypt decrypt = new AESEncryptDecrypt(AppValues.aeskey, ctx
				.getCacheDir().getAbsolutePath() + AppValues.secretKey);
		final DataBaseHelper helper = new DataBaseHelper(ctx);
		final SQLiteDatabase db = helper.getReadableDatabase();

		try {
			Cursor cur = db.query(
					CacheSchema.TABLE_NAME,
					new String[] { CacheSchema.RESULT },
					CacheSchema.URL + "=? and " + CacheSchema.PARAMS + "=?",
					new String[] { decrypt.encrypt(post),
							decrypt.encrypt(params) }, null, null, null);
			DocLog.d("Cache", "select result from cache_schema where url='"
					+ post + "' and params='" + params + "';");
			if (cur.getCount() == 1) {
				cur.moveToFirst();
				try {
					JSONObject jObj = new JSONObject(decrypt.decrypt(cur
							.getString(0)));
					JSONObject jData = jObj.getJSONObject("data");
					jData.put("resolution_flag", status);

					SQLiteDatabase wb = helper.getWritableDatabase();
					ContentValues values = new ContentValues();
					values.put(CacheSchema.RESULT,
							decrypt.encrypt(jObj.toString()));
					values.put(CacheSchema.INSERT_TIME,
							System.currentTimeMillis() / 1000);
					wb.update(
							CacheSchema.TABLE_NAME,
							values,
							CacheSchema.URL + "=? and " + CacheSchema.PARAMS
									+ "=?",
							new String[] { decrypt.encrypt(post),
									decrypt.encrypt(params) });
					DocLog.d(
							"Cache",
							"update cache_schema set result='"
									+ jObj.toString() + "' , insert_time='"
									+ System.currentTimeMillis() / 1000
									+ "' where url='" + post + "' and params='"
									+ params + "';");
					wb.close();
					success = true;
				} catch (JSONException e) {
					DocLog.e("CaChe", "JSONException", e);
					success = false;
				}
			} else {
				StackTraceElement[] stackTraceElements = Thread.currentThread()
						.getStackTrace();
				DocLog.e("error", "no cache found");
				for (int i = 0, len = stackTraceElements.length; i < len; i++) {
					StackTraceElement stackTraceElement = stackTraceElements[i];
					DocLog.e(
							"Cache error",
							"in file " + stackTraceElement.getFileName()
									+ ", class:"
									+ stackTraceElement.getClassName() + "$"
									+ stackTraceElement.getMethodName()
									+ "() in line: "
									+ stackTraceElement.getLineNumber());
				}
				success = false;
			}
		} catch (Exception e1) {
			DocLog.e("CaChe", "Exception", e1);
			success = false;
		}
		db.close();
		helper.close();
		return success;
	}	
	
	public static void resetThreadingMessageList() {
		List<RequestList> tempList = new ArrayList<RequestList>();
		if (memoryRequestList != null && memoryRequestList.size() > 0) {
			for (int i = 0, length = memoryRequestList.size(); i < length; i++) {
				RequestList ml = memoryRequestList.get(i);
				if (!ml.getUrl().contains(
						NetConstantValues.THREADING.PATH)) {
					tempList.add(ml);
				}
			}
		}
		if (memoryRequestList != null)
			memoryRequestList.clear();
		memoryRequestList = tempList;
		tempList = null;

	}

	public static boolean hasReceivedMessageListCache() {
		boolean has = false;
		if (memoryRequestList != null && memoryRequestList.size() > 0) {
			for (int i = 0, length = memoryRequestList.size(); i < length; i++) {
				RequestList ml = memoryRequestList.get(i);
				if (ml.getUrl().contains(
						NetConstantValues.MESSAGING_LIST_RECEIVED.PATH)) {
					has = true;
					break;
				}
			}
		}
		return has;
	}

	public static void resetReceivedMessageList() {
		List<RequestList> tempList = new ArrayList<RequestList>();
		if (memoryRequestList != null && memoryRequestList.size() > 0) {
			for (int i = 0, length = memoryRequestList.size(); i < length; i++) {
				RequestList ml = memoryRequestList.get(i);
				if (!ml.getUrl().contains(
						NetConstantValues.MESSAGING_LIST_RECEIVED.PATH)) {
					tempList.add(ml);
				}
			}
		}
		if (memoryRequestList != null)
			memoryRequestList.clear();
		memoryRequestList = tempList;
		tempList = null;

	}

	public static boolean hasSentMessageListCache() {
		boolean has = false;
		if (memoryRequestList != null && memoryRequestList.size() > 0) {
			for (int i = 0, length = memoryRequestList.size(); i < length; i++) {
				RequestList ml = memoryRequestList.get(i);
				if (ml.getUrl().contains(
						NetConstantValues.MESSAGING_LIST_SENT.PATH)) {
					has = true;
					break;
				}
			}
		}
		return has;
	}

	public static void resetSentMessageList() {
		List<RequestList> tempList = new ArrayList<RequestList>();
		if (memoryRequestList != null && memoryRequestList.size() > 0) {
			for (int i = 0, length = memoryRequestList.size(); i < length; i++) {
				RequestList ml = memoryRequestList.get(i);
				if (!ml.getUrl().contains(
						NetConstantValues.MESSAGING_LIST_SENT.PATH)) {
					tempList.add(ml);
				}
			}
		}
		memoryRequestList.clear();
		memoryRequestList = tempList;
		tempList = null;
	}

	public static boolean hasThtreaingList() {
		boolean has = false;
		if (memoryRequestList != null && memoryRequestList.size() > 0) {
			for (int i = 0, length = memoryRequestList.size(); i < length; i++) {
				RequestList ml = memoryRequestList.get(i);
				if (ml.getUrl().contains(NetConstantValues.THREADING.PATH)) {
					has = true;
					break;
				}
			}
		}
		return has;
	}

	public static void resetThtreaingList() {
		List<RequestList> tempList = new ArrayList<RequestList>();
		if (memoryRequestList != null && memoryRequestList.size() > 0) {
			for (int i = 0, length = memoryRequestList.size(); i < length; i++) {
				RequestList ml = memoryRequestList.get(i);
				if (!ml.getUrl().contains(NetConstantValues.THREADING.PATH)) {
					tempList.add(ml);
				}
			}
		}
		memoryRequestList.clear();
		memoryRequestList = tempList;
		tempList = null;
	}

	public static void resetFollowupTaskList() {
		List<RequestList> tempList = new ArrayList<RequestList>();
		if (memoryRequestList != null && memoryRequestList.size() > 0) {
			for (int i = 0, length = memoryRequestList.size(); i < length; i++) {
				RequestList ml = memoryRequestList.get(i);
				if (!ml.getUrl()
						.contains(NetConstantValues.FOLLOWUPS_LIST.PATH)) {
					tempList.add(ml);
				}
			}
		}
		memoryRequestList.clear();
		memoryRequestList = tempList;
		tempList = null;
	}

	public static void resetMemoryCache() {
		if (memoryRequestList != null) {
			memoryRequestList.clear();
		}
	}

	public static void cleanListCache(String category, String url,
			Context context) {
		// TODO Auto-generated method stub
		final String CATEGORY = category;
		final String URL = url;
		final DataBaseHelper helper = new DataBaseHelper(context);
		final SQLiteDatabase db = helper.getWritableDatabase();
		final Context ctx = context;
		final AESEncryptDecrypt decrypt = new AESEncryptDecrypt(
				AppValues.aeskey, context.getCacheDir().getAbsolutePath()
						+ AppValues.secretKey);

		new Thread() {

			@Override
			public void run() {
				String decryptUrl;
				try {
					AppValues appValues = new AppValues(ctx);
					decryptUrl = decrypt.encrypt(appValues.getServerURL()
							+ NetConstantValues.APP_URL + URL);
					db.delete(CacheSchema.TABLE_NAME, "category = ?" + " and "
							+ CacheSchema.URL + " = ?", new String[] {
							CATEGORY, decryptUrl });
					DocLog.d("cache class", "delete cache" + URL);
				} catch (AESEncryptDecryptException e) {
					db.delete(CacheSchema.TABLE_NAME, null, null);
					DocLog.e("cache class", "AESEncryptDecryptException", e);
				} finally {
					db.close();
					helper.close();
				}
			}

		}.start();

	}

	static public class RequestList {
		private String url, params, result;
		long insertTime;

		public RequestList() {

		}

		public RequestList(String url, String params, String result,
				long insertTime) {
			this.url = url;
			this.params = params;
			this.result = result;
			this.insertTime = insertTime;
		}

		public String getUrl() {
			return url;
		}

		public void setUrl(String url) {
			this.url = url;
		}

		public String getParams() {
			return params;
		}

		public void setParams(String params) {
			this.params = params;
		}

		public String getResult() {
			return result;
		}

		public void setResult(String result) {
			this.result = result;
		}

		public long getInsertTime() {
			return insertTime;
		}

		public void setInsertTime(long insertTime) {
			this.insertTime = insertTime;
		}

	}

	public static interface CacheSchema {
		static String TABLE_NAME = "cache_schema";
		static String URL = "url";
		static String PARAMS = "params";
		static String RESULT = "result";
		static String INSERT_TIME = "insert_time";
		static String CATEGORY = "category";
	}

}
