package com.doctorcom.physician.activity.main;

import java.io.File;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

import android.accounts.Account;
import android.accounts.AccountManager;
import android.app.AlertDialog;
import android.app.NotificationManager;
import android.app.ProgressDialog;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager.NameNotFoundException;
import android.content.res.Resources;
import android.graphics.Bitmap;
import android.os.AsyncTask;
import android.os.Bundle;
import android.support.v4.app.Fragment;
import android.support.v4.app.FragmentActivity;
import android.support.v4.app.FragmentManager;
import android.support.v4.app.FragmentTransaction;
import android.support.v4.content.LocalBroadcastManager;
import android.view.Menu;
import android.view.MenuItem;
import android.view.View;
import android.view.View.OnClickListener;
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.ImageView;
import android.widget.RelativeLayout;
import android.widget.Toast;

import com.doctorcom.android.R;
import com.doctorcom.android.ServerUtilities;
import com.doctorcom.physician.AppValues;
import com.doctorcom.physician.activity.call.CallActivity;
import com.doctorcom.physician.activity.doctor.DoctorListActivity;
import com.doctorcom.physician.activity.login.LoginActivity;
import com.doctorcom.physician.activity.message.MessageListActivity;
import com.doctorcom.physician.activity.more.CommonMoreMethods;
import com.doctorcom.physician.activity.more.MoreListActivity;
import com.doctorcom.physician.activity.task.TaskListActivity;
import com.doctorcom.physician.net.NetConstantValues;
import com.doctorcom.physician.net.OriginalImageDownload;
import com.doctorcom.physician.net.OriginalImageDownload.OrinialImageDownloadFinishListener;
import com.doctorcom.physician.net.http.NetConncet;
import com.doctorcom.physician.settings.AppSettings;
import com.doctorcom.physician.utils.CallBack;
import com.doctorcom.physician.utils.DocLog;
import com.doctorcom.physician.utils.cache.CacheService;
import com.google.android.gcm.GCMRegistrar;

/**
 * Use to navigation.
 * 
 * @author zhzhu
 * @version 1.0
 * 
 */
