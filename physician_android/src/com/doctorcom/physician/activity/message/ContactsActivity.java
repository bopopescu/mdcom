package com.doctorcom.physician.activity.message;

import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import java.util.regex.Pattern;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import android.app.ListActivity;
import android.content.ContentValues;
import android.content.Context;
import android.content.Intent;
import android.graphics.drawable.BitmapDrawable;
import android.os.Bundle;
import android.text.Html;
import android.view.KeyEvent;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.view.ViewGroup.LayoutParams;
import android.widget.AdapterView;
import android.widget.BaseAdapter;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ListView;
import android.widget.PopupWindow;
import android.widget.ProgressBar;
import android.widget.RelativeLayout;
import android.widget.TextView;

import com.doctorcom.android.R;
import com.doctorcom.physician.activity.doctor.CommonDoctorMethods;
import com.doctorcom.physician.activity.doctor.DoctorTabItem;
import com.doctorcom.physician.activity.doctor.PracticeItem;
import com.doctorcom.physician.activity.doctor.TabListAdapter;
import com.doctorcom.physician.net.NetConstantValues;
import com.doctorcom.physician.net.http.NetConncet;
import com.doctorcom.physician.utils.DocLog;
import com.doctorcom.physician.utils.JsonErrorProcess;
import com.doctorcom.physician.utils.QuickAlphabeticBar;
import com.doctorcom.physician.utils.cache.Cache;

