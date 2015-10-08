package com.doctorcom.physician.activity.message;

import java.io.File;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import android.app.Activity;
import android.app.AlertDialog;
import android.app.ProgressDialog;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.DialogInterface;
import android.content.DialogInterface.OnCancelListener;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.pm.PackageManager;
import android.content.pm.ResolveInfo;
import android.database.sqlite.SQLiteDatabase;
import android.graphics.Typeface;
import android.media.AudioManager;
import android.media.MediaPlayer;
import android.media.MediaPlayer.OnCompletionListener;
import android.os.Bundle;
import android.os.Handler;
import android.support.v4.app.Fragment;
import android.support.v4.app.FragmentActivity;
import android.support.v4.app.FragmentManager;
import android.support.v4.content.LocalBroadcastManager;
import android.telephony.PhoneStateListener;
import android.telephony.TelephonyManager;
import android.text.Html;
import android.text.Spannable;
import android.text.SpannableString;
import android.text.method.LinkMovementMethod;
import android.text.style.ClickableSpan;
import android.util.SparseArray;
import android.view.LayoutInflater;
import android.view.View;
import android.view.View.OnClickListener;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.ScrollView;
import android.widget.TableRow;
import android.widget.TextView;
import android.widget.Toast;

import com.doctorcom.android.R;
import com.doctorcom.android.document.pdf.PdfViewerActivity;
import com.doctorcom.physician.AppValues;
import com.doctorcom.physician.activity.call.CallActivity;
import com.doctorcom.physician.activity.doctor.DoctorDetailActivity;
import com.doctorcom.physician.activity.message.AttachmentsActivity.DesFilePlay;
import com.doctorcom.physician.activity.message.MessageActivity.onPlayListener;
import com.doctorcom.physician.activity.task.TaskNewActivity;
import com.doctorcom.physician.net.ImageDownload;
import com.doctorcom.physician.net.NetConstantValues;
import com.doctorcom.physician.net.http.NetConncet;
import com.doctorcom.physician.utils.AESEncryptDecrypt;
import com.doctorcom.physician.utils.AESEncryptDecrypt.AESEncryptDecryptException;
import com.doctorcom.physician.utils.CallBack;
import com.doctorcom.physician.utils.DocLog;
import com.doctorcom.physician.utils.FileUtil;
import com.doctorcom.physician.utils.JsonErrorProcess;
import com.doctorcom.physician.utils.ProgressCancelDialog;
import com.doctorcom.physician.utils.Utils;
import com.doctorcom.physician.utils.cache.Cache;
import com.doctorcom.physician.utils.cache.Cache.CacheSchema;
import com.doctorcom.physician.utils.cache.DataBaseHelper;

public class MessageDetailActivity extends FragmentActivity {

	@Override
	protected void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
		FragmentManager fm = getSupportFragmentManager();

