package com.doctorcom.physician.activity.task;

import java.util.Calendar;
import java.util.TimeZone;

import com.doctorcom.physician.AppValues;

import android.app.DatePickerDialog;
import android.app.Dialog;
import android.os.Bundle;
import android.support.v4.app.DialogFragment;
import android.widget.DatePicker;

public class DatePickerFragment extends DialogFragment  implements DatePickerDialog.OnDateSetListener {
	
	public interface DateSelectedListener {
		void onDateSelectedFinish(long timestamp);
	}

	private long timestamp;
	private AppValues appValues;
	
	@Override
	public void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
		Bundle bundle = getArguments();
		timestamp = bundle.getLong("timestamp");
		appValues = new AppValues(getActivity());
	}

	@Override
	public Dialog onCreateDialog(Bundle savedInstanceState) {
        int year, month, day;
        Calendar mCalendar = Calendar.getInstance(TimeZone.getTimeZone(appValues.getTimezone()));
        mCalendar.setTimeInMillis(timestamp);
		year = mCalendar.get(Calendar.YEAR);
		month = mCalendar.get(Calendar.MONTH);
		day = mCalendar.get(Calendar.DAY_OF_MONTH);
        return new DatePickerDialog(getActivity(), this, year, month, day);
	}

	@Override
	public void onDateSet(DatePicker view, int year, int monthOfYear, int dayOfMonth) {
		Calendar mCalendar = Calendar.getInstance(TimeZone.getTimeZone(appValues.getTimezone()));
		mCalendar.set(year, monthOfYear, dayOfMonth, 23, 59, 59);
		timestamp = mCalendar.getTimeInMillis();
		DateSelectedListener dateSelected = (DateSelectedListener) getActivity();
		dateSelected.onDateSelectedFinish(timestamp);
		
	}
}
