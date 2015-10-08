package com.doctorcom.physician.utils.cache;

import java.io.File;

import android.app.IntentService;
import android.content.Intent;
import android.database.sqlite.SQLiteDatabase;
import android.support.v4.content.LocalBroadcastManager;

import com.doctorcom.physician.utils.DocLog;
import com.doctorcom.physician.utils.FileUtil;
import com.doctorcom.physician.utils.cache.Cache.CacheSchema;

public class CacheService extends IntentService {
	
	private final String TAG = "CacheService";
	public static final String CLEAN_CACHE_ACTION = "CacheCleanAction"; 
	public static final String CACHE_SERVICE = "com.doctorcom.util.cache";
	public static final int CACHE_CLEAN = 0;
	public static final int UPDATE_USER_LIST = 1;
	public static final int UPDATE_CALL_BACK_MESSAGE = 2;
	public static final int UPDATE_PRACTICE = 3;
	public static final int UPDATE_ORG = 4;

	public CacheService() {
		super("CacheService");
	}

	@Override
	protected void onHandleIntent(Intent intent) {
		DataBaseHelper helper = new DataBaseHelper(this);
		SQLiteDatabase db = helper.getWritableDatabase();
		LocalBroadcastManager broadcastManager = LocalBroadcastManager.getInstance(this);
		switch(intent.getIntExtra("cmd", -1)) {
		case CACHE_CLEAN:
			db.delete(CacheSchema.TABLE_NAME, null, null);
			db.close();
			helper.close();
			Cache.resetMemoryCache();
			String appPath = FileUtil.getAppPath(this);
			if (appPath != null) {
				FileUtil.deleteFile(new File(appPath));
			}
			DocLog.d(TAG, "Cache Cleaned");
			broadcastManager.sendBroadcast(new Intent(CLEAN_CACHE_ACTION));
			//broadcastManager.sendBroadcast(new Intent("refreshAction"));
			break;
		case UPDATE_USER_LIST:
			db.delete(CacheSchema.TABLE_NAME, "category = 1", null);
			db.close();
			helper.close();
			/*Intent i = new Intent("refreshAction");
			i.putExtra("cmd", 1);
			broadcastManager.sendBroadcast(i);*/
			DocLog.d(TAG, "UPDATE_USER_LIST");
			break;
		case UPDATE_CALL_BACK_MESSAGE:
			db.delete(CacheSchema.TABLE_NAME, "category = 4", null);
			db.close();
			helper.close();
			DocLog.d(TAG, "UPDATE_CALL_BACK_MESSAGE");
			/*Intent inet = new Intent("refreshAction");
			inet.putExtra("cmd", 1);
			broadcastManager.sendBroadcast(inet);*/
			DocLog.d(TAG, "UPDATE_USER_LIST");
			break;
		case UPDATE_PRACTICE:
			db.delete(CacheSchema.TABLE_NAME, "category = 7", null);
			db.close();
			helper.close();
			DocLog.d(TAG, "delete practice");
			break;
		case UPDATE_ORG:
			db.delete(CacheSchema.TABLE_NAME, "category = 10", null);
			db.close();
			helper.close();
			DocLog.d(TAG, "delete org");
			break;
		}
	}

}
