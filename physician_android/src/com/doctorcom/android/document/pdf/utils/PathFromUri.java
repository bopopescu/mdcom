package com.doctorcom.android.document.pdf.utils;

import java.util.Locale;

import android.content.ContentResolver;
import android.database.Cursor;
import android.net.Uri;

public class PathFromUri
{
    public static String retrieve(ContentResolver resolver, Uri uri)
    {
    	String errorInfo;
		if (Locale.getDefault().getLanguage().contains("de")) {
			errorInfo = "Kann angegebenen Pfad nicht finden: ";
		} else {
			errorInfo = "Can't retrieve path from uri: ";
		}
        if (uri.getScheme().equals("file"))
        {
            return uri.getPath();
        }
        final Cursor cursor = resolver.query(uri, new String[]{"_data"}, null, null, null);
        if (cursor.moveToFirst())
        {
            return cursor.getString(0);
        }
        throw new RuntimeException(errorInfo + uri.toString());
    }
}
