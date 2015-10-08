package com.doctorcom.physician.activity.message;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.io.UnsupportedEncodingException;
import java.nio.charset.Charset;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Timer;
import java.util.TimerTask;
import java.util.Map.Entry;

import javax.net.ssl.HostnameVerifier;
import javax.net.ssl.HttpsURLConnection;

import org.apache.http.Header;
import org.apache.http.HttpResponse;
import org.apache.http.HttpVersion;
import org.apache.http.client.ClientProtocolException;
import org.apache.http.client.HttpClient;
import org.apache.http.client.methods.HttpPost;
import org.apache.http.conn.params.ConnManagerParams;
import org.apache.http.conn.ssl.SSLSocketFactory;
import org.apache.http.conn.ssl.X509HostnameVerifier;
import org.apache.http.entity.mime.HttpMultipartMode;
import org.apache.http.entity.mime.content.FileBody;
import org.apache.http.entity.mime.content.StringBody;
import org.apache.http.impl.client.DefaultHttpClient;
import org.apache.http.message.BasicHeader;
import org.apache.http.message.BasicNameValuePair;
import org.apache.http.params.BasicHttpParams;
import org.apache.http.params.HttpConnectionParams;
import org.apache.http.params.HttpParams;
import org.apache.http.params.HttpProtocolParams;
import org.apache.http.protocol.BasicHttpContext;
import org.apache.http.protocol.HTTP;
import org.apache.http.protocol.HttpContext;
import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import android.app.Activity;
import android.app.AlertDialog;
import android.app.ProgressDialog;
import android.content.Context;
import android.content.DialogInterface;
import android.content.DialogInterface.OnCancelListener;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.database.Cursor;
import android.graphics.Bitmap;
import android.graphics.Bitmap.CompressFormat;
import android.graphics.BitmapFactory;
import android.net.Uri;
import android.os.AsyncTask;
import android.os.Bundle;
import android.os.Environment;
import android.provider.MediaStore;
import android.text.TextUtils.TruncateAt;
import android.util.SparseArray;
import android.view.Gravity;
import android.view.View;
import android.view.View.OnClickListener;
import android.view.ViewGroup.LayoutParams;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;

import com.doctorcom.android.R;
import com.doctorcom.physician.AppValues;
import com.doctorcom.physician.activity.doctor.DoctorDetailActivity;
import com.doctorcom.physician.net.CustomMultiPartEntity;
import com.doctorcom.physician.net.NetConstantValues;
import com.doctorcom.physician.net.http.NetConncet;
import com.doctorcom.physician.utils.DocLog;
import com.doctorcom.physician.utils.FileUtil;
import com.doctorcom.physician.utils.ScalingUtilities;
import com.doctorcom.physician.utils.ScalingUtilities.ScalingLogic;
import com.doctorcom.physician.utils.camera.CameraActivity;
import com.doctorcom.physician.utils.Utils;

public class MessageNewActivity extends Activity {
	private final String TAG = "MessageNewActivity";
	public static final int NEW_MESSAGE = 0;
	public static final int REPLY_MESSAGE = 1;
	public static final int FORWARD_MESSAGE = 2;
	public static final int TO = 0;
	public static final int CC = 1;
	public static final int TAKE_PHOTO = 3;
	public static final int ADD_PHOTO = 4;
	private int MessageDispatcherObject = DoctorDetailActivity.MESSAGE_DISPATCHER_PROVIDER;// practice
																							// or
																							// provider
	private int rate = 100, offset = 0, type;
	private ProgressDialog progress = null, cancelProgressDialog = null;
	private EditText subjectEditText, contentEditText;
	LinearLayout toLinear, ccLinear;
	SparseArray<Button> toIds, ccIds;
	private List<String> normalAttachmentsList;
	private List<String> imageAttachmentList;
	private List<String> deprecatedAttachmentList;
	private List<Map<String, String>> forwardAttachmentsList;
	private String forwardMessageId, uuid;
	private boolean isRefer = false, hasReferId = true;
	private int practiceId;
	private AppValues appValues;
	private int transmissionMethod = 1;
	private static final int maxImageFileSize = 1000 * 1000;// 1 M
	private int recLen = 5;
	private AlertDialog sentSusAD;

