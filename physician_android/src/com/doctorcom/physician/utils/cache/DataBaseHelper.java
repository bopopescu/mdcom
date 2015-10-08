package com.doctorcom.physician.utils.cache;


import android.content.Context;
import android.database.sqlite.SQLiteDatabase;
import android.database.sqlite.SQLiteOpenHelper;

import com.doctorcom.physician.utils.DocLog;
import com.doctorcom.physician.utils.cache.Cache.CacheSchema;

public class DataBaseHelper extends SQLiteOpenHelper {
	private final String TAG = "DataBaseHelper";
	private static final String DATABASE_NAME = "CacheDB";
	private static final int DATABASE_VERSION = 1;
	
	public DataBaseHelper(Context context) {
		super(context, DATABASE_NAME, null, DATABASE_VERSION);
	}

	@Override
	public void onCreate(SQLiteDatabase db) {
		db.beginTransaction();
		try {
			String sqlSchema = "create table " + CacheSchema.TABLE_NAME + " ("
					+ CacheSchema.URL + " text not null, "
					+ CacheSchema.PARAMS + " text, "
					+ CacheSchema.RESULT + " text not null, "
					+ CacheSchema.CATEGORY + " integer, "
					+ CacheSchema.INSERT_TIME + " text not null );";
			DocLog.d(TAG, "sql -> " + sqlSchema);
			db.execSQL(sqlSchema);
			db.setTransactionSuccessful();
		} finally {
			db.endTransaction();
		}
	}

	@Override
	public void onUpgrade(SQLiteDatabase db, int oldVersion, int newVersion) {
		db.beginTransaction();
		try {
			db.execSQL("drop table if exists " + CacheSchema.TABLE_NAME);
			onCreate(db);
			db.setTransactionSuccessful();
		} finally {
			db.endTransaction();
		}
		DocLog.d(TAG, "onUpgrade" + newVersion);
		
	}
	
}