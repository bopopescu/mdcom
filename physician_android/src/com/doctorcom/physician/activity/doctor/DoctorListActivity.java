package com.doctorcom.physician.activity.doctor;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import android.annotation.SuppressLint;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.graphics.drawable.BitmapDrawable;
import android.os.Bundle;
import android.support.v4.app.FragmentActivity;
import android.support.v4.app.FragmentManager;
import android.support.v4.app.ListFragment;
import android.support.v4.content.LocalBroadcastManager;
import android.text.Html;
import android.view.KeyEvent;
import android.view.LayoutInflater;
import android.view.Menu;
import android.view.MenuInflater;
import android.view.View;
import android.view.ViewGroup;
import android.view.ViewGroup.LayoutParams;
import android.widget.AdapterView;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ListView;
import android.widget.PopupWindow;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;

import com.doctorcom.android.R;
import com.doctorcom.physician.AppValues;
import com.doctorcom.physician.activity.main.NavigationActivity.RefreshListener;
import com.doctorcom.physician.net.ImageDownload;
import com.doctorcom.physician.net.NetConstantValues;
import com.doctorcom.physician.net.http.NetConncet;
import com.doctorcom.physician.utils.DocLog;
import com.doctorcom.physician.utils.JsonErrorProcess;
import com.doctorcom.physician.utils.PreferLogo;
import com.doctorcom.physician.utils.cache.Cache;

public class DoctorListActivity extends FragmentActivity {

	@Override
	protected void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
		FragmentManager fm = getSupportFragmentManager();

