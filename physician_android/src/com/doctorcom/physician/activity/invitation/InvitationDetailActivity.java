package com.doctorcom.physician.activity.invitation;

import android.app.Activity;
import android.app.AlertDialog;
import android.app.AlertDialog.Builder;
import android.app.ProgressDialog;
import android.content.DialogInterface;
import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.TextView;
import android.widget.Toast;

import com.doctorcom.android.R;
import com.doctorcom.physician.AppValues;
import com.doctorcom.physician.net.NetConstantValues;
import com.doctorcom.physician.net.http.NetConncet;
import com.doctorcom.physician.utils.JsonErrorProcess;
import com.doctorcom.physician.utils.Utils;
import com.doctorcom.physician.utils.cache.Cache;

public class InvitationDetailActivity extends Activity {

	public final int INVITATION_RESEND = 1;
	private InvitationItem item;
	private TextView dueTextView;
	private Button resendButton, deleteButton;
	private AppValues appValues;

	@Override
	protected void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
		setContentView(R.layout.activity_invitation_detail);
		
		appValues = new AppValues(this);
		Intent intent = getIntent();
		item = (InvitationItem) intent.getSerializableExtra("invitation");
		TextView recipientTextView = (TextView) findViewById(R.id.tvRecipient);
		recipientTextView.setText(item.getRecipient());
		dueTextView = (TextView) findViewById(R.id.tvDue);
		resendButton = (Button) findViewById(R.id.btResend);
		deleteButton = (Button) findViewById(R.id.btDelete);
		Button backButton = (Button) findViewById(R.id.btBack);
		backButton.setOnClickListener(new View.OnClickListener() {
			
			@Override
			public void onClick(View v) {
				finish();
				
			}
		});
		init();
	}
	
	private void init() {
		dueTextView.setText(Utils.getDateTimeFormat(item.getDueTimestamp(), appValues.getTimeFormat(), appValues.getTimezone()));
		resendButton.setOnClickListener(new View.OnClickListener() {
			
			@Override
			public void onClick(View v) {
				Intent i = new Intent(InvitationDetailActivity.this, InvitationNewActivity.class);
				i.putExtra("item", item);
				startActivityForResult(i, INVITATION_RESEND);
				overridePendingTransition(R.anim.up, R.anim.hold);
				
			}
		});
		deleteButton.setOnClickListener(new InvitationDelete());
	}
	
	class InvitationDelete implements View.OnClickListener {

		@Override
		public void onClick(View v) {
			AlertDialog.Builder builder = new Builder(InvitationDetailActivity.this);
			builder.setMessage(R.string.invitation_cancel_warning_message)
					.setTitle(R.string.warning_title)
					.setPositiveButton(R.string.ok, new DialogInterface.OnClickListener() {

								@Override
								public void onClick(DialogInterface dialog, int which) {
									dialog.dismiss();
									final ProgressDialog progress = ProgressDialog.show(InvitationDetailActivity.this, "", getString(R.string.process_text));
									NetConncet netConncet = new NetConncet(InvitationDetailActivity.this, NetConstantValues.CANCEL_INVITATION.getPath(String.valueOf(item.getId())), null) {
										
										@Override
										protected void onPostExecute(String result) {
											super.onPostExecute(result);
											progress.dismiss();
											if (JsonErrorProcess.checkJsonError(result, InvitationDetailActivity.this)) {
												Toast.makeText(InvitationDetailActivity.this, R.string.action_successed,Toast.LENGTH_SHORT).show();
												Cache.cleanListCache(String.valueOf(Cache.CACHE_INVITATION_LIST), NetConstantValues.GET_OUTSTANDING_INVITATIONS.PATH, getApplicationContext());
												finish();
											}
										}
										
									};
									netConncet.execute();

								}

							})
					.setNegativeButton(R.string.cancel, new DialogInterface.OnClickListener() {

								@Override
								public void onClick(DialogInterface dialog, int which) {
									dialog.dismiss();

								}

							});
			builder.show();
		}
	}
	
	@Override
	protected void onActivityResult(int requestCode, int resultCode, Intent data) {
		if (resultCode == RESULT_OK) {
			switch (requestCode) {
			case INVITATION_RESEND:
				item = (InvitationItem) data.getSerializableExtra("invitation");
				init();
				break;
			}
		}
	}

}