public class ContactsActivity extends ListActivity implements
		Cache.CacheFinishListener {
	private final String TAG = "ContactsActivity";
	public final String FIRST_NAME = "firstName", LAST_NAME = "lastName", FULL_NAME = "fullname",
			USER_ID = "userId", SORT_KEY = "sort_key";
	private QuickAlphabeticBar alpha;
	private List<ContentValues> list;
	private String path, asterisk;
	private ListAdapter adapter;
	private TextView mTitle;
	private PopupWindow popupWindow;
	private HashMap<String, String> params = new HashMap<String, String>();
	private boolean isUserTabs, isSearch;
	private int hasCache;
	private ProgressBar refreshProgressBar;
	private List<DoctorTabItem> doctorTabList;
	private int tabSelectedPos;
	private ListView tabListView;
	private Button selectButton;
	private int resultDoctorType;
	private boolean isLoadMore;
	private String id;
	private String firstName;
	private String lastName;
	private int requestCount;
	private TextView tvSearchHeader;
	private int userAdd;
	private int mQueryCount;
	private View loadMoreView;
	private final int PAGE_COUNT = 50;
	private LinearLayout loadingLinearLayout;
	private LinearLayout retryLinearLayout;
	private ProgressBar loadingProgressBar;
	private Button yesButton;
	private Button noButton;
	private RelativeLayout llContent;
	// imitational codes
	// **************************************************************
	private int start;

	// **************************************************************

	@Override
	protected void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
		setContentView(R.layout.activity_contacts_list);
		mTitle = (TextView) findViewById(R.id.tvDC);

		alpha = (QuickAlphabeticBar) findViewById(R.id.fast_scroller);
		refreshProgressBar = (ProgressBar) findViewById(R.id.pbRefresh);
		selectButton = (Button) findViewById(R.id.btSelect);

		Button closeButton = (Button) findViewById(R.id.btClose);
		closeButton.setOnClickListener(new View.OnClickListener() {

			@Override
			public void onClick(View v) {
				setResult(RESULT_CANCELED);
				closeActivity();
			}
		});

		final EditText searchEditText = (EditText) findViewById(R.id.etSearch);
		searchEditText.setOnKeyListener(new View.OnKeyListener() {

			@Override
			public boolean onKey(View v, int keyCode, KeyEvent event) {
				if (keyCode == KeyEvent.KEYCODE_ENTER
						&& event.getAction() == KeyEvent.ACTION_UP) {
					String result = searchEditText.getText().toString();
					if (result.equals("")) {
						searchEditText.setError(Html
								.fromHtml(getString(R.string.cannot_be_empty)));
						return true;
					} else {
						search(result);
					}
				}
				return false;
			}

		});
		loadingLinearLayout = (LinearLayout) findViewById(R.id.linearLoading);
		retryLinearLayout = (LinearLayout) findViewById(R.id.linearRetry);
		loadingProgressBar = (ProgressBar) findViewById(R.id.progressbar_loading);
		yesButton = (Button) findViewById(R.id.button_yes);
		noButton = (Button) findViewById(R.id.button_no);
		tvSearchHeader = (TextView) findViewById(R.id.tvSearchHeader);
		llContent = (RelativeLayout) findViewById(R.id.rlContent);
		getUserTABS();
	}

	protected void initParams() {
		yesButton.setOnClickListener(new View.OnClickListener() {

			@Override
			public void onClick(View v) {
				loadingProgressBar.setVisibility(View.VISIBLE);
				retryLinearLayout.setVisibility(View.GONE);
				getData();

			}
		});
		noButton.setOnClickListener(new View.OnClickListener() {

			@Override
			public void onClick(View v) {
				retryLinearLayout.setVisibility(View.GONE);
				loadingLinearLayout.setVisibility(View.GONE);
				llContent.setVisibility(View.VISIBLE);
				setListAdapter(null);

			}
		});
	}

	protected void init() {
		adapter = new ListAdapter(this);
		String name = null;
		if (isSearch) {
			name = params.get(NetConstantValues.SEARCH_USER.PARAM_NAME);
		}
		params = new HashMap<String, String>();
		if (isSearch)
			params.put(NetConstantValues.SEARCH_USER.PARAM_NAME, name);
		asterisk = null;
		isLoadMore = false;
		setUserAdd(0);
		setmQueryCount(0);
		id = "";
		firstName = "";
		lastName = "";
		requestCount = 0;
		tvSearchHeader.setVisibility(View.GONE);
		loadingLinearLayout.setVisibility(View.VISIBLE);
		loadingProgressBar.setVisibility(View.VISIBLE);
		retryLinearLayout.setVisibility(View.GONE);
		// imitational codes
		// **************************************************************
		start = 0;
		// **************************************************************
	}

	/**
	 * @return the receivedMessageAdd
	 */
	public int getUserAdd() {
		return userAdd;
	}

	/**
	 * @param receivedMessageAdd
	 *            the receivedMessageAdd to set
	 */
	public void setUserAdd(int userAdd) {
		this.userAdd = userAdd;
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
	protected void onListItemClick(ListView l, View v, int position, long id) {
		ContentValues item = adapter.getItem(position);
		Intent intent = new Intent();
		intent.putExtra(USER_ID, item.getAsInteger(USER_ID));
		intent.putExtra(FIRST_NAME, item.getAsString(FIRST_NAME));
		intent.putExtra(LAST_NAME, item.getAsString(LAST_NAME));
		setResult(RESULT_OK, intent);
		closeActivity();
	}

	public void getUserTABS() {
		isUserTabs = true;
		doctorTabList = new ArrayList<DoctorTabItem>();
		Cache cache = new Cache(this, NetConncet.HTTP_POST);
		cache.setCacheType(Cache.CACHE_USER_TABS);
		HashMap<String, String> params = new HashMap<String, String>();
		params.put(NetConstantValues.USER_TABS.ONLY_USER_TAB,
				String.valueOf(true));
		params.put("show_my_favorite", String.valueOf(true));
		cache.useCache(this, NetConstantValues.USER_TABS.PATH, null, params);

	}

	private void getPopupWindow() {
		if (null != popupWindow) {
			popupWindow.dismiss();
		} else {
			initPopuptWindow();
		}
	}

	private void search(String name) {
		init();
		resultDoctorType = DoctorTabItem.PROVIDER;
		isSearch = true;
		tabSelectedPos = -1;
		llContent.setVisibility(View.GONE);
		path = NetConstantValues.SEARCH_USER.PATH;
		params.put(NetConstantValues.SEARCH_USER.PARAM_NAME, name);
		params.put(NetConstantValues.SEARCH_USER.PARAM_LIMIT,
				String.valueOf(PAGE_COUNT));
		mTitle.setText(R.string.search);
		getData();

	}

	protected void getData() {
		initParams();
		isUserTabs = false;
		if (resultDoctorType == DoctorTabItem.FAVOURITE)
			params.put("object_type_flag", String.valueOf(1));
		params.put(NetConstantValues.USER_LIST.FIRST_NAME, firstName);
		params.put(NetConstantValues.USER_LIST.LAST_NAME, lastName);
		params.put(NetConstantValues.USER_LIST.ID, id);
		params.put(NetConstantValues.USER_LIST.COUNT, String.valueOf(25));
		Cache cache = new Cache(this, NetConncet.HTTP_POST);
		cache.setCacheType(Cache.CACHE_USER_LIST);
		cache.useCache(this, path, asterisk, params);
		refreshProgressBar.setVisibility(View.VISIBLE);
	}

	protected void initPopuptWindow() {
		View popupWindowView = getLayoutInflater().inflate(
				R.layout.dropdown_doctor_tab, null, false);
		popupWindowView.findViewById(R.id.framelayout_contacts_top)
				.setBackgroundResource(R.drawable.dropdown_top_03);
		tabListView = (ListView) popupWindowView
				.findViewById(R.id.listview_user_select);
		final TabListAdapter tabListAdapter = new TabListAdapter(this,
				R.layout.cell_dropdown_doctor_tab, R.id.textview_users_select,
				doctorTabList);
		tabListView.setAdapter(tabListAdapter);
		tabListView
				.setOnItemClickListener(new AdapterView.OnItemClickListener() {

					@Override
					public void onItemClick(AdapterView<?> parent, View view,
							int position, long id) {
						popupWindow.dismiss();
						isSearch = false;
						tabSelectedPos = position;
						llContent.setVisibility(View.GONE);
						DoctorTabItem item = tabListAdapter.getItem(position);
						resultDoctorType = item.getResultType();
						if (resultDoctorType == DoctorTabItem.ORG) {
							asterisk = "/Org/*/Users/";
						} else {
							asterisk = null;
						}

						mTitle.setText(item.getName());
						path = item.getUrl();
						init();
						getData();
					}
				});
		popupWindow = new PopupWindow(popupWindowView,
				selectButton.getWidth() * 231 / 90, LayoutParams.WRAP_CONTENT);
		popupWindow.setBackgroundDrawable(new BitmapDrawable());
		popupWindow.setFocusable(true);
		selectButton.setOnClickListener(new View.OnClickListener() {

			@Override
			public void onClick(View v) {
				TabListAdapter adapter = (TabListAdapter) tabListView
						.getAdapter();
				int len = adapter.getCount();
				if (len == 0) {

				} else {
					for (int i = 0; i < len; i++) {
						DoctorTabItem item = adapter.getItem(i);
						if (i == tabSelectedPos) {
							item.setSelected(true);
						} else {
							item.setSelected(false);
						}
					}
					adapter.notifyDataSetChanged();
					popupWindow.showAsDropDown(v, 0, -15);
				}
			}
		});

	}

	public void updateData(String result, boolean isCache) {
		list = new ArrayList<ContentValues>();
		try {
			JSONObject jsonObj = new JSONObject(result);
			if (!jsonObj.isNull("errno")) {
				if ((hasCache & (1 << tabSelectedPos)) == 0) {
					setListAdapter(null);
				}
				if (isSearch) {
					if (requestCount < 3) {
						requestCount++;
						getData();
						return;
					}
					// will be recovered
					// **************************************************************
					/*if (requestCount == 3) {
						if (jsonObj.isNull("count"))
							this.handleError();
						return;
					}*/
					// **************************************************************
				}
			} else {
				if (isSearch) {
					if (requestCount < 3 && jsonObj.isNull("count")) {
						requestCount++;
						getData();
						return;
					}
					// will be recovered
					// **************************************************************
					/*if (requestCount == 3) {
						if (jsonObj.isNull("count"))
							this.handleError();
						return;
					}*/
					// **************************************************************
				}
				JSONArray jsonArr;
				if (resultDoctorType == DoctorTabItem.FAVOURITE) {
					jsonArr = jsonObj.getJSONObject("data").getJSONArray(
							"favorites");
					int length = jsonArr.length();
					for (int i = 0; i < length; i++) {
						JSONObject favourite = jsonArr.optJSONObject(i);
						ContentValues cv = new ContentValues();
						String name = favourite.getString("object_name");
						String[] names = name.split(" ");
						String firstName = names[0];
						String lastName = names[1];
//						String sortKey = lastName + " " + firstName;
						int userId = favourite.getInt("object_id");
						cv.put(USER_ID, userId);
						cv.put(FIRST_NAME, firstName);
						cv.put(LAST_NAME, lastName);
						cv.put(SORT_KEY, name);
						cv.put(FULL_NAME, name);
						list.add(cv);
					}
					addFooterView();
					adapter.initItems(list);
					setListAdapter(adapter);
				} else {
					if (isSearch) {
						jsonArr = jsonObj.getJSONObject("data").getJSONArray(
								"results");
						int count = 0;
						if (!jsonObj.getJSONObject("data")
								.isNull("total_count"))
							count = jsonObj.getJSONObject("data").getInt(
									"total_count");
						else
							count = jsonArr.length();
						String searchHeader = CommonDoctorMethods.getTotalCountStr(count, this);
						this.addSearchHeader(searchHeader);
					} else {
						jsonArr = jsonObj.getJSONObject("data").getJSONArray(
								"users");
					}
					int length = jsonArr.length();
					// will be recovered
					// **************************************************************
//					setUserAdd(length);
//					int queryCount = 0;
//					if (!jsonObj.getJSONObject("data").isNull("query_count"))
//						queryCount = jsonObj.getJSONObject("data").getInt(
//								"query_count");
//					setmQueryCount(queryCount);
//					for (int i = 0; i < length; i++) {
//						JSONObject doctor = jsonArr.optJSONObject(i);
//						ContentValues cv = new ContentValues();
//						String firstName = doctor.getString("first_name");
//						String lastName = doctor.getString("last_name");
//						String sortKey = lastName + " " + firstName;
//						int userId = doctor.getInt("id");
//						String fullname = doctor.getString("fullname");
//						cv.put(USER_ID, userId);
//						cv.put(FIRST_NAME, firstName);
//						cv.put(LAST_NAME, lastName);
//						cv.put(SORT_KEY, fullname);
//						cv.put(FULL_NAME, fullname);
//						list.add(cv);
//					}
					// **************************************************************
					
					// imitational codes
					// **************************************************************
					int queryCount = length - start;
					int size;
					if(queryCount < PAGE_COUNT)
						size = queryCount;
					else
						size = PAGE_COUNT;
					setUserAdd(size);
					setmQueryCount(queryCount);
					for (int i = start; i < start + size; i++) {
						JSONObject doctor = jsonArr.optJSONObject(i);
						ContentValues cv = new ContentValues();
						String firstName = doctor.getString("first_name");
						String lastName = doctor.getString("last_name");
//						String sortKey = lastName + " " + firstName;
						int userId = doctor.getInt("id");
						String fullname = doctor.getString("fullname");
						cv.put(USER_ID, userId);
						cv.put(FIRST_NAME, firstName);
						cv.put(LAST_NAME, lastName);
						cv.put(SORT_KEY, fullname);
						cv.put(FULL_NAME, fullname);
						list.add(cv);
					}
					if(isLoadMore)
						start += size;
					else
						start = PAGE_COUNT;
					// **************************************************************
					if (length > 0) {
						JSONObject doctor = jsonArr.optJSONObject(length - 1);
						id = String.valueOf(doctor.getInt("id"));
						firstName = doctor.getString("first_name");
						lastName = doctor.getString("last_name");
					}
					addFooterView();
					if (isLoadMore) {
						adapter.addItems(list);
						adapter.notifyDataSetChanged();
					} else {
						adapter.initItems(list);
						setListAdapter(adapter);
					}
					requestCount = 0;
				}
				alpha.init(this);
				alpha.setListView(getListView());
				alpha.setHight(alpha.getHeight());
				alpha.setVisibility(View.VISIBLE);
				requestCount = 0;
			}
			loadingLinearLayout.setVisibility(View.GONE);
			refreshProgressBar.setVisibility(View.GONE);
			llContent.setVisibility(View.VISIBLE);
		} catch (JSONException e) {
			DocLog.e(TAG, "JSONException", e);
			setListAdapter(null);
			if (isSearch) {
				if (requestCount < 3) {
					requestCount++;
					getData();
					return;
				}
			}
			loadingLinearLayout.setVisibility(View.GONE);
			refreshProgressBar.setVisibility(View.GONE);
			llContent.setVisibility(View.VISIBLE);
		} finally {
			if (list.size() <= 0 && ((hasCache & (1 << tabSelectedPos)) == 0)) {
				alpha.setVisibility(View.GONE);
			}
		}
	}

	private void addSearchHeader(String searchHeader) {
		tvSearchHeader.setVisibility(View.VISIBLE);
		tvSearchHeader.setText(searchHeader);
	}

	@SuppressWarnings("null")
	@Override
	public void onCacheFinish(String result, boolean isCache) {
		refreshProgressBar.setVisibility(View.GONE);
		if (isUserTabs) {
			try {
				String first = updateTABs(result);
				if (first == null && first.equals("")) {
					setListAdapter(null);
					return;
				}
				String[] titleAndPath = first.split("&");
				getPopupWindow();
				mTitle.setText(titleAndPath[0]);
				path = titleAndPath[1];
				tabSelectedPos = 0;
				init();
				getData();
				return;
			} catch (Exception e) {
				DocLog.e(TAG, "Exception", e);
			}
		} else {
			if (isCache) {
				if (tabSelectedPos != -1) {
					hasCache |= 1 << tabSelectedPos;
				}
				updateData(result, isCache);
			} else {
				if (isSearch) {
					updateData(result, isCache);
				} else {
					if (JsonErrorProcess.checkJsonError(result, this)) {
						updateData(result, isCache);
					} else {
						if (isLoadMore) {
							addFooterView();
						} else {
							if ((hasCache & (1 << tabSelectedPos)) == 0) {
								setListAdapter(null);
							}
						}
					}
				}
			}
		}

	}

	protected void handleError() {
		loadingProgressBar.setVisibility(View.GONE);
		retryLinearLayout.setVisibility(View.VISIBLE);
		refreshProgressBar.setVisibility(View.GONE);
	}

	private void addFooterView() {
		ListView mListView = getListView();
		if (resultDoctorType == DoctorTabItem.FAVOURITE) {
			if (loadMoreView != null)
				mListView.removeFooterView(loadMoreView);
		} else {
			if (loadMoreView != null) {
				mListView.removeFooterView(loadMoreView);
			}
			if (hasMore()) {
				loadMoreView = this.getLayoutInflater().inflate(
						R.layout.load_more, null, false);
				Button loadMore = (Button) loadMoreView
						.findViewById(R.id.btLoadMore);
				loadMore.setText(R.string.user_get_50_more);
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
	}

	public boolean hasMore() {
		if (getUserAdd() < PAGE_COUNT) {
			return false;
		} else if (getUserAdd() == PAGE_COUNT) {
			if (getUserAdd() < getmQueryCount()) {
				return true;
			} else {
				return false;
			}
		} else {
			return true;
		}
	}

	public String updateTABs(String result) {
		String first = "";
		if (doctorTabList == null) {
			doctorTabList = new ArrayList<DoctorTabItem>();
		} else {
			doctorTabList.clear();
		}
		try {
			JSONObject jsonObj = new JSONObject(result);
			JSONArray jsonArr = jsonObj.getJSONArray("data");
			for (int i = 0, len = jsonArr.length(); i < len; i++) {
				JSONObject tab = jsonArr.optJSONObject(i);
				DoctorTabItem item = new DoctorTabItem();
				int tabType = Integer.parseInt(tab.getString("tab_type"));
				switch (tabType) {
				case 1:
					item.setResultType(DoctorTabItem.PROVIDER);
					break;
				case 2:
					item.setResultType(DoctorTabItem.STAFF);
					break;
				case 3:
					item.setResultType(DoctorTabItem.PROVIDER);
					break;
				case 4:
					item.setResultType(DoctorTabItem.STAFF);
					break;
				case 5:
					item.setResultType(DoctorTabItem.PROVIDER);
					break;
				case 6:
					item.setResultType(DoctorTabItem.LOCAL_PRACTICEE);
					break;
				case 7:
					item.setResultType(DoctorTabItem.ORG);
					break;
				case 8:
					item.setResultType(DoctorTabItem.FAVOURITE);
					break;
				}
				String tabName = tab.getString("tab_name");
				item.setName(tabName);
				String url = tab.getString("url").substring(18);
				item.setUrl(url);
				if (i == 0) {
					first = tabName + "&" + url;
				}
				doctorTabList.add(item);
			}
		} catch (JSONException e) {
			DocLog.e(TAG, "JSONException", e);
		}
		return first;
	}

	private static class ViewHolder {
		TextView alpha;
		TextView name;
	}

	private class ListAdapter extends BaseAdapter {
		private LayoutInflater inflater;
		private List<ContentValues> list;
		private HashMap<String, Integer> alphaIndexer;
		private String[] sections;
		private Context mcontext;

		public ListAdapter(Context context) {
			mcontext = context;
		}

		private void configParams() {
			this.inflater = LayoutInflater.from(mcontext);
			this.alphaIndexer = new HashMap<String, Integer>();
			this.sections = new String[list.size()];

			for (int i = 0; i < list.size(); i++) {
				String name = getAlpha(list.get(i).getAsString(SORT_KEY));
				if (!alphaIndexer.containsKey(name)) {
					alphaIndexer.put(name, i);
				}
			}
			Set<String> sectionLetters = alphaIndexer.keySet();
			ArrayList<String> sectionList = new ArrayList<String>(
					sectionLetters);
			Collections.sort(sectionList);
			sections = new String[sectionList.size()];
			sectionList.toArray(sections);

			alpha.setAlphaIndexer(alphaIndexer);
		}

		@Override
		public int getCount() {
			return list.size();
		}

		@Override
		public ContentValues getItem(int position) {
			return list.get(position);
		}

		@Override
		public long getItemId(int position) {
			return position;
		}

		public void addItem(ContentValues item) {
			if (list == null) {
				list = new ArrayList<ContentValues>();
			}
			list.add(item);
		}

		public void addItems(List<ContentValues> items) {
			for (int i = 0, length = items.size(); i < length; i++) {
				ContentValues item = items.get(i);
				addItem(item);
			}
			configParams();
		}

		public void initItems(List<ContentValues> items) {
			if (list != null) {
				list.clear();
				list = null;
			} else {
				list = new ArrayList<ContentValues>();
			}
			if (items != null) {
				addItems(items);
			}
			configParams();
		}

		@Override
		public View getView(int position, View convertView, ViewGroup parent) {
			ViewHolder holder;

			if (convertView == null) {
				convertView = inflater.inflate(R.layout.list_item, null);
				holder = new ViewHolder();
				holder.alpha = (TextView) convertView.findViewById(R.id.alpha);
				holder.name = (TextView) convertView.findViewById(R.id.name);
				convertView.setTag(holder);
			} else {
				holder = (ViewHolder) convertView.getTag();
			}
			ContentValues cv = list.get(position);
//			String name = cv.getAsString(LAST_NAME) + " "
//					+ cv.getAsString(FIRST_NAME);
			String name = cv.getAsString(FULL_NAME);
			holder.name.setText(name);

			String currentStr = getAlpha(list.get(position).getAsString(
					SORT_KEY));
			String previewStr = (position - 1) >= 0 ? getAlpha(list.get(
					position - 1).getAsString(SORT_KEY)) : " ";
			if (!previewStr.equals(currentStr)) {
				holder.alpha.setVisibility(View.VISIBLE);
				holder.alpha.setText(currentStr);
			} else {
				holder.alpha.setVisibility(View.GONE);
			}
			return convertView;
		}
	}

	private String getAlpha(String str) {
		if (str == null) {
			return "#";
		}

		if (str.trim().length() == 0) {
			return "#";
		}

		char c = str.trim().substring(0, 1).charAt(0);
		Pattern pattern = Pattern.compile("^[A-Za-z]+$");
		if (pattern.matcher(c + "").matches()) {
			return (c + "").toUpperCase(Locale.US);
		} else {
			return "#";
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