		// Create the list fragment and add it as our sole content.
		if (fm.findFragmentById(android.R.id.content) == null) {
			DoctorListFragment list = new DoctorListFragment();
			fm.beginTransaction().add(android.R.id.content, list).commit();
		}
	}

	public static class DoctorListFragment extends ListFragment implements
			Cache.CacheFinishListener, RefreshListener {
		private static final int NON_FAVOURITE = 0;
		private static final int FAVOURITE = 1;
		private static final int REFRESH = 10;
		private static final int FAVOURITE_REFRESH = 11;
		private static final int PAGE_COUNT = 50;
		private final String TAG = "DoctorListFragment";
		private TextView mTitle;
		private Button selectButton;
		private LinearLayout llContent;
		private ImageView orgLogoImageView;
		private ProgressBar refreshProgressBar;
		private PopupWindow popupWindow;
		private DoctorAdapter doctorAdapter;
		private PracticeAdapter practiceAdapter;
		private FavouriteAdapter favouriteAdapter;
		private List<DoctorItem> doctorList;
		private List<PracticeItem> practiceList;
		private List<FavoriteItem> favouriteList;
		private List<DoctorTabItem> doctorTabList;
		private String path, asterisk;
		private int resultDoctorType;
		private boolean isSearch = false, isUserTabs;
		private int hasCache;
		private int tabSelectedPos;
		private HashMap<String, String> params;
		private ListView tabListView;
		private Context context;
		private boolean hasFavourite = false;

		private LocalBroadcastManager broadcastManager;
		private final String UPDATE_USER_TABS = "updateUserTabs";
		private UserTabsReceiver userTabsReceiver;
		private String firstName;
		private String lastName;
		private String id;
		private boolean isLoadMore;
		private int mQueryCount;
		private String practiceName;
		private int userAdd;
		private View loadMoreView;
		private ListView mListView;
		private EditText etSearch;
		private int requestCount;
		private TextView tvSearchHeader;
		private LinearLayout loadingLinearLayout;
		private LinearLayout retryLinearLayout;
		private ProgressBar loadingProgressBar;
		private Button yesButton;
		private Button noButton;
		// imitational codes
		// **************************************************************
		private int start;

		// **************************************************************

		@Override
		public void onCreate(Bundle savedInstanceState) {
			super.onCreate(savedInstanceState);
			setHasOptionsMenu(true);
		}

		@SuppressLint("CutPasteId")
		@Override
		public View onCreateView(LayoutInflater inflater, ViewGroup container,
				Bundle savedInstanceState) {
			View view = inflater.inflate(R.layout.fragment_doctor_list,
					container, false);
			refreshProgressBar = (ProgressBar) view
					.findViewById(R.id.pbRefresh);
			llContent = (LinearLayout) view.findViewById(R.id.llContent);
			tvSearchHeader = (TextView) view.findViewById(R.id.tvSearchHeader);
			mTitle = (TextView) view.findViewById(R.id.tvDC);
			selectButton = (Button) view.findViewById(R.id.btSelect);
			orgLogoImageView = (ImageView) view
					.findViewById(R.id.imageview_org_logo);
			orgLogoImageView.setVisibility(View.INVISIBLE);

			final EditText searchEditText = (EditText) view
					.findViewById(R.id.etSearch);
			etSearch = (EditText) view.findViewById(R.id.etSearch);
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
							orgLogoImageView.setVisibility(View.INVISIBLE);
							search(result);
						}
					}
					return false;
				}

			});
			loadingLinearLayout = (LinearLayout) view
					.findViewById(R.id.linearLoading);
			retryLinearLayout = (LinearLayout) view
					.findViewById(R.id.linearRetry);
			loadingProgressBar = (ProgressBar) view
					.findViewById(R.id.progressbar_loading);
			yesButton = (Button) view.findViewById(R.id.button_yes);
			noButton = (Button) view.findViewById(R.id.button_no);
			return view;
		}

		@Override
		public void onResume() {
			super.onResume();
			initParams();
			init();
			getUserTABS();
			DocLog.d(TAG, "DoctorListFragment onResume");
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

		private void search(String name) {
			init();
			resultDoctorType = DoctorTabItem.PROVIDER;
			isSearch = true;
			llContent.setVisibility(View.GONE);
			tabSelectedPos = -1;
			params.put(NetConstantValues.SEARCH_USER.PARAM_NAME, name);
			params.put(NetConstantValues.SEARCH_USER.PARAM_LIMIT,
					String.valueOf(PAGE_COUNT));
			mTitle.setText(R.string.search);
			path = NetConstantValues.SEARCH_USER.PATH;
			getData();

		}

		protected void init() {
			doctorList = new ArrayList<DoctorItem>();
			practiceList = new ArrayList<PracticeItem>();
			favouriteList = new ArrayList<FavoriteItem>();
			doctorAdapter = new DoctorAdapter(context);
			practiceAdapter = new PracticeAdapter(context);
			favouriteAdapter = new FavouriteAdapter(context);
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
			practiceName = "";
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

		@Override
		public void onActivityCreated(Bundle savedInstanceState) {
			super.onActivityCreated(savedInstanceState);
			context = this.getActivity();
			broadcastManager = LocalBroadcastManager.getInstance(context);
			userTabsReceiver = new UserTabsReceiver();
			IntentFilter filter = new IntentFilter(this.UPDATE_USER_TABS);
			broadcastManager.registerReceiver(userTabsReceiver, filter);
			mListView = this.getListView();
		}

		public void getUserTABS() {
			refreshProgressBar.setVisibility(View.VISIBLE);
			mTitle.setText(R.string.loading);
			isUserTabs = true;
			doctorTabList = new ArrayList<DoctorTabItem>();
			HashMap<String, String> pms = new HashMap<String, String>();
			pms.put(NetConstantValues.USER_TABS.SHOW_MY_FAVORITE,
					String.valueOf(true));
			Cache cache = new Cache(context, NetConncet.HTTP_POST);
			cache.setCacheType(Cache.CACHE_USER_TABS);
			cache.useCache(this, NetConstantValues.USER_TABS.PATH, null, pms);
		}

		protected void getData() {
			initParams();
			if (!(resultDoctorType == DoctorTabItem.ORG))
				PreferLogo.showPreferLogo(context, orgLogoImageView);
			isUserTabs = false;
			refreshProgressBar.setVisibility(View.VISIBLE);
			params.put(NetConstantValues.USER_LIST.NAME, practiceName);
			params.put(NetConstantValues.USER_LIST.FIRST_NAME, firstName);
			params.put(NetConstantValues.USER_LIST.LAST_NAME, lastName);
			params.put(NetConstantValues.USER_LIST.ID,
					DoctorListFragment.this.id);
			params.put(NetConstantValues.USER_LIST.COUNT, String.valueOf(25));
			Cache cache = new Cache(context, NetConncet.HTTP_POST);
			cache.setCacheType(Cache.CACHE_USER_LIST);
			cache.useCache(this, path, asterisk, params);
		}

		protected void initPopuptWindow() {
			View popupWindowView = LayoutInflater.from(context).inflate(
					R.layout.dropdown_doctor_tab, null);
			tabListView = (ListView) popupWindowView
					.findViewById(R.id.listview_user_select);
			final TabListAdapter tabListAdapter = new TabListAdapter(context,
					R.layout.cell_dropdown_doctor_tab,
					R.id.textview_users_select, doctorTabList);
			tabListView.setAdapter(tabListAdapter);
			tabListView
					.setOnItemClickListener(new AdapterView.OnItemClickListener() {

						@Override
						public void onItemClick(AdapterView<?> parent,
								View view, int position, long id) {
							popupWindow.dismiss();
							isSearch = false;
							tabSelectedPos = position;
							llContent.setVisibility(View.GONE);
							DoctorTabItem item = tabListAdapter
									.getItem(position);
							if ("".equals(item.getLogo_middle())) {
								orgLogoImageView.setVisibility(View.INVISIBLE);
							} else {
								ImageDownload download = new ImageDownload(
										context, "org"
												+ String.valueOf(item.getId()),
										orgLogoImageView,
										R.drawable.avatar_male_small);
								AppValues appValues = new AppValues(context);
								String orgLogoMiddle = item.getLogo_middle();
								download.execute(appValues.getServerURL()
										+ orgLogoMiddle);
								orgLogoImageView.setVisibility(View.VISIBLE);
							}

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
					selectButton.getWidth() * 231 / 90,
					LayoutParams.WRAP_CONTENT);
			popupWindow.setBackgroundDrawable(new BitmapDrawable());
			// popupWindow.setOutsideTouchable(true);
			// popupWindow.update();
			// popupWindow.setTouchable(true);
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

		@Override
		public void onCacheFinish(String result, boolean isCache) {
			if (isUserTabs) {
				try {
					String first = updateTABs(result);
					if (first == null) {
						loadingLinearLayout.setVisibility(View.GONE);
						llContent.setVisibility(View.VISIBLE);
						refreshProgressBar.setVisibility(View.GONE);
						mTitle.setText(R.string.error_occur);
						setListAdapter(null);
						return;
					}
					DoctorTabItem item = null;
					initPopuptWindow();
					if (!isCache)
						path = null;
					if (path == null) {
						String[] titleAndPath = first.split("&");
						mTitle.setText(titleAndPath[0]);
						path = titleAndPath[1];
						tabSelectedPos = 0;
						item = doctorTabList.get(tabSelectedPos);
						resultDoctorType = item.getResultType();
					} else {
						if (isSearch) {
							mTitle.setText(R.string.search);
							resultDoctorType = DoctorTabItem.PROVIDER;
						} else {
							item = doctorTabList.get(tabSelectedPos);
							mTitle.setText(item.getName());
							resultDoctorType = item.getResultType();
							path = item.getUrl();
						}
					}

					// if (!isCache) {
					init();
					getData();
					// }
					// else
					// {
					// refreshProgressBar.setVisibility(View.GONE);
					// }
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
						if (JsonErrorProcess.checkJsonError(result,
								this.getActivity())) {
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

		public String updateTABs(String result) {
			String first = null;
			if (doctorTabList == null) {
				doctorTabList = new ArrayList<DoctorTabItem>();
			}
			try {
				JSONObject jsonObj = new JSONObject(result);
				if (jsonObj.isNull("errno")) {
					doctorTabList.clear();
					JSONArray jsonArr = jsonObj.getJSONArray("data");
					for (int i = 0, len = jsonArr.length(); i < len; i++) {
						JSONObject tab = jsonArr.optJSONObject(i);
						DoctorTabItem item = new DoctorTabItem();
						String id = tab.getString("org_id");
						int tabType = Integer.parseInt(tab
								.getString("tab_type"));
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
						item.setId(id);
						String tabName = tab.getString("tab_name");
						item.setName(tabName);
						item.setLogo(tab.getString("logo"));
						item.setLogo_middle(tab.getString("logo_middle"));
						String url = tab.getString("url").substring(18);
						item.setUrl(url);
						if (i == 0) {
							first = tabName + "&" + url;
						}
						doctorTabList.add(item);
					}
				} else {
					Toast.makeText(context, jsonObj.getString("descr"),
							Toast.LENGTH_LONG).show();
				}
			} catch (JSONException e) {
				DocLog.e(TAG, "JSONException", e);
			}
			return first;
		}

		protected void handleError() {
			loadingProgressBar.setVisibility(View.GONE);
			retryLinearLayout.setVisibility(View.VISIBLE);
			refreshProgressBar.setVisibility(View.GONE);
		}

		public void updateData(String result, boolean isCache) {

			if (isCache) {
				if (tabSelectedPos != -1) {
					hasCache |= 1 << tabSelectedPos;
				}
			}
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
						/*
						 * if (requestCount == 3) { if (jsonObj.isNull("count"))
						 * this.handleError(); return; }
						 */
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
						/*
						 * if (requestCount == 3) { if (jsonObj.isNull("count"))
						 * this.handleError(); return; }
						 */
						// **************************************************************
					}
					JSONArray jsonArr;
					DocLog.d(TAG, "doctorType: " + resultDoctorType);
					if (resultDoctorType == DoctorTabItem.LOCAL_PRACTICEE) {
						jsonArr = jsonObj.getJSONObject("data").getJSONArray(
								"practices");
						int length = jsonArr.length();
						// will be recovered
						// **************************************************************
						/*
						 * setUserAdd(length); int queryCount = 0; if
						 * (!jsonObj.getJSONObject("data")
						 * .isNull("query_count")) queryCount =
						 * jsonObj.getJSONObject("data").getInt( "query_count");
						 * setmQueryCount(queryCount); practiceList.clear();
						 * 
						 * for (int i = 0; i < length; i++) { PracticeItem item
						 * = new PracticeItem(); JSONObject practice =
						 * jsonArr.optJSONObject(i);
						 * item.setId(practice.getInt("id"));
						 * item.setPracticeName(practice
						 * .getString("practice_name"));
						 * item.setHasMobile(practice.getBoolean("has_mobile"));
						 * item.setHasManager(practice
						 * .getBoolean("has_manager"));
						 * item.setPracticePhoto(practice
						 * .getString("practice_photo")); if
						 * (!practice.isNull("is_favorite")) { hasFavourite =
						 * true; item.setIs_favorite(practice
						 * .getBoolean("is_favorite")); }
						 * practiceList.add(item); }
						 */

						// imitational codes
						// **************************************************************
						int queryCount = length - start;
						int size;
						if (queryCount < PAGE_COUNT)
							size = queryCount;
						else
							size = PAGE_COUNT;
						setUserAdd(size);
						setmQueryCount(queryCount);
						practiceList.clear();
						for (int i = start; i < start + size; i++) {
							PracticeItem item = new PracticeItem();
							JSONObject practice = jsonArr.optJSONObject(i);
							item.setId(practice.getInt("id"));
							item.setPracticeName(practice
									.getString("practice_name"));
							item.setHasMobile(practice.getBoolean("has_mobile"));
							item.setHasManager(practice
									.getBoolean("has_manager"));
							item.setPracticePhoto(practice
									.getString("practice_photo"));
							if (!practice.isNull("is_favorite")) {
								hasFavourite = true;
								item.setIs_favorite(practice
										.getBoolean("is_favorite"));
							}
							practiceList.add(item);
						}
						if (isLoadMore)
							start += size;
						else
							start = PAGE_COUNT;
						// **************************************************************

						if (length > 0) {
							JSONObject practice = jsonArr
									.optJSONObject(length - 1);
							id = String.valueOf(practice.getInt("id"));
							practiceName = practice.getString("practice_name");
						}
						addFooterView();
						if (isLoadMore) {
							practiceAdapter.addItems(practiceList);
							practiceAdapter.notifyDataSetChanged();
						} else {
							practiceAdapter.initItems(practiceList);
							setListAdapter(practiceAdapter);
						}
					} else if (resultDoctorType == DoctorTabItem.FAVOURITE) {
						hasFavourite = true;
						jsonArr = jsonObj.getJSONObject("data").getJSONArray(
								"favorites");
						int length = jsonArr.length();
						favouriteList.clear();
						for (int i = 0; i < length; i++) {
							FavoriteItem item = new FavoriteItem();
							JSONObject favourite = jsonArr.optJSONObject(i);
							item.setCall_available(favourite
									.getBoolean("call_available"));
							item.setPrefer_logo(favourite
									.getString("prefer_logo"));
							item.setMsg_available(favourite
									.getBoolean("msg_available"));
							item.setObject_id(favourite.getInt("object_id"));
							item.setObject_name(favourite
									.getString("object_name"));
							item.setObject_type_display(favourite
									.getString("object_type_display"));
							item.setObject_type_flag(favourite
									.getInt("object_type_flag"));
							item.setPager_available(favourite
									.getBoolean("pager_available"));
							item.setPhoto(favourite.getString("photo"));
							favouriteList.add(item);
						}
						addFooterView();
						favouriteAdapter.setItem(favouriteList);
						setListAdapter(favouriteAdapter);
					} else {
						if (isSearch) {
							jsonArr = jsonObj.getJSONObject("data")
									.getJSONArray("results");
							int count = 0;
							if (!jsonObj.getJSONObject("data").isNull(
									"total_count"))
								count = jsonObj.getJSONObject("data").getInt(
										"total_count");
							else
								count = jsonArr.length();
							String searchHeader = CommonDoctorMethods
									.getTotalCountStr(count, getActivity());
							this.addSearchHeader(searchHeader);
						} else {
							jsonArr = jsonObj.getJSONObject("data")
									.getJSONArray("users");
						}
						int length = jsonArr.length();

						// will be recovered
						// **************************************************************
//
//						setUserAdd(length);
//
//						@SuppressWarnings("unused")
//						int queryCount = 0;
//						if (!jsonObj.getJSONObject("data")
//								.isNull("query_count"))
//							queryCount = jsonObj.getJSONObject("data").getInt(
//									"query_count");
//						doctorList.clear();
//						for (int i = 0; i < length; i++) {
//							DoctorItem item = new DoctorItem();
//							JSONObject doctor = jsonArr.optJSONObject(i);
//							item.setId(doctor.getInt("id"));
//							item.setFirstName(doctor.getString("first_name"));
//							item.setLastName(doctor.getString("last_name"));
//							item.setHasPager(doctor.getBoolean("has_pager"));
//							item.setThumbnail(doctor.getString("thumbnail"));
//							item.setFullname(doctor.getString("fullname"));
//							if (resultDoctorType == DoctorTabItem.STAFF) {
//								item.setSpecialty(doctor
//										.getString("staff_type"));
//							} else {
//								item.setSpecialty(doctor.getString("specialty"));
//							}
//							item.setHasMobile(doctor.getBoolean("has_mobile"));
//							item.setPracticePhoto(doctor
//									.getString("practice_photo"));
//							item.setPrefer_logo(doctor.getString("prefer_logo"));
//							if (!doctor.isNull("is_favorite")) {
//								hasFavourite = true;
//								item.setIs_favorite(doctor
//										.getBoolean("is_favorite"));
//							}
//							doctorList.add(item);
//						}

						// **************************************************************

						// imitational codes
						// **************************************************************
						int queryCount = length - start;
						int size;
						if (queryCount < PAGE_COUNT)
							size = queryCount;
						else
							size = PAGE_COUNT;
						setUserAdd(size);
						setmQueryCount(queryCount);
						doctorList.clear();
						for (int i = start; i < start + size; i++) {
							DoctorItem item = new DoctorItem();
							JSONObject doctor = jsonArr.optJSONObject(i);
							item.setId(doctor.getInt("id"));
							item.setFirstName(doctor.getString("first_name"));
							item.setLastName(doctor.getString("last_name"));
							item.setHasPager(doctor.getBoolean("has_pager"));
							item.setThumbnail(doctor.getString("thumbnail"));
							item.setFullname(doctor.getString("fullname"));
							if (resultDoctorType == DoctorTabItem.STAFF) {
								item.setSpecialty(doctor
										.getString("staff_type"));
							} else {
								item.setSpecialty(doctor.getString("specialty"));
							}
							item.setHasMobile(doctor.getBoolean("has_mobile"));
							item.setPracticePhoto(doctor
									.getString("practice_photo"));
							item.setPrefer_logo(doctor.getString("prefer_logo"));
							if (!doctor.isNull("is_favorite")) {
								hasFavourite = true;
								item.setIs_favorite(doctor
										.getBoolean("is_favorite"));
							}
							doctorList.add(item);
						}
						if (isLoadMore)
							start += size;
						else
							start = PAGE_COUNT;
						// **************************************************************
						if (length > 0) {
							JSONObject doctor = jsonArr
									.optJSONObject(length - 1);
							id = String.valueOf(doctor.getInt("id"));
							firstName = doctor.getString("first_name");
							lastName = doctor.getString("last_name");
						}
						addFooterView();
						if (isLoadMore) {
							doctorAdapter.addItems(doctorList);
							doctorAdapter.notifyDataSetChanged();
						} else {
							doctorAdapter.initItems(doctorList);
							setListAdapter(doctorAdapter);
						}
						requestCount = 0;
					}
				}

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
			}
			loadingLinearLayout.setVisibility(View.GONE);
			refreshProgressBar.setVisibility(View.GONE);
			llContent.setVisibility(View.VISIBLE);
		}

		@Override
		public void onListItemClick(ListView l, View v, int position, long id) {
			if (resultDoctorType == DoctorTabItem.LOCAL_PRACTICEE) {
				PracticeItem item = practiceAdapter.getItem(position);
				if (null == item)
					return;
				Intent intent = new Intent(context,
						PracticeDetailActivity.class);
				intent.putExtra("practiceId", item.getId());
				if (hasFavourite)
					intent.putExtra("listIsFavourite", item.isIs_favorite());
				intent.putExtra("path", path);
				this.startActivityForResult(intent, NON_FAVOURITE);
				// this.startActivity(intent);
			} else if (resultDoctorType == DoctorTabItem.FAVOURITE) {
				FavoriteItem item = favouriteAdapter.getItem(position);
				if (null == item)
					return;
				if (item.getObject_type_flag() == 2) {
					Intent intent = new Intent(context,
							PracticeDetailActivity.class);
					intent.putExtra("practiceId", item.getObject_id());
					if (hasFavourite)
						intent.putExtra("listIsFavourite", true);
					intent.putExtra("path", path);
					this.startActivityForResult(intent, FAVOURITE);
					// this.startActivity(intent);
				} else {
					Intent intent = new Intent(context,
							DoctorDetailActivity.class);
					intent.putExtra("userId", item.getObject_id());
					intent.putExtra("name", item.getObject_name());
					if (hasFavourite)
						intent.putExtra("listIsFavourite", true);
					intent.putExtra("path", path);
					this.startActivityForResult(intent, FAVOURITE);
					// this.startActivity(intent);
				}
			} else {
				DoctorItem item = doctorAdapter.getItem(position);
				if (null == item)
					return;
				Intent intent = new Intent(context, DoctorDetailActivity.class);
				intent.putExtra("userId", item.getId());
				intent.putExtra("name",
						item.getFirstName() + " " + item.getLastName());
				if (hasFavourite)
					intent.putExtra("listIsFavourite", item.isIs_favorite());
				intent.putExtra("path", path);
				this.startActivityForResult(intent, NON_FAVOURITE);
				// this.startActivity(intent);
			}

		}

		private void addFooterView() {
			if (resultDoctorType == DoctorTabItem.FAVOURITE) {
				if (loadMoreView != null)
					mListView.removeFooterView(loadMoreView);
			} else {
				if (loadMoreView != null) {
					mListView.removeFooterView(loadMoreView);
				}
				if (hasMore()) {
					loadMoreView = this.getActivity().getLayoutInflater()
							.inflate(R.layout.load_more, null, false);
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

		private void addSearchHeader(String searchHeader) {
			tvSearchHeader.setVisibility(View.VISIBLE);
			tvSearchHeader.setText(searchHeader);
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
		public void refreshView() {
			getUserTABS();
		}

		@Override
		public void onCreateOptionsMenu(Menu menu, MenuInflater inflater) {
			super.onCreateOptionsMenu(menu, inflater);
			menu.add(0, R.id.iRefresh, 2, R.string.refresh);
		}

		@Override
		public void onHiddenChanged(boolean hidden) {
			super.onHiddenChanged(hidden);
			if (!hidden) {
				etSearch.setError(null);
				init();
				refreshView();
			}
		}

		@Override
		public void forceRefreshView() {
			Cache.cleanListCache(String.valueOf(Cache.CACHE_USER_LIST), path,
					DoctorListFragment.this.getActivity()
							.getApplicationContext());
			refreshView();
		}

		@Override
		public void onActivityResult(int requestCode, int resultCode,
				Intent data) {
			// TODO Auto-generated method stub
			super.onActivityResult(requestCode, resultCode, data);

			if (resultCode == REFRESH) {
				getData();
			}
			if (resultCode == FAVOURITE_REFRESH) {
				getData();
			}
		}

		class UserTabsReceiver extends BroadcastReceiver {

			@Override
			public void onReceive(Context context, Intent intent) {
				if (DoctorListFragment.this.isResumed())
					refreshView();
			}
		}

	}

}
