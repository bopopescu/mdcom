package com.doctorcom.physician.activity.doctor;

import java.util.HashMap;

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

public class PracticeDetailActivity extends Activity implements
		Cache.CacheFinishListener {

	private static final int REFRESH = 10;
	private static final int FAVOURITE_REFRESH = 11;
	private final String TAG = "PracticeDetailActivity";
	private FrameLayout frameLoading;
	private ScrollView scroll;
	private int practiceId;
	private Button isFavouriteButton;
	private boolean isFavourite;
	private int times = 0;
	private boolean hasData = false;
	private AppValues appValues;
	private String path;

	@Override
	protected void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
		setContentView(R.layout.activity_practice_detail);
		Cache cache = new Cache(this, NetConncet.HTTP_POST);
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
		isFavouriteButton = (Button) findViewById(R.id.btIsFavourite);
		isFavouriteButton.setVisibility(View.INVISIBLE);
		practiceId = intent.getIntExtra("practiceId", 0);
		if (intent.hasExtra("path"))
			path = intent.getStringExtra("path");
		appValues = new AppValues(this);
		cache.setCacheType(Cache.CACHE_PRACTICE_PROFILE);
		cache.useCache(this, NetConstantValues.PRACTICE_PROFILE.getPath(String
				.valueOf(practiceId)), NetConstantValues.PRACTICE_PROFILE.PATH
				+ "*/Profile/", null);

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
						if (!(path == null || path.equals("")))
							Cache.cleanListCache(String.valueOf(Cache.CACHE_USER_LIST), path, getApplicationContext());
						this.setResult(REFRESH);
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
					practiceId = intent.getIntExtra("practiceId", 0);
					String url = NetConstantValues.PRACTICE_PROFILE
							.getPath(String.valueOf(practiceId));
					decryptUrl = decrypt.encrypt(appValues.getServerURL()
							+ NetConstantValues.APP_URL + url);
					db.delete(CacheSchema.TABLE_NAME, "category = 3 and "
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

	private void getData() {
		Intent intent = getIntent();
		practiceId = intent.getIntExtra("practiceId", 0);
		Cache cache = new Cache(this, NetConncet.HTTP_POST);
		cache.setCacheType(Cache.CACHE_PRACTICE_PROFILE);
		cache.useCache(this, NetConstantValues.PRACTICE_PROFILE.getPath(String
				.valueOf(practiceId)), NetConstantValues.PRACTICE_PROFILE.PATH
				+ "*/Profile/", null);
	}

	public void updateData(String result) {
		frameLoading.setVisibility(View.GONE);
		scroll.setVisibility(View.VISIBLE);
		TextView nameTextView = (TextView) findViewById(R.id.tvName);
		TextView practiceLocationTextView = (TextView) findViewById(R.id.tvPracticeLocation);
		Button practiceMessageButton = (Button) findViewById(R.id.btPracticeMessage);
		Button practiceCallButton = (Button) findViewById(R.id.btPracticeCall);
		try {
			JSONObject jsonObj = new JSONObject(result);
			JSONObject jsonPractice = jsonObj.getJSONObject("data");
			if (!jsonPractice.isNull("is_favorite")) {
				isFavouriteButton.setVisibility(View.VISIBLE);
				isFavourite = jsonPractice.getBoolean("is_favorite");
				if (isFavourite)
					isFavouriteButton
							.setBackgroundResource(R.drawable.is_favourite);
				else
					isFavouriteButton
							.setBackgroundResource(R.drawable.is_not_favourite);
				isFavouriteButton
						.setOnClickListener(new UserFavouriteClickListener(
								this, practiceId));
			}
			final String practiceName = jsonPractice.getString("practice_name");
			nameTextView.setText(practiceName);
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
			if (jsonPractice.getBoolean("has_manager")) {
				practiceMessageButton
						.setBackgroundResource(R.drawable.button_msg);
				practiceMessageButton
						.setOnClickListener(new View.OnClickListener() {

							@Override
							public void onClick(View v) {
								Intent intent = new Intent(
										PracticeDetailActivity.this,
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
			if (jsonPractice.getBoolean("has_mobile")) {
				practiceCallButton
						.setBackgroundResource(R.drawable.button_call);
				practiceCallButton.setOnClickListener(new Connection(this,
						Connection.CALL, -1, NetConstantValues.CALL_PRACTICE
								.getPath(String.valueOf(practiceId))));
			} else {
				practiceCallButton
						.setBackgroundResource(R.drawable.button_call_disable);
			}
			String practicePhoto = "";
			if (!jsonPractice.isNull("practice_photo")) {
				practicePhoto = jsonPractice.getString("practice_photo");
				ImageView practicePhotoImageView = (ImageView) findViewById(R.id.ivPracticePhoto);
				ImageDownload practiceImageDownloader = new ImageDownload(this,
						"org" + String.valueOf(practiceId), practicePhotoImageView, -1);
				AppValues appValues = new AppValues(this);
				practiceImageDownloader.execute(appValues.getServerURL()
						+ practicePhoto);
			}
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
					Integer.toString(2));
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
