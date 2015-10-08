package com.doctorcom.physician.utils;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.IOException;

import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import android.os.Environment;

public class FileUtil {
	private static final String TAG = "FileUtil";

	public static boolean isSdcardAvailable() {
		if(Environment.getExternalStorageState().equals(Environment.MEDIA_MOUNTED)){
			return true;
		} else {
			return false;
		}

	}
	
	public static String getAppPath(Context context) {
		if (!isSdcardAvailable()) return null;
		String dir = null;
		try {
			dir = context.getExternalFilesDir(null).getAbsolutePath();
		} catch (Exception e) {
			DocLog.e(TAG, "Exception", e);
			return null;
		}
		return dir;
	}
	
	public static void deleteFile(File file){
		try{
			if(file.exists()){
				if(file.isDirectory()){
					File[] fileList = file.listFiles();
					if(fileList != null){
						for (File subFile : fileList) {
							deleteFile(subFile);
						}
					}
					file.delete();
				} else if(file.isFile()){
					file.delete();
				}
			}
		}catch(Exception ex){
			DocLog.e(TAG, "deleteFile Exception",ex);
		}
	}

	public static Intent getOpenFileIntent(String strFile) {
		File file = new File(strFile);
		return getOpenFileIntent(file);
	}

	public static Intent getOpenFileIntent(File file) {
		Intent intent = new Intent();
		intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
		intent.setAction(android.content.Intent.ACTION_VIEW);
		/* getMIMEType() */
		String type = getMIMEType(file);
		intent.setDataAndType(Uri.fromFile(file), type);
		return intent;
	}
	public static String getMIMEType(String f) {
		return getMIMEType(new File(f));
	}
	public static String getMIMEType(File f) {

		String type = "";
		String fName = f.getName();
		/* get file ext */
		String end = fName.substring(fName.lastIndexOf(".") + 1, fName.length());

		/* MimeType */
		if (end.equalsIgnoreCase("m4a") || end.equalsIgnoreCase("mp3") || end.equalsIgnoreCase("mid")
				|| end.equalsIgnoreCase("xmf") || end.equalsIgnoreCase("ogg") || end.equalsIgnoreCase("wav")) {
			type = "audio/" + "*";
		} else if (end.equalsIgnoreCase("3gp") || end.equalsIgnoreCase("mp4")) {
			type = "video/" + "*";
		} else if (end.equalsIgnoreCase("jpg") || end.equalsIgnoreCase("gif") || end.equalsIgnoreCase("png")
				|| end.equalsIgnoreCase("jpeg") || end.equalsIgnoreCase("bmp")) {
			type = "image/" + "*";
		} else if (end.equalsIgnoreCase("apk")) {
			/* android.permission.INSTALL_PACKAGES */
			type = "application/vnd.android.package-archive";
		} else if (end.equalsIgnoreCase("dcm") || end.equalsIgnoreCase("dicom")) {
			type = "application/dicom";
		} else if (end.equalsIgnoreCase("pdf")) {
			type = "applications/vnd.pdf ";
		} else if (end.equalsIgnoreCase("rar")) {
			type = "application/x-rar-compressed";
		} else if (end.equalsIgnoreCase("zip")) {
			type = "application/zip";
		} else if (end.equalsIgnoreCase("doc") || end.equalsIgnoreCase("dot")) {
			type = "application/msword";
		} else if (end.equalsIgnoreCase("docx")) {
			type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document";
		} else if (end.equalsIgnoreCase("xls") || end.equalsIgnoreCase("xlt")) {
			type = "application/vnd.ms-excel";
		} else if (end.equalsIgnoreCase("xlsx")) {
			type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet";
		} else if (end.equalsIgnoreCase("ppt") || end.equalsIgnoreCase("pot") || end.equalsIgnoreCase("pps")) {
			type = "application/vnd.ms-powerpoint";
		} else if (end.equalsIgnoreCase("pptx")) {
			type = "application/vnd.openxmlformats-officedocument.presentationml.presentation";
		}else if (end.equalsIgnoreCase("txt") || end.equalsIgnoreCase("json")) {
			type = "text/plain";
		} else if (end.equalsIgnoreCase("htm") || end.equalsIgnoreCase("html")) {
			type = "text/html ";
		} else {
			type = "*/*";
		}
		return type;
	}
	
	 public static String getFileSize(double size) {
		 String strSize = "";
		 if (size > 1024 * 1024 * 1024) {
			 String temp = String.valueOf(size /1024  / 1024 / 1024);
			 strSize =temp.substring(0, temp.indexOf(".") + 2) + "GB";
			 if (!temp.contains(".")) {
				 temp = temp + ".0";
			 }
		 } else if (size > 1024 * 1024) {
			 String temp = String.valueOf(size /1024  / 1024);
			 if (!temp.contains(".")) {
				 temp = temp + ".0";
			 }
			 strSize =temp.substring(0, temp.indexOf(".") + 2) + "MB";
		 } else if (size > 1024) {
			 String temp = String.valueOf(size / 1024);
			 if (!temp.contains(".")) {
				 temp = temp + ".0";
			 }
			 strSize =temp.substring(0, temp.indexOf(".") + 2) + "KB";
		 } else {
			 strSize = size + "B";
		 }
		 return strSize;
		 
	 }
	 public static int getFileSize(String file) {
			return getFileSize(new File(file));
	 }
	 public static int getFileSize(File file) {
			FileInputStream fis = null;
			int fileLen = 0;
			try {
				fis = new FileInputStream(file);
				//get the file size
				fileLen = fis.available();
				DocLog.i(TAG, "the photo size is " + fileLen / 1000 + "Kb");
			} catch (FileNotFoundException e1) {				
				DocLog.e(TAG, "FileNotFoundException", e1);
			} catch (IOException e) {
				DocLog.e(TAG, "IOException", e);
			}
			return fileLen;
			
	 }

	 public static void releaseAttachment(String parent) {
		 releaseAttachment(new File(parent));
	 }
	 public static void releaseAttachment(File parent) {
		int fileSize = 0;
		int index = 0;
		// TODO
//		File parent = new File("/sdcard/doctorcom/");
		if (parent.isDirectory()) {
			File[] fileList = parent.listFiles();
			if (fileList != null && fileList.length > 0) {
				for (int i = 0, length = fileList.length; i < length; i++) {
					if (fileList[i].isFile()) {
						fileSize += getFileSize(fileList[i]);
					}
				}
				long filelastModifiedTime = getFileSize(fileList[0]);
				for (int i = 1, length = fileList.length; i < length; i++) {
					if (fileList[i].isFile()) {
						if (filelastModifiedTime > fileList[i].lastModified()) {
							filelastModifiedTime = fileList[i].lastModified();
							index = i;
						}
					}
				}
			}
			if (fileSize > 128 * 1024 * 1024) {
				fileList[index].delete();
				releaseAttachment(parent);
			}
		}
	 }
	 
}
