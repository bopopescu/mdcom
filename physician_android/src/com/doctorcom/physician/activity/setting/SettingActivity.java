package com.doctorcom.physician.activity.setting;

import java.io.File;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.json.JSONException;
import org.json.JSONObject;

import android.annotation.SuppressLint;
import android.annotation.TargetApi;
import android.app.ProgressDialog;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.content.pm.PackageManager.NameNotFoundException;
import android.graphics.BitmapFactory;
import android.hardware.Camera;
import android.os.Build;
import android.os.Bundle;
import android.support.v4.app.Fragment;
import android.support.v4.app.FragmentActivity;
import android.support.v4.app.FragmentManager;
import android.support.v4.content.LocalBroadcastManager;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.ImageView;
import android.widget.TextView;
import android.widget.Toast;

import com.doctorcom.android.R;
import com.doctorcom.physician.AppValues;
import com.doctorcom.physician.net.HttpMultipartPost;
import com.doctorcom.physician.net.ImageDownload;
import com.doctorcom.physician.net.NetConstantValues;
import com.doctorcom.physician.net.NetConstantValues.UPDATEAVATAR;
import com.doctorcom.physician.net.http.NetConncet;
import com.doctorcom.physician.utils.CallBack;
import com.doctorcom.physician.utils.DocLog;
import com.doctorcom.physician.utils.JsonErrorProcess;
import com.doctorcom.physician.utils.PreferLogo;
import com.doctorcom.physician.utils.cache.CacheService;
import com.doctorcom.physician.utils.cache.SucessReceiver;
import com.doctorcom.physician.utils.camera.CameraActivity;

public class SettingActivity extends FragmentActivity {

	@Override
	protected void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
		FragmentManager fm = getSupportFragmentManager();

