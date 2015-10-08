package com.doctorcom.physician.utils;

import android.app.AlertDialog;
import android.content.Context;
import android.view.LayoutInflater;
import android.view.View;
import android.widget.EditText;
import android.widget.TextView;

import com.doctorcom.android.R;

public class Connection implements View.OnClickListener{

	public Context context;
	public int method, userId;
	private String path = "";
	public static final int CALL = 1, PAGE = 2;
	public Connection(Context context, int method, int id, String path) {
		this.context = context;
		this.method = method;
		userId = id;
		this.path = path;
	}
	
	@Override
	public void onClick(View v) {
		switch (method) {
		case CALL:
			CallBack callBack = new CallBack(context);
			callBack.call(path, null);
			break;
		case PAGE:
            LayoutInflater factory = LayoutInflater.from(context);
            final View textEntryView = factory.inflate(R.layout.alert_dialog_text_entry, null);
            ((TextView) textEntryView.findViewById(R.id.tvTitle)).setText(R.string.leave_your_number_here);
            AlertDialog.Builder builder = new AlertDialog.Builder(context);
			builder.setTitle(R.string.page_title).setView(textEntryView)
					.setPositiveButton(R.string.ok,
							new android.content.DialogInterface.OnClickListener() {
								public void onClick(android.content.DialogInterface dialog, int id) {
									CallBack callBack = new CallBack(context);
									callBack.userPage(String.valueOf(userId), ((EditText)textEntryView.findViewById(R.id.etReason)).getText().toString());
								}
							})
					.setNegativeButton(R.string.cancel,
							new android.content.DialogInterface.OnClickListener() {
								public void onClick(android.content.DialogInterface dialog,
										int id) {
									dialog.cancel();
								}
							});
			AlertDialog alert = builder.create();
			alert.show();
			break;
		}
		
	}

}