public class NavigationActivity extends FragmentActivity implements
		OrinialImageDownloadFinishListener {

	private String TAG = "NavigationActivity";
	private Button messagesButton, doctorsButton, tasksButton, callButton,
			moreButton;

	private final int MESSAGE_FRAGMENT = 1;
	private final int DOCTOR_FRAGMENT = 2;
	private final int TASK_FRAGMENT = 3;
	private final int CALL_FRAGMENT = 4;
	private final int MORE_FRAGMENT = 5;
	private Fragment lastFragment;
	private FrameLayout messageFrameLayout, doctorFrameLayout, taskFrameLayout,
			callFrameLayout, moreFrameLayout;
	private RelativeLayout messageLinearLayout, doctorLinearLayout,
			taskLinearLayout, callLinearLayout, moreLinearLayout;
	AsyncTask<Void, Void, Void> mRegisterTask;
	private CacheCleanReceiver cacheCleanReceiver = null;
	private LocalBroadcastManager broadcastManager;
	public final String REFRESH_ACTION = "refreshAction";
	private AppValues appValues;

	public interface RefreshListener {
		void refreshView();

		void forceRefreshView();
	}

	@Override
	protected void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
		try {
			// Make sure the device has the proper dependencies.
			GCMRegistrar.checkDevice(this);
			int level = android.os.Build.VERSION.SDK_INT;
			if (level >= 16) {
				registerGCM();
			} else {
				AccountManager accountManager = AccountManager.get(this);
				Account[] account = accountManager
						.getAccountsByType("com.google");
				if (account == null || account.length <= 0) {
					Intent i = new Intent("com.doctorcom.physician.message");
					startService(i);
				} else {
					registerGCM();
				}
			}
		} catch (Exception e) {
			DocLog.i(TAG, "use sercice", e);
			startService(new Intent("com.doctorcom.physician.message"));
		}
		setContentView(R.layout.activity_navigation);
		
		appValues = new AppValues(this);
		boolean showPreferLogo = appValues.isShowPreferLogo();
		String preferLogoPath = appValues.getPreferLogoPath();
		if (showPreferLogo && !preferLogoPath.equals("")) {
			RelativeLayout rlPrefer = (RelativeLayout) findViewById(R.id.rlPrefer);
			rlPrefer.setVisibility(View.VISIBLE);
			OriginalImageDownload download = new OriginalImageDownload(
					this, AppValues.PREFER_LOGO);
			download.execute(appValues.getServerURL() + preferLogoPath);
		}

		messagesButton = (Button) findViewById(R.id.btMessages);
		messagesButton.setOnClickListener(new OnClickListener() {

			@Override
			public void onClick(View v) {
				switchFragment(MESSAGE_FRAGMENT);

			}

		});

		doctorsButton = (Button) findViewById(R.id.btDoctors);
		doctorsButton.setOnClickListener(new OnClickListener() {

			@Override
			public void onClick(View v) {
				switchFragment(DOCTOR_FRAGMENT);

			}

		});

		tasksButton = (Button) findViewById(R.id.btTasks);
		tasksButton.setOnClickListener(new OnClickListener() {

			@Override
			public void onClick(View v) {
				switchFragment(TASK_FRAGMENT);

			}

		});

		callButton = (Button) findViewById(R.id.btCall);
		callButton.setOnClickListener(new OnClickListener() {

			@Override
			public void onClick(View v) {
				switchFragment(CALL_FRAGMENT);

			}

		});

		moreButton = (Button) findViewById(R.id.btMore);
		moreButton.setOnClickListener(new OnClickListener() {

			@Override
			public void onClick(View v) {
				switchFragment(MORE_FRAGMENT);

			}

		});

		messageFrameLayout = (FrameLayout) findViewById(R.id.fMessages);
		doctorFrameLayout = (FrameLayout) findViewById(R.id.fDoctors);
		taskFrameLayout = (FrameLayout) findViewById(R.id.fTasks);
		callFrameLayout = (FrameLayout) findViewById(R.id.fCall);
		moreFrameLayout = (FrameLayout) findViewById(R.id.fMore);

		messageLinearLayout = (RelativeLayout) findViewById(R.id.rlMessages);
		messageLinearLayout.setOnClickListener(new View.OnClickListener() {

			@Override
			public void onClick(View v) {
				messagesButton.performClick();

			}
		});
		doctorLinearLayout = (RelativeLayout) findViewById(R.id.rlDoctors);
		doctorLinearLayout.setOnClickListener(new View.OnClickListener() {

			@Override
			public void onClick(View v) {
				doctorsButton.performClick();

			}
		});
		taskLinearLayout = (RelativeLayout) findViewById(R.id.rlTasks);
		taskLinearLayout.setOnClickListener(new View.OnClickListener() {

			@Override
			public void onClick(View v) {
				tasksButton.performClick();

			}
		});
		callLinearLayout = (RelativeLayout) findViewById(R.id.rlCall);
		callLinearLayout.setOnClickListener(new View.OnClickListener() {

			@Override
			public void onClick(View v) {
				callButton.performClick();

			}
		});
		moreLinearLayout = (RelativeLayout) findViewById(R.id.rlMore);
		moreLinearLayout.setOnClickListener(new View.OnClickListener() {

			@Override
			public void onClick(View v) {
				moreButton.performClick();

			}
		});
		messagesButton.performClick();
		broadcastManager = LocalBroadcastManager.getInstance(this);
		cacheCleanReceiver = new CacheCleanReceiver();
		IntentFilter filter = new IntentFilter(REFRESH_ACTION);
		broadcastManager.registerReceiver(cacheCleanReceiver, filter);
	}

	FragmentManager fm;

	/**
	 * Switch to the fragment rely on the position.
	 * 
	 * @param position
	 */
	public void switchFragment(int position) {
		/*
		 * FragmentInfo newFragment = mFragments.get(position); FragmentManager
		 * fm = getSupportFragmentManager(); FragmentTransaction ft =
		 * fm.beginTransaction(); if (lastFragment != null) {
		 * if(newFragment.fragment == null) { ft.detach(lastFragment);
		 * newFragment.fragment = Fragment.instantiate(this,
		 * newFragment.clss.getName(), newFragment.args); ft.add(R.id.nav,
		 * newFragment.fragment); ft.commit(); lastFragment =
		 * newFragment.fragment; } else { if (lastFragment ==
		 * newFragment.fragment) { //user stay on the current fragment,so just
		 * need to refresh it RefreshListener f = (RefreshListener)
		 * lastFragment; f.refreshView(); } else { ft.detach(lastFragment);
		 * ft.attach(newFragment.fragment).commit(); lastFragment =
		 * newFragment.fragment; } } } else { if(newFragment.fragment == null) {
		 * newFragment.fragment = Fragment.instantiate(this,
		 * newFragment.clss.getName()); ft.add(R.id.nav, newFragment.fragment);
		 * ft.commit(); lastFragment = newFragment.fragment; } }
		 */

		fm = getSupportFragmentManager();
		FragmentTransaction ft = fm.beginTransaction();
		Fragment fMessage = fm.findFragmentById(R.id.fMessages);
		Fragment fDoctor = fm.findFragmentById(R.id.fDoctors);
		Fragment fTask = fm.findFragmentById(R.id.fTasks);
		Fragment fCall = fm.findFragmentById(R.id.fCall);
		Fragment fMore = fm.findFragmentById(R.id.fMore);

		switch (position) {
		case MESSAGE_FRAGMENT: {
			if (fDoctor != null) {
				ft.hide(fDoctor);
			}
			if (fTask != null) {
				ft.hide(fTask);
			}
			if (fCall != null) {
				ft.hide(fCall);
			}
			if (fMore != null) {
				ft.hide(fMore);
			}
			if (fMessage == null) {
				fMessage = Fragment
						.instantiate(this,
								MessageListActivity.MessageListFragment.class
										.getName());
				ft.add(R.id.fMessages, fMessage);
			} else {
				ft.show(fMessage);
				if (lastFragment == fMessage) {
					RefreshListener f = (RefreshListener) lastFragment;
					f.refreshView();
				}
			}
			ft.commitAllowingStateLoss();
			lastFragment = fMessage;
			messageFrameLayout.setVisibility(View.VISIBLE);
			doctorFrameLayout.setVisibility(View.GONE);
			taskFrameLayout.setVisibility(View.GONE);
			callFrameLayout.setVisibility(View.GONE);
			moreFrameLayout.setVisibility(View.GONE);
			messagesButton.setBackgroundResource(R.drawable.tab_messages_press);
			doctorsButton.setBackgroundResource(R.drawable.tab_doctors);
			tasksButton.setBackgroundResource(R.drawable.tab_tasks);
			callButton.setBackgroundResource(R.drawable.tab_call);
			moreButton.setBackgroundResource(R.drawable.tab_more);
			messageLinearLayout
					.setBackgroundResource(R.drawable.footer_menu_bg_select);
			doctorLinearLayout.setBackgroundDrawable(null);
			taskLinearLayout.setBackgroundDrawable(null);
			callLinearLayout.setBackgroundDrawable(null);
			moreLinearLayout.setBackgroundDrawable(null);
			break;
		}
		case DOCTOR_FRAGMENT: {
			if (fMessage != null) {
				ft.hide(fMessage);
			}
			if (fTask != null) {
				ft.hide(fTask);
			}
			if (fCall != null) {
				ft.hide(fCall);
			}
			if (fMore != null) {
				ft.hide(fMore);
			}
			if (fDoctor == null) {
				fDoctor = Fragment.instantiate(this,
						DoctorListActivity.DoctorListFragment.class.getName());
				ft.add(R.id.fDoctors, fDoctor);
			} else {
				ft.show(fDoctor);
				if (lastFragment == fDoctor) {
					RefreshListener f = (RefreshListener) lastFragment;
					f.refreshView();
				}
			}
			ft.commit();
			lastFragment = fDoctor;
			messageFrameLayout.setVisibility(View.GONE);
			doctorFrameLayout.setVisibility(View.VISIBLE);
			taskFrameLayout.setVisibility(View.GONE);
			callFrameLayout.setVisibility(View.GONE);
			moreFrameLayout.setVisibility(View.GONE);
			messagesButton.setBackgroundResource(R.drawable.tab_messages);
			doctorsButton.setBackgroundResource(R.drawable.tab_doctors_press);
			tasksButton.setBackgroundResource(R.drawable.tab_tasks);
			callButton.setBackgroundResource(R.drawable.tab_call);
			moreButton.setBackgroundResource(R.drawable.tab_more);
			messageLinearLayout.setBackgroundDrawable(null);
			doctorLinearLayout
					.setBackgroundResource(R.drawable.footer_menu_bg_select);
			taskLinearLayout.setBackgroundDrawable(null);
			callLinearLayout.setBackgroundDrawable(null);
			moreLinearLayout.setBackgroundDrawable(null);
			break;
		}
		case TASK_FRAGMENT: {
			if (fMessage != null) {
				ft.hide(fMessage);
			}
			if (fDoctor != null) {
				ft.hide(fDoctor);
			}
			if (fCall != null) {
				ft.hide(fCall);
			}
			if (fMore != null) {
				ft.hide(fMore);
			}
			if (fTask == null) {
				fTask = Fragment.instantiate(this,
						TaskListActivity.TaskListFragment.class.getName());
				ft.add(R.id.fTasks, fTask);
			} else {
				ft.show(fTask);
				if (lastFragment == fTask) {
					RefreshListener f = (RefreshListener) lastFragment;
					f.refreshView();
				}
			}
			ft.commit();
			lastFragment = fTask;
			messageFrameLayout.setVisibility(View.GONE);
			doctorFrameLayout.setVisibility(View.GONE);
			taskFrameLayout.setVisibility(View.VISIBLE);
			callFrameLayout.setVisibility(View.GONE);
			moreFrameLayout.setVisibility(View.GONE);
			messagesButton.setBackgroundResource(R.drawable.tab_messages);
			doctorsButton.setBackgroundResource(R.drawable.tab_doctors);
			tasksButton.setBackgroundResource(R.drawable.tab_tasks_press);
			callButton.setBackgroundResource(R.drawable.tab_call);
			moreButton.setBackgroundResource(R.drawable.tab_more);
			messageLinearLayout.setBackgroundDrawable(null);
			doctorLinearLayout.setBackgroundDrawable(null);
			taskLinearLayout
					.setBackgroundResource(R.drawable.footer_menu_bg_select);
			callLinearLayout.setBackgroundDrawable(null);
			moreLinearLayout.setBackgroundDrawable(null);
			break;
		}
		case CALL_FRAGMENT: {
			AppSettings setting = new AppSettings(this);
			if (setting.getSettingBoolean("hasMobilePhone", true)) {
				if (fMessage != null) {
					ft.hide(fMessage);
				}
				if (fDoctor != null) {
					ft.hide(fDoctor);
				}
				if (fTask != null) {
					ft.hide(fTask);
				}
				if (fMore != null) {
					ft.hide(fMore);
				}
				if (fCall == null) {
					fCall = Fragment.instantiate(this,
							CallActivity.CallFragment.class.getName());
					Bundle args = new Bundle();
					args.putString("number", "");
					args.putBoolean("isActivity", false);
					fCall.setArguments(args);
					ft.add(R.id.fCall, fCall);
				} else {
					ft.show(fCall);
				}
				ft.commit();
				lastFragment = null;
				messageFrameLayout.setVisibility(View.GONE);
				doctorFrameLayout.setVisibility(View.GONE);
				taskFrameLayout.setVisibility(View.GONE);
				callFrameLayout.setVisibility(View.VISIBLE);
				moreFrameLayout.setVisibility(View.GONE);
				messagesButton.setBackgroundResource(R.drawable.tab_messages);
				doctorsButton.setBackgroundResource(R.drawable.tab_doctors);
				tasksButton.setBackgroundResource(R.drawable.tab_tasks);
				callButton.setBackgroundResource(R.drawable.tab_call_press);
				moreButton.setBackgroundResource(R.drawable.tab_more);
				messageLinearLayout.setBackgroundDrawable(null);
				doctorLinearLayout.setBackgroundDrawable(null);
				taskLinearLayout.setBackgroundDrawable(null);
				callLinearLayout
						.setBackgroundResource(R.drawable.footer_menu_bg_select);
				moreLinearLayout.setBackgroundDrawable(null);
			} else {
				Toast.makeText(this, R.string.no_mobile, Toast.LENGTH_LONG)
						.show();
			}
			break;
		}
		case MORE_FRAGMENT: {
			if (fMessage != null) {
				ft.hide(fMessage);
			}
			if (fDoctor != null) {
				ft.hide(fDoctor);
			}
			if (fTask != null) {
				ft.hide(fTask);
			}
			if (fCall != null) {
				ft.hide(fCall);
			}
			if (fMore == null) {
				fMore = Fragment.instantiate(this,
						MoreListActivity.MoreListFragment.class.getName());
				ft.add(R.id.fMore, fMore);
			} else {
				ft.show(fMore);
			}
			ft.commit();
			lastFragment = null;
			messageFrameLayout.setVisibility(View.GONE);
			doctorFrameLayout.setVisibility(View.GONE);
			taskFrameLayout.setVisibility(View.GONE);
			callFrameLayout.setVisibility(View.GONE);
			moreFrameLayout.setVisibility(View.VISIBLE);
			messagesButton.setBackgroundResource(R.drawable.tab_messages);
			doctorsButton.setBackgroundResource(R.drawable.tab_doctors);
			tasksButton.setBackgroundResource(R.drawable.tab_tasks);
			callButton.setBackgroundResource(R.drawable.tab_call);
			moreButton.setBackgroundResource(R.drawable.tab_more_press);
			messageLinearLayout.setBackgroundDrawable(null);
			doctorLinearLayout.setBackgroundDrawable(null);
			taskLinearLayout.setBackgroundDrawable(null);
			callLinearLayout.setBackgroundDrawable(null);
			moreLinearLayout
					.setBackgroundResource(R.drawable.footer_menu_bg_select);
			break;
		}
		}

	}

	@Override
	protected void onNewIntent(Intent intent) {
		super.onNewIntent(intent);
		setIntent(intent);
		switchFragment(MESSAGE_FRAGMENT);
		DocLog.i(TAG, "onNewIntent");
	}

	@Override
	public boolean onCreateOptionsMenu(Menu menu) {
		menu.add(0, R.id.iQuit, 0, R.string.quit);
		menu.add(0, R.id.iLogout, 1, R.string.logout);
		menu.add(0, R.id.iAbout, 3, R.string.about);
		return true;
	}

	@Override
	public boolean onOptionsItemSelected(MenuItem item) {
		AlertDialog.Builder builder = new AlertDialog.Builder(this);
		switch (item.getItemId()) {
		case R.id.iQuit:
			setResult(RESULT_CANCELED);
			finish();
			break;
		case R.id.iLogout:
			builder.setTitle(R.string.dissociate_warning_title).setMessage(
					R.string.dissociate_warning_message);
			builder.setCancelable(true);
			builder.setNegativeButton(R.string.cancel,
					new DialogInterface.OnClickListener() {
						@Override
						public void onClick(DialogInterface dialog, int which) {
							dialog.dismiss();
						}
					});
			builder.setPositiveButton(R.string.ok,
					new DialogInterface.OnClickListener() {
						@Override
						public void onClick(DialogInterface dialog, int which) {
							dialog.dismiss();
							final ProgressDialog progress = ProgressDialog
									.show(NavigationActivity.this, "",
											getString(R.string.process_text));
							NetConncet netConnect = new NetConncet(
									NavigationActivity.this,
									NetConstantValues.DEVICE_DISSOCIATE.PATH) {

								@Override
								protected void onPostExecute(String result) {
									progress.dismiss();
									NotificationManager nm = (NotificationManager) getSystemService(Context.NOTIFICATION_SERVICE);
									nm.cancel(R.string.app_name);
									AppSettings setting = new AppSettings(
											NavigationActivity.this);
									AppValues appValues = new AppValues(
											NavigationActivity.this);
									int cv = appValues.getCurrent_version();
									setting.clearPreferences();
									if (!stopService(new Intent(
											"com.doctorcom.physician.message"))) {
										GCMRegistrar
												.unregister(NavigationActivity.this);
									}
									CallBack.callerNumber = null;
									Intent intent = new Intent(
											CacheService.CACHE_SERVICE);
									intent.putExtra("cmd",
											CacheService.CACHE_CLEAN);
									startService(intent);
									appValues.setCurrent_version(cv);
									appValues.setDcomDeviceId("");
									appValues.setLogined(false);
									setting.setSettingsBoolean(
											"dcom_is_first_run", false);
									appValues.setEncrypted(true);
									CommonMoreMethods.setNewFeatureConfig(context);
									setResult(RESULT_OK);
									finish();
									startActivity(new Intent(context,
											LoginActivity.class)
											.setFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP));
								}
							};
							netConnect.execute();

						}
					});
			builder.show();
			break;
		case R.id.iRefresh:
			if (lastFragment != null) {
				RefreshListener f = (RefreshListener) lastFragment;
				f.forceRefreshView();
			}
			break;
		case R.id.iAbout:
			StringBuffer about = new StringBuffer();
			Resources res = getResources();
			try {
				PackageInfo info = getPackageManager().getPackageInfo(
						getPackageName(), 0);
				about.append(info.versionCode + "\n"
						+ res.getString(R.string.version_name_colon)
						+ info.versionName);
			} catch (NameNotFoundException ex) {
				DocLog.d(TAG, "processMenuAbout get PackageInfo error", ex);
			}
			builder.setTitle(R.string.about_doctorcom).setMessage(
					about.toString());
			builder.setCancelable(true);
			builder.setPositiveButton(R.string.ok,
					new DialogInterface.OnClickListener() {
						@Override
						public void onClick(DialogInterface dialog, int which) {
							dialog.dismiss();
						}
					});
			builder.show();
			break;
		}
		return true;
	}

	@Override
	protected void onDestroy() {
		DocLog.d(TAG, "NavigationActivity onDestroy");
		broadcastManager.unregisterReceiver(cacheCleanReceiver);
		if (mRegisterTask != null) {
			mRegisterTask.cancel(true);
		}
		GCMRegistrar.onDestroy(getApplicationContext());
		new File(getCacheDir() + AppValues.secretKey).delete();
		super.onDestroy();
	}

	private void registerGCM() {
		final String regId = GCMRegistrar.getRegistrationId(this);
		if (regId.equals("")) {
			// Automatically registers application on startup.
			GCMRegistrar.register(this, new AppValues(this).getProjectId());
		} else {
			// Device is already registered on GCM, check server.
			if (GCMRegistrar.isRegisteredOnServer(this)) {
				// Skips registration.
				DocLog.d(TAG, "already registered");
			} else {
				// Try to register again, but not in the UI thread.
				// It's also necessary to cancel the thread onDestroy(),
				// hence the use of AsyncTask instead of a raw thread.
				final Context context = this;
				mRegisterTask = new AsyncTask<Void, Void, Void>() {

					@Override
					protected Void doInBackground(Void... params) {
						boolean registered = ServerUtilities.register(context,
								regId);
						// At this point all attempts to register with the app
						// server failed, so we need to unregister the device
						// from GCM - the app will try to register again when
						// it is restarted. Note that GCM will send an
						// unregistered callback upon completion, but
						// GCMIntentService.onUnregistered() will ignore it.
						if (!registered) {
							GCMRegistrar.unregister(context);
						}
						return null;
					}

					@Override
					protected void onPostExecute(Void result) {
						mRegisterTask = null;
					}

				};
				mRegisterTask.execute(null, null, null);
			}
		}

	}

	private long exitTime = 0;

	@Override
	public void onBackPressed() {
		if ((System.currentTimeMillis() - exitTime) > 2000) {
			Toast.makeText(getApplicationContext(),
					getString(R.string.exit_affirm), Toast.LENGTH_SHORT).show();
			exitTime = System.currentTimeMillis();
		} else {
			setResult(RESULT_CANCELED);
			long max_wait_time = 5000;
			long currentTime = System.currentTimeMillis();
			while (System.currentTimeMillis() < max_wait_time + currentTime) {
				if (NetConncet.activeConnections > 0) {
					try {
						Thread.sleep(500);
						DocLog.d(TAG, "Sleep! ActiveConnections:"
								+ NetConncet.activeConnections);
					} catch (InterruptedException e) {
						// TODO Auto-generated catch block
						finish();
					}
				} else {
					break;
				}
			}
			finish();
		}
	}

	public class CacheCleanReceiver extends BroadcastReceiver {

		public final int CLEAN_DOCTOR_LIST = 1;
		public final int CLEAN_TASK_LIST = 2;
		public final int CLEAN_ALL = 3;
		public final int CLEAN_TIME = 4;
		public final int CLEAN_MESSAGE = 5;

		@Override
		public void onReceive(Context context, Intent intent) {
			FragmentTransaction ft = fm.beginTransaction();
			Fragment fMessage = fm.findFragmentById(R.id.fMessages);
			Fragment fDoctor = fm.findFragmentById(R.id.fDoctors);
			Fragment fTask = fm.findFragmentById(R.id.fTasks);
			switch (intent.getIntExtra("cmd", -1)) {
			case CLEAN_DOCTOR_LIST:
				if (fDoctor != null) {
					ft.remove(fDoctor);
				}
				ft.commitAllowingStateLoss();
				break;
			case CLEAN_TASK_LIST:
				if (fTask != null) {
					ft.remove(fTask);
				}
				ft.commitAllowingStateLoss();
				break;
			case CLEAN_TIME:
				if (fMessage != null) {
					ft.remove(fMessage);
				}
				if (fTask != null) {
					ft.remove(fTask);
				}
				ft.commitAllowingStateLoss();
				break;
			case CLEAN_MESSAGE:
				if (fMessage != null) {
					ft.remove(fMessage);
				}
				fMessage = Fragment
						.instantiate(context,
								MessageListActivity.MessageListFragment.class
										.getName());
				Bundle bundle = new Bundle();
				bundle.putBoolean("isRedeived",
						intent.getBooleanExtra("isRedeived", true));
				fMessage.setArguments(bundle);
				ft.add(R.id.fMessages, fMessage);
				ft.commitAllowingStateLoss();
				break;
			default:
				if (fMessage != null) {
					ft.remove(fMessage);
				}
				if (fDoctor != null) {
					ft.remove(fDoctor);
				}
				if (fTask != null) {
					ft.remove(fTask);
				}
				ft.commitAllowingStateLoss();
				break;
			}
		}

	}

	@Override
	public void onOrinialImageDownloadFinish(Bitmap result) {
		// show prefer logo and automatically disappear in 2 seconds
		final RelativeLayout rlPrefer = (RelativeLayout) findViewById(R.id.rlPrefer);
		if (result != null) {
			rlPrefer.setBackgroundResource(R.color.splash_color);
			ImageView ivPreferLogo = (ImageView) findViewById(R.id.ivprefer_logo);
			ivPreferLogo.setScaleType(ImageView.ScaleType.CENTER_INSIDE);
			ivPreferLogo.setImageBitmap(result);
			ScheduledExecutorService executor = Executors
					.newSingleThreadScheduledExecutor();
			executor = Executors.newSingleThreadScheduledExecutor();
			executor.schedule(new Runnable() {

				@Override
				public void run() {
					runOnUiThread(new Runnable() { // UI thread
						@Override
						public void run() {
							rlPrefer.setVisibility(View.GONE);
						}
					});
				}

			}, 2000, TimeUnit.MILLISECONDS);
			appValues.setShowPreferLogo(false);
		}
		else{
			rlPrefer.setVisibility(View.GONE);
		}
	}
}
