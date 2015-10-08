package com.doctorcom.physician.utils;

import org.json.JSONException;
import org.json.JSONObject;

import android.content.Context;
import android.widget.Toast;

import com.doctorcom.android.R;

public class JsonErrorProcess {

	public static boolean checkJsonError(String result, Context context) {
		boolean returnValue = true;
		try {
			JSONObject jsonObj = new JSONObject(result);
			if (!jsonObj.isNull("errno")) {
				Toast.makeText(context, jsonObj.getString("descr"), Toast.LENGTH_LONG).show();
				returnValue = false;
			}
		} catch (JSONException e) {
			returnValue = false;
			Toast.makeText(context, R.string.error_occur, Toast.LENGTH_SHORT).show();
		}
		return returnValue;
	}

}
