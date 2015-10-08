package com.doctorcom.physician.activity.message;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import android.app.AlertDialog;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.os.Bundle;
import android.support.v4.app.FragmentActivity;
import android.support.v4.app.FragmentManager;
import android.support.v4.app.ListFragment;
import android.support.v4.content.LocalBroadcastManager;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.view.View.OnClickListener;
import android.widget.AdapterView;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ListView;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;
import android.widget.AdapterView.OnItemLongClickListener;

import com.doctorcom.android.R;
import com.doctorcom.physician.AppValues;
import com.doctorcom.physician.activity.message.CommonMessageMethods.DeleteMessageListener;
import com.doctorcom.physician.activity.message.MessageActivity.onRefreshThreading;
import com.doctorcom.physician.activity.task.TaskNewActivity;
import com.doctorcom.physician.net.NetConstantValues;
import com.doctorcom.physician.net.http.NetConncet;
import com.doctorcom.physician.utils.DocLog;
import com.doctorcom.physician.utils.JsonErrorProcess;
import com.doctorcom.physician.utils.cache.Cache;

public class ThreadingListActivity extends FragmentActivity {
	@Override
	protected void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
		FragmentManager fm = getSupportFragmentManager();

		// Create the list fragment and add it as our sole content.
		if (fm.findFragmentById(android.R.id.content) == null) {
			ThreadingistFragment list = new ThreadingistFragment();
			fm.beginTransaction().add(android.R.id.content, list).commit();
		}
	}

	public static class ThreadingistFragment extends ListFragment implements
			Cache.CacheFinishListener, onRefreshThreading,
			DeleteMessageListener {
		private final String TAG = "ThreadingListActivity";
		private List<ThreadingItem> threadingList;
		private ThreadingAdapter threadingAdapter;
		private SentMessageAdapter sentAdapter;
		private boolean isReceived = true, hasCache = false;
		private int position;
		private String[] allMessageSubject;
		private String threadingUUID;
		private LinearLayout llContent, llLoading;
		private final int REFRESH = 1;
		private LocalBroadcastManager broadcastManager;
		private ThreadingResolvedReceiver threadingResolvedReceiver;
		private String resolveTimestamp = null;
		private long to_timestamp;
		private long checkTime;
		private String id;
		private View loadMoreView;
		private ListView mListView;
		private final int PAGE_COUNT = AppValues.PAGE_COUNT;
		private int receivedMessageAdd;
		private int mQueryCount;
		protected boolean isLoadMore;
		private boolean isThreadingBody;
		private HashMap<String, String> params;
		private int requestCount = 0;
		private List<String> ids;

		@Override
		public void onCreate(Bundle savedInstanceState) {
			super.onCreate(savedInstanceState);
			Bundle bundle = getArguments();
			position = bundle.getInt("position", 0);
			allMessageSubject = bundle.getStringArray("allMessageSubject");
			threadingUUID = bundle.getStringArray("allThreadingUUID")[position];
			ids = new ArrayList<String>();
		}

		@Override
		public View onCreateView(LayoutInflater inflater, ViewGroup container,
				Bundle savedInstanceState) {
			View view = inflater.inflate(R.layout.fragment_threading_list,
					container, false);
			llContent = (LinearLayout) view.findViewById(R.id.llContent);
			llLoading = (LinearLayout) view.findViewById(R.id.llLoading);

			threadingList = new ArrayList<ThreadingItem>();
			threadingAdapter = new ThreadingAdapter(getActivity());
			onRefresh();
			return view;
		}

		@Override
		public void onActivityCreated(Bundle savedInstanceState) {
			super.onActivityCreated(savedInstanceState);
			broadcastManager = LocalBroadcastManager.getInstance(getActivity());
			threadingResolvedReceiver = new ThreadingResolvedReceiver();
			IntentFilter filter = new IntentFilter("messageResolvedReceiver");
			broadcastManager
					.registerReceiver(threadingResolvedReceiver, filter);
			mListView = this.getListView();
			mListView.setOnItemLongClickListener(new OnItemLongClickListener() {

				@Override
				public boolean onItemLongClick(AdapterView<?> paramAdapterView,
						View paramView, int paramInt, long paramLong) {
					AlertDialog.Builder builder = new AlertDialog.Builder(
							getActivity());
					AlertDialog alert = builder.create();
					alert.setCanceledOnTouchOutside(true);
					alert.show();
					alert.getWindow().setContentView(R.layout.chat_menu_dialog);
					View rootView = alert.getWindow().findViewById(
							R.id.ll_chat_root_container);
					setChildViewsClickListener(rootView, paramInt, alert);
					return true;
				}

			});

		}

		@SuppressWarnings("unused")
		private void setChildViewsClickListener(View parentView, int position,
				final AlertDialog alertDialog) {
			final Context mContext = getActivity();
			String refer;
			final String subject;
			final String body;
			final String messageId;
			final int fromID;
			final String fromName;
			final String threadingUUID;
			final String jsonStrMessageDetail;
			ThreadingItem item = threadingAdapter.getItem(position);
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
				Toast.makeText(mContext, R.string.get_data_error, Toast.LENGTH_SHORT).show();
			}				
			jsonStrMessageDetail = str;

			
			// set reply button onclick listener
			Button btReply = (Button) parentView.findViewById(R.id.chat_reply);
			btReply.setOnClickListener(new OnClickListener() {

				@Override
				public void onClick(View v) {
					Intent intent = new Intent(mContext,
							MessageNewActivity.class);
					intent.putExtra("userId", fromID);
					intent.putExtra("name", fromName);
					intent.putExtra("subject", subject);
					intent.putExtra("type", MessageNewActivity.REPLY_MESSAGE);
					intent.putExtra("threadingUUID", threadingUUID);
					getActivity().startActivityForResult(intent, REFRESH);
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
					intent.putExtra("subject",
							subject);
					intent.putExtra("body", jsonStrMessageDetail);
					intent.putExtra("messageId", messageId);
					startActivity(intent);
					getActivity().overridePendingTransition(
							R.anim.up, R.anim.hold);
					alertDialog.dismiss();
				}
			});

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
											CommonMessageMethods.deleteMessage(
													messageId, mContext,
													ThreadingistFragment.this);
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
		public void onListItemClick(ListView l, View v, int position, long id) {
			int count = 0;
			String[] allMessageIds, allMessageSubject, allThreadingUUID = null, allMessageDetails;
			boolean[] allThreading = null, allRefer = null, allRead = null, allResolved = null;
			int[] allActionHistoryCounts;
			if (isReceived) {
				count = threadingAdapter.getCount();
				allMessageIds = new String[count];
				allMessageSubject = new String[count];
				allThreadingUUID = new String[count];
				allThreading = new boolean[count];
				allRefer = new boolean[count];
				allRead = new boolean[count];
				allResolved = new boolean[count];
				allActionHistoryCounts = new int[count];
				allMessageDetails = new String[count];
				for (int i = 0; i < count; i++) {
					ThreadingItem items = threadingAdapter.getItem(i);
					allMessageIds[i] = items.getId();
					allMessageSubject[i] = items.getSubject();
					allThreading[i] = false;
					allRead[i] = items.isRead();
					allRefer[i] = false;
					allThreadingUUID[i] = items.getThreadingUUID();
					allActionHistoryCounts[i] = items.getActionHistoryCount();
					allResolved[i] = items.isResolved();
					allMessageDetails[i] = items.getBody().getJsonStrMessageDetail();
				}
			} else {
				count = sentAdapter.getCount();
				allMessageIds = new String[count];
				allMessageSubject = new String[count];
				allActionHistoryCounts = new int[count];
				allResolved = new boolean[count];
				allMessageDetails = new String[count];
				for (int i = 0; i < count; i++) {
					SentMessageItem items = sentAdapter.getItem(i);
					allMessageIds[i] = items.getId();
					allMessageSubject[i] = items.getSubject();
					allActionHistoryCounts[i] = items.getActionHistoryCount();
					allResolved[i] = items.isResolved();
					allMessageDetails[i] = items.getBody().getJsonStrMessageDetail();
				}
			}
			if (position >= count)
				return;
			Intent intent = new Intent(getActivity(), MessageActivity.class);
			intent.putExtra("received", isReceived);
			intent.putExtra("position", position);
			intent.putExtra("allMessageIds", allMessageIds);
			intent.putExtra("allMessageSubject", allMessageSubject);
			intent.putExtra("allThreading", allThreading);
			intent.putExtra("allRefer", allRefer);
			intent.putExtra("allRead", allRead);
			intent.putExtra("allThreadingUUID", allThreadingUUID);
			intent.putExtra("allActionHistoryCounts", allActionHistoryCounts);
			intent.putExtra("allResolved", allResolved);
			intent.putExtra("allMessageDetails", allMessageDetails);
			getActivity().startActivityForResult(intent, REFRESH);

		}

		@Override
		public void onCacheFinish(String result, boolean isCache) {
			llLoading.setVisibility(View.GONE);
			llContent.setVisibility(View.VISIBLE);
			if (!isThreadingBody) {
				if (isCache) {
					hasCache = true;
					updateData(result, isCache);
				} else {
					if (JsonErrorProcess.checkJsonError(result,
							this.getActivity())) {
						updateData(result, isCache);
					} else {
						if (isLoadMore) {
							addFooterView();
						} else {
							if (!hasCache) {
								setListAdapter(null);
							}
						}
					}
				}
			} else {
				isThreadingBody = false;
				// will be recovered
				// **************************************************************

//				JSONObject jsonObj;
//				try {
//					jsonObj = new JSONObject(result);
//
//					if (!jsonObj.isNull("errno")) {
//						Toast.makeText(getActivity(),
//								jsonObj.getString("descr"), Toast.LENGTH_SHORT)
//								.show();
//						if (requestCount < 3) {
//							requestCount++;
//							getThreadBody();
//						}
//						return;
//					}
//					JSONObject jsonSettings = jsonObj.getJSONObject("settings");
//					JSONArray jsonArr = jsonObj.getJSONObject("data")
//							.getJSONArray("messages");
//					int length = jsonArr.length();
//					ArrayList<ThreadingItem.Body> list = new ArrayList<ThreadingItem.Body>();
//					for (int i = 0; i < length; i++) {
//						String jsonStrMessageDetailData = jsonArr.getString(i);
//						JSONObject jsonObjMessageDetail = new JSONObject();
//						jsonObjMessageDetail.put("settings", jsonSettings);
//						jsonObjMessageDetail.put("data",
//								jsonStrMessageDetailData);
//						String id = jsonArr.getJSONObject(i).getString("id");
//						String body = jsonArr.getJSONObject(i)
//								.getString("body");
//						JSONArray attachmentsjson = jsonArr.getJSONObject(i)
//								.getJSONArray("attachments");
//						ReceivedMessageItem.Attachment[] attachments = new ReceivedMessageItem.Attachment[attachmentsjson
//								.length()];
//						for (int j = 0; i < attachments.length; j++) {
//							attachments[j].setFilename(attachmentsjson
//									.getJSONObject(j).getString("filename"));
//							attachments[j].setFilesize(attachmentsjson
//									.getJSONObject(j).getLong("filesize"));
//							attachments[j].setId(attachmentsjson.getJSONObject(
//									j).getString("id"));
//						}
//						String jsonStrMessageDetail = jsonObjMessageDetail
//								.toString();
//						ThreadingItem.Body itemBody = new ThreadingItem.Body();
//						itemBody.setAttachments(attachments);
//						itemBody.setBody(body);
//						itemBody.setId(id);
//						itemBody.setJsonStrMessageDetail(jsonStrMessageDetail);
//						list.add(itemBody);
//					}
//					threadingAdapter.setThreadingBody(list);
//					threadingAdapter.notifyDataSetChanged();
//					requestCount = 0;
//				} catch (JSONException e) { // TODO Auto-generated catch block
//					if (requestCount < 3) {
//						requestCount++;
//						getThreadBody();
//					}
//					DocLog.e(TAG, "JSONException", e);
//				}

				// **************************************************************

				// imitational codes
				// **************************************************************
				ArrayList<ThreadingItem.Body> list = new ArrayList<ThreadingItem.Body>();
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
					ThreadingItem.Body itemBody = new ThreadingItem.Body();
					itemBody.setAttachments(attachments);
					if (ran < bodys.length)
						itemBody.setBody(bodys[0]);
					else
						itemBody.setBody(bodys[0]);
					itemBody.setId(id);
					list.add(itemBody);
				}
				threadingAdapter.setThreadingBody(list);
				threadingAdapter.notifyDataSetChanged();
				// **************************************************************
			}

		}

		public void updateData(String result, boolean isCache) {
			try {
				JSONObject jsonObj = new JSONObject(result);
				if (hasCache && !isCache) {
					if (!jsonObj.isNull("errno")) {
						Toast.makeText(getActivity(),
								jsonObj.getString("descr"), Toast.LENGTH_SHORT)
								.show();
						return;
					}
				} else {
					if (!jsonObj.isNull("errno")) {
						Toast.makeText(getActivity(),
								jsonObj.getString("descr"), Toast.LENGTH_SHORT)
								.show();
						return;
					}
				}
				JSONArray jsonArr = jsonObj.getJSONObject("data").getJSONArray(
						"messages");
				int length = jsonArr.length();
				setReceivedMessageAdd(length);
				setmQueryCount(jsonObj.getJSONObject("data").getInt(
						"query_count"));
				threadingList.clear();
				for (int i = 0; i < length; i++) {
					ThreadingItem item = new ThreadingItem();
					ThreadingItem.Sender sender = new ThreadingItem.Sender();
					JSONObject jsonOpt = jsonArr.optJSONObject(i);
					item.setId(jsonOpt.getString("id"));
					ids.add(jsonOpt.getString("id"));
					sender.setName(jsonOpt.getJSONObject("sender").getString(
							"name"));
					sender.setId(jsonOpt.getJSONObject("sender").getInt("id"));
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
					String[] avatars = new String[] { avatar1, avatar2, avatar3, avatar4,
							avatar5 };
					int ran = (int) (Math.random() * 5);
					if(ran < avatars.length)
						sender.setPhoto(avatars[ran]);
					else
						sender.setPhoto(avatars[0]);
					// **************************************************************
					item.setSender(sender);
					item.setHasAttachements(jsonOpt.getBoolean("attachments"));
					if (jsonOpt.has("urgent")) {
						item.setUrgent(jsonOpt.getBoolean("urgent"));
					}
					item.setSubject(jsonOpt.getString("subject"));
					item.setRead(jsonOpt.getBoolean("read_flag"));
					item.setRefer(jsonOpt.getString("refer"));
					long timestampInLong = jsonOpt.getLong("send_timestamp");
					item.setTimeStamp(timestampInLong);
					if (timestampInLong > checkTime) {
						checkTime = timestampInLong;
					}
					if (to_timestamp <= 0 || to_timestamp > timestampInLong) {
						to_timestamp = timestampInLong;
						id = jsonOpt.getString("id");
					}
					item.setThreadingCount(0);
					item.setThreadingUUID(jsonOpt.getString("thread_uuid"));
					item.setResolved(jsonOpt.getBoolean("resolution_flag"));
					item.setActionHistoryCount(jsonOpt
							.getInt("action_history_count"));
					threadingList.add(item);
				}
				addFooterView();
				if (isLoadMore) {
					threadingAdapter.addItems(threadingList);
					threadingAdapter.notifyDataSetChanged();
				} else {
					threadingAdapter.initItems(threadingList);
					setListAdapter(threadingAdapter);
				}
				getThreadBody();
			} catch (JSONException e) {
				DocLog.e(TAG, "JSONException", e);
				setListAdapter(null);
			}

		}

		@Override
		public void onRefresh() {
			llLoading.setVisibility(View.VISIBLE);
			llContent.setVisibility(View.GONE);
			Cache.resetThreadingMessageList();
			init();
			getData();
		}

		private void init() {
			params = new HashMap<String, String>();
			threadingAdapter = new ThreadingAdapter(getActivity());
			sentAdapter = new SentMessageAdapter(getActivity());
			threadingList = new ArrayList<ThreadingItem>();
			isLoadMore = false;
			to_timestamp = 0L;
			setReceivedMessageAdd(0);
			setmQueryCount(0);
			checkTime = 0;
			id = "";
			requestCount = 0;
		}

		private void addFooterView() {
			if (loadMoreView != null) {
				mListView.removeFooterView(loadMoreView);
			}
			if (hasMore()) {
				loadMoreView = this.getActivity().getLayoutInflater()
						.inflate(R.layout.load_more, null, false);
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

		private void getData() {
			if (ids == null)
				ids = new ArrayList<String>();
			ids.clear();
			String toTime = String.valueOf(to_timestamp);
			Cache cache = new Cache(getActivity(), NetConncet.HTTP_POST);
			params.put(NetConstantValues.MESSAGING_LIST_RECEIVED.PARAM_COUNT,
					String.valueOf(25));
			params.put(NetConstantValues.MESSAGING_LIST_RECEIVED.PARAM_TO,
					toTime);
			params.put(NetConstantValues.MESSAGING_LIST_RECEIVED.PARAM_FROM,
					"0");
			params.put(
					NetConstantValues.MESSAGING_LIST_RECEIVED.PARAM_EXCLUDE_ID,
					id);
			params.put(NetConstantValues.THREADING.PARAM_IS_THREADING,
					String.valueOf(false));
			params.put(NetConstantValues.THREADING.PARAM_THREADING_UUID,
					threadingUUID);
			cache.setHowSearch(Cache.SEARCH_MEMORY_ONLY);
			cache.useCache(this, NetConstantValues.THREADING.PATH, null, params);
		}

		private void getThreadBody() {
			isThreadingBody = true;
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
			 * params.put(NetConstantValues.RECEIVED_LIST_BODY.IDS, strIds);
			 * Cache cache = new Cache(context, NetConncet.HTTP_POST);
			 * cache.setHowSearch(Cache.SEARCH_MEMORY_ONLY);
			 * cache.useCache(this, NetConstantValues.THREADING_BODY.PATH, null,
			 * params);
			 */
			// **************************************************************

			// imitational codes
			// **************************************************************
			onCacheFinish(strIds, true);
			// **************************************************************
		}

		@Override
		public void onDestroy() {
			broadcastManager.unregisterReceiver(threadingResolvedReceiver);
			super.onDestroy();
		}

		class ThreadingResolvedReceiver extends BroadcastReceiver {

			@Override
			public void onReceive(Context context, Intent intent) {
				String message = intent.getStringExtra("message");
				if (message != null) {
					try {
						JSONObject jsonObject = new JSONObject(message);
						String timestamp = jsonObject.getString("timestamp");
						if (!timestamp.equals(resolveTimestamp)) {
							if (ThreadingistFragment.this.isResumed())
								onRefresh();
							resolveTimestamp = timestamp;
						}
					} catch (JSONException e) {
						DocLog.e("MessageResolvedReceiver", "JSONException", e);
					}
				}

			}

		}

		@Override
		public void onSuccessDelete() {
			onRefresh();
			this.getActivity().setResult(RESULT_OK);
		}
	}

}
