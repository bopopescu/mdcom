package com.doctorcom.physician.activity.message;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.IntentFilter;
import android.graphics.drawable.BitmapDrawable;
import android.os.Bundle;
import android.support.v4.app.FragmentActivity;
import android.support.v4.app.FragmentManager;
import android.support.v4.app.ListFragment;
import android.support.v4.content.LocalBroadcastManager;
import android.view.LayoutInflater;
import android.view.Menu;
import android.view.MenuInflater;
import android.view.View;
import android.view.View.OnClickListener;
import android.view.View.OnLongClickListener;
import android.view.ViewGroup;
import android.widget.AdapterView;
import android.widget.AdapterView.OnItemLongClickListener;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ListView;
import android.widget.PopupWindow;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;

import com.doctorcom.android.R;
import com.doctorcom.physician.AppValues;
import com.doctorcom.physician.activity.invitation.InvitationReceivedActivity;
import com.doctorcom.physician.activity.main.NavigationActivity.RefreshListener;
import com.doctorcom.physician.activity.task.TaskNewActivity;
import com.doctorcom.physician.net.NetConstantValues;
import com.doctorcom.physician.net.http.NetConncet;
import com.doctorcom.physician.utils.DocLog;
import com.doctorcom.physician.utils.JsonErrorProcess;
import com.doctorcom.physician.utils.Utils;
import com.doctorcom.physician.utils.cache.Cache;

public class MessageListActivity extends FragmentActivity {

	@Override
	protected void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
		FragmentManager fm = getSupportFragmentManager();

