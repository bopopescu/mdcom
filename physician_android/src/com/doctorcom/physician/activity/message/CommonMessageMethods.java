package com.doctorcom.physician.activity.message;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;

import android.app.ProgressDialog;
import android.content.Context;
import android.content.res.AssetManager;
import android.text.Html;
import android.text.Spannable;
import android.text.SpannableString;
import android.text.method.LinkMovementMethod;
import android.util.SparseArray;
import android.view.View;
import android.widget.Button;
import android.widget.TextView;
import android.widget.Toast;

import com.doctorcom.android.R;
import com.doctorcom.physician.activity.message.MessageDetailActivity.MessageDetailFragment.MyURLSpan;
import com.doctorcom.physician.net.NetConstantValues;
import com.doctorcom.physician.net.http.NetConncet;
import com.doctorcom.physician.utils.CallBack;
import com.doctorcom.physician.utils.JsonErrorProcess;
import com.doctorcom.physician.utils.Utils;

public class CommonMessageMethods {

	public interface DeleteMessageListener {
		public void onSuccessDelete();
	}

	public static void deleteMessage(String messageId, final Context context,
			final DeleteMessageListener dml) {
		final ProgressDialog progress = ProgressDialog.show(context, "",
				context.getString(R.string.message_deleting));
		final NetConncet httpConn = new NetConncet(context,
				NetConstantValues.MESSAGE_DELETE.getPath(messageId)) {

			@Override
			protected void onPostExecute(String result) {
				super.onPostExecute(result);
				progress.dismiss();
				if (JsonErrorProcess.checkJsonError(result, context)) {
					Toast.makeText(context, R.string.delete_successfully,
							Toast.LENGTH_LONG).show();
					dml.onSuccessDelete();
				}
			}
		};
		httpConn.execute();
	}

	public static void setLinkBody(TextView contactTextView, Context context,
			String body) {
		final SpannableString ss = new SpannableString(body);
		SparseArray<String> sa = Utils.getNumbers(ss.toString());
		for (int i = 0, len = sa.size(); i < len; i++) {
			int k = sa.keyAt(i);
			String v = sa.get(k);
			MyURLSpan myURLSpan = new MyURLSpan(context, v);
			ss.setSpan(myURLSpan, k, k + v.length(),
					Spannable.SPAN_EXCLUSIVE_EXCLUSIVE);
		}
		contactTextView.setText(ss);
		contactTextView.setMovementMethod(LinkMovementMethod
				.getInstance());
		contactTextView.setFocusable(false);
	}

	public static void setLinkString(TextView targetTextView, String text) {
		targetTextView.setText(Html.fromHtml("<font color='white'><u>" + text
				+ "</u></font>"));
	}
	
	public static void setCallBackButton(Button callbackButton, final Context context, final String callBackNumber, boolean callBackAvailable){
		if (callBackAvailable
				&& callBackNumber != null
				&& callBackNumber.length() > 0) {
			callbackButton
					.setBackgroundResource(R.drawable.button_call);
			callbackButton
					.setOnClickListener(new View.OnClickListener() {

						@Override
						public void onClick(View v) {
							CallBack callBack = new CallBack(
									context);
							callBack.call(
									NetConstantValues.CALL_ARBITRARY.PATH,
									Utils.getNumberOfPhone(callBackNumber));

						}
					});
		} else {
			callbackButton
					.setBackgroundResource(R.drawable.button_call_disable);
		}

	}

	// imitational codes
	// **************************************************************
	public static String getJsonStrMessageDetail(boolean isRefer,
			Context context) {
		AssetManager am = context.getResources().getAssets();
		InputStream is;
		String result = "";
		try {
			if (isRefer)
				is = am.open("refer.txt");
			else
				is = am.open("normal_message.txt");
			BufferedReader br = new BufferedReader(new InputStreamReader(is));
			String line = "";
			while ((line = br.readLine()) != null) {
				result += line;
			}
			br.close();
			is.close();
			// am.close();
		} catch (IOException e) {

		}
		return result;

	}
	// **************************************************************

}
