package com.doctorcom.physician.activity.doctor;

import com.doctorcom.android.R;

import android.content.Context;

public class CommonDoctorMethods {
	public static String getTotalCountStr(int count, Context context){
		String targetStr = context.getString(R.string.totally_find) +" " +count + " " +context.getString(R.string.users);
		return targetStr;
		
	}

}