		// Create the list fragment and add it as our sole content.
		if (fm.findFragmentById(android.R.id.content) == null) {
			MessageListFragment list = new MessageListFragment();
			fm.beginTransaction().add(android.R.id.content, list).commit();
		}
	}

	public static class MessageListFragment extends ListFragment implements
			Cache.CacheFinishListener, RefreshListener,
			CommonMessageMethods.DeleteMessageListener {
		private final String TAG = "MessageListFragment";
		private String id;
		private long to_timestamp;
		private int receivedMessageAdd;
		private int mQueryCount;
		private long checkTime;
		private ArrayList<ReceivedMessageItem> receivedMessageList;
		private ArrayList<SentMessageItem> sentMessageList;
		private TextView messageTitle;
		private LinearLayout llContent, llLoading;
		private ListView mListView;
		private View loadMoreView;
		private ProgressBar refreshProgressBar;
		private boolean isLoadMore;
		private ReceivedMessageAdapter receivedAdapter;
		private SentMessageAdapter sentAdapter;
		private String path = NetConstantValues.MESSAGING_LIST_RECEIVED.PATH;
		private PopupWindow popupWindow;
		private boolean isReceived = true;
		private NewMessageReceiver messageReceiver;
		private boolean receivedCached = false, sentCached = false;
		private Context mContext;
		private Activity mActivity;

		private final int PAGE_COUNT = AppValues.PAGE_COUNT;
		private final int ACTIVITY_DELETE_MESSAGE = 1;
		private final int ACTIVITY_NEW_MESSAGE = 2;
		private final int REPLY = 3;
		private TextView badgeView;
		private boolean isReceivedListBody;
		private boolean isSentListBody;
		HashMap<String, String> params;

		private LocalBroadcastManager broadcastManager;

		private String resolveTimestamp = null;
		private int requestCount = 0;
		private boolean isGettingData;
		private List<String> ids;

		@Override
		public void onCreate(Bundle savedInstanceState) {
			super.onCreate(savedInstanceState);
			setHasOptionsMenu(true);
			Bundle bundle = getArguments();
			if (bundle != null) {
				isReceived = bundle.getBoolean("isRedeived");
			}
		}

		@Override
		public View onCreateView(LayoutInflater inflater, ViewGroup container,
				Bundle savedInstanceState) {
			DocLog.d(TAG, "MessageListFragment onCreateView");
			View view = inflater.inflate(R.layout.fragment_message_list,
					container, false);
			llContent = (LinearLayout) view.findViewById(R.id.llContent);
			llLoading = (LinearLayout) view.findViewById(R.id.llLoading);
			messageTitle = (TextView) view.findViewById(R.id.tvDC);
			refreshProgressBar = (ProgressBar) view
					.findViewById(R.id.pbRefresh);
			Button selectButton = (Button) view.findViewById(R.id.btSelect);
			selectButton.setOnClickListener(new View.OnClickListener() {

				@Override
				public void onClick(View v) {
					getPopupWindow();
					popupWindow.showAsDropDown(v, 0, -15);

				}
			});
			Button newButton = (Button) view.findViewById(R.id.btNew);
			newButton.setOnClickListener(new View.OnClickListener() {

				@Override
				public void onClick(View v) {
					Intent intent = new Intent(mContext,
							MessageNewActivity.class);
					startActivityForResult(intent, ACTIVITY_NEW_MESSAGE);
					mActivity.overridePendingTransition(R.anim.up, R.anim.hold);
				}
			});
			badgeView = (TextView) getActivity().findViewById(
					R.id.textview_badge);
			badgeView.setVisibility(View.GONE);
			return view;
		}

		@Override
		public void onActivityCreated(Bundle savedInstanceState) {
			super.onActivityCreated(savedInstanceState);
			DocLog.d(TAG, "MessageListFragment onActivityCreated");
			mContext = getActivity();
			mActivity = getActivity();
			broadcastManager = LocalBroadcastManager.getInstance(mContext);
			ids = new ArrayList<String>();
			messageReceiver = new NewMessageReceiver();
			IntentFilter filter = new IntentFilter("newMessageReceiver");
			broadcastManager.registerReceiver(messageReceiver, filter);
			mListView = getListView();
			mListView.setOnItemLongClickListener(new OnItemLongClickListener() {

				@Override
				public boolean onItemLongClick(AdapterView<?> paramAdapterView,
						View paramView, int paramInt, long paramLong) {
					AlertDialog.Builder builder = new AlertDialog.Builder(
							mContext);
					AlertDialog alert = builder.create();
					alert.setCanceledOnTouchOutside(true);
					alert.show();
					alert.getWindow().setContentView(R.layout.chat_menu_dialog);
					View rootView = alert.getWindow().findViewById(
							R.id.ll_chat_root_container);
					setChildViewsShow(rootView, paramInt);
					setChildViewsClickListener(rootView, paramInt, alert);
					return true;
				}

			});
			Cache.resetReceivedMessageList();
			getInvitation();
		}

		private void setChildViewsShow(View parentView, int position) {
			String refer;
			if (isReceived) {
				ReceivedMessageItem item = receivedAdapter.getItem(position);
				refer = item.getRefer();
				if (item.getSender().getId() == 0) {
					parentView.findViewById(R.id.fl_chat_retry_container)
							.setVisibility(View.GONE);
					if (!item.getMessage_type().equalsIgnoreCase("ANS")) {
						parentView.findViewById(R.id.fl_chat_forward_container)
								.setVisibility(View.GONE);
					}
				}
			} else {
				SentMessageItem item = sentAdapter.getItem(position);
				refer = item.getRefer();
				parentView.findViewById(R.id.fl_chat_retry_container)
						.setVisibility(View.GONE);
				parentView.findViewById(R.id.fl_chat_forward_container)
						.setVisibility(View.GONE);
			}

			if (refer != null && !refer.equals("")) {
				parentView.findViewById(R.id.fl_chat_retry_container)
						.setVisibility(View.GONE);
				parentView.findViewById(R.id.fl_chat_delete_container)
						.setVisibility(View.GONE);
			}

		}

		private void setChildViewsClickListener(View parentView, int position,
				final AlertDialog alertDialog) {
			String refer;
			final String subject;
			final String body;
			final String messageId;
			if (isReceived) {
				final int fromID;
				final String fromName;
				final String threadingUUID;
				final String jsonStrMessageDetail;
				ReceivedMessageItem item = receivedAdapter.getItem(position);
				subject = item.getSubject();
				fromID = item.getSender().getId();
				fromName = item.getSender().getName();
				threadingUUID = item.getThreadingUUID();
				refer = item.getRefer();
				messageId = item.getId();
				body = item.getBody().getBody();
				String str = item.getBody().getJsonStrMessageDetail();
				try {
					str = new JSONObject(str).getString("data");
				} catch (JSONException e) {
					// TODO Auto-generated catch block
					DocLog.e(TAG, "JSONException", e);
					Toast.makeText(mContext, R.string.get_data_error,
							Toast.LENGTH_SHORT).show();
				}
				jsonStrMessageDetail = str;

				// set reply button onclick listener
				Button btReply = (Button) parentView
						.findViewById(R.id.chat_reply);
				btReply.setOnClickListener(new OnClickListener() {

					@Override
					public void onClick(View v) {
						Intent intent = new Intent(mContext,
								MessageNewActivity.class);
						intent.putExtra("userId", fromID);
						intent.putExtra("name", fromName);
						intent.putExtra("subject", subject);
						intent.putExtra("type",
								MessageNewActivity.REPLY_MESSAGE);
						intent.putExtra("threadingUUID", threadingUUID);
						startActivityForResult(intent, REPLY);
						getActivity().overridePendingTransition(R.anim.up,
								R.anim.hold);
						alertDialog.dismiss();

					}
				});

				// set forward button onclick listener
				Button btForward = (Button) parentView
						.findViewById(R.id.chat_forward);
				btForward.setOnClickListener(new OnClickListener() {

					@Override
					public void onClick(View v) {
						Intent intent = new Intent(mContext,
								MessageNewActivity.class);
						intent.putExtra("type",
								MessageNewActivity.FORWARD_MESSAGE);
						intent.putExtra("subject", subject);
						intent.putExtra("body", jsonStrMessageDetail);
						intent.putExtra("messageId", messageId);
						startActivity(intent);
						getActivity().overridePendingTransition(R.anim.up,
								R.anim.hold);
						alertDialog.dismiss();
					}
				});
			} else {
				SentMessageItem item = sentAdapter.getItem(position);
				refer = item.getRefer();
				messageId = item.getId();
				subject = item.getSubject();
				body = item.getBody().getBody();
			}

			if (refer == null || refer.equals("")) {
				Button btDelete = (Button) parentView
						.findViewById(R.id.chat_delete);
				btDelete.setOnClickListener(new OnClickListener() {

					@Override
					public void onClick(View v) {
						AlertDialog.Builder builder = new AlertDialog.Builder(
								mContext);
						builder.setMessage(R.string.delete_message_warning)
								.setCancelable(false)
								.setPositiveButton(
										R.string.yes,
										new android.content.DialogInterface.OnClickListener() {
											public void onClick(
													android.content.DialogInterface dialog,
													int id) {

												DocLog.d(TAG, "delete message");
												CommonMessageMethods
														.deleteMessage(
																messageId,
																mContext,
																MessageListFragment.this);
											}
										})
								.setNegativeButton(
										R.string.no,
										new android.content.DialogInterface.OnClickListener() {
											public void onClick(
													android.content.DialogInterface dialog,
													int id) {
											}
										});
						AlertDialog alert = builder.create();
						alert.show();
						alertDialog.dismiss();
					}
				});
			}

			Button btFollowUp = (Button) parentView
					.findViewById(R.id.chat_follow_up);
			btFollowUp.setOnClickListener(new OnClickListener() {

				@Override
				public void onClick(View v) {
					Intent intent = new Intent(mContext, TaskNewActivity.class);
					intent.putExtra("description", subject);
					intent.putExtra("note", body);
					intent.putExtra("isMessageTask", true);
					startActivity(intent);
					getActivity().overridePendingTransition(R.anim.up,
							R.anim.hold);
					alertDialog.dismiss();
				}
			});

			Button btCancel = (Button) parentView
					.findViewById(R.id.chat_cancel);
			btCancel.setOnClickListener(new OnClickListener() {

				@Override
				public void onClick(View v) {
					alertDialog.dismiss();
				}
			});

		}

		@Override
		public void onStart() {
			DocLog.d(TAG, "MessageListFragment onStart");
			super.onStart();
		}

		@Override
		public void onResume() {
			super.onResume();
			init();
			getData();
			DocLog.d(TAG, "MessageListFragment onResume");
		}

		@Override
		public void onPause() {
			super.onPause();
			DocLog.d(TAG, "MessageListFragment onPause");
		}

		@Override
		public void onStop() {
			DocLog.d(TAG, "MessageListFragment onStop");
			super.onStop();
			if (isReceived) {
				receivedAdapter.clean();
				receivedAdapter = null;
			}
		}

		@Override
		public void onDestroy() {
			DocLog.d(TAG, "MessageListFragment onDestroy");
			broadcastManager.unregisterReceiver(messageReceiver);
			super.onDestroy();
		}

		protected void init() {
			if (null != receivedAdapter) {
				if (isReceived)
					receivedAdapter.clean();
			}
			receivedAdapter = new ReceivedMessageAdapter(mContext);
			sentAdapter = new SentMessageAdapter(mContext);
			receivedMessageList = new ArrayList<ReceivedMessageItem>();
			sentMessageList = new ArrayList<SentMessageItem>();
			isLoadMore = false;
			to_timestamp = 0L;
			setReceivedMessageAdd(0);
			setmQueryCount(0);
			checkTime = 0;
			requestCount = 0;
			id = "";
			if (isReceived) {
				messageTitle.setText(R.string.received);
				path = NetConstantValues.MESSAGING_LIST_RECEIVED.PATH;
			} else {
				messageTitle.setText(R.string.sent);
				path = NetConstantValues.MESSAGING_LIST_SENT.PATH;
			}
		}

		protected void getData() {
			isGettingData = true;
			refreshProgressBar.setVisibility(View.VISIBLE);
			String toTime = String.valueOf(to_timestamp);
			Cache cache = new Cache(mContext, NetConncet.HTTP_POST);
			params = new HashMap<String, String>();
			params.put(NetConstantValues.MESSAGING_LIST_RECEIVED.PARAM_COUNT,
					String.valueOf(PAGE_COUNT));
			params.put(NetConstantValues.MESSAGING_LIST_RECEIVED.PARAM_TO,
					toTime);
			params.put(NetConstantValues.MESSAGING_LIST_RECEIVED.PARAM_FROM,
					"0");
			params.put(
					NetConstantValues.MESSAGING_LIST_RECEIVED.PARAM_EXCLUDE_ID,
					id);
			params.put(NetConstantValues.THREADING.PARAM_IS_THREADING,
					String.valueOf(true));
			cache.setHowSearch(Cache.SEARCH_MEMORY_ONLY);
			cache.useCache(this, path, null, params);
		}

		private void getReceivedListBody() {
			isReceivedListBody = true;
			Context context = null;
			if (this != null)
				context = this.getActivity();
			else
				return;
			if (null != context)
				context = context.getApplicationContext();
			else
				return;
			HashMap<String, String> params = new HashMap<String, String>();
			String strIds = "";
			for (int i = 0; i < ids.size(); i++) {
				String id = ids.get(i);
				strIds += id + ",";
			}
			if (ids.size() > 0)
				strIds = strIds.substring(0, strIds.length() - 1);
			// will be recovered
			// **************************************************************
			/*
			 * params.put(NetConstantValues.RECEIVED_LIST_BODY.IDS, strIds);
			 * Cache cache = new Cache(context, NetConncet.HTTP_POST);
			 * cache.setHowSearch(Cache.SEARCH_MEMORY_ONLY);
			 * cache.useCache(this, NetConstantValues.RECEIVED_LIST_BODY.PATH,
			 * null, params);
			 */
			// **************************************************************

			// imitational codes
			// **************************************************************
			onCacheFinish(strIds, true);
			// **************************************************************
		}

		private void getSentListBody() {
			isSentListBody = true;
			Context context = null;
			if (this != null)
				context = this.getActivity();
			else
				return;
			if (null != context)
				context = context.getApplicationContext();
			else
				return;
			HashMap<String, String> params = new HashMap<String, String>();
			String strIds = "";
			for (int i = 0; i < ids.size(); i++) {
				String id = ids.get(i);
				strIds += id + ",";
			}
			strIds = strIds.substring(0, strIds.length() - 1);

			// will be recovered
			// **************************************************************
			/*
			 * params.put(NetConstantValues.SENT_LIST_BODY.IDS, strIds); Cache
			 * cache = new Cache(context, NetConncet.HTTP_POST);
			 * cache.setHowSearch(Cache.SEARCH_MEMORY_ONLY);
			 * cache.useCache(this, NetConstantValues.SENT_LIST_BODY.PATH, null,
			 * params);
			 */
			// **************************************************************

			// imitational codes
			// **************************************************************
			onCacheFinish(strIds, true);
			// **************************************************************
		}

		@Override
		public void onCacheFinish(String result, boolean isCache) {
			if (isReceivedListBody && !isGettingData) {
				if (!isReceived)
					return;
				isReceivedListBody = false;
				// will be recovered
				// **************************************************************

				// JSONObject jsonObj;
				// try {
				// jsonObj = new JSONObject(result);
				//
				// if (!jsonObj.isNull("errno")) {
				// Toast.makeText(getActivity(),
				// jsonObj.getString("descr"), Toast.LENGTH_SHORT)
				// .show();
				// if (requestCount < 3) {
				// requestCount++;
				// this.getReceivedListBody();
				// }
				// return;
				// }
				// JSONObject jsonSettings = jsonObj.getJSONObject("settings");
				// JSONArray jsonArr = jsonObj.getJSONObject("data")
				// .getJSONArray("messages");
				// int length = jsonArr.length();
				// ArrayList<ReceivedMessageItem.Body> list = new
				// ArrayList<ReceivedMessageItem.Body>();
				// for (int i = 0; i < length; i++) {
				// String jsonStrMessageDetailData = jsonArr.getString(i);
				// JSONObject jsonObjMessageDetail = new JSONObject();
				// jsonObjMessageDetail.put("settings", jsonSettings);
				// jsonObjMessageDetail.put("data",
				// jsonStrMessageDetailData);
				// String id = jsonArr.getJSONObject(i).getString("id");
				// String body = jsonArr.getJSONObject(i)
				// .getString("body");
				// JSONArray attachmentsjson = jsonArr.getJSONObject(i)
				// .getJSONArray("attachments");
				// ReceivedMessageItem.Attachment[] attachments = new
				// ReceivedMessageItem.Attachment[attachmentsjson
				// .length()];
				// for (int j = 0; i < attachments.length; j++) {
				// attachments[j].setFilename(attachmentsjson
				// .getJSONObject(j).getString("filename"));
				// attachments[j].setFilesize(attachmentsjson
				// .getJSONObject(j).getLong("filesize"));
				// attachments[j].setId(attachmentsjson.getJSONObject(
				// j).getString("id"));
				// }
				// String jsonStrMessageDetail = jsonObjMessageDetail
				// .toString();
				// ReceivedMessageItem.Body itemBody = new
				// ReceivedMessageItem.Body();
				// itemBody.setAttachments(attachments);
				// itemBody.setBody(body);
				// itemBody.setId(id);
				// itemBody.setJsonStrMessageDetail(jsonStrMessageDetail);
				// list.add(itemBody);
				// }
				// receivedAdapter.setMessageBody(list);
				// receivedAdapter.notifyDataSetChanged();
				// requestCount = 0;
				// } catch (JSONException e) { // TODO Auto-generated catch
				// block
				// if (requestCount < 3) {
				// requestCount++;
				// this.getReceivedListBody();
				// }
				// DocLog.e(TAG, "JSONException", e);
				// }

				// **************************************************************

				// imitational codes
				// **************************************************************
				ArrayList<ReceivedMessageItem.Body> list = new ArrayList<ReceivedMessageItem.Body>();
				String[] strIds = result.split(",");
				for (String id : strIds) {
					String body1 = "Please call: 8005555125. Way back in the late 1950s, at the tender age"
							+ " of 11, Peter Lynch started caddying at Brae Burn"
							+ " Country Club in Newton, Mass. \"It was better than"
							+ " a paper route, and much more lucrative,\" the Fidelity"
							+ " vice chairman recalls. He kept it up during the summers"
							+ " for almost a decade. \"You get to know the course and can"
							+ " give the players advice about how to approach various holes\"";
					String body2 = "hello world!";
					String body3 = "Nice to meet you! Thank you";
					String body4 = "Way back in the late 1950s, at the tender age"
							+ " of 11, Peter Lynch started caddying at Brae Burn";
					String body5 = "Way back in the late 1950s, at the tender age"
							+ " of 11, Peter Lynch started caddying at Brae Burn"
							+ " Country Club in Newton, Mass. \"It was better than";
					String[] bodys = new String[] { body1, body2, body3, body4,
							body5 };
					int ran = (int) (Math.random() * 5);
					ReceivedMessageItem.Attachment[] attachments = new ReceivedMessageItem.Attachment[1];
					attachments[0] = new ReceivedMessageItem.Attachment();
					attachments[0].setId("28515fb563704c469e9bc359d66747f9");
					attachments[0].setFilename("call_from_6617480240.mp3");
					attachments[0].setFilesize(43050);
					ReceivedMessageItem.Body itemBody = new ReceivedMessageItem.Body();
					itemBody.setAttachments(attachments);
					if (ran < bodys.length)
						itemBody.setBody(bodys[0]);
					else
						itemBody.setBody(bodys[0]);
					itemBody.setId(id);
					list.add(itemBody);
				}
				receivedAdapter.setMessageBody(list);
				receivedAdapter.notifyDataSetChanged();
				// **************************************************************
			} else if (isSentListBody && !isGettingData) {
				if (isReceived)
					return;
				isSentListBody = false;
				// will be recovered
				// **************************************************************

				// JSONObject jsonObj;
				// try {
				// jsonObj = new JSONObject(result);
				//
				// if (!jsonObj.isNull("errno")) {
				// Toast.makeText(getActivity(),
				// jsonObj.getString("descr"), Toast.LENGTH_SHORT)
				// .show();
				// if (requestCount < 3) {
				// requestCount++;
				// this.getSentListBody();
				// }
				// return;
				// }
				// JSONObject jsonSettings = jsonObj.getJSONObject("settings");
				// JSONArray jsonArr = jsonObj.getJSONObject("data")
				// .getJSONArray("messages");
				// int length = jsonArr.length();
				// ArrayList<SentMessageItem.Body> list = new
				// ArrayList<SentMessageItem.Body>();
				// for (int i = 0; i < length; i++) {
				// String jsonStrMessageDetailData = jsonArr.getString(i);
				// JSONObject jsonObjMessageDetail = new JSONObject();
				// jsonObjMessageDetail.put("settings", jsonSettings);
				// jsonObjMessageDetail.put("data",
				// jsonStrMessageDetailData);
				// String id = jsonArr.getJSONObject(i).getString("id");
				// String body = jsonArr.getJSONObject(i)
				// .getString("body");
				// JSONArray attachmentsjson = jsonArr.getJSONObject(i)
				// .getJSONArray("attachments");
				// ReceivedMessageItem.Attachment[] attachments = new
				// ReceivedMessageItem.Attachment[attachmentsjson
				// .length()];
				// for (int j = 0; i < attachments.length; j++) {
				// attachments[j].setFilename(attachmentsjson
				// .getJSONObject(j).getString("filename"));
				// attachments[j].setFilesize(attachmentsjson
				// .getJSONObject(j).getLong("filesize"));
				// attachments[j].setId(attachmentsjson.getJSONObject(
				// j).getString("id"));
				// }
				// String jsonStrMessageDetail = jsonObjMessageDetail
				// .toString();
				// SentMessageItem.Body itemBody = new SentMessageItem.Body();
				// itemBody.setAttachments(attachments);
				// itemBody.setBody(body);
				// itemBody.setId(id);
				// itemBody.setJsonStrMessageDetail(jsonStrMessageDetail);
				// list.add(itemBody);
				// }
				// sentAdapter.setThreadingBody(list);
				//
				// sentAdapter.notifyDataSetChanged();
				// requestCount = 0;
				// } catch (JSONException e) {
				// if (requestCount < 3) {
				// requestCount++;
				// this.getSentListBody();
				// }
				// DocLog.e(TAG, "JSONException", e);
				// }

				// **************************************************************

				// imitational codes
				// **************************************************************
				ArrayList<SentMessageItem.Body> list = new ArrayList<SentMessageItem.Body>();
				String[] strIds = result.split(",");
				for (String id : strIds) {
					String body1 = "Way back in the late 1950s, at the tender age"
							+ " of 11, Peter Lynch started caddying at Brae Burn"
							+ " Country Club in Newton, Mass. \"It was better than"
							+ " a paper route, and much more lucrative,\" the Fidelity"
							+ " vice chairman recalls. He kept it up during the summers"
							+ " for almost a decade. \"You get to know the course and can"
							+ " give the players advice about how to approach various holes\"";
					String body2 = "hello world!";
					String body3 = "Nice to meet you! Thank you";
					String body4 = "Way back in the late 1950s, at the tender age"
							+ " of 11, Peter Lynch started caddying at Brae Burn";
					String body5 = "Way back in the late 1950s, at the tender age"
							+ " of 11, Peter Lynch started caddying at Brae Burn"
							+ " Country Club in Newton, Mass. \"It was better than";
					String[] bodys = new String[] { body1, body2, body3, body4,
							body5 };
					int ran = (int) (Math.random() * 5);
					ReceivedMessageItem.Attachment[] attachments = new ReceivedMessageItem.Attachment[1];
					attachments[0] = new ReceivedMessageItem.Attachment();
					attachments[0].setId("28515fb563704c469e9bc359d66747f9");
					attachments[0].setFilename("call_from_6617480240.mp3");
					attachments[0].setFilesize(43050);
					SentMessageItem.Body itemBody = new SentMessageItem.Body();
					itemBody.setAttachments(attachments);
					if (ran < bodys.length)
						itemBody.setBody(bodys[0]);
					else
						itemBody.setBody(bodys[0]);
					itemBody.setId(id);
					list.add(itemBody);
				}
				sentAdapter.setThreadingBody(list);
				sentAdapter.notifyDataSetChanged();
				// **************************************************************

			} else {
				llLoading.setVisibility(View.GONE);
				llContent.setVisibility(View.VISIBLE);
				refreshProgressBar.setVisibility(View.GONE);
				receivedMessageList.clear();
				sentMessageList.clear();
				if (isCache) {
					if (isReceived) {
						receivedCached = true;
					} else {
						sentCached = true;
					}
					updateData(result);
				} else {
					if (JsonErrorProcess.checkJsonError(result, mContext)) {
						updateData(result);
					} else {
						if (isLoadMore) {
							addFooterView();
						} else {
							if (isReceived) {
								if (!receivedCached) {
									setListAdapter(null);
								}
							} else {
								if (!sentCached) {
									setListAdapter(null);
								}
							}
						}
					}
				}
			}

		}

		public void updateData(String result) {
			if (ids == null)
				ids = new ArrayList<String>();
			ids.clear();
			if (isReceived) {
				try {
					JSONObject jsonObj = new JSONObject(result);
					setBadgeNumber(jsonObj.getJSONObject("data").getInt(
							"unread_message_count"));
					JSONArray jsonArr = jsonObj.getJSONObject("data")
							.getJSONArray("messages");
					int length = jsonArr.length();
					setReceivedMessageAdd(length);
					setmQueryCount(jsonObj.getJSONObject("data").getInt(
							"query_count"));
					for (int i = 0; i < length; i++) {
						ReceivedMessageItem item = new ReceivedMessageItem();
						ReceivedMessageItem.Sender sender = new ReceivedMessageItem.Sender();
						JSONObject jsonOpt = jsonArr.optJSONObject(i);
						item.setId(jsonOpt.getString("id"));
						ids.add(jsonOpt.getString("id"));
						sender.setName(jsonOpt.getJSONObject("sender")
								.getString("name"));
						sender.setId(jsonOpt.getJSONObject("sender").getInt(
								"id"));
						if (!jsonOpt.getJSONObject("sender").isNull("photo"))
							sender.setPhoto(jsonOpt.getJSONObject("sender")
									.getString("photo"));

						// imitational codes
						// **************************************************************
						String avatar1 = "media/images/photos/face_01.png";
						String avatar2 = "media/images/photos/face_02.png";
						String avatar3 = "media/images/photos/face_03.png";
						String avatar4 = "media/images/photos/avatar2.png";
						String avatar5 = "media/images/photos/staff_icon.jpg";
						String[] avatars = new String[] { avatar1, avatar2,
								avatar3, avatar4, avatar5 };
						int ran = (int) (Math.random() * 5);
						if (ran < avatars.length)
							sender.setPhoto(avatars[ran]);
						else
							sender.setPhoto(avatars[0]);
						// **************************************************************
						item.setSender(sender);
						item.setHasAttachements(jsonOpt
								.getBoolean("attachments"));
						if (jsonOpt.has("urgent")) {
							item.setUrgent(jsonOpt.getBoolean("urgent"));
						}
						item.setSubject(jsonOpt.getString("subject"));
						item.setRead(jsonOpt.getBoolean("read_flag"));
						item.setRefer(jsonOpt.getString("refer"));
						item.setMessage_type(jsonOpt.getString("message_type"));
						item.setCallback_number(jsonOpt
								.getString("callback_number"));
						item.setIsPlaying("no");
						long timestampInLong = jsonOpt
								.getLong("send_timestamp");
						item.setTimeStamp(timestampInLong);
						if (timestampInLong > checkTime) {
							checkTime = timestampInLong;
						}
						if (to_timestamp <= 0 || to_timestamp > timestampInLong) {
							to_timestamp = timestampInLong;
							id = jsonOpt.getString("id");
						}
						item.setThreadingCount(jsonOpt
								.getInt("threading_msg_count"));
						item.setThreadingUUID(jsonOpt.getString("thread_uuid"));
						item.setResolved(jsonOpt.getBoolean("resolution_flag"));
						item.setActionHistoryCount(jsonOpt
								.getInt("action_history_count"));
						receivedMessageList.add(item);
					}
					isGettingData = false;
					addFooterView();
					if (isLoadMore) {
						receivedAdapter.addItems(receivedMessageList);
						receivedAdapter.notifyDataSetChanged();
					} else {
						receivedAdapter.initItems(receivedMessageList);
						setListAdapter(receivedAdapter);
					}
					this.getReceivedListBody();
				} catch (JSONException e) {
					isGettingData = false;
					addFooterView();
					if (isLoadMore) {
						receivedAdapter.addItems(receivedMessageList);
						receivedAdapter.notifyDataSetChanged();
					} else {
						receivedAdapter.initItems(receivedMessageList);
						setListAdapter(receivedAdapter);
					}
					DocLog.e(TAG, "JSONException", e);
				} finally {
					/*
					 * addFooterView(); if (isLoadMore) {
					 * receivedAdapter.addItems(receivedMessageList);
					 * receivedAdapter.notifyDataSetChanged(); } else {
					 * receivedAdapter.initItems(receivedMessageList);
					 * setListAdapter(receivedAdapter); }
					 */
					// NotificationManager nm = (NotificationManager)
					// getActivity().getSystemService(NOTIFICATION_SERVICE);
					// nm.cancel(R.string.app_name);

				}
			} else {
				try {
					JSONObject jsonObj = new JSONObject(result);
					JSONArray jsonArr = jsonObj.getJSONObject("data")
							.getJSONArray("messages");
					int length = jsonArr.length();
					setReceivedMessageAdd(length);
					setmQueryCount(jsonObj.getJSONObject("data").getInt(
							"query_count"));
					for (int i = 0; i < length; i++) {
						SentMessageItem item = new SentMessageItem();
						JSONObject jsonOpt = jsonArr.optJSONObject(i);
						item.setId(jsonOpt.getString("id"));
						ids.add(jsonOpt.getString("id"));
						JSONArray jRecipients = jsonOpt
								.getJSONArray("recipients");
						int len = jRecipients.length();
						SentMessageItem.Recipients[] recipients = new SentMessageItem.Recipients[len];
						for (int j = 0; j < len; j++) {
							JSONObject obj = jRecipients.optJSONObject(j);
							recipients[j] = new SentMessageItem.Recipients(
									obj.getInt("id"), obj.getString("name"));
						}

						item.setRecipients(recipients);
						SentMessageItem.Sender sender = new SentMessageItem.Sender();
						sender.setName(jsonOpt.getJSONObject("sender")
								.getString("name"));
						sender.setId(jsonOpt.getJSONObject("sender").getInt(
								"id"));
						if (!jsonOpt.getJSONObject("sender").isNull("photo"))
							sender.setPhoto(jsonOpt.getJSONObject("sender")
									.getString("photo"));

						// imitational codes
						// **************************************************************
						String avatar1 = "media/images/photos/face_01.png";
						String avatar2 = "media/images/photos/face_02.png";
						String avatar3 = "media/images/photos/face_03.png";
						String avatar4 = "media/images/photos/avatar2.png";
						String avatar5 = "media/images/photos/staff_icon.jpg";
						String[] avatars = new String[] { avatar1, avatar2,
								avatar3, avatar4, avatar5 };
						int ran = (int) (Math.random() * 5);
						if (ran < avatars.length)
							sender.setPhoto(avatars[ran]);
						else
							sender.setPhoto(avatars[0]);
						// **************************************************************

						item.setSender(sender);
						item.setHasAttachements(jsonOpt
								.getBoolean("attachments"));
						item.setUrgent(jsonOpt.getBoolean("urgent"));
						item.setSubject(jsonOpt.getString("subject"));
						item.setRead(jsonOpt.getBoolean("read_flag"));
						item.setRefer(jsonOpt.getString("refer"));
						long timestampInLong = jsonOpt
								.getLong("send_timestamp");
						item.setTimeStamp(timestampInLong);
						if (timestampInLong > checkTime) {
							checkTime = timestampInLong;
						}
						if (to_timestamp <= 0 || to_timestamp > timestampInLong) {
							to_timestamp = timestampInLong;
							id = jsonOpt.getString("id");
						}
						item.setThreadingCount(jsonOpt
								.getInt("threading_msg_count"));
						item.setThreadingUUID(jsonOpt.getString("thread_uuid"));
						item.setResolved(jsonOpt.getBoolean("resolution_flag"));
						item.setActionHistoryCount(jsonOpt
								.getInt("action_history_count"));
						sentMessageList.add(item);
					}
					isGettingData = false;
					addFooterView();
					if (isLoadMore) {
						sentAdapter.addItems(sentMessageList);
						sentAdapter.notifyDataSetChanged();
					} else {
						sentAdapter.initItems(sentMessageList);
						setListAdapter(sentAdapter);
					}
					this.getSentListBody();
				} catch (JSONException e) {
					isGettingData = false;
					addFooterView();
					if (isLoadMore) {
						sentAdapter.addItems(sentMessageList);
						sentAdapter.notifyDataSetChanged();
					} else {
						sentAdapter.initItems(sentMessageList);
						setListAdapter(sentAdapter);
					}
					DocLog.e(TAG, "JSONException", e);
				}
			}

		}

		private void addFooterView() {
			if (loadMoreView != null) {
				mListView.removeFooterView(loadMoreView);
			}
			if (hasMore()) {
				loadMoreView = mActivity.getLayoutInflater().inflate(
						R.layout.load_more, null, false);
				Button loadMore = (Button) loadMoreView
						.findViewById(R.id.btLoadMore);
				loadMore.setText(R.string.message_get_25_more);
				final ProgressBar pb = (ProgressBar) loadMoreView
						.findViewById(R.id.pb);
				final TextView loadingTextView = (TextView) loadMoreView
						.findViewById(R.id.tvLoading);
				loadMore.setOnClickListener(new View.OnClickListener() {

					@Override
					public void onClick(View v) {
						v.setVisibility(View.GONE);
						pb.setVisibility(View.VISIBLE);
						loadingTextView.setVisibility(View.VISIBLE);
						isLoadMore = true;
						getData();

					}
				});
				mListView.addFooterView(loadMoreView);
			}
		}

		public void setBadgeNumber(int unreadReceivedMessages) {
			if (unreadReceivedMessages > 0) {
				if (unreadReceivedMessages < 1000) {
					badgeView.setText(String.valueOf(unreadReceivedMessages));
				} else {
					badgeView.setText("999+");
				}
				badgeView.setVisibility(View.VISIBLE);
			} else {
				badgeView.setVisibility(View.GONE);
			}
		}

		@Override
		public void onListItemClick(ListView l, View v, int position, long id) {
			int count = 0;
			String[] allMessageIds, allMessageSubject, allThreadingUUID = null, allReferStatus, allMessageDetails;
			boolean[] allThreading = null, allRefer = null, allRead = null, allResolved = null;
			int[] allActionHistoryCounts;
			if (isReceived) {
				count = receivedAdapter.getCount();
				allMessageIds = new String[count];
				allMessageSubject = new String[count];
				allThreadingUUID = new String[count];
				allThreading = new boolean[count];
				allRefer = new boolean[count];
				allRead = new boolean[count];
				allActionHistoryCounts = new int[count];
				allResolved = new boolean[count];
				allReferStatus = new String[count];
				allMessageDetails = new String[count];
				for (int i = 0; i < count; i++) {
					ReceivedMessageItem items = receivedAdapter.getItem(i);
					allMessageIds[i] = items.getId();
					allMessageSubject[i] = items.getSubject();
					if (items.getThreadingCount() > 1) {
						allThreading[i] = true;
					} else {
						allThreading[i] = false;
					}
					allThreadingUUID[i] = items.getThreadingUUID();
					if (items.getRefer() == null || items.getRefer().equals("")) {
						allRefer[i] = false;
					} else {
						allRefer[i] = true;
					}
					allRead[i] = items.isRead();
					allActionHistoryCounts[i] = items.getActionHistoryCount();
					allResolved[i] = items.isResolved();
					allReferStatus[i] = items.getRefer();
					allMessageDetails[i] = items.getBody()
							.getJsonStrMessageDetail();
				}
			} else {
				count = sentAdapter.getCount();
				allMessageIds = new String[count];
				allMessageSubject = new String[count];
				allThreadingUUID = new String[count];
				allThreading = new boolean[count];
				allRefer = new boolean[count];
				allRead = new boolean[count];
				allActionHistoryCounts = new int[count];
				allResolved = new boolean[count];
				allReferStatus = new String[count];
				allMessageDetails = new String[count];
				for (int i = 0; i < count; i++) {
					SentMessageItem items = sentAdapter.getItem(i);
					allMessageIds[i] = items.getId();
					allMessageSubject[i] = sentAdapter.getItem(i).getSubject();
					if (items.getThreadingCount() > 1) {
						allThreading[i] = true;
					} else {
						allThreading[i] = false;
					}
					allThreadingUUID[i] = items.getThreadingUUID();
					if (items.getRefer() == null || items.getRefer().equals("")) {
						allRefer[i] = false;
					} else {
						allRefer[i] = true;
					}
					allRead[i] = items.isRead();
					allActionHistoryCounts[i] = items.getActionHistoryCount();
					allResolved[i] = items.isResolved();
					allReferStatus[i] = items.getRefer();
					allMessageDetails[i] = items.getBody()
							.getJsonStrMessageDetail();
				}
			}
			if (count <= position)
				return;
			Intent intent = new Intent(mContext, MessageActivity.class);
			intent.putExtra("received", isReceived);
			intent.putExtra("position", position);
			intent.putExtra("allMessageIds", allMessageIds);
			intent.putExtra("allThreadingUUID", allThreadingUUID);
			intent.putExtra("allMessageSubject", allMessageSubject);
			intent.putExtra("allThreading", allThreading);
			intent.putExtra("allRefer", allRefer);
			intent.putExtra("allRead", allRead);
			intent.putExtra("allActionHistoryCounts", allActionHistoryCounts);
			intent.putExtra("allResolved", allResolved);
			intent.putExtra("allReferStatus", allReferStatus);
			intent.putExtra("allMessageDetails", allMessageDetails);
			startActivityForResult(intent, ACTIVITY_DELETE_MESSAGE);

		}

		@Override
		public void onActivityResult(int requestCode, int resultCode,
				Intent data) {
			DocLog.d(TAG,
					"onActivityResult resultCode:" + String.valueOf(resultCode));// default:
																					// 0

			if (resultCode == RESULT_OK) {
				if (isReceived) {
					if (Cache.hasReceivedMessageListCache()) {
						llLoading.setVisibility(View.GONE);
						llContent.setVisibility(View.VISIBLE);
					} else {
						llLoading.setVisibility(View.VISIBLE);
						llContent.setVisibility(View.GONE);

					}
				} else {
					if (Cache.hasSentMessageListCache()) {
						llLoading.setVisibility(View.GONE);
						llContent.setVisibility(View.VISIBLE);
					} else {
						llLoading.setVisibility(View.VISIBLE);
						llContent.setVisibility(View.GONE);

					}
				}
				if (requestCode == ACTIVITY_DELETE_MESSAGE) {
					if (isReceived) {
						Cache.resetReceivedMessageList();
					} else {
						Cache.resetSentMessageList();
					}
					getInvitation();
				}
				if (requestCode == REPLY) {
					if (isReceived) {
						Cache.resetReceivedMessageList();
					} else {
						Cache.resetSentMessageList();
					}
					getInvitation();
				}
			}
		}

		private void getPopupWindow() {
			if (null != popupWindow) {
				popupWindow.dismiss();
				return;
			} else {
				initPopuptWindow();
			}
		}

		protected void initPopuptWindow() {
			View popupWindow_view = mActivity.getLayoutInflater().inflate(
					R.layout.dropdown_message, null, false);

			popupWindow = new PopupWindow(popupWindow_view, 231, 171, true);
			popupWindow.setBackgroundDrawable(new BitmapDrawable());
			// popupWindow.setOutsideTouchable(true);
			final Button receivedButton = (Button) popupWindow_view
					.findViewById(R.id.btReceived);
			final Button sentButton = (Button) popupWindow_view
					.findViewById(R.id.btSent);
			if (isReceived) {
				receivedButton
						.setBackgroundResource(R.drawable.dropdown_top_active);
				sentButton.setBackgroundResource(R.drawable.dropdown_bottom);
			} else {
				receivedButton.setBackgroundResource(R.drawable.dropdown_top);
				sentButton
						.setBackgroundResource(R.drawable.dropdown_bottom_active);
			}
			receivedButton.setOnClickListener(new View.OnClickListener() {

				@Override
				public void onClick(View v) {
					if (isReceived) {
						refreshView();
					} else {
						receivedButton
								.setBackgroundResource(R.drawable.dropdown_top_active);
						sentButton
								.setBackgroundResource(R.drawable.dropdown_bottom);
						llLoading.setVisibility(View.VISIBLE);
						llContent.setVisibility(View.GONE);
						isReceived = true;
						refreshView();
					}
					popupWindow.dismiss();
				}
			});

			sentButton.setOnClickListener(new View.OnClickListener() {

				@Override
				public void onClick(View v) {
					if (isReceived) {
						receivedButton
								.setBackgroundResource(R.drawable.dropdown_top);
						sentButton
								.setBackgroundResource(R.drawable.dropdown_bottom_active);
						llLoading.setVisibility(View.VISIBLE);
						llContent.setVisibility(View.GONE);
						isReceived = false;
						if (null != receivedAdapter) {
							receivedAdapter.clean();
						}
						refreshView();
					} else {
						refreshView();
					}
					popupWindow.dismiss();
				}
			});

		}

		public boolean hasMore() {
			if (getReceivedMessageAdd() < PAGE_COUNT) {
				return false;
			} else if (getReceivedMessageAdd() == PAGE_COUNT) {
				if (getReceivedMessageAdd() < getmQueryCount()) {
					return true;
				} else {
					return false;
				}
			} else {
				return true;
			}
		}

		@Override
		public void refreshView() {
			llLoading.setVisibility(View.VISIBLE);
			llContent.setVisibility(View.GONE);
			getInvitation();
			init();
			getData();

		}

		private void getInvitation() {
			NetConncet netConncet = new NetConncet(mContext,
					NetConstantValues.INVITATIONS.PATH) {

				@Override
				protected void onPostExecute(String result) {
					super.onPostExecute(result);
					try {
						JSONObject jsonObj = new JSONObject(result);
						JSONObject jData = jsonObj.getJSONObject("data");
						JSONArray invitations = jData
								.getJSONArray("invitations");
						if (!jData.isNull("call_group_penddings")) {
							JSONArray call_group_penddings = jData
									.getJSONArray("call_group_penddings");
							if (invitations.length() > 0
									|| call_group_penddings.length() > 0) {
								Intent intent = new Intent(mContext,
										InvitationReceivedActivity.class);
								intent.putExtra("result", jData.toString());
								startActivity(intent);
							}
						} else {
							if (invitations.length() > 0) {
								Intent intent = new Intent(mContext,
										InvitationReceivedActivity.class);
								intent.putExtra("result", jData.toString());
								startActivity(intent);
							}
						}
					} catch (JSONException e) {
						DocLog.e(TAG, "JSONException", e);
					}
				}

			};
			netConncet.execute();
		}

		@Override
		public void onHiddenChanged(boolean hidden) {
			super.onHiddenChanged(hidden);
			if (!hidden) {
				refreshView();
			}
		}

		@Override
		public void onCreateOptionsMenu(Menu menu, MenuInflater inflater) {
			super.onCreateOptionsMenu(menu, inflater);
			menu.add(0, R.id.iRefresh, 2, R.string.refresh);
		}

		class NewMessageReceiver extends BroadcastReceiver {

			@Override
			public void onReceive(Context context, Intent intent) {
				String message = intent.getStringExtra("message");
				if (message != null) {
					try {
						JSONObject jsonObject = new JSONObject(message);
						String timestamp = jsonObject.getString("timestamp");
						if (!timestamp.equals(resolveTimestamp)) {
							Cache.resetMemoryCache();
							if (MessageListFragment.this.isResumed())
								refreshView();
							resolveTimestamp = timestamp;
						}
					} catch (JSONException e) {
						DocLog.e("MessageResolvedReceiver", "JSONException", e);
					}
				} else {
					Cache.resetReceivedMessageList();
					if (isReceived) {
						if (MessageListFragment.this.isResumed())
							refreshView();
					}
				}
			}
		}

		@Override
		public void forceRefreshView() {
			if (isReceived) {
				Cache.resetReceivedMessageList();
			} else {
				Cache.resetSentMessageList();
			}
			refreshView();
		}

		/**
		 * @return the receivedMessageAdd
		 */
		public int getReceivedMessageAdd() {
			return receivedMessageAdd;
		}

		/**
		 * @param receivedMessageAdd
		 *            the receivedMessageAdd to set
		 */
		public void setReceivedMessageAdd(int receivedMessageAdd) {
			this.receivedMessageAdd = receivedMessageAdd;
		}

		/**
		 * @return the mQueryCount
		 */
		public int getmQueryCount() {
			return mQueryCount;
		}

		/**
		 * @param mQueryCount
		 *            the mQueryCount to set
		 */
		public void setmQueryCount(int mQueryCount) {
			this.mQueryCount = mQueryCount;
		}

		@Override
		public void onSuccessDelete() {
			forceRefreshView();
		}
	}

}