	@Override
	protected void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
		setContentView(R.layout.activity_message_new);
		Intent intent = getIntent();
		type = intent.getIntExtra("type", NEW_MESSAGE);
		MessageDispatcherObject = intent.getIntExtra("dispatcher",
				DoctorDetailActivity.MESSAGE_DISPATCHER_PROVIDER);
		init();
		setInitMessageContent(type, intent);

	}

	private void init() {
		appValues = new AppValues(this);
		progress = new ProgressDialog(this) {

			@Override
			protected void onStop() {
				setProgress(0);
				super.onStop();
			}

		};
		progress.setProgressStyle(ProgressDialog.STYLE_HORIZONTAL);
		progress.setMessage(getResources().getText(R.string.message_checking));

		// set recipient
		toLinear = (LinearLayout) findViewById(R.id.vTo);
		toLinear.removeAllViews();
		ccLinear = (LinearLayout) findViewById(R.id.vCc);
		ccLinear.removeAllViews();
		toIds = new SparseArray<Button>();
		ccIds = new SparseArray<Button>();
		subjectEditText = (EditText) findViewById(R.id.etSubject);
		contentEditText = (EditText) findViewById(R.id.etContent);
		forwardAttachmentsList = new ArrayList<Map<String, String>>();
		Button toButton = (Button) findViewById(R.id.btAddTo);
		toButton.setOnClickListener(new Contacts(TO));
		Button ccButton = (Button) findViewById(R.id.btAddCc);
		ccButton.setOnClickListener(new Contacts(CC));
		if (MessageDispatcherObject == DoctorDetailActivity.MESSAGE_DISPATCHER_PRACTICE) {
			findViewById(R.id.llCc).setVisibility(View.GONE);
			toButton.setVisibility(View.GONE);
			findViewById(R.id.ivLine).setVisibility(View.GONE);
		}

		Button sendButton = (Button) findViewById(R.id.btSend);
		sendButton.setOnClickListener(new Send());
		Button closeButton = (Button) findViewById(R.id.btClose);
		closeButton.setOnClickListener(new View.OnClickListener() {

			@Override
			public void onClick(View v) {
				closeActivity();
			}
		});

		Button photoButton = (Button) findViewById(R.id.btPhoto);
		if (getPackageManager().hasSystemFeature(PackageManager.FEATURE_CAMERA)) {
			photoButton.setVisibility(View.VISIBLE);
			photoButton.setOnClickListener(btnTakePhotoClick);
		} else {
			photoButton.setVisibility(View.GONE);
		}

		Button addPhotoButton = (Button) findViewById(R.id.btAddPhoto);
		addPhotoButton.setOnClickListener(new View.OnClickListener() {

			@Override
			public void onClick(View v) {
				Intent intent = new Intent();
				intent.setType("image/*");
				intent.setAction(Intent.ACTION_PICK);
				startActivityForResult(intent, ADD_PHOTO);

			}
		});

		normalAttachmentsList = new ArrayList<String>();
		imageAttachmentList = new ArrayList<String>();
		deprecatedAttachmentList = new ArrayList<String>();

	}

	private void setInitMessageContent(int type, Intent intent) {
		TextView titleTextView = (TextView) findViewById(R.id.tvTitle);
		int userId = intent.getIntExtra("userId", -1);
		String name = intent.getStringExtra("name");
		String subject = "";
		String firstThreeChars = "";
		String targetSubject = "";
		final String re = getString(R.string.re);
		final String fw = getString(R.string.fw);
		switch (type) {
		case NEW_MESSAGE:
			setReplayMessage(userId, name, MessageDispatcherObject);
			break;
		case REPLY_MESSAGE:
			titleTextView.setText(R.string.reply_message);
			subject = intent.getStringExtra("subject");
			if (subject.length() >= 3) {
				firstThreeChars = subject.substring(0, 3);
				if (firstThreeChars.equalsIgnoreCase(re))
					targetSubject = subject;
				else if (firstThreeChars.equalsIgnoreCase(fw))
					targetSubject = re + subject.substring(3);
				else
					targetSubject = re + subject;
			} else
				targetSubject = re + subject;
			subjectEditText.setText(targetSubject);
			subjectEditText.setSelection(targetSubject.length());
			setReplayMessage(userId, name, MessageDispatcherObject);
			break;
		case FORWARD_MESSAGE:
			titleTextView.setText(R.string.forward_message);
			subject = intent.getStringExtra("subject");
			if (subject.length() >= 3) {
				firstThreeChars = subject.substring(0, 3);
				if (firstThreeChars.equalsIgnoreCase(fw))
					targetSubject = subject;
				else if (firstThreeChars.equalsIgnoreCase(re))
					targetSubject = fw + subject.substring(3);
				else
					targetSubject = fw + subject;
			} else
				targetSubject = fw + subject;
			subjectEditText.setText(targetSubject);
			subjectEditText.setSelection(targetSubject.length());
			forwardMessageId = intent.getStringExtra("messageId");
			setFowardMessage(subject, intent.getStringExtra("body"));
			break;
		}
	}

	private void setReplayMessage(int userId, String name,
			int MessageDispatcherObject) {
		if (userId != -1 && name != null) {// otherwise a new empty message
			LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
					LinearLayout.LayoutParams.WRAP_CONTENT,
					LinearLayout.LayoutParams.WRAP_CONTENT);
			lp.setMargins(5, 0, 3, 0);
			View vName;
			if (MessageDispatcherObject == DoctorDetailActivity.MESSAGE_DISPATCHER_PRACTICE) {
				vName = new TextView(this);
				((TextView) vName).setText(name);
				((TextView) vName).setTextColor(getResources().getColor(
						R.color.black));
				practiceId = userId;
			} else {
				vName = new Button(this);
				((Button) vName).setText(name);
				vName.setBackgroundResource(R.drawable.contact_remove_selector);
				((Button) vName).setTextColor(getResources().getColor(
						R.color.contact_color));
				toIds.append(userId, (Button) vName);
				vName.setOnClickListener(new View.OnClickListener() {

					@Override
					public void onClick(View v) {
						toLinear.removeView(v);
						int index = toIds.indexOfValue((Button) v);
						int key = toIds.keyAt(index);
						toIds.remove(key);

					}
				});
			}
			vName.setLayoutParams(lp);
			toLinear.addView(vName);
		}

	}

	private void setFowardMessage(String subject, String forwardBody) {
		try {
			JSONObject jData = new JSONObject(forwardBody);
			if (jData.isNull("refer")) {
				// message
				isRefer = false;
			} else {
				// refer
				isRefer = true;
				uuid = jData.getJSONObject("refer").getString("uuid");
				addAttachments(uuid, true);
			}
			StringBuffer content = new StringBuffer(
					"\r\n\r\n---------------------------------------\r\n");
			content.append(getString(R.string.from) + " ");
			content.append(jData.getJSONObject("sender").getString("name")
					+ "\r\n");
			content.append(getString(R.string.date) + " ");
			content.append(jData.getString("timestamp") + "\r\n");
			content.append(getString(R.string.to) + " ");
			JSONArray recipients = jData.getJSONArray("recipients");
			for (int i = 0, len = recipients.length(); i < len; i++) {
				JSONObject recipient = recipients.getJSONObject(i);
				String recipientName = recipient.getString("name");
				if (i == len - 1) {
					content.append(recipientName);
				} else {
					content.append(recipientName + ", ");
				}

			}
			content.append("\r\n");
			content.append(getString(R.string.subject) + " ");
			content.append(subject + "\r\n\r\n");
			content.append(jData.getString("body"));
			contentEditText.setText(content);
			// add attachments
			JSONArray jArr = jData.getJSONArray("attachments");
			for (int i = 0, len = jArr.length(); i < len; i++) {
				JSONObject jsonOpt = jArr.optJSONObject(i);
				String strAttchmentfileName = jsonOpt.getString("filename");
				String strAttchmentId = jsonOpt.getString("id");
				addAttachments(strAttchmentfileName, true);
				Map<String, String> map = new HashMap<String, String>();
				map.put("id", strAttchmentId);
				map.put("name", strAttchmentfileName);
				forwardAttachmentsList.add(map);

			}

		} catch (JSONException e) {
			DocLog.e(TAG, "JSONException", e);
		}

	}

	class Contacts implements View.OnClickListener {
		private int request;

		public Contacts(int request) {
			this.request = request;
		}

		@Override
		public void onClick(View v) {
			Intent intent = new Intent(MessageNewActivity.this,
					ContactsActivity.class);
			startActivityForResult(intent, request);
			overridePendingTransition(R.anim.up, R.anim.hold);
		}

	}

	@Override
	protected void onActivityResult(int requestCode, int resultCode, Intent data) {
		if (resultCode == RESULT_OK) {
			final int userId = data.getIntExtra("userId", -1);
			final String name = data.getStringExtra("firstName") + " "
					+ data.getStringExtra("lastName");
			Button bName = new Button(this);
			bName.setText(name);
			bName.setBackgroundResource(R.drawable.contact_remove_selector);
			bName.setTextColor(getResources().getColor(R.color.contact_color));
			LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
					LinearLayout.LayoutParams.WRAP_CONTENT,
					LinearLayout.LayoutParams.WRAP_CONTENT);
			lp.setMargins(5, 0, 3, 0);
			bName.setLayoutParams(lp);
			switch (requestCode) {
			case TO:
				if (toIds.get(userId) == null) {
					toLinear.addView(bName);
					toIds.append(userId, bName);
					bName.setOnClickListener(new View.OnClickListener() {

						@Override
						public void onClick(View v) {
							toLinear.removeView(v);
							int index = toIds.indexOfValue((Button) v);
							int key = toIds.keyAt(index);
							toIds.remove(key);

						}
					});
				}

				break;
			case CC:
				if (ccIds.get(userId) == null) {
					ccLinear.addView(bName);
					ccIds.append(userId, bName);
					bName.setOnClickListener(new View.OnClickListener() {

						@Override
						public void onClick(View v) {
							ccLinear.removeView(v);
							int index = ccIds.indexOfValue((Button) v);
							int key = ccIds.keyAt(index);
							ccIds.remove(key);

						}
					});
				}
				break;
			case TAKE_PHOTO:
				String image = data.getStringExtra("image");
				if (image != null && !image.equals("")) {
					addAttachments(image, false);
				}
				break;
			case ADD_PHOTO:
				Uri uri = data.getData();
				Cursor c = this.getContentResolver().query(uri, null, null,
						null, null);
				c.moveToFirst();
				int index = c
						.getColumnIndexOrThrow(MediaStore.Images.Media.DATA);
				String path = c.getString(index);
				if (path != null && !path.equals("")) {
					addAttachments(path, false);
				}
			}

		}
	}

	class Send implements View.OnClickListener {

		@Override
		public void onClick(View v) {
			// if(isRunning) {
			// if(!progress.isShowing()) progress.show();
			// return;
			// }
			if (toIds.size() == 0
					&& MessageDispatcherObject == DoctorDetailActivity.MESSAGE_DISPATCHER_PROVIDER) {
				Toast.makeText(MessageNewActivity.this, R.string.no_recipient,
						Toast.LENGTH_SHORT).show();
				return;
			}
			if (contentEditText.getText().toString().trim().equals("")) {
				Toast.makeText(MessageNewActivity.this,
						R.string.message_body_empty, Toast.LENGTH_LONG).show();
				contentEditText.requestFocus();
			} else {
				final boolean needCompress = checkNeedCompress(imageAttachmentList);
				if (needCompress) {
					AlertDialog.Builder builder = new AlertDialog.Builder(
							MessageNewActivity.this);
					builder.setTitle(R.string.compress_photo)
							.setPositiveButton(R.string.ok,
									new DialogInterface.OnClickListener() {
										public void onClick(
												DialogInterface dialog, int id) {
											dialog.dismiss();
											sendMessage(needCompress);
										}
									})
							.setNegativeButton(R.string.cancel,
									new DialogInterface.OnClickListener() {
										public void onClick(
												DialogInterface dialog, int id) {
											dialog.dismiss();
										}
									});
					builder.setSingleChoiceItems(
							R.array.photo_compress_item_select, 1,
							new DialogInterface.OnClickListener() {
								public void onClick(DialogInterface dialog,
										int item) {
									transmissionMethod = item;
								}
							}).create().show();
				} else {
					sendMessage(needCompress);
				}
			}

		}

	}

	protected void addAttachments(final String fileName, final boolean forward) {
		DocLog.d(TAG, "add attachment " + fileName);
		final LinearLayout linearLayout = (LinearLayout) findViewById(R.id.ll_attachment_list);
		final LinearLayout container = new LinearLayout(this);
		container.setLayoutParams(new LayoutParams(LayoutParams.MATCH_PARENT,
				LayoutParams.WRAP_CONTENT));
		container.setGravity(Gravity.CENTER_VERTICAL);
		LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
				LinearLayout.LayoutParams.WRAP_CONTENT,
				LinearLayout.LayoutParams.WRAP_CONTENT);
		lp.setMargins(5, 3, 3, 3);
		// set icon
		ImageView iconImageView = new ImageView(this);
		String fileType = FileUtil.getMIMEType(fileName);
		if (fileType.contains("audio")) {
			iconImageView.setImageResource(R.drawable.icon_video_file);
		} else if (fileType.contains("image")) {
			iconImageView.setImageResource(R.drawable.icon_img_file);
		} else {
			iconImageView.setImageResource(R.drawable.icon_other_file);
		}
		iconImageView.setLayoutParams(lp);
		// set filename
		TextView filenameTextView = new TextView(this);
		if (fileName.equals(uuid)) {
			filenameTextView.setText(getString(R.string.refer_pdf));
		} else {
			filenameTextView.setText(new File(fileName).getName());
		}
		filenameTextView.setEllipsize(TruncateAt.END);
		LinearLayout.LayoutParams filenameLayout = new LinearLayout.LayoutParams(
				LinearLayout.LayoutParams.WRAP_CONTENT,
				LinearLayout.LayoutParams.WRAP_CONTENT, 1);
		filenameTextView.setLayoutParams(filenameLayout);

		// set delete button
		ImageView deleteImageView = new ImageView(this);
		deleteImageView.setImageResource((R.drawable.icon_delete));
		deleteImageView.setLayoutParams(lp);
		deleteImageView.setOnClickListener(new View.OnClickListener() {

			@Override
			public void onClick(View v) {
				linearLayout.removeView(container);
				if (forward) {
					if (fileName.equals(uuid)) {
						hasReferId = false;
					} else {
						for (int i = 0, len = forwardAttachmentsList.size(); i < len; i++) {
							Map<String, String> map = forwardAttachmentsList
									.get(i);
							if (map.get("name").equals(fileName)) {
								forwardAttachmentsList.remove(map);
								break;
							}
						}
					}

				} else {
					if (FileUtil.getMIMEType(fileName).contains("image")) {
						imageAttachmentList.remove(fileName);
					} else {
						normalAttachmentsList.remove(fileName);
					}
				}

			}
		});
		container.addView(iconImageView);
		container.addView(filenameTextView);
		container.addView(deleteImageView);
		linearLayout.addView(container);
		if (!forward) {
			if (FileUtil.getMIMEType(fileName).contains("image")) {
				imageAttachmentList.add(fileName);
			} else {
				normalAttachmentsList.add(fileName);
			}
		}

	}

	public static boolean checkNeedCompress(List<String> list) {
		boolean needCompress = false;
		if (list != null) {
			for (int i = 0, len = list.size(); i < len; i++) {
				String file = list.get(i);
				if (FileUtil.getMIMEType(file).contains("image")) {
					if (FileUtil.getFileSize(file) > maxImageFileSize) {
						needCompress = true;
						break;
					}
				}
			}
		}
		return needCompress;
	}

	protected void compressPicture() {
		int i = 0, length = imageAttachmentList.size();
		int per = (10 / length) == 0 ? 1 : 10 / length;
		String[] value;
		Iterator<String> iterator = imageAttachmentList.iterator();
		value = new String[length];
		for (i = 0; iterator.hasNext(); i++) {
			value[i] = iterator.next();
		}
		progress.setProgress(1);
		switch (transmissionMethod) {
		case 0: {
			break;
		}
		case 1: {
			int speed;
			for (i = 0; i < length; i++) {
				if (fitBitmap(value[i], 1280, 1024)) {
					speed = (i + 1) > 10 ? 10 : i + 1;
					progress.setProgress(per * speed);
				} else
					return;

			}
			break;
		}
		case 2: {
			int speed;
			for (i = 0; i < length; i++) {
				if (fitBitmap(value[i], 1024, 768)) {
					speed = (i + 1) > 10 ? 10 : i + 1;
					progress.setProgress(per * speed);
				} else
					return;
			}
			break;
		}
		}// switch

	}

	/**
	 * Invoked when pressing button for showing result of the "Fit" decoding
	 * method
	 */
	protected boolean fitBitmap(String file, int mDstWidth, int mDstHeight) {
		int fileLen = FileUtil.getFileSize(file);
		if (fileLen == 0)
			return false;

		if (fileLen > maxImageFileSize) {
			BitmapFactory.Options opts = new BitmapFactory.Options();
			opts.inJustDecodeBounds = true;
			BitmapFactory.decodeFile(file, opts);
			int srcWidth = opts.outWidth;
			int srcHeight = opts.outHeight;
			DocLog.i(TAG, srcWidth + "*" + srcHeight);
			if (srcWidth <= 1280 && srcHeight <= 1024)
				return true;

			// Part 1: Decode image
			Bitmap unscaledBitmap = ScalingUtilities.decodeBitmap(file,
					mDstWidth, mDstHeight, ScalingLogic.FIT);

			// Part 2: Scale image
			Bitmap scaledBitmap = ScalingUtilities.createScaledBitmap(
					unscaledBitmap, mDstWidth, mDstHeight, ScalingLogic.FIT);
			unscaledBitmap.recycle();

			// Publish results
			if (scaledBitmap == null) {
				DocLog.e(TAG, "destBm null");
				return false;
			} else {
				String fileName = file.substring(file
						.lastIndexOf(File.separator));
				String fileNameWithoutExtension = fileName.substring(0,
						fileName.lastIndexOf("."));
				File destFile = new File(
						getExternalFilesDir(Environment.DIRECTORY_PICTURES)
								+ fileName);
				if (destFile.exists()) {
					destFile = new File(
							getExternalFilesDir(Environment.DIRECTORY_PICTURES)
									+ fileNameWithoutExtension + "_"
									+ mDstWidth + "_" + mDstHeight + ".jpg");
				}
				try {
					// create the file output stream
					OutputStream os = new FileOutputStream(destFile);
					// save
					scaledBitmap.compress(CompressFormat.JPEG, 100, os);
					// close the stream
					os.close();
					imageAttachmentList.remove(file);
					deprecatedAttachmentList.add(file);
					imageAttachmentList.add(destFile.getAbsolutePath());
					DocLog.d(
							TAG,
							"scale " + file + " to "
									+ destFile.getAbsolutePath());
				} catch (FileNotFoundException e) {
					// Toast.makeText(this, R.string.attchment_not_file,
					// Toast.LENGTH_LONG).show();
					DocLog.e(TAG, "FileNotFoundException", e);
					return false;
				} catch (IOException e) {
					DocLog.e(TAG, "IOException", e);
					return false;
				} finally {

				}
			}
		}
		return true;
	}

	private String checkSendLimited() {
		int toLen = toIds.size();
		int ccLen = ccIds.size();
		Map<String, String> map = new HashMap<String, String>();
		if (MessageDispatcherObject == DoctorDetailActivity.MESSAGE_DISPATCHER_PRACTICE) {
			map.put(NetConstantValues.MESSAGEING_MESSAGE_SENDCHECK.PARAM_PRACTICE_RECIPIENTS,
					String.valueOf(practiceId));
		} else {
			StringBuffer toSB = new StringBuffer();
			for (int i = 0; i < toLen; i++) {
				int key = toIds.keyAt(i);
				if (i == toLen - 1) {
					toSB.append(key);
				} else {
					toSB.append(key + ",");
				}
			}
			map.put(NetConstantValues.MESSAGEING_MESSAGE_SENDCHECK.PARAM_RECIPIENTS,
					toSB.toString());
		}

		if (ccLen != 0) {
			StringBuffer ccSB = new StringBuffer();
			for (int j = 0; j < ccLen; j++) {
				int key = ccIds.keyAt(j);
				if (j == ccLen - 1) {
					ccSB.append(key);
				} else {
					ccSB.append(key + ",");
				}
			}
			map.put(NetConstantValues.MESSAGEING_MESSAGE_SENDCHECK.PARAM_CCS,
					ccSB.toString());
		}
		map.put(NetConstantValues.MESSAGEING_MESSAGE_SENDCHECK.PARAM_ATTACHMENT_COUNT,
				String.valueOf(normalAttachmentsList.size()
						+ imageAttachmentList.size()));
		NetConncet netConncet = new NetConncet(this,
				NetConstantValues.MESSAGEING_MESSAGE_SENDCHECK.PATH, map);
		return netConncet.connect(0);
	}

	protected void sendMessage(boolean needCompress) {
		int toLen = toIds.size();
		int ccLen = ccIds.size();
		int nLen = normalAttachmentsList.size();
		int iLen = imageAttachmentList.size();
		String subject = subjectEditText.getText().toString();
		String content = contentEditText.getText().toString();
		// final Timer timer = new Timer();
		// final String originalMessage = MessageNewActivity.this
		// .getString(R.string.sent_successfully);
		// final TimerTask task = new TimerTask() {
		// @Override
		// public void run() {
		//
		// runOnUiThread(new Runnable() { // UI thread
		// @Override
		// public void run() {
		// recLen--;
		// String message = originalMessage + "   " + recLen;
		// sentSusAD.setMessage(String.valueOf(message));
		// if (recLen == 0) {
		// timer.cancel();
		// setResult(RESULT_OK);
		// finish();
		//
		// }
		// }
		// });
		// }
		// };
		final HttpMultipartPost docConn = new HttpMultipartPost(
				NetConstantValues.MESSAGING_MESSAGE_NEW.PATH, this,
				needCompress) {

			@Override
			protected void onPostExecute(String result) {
				progress.dismiss();
				try {
					JSONObject jsonObj = new JSONObject(result);
					if (jsonObj.isNull("errno")) {
						JSONObject jData = jsonObj.getJSONObject("data");
						if (jData.has("valid")) {
							AlertDialog.Builder builder = new AlertDialog.Builder(
									MessageNewActivity.this);
							builder.setTitle(R.string.error);
							if (jData.has("message")) {
								builder.setMessage(jData.getString("message"));
							} else {
								builder.setMessage(R.string.message_send_warning);
							}
							builder.setPositiveButton(R.string.ok, null);
							builder.show();
						} else {
							// previous handle
							//2012.8.9 restore previous handle
							Toast.makeText(MessageNewActivity.this,
									R.string.sent_successfully,
									Toast.LENGTH_SHORT).show();
							setResult(RESULT_OK);
							finish();
							// Current handle
							// AlertDialog.Builder builder = new
							// AlertDialog.Builder(
							// MessageNewActivity.this);
							// String message = originalMessage + "   " +
							// recLen;
							// builder.setMessage(message);
							// builder.setPositiveButton(R.string.ok,
							// new DialogInterface.OnClickListener() {
							//
							// @Override
							// public void onClick(
							// DialogInterface dialog,
							// int which) {
							// setResult(RESULT_OK);
							// finish();
							//
							// }
							// });
							// builder.setOnCancelListener(new
							// OnCancelListener() {
							//
							// @Override
							// public void onCancel(DialogInterface arg0) {
							// Toast.makeText(MessageNewActivity.this,
							// R.string.sent_successfully,
							// Toast.LENGTH_SHORT).show();
							// setResult(RESULT_OK);
							// finish();
							//
							// }
							//
							// });
							// sentSusAD = builder.create();
							// sentSusAD.show();
							// timer.schedule(task, 1000, 1000);

						}
					} else {
						Toast.makeText(MessageNewActivity.this,
								jsonObj.getString("descr"), Toast.LENGTH_LONG)
								.show();
					}
				} catch (JSONException e) {
					DocLog.e(TAG, "JSONException", e);
					Toast.makeText(MessageNewActivity.this,
							R.string.error_occur, Toast.LENGTH_LONG).show();
				}

			}

		};
		Map<String, String> map = new HashMap<String, String>();
		map.put(NetConstantValues.MESSAGING_MESSAGE_NEW.PARAM_SUBJECT, subject);
		map.put(NetConstantValues.MESSAGING_MESSAGE_NEW.PARAM_BODY, content);
		map.put("DCOM_DEVICE_ID", appValues.getDcomDeviceId());
		if (type == REPLY_MESSAGE) {
			map.put(NetConstantValues.THREADING.PARAM_THREADING_UUID,
					getIntent().getStringExtra("threadingUUID"));
		}
		if (MessageDispatcherObject == DoctorDetailActivity.MESSAGE_DISPATCHER_PRACTICE) {
			map.put(NetConstantValues.MESSAGING_MESSAGE_NEW.PARAM_PRACTICE_RECIPIENTS,
					String.valueOf(practiceId));
		} else {
			StringBuffer toSB = new StringBuffer();
			for (int i = 0; i < toLen; i++) {
				int key = toIds.keyAt(i);
				if (i == toLen - 1) {
					toSB.append(key);
				} else {
					toSB.append(key + ",");
				}
			}
			map.put(NetConstantValues.MESSAGING_MESSAGE_NEW.PARAM_RECIPIENTS,
					toSB.toString());
		}

		if (ccLen != 0) {
			StringBuffer ccSB = new StringBuffer();
			for (int j = 0; j < ccLen; j++) {
				int key = ccIds.keyAt(j);
				if (j == ccLen - 1) {
					ccSB.append(key);
				} else {
					ccSB.append(key + ",");
				}
			}
			map.put(NetConstantValues.MESSAGING_MESSAGE_NEW.PARAM_CCS,
					ccSB.toString());
		}
		if (type == FORWARD_MESSAGE) {
			map.put(NetConstantValues.MESSAGING_MESSAGE_NEW.PARAM_SECRET,
					appValues.getSecret());
			map.put(NetConstantValues.MESSAGING_MESSAGE_NEW.PARAM_MESSAGE_ID,
					forwardMessageId);
			if (isRefer && hasReferId) {
				map.put(NetConstantValues.MESSAGING_MESSAGE_NEW.PARAM_REFER_ID,
						uuid);
			}
			int len = forwardAttachmentsList.size();
			if (len > 0) {
				StringBuffer sb = new StringBuffer();
				for (int i = 0; i < len; i++) {
					String strAttchmentId = forwardAttachmentsList.get(i).get(
							"id");
					if (i == len - 1) {
						sb.append(strAttchmentId);
					} else {
						sb.append(strAttchmentId + ",");
					}
				}
				map.put(NetConstantValues.MESSAGING_MESSAGE_NEW.PARAM_ATTACHMENT_IDS,
						sb.toString());

			}
		}
		int length = map.size();
		BasicNameValuePair[] pair = new BasicNameValuePair[length + nLen + iLen];

		Iterator<Entry<String, String>> iter = map.entrySet().iterator();
		int i = 0;
		while (iter.hasNext()) {
			Map.Entry<String, String> entry = iter.next();
			String key = entry.getKey();
			String val = entry.getValue();
			pair[i++] = new BasicNameValuePair(key, val);
		}
		for (int k = 0; k < nLen; k++) {
			pair[length + k] = new BasicNameValuePair(
					NetConstantValues.MESSAGING_MESSAGE_NEW.PARAM_ATTACHMENT,
					normalAttachmentsList.get(k));
		}
		for (int k = 0; k < iLen; k++) {
			pair[length + nLen + k] = new BasicNameValuePair(
					NetConstantValues.MESSAGING_MESSAGE_NEW.PARAM_ATTACHMENT,
					imageAttachmentList.get(k));
		}
		docConn.execute(pair);
		progress.show();
		progress.setCanceledOnTouchOutside(false);
		progress.setOnCancelListener(new DialogInterface.OnCancelListener() {

			@Override
			public void onCancel(DialogInterface dialog) {
				DocLog.d(TAG, "progress cancel");
				docConn.cancel(true);
				cancelProgressDialog = ProgressDialog.show(
						MessageNewActivity.this, "",
						getString(R.string.cancelling));
			}

		});
	}

	private OnClickListener btnTakePhotoClick = new OnClickListener() {

		@Override
		public void onClick(View v) {
			Intent intent = new Intent(MessageNewActivity.this,
					CameraActivity.class);
			startActivityForResult(intent, TAKE_PHOTO);
		}
	};

	class HttpMultipartPost extends
			AsyncTask<BasicNameValuePair, Integer, String> {
		long totalSize;
		private int READ_MAX_LENGTH = 512;
		private String postAddress;
		private Context context;
		private boolean needCompress;

		public HttpMultipartPost(String path, Context c, boolean needCompress) {
			postAddress = appValues.getServerURL() + NetConstantValues.APP_URL
					+ path;
			context = c;
			this.needCompress = needCompress;
		}

		@Override
		protected String doInBackground(BasicNameValuePair... params) {
			Utils utils = new Utils(MessageNewActivity.this);
			if (!utils.checkNetworkAvailable()) {
				return MessageNewActivity.this
						.getString(R.string.network_not_available);
			}
			String limited = checkSendLimited();
			try {
				JSONObject jsonObj = new JSONObject(limited);
				boolean isLimited = jsonObj.getJSONObject("data").getBoolean(
						"valid");
				if (!isLimited) {
					return limited;
				}
			} catch (JSONException e1) {
				DocLog.e(TAG, "JSONException", e1);
				return limited;
			}
			runOnUiThread(new Runnable() {

				@Override
				public void run() {
					progress.setMessage(getResources().getString(
							R.string.message_sending));
				}

			});
			int length = params.length;
			if (needCompress) {
				compressPicture();
				for (int k = 0, iLen = imageAttachmentList.size(); k < iLen; k++) {
					params[length - iLen + k] = new BasicNameValuePair(
							NetConstantValues.MESSAGING_MESSAGE_NEW.PARAM_ATTACHMENT,
							imageAttachmentList.get(k));
				}
				rate = 90;
				offset = 10;
			}
			// isRunning = true;
			String reslut = "";
			// basic http params
			HttpParams httpParams = new BasicHttpParams();
			HttpProtocolParams.setVersion(httpParams, HttpVersion.HTTP_1_1);
			HttpProtocolParams.setContentCharset(httpParams, HTTP.UTF_8);
			HttpProtocolParams.setUseExpectContinue(httpParams, true);
			HttpProtocolParams.setUserAgent(httpParams,
					"DoctorCom Android Application");

			// ConnManagerParams.setTimeout(httpParams, 2000);
			//
			// HttpConnectionParams.setConnectionTimeout(httpParams, 3000);
			// HttpConnectionParams.setSoTimeout(httpParams, 8000);

			HttpClient httpClient = new DefaultHttpClient(httpParams);
			if (appValues.getCurrent_version() == AppValues.ROLE_DEVELOP_VERSION) {
				HostnameVerifier hostnameVerifier = org.apache.http.conn.ssl.SSLSocketFactory.ALLOW_ALL_HOSTNAME_VERIFIER;
				SSLSocketFactory socketFactory = SSLSocketFactory
						.getSocketFactory();
				socketFactory
						.setHostnameVerifier((X509HostnameVerifier) hostnameVerifier);
				HttpsURLConnection.setDefaultHostnameVerifier(hostnameVerifier);
			}
			HttpContext httpContext = new BasicHttpContext();
			HttpPost httpPost = new HttpPost(postAddress);
			// post multipart data
			// set Header
			Header doctorHeader = getDoctorHeader(params);
			if (doctorHeader != null) {
				httpPost.setHeader(doctorHeader);
			}

			CustomMultiPartEntity multipartContent = new CustomMultiPartEntity(
					HttpMultipartMode.BROWSER_COMPATIBLE, null,
					Charset.forName("UTF-8"),
					new CustomMultiPartEntity.ProgressListener() {
						@Override
						public void transferred(long num) {
							publishProgress((int) ((num / (float) totalSize)
									* rate + offset));
						}
					}) {

				@Override
				public void writeTo(OutputStream outstream) throws IOException {
					super.writeTo(new CountingOutputStream(outstream,
							this.listener) {

						@Override
						public void write(byte[] b, int off, int len)
								throws IOException {
							if (isCancelled())
								return;
							super.write(b, off, len);
						}

						@Override
						public void write(int b) throws IOException {
							if (isCancelled())
								return;
							super.write(b);
						}

					});
				}
			};
			for (int i = 0; i < length; i++) {
				String name = params[i].getName();
				String value = params[i].getValue();
				File uploadFile = new File(value);
				if ("DCOM_DEVICE_ID".equals(name)) {
					continue;
				}
				if (uploadFile.isFile()) {
					FileBody fileBody = new FileBody(uploadFile,
							FileUtil.getMIMEType(uploadFile), "UTF-8");
					multipartContent.addPart(name, fileBody);
					DocLog.d(TAG, "Param > File " + name + " : " + value);
				} else {
					try {
						StringBody strBody = new StringBody(value,
								Charset.forName("UTF-8"));
						multipartContent.addPart(name, strBody);
						DocLog.d(TAG, "Param > String " + name + " : " + value);
					} catch (UnsupportedEncodingException ex) {
						DocLog.e(
								TAG,
								"getRequestEntityParams on POST_TYPE_MULTIPART error",
								ex);
					}
				}
			}

			totalSize = multipartContent.getContentLength();

			// Send it
			httpPost.setEntity(multipartContent);
			HttpResponse response = null;
			try {
				HttpParams postParams = httpPost.getParams();
				ConnManagerParams.setTimeout(postParams, 1000);
				HttpConnectionParams.setConnectionTimeout(postParams, 15000);
				HttpConnectionParams.setSoTimeout(postParams, 60000);
				response = httpClient.execute(httpPost, httpContext);
			} catch (ClientProtocolException e) {
				DocLog.d(TAG, "ClientProtocolException", e);
			} catch (IOException e) {
				DocLog.d(TAG, "IOException", e);
			}
			if (response != null) {
				int statusCode = response.getStatusLine().getStatusCode();
				DocLog.d(TAG, "StatusCode > " + statusCode);
				// set the status unexpected json string
				// if (statusCode != 200) {
				// if (statusCode == 404) {
				// return DoctorComConn.JSONERROR_404;
				// } else if (statusCode == 500) {
				// return DoctorComConn.JSONERROR_500;
				// }
				// }

				InputStream input = null;
				try {
					input = response.getEntity().getContent();

					// read as text
					ByteArrayOutputStream outputStream = new ByteArrayOutputStream();
					byte[] buffer = new byte[READ_MAX_LENGTH];
					int len = -1;
					while ((len = input.read(buffer)) != -1) {
						outputStream.write(buffer, 0, len);
					}
					byte[] data = outputStream.toByteArray();
					reslut = new String(data, HTTP.UTF_8);
					outputStream.close();
					input.close();
				} catch (IllegalStateException e) {
					DocLog.e(TAG, "IllegalStateException", e);
				} catch (IOException e) {
					DocLog.e(TAG, "IOException", e);
				}
			}
			try {
				if (httpClient != null)
					httpClient.getConnectionManager().shutdown();
			} catch (Exception ex) {
				DocLog.e(TAG, "ConnectionManager shutdown Exception", ex);
			}
			// if(reslut == null || reslut.length() <= 0){
			// reslut = DoctorComConn.JSONERROR_UNKOWN;
			// }
			DocLog.d(TAG, "Reslut > " + reslut);
			return reslut;
		}

		@Override
		protected void onProgressUpdate(Integer... values) {
			if (isCancelled())
				return;
			progress.setProgress((int) values[0]);
		}

		@Override
		protected void onCancelled() {
			if (cancelProgressDialog != null) {
				cancelProgressDialog.dismiss();
			}
			DocLog.d(TAG, "cancel message send!!!");
			Toast.makeText(context, R.string.cancel, Toast.LENGTH_SHORT).show();
			finish();
			super.onCancelled();
		}

		protected Header getDoctorHeader(BasicNameValuePair... params) {
			Header header = null;
			int length = params.length;
			for (int i = 0; i < length; i++) {
				String name = params[i].getName();
				String value = params[i].getValue();
				if ("DCOM_DEVICE_ID".equals(name)) {
					DocLog.d(TAG, "Head > String " + name + " : " + value);
					header = new BasicHeader(name, value);
					break;
				}
			}
			return header;
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

	@Override
	protected void onDestroy() {
		// clean
		int i = 0, len = 0;
		for (i = 0, len = normalAttachmentsList.size(); i < len; i++) {
			new File(normalAttachmentsList.get(i)).delete();
		}
		for (i = 0, len = imageAttachmentList.size(); i < len; i++) {
			new File(imageAttachmentList.get(i)).delete();
		}
		for (i = 0, len = deprecatedAttachmentList.size(); i < len; i++) {
			new File(deprecatedAttachmentList.get(i)).delete();
		}
		super.onDestroy();

	}

}
