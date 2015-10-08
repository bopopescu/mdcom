package com.doctorcom.physician.activity.invitation;

import java.util.HashMap;

import org.json.JSONException;
import org.json.JSONObject;

import android.app.Activity;
import android.app.ProgressDialog;
import android.content.Intent;
import android.os.Bundle;
import android.text.Html;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.TextView;
import android.widget.Toast;

import com.doctorcom.android.R;
import com.doctorcom.physician.net.NetConstantValues;
import com.doctorcom.physician.net.http.NetConncet;
import com.doctorcom.physician.utils.DocLog;
import com.doctorcom.physician.utils.JsonErrorProcess;
import com.doctorcom.physician.utils.Utils;
import com.doctorcom.physician.utils.cache.Cache;

public class InvitationNewActivity extends Activity {

	//invite type
	public static final String INVITE_TO_DOCTORCOM = "1";
	public static final String INVITE_TO_PRACTICE = "2";
	//invite user type
	public static final String INVITE_AS_PROVIDER = "1";
	public static final String INVITE_AS_STAFF = "101";
	
	private final String TAG = "InvitationNewActivity";
	private EditText recipientEditText, contentEditText;
	private InvitationItem item;
	@Override
	protected void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
		setContentView(R.layout.activity_invitation_new);
		
		Intent intent = getIntent();
		recipientEditText = (EditText) findViewById(R.id.etRecipient);
		contentEditText = (EditText) findViewById(R.id.etContent);
		TextView titleTextView = (TextView) findViewById(R.id.tvTitle);
		item = (InvitationItem) intent.getSerializableExtra("item");
		Button sendButton = (Button) findViewById(R.id.btSend);
		if (item == null) {
			titleTextView.setText(R.string.new_invitation);
			sendButton.setText(R.string.send);
			sendButton.setOnClickListener(new InvitationSend(intent.getIntExtra("type", -1)));
		} else {
			titleTextView.setText(R.string.resend_invitation);
			recipientEditText.setText(item.getRecipient());
			recipientEditText.setEnabled(false);
			contentEditText.requestFocus();
			sendButton.setText(R.string.resend);
			sendButton.setOnClickListener(new InvitationResend());
		}
		Button closeButton = (Button) findViewById(R.id.btClose);
		closeButton.setOnClickListener(new View.OnClickListener() {
			
			@Override
			public void onClick(View v) {
				closeActivity();
				
			}
		});
	}

	class InvitationSend implements View.OnClickListener {

		private String inviteType, inviteUserType;;
		public InvitationSend(int type) {
			switch(type){
			case 0:{
				inviteType = INVITE_TO_PRACTICE;
				inviteUserType = INVITE_AS_PROVIDER;
				break;
			}
			case 1:{
				inviteType = INVITE_TO_PRACTICE;
				inviteUserType = INVITE_AS_STAFF;
				break;
			}
			case 2:{
				inviteType = INVITE_TO_DOCTORCOM;
				inviteUserType = INVITE_AS_PROVIDER;
				break;
			}
			default :{
				inviteType = INVITE_TO_DOCTORCOM;
				inviteUserType = INVITE_AS_PROVIDER;
			}
			}

		}
		
		@Override
		public void onClick(View v) {
			String recipient = recipientEditText.getText().toString();
			if (Utils.validateEmail(recipient)) {
				final ProgressDialog progress = ProgressDialog.show(InvitationNewActivity.this, "", getString(R.string.process_text));
				HashMap<String, String> params = new HashMap<String, String>();
				params.put(NetConstantValues.NEW_INVITATION.PARAM_EMAIL, recipient);
				params.put(NetConstantValues.NEW_INVITATION.PARAM_NOTE, contentEditText.getText().toString());
				params.put(NetConstantValues.NEW_INVITATION.PARAM_INVITE_TYPE, inviteType);
				params.put(NetConstantValues.NEW_INVITATION.PARAM_INVITE_USER_TYPE, inviteUserType);
				NetConncet netConncet = new NetConncet(InvitationNewActivity.this, NetConstantValues.NEW_INVITATION.PATH, params) {

					@Override
					protected void onPostExecute(String result) {
						super.onPostExecute(result);
						progress.dismiss();
						if (JsonErrorProcess.checkJsonError(result, InvitationNewActivity.this)) {
							Toast.makeText(InvitationNewActivity.this,R.string.saved_successfully,Toast.LENGTH_SHORT).show();
							Cache.cleanListCache(String.valueOf(Cache.CACHE_INVITATION_LIST), NetConstantValues.GET_OUTSTANDING_INVITATIONS.PATH, InvitationNewActivity.this.getApplicationContext());
							finish();
						}
					}
					
				};
				netConncet.execute();
			} else {
				recipientEditText.setError(Html.fromHtml(getString(R.string.field_invalid)));
				recipientEditText.requestFocus();
				recipientEditText.selectAll();
			}
		}
		
	}
	
	class InvitationResend implements View.OnClickListener {

		@Override
		public void onClick(View v) {
			final ProgressDialog progress = ProgressDialog.show(InvitationNewActivity.this, "", getString(R.string.process_text));
			final String content = contentEditText.getText().toString();
			HashMap<String, String> params = new HashMap<String, String>();
			params.put(NetConstantValues.NEW_INVITATION.PARAM_NOTE, content);
			NetConncet netConncet = new NetConncet(InvitationNewActivity.this, NetConstantValues.RESEND_INVITATION.getPath(String.valueOf(item.getId())), params) {

				@Override
				protected void onPostExecute(String result) {
					super.onPostExecute(result);
					progress.dismiss();
					try {
						JSONObject jsonObj = new JSONObject(result);
						if (jsonObj.isNull("errno")) {
							Toast.makeText(InvitationNewActivity.this,R.string.saved_successfully,Toast.LENGTH_SHORT).show();
							Cache.cleanListCache(String.valueOf(Cache.CACHE_INVITATION_LIST), NetConstantValues.GET_OUTSTANDING_INVITATIONS.PATH, InvitationNewActivity.this.getApplicationContext());
							long due = jsonObj.getJSONObject("data").getLong("request_timestamp");
							Intent intent = new Intent();
							item.setDueTimestamp(due * 1000);
							item.setSummary(content);
							intent.putExtra("invitation", item);
							setResult(RESULT_OK, intent);
							DocLog.d(TAG, "resend " + item.getId());
							finish();
						} else {
							Toast.makeText(InvitationNewActivity.this, jsonObj.getString("descr"), Toast.LENGTH_LONG).show();
						}
					} catch (JSONException e) {
						Toast.makeText(InvitationNewActivity.this, R.string.error_occur, Toast.LENGTH_LONG).show();
						DocLog.e(TAG, "JSONException", e);
					}

				}

			};
			netConncet.execute();
			
		}
		
	}
	
	@Override
	public void onBackPressed() {
		super.onBackPressed();
		overridePendingTransition(0, R.anim.down);
	}
	
	public void closeActivity() {
		finish();
		overridePendingTransition(0, R.anim.down);
	}

}