		// Create the list fragment and add it as our sole content.
		if (fm.findFragmentById(android.R.id.content) == null) {
			MessageDetailFragment detail = new MessageDetailFragment();
			fm.beginTransaction().add(android.R.id.content, detail).commit();
		}
	}

	public static class MessageDetailFragment extends Fragment implements
			Cache.CacheFinishListener, onPlayListener {
		public interface onNeedRefreshListener {
			public void onNeedRefresh();
		}

		private final String TAG = "MessageDetailActivity";
		private boolean show = false, retryDownloadCallBack = false;
		private TextView subjectTextView, contactTextView, timeTextView,
				fromTextView;
		private Button fromButton, attachmentsButton, playButton, acceptButton,
				declineButton;
		private View rootView;
		private LinearLayout loadingLinearLayout, retryLinearLayout;
		private ScrollView scroll;
		private int position;
		private String messageId = "", refer_pdf, uuid, threadingUUID;
		private boolean isReceived;
		private boolean[] allResolved;
		private String[] allMessageSubject, allMessageIds, allThreadingUUID;
		private int[] allActionHistoryCounts;
		private boolean isResolved;
		private int actionHistoryCount;
		protected ProgressDialog progress;
		private MediaPlayer mediaPlayer;
		private AudioManager am = null;
		private TelephonyManager mTelephonyMgr = null;
		private TeleListener mTeleListener = null;
		private boolean speakOn = true;
		private List<File> desFileList;
		private AppValues appValues;
		private LinearLayout toLinear, ccLinear, contain, action_historyLinear;
		private final int REPLY = 2;
		private String fileId, fileName;
		private long fileSize;
		private ProgressBar loadingProgressBar;
		private Button resolvedButton;
		private onNeedRefreshListener refreshListener;
		private MessageResolvedReceiver resolvedReceiver;
		private LocalBroadcastManager broadcastManager;
		private String[] allReferStatus;
		private boolean[] allRefer;
		private String[] allMessageDetails;

		@Override
		public void onCreate(Bundle savedInstanceState) {
			super.onCreate(savedInstanceState);
			Bundle bundle = getArguments();
			if (bundle != null) {
				isReceived = bundle.getBoolean("received", false);
				position = bundle.getInt("position", 0);
				allMessageSubject = bundle.getStringArray("allMessageSubject");
				allMessageIds = bundle.getStringArray("allMessageIds");
				messageId = allMessageIds[position];
				allThreadingUUID = bundle.getStringArray("allThreadingUUID");
				threadingUUID = allThreadingUUID[position];
				allActionHistoryCounts = bundle
						.getIntArray("allActionHistoryCounts");
				allResolved = bundle.getBooleanArray("allResolved");
				allRefer = bundle.getBooleanArray("allRefer");
				allReferStatus = bundle.getStringArray("allReferStatus");
				allMessageDetails = bundle.getStringArray("allMessageDetails");
				
			}
		}

		@Override
		public View onCreateView(LayoutInflater inflater, ViewGroup container,
				Bundle savedInstanceState) {
			View view = inflater.inflate(R.layout.activity_message_detail,
					container, false);
			appValues = new AppValues(getActivity());
			am = (AudioManager) getActivity().getSystemService(
					Context.AUDIO_SERVICE);
			mTelephonyMgr = (TelephonyManager) getActivity().getSystemService(
					Context.TELEPHONY_SERVICE);
			// Registers a listener object to receive notification of changes in
			// specified telephony states
			mTeleListener = new TeleListener();
			mTelephonyMgr.listen(mTeleListener,
					PhoneStateListener.LISTEN_CALL_STATE);
			action_historyLinear = (LinearLayout) view
					.findViewById(R.id.msg_detail_action_history);
			setShowUI(view);
			initParams(view);
			toLinear = (LinearLayout) view.findViewById(R.id.vTo);
			ccLinear = (LinearLayout) view.findViewById(R.id.vCc);
			contain = (LinearLayout) view.findViewById(R.id.vContain);

//			getMessageBody();
			// will be recovered
			// **************************************************************
			String result = allMessageDetails[position];
			this.onCacheFinish(result, true);
			// **************************************************************
			mediaPlayer = new MediaPlayer();
			mediaPlayer.setOnCompletionListener(new OnCompletionListener() {

				@Override
				public void onCompletion(MediaPlayer mp) {
					playButton.setBackgroundResource(R.drawable.button_play);

				}

			});
			desFileList = new ArrayList<File>();
			return view;
		}

		@Override
		public void onActivityCreated(Bundle savedInstanceState) {
			super.onActivityCreated(savedInstanceState);
			broadcastManager = LocalBroadcastManager.getInstance(getActivity());
			resolvedReceiver = new MessageResolvedReceiver();
			IntentFilter filter = new IntentFilter("messageResolvedReceiver");
			broadcastManager.registerReceiver(resolvedReceiver, filter);
		}

		@Override
		public void onAttach(Activity activity) {
			super.onAttach(activity);
			refreshListener = (onNeedRefreshListener) activity;
		}

		protected void setShowUI(View view) {
			final TextView showTextView = (TextView) view
					.findViewById(R.id.tvShow);
			final LinearLayout toLinear = (LinearLayout) view
					.findViewById(R.id.llTo);
			final LinearLayout ccLinear = (LinearLayout) view
					.findViewById(R.id.llCc);
			toLinear.setVisibility(View.GONE);
			ccLinear.setVisibility(View.GONE);
			action_historyLinear.setVisibility(View.GONE);
			showTextView.setOnClickListener(new View.OnClickListener() {

				@Override
				public void onClick(View v) {
					if (show) {
						showTextView.setText(R.string.show_detail);
						toLinear.setVisibility(View.GONE);
						ccLinear.setVisibility(View.GONE);
						action_historyLinear.setVisibility(View.GONE);
					} else {
						showTextView.setText(R.string.hide_detail);
						toLinear.setVisibility(View.VISIBLE);
						ccLinear.setVisibility(View.VISIBLE);
						action_historyLinear.setVisibility(View.VISIBLE);
					}
					show = !show;

				}
			});
		}

		protected void setSubject(String subject) {
			if (subject.equals("")) {
				subject = getString(R.string.no_subject);
				subjectTextView.setTypeface(Typeface.create(Typeface.DEFAULT,
						Typeface.BOLD_ITALIC));
			}
			subjectTextView.setText(subject);

		}

		protected void initParams(View view) {
			loadingLinearLayout = (LinearLayout) view
					.findViewById(R.id.linearLoading);
			retryLinearLayout = (LinearLayout) view
					.findViewById(R.id.linearRetry);
			loadingProgressBar = (ProgressBar) view
					.findViewById(R.id.progressbar_loading);
			retryLinearLayout.setVisibility(View.GONE);
			scroll = (ScrollView) view.findViewById(R.id.scroll);
			loadingLinearLayout.setVisibility(View.VISIBLE);
			scroll.setVisibility(View.GONE);

			timeTextView = (TextView) view.findViewById(R.id.tvTime);
			fromButton = (Button) view.findViewById(R.id.btFrom);
			fromTextView = (TextView) view.findViewById(R.id.tvFrom);
			Button yesButton = (Button) view.findViewById(R.id.button_yes);
			yesButton.setOnClickListener(new View.OnClickListener() {

				@Override
				public void onClick(View v) {
					loadingProgressBar.setVisibility(View.VISIBLE);
					retryLinearLayout.setVisibility(View.GONE);
					getMessageBody();

				}
			});
			Button noButton = (Button) view.findViewById(R.id.button_no);
			noButton.setOnClickListener(new View.OnClickListener() {

				@Override
				public void onClick(View v) {
					closeActivity();

				}
			});
			resolvedButton = (Button) view.findViewById(R.id.button_resolved);
			resolvedButton.setOnClickListener(new View.OnClickListener() {

				@Override
				public void onClick(View v) {
					final Context mContext = getActivity();
					final ProgressDialog progress = ProgressDialog.show(
							mContext, "", getString(R.string.process_text));
					HashMap<String, String> params = new HashMap<String, String>();
					params.put(
							NetConstantValues.MESSAGE_STATUS_UPDATE.PARAM_RESOLVED,
							String.valueOf(!isResolved));
					final boolean targetResolvedstatus = !isResolved;
					NetConncet conncet = new NetConncet(getActivity(),
							NetConstantValues.MESSAGE_STATUS_UPDATE
									.getPath(messageId), params) {

						@Override
						protected void onPostExecute(String result) {
							super.onPostExecute(result);
							progress.dismiss();
							if (JsonErrorProcess
									.checkJsonError(result, context)) {
								isResolved = targetResolvedstatus;
								setResolvedStstus(context, isResolved);
								DocLog.i("MessageResolvedReceiver",
										"resolve status is changed:"
												+ isResolved);
								refreshListener.onNeedRefresh();
								// changeMessageResolvedStatus(mContext,
								// messageId, isResolved);
								Toast.makeText(mContext,
										R.string.action_successed,
										Toast.LENGTH_SHORT).show();
							}
						}

					};
					conncet.execute();
				}
			});
		}

		void setResolvedStstus(Context context, boolean resolved) {
			if (resolved) {
				resolvedButton
						.setBackgroundResource(R.drawable.button_resolved);
				resolvedButton.setText(R.string.resolved);
				resolvedButton.setTextColor(context.getResources().getColor(
						R.color.white));
			} else {
				resolvedButton
						.setBackgroundResource(R.drawable.button_unresolved);
				resolvedButton.setText(R.string.unresolved);
				resolvedButton.setTextColor(context.getResources().getColor(
						R.color.message_time));
			}

		}

		public static void changeMessageResolvedStatus(final Context mContext,
				final String messageId, final boolean isResolved) {
			new Thread() {

				@Override
				public void run() {
					AppValues appValues = new AppValues(mContext);
					HashMap<String, String> params = new HashMap<String, String>();
					params.put(
							NetConstantValues.MESSAGING_MESSAGE_BODY.PARAM_SECRET,
							appValues.getSecret());
					Cache.updateMessageStatus(
							mContext,
							appValues.getServerURL()
									+ NetConstantValues.APP_URL
									+ NetConstantValues.MESSAGING_MESSAGE_BODY
											.getPath(messageId),
							Cache.pair2String(params), isResolved);
				}

			}.start();

		}

		protected void getMessageBody() {
			HashMap<String, String> params = new HashMap<String, String>();
			params.put(NetConstantValues.MESSAGING_MESSAGE_BODY.PARAM_SECRET,
					appValues.getSecret());
			Cache cache = new Cache(getActivity(), NetConncet.HTTP_POST);
			cache.setCacheType(Cache.CACHE_MESSAGE_BODY);
			cache.useCache(
					this,
					NetConstantValues.MESSAGING_MESSAGE_BODY.getPath(messageId),
					NetConstantValues.MESSAGING_MESSAGE_BODY.PATH + "*/",
					params);

		}

		private void cleanMessageBodyAndRefresh() {
			final Handler handler = new Handler();
			final DataBaseHelper helper = new DataBaseHelper(getActivity());
			final SQLiteDatabase db = helper.getWritableDatabase();
			final AESEncryptDecrypt decrypt = new AESEncryptDecrypt(
					AppValues.aeskey, getActivity().getCacheDir()
							.getAbsolutePath() + AppValues.secretKey);
			final Runnable runnable = new Runnable() {

				@Override
				public void run() {
					DocLog.d(TAG, "getMessageBody");
					getMessageBody();
				}
			};

			new Thread() {

				@Override
				public void run() {
					String decryptUrl;
					try {
						decryptUrl = decrypt.encrypt(appValues.getServerURL()
								+ NetConstantValues.APP_URL
								+ NetConstantValues.MESSAGING_MESSAGE_BODY
										.getPath(messageId));
						db.delete(CacheSchema.TABLE_NAME, "category = 4 and "
								+ CacheSchema.URL + " = ?",
								new String[] { decryptUrl });
						DocLog.d(TAG, "delete message detail");
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

		private boolean shouldForceRefresh(boolean isCache, String referStatus) {
			if (!isCache)
				return false;
			if (allResolved[position] == isResolved
					&& allActionHistoryCounts[position] == actionHistoryCount) {
				if(allRefer[position]){
					if(referStatus.equalsIgnoreCase(allReferStatus[position]))
						return false;
				}
				else{
					return false;
				}
			}			
			return true;
		}

		@Override
		public void onCacheFinish(String result, boolean isCache) {
			final Context context = getActivity();
			if (context == null)
				return;
			try {
				JSONObject jsonObj = new JSONObject(result);
				if (!jsonObj.isNull("errno")) {
					handleError();
					return;
				}
				final JSONObject jData = jsonObj.getJSONObject("data");
				isResolved = jData.getBoolean("resolution_flag");
				actionHistoryCount = jData.getInt("action_history_count");
				String referStatus= "";
				if(allRefer[position]){
					referStatus = jData.getJSONObject("refer").getString("status");
				}
				if (shouldForceRefresh(isCache, referStatus)) {
					cleanMessageBodyAndRefresh();
				} else {
					setResolvedStstus(context, isResolved);
					// set time
					timeTextView
							.setText(Utils.getDateTimeFormat(
									jData.getLong("send_timestamp") * 1000,
									appValues.getTimeFormat(),
									appValues.getTimezone()));
					String messageType = jData.getString("message_type");
					// set from
					final int fromID = jData.getJSONObject("sender").getInt(
							"id");
					final String fromName = jData.getJSONObject("sender")
							.getString("name");
					if (fromID == 0) {
						// system message
						fromTextView.setVisibility(View.VISIBLE);
						fromTextView.setText(getString(R.string.system));
						fromButton.setVisibility(View.GONE);
					} else {
						fromButton.setVisibility(View.VISIBLE);
						fromButton.setText(fromName);
						fromTextView.setVisibility(View.GONE);
						fromButton
								.setOnClickListener(new View.OnClickListener() {

									@Override
									public void onClick(View v) {
										Intent intent = new Intent(
												getActivity(),
												DoctorDetailActivity.class);
										intent.putExtra("userId", fromID);
										intent.putExtra("name", fromName);
										startActivity(intent);

									}
								});
					}
					// set recipient
					toLinear.removeAllViews();
					JSONArray recipients = jData.getJSONArray("recipients");
					for (int i = 0, len = recipients.length(); i < len; i++) {
						JSONObject recipient = recipients.getJSONObject(i);
						final String name = recipient.getString("name");
						final int recipientId = recipient.getInt("id");
						Button bName = new Button(context);
						bName.setText(name);
						bName.setBackgroundResource(R.drawable.contact_selector);
						bName.setTextColor(getResources().getColor(
								R.color.contact_color));
						LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
								LinearLayout.LayoutParams.WRAP_CONTENT,
								LinearLayout.LayoutParams.WRAP_CONTENT);
						lp.setMargins(5, 0, 3, 0);
						bName.setLayoutParams(lp);
						toLinear.addView(bName);
						bName.setOnClickListener(new View.OnClickListener() {

							@Override
							public void onClick(View v) {
								Intent intent = new Intent(context,
										DoctorDetailActivity.class);
								intent.putExtra("userId", recipientId);
								intent.putExtra("name", name);
								startActivity(intent);

							}
						});
					}
					// set cc
					ccLinear.removeAllViews();
					JSONArray ccs = jData.getJSONArray("ccs");
					for (int i = 0, len = ccs.length(); i < len; i++) {
						JSONObject cc = ccs.getJSONObject(i);
						final String name = cc.getString("name");
						final int recipientId = cc.getInt("id");
						Button bName = new Button(context);
						bName.setText(name);
						bName.setBackgroundResource(R.drawable.contact_selector);
						bName.setTextColor(getResources().getColor(
								R.color.contact_color));
						LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
								LinearLayout.LayoutParams.WRAP_CONTENT,
								LinearLayout.LayoutParams.WRAP_CONTENT);
						lp.setMargins(5, 0, 3, 0);
						bName.setLayoutParams(lp);
						ccLinear.addView(bName);
						bName.setOnClickListener(new View.OnClickListener() {

							@Override
							public void onClick(View v) {
								Intent intent = new Intent(context,
										DoctorDetailActivity.class);
								intent.putExtra("userId", recipientId);
								intent.putExtra("name", name);
								startActivity(intent);

							}
						});
					}

					// set action_historys
					action_historyLinear.removeAllViews();
					JSONArray action_historys = jData
							.getJSONArray("action_history");
					for (int i = 0, len = action_historys.length(); i < len; i++) {
						JSONObject action_history = action_historys
								.getJSONObject(i);
						final String content = action_history
								.getString("content");
						final Long timestamp = action_history
								.getLong("timestamp");
						final String time = Utils.getDateTimeFormat(
								timestamp * 1000, appValues.getTimeFormat(),
								appValues.getTimezone());
						final String action_history_entry = content + " "
								+ time;
						TextView tv = new TextView(context);
						tv.setText(action_history_entry);
						tv.setTextColor(getResources().getColor(
								R.color.message_time));
						action_historyLinear.addView(tv);
					}

					LayoutInflater mInflater = LayoutInflater.from(context);
					if (rootView != null) {
						contain.removeViewAt(4);
					}
					if (jData.isNull("refer")) {
						if (messageType.equalsIgnoreCase("ans")) {
							rootView = mInflater.inflate(
									R.layout.activity_message_detail_vm_ans,
									contain, true);

						} else if (messageType.equalsIgnoreCase("vm")) {
							rootView = mInflater.inflate(
									R.layout.activity_message_detail_vm_ans,
									contain, true);

						} else {
							rootView = mInflater.inflate(
									R.layout.activity_message_detail_normal,
									contain, true);

						}
					} else {
						rootView = mInflater.inflate(
								R.layout.activity_message_detail_refer,
								contain, true);
					}
					Button forwardButton = (Button) rootView
							.findViewById(R.id.btForward);
					forwardButton
							.setOnClickListener(new View.OnClickListener() {

								@Override
								public void onClick(View v) {
									Intent intent = new Intent(context,
											MessageNewActivity.class);
									intent.putExtra("type",
											MessageNewActivity.FORWARD_MESSAGE);
									intent.putExtra("subject",
											allMessageSubject[position]);
									intent.putExtra("body", jData.toString());
									intent.putExtra("messageId", messageId);
									startActivity(intent);
									getActivity().overridePendingTransition(
											R.anim.up, R.anim.hold);
								}
							});

					Button taskButton = (Button) rootView
							.findViewById(R.id.btFollowUp);
					taskButton.setOnClickListener(new View.OnClickListener() {

						@Override
						public void onClick(View v) {
							Intent intent = new Intent(context,
									TaskNewActivity.class);
							intent.putExtra("description",
									allMessageSubject[position]);
							try {
								intent.putExtra("note", jData.getString("body"));
							} catch (JSONException e) {
								intent.putExtra("note", "");
							}
							intent.putExtra("isMessageTask", true);
							startActivity(intent);
							getActivity().overridePendingTransition(R.anim.up,
									R.anim.hold);

						}
					});
					if (jData.isNull("refer")) {
						// message

						subjectTextView = (TextView) rootView
								.findViewById(R.id.tvSubject);
						contactTextView = (TextView) rootView
								.findViewById(R.id.tvContent);
						setSubject(allMessageSubject[position]);
						// set body
						final SpannableString ss = new SpannableString(
								jData.getString("body"));
						SparseArray<String> sa = Utils
								.getNumbers(ss.toString());
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
						contactTextView
								.setOnLongClickListener(new View.OnLongClickListener() {

									@Override
									public boolean onLongClick(View v) {
										AlertDialog.Builder builder = new AlertDialog.Builder(
												context);
										builder.setTitle(R.string.options);
										builder.setItems(
												R.array.message_item_select,
												new DialogInterface.OnClickListener() {
													public void onClick(
															DialogInterface dialog,
															int item) {
														if (item == 0) {
															Utils utils = new Utils(
																	context);
															utils.copy(ss
																	.toString());
														}
													}
												});
										AlertDialog alert = builder.create();
										alert.setCanceledOnTouchOutside(true);
										alert.show();
										return true;
									}
								});
						if (isReceived) {

						} else {
							forwardButton.setVisibility(View.GONE);
						}

						if (messageType.equalsIgnoreCase("ans")
								|| messageType.equalsIgnoreCase("vm")) {
							if (messageType.equalsIgnoreCase("vm")) {
								forwardButton.setVisibility(View.GONE);
							}
							// set attachment
							JSONArray attachments = jData
									.getJSONArray("attachments");
							TextView voiceTextView = (TextView) rootView
									.findViewById(R.id.tvVoice);
							Button speakSwichButton = (Button) rootView
									.findViewById(R.id.btSpeak_on_off);
							playButton = (Button) rootView
									.findViewById(R.id.btPlay);
							if (attachments.length() == 1) {
								JSONObject jsonOpt = attachments
										.optJSONObject(0);
								fileId = jsonOpt.getString("id");
								fileName = jsonOpt.getString("filename");
								fileSize = jsonOpt.getLong("filesize");
								voiceTextView.setText(fileName);
								playButton
										.setOnClickListener(new AttachmentPlay(
												fileId, fileName, fileSize));
								am.setSpeakerphoneOn(true);
								am.setMode(AudioManager.MODE_NORMAL);
								getActivity().setVolumeControlStream(
										AudioManager.STREAM_MUSIC);
								speakSwichButton
										.setOnClickListener(new View.OnClickListener() {

											@Override
											public void onClick(View v) {
												speakOn = !speakOn;
												if (speakOn) {
													am.setSpeakerphoneOn(true);
													am.setMode(AudioManager.MODE_NORMAL);
													getActivity()
															.setVolumeControlStream(
																	AudioManager.STREAM_MUSIC);
													v.setBackgroundResource(R.drawable.icon_speakes_on);
												} else {
													am.setSpeakerphoneOn(false);
													am.setMode(AudioManager.MODE_IN_CALL);
													v.setBackgroundResource(R.drawable.icon_speaker_off);
												}

											}
										});
							} else {
								// error
								voiceTextView.setVisibility(View.GONE);
								playButton.setVisibility(View.GONE);
								speakSwichButton.setVisibility(View.GONE);
							}

							// set callback
							Button callbackButton = (Button) rootView
									.findViewById(R.id.btCallBack);
							TextView callBackTextView = (TextView) rootView
									.findViewById(R.id.tvCallBack);
							final String callBackNumber = jData
									.getString("callback_number");
							callBackTextView.setText(callBackNumber);
							if (jData.getBoolean("callback_available")
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
						} else {
							Button replyButton = (Button) rootView
									.findViewById(R.id.btReply);
							attachmentsButton = (Button) rootView
									.findViewById(R.id.btAttachments);
							if (fromID == 0 || !isReceived) {
								forwardButton.setVisibility(View.GONE);
								replyButton.setVisibility(View.GONE);

							} else {
								replyButton
										.setOnClickListener(new View.OnClickListener() {

											@Override
											public void onClick(View v) {
												Intent intent = new Intent(
														context,
														MessageNewActivity.class);
												intent.putExtra("userId",
														fromID);
												intent.putExtra("name",
														fromName);
												intent.putExtra(
														"subject",
														allMessageSubject[position]);
												intent.putExtra(
														"type",
														MessageNewActivity.REPLY_MESSAGE);
												intent.putExtra(
														"threadingUUID",
														threadingUUID);
												getActivity()
														.startActivityForResult(
																intent, REPLY);
												getActivity()
														.overridePendingTransition(
																R.anim.up,
																R.anim.hold);

											}
										});
							}
							// set attachments
							final JSONArray attachments = jData
									.getJSONArray("attachments");
							int len = attachments.length();
							if (len == 0) {
								attachmentsButton.setVisibility(View.GONE);
							} else {
								attachmentsButton.setVisibility(View.VISIBLE);
								attachmentsButton.setText(getResources()
										.getString(R.string.view_attachments)
										+ "(" + String.valueOf(len) + ")");
								attachmentsButton
										.setOnClickListener(new View.OnClickListener() {

											@Override
											public void onClick(View v) {
												JSONObject obj = new JSONObject();
												try {
													obj.putOpt("attachments",
															attachments);
													viewAttachments(obj
															.toString());
												} catch (JSONException e) {
													DocLog.e(TAG,
															"JSONException", e);
												}

											}
										});
							}
						}

					} else {
						// refer
						// rootView =
						// mInflater.inflate(R.layout.activity_message_detail_refer,
						// contain, true);
						attachmentsButton = (Button) rootView
								.findViewById(R.id.btAttachments);
						// set attachments
						final JSONArray attachments = jData
								.getJSONArray("attachments");
						int len = attachments.length();
						if (len == 0) {
							attachmentsButton.setVisibility(View.GONE);
						} else {
							attachmentsButton.setVisibility(View.VISIBLE);
							attachmentsButton.setText(getResources().getString(
									R.string.view_attachments)
									+ "(" + String.valueOf(len) + ")");
							attachmentsButton
									.setOnClickListener(new View.OnClickListener() {

										@Override
										public void onClick(View v) {
											JSONObject obj = new JSONObject();
											try {
												obj.putOpt("attachments",
														attachments);
												viewAttachments(obj.toString());
											} catch (JSONException e) {
												DocLog.e(TAG, "JSONException",
														e);
											}

										}
									});
						}
						JSONObject jRefer = jData.getJSONObject("refer");
						// set logo
						String practicePhoto = "";
						if (!jRefer.isNull("practice_logo")) {
							practicePhoto = jRefer.getString("practice_logo");
							ImageView practicePhotoImageView = (ImageView) rootView
									.findViewById(R.id.ivPracticePhoto);
							ImageDownload download = new ImageDownload(context,
									messageId, practicePhotoImageView, -1);
							download.execute(appValues.getServerURL()
									+ practicePhoto);
						}
						// set referring physician
						TextView rfTextView = (TextView) rootView
								.findViewById(R.id.tvRP);
						rfTextView.setText(jRefer
								.getString("referring_physician"));
						// set physician phone
						TextView ppTextView = (TextView) rootView
								.findViewById(R.id.tvPP);
						final String pp = jRefer
								.getString("physician_phone_number");
						ppTextView.setText(Html
								.fromHtml("<font color='blue'><u>" + pp
										+ "</u></font>"));
						if (!pp.equals("")) {
							ppTextView
									.setOnClickListener(new View.OnClickListener() {

										@Override
										public void onClick(View v) {
											callC2Cnumber(context, pp);

										}
									});
						}
						// set office phone
						TextView opTextView = (TextView) rootView
								.findViewById(R.id.tvOP);
						final String op = jRefer
								.getString("practice_phone_number");
						opTextView.setText(Html
								.fromHtml("<font color='blue'><u>" + op
										+ "</u></font>"));
						if (!op.equals("")) {
							opTextView
									.setOnClickListener(new View.OnClickListener() {

										@Override
										public void onClick(View v) {
											callC2Cnumber(context, op);

										}
									});
						}
						// set practice name
						TextView pnTextView = (TextView) rootView
								.findViewById(R.id.tvPN);
						pnTextView.setText(jRefer.getString("practice_name"));
						// set city
						TextView cityTextView = (TextView) rootView
								.findViewById(R.id.tvCity);
						cityTextView.setText(jRefer.getString("practice_city"));
						// set state
						TextView stateTextView = (TextView) rootView
								.findViewById(R.id.tvState);
						stateTextView.setText(jRefer
								.getString("practice_state"));
						// set address
						TextView addressTextView = (TextView) rootView
								.findViewById(R.id.tvAddress);
						addressTextView.setText(jRefer
								.getString("practice_address"));
						// set patient name
						TextView panTextView = (TextView) rootView
								.findViewById(R.id.tvPaN);
						panTextView.setText(jRefer.getString("patient_name"));
						// set gender
						TextView genderTextView = (TextView) rootView
								.findViewById(R.id.tvGender);
						genderTextView.setText(jRefer.getString("gender"));
						// set birth
						TextView birthTextView = (TextView) rootView
								.findViewById(R.id.tvBirth);
						birthTextView
								.setText(jRefer.getString("date_of_birth"));
						// set phone
						TextView phoneTextView = (TextView) rootView
								.findViewById(R.id.tvPhone);
						final String p = jRefer.getString("phone_number");
						phoneTextView.setText(Html
								.fromHtml("<font color='blue'><u>" + p
										+ "</u></font>"));
						if (!p.equals("")) {
							phoneTextView
									.setOnClickListener(new View.OnClickListener() {

										@Override
										public void onClick(View v) {
											callC2Cnumber(context, p);

										}
									});
						}
						// set alternative phone
						TextView apTextView = (TextView) rootView
								.findViewById(R.id.tvAP);
						final String ap = jRefer
								.getString("alternative_phone_number");
						apTextView.setText(Html
								.fromHtml("<font color='blue'><u>" + ap
										+ "</u></font>"));
						if (!ap.equals("")) {
							apTextView
									.setOnClickListener(new View.OnClickListener() {

										@Override
										public void onClick(View v) {
											callC2Cnumber(context, ap);

										}
									});
						}
						// set MRN
						TextView tvMrn = (TextView) rootView
								.findViewById(R.id.tvMrn);
						tvMrn.setText(jRefer.getString("refer_mrn"));
						
						// set SSN
						TextView tvSsn = (TextView) rootView
								.findViewById(R.id.tvSsn);
						tvSsn.setText(jRefer.getString("refer_ssn"));
						
						// set Refer Address
						TextView tvReferAddress = (TextView) rootView
								.findViewById(R.id.tvReferAddress);
						tvReferAddress.setText(jRefer.getString("refer_address"));
						
						// set Prior Authorization Number
						TextView tvPAuthNo = (TextView) rootView
								.findViewById(R.id.tvPAuthNo);
						tvPAuthNo.setText(jRefer.getString("prior_authorization_number"));
						
						// set Other Authorization
						TextView tvOtherAuth = (TextView) rootView
								.findViewById(R.id.tvOtherAuth);
						tvOtherAuth.setText(jRefer.getString("other_authorization"));
						
						// set Internal Tracking Number
						TextView tvITrackNo = (TextView) rootView
								.findViewById(R.id.tvITrackNo);
						tvITrackNo.setText(jRefer.getString("internal_tracking_number"));
						
						// set insurance
						TextView piTextView = (TextView) rootView
								.findViewById(R.id.tvPI);
						piTextView.setText(jRefer.getString("insurance_name"));
						TextView pidTextVIew = (TextView) rootView
								.findViewById(R.id.tvPID);
						pidTextVIew.setText(jRefer.getString("insurance_id"));
						String si = jRefer
								.getString("secondary_insurance_name");
						String sid = jRefer.getString("secondary_insurance_id");
						String ti = jRefer.getString("tertiary_insurance_name");
						String tid = jRefer.getString("tertiary_insurance_id");
						TextView siTextView = (TextView) rootView
								.findViewById(R.id.tvSI);
						TextView sidTextView = (TextView) rootView
								.findViewById(R.id.tvSID);
						TextView tiTextView = (TextView) rootView
								.findViewById(R.id.tvTI);
						TextView tidTextView = (TextView) rootView
								.findViewById(R.id.tvTID);
						TextView piTitleTextView = (TextView) rootView
								.findViewById(R.id.tvPI_title);
						TextView pidTitleTextView = (TextView) rootView
								.findViewById(R.id.tvPID_title);
						TableRow siTableRow = (TableRow) rootView
								.findViewById(R.id.trSI);
						TableRow siiTableRow = (TableRow) rootView
								.findViewById(R.id.trSID);
						TableRow tiTableRow = (TableRow) rootView
								.findViewById(R.id.trTI);
						TableRow tidTableRow = (TableRow) rootView
								.findViewById(R.id.trTID);
						if (!si.equals("")) {
							piTitleTextView.setText(R.string.primary_insurance);
							pidTitleTextView
									.setText(R.string.primary_insurance_id);
							siTextView.setText(si);
							sidTextView.setText(sid);
							if (ti.equals("")) {
								tiTableRow.setVisibility(View.GONE);
								tidTableRow.setVisibility(View.GONE);
							} else {
								tiTextView.setText(ti);
								tidTextView.setText(tid);
							}
						} else {
							siTableRow.setVisibility(View.GONE);
							siiTableRow.setVisibility(View.GONE);
							tiTableRow.setVisibility(View.GONE);
							tidTableRow.setVisibility(View.GONE);
						}
						/*
						// set ICD Code
						String icd = jRefer.getString("icd_code");
						if(!icd.equals("")){
						TextView tvICD = (TextView) rootView
								.findViewById(R.id.tvIcdCode);
						tvICD.setText(icd);
						}
						else{
							rootView.findViewById(R.id.iCDRow).setVisibility(View.GONE);
						}
						
						//set OPS Code
						String ops = jRefer.getString("ops_code");
						if(!ops.equals("")){
						TextView tvOpsCode = (TextView) rootView
								.findViewById(R.id.tvOpsCode);
						tvOpsCode.setText(ops);
						}
						else{
							rootView.findViewById(R.id.oPSRow).setVisibility(View.GONE);
						}
						
						// set medication list
						String medicationList = jRefer.getString("medication_list");
						if(!medicationList.equals("")){
						TextView tvMedicationList = (TextView) rootView
								.findViewById(R.id.tvMedicationList);
						tvMedicationList.setText(medicationList);
						}
						else{
							rootView.findViewById(R.id.medicationListRow).setVisibility(View.GONE);
						}
						
						String language = jsonObj.getJSONObject("settings").getString("FORCED_LANGUAGE_CODE");
						if(language.equals("en-us")){
							rootView.findViewById(R.id.oPSRow).setVisibility(View.GONE);
							rootView.findViewById(R.id.medicationListRow).setVisibility(View.GONE);
						}
						*/
						// set Note
						TextView tvNotes = (TextView) rootView
								.findViewById(R.id.tvNotes);
						final SpannableString noteStr = new SpannableString(
								jRefer.getString("notes"));
						SparseArray<String> noteStrArr = Utils
								.getNumbers(noteStr.toString());
						len = noteStrArr.size();
						for (int i = 0; i < len; i++) {
							int k = noteStrArr.keyAt(i);
							String v = noteStrArr.get(k);
							MyURLSpan myURLSpan = new MyURLSpan(context, v);
							noteStr.setSpan(myURLSpan, k, k + v.length(),
									Spannable.SPAN_EXCLUSIVE_EXCLUSIVE);
						}
						tvNotes.setText(noteStr);
						tvNotes.setMovementMethod(LinkMovementMethod
								.getInstance());
						tvNotes
								.setOnLongClickListener(new View.OnLongClickListener() {

									@Override
									public boolean onLongClick(View v) {
										AlertDialog.Builder builder = new AlertDialog.Builder(
												context);
										builder.setTitle(R.string.options);
										builder.setItems(
												R.array.message_item_select,
												new DialogInterface.OnClickListener() {
													public void onClick(
															DialogInterface dialog,
															int item) {
														if (item == 0) {
															Utils utils = new Utils(
																	context);
															utils.copy(noteStr
																	.toString());
														}
													}
												});
										AlertDialog alert = builder.create();
										alert.setCanceledOnTouchOutside(true);
										alert.show();
										return true;
									}
								});
						// set reason
						TextView reasonTextView = (TextView) rootView
								.findViewById(R.id.tvReason);
						final SpannableString ss = new SpannableString(
								jData.getString("body"));
						SparseArray<String> sa = Utils
								.getNumbers(ss.toString());
						len = sa.size();
						for (int i = 0; i < len; i++) {
							int k = sa.keyAt(i);
							String v = sa.get(k);
							MyURLSpan myURLSpan = new MyURLSpan(context, v);
							ss.setSpan(myURLSpan, k, k + v.length(),
									Spannable.SPAN_EXCLUSIVE_EXCLUSIVE);
						}
						reasonTextView.setText(ss);
						reasonTextView.setMovementMethod(LinkMovementMethod
								.getInstance());
						reasonTextView
								.setOnLongClickListener(new View.OnLongClickListener() {

									@Override
									public boolean onLongClick(View v) {
										AlertDialog.Builder builder = new AlertDialog.Builder(
												context);
										builder.setTitle(R.string.options);
										builder.setItems(
												R.array.message_item_select,
												new DialogInterface.OnClickListener() {
													public void onClick(
															DialogInterface dialog,
															int item) {
														if (item == 0) {
															Utils utils = new Utils(
																	context);
															utils.copy(ss
																	.toString());
														}
													}
												});
										AlertDialog alert = builder.create();
										alert.setCanceledOnTouchOutside(true);
										alert.show();
										return true;
									}
								});
						uuid = jRefer.getString("uuid");
						refer_pdf = jRefer.getString("refer_pdf");

						acceptButton = (Button) rootView
								.findViewById(R.id.btAccept);
						acceptButton.setOnClickListener(new Accept());
						declineButton = (Button) rootView
								.findViewById(R.id.btDecline);
						declineButton.setOnClickListener(new Decline());
						String status = jRefer.getString("status");
						if (!status.equalsIgnoreCase("NO") || !isReceived) {
							acceptButton.setVisibility(View.GONE);
							declineButton.setVisibility(View.GONE);
						}
						Button pdfButton = (Button) rootView
								.findViewById(R.id.btPDFDown);
						pdfButton.setOnClickListener(new PDFDownload());
					}
					// load success
					loadingLinearLayout.setVisibility(View.GONE);
					scroll.setVisibility(View.VISIBLE);
				}

			} catch (JSONException e) {
				handleError();
				DocLog.e(TAG, "JSONException", e);
			}

		}

		protected void viewAttachments(String attachments) {
			Intent intent = new Intent(getActivity(), AttachmentsActivity.class);
			intent.putExtra("attachments", attachments);
			intent.putExtra("messageId", messageId);
			startActivity(intent);
		}

		protected void handleError() {
			loadingProgressBar.setVisibility(View.GONE);
			retryLinearLayout.setVisibility(View.VISIBLE);
		}

		class Accept implements OnClickListener {

			@Override
			public void onClick(View v) {
				final Context mContext = getActivity();
				AlertDialog.Builder builder = new AlertDialog.Builder(mContext);
				builder.setTitle(R.string.accept_refer)
						.setPositiveButton(R.string.yes,
								new DialogInterface.OnClickListener() {
									public void onClick(DialogInterface dialog,
											int id) {
										progress = ProgressDialog
												.show(getActivity(),
														"",
														getString(R.string.process_text));
										HashMap<String, String> params = new HashMap<String, String>();
										params.put(
												NetConstantValues.MESSAGE_REFER.STATUS,
												"AC");
										final NetConncet netConncet = new NetConncet(
												mContext,
												NetConstantValues.MESSAGE_REFER
														.getPath(uuid), params) {

											@Override
											protected void onPostExecute(
													String result) {
												super.onPostExecute(result);
												progress.dismiss();
												if (JsonErrorProcess
														.checkJsonError(result,
																mContext)) {
													Toast.makeText(
															context,
															R.string.refer_accept_success,
															Toast.LENGTH_LONG)
															.show();
													new Thread() {

														@Override
														public void run() {
															super.run();
															HashMap<String, String> ps = new HashMap<String, String>();
															ps.put(NetConstantValues.MESSAGING_MESSAGE_BODY.PARAM_SECRET,
																	appValues
																			.getSecret());
															Cache.updateRefer(
																	mContext,
																	appValues
																			.getServerURL()
																			+ NetConstantValues.APP_URL
																			+ NetConstantValues.MESSAGING_MESSAGE_BODY
																					.getPath(messageId),
																	Cache.pair2String(ps),
																	"AC");
														}

													}.start();
													acceptButton
															.setVisibility(View.GONE);
													declineButton
															.setVisibility(View.GONE);
													getActivity().setResult(
															RESULT_OK);
												}
											}
										};
										netConncet.execute();
									}
								})
						.setNegativeButton(R.string.no,
								new DialogInterface.OnClickListener() {
									public void onClick(DialogInterface dialog,
											int id) {
										dialog.cancel();
									}
								});
				AlertDialog alert = builder.create();
				alert.show();
			}
		}

		class Decline implements OnClickListener {

			@Override
			public void onClick(View v) {
				final Context mContext = getActivity();
				LayoutInflater factory = LayoutInflater.from(mContext);
				final View textEntryView = factory.inflate(
						R.layout.alert_dialog_text_entry, null);

				AlertDialog.Builder builder = new AlertDialog.Builder(mContext);
				builder.setTitle(R.string.decline_refer)
						.setView(textEntryView)
						.setPositiveButton(R.string.yes,
								new DialogInterface.OnClickListener() {
									public void onClick(DialogInterface dialog,
											int id) {
										HashMap<String, String> params = new HashMap<String, String>();
										params.put(
												NetConstantValues.MESSAGE_REFER.STATUS,
												"RE");
										params.put(
												NetConstantValues.MESSAGE_REFER.REFUSE_REASON,
												((EditText) textEntryView
														.findViewById(R.id.etReason))
														.getText().toString());
										progress = ProgressDialog
												.show(getActivity(),
														"",
														getString(R.string.process_text));
										final NetConncet netConncet = new NetConncet(
												mContext,
												NetConstantValues.MESSAGE_REFER
														.getPath(uuid), params) {

											@Override
											protected void onPostExecute(
													String result) {
												super.onPostExecute(result);
												progress.dismiss();
												if (JsonErrorProcess
														.checkJsonError(result,
																mContext)) {
													Toast.makeText(
															mContext,
															R.string.refer_decline_success,
															Toast.LENGTH_LONG)
															.show();
													new Thread() {

														@Override
														public void run() {
															super.run();
															HashMap<String, String> ps = new HashMap<String, String>();
															ps.put(NetConstantValues.MESSAGING_MESSAGE_BODY.PARAM_SECRET,
																	appValues
																			.getSecret());
															Cache.updateRefer(
																	mContext,
																	appValues
																			.getServerURL()
																			+ NetConstantValues.APP_URL
																			+ NetConstantValues.MESSAGING_MESSAGE_BODY
																					.getPath(messageId),
																	Cache.pair2String(ps),
																	"RE");
														}

													}.start();
													acceptButton
															.setVisibility(View.GONE);
													declineButton
															.setVisibility(View.GONE);
													getActivity().setResult(
															RESULT_OK);
												}
											}
										};
										netConncet.execute();
									}
								})
						.setNegativeButton(R.string.no,
								new DialogInterface.OnClickListener() {
									public void onClick(DialogInterface dialog,
											int id) {
										dialog.cancel();
									}
								});
				AlertDialog alert = builder.create();
				alert.show();

			}

		}

		class PDFDownload implements OnClickListener {
			@Override
			public void onClick(View v) {
				Context mContext = getActivity();
				String appPath = FileUtil.getAppPath(mContext);
				if (appPath == null) {
					Toast.makeText(mContext, R.string.sdcard_unavailable,
							Toast.LENGTH_LONG).show();
					return;
				}
				File file = new File(appPath, refer_pdf + ".pdf");
				if (!file.exists()) {
					procressDownload(refer_pdf, ".pdf", -1);
				} else {
					startMediaPlayer(file.getAbsolutePath());
				}

			}
		}

		@Override
		public void onPlay(String result) {
			final Context mContext = getActivity();
			try {
				JSONObject obj = new JSONObject(result);
				File originalFilePath = new File(obj.getString("data"));
				if (!obj.isNull("errno")) {
					retryDownload(originalFilePath);
					if (Utils.isDeviceDissociated(result)) {
						Toast.makeText(mContext, obj.getString("descr"),
								Toast.LENGTH_LONG).show();
						closeActivity();
					}
				} else {
					play(new File(obj.getString("data")));
				}
			} catch (JSONException e) {
				DocLog.e(TAG, "JSONException", e);
				String appPath = FileUtil.getAppPath(mContext);
				if (appPath != null) {
					retryDownload(new File(appPath + "/des_tag_" + fileId
							+ fileName));
				} else {
					Toast.makeText(mContext, R.string.sdcard_unavailable,
							Toast.LENGTH_LONG).show();
				}
			}

		}

		private void startMediaPlayer(String encryptFileName) {
			final Context mContext = getActivity();
			final File encryptFilePath = new File(encryptFileName);
			final String originalFileName = encryptFilePath.getParent()
					.toString() + "/des_tag_" + encryptFilePath.getName();
			final File originalFilePath = new File(originalFileName);
			if (originalFilePath.exists()) {
				play(originalFilePath);
			} else {
				final ProgressDialog progress = ProgressDialog.show(mContext,
						"", getString(R.string.decrypting_file));
				final DesFilePlay desFilePlay = new DesFilePlay(
						encryptFileName, originalFileName, mContext) {

					@Override
					protected void onPostExecute(final String result) {
						progress.dismiss();
						if (result == null || result.equals("")) {
							retryDownload(originalFilePath);
						} else {
							play(originalFilePath);
						}
					}

				};

				progress.setCancelable(true);
				progress.setOnCancelListener(new OnCancelListener() {

					@Override
					public void onCancel(DialogInterface dialog) {
						if (!desFilePlay.isCancelled()) {
							desFilePlay.cancel(true);
						}
					}
				});
				desFilePlay.execute();
			}

		}

		private void play(File originalFilePath) {
			desFileList.add(originalFilePath);
			String mime = FileUtil.getMIMEType(originalFilePath);
			if (mime.contains("pdf")) {
				Intent openIntent = new Intent(getActivity(),
						PdfViewerActivity.class);
				openIntent.putExtra("pdf_document",
						originalFilePath.getAbsolutePath());
				startActivity(openIntent);
			} else if (mime.contains("audio")) {
				try {
					if (mediaPlayer.isPlaying()) {
						mediaPlayer.stop();
						playButton
								.setBackgroundResource(R.drawable.button_play);
					} else {
						playButton
								.setBackgroundResource(R.drawable.button_stop);
						mediaPlayer.reset();
						mediaPlayer.setDataSource(originalFilePath
								.getAbsolutePath());
						mediaPlayer.prepare();
						mediaPlayer.start();

					}
				} catch (Exception e) {
					DocLog.d(TAG, "Exception", e);
					retryDownload(originalFilePath);
				}
			} else {
				Intent fileOpenIntent = FileUtil
						.getOpenFileIntent(originalFilePath);
				PackageManager packageManager = getActivity()
						.getPackageManager();
				List<ResolveInfo> activities = packageManager
						.queryIntentActivities(fileOpenIntent, 0);
				boolean isIntentSafe = activities.size() > 0;
				if (isIntentSafe) {
					startActivity(fileOpenIntent);
				} else {
					Toast.makeText(getActivity(),
							R.string.not_support_file_type, Toast.LENGTH_LONG)
							.show();
				}
			}
		}

		private void retryDownload(File originalFilePath) {
			if (originalFilePath.exists())
				originalFilePath.delete();
			File encryptFilePath = new File(originalFilePath.getParent(),
					originalFilePath.getName().substring("des_tag_".length()));
			if (encryptFilePath.exists())
				encryptFilePath.delete();
			// bad file, download again
			if (retryDownloadCallBack) {
				AlertDialog.Builder builder = new AlertDialog.Builder(
						getActivity());
				builder.setTitle(R.string.error)
						.setMessage(R.string.load_failed_retry)
						.setPositiveButton(R.string.yes,
								new DialogInterface.OnClickListener() {

									@Override
									public void onClick(DialogInterface dialog,
											int which) {
										dialog.dismiss();
										retryDownloadCallBack = false;
										procressDownload(fileId, fileName,
												fileSize);
									}
								})
						.setNegativeButton(R.string.no,
								new DialogInterface.OnClickListener() {

									@Override
									public void onClick(DialogInterface dialog,
											int which) {
										dialog.dismiss();

									}
								}).show();
			} else {
				retryDownloadCallBack = true;
				procressDownload(fileId, fileName, fileSize);
			}

		}

		class AttachmentPlay implements OnClickListener {
			private String fileId, fileName;
			private long fileSize;

			public AttachmentPlay(String id, String name, long size) {
				fileId = id;
				fileName = name;
				fileSize = size;
			}

			@Override
			public void onClick(View v) {
				String appPath = FileUtil.getAppPath(getActivity());
				if (appPath == null) {
					Toast.makeText(getActivity(), R.string.sdcard_unavailable,
							Toast.LENGTH_LONG).show();
					return;
				}
				File file = new File(appPath, fileId + fileName);
				if (file.exists()) {
					startMediaPlayer(file.getAbsolutePath());
				} else {
					procressDownload(fileId, fileName, fileSize);
				}

			}

		}

		protected void procressDownload(String id, String name, long size) {
			FragmentManager fm = getActivity().getSupportFragmentManager();
			ProgressCancelDialog pd = new ProgressCancelDialog();
			Bundle args = new Bundle();
			args.putString("messageId", messageId);
			args.putString("attchmentId", id);
			args.putString("fileName", name);
			args.putLong("fileSize", size);
			pd.setArguments(args);
			pd.show(fm, TAG);
		}

		@Override
		public void onDestroy() {
			broadcastManager.unregisterReceiver(resolvedReceiver);
			super.onDestroy();
			for (int i = 0, len = desFileList.size(); i < len; i++) {
				desFileList.get(i).delete();
			}
			am.setMode(AudioManager.MODE_NORMAL);
			if (mediaPlayer != null) {
				mediaPlayer.release();
				mediaPlayer = null;
			}
			if (mTeleListener != null)
				mTelephonyMgr.listen(mTeleListener,
						PhoneStateListener.LISTEN_NONE);
		}

		public void closeActivity() {
			getActivity().finish();
		}

		class TeleListener extends PhoneStateListener {

			@Override
			public void onCallStateChanged(int state, String incomingNumber) {
				super.onCallStateChanged(state, incomingNumber);
				switch (state) {
				case TelephonyManager.CALL_STATE_IDLE: {
					DocLog.d(TAG, "CALL_STATE_IDLE" + incomingNumber);
					break;
				}
				case TelephonyManager.CALL_STATE_OFFHOOK: {
					DocLog.d(TAG, "CALL_STATE_OFFHOOK" + incomingNumber);
					if (mediaPlayer != null && mediaPlayer.isPlaying()) {
						mediaPlayer.stop();
						playButton
								.setBackgroundResource(R.drawable.button_play);
					}
					break;
				}
				case TelephonyManager.CALL_STATE_RINGING: {
					DocLog.d(TAG, "CALL_STATE_RINGING" + incomingNumber);
					if (mediaPlayer != null && mediaPlayer.isPlaying()) {
						mediaPlayer.stop();
						playButton
								.setBackgroundResource(R.drawable.button_play);
					}
					break;
				}
				default:
					break;
				}
			}

		}

		private static void callC2Cnumber(final Context ctx,
				final String phoneNumber) {
			AlertDialog.Builder builder = new AlertDialog.Builder(ctx);
			builder.setMessage(
					String.format(
							ctx.getResources().getString(
									R.string.call_c2c_number), phoneNumber))
					.setCancelable(false)
					.setPositiveButton(
							R.string.yes,
							new android.content.DialogInterface.OnClickListener() {
								public void onClick(
										android.content.DialogInterface dialog,
										int id) {
									Intent intent = new Intent(ctx,
											CallActivity.class);
									intent.putExtra("number",
											Utils.getNumberOfPhone(phoneNumber));
									ctx.startActivity(intent);
									dialog.dismiss();
								}
							})
					.setNegativeButton(
							R.string.no,
							new android.content.DialogInterface.OnClickListener() {
								public void onClick(
										android.content.DialogInterface dialog,
										int id) {
									dialog.dismiss();
								}
							});
			AlertDialog alert = builder.create();
			alert.show();
		}

		static class MyURLSpan extends ClickableSpan {

			private String phoneNumber;
			private Context ctx;

			public MyURLSpan(Context ctx, String p) {
				phoneNumber = p;
				this.ctx = ctx;
			}

			@Override
			public void onClick(View widget) {
				callC2Cnumber(ctx, phoneNumber);
			}

		}

		class MessageResolvedReceiver extends BroadcastReceiver {

			@Override
			public void onReceive(Context context, Intent intent) {
				String message = intent.getStringExtra("message");
				if (message != null) {
					try {
						JSONObject jsonObject = new JSONObject(message);
						String uuid = jsonObject.getString("uuid");
						boolean updateResolved = jsonObject
								.getBoolean("resolve");
						DocLog.i("MessageResolvedReceiver",
								"received resolve status is :" + updateResolved);
						if (messageId.equals(uuid)) {
							if (updateResolved != isResolved) {
								DocLog.d("MessageResolvedReceiver",
										"resolved status changed");
								isResolved = updateResolved;
								if (MessageDetailFragment.this.isResumed())
									setResolvedStstus(context, updateResolved);
							}
						}
					} catch (JSONException e) {
						DocLog.e("MessageResolvedReceiver", "JSONException", e);
					}
				}
			}
		}
	}

}