		// Create the list fragment and add it as our sole content.
		if (fm.findFragmentById(android.R.id.content) == null) {
			SettingFragment setting = new SettingFragment();
			fm.beginTransaction().add(android.R.id.content, setting).commit();
		}
	}

	public static class SettingFragment extends Fragment {
		private final String TAG = "SettingFragment";
		private SucessReceiver cleanCacheReceiver = null;
		private LocalBroadcastManager broadcastManager;
		private final int AVATAR_CAMERA = 1;
		private ImageView avatarImageView;
		private ProgressDialog progress;
		private List<String> deprecatedAvatar;
		private ImageView ivPreferLogoImageView;

		@Override
		public View onCreateView(LayoutInflater inflater, ViewGroup container,
				Bundle savedInstanceState) {
			final View view = inflater.inflate(R.layout.fragment_settings,
					container, false);
			final AppValues appValues = new AppValues(getActivity());
			deprecatedAvatar = new ArrayList<String>();
			ivPreferLogoImageView = (ImageView) view
					.findViewById(R.id.ivPreferLogo);
			PreferLogo.showPreferLogo(getActivity(), ivPreferLogoImageView);
			Button siteButton = (Button) view.findViewById(R.id.btSite);
			Button practiceButton = (Button) view.findViewById(R.id.btPractice);
			practiceButton.setOnClickListener(new View.OnClickListener() {

				@Override
				public void onClick(View v) {
					Intent intent = new Intent(getActivity(),
							PracticeActivity.class);
					startActivity(intent);

				}
			});

			Button callForwardButton = (Button) view
					.findViewById(R.id.btCallForward);
			Button answeringServiceButton = (Button) view
					.findViewById(R.id.btAnsweringService);
			Button mobileButton = (Button) view.findViewById(R.id.btMobile);
			mobileButton.setOnClickListener(new View.OnClickListener() {

				@Override
				public void onClick(View v) {
					validatePhoneNumber();

				}
			});
			Button uploadAvatarButton = (Button) view
					.findViewById(R.id.btUploadAvatar);
			if (getActivity().getPackageManager().hasSystemFeature(
					PackageManager.FEATURE_CAMERA)) {
				uploadAvatarButton
						.setOnClickListener(new View.OnClickListener() {

							@TargetApi(Build.VERSION_CODES.GINGERBREAD)
							@Override
							public void onClick(View v) {
								if (Build.VERSION.SDK_INT > Build.VERSION_CODES.FROYO) {
									int id = -1;
									for (int i = 0, len = Camera
											.getNumberOfCameras(); i < len; i++) {
										Camera.CameraInfo info = new Camera.CameraInfo();
										Camera.getCameraInfo(i, info);
										if (info.facing == Camera.CameraInfo.CAMERA_FACING_FRONT) {
											id = i;
											break;
										}
									}
									Intent intent = new Intent(getActivity(),
											CameraActivity.class);
									intent.putExtra("cameraId", id);
									startActivityForResult(intent,
											AVATAR_CAMERA);
								}
							}
						});
			} else {
				uploadAvatarButton.setTextColor(getResources().getColor(
						android.R.color.darker_gray));
			}
			Button prefrenceButton = (Button) view
					.findViewById(R.id.btPrefrence);
			prefrenceButton.setOnClickListener(new View.OnClickListener() {

				@Override
				public void onClick(View v) {
					Intent intent = new Intent(getActivity(),
							PreferenceActivity.class);
					startActivity(intent);
				}
			});
			int userType = appValues.getUserType();
			siteButton.setOnClickListener(new View.OnClickListener() {

				@Override
				public void onClick(View v) {
					Intent intent = new Intent(getActivity(),
							SiteActivity.class);
					startActivity(intent);

				}
			});
			if (userType == AppValues.PROVIDER) {
				callForwardButton
						.setOnClickListener(new View.OnClickListener() {

							@Override
							public void onClick(View v) {
								Intent intent = new Intent(getActivity(),
										CallForwardActivity.class);
								startActivity(intent);

							}
						});
				answeringServiceButton
						.setOnClickListener(new View.OnClickListener() {

							@Override
							public void onClick(View v) {
								Intent intent = new Intent(getActivity(),
										AnsweringServicesActivity.class);
								startActivity(intent);

							}
						});
			} else {
				view.findViewById(R.id.llCallAnswering)
						.setVisibility(View.GONE);
				practiceButton.setText(R.string.practice_organization);
			}
			Button cleanCacheButton = (Button) view
					.findViewById(R.id.btCleanCache);
			cleanCacheButton.setOnClickListener(new View.OnClickListener() {

				@Override
				public void onClick(View v) {
					cleanCache();

				}
			});

			Button backButton = (Button) view.findViewById(R.id.btBack);
			backButton.setOnClickListener(new View.OnClickListener() {

				@Override
				public void onClick(View v) {
					getActivity().finish();

				}
			});

			try {
				PackageInfo info = getActivity().getPackageManager()
						.getPackageInfo(getActivity().getPackageName(), 0);
				TextView versionTextView = (TextView) view
						.findViewById(R.id.tvVersion);
				versionTextView.setText(getString(R.string.version_name_colon)
						+ info.versionName);
			} catch (NameNotFoundException ex) {
				DocLog.d(TAG, "processMenuAbout get PackageInfo error", ex);
			}
			avatarImageView = (ImageView) view
					.findViewById(R.id.imageview_avatar);
			NetConncet netConncet = new NetConncet(getActivity(),
					UPDATEAVATAR.PATH) {

				@Override
				protected void onPostExecute(String result) {
					super.onPostExecute(result);
					try {
						JSONObject jsonObject = new JSONObject(result);
						if (jsonObject.isNull("errno")) {
							ImageDownload download = new ImageDownload(
									getActivity(), "avatar001",
									avatarImageView,
									R.drawable.avatar_male_small);
							download.execute(appValues.getServerURL()
									+ jsonObject.getString("photo"));
						}
					} catch (JSONException e) {
						DocLog.e(TAG, "JSONException", e);
					}
				}

			};
			netConncet.execute();
			return view;
		}

		@Override
		public void onActivityCreated(Bundle savedInstanceState) {
			super.onActivityCreated(savedInstanceState);
			broadcastManager = LocalBroadcastManager.getInstance(getActivity());
			progress = new ProgressDialog(getActivity()) {

				@Override
				protected void onStop() {
					setProgress(0);
					super.onStop();
				}

			};
			progress.setProgressStyle(ProgressDialog.STYLE_HORIZONTAL);
			progress.setMessage(getResources().getText(
					R.string.uploading_avatar));

		}

		@Override
		public void onResume() {
			super.onResume();
			cleanCacheReceiver = new SucessReceiver();
			IntentFilter filter = new IntentFilter(
					CacheService.CLEAN_CACHE_ACTION);
			broadcastManager.registerReceiver(cleanCacheReceiver, filter);
			// getActivity().registerReceiver(cleanCacheReceiver, filter);
		}

		@Override
		public void onPause() {
			super.onPause();
			if (cleanCacheReceiver != null) {
				// getActivity().unregisterReceiver(cleanCacheReceiver);
				broadcastManager.unregisterReceiver(cleanCacheReceiver);
			}
		}

		public void validatePhoneNumber() {
				final ProgressDialog progress = ProgressDialog.show(
						getActivity(), "", getString(R.string.process_text));
				NetConncet netConncet = new NetConncet(getActivity(),
						NetConstantValues.PHONE_NUMBER.PATH, null) {

					@Override
					protected void onPostExecute(String result) {
						super.onPostExecute(result);
						progress.dismiss();
						try {
							JSONObject obj = new JSONObject(result);
							if (obj.isNull("errno")) {
								String mobilePhone = obj.getJSONObject("data")
										.getString("mobile_phone");
								boolean mobileConfirmed = obj.getJSONObject(
										"data").getBoolean("mobile_confirmed");
								CallBack.callerNumber = mobilePhone;
								CallBack.isNumberConfirmed = mobileConfirmed;
								Intent intent = new Intent(getActivity(),
										PhoneInputActivity.class);
								intent.putExtra("validated", true);
								startActivity(intent);

							} else {
								Toast.makeText(getActivity(),
										obj.getString("descr"),
										Toast.LENGTH_LONG).show();
							}
						} catch (JSONException e) {
							Toast.makeText(getActivity(), R.string.error_occur,
									Toast.LENGTH_LONG).show();
							DocLog.e(TAG, "JSONException", e);
						}
					}
				};
				netConncet.setHttpMethod(NetConncet.HTTP_GET);
				netConncet.execute();

		}

		@SuppressLint("ShowToast")
		@Override
		public void onActivityResult(int requestCode, int resultCode,
				Intent data) {
			if (resultCode == RESULT_OK) {
				switch (requestCode) {
				case AVATAR_CAMERA:
					try {
						String image = data.getStringExtra("image");
						if (image != null && !image.equals("")) {
							deprecatedAvatar.add(image);
							if (avatarImageView != null) {
								BitmapFactory.Options options = new BitmapFactory.Options();
								options.inJustDecodeBounds = true;
								BitmapFactory.decodeFile(image, options);
								options.inSampleSize = calculateInSampleSize(
										options, 100, 130);
								options.inJustDecodeBounds = false;
								avatarImageView.setImageBitmap(BitmapFactory
										.decodeFile(image, options));
							}
							uploadAvatar(image);
						}
						break;
					} catch (Exception e) {
						Toast.makeText(this.getActivity(), R.string.error_occur, Toast.LENGTH_LONG);
						DocLog.e(TAG, "Exception", e);
					}
				}
			}
		}

		public static int calculateInSampleSize(BitmapFactory.Options options,
				int reqWidth, int reqHeight) {
			// Raw height and width of image
			final int height = options.outHeight;
			final int width = options.outWidth;
			int inSampleSize = 1;

			if (height > reqHeight || width > reqWidth) {

				// Calculate ratios of height and width to requested height and
				// width
				final int heightRatio = Math.round((float) height
						/ (float) reqHeight);
				final int widthRatio = Math.round((float) width
						/ (float) reqWidth);

				// Choose the smallest ratio as inSampleSize value, this will
				// guarantee
				// a final image with both dimensions larger than or equal to
				// the
				// requested height and width.
				inSampleSize = heightRatio < widthRatio ? heightRatio
						: widthRatio;
			}

			return inSampleSize;
		}

		private void uploadAvatar(String avatar) {
			HttpMultipartPost docConn = new HttpMultipartPost(getActivity(),
					NetConstantValues.UPDATEAVATAR.PATH) {

				@Override
				protected void onPostExecute(String result) {
					if (JsonErrorProcess.checkJsonError(result, getActivity())) {
						Toast.makeText(getActivity(),
								R.string.action_successed, Toast.LENGTH_SHORT)
								.show();
					}
					super.onPostExecute(result);
					progress.dismiss();
				}

				@Override
				protected void onProgressUpdate(Integer... values) {
					progress.setProgress((int) values[0]);
				}

			};
			Map<String, String> params = new HashMap<String, String>();
			params.put("photo", avatar);
			docConn.setParams(params);
			docConn.execute();
			progress.show();

		}

		public void cleanCache() {
			Intent intent = new Intent(CacheService.CACHE_SERVICE);
			intent.putExtra("cmd", CacheService.CACHE_CLEAN);
			getActivity().startService(new Intent(intent));

		}

		@Override
		public void onDestroy() {
			for (int i = 0, len = deprecatedAvatar.size(); i < len; i++) {
				File file = new File(deprecatedAvatar.get(i));
				if (file.isFile() && file.exists()) {
					file.delete();
				}
			}
			super.onDestroy();
		}

	}

}
