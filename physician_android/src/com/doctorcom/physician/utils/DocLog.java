package com.doctorcom.physician.utils;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.io.PrintWriter;
import java.io.StringWriter;
import java.io.Writer;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

import android.os.Environment;
import android.util.Log;

public final class DocLog {
	private static final boolean DEBUG_ENABLE = true;
	private static final boolean ERROR_ENABLE = true;
	private static final boolean INFO_ENABLE  = true;
	private static boolean mLogFileWritable = false;
	private static boolean mLogShowable = false;
	private static final String FILE_NAME = "debuglog.info";
	private static final String LOG_FILE_PATH = Environment.getExternalStorageDirectory().getPath() + "doctorcom/log/";

	private static final int DOCLOG_SUCCESS = 1;
	
	public static void setmLogFileWritable(boolean writable){
		mLogFileWritable = writable;
	}
	
	public static void setmLogShowable(boolean showable){
		mLogShowable = showable;
	}
	
	public static boolean getmLogFileWritable() {
		return mLogFileWritable;
	}
	
	public static boolean getmLogShowable() {
		return mLogShowable;
	}
	//debug
	public static int d(String tag, String msg) {
		if(mLogFileWritable){
			writeLogFile(msg);
		}
		if (DEBUG_ENABLE && mLogShowable) {
			return Log.d(tag, msg);
		} else {
			return DOCLOG_SUCCESS;
		}
	}

	public static int d(String tag, String msg, Throwable tr) {
		if(mLogFileWritable){
			msg = getCrashInfo(tr);
			writeLogFile(msg);
		}
		if (DEBUG_ENABLE &&
				mLogShowable) {
			return Log.d(tag, msg, tr);
		} else {
			return DOCLOG_SUCCESS;
		}
	}

	//info
	public static int i(String tag, String msg) {
		if(mLogFileWritable){
			writeLogFile(msg);
		}
		if (INFO_ENABLE && mLogShowable) {
			return Log.i(tag, msg);
		} else {
			return DOCLOG_SUCCESS;
		}
	}
	
	public static int i(String tag, String msg, Throwable tr) {
		if(mLogFileWritable){
			msg = getCrashInfo(tr);
			writeLogFile(msg);
		}
		if (INFO_ENABLE && mLogShowable) {
			return Log.i(tag, msg, tr);
		} else {
			return DOCLOG_SUCCESS;
		}
	}
	
	//error
	public static int e(String tag, String msg) {
		if(mLogFileWritable){
			writeLogFile(msg);
		}
		if (ERROR_ENABLE && mLogShowable) {
			return Log.e(tag, msg);
		} else {
			return DOCLOG_SUCCESS;
		}
	}

	public static int e(String tag, String msg, Throwable tr) {
		if(mLogFileWritable){
			msg = getCrashInfo(tr);
			writeLogFile(msg);
		}
		if (ERROR_ENABLE && mLogShowable) {
			return Log.e(tag, msg, tr);
		} else {
			return DOCLOG_SUCCESS;
		}
	}
	
	private static String getCrashInfo(Throwable ex){
		Writer info = new StringWriter();
		PrintWriter printWriter = new PrintWriter(info);
		ex.printStackTrace(printWriter);
		Throwable cause = ex.getCause();
		while (cause != null) {
			cause.printStackTrace(printWriter);
			cause = cause.getCause();
		}
		String result = info.toString();
		printWriter.close();
		return result;
	}
	
	private static void writeLogFile(String logStr){
		try {
			if(Environment.getExternalStorageState().equals(Environment.MEDIA_MOUNTED)){
				File pLogFile = new File(LOG_FILE_PATH);
		        if(!pLogFile.exists()){
		        	     pLogFile.mkdirs();
		        }
		        File logFile = new File(LOG_FILE_PATH+FILE_NAME);
		        if(!logFile.exists()){
		    	        logFile.createNewFile();
		        }
		        FileWriter writer = new FileWriter(logFile,true);
		        logStr = getCurrentDate() +"\n" + logStr;
		        writer.write(logStr);
				writer.flush();
				writer.close();
//		            judgeLogFile();
			}
		} catch (IOException e) {
			e.printStackTrace();
		}
	}
	
	private static String getCurrentDate(){
		Date date = new Date();
		SimpleDateFormat format = new SimpleDateFormat("yyyyMMddHHmmss", Locale.US);
		String strDate = format.format(date);
		return strDate;
	}
}
