package com.doctorcom.physician.activity.doctor;

import java.util.HashMap;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import android.app.Activity;
import android.app.ProgressDialog;
import android.content.Context;
import android.content.Intent;
import android.database.sqlite.SQLiteDatabase;
import android.os.Bundle;
import android.os.Handler;
import android.view.View;
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import com.doctorcom.android.R;
import com.doctorcom.physician.AppValues;
import com.doctorcom.physician.activity.message.MessageNewActivity;
import com.doctorcom.physician.net.ImageDownload;
import com.doctorcom.physician.net.NetConstantValues;
import com.doctorcom.physician.net.http.NetConncet;
import com.doctorcom.physician.utils.AESEncryptDecrypt;
import com.doctorcom.physician.utils.Connection;
import com.doctorcom.physician.utils.DocLog;
import com.doctorcom.physician.utils.JsonErrorProcess;
import com.doctorcom.physician.utils.AESEncryptDecrypt.AESEncryptDecryptException;
import com.doctorcom.physician.utils.cache.Cache;
import com.doctorcom.physician.utils.cache.DataBaseHelper;
import com.doctorcom.physician.utils.cache.Cache.CacheSchema;

public class DoctorDetailActivity extends Activity implements
		Cache.CacheFinishListener {
	private final String TAG = "DoctorDetailActivity";
	public static final int MESSAGE_DISPATCHER_PROVIDER = 1;
	public static final int MESSAGE_DISPATCHER_PRACTICE = 2;
	private static final int REFRESH = 10;
	private static final int FAVOURITE_REFRESH = 11;
	private int userId = 0;
	private String name = "";
	private FrameLayout frameLoading;
	private ScrollView scroll;
	private boolean hasData = false;
	private Button isFavouriteButton;
	private boolean isFavourite;
	private AppValues appValues;
	private int times = 0;
	private String path;
	private LinearLayout llOrgLogoContainer;

	@Override
	protected void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
		setContentView(R.layout.activity_doctor_detail);
		frameLoading = (FrameLayout) findViewById(R.id.frameLoading);
		scroll = (ScrollView) findViewById(R.id.scroll);
		frameLoading.setVisibility(View.VISIBLE);
		scroll.setVisibility(View.GONE);
		Intent intent = getIntent();
		Button backButton = (Button) findViewById(R.id.btBack);
		backButton.setOnClickListener(new View.OnClickListener() {

			@Override
			public void onClick(View v) {
				finish();

			}
		});
		appValues = new AppValues(this);
		isFavouriteButton = (Button) findViewById(R.id.btIsFavourite);
		isFavouriteButton.setVisibility(View.INVISIBLE);
		userId = intent.getIntExtra("userId", 0);
		name = intent.getStringExtra("name");
		if (intent.hasExtra("path"))
			path = intent.getStringExtra("path");
		Cache cache = new Cache(this, NetConncet.HTTP_POST);
		cache.setCacheType(Cache.CACHE_USER_PROFILE);
		cache.useCache(this,
				NetConstantValues.USER_PROFILE.getPath(String.valueOf(userId)),
				"/User/*/Profile/", null);

	}

	@Override
	public void onCacheFinish(String result, boolean hasData) {
		if (JsonErrorProcess.checkJsonError(result, this)) {
			Intent intent = getIntent();
			Boolean hasListIsFavourite = intent.hasExtra("listIsFavourite");
			JSONObject jsonObj;
			try {
				jsonObj = new JSONObject(result);
				JSONObject jData = jsonObj.getJSONObject("data");
				if (!jData.isNull("is_favorite")) {
					isFavourite = jData.getBoolean("is_favorite");
				}
			} catch (JSONException e) {
				// TODO Auto-generated catch block
				DocLog.e(TAG, "JSONException", e);
				Toast.makeText(this, R.string.error_occur, Toast.LENGTH_SHORT)
						.show();
				finish();
			}
			if (hasListIsFavourite) {
				Boolean listIsFavourite = intent.getBooleanExtra(
						"listIsFavourite", true);
				if (listIsFavourite != isFavourite) {
					if (this.times == 0)
						cleanCacheAndRefresh();
					else {
						this.hasData = true;
						updateData(result);
						this.setResult(REFRESH);
						if (!(path == null || path.equals("")))
							Cache.cleanListCache(String.valueOf(Cache.CACHE_USER_LIST), path, getApplicationContext());
					}
				} else {
					this.hasData = true;
					updateData(result);
				}
			} else {
				this.hasData = true;
				updateData(result);
			}
		} else {
			if (!this.hasData) {
				finish();
			}
		}
	}

	private void getData() {
		Intent intent = getIntent();
		userId = intent.getIntExtra("userId", 0);
		name = intent.getStringExtra("name");
		Cache cache = new Cache(this, NetConncet.HTTP_POST);
		cache.setCacheType(Cache.CACHE_USER_PROFILE);
		cache.useCache(this,
				NetConstantValues.USER_PROFILE.getPath(String.valueOf(userId)),
				"/User/*/Profile/", null);
	}

	private void cleanCacheAndRefresh() {
		// TODO Auto-generated method stub
		this.times++;
		final Handler handler = new Handler();
		final DataBaseHelper helper = new DataBaseHelper(this);
		final SQLiteDatabase db = helper.getWritableDatabase();
		final AESEncryptDecrypt decrypt = new AESEncryptDecrypt(
				AppValues.aeskey, this.getCacheDir().getAbsolutePath()
						+ AppValues.secretKey);
		final Runnable runnable = new Runnable() {

			@Override
			public void run() {
				DocLog.d(TAG, "getMessageBody");
				getData();
			}
		};

		new Thread() {

			@Override
			public void run() {
				String decryptUrl;
				try {
					Intent intent = getIntent();
					userId = intent.getIntExtra("userId", 0);
					String url = NetConstantValues.USER_PROFILE.getPath(String
							.valueOf(userId));
					decryptUrl = decrypt.encrypt(appValues.getServerURL()
							+ NetConstantValues.APP_URL + url);
					db.delete(CacheSchema.TABLE_NAME, "category = 2 and "
							+ CacheSchema.URL + " = ?",
							new String[] { decryptUrl });
					DocLog.d(TAG, "delete cache" + url);
				} catch (AESEncryptDecryptException e) {
					db.delete(CacheSchema.TABLE_NAME, null, null);
					DocLog.e(TAG, "AESEncryptDecryptException", e);
				} finally {
					db.close();
					helper.close();
				}
				handler.post(runnable);
			}

		}.start();

	}

	private void updateData(String result) {
		frameLoading.setVisibility(View.GONE);
		scroll.setVisibility(View.VISIBLE);
		TextView nameTextView = (TextView) findViewById(R.id.tvName);
		TextView specialtyTextView = (TextView) findViewById(R.id.tvSpecialty);
		TextView specialSkillsTextView = (TextView) findViewById(R.id.tvSpecialSkills);
		TextView currentOrgTitleTV = (TextView) findViewById(R.id.tvCurrentOrgTitle);
		TextView practiceLocationTextView = (TextView) findViewById(R.id.tvPracticeLocation);
		TextView otherORGs = (TextView) findViewById(R.id.textview_other_orgs);
		Button messageButton = (Button) findViewById(R.id.btMessage);
		Button callButton = (Button) findViewById(R.id.btCall);
		Button pageButton = (Button) findViewById(R.id.btPage);
		Button practiceMessageButton = (Button) findViewById(R.id.btPracticeMessage);
		Button practiceCallButton = (Button) findViewById(R.id.btPracticeCall);
		llOrgLogoContainer = (LinearLayout) findViewById(R.id.llOrgLogoContainer);
		try {
			JSONObject jsonObj = new JSONObject(result);
			JSONObject jData = jsonObj.getJSONObject("data");
			if (!jData.isNull("is_favorite")) {
				isFavouriteButton.setVisibility(View.VISIBLE);
				isFavourite = jData.getBoolean("is_favorite");
				if (isFavourite)
					isFavouriteButton
							.setBackgroundResource(R.drawable.is_favourite);
				else
					isFavouriteButton
							.setBackgroundResource(R.drawable.is_not_favourite);
				isFavouriteButton
						.setOnClickListener(new UserFavouriteClickListener(
								this, userId));
			}
			nameTextView.setText(jData.getString("last_name") + " "
					+ jData.getString("first_name"));
			if (!jData.isNull("specialty")) {
				specialtyTextView.setText(jData.getString("specialty"));
			}
			if (!jData.isNull("skill")) {
				specialSkillsTextView.setText(jData.getString("skill"));
			}
			JSONArray orgsJsonArray = jData.getJSONArray("other_orgs");
			StringBuffer sb = new StringBuffer();
			for (int i = 0, len = orgsJsonArray.length(); i < len; i++) {
				JSONObject orgJSONObject = orgsJsonArray.getJSONObject(i);
				sb.append(orgJSONObject.getString("name") + "\r\n");
			}
			if (sb.length() <= 0) {
				findViewById(R.id.framelayout_top).setVisibility(View.GONE);
				findViewById(R.id.framelayout_bottom).setVisibility(View.GONE);
				findViewById(R.id.linearlayout_org_content).setVisibility(
						View.GONE);
			} else {
				otherORGs.setText(sb);
			}
			String photo = "";
			AppValues appValues = new AppValues(this);
			if (!jData.isNull("photo")) {
				photo = jData.getString("photo");
				ImageView avatarImageView = (ImageView) findViewById(R.id.ivAvatar);
				ImageDownload download = new ImageDownload(this,
						String.valueOf(userId), avatarImageView,
						R.drawable.avatar_male_small);
				download.execute(appValues.getServerURL() + photo);
			}
			String practice = jData.getString("current_practice");
			if (!practice.equals("")) {
				JSONObject jsonPractice = new JSONObject(practice);
				if (!jsonPractice.isNull("org_type_id")) {
					int orgTypeId = jsonPractice.getInt("org_type_id");
					if (orgTypeId == 1)
						currentOrgTitleTV.setText(R.string.current_practice);
					else
						currentOrgTitleTV
								.setText(R.string.current_organization);
				}
				String address = "", city = "", state = "", zip = "";
				if (!jsonPractice.isNull("practice_address1")) {
					address = jsonPractice.getString("practice_address1");
				}
				if (!jsonPractice.isNull("practice_state")) {
					state = jsonPractice.getString("practice_state");
				}
				if (!jsonPractice.isNull("practice_zip")) {
					zip = jsonPractice.getString("practice_zip");
				}
				if (!jsonPractice.isNull("practice_city")) {
					city = jsonPractice.getString("practice_city");
				}
				practiceLocationTextView.setText(address + " " + city + ", "
						+ state + " " + zip);
				final int practiceId = jsonPractice.getInt("id");
				final String practiceName = jsonPractice
						.getString("practice_name");
				if (jsonPractice.getBoolean("msg_available")) {
					practiceMessageButton
							.setBackgroundResource(R.drawable.button_msg);
					practiceMessageButton
							.setOnClickListener(new View.OnClickListener() {

								@Override
								public void onClick(View v) {
									Intent intent = new Intent(
											DoctorDetailActivity.this,
											MessageNewActivity.class);
									intent.putExtra("userId", practiceId);
									intent.putExtra("name", practiceName);
									intent.putExtra(
											"dispatcher",
											DoctorDetailActivity.MESSAGE_DISPATCHER_PRACTICE);
									startActivity(intent);
									overridePendingTransition(R.anim.up,
											R.anim.hold);

								}
							});
				} else {
					practiceMessageButton
							.setBackgroundResource(R.drawable.button_msg_disable);
				}
				if (jsonPractice.getBoolean("call_available")) {
					practiceCallButton
							.setBackgroundResource(R.drawable.button_call);
					practiceCallButton.setOnClickListener(new Connection(this,
							Connection.CALL, userId,
							NetConstantValues.CALL_PRACTICE.getPath(String
									.valueOf(practiceId))));
				} else {
					practiceCallButton
							.setBackgroundResource(R.drawable.button_call_disable);
				}
			} else {
				LinearLayout currentPracticeOrg = (LinearLayout) findViewById(R.id.llcurrentPracticeOrg);
				currentPracticeOrg.setVisibility(View.GONE);
			}
			if (!jData.isNull("custom_logos")) {
				JSONArray customLogos = jData.getJSONArray("custom_logos");
				int maxCount = 4;
				int count = 0;
				for (int i = 0; i < customLogos.length(); i++) {
					if (count >= maxCount)
						break;
					JSONObject orgLogo = customLogos.getJSONObject(i);
					String logoUrl = orgLogo.getString("logo");
					ImageView image = (ImageView) llOrgLogoContainer
							.getChildAt(i);
					ImageDownload download = new ImageDownload(this,
							"detail_org" + String.valueOf(userId) + String.valueOf(i), image, -1);
					download.execute(appValues.getServerURL() + logoUrl);
					count++;

				}
			}

			if (jData.getBoolean("has_pager")) {
				pageButton.setBackgroundResource(R.drawable.button_page);
				pageButton.setOnClickListener(new Connection(this,
						Connection.PAGE, userId, null));
			} else {
				pageButton
						.setBackgroundResource(R.drawable.button_page_disable);
			}
			if (jData.getBoolean("has_mobile")) {
				callButton.setBackgroundResource(R.drawable.button_call);
				callButton.setOnClickListener(new Connection(this,
						Connection.CALL, userId, NetConstantValues.CALL_USER
								.getPath(String.valueOf(userId))));
			} else {
				callButton
						.setBackgroundResource(R.drawable.button_call_disable);
			}
			messageButton.setOnClickListener(new View.OnClickListener() {

				@Override
				public void onClick(View v) {
					Intent intent = new Intent(DoctorDetailActivity.this,
							MessageNewActivity.class);
					intent.putExtra("userId", userId);
					intent.putExtra("name", name);
					startActivity(intent);
					overridePendingTransition(R.anim.up, R.anim.hold);

				}
			});

		} catch (JSONException e) {
			DocLog.e(TAG, "JSONException", e);
			Toast.makeText(this, R.string.error_occur, Toast.LENGTH_SHORT)
					.show();
			finish();
		}

	}

	class UserFavouriteClickListener implements View.OnClickListener {
		private Context mContext;
		private int objectId;

		public UserFavouriteClickListener(Context context, int objectId) {
			mContext = context;
			this.objectId = objectId;
		}

		@Override
		public void onClick(View v) {
			final ProgressDialog progress = ProgressDialog.show(mContext, "",
					getString(R.string.process_text));
			HashMap<String, String> params = new HashMap<String, String>();
			params.put(
					NetConstantValues.USER_STATUS_UPDATE.PARAM_OBJECT_TYPE_FLAG,
					Integer.toString(1));
			params.put(NetConstantValues.USER_STATUS_UPDATE.PARAM_OBJECT_ID,
					String.valueOf(objectId));
			params.put(NetConstantValues.USER_STATUS_UPDATE.PARAM_IS_FAVOURITE,
					String.valueOf(!isFavourite));

			NetConncet netConncet = new NetConncet(mContext,
					NetConstantValues.USER_STATUS_UPDATE.PATH, params) {

				@Override
				protected void onPostExecute(String result) {
					super.onPostExecute(result);
					progress.dismiss();
					if (JsonErrorProcess.checkJsonError(result, mContext)) {
						if (isFavourite)
							Toast.makeText(mContext, R.string.leave_favourite,
									Toast.LENGTH_SHORT).show();
						else
							Toast.makeText(mContext, R.string.add_favourite,
									Toast.LENGTH_SHORT).show();
						isFavourite = !isFavourite;
						setFavouriteStstus();
						cleanListCache("UserList");
						setResult(FAVOURITE_REFRESH);
					}
				}
			};
			netConncet.execute();

		}

	}

	void setFavouriteStstus() {
		if (isFavourite)
			isFavouriteButton.setBackgroundResource(R.drawable.is_favourite);
		else
			isFavouriteButton
					.setBackgroundResource(R.drawable.is_not_favourite);

	}

	private void cleanListCache(String url) {
		// TODO Auto-generated method stub
		final DataBaseHelper helper = new DataBaseHelper(this);
		final SQLiteDatabase db = helper.getWritableDatabase();
		new Thread() {

			@Override
			public void run() {
				db.delete(CacheSchema.TABLE_NAME, "category = 1", null);
				DocLog.d(TAG, "delete cache userlist");
				db.close();
				helper.close();
			}

		}.start();

	}
}
