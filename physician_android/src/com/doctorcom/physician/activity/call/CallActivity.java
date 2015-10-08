package com.doctorcom.physician.activity.call;

import android.media.AudioManager;
import android.media.ToneGenerator;
import android.os.Bundle;
import android.support.v4.app.Fragment;
import android.support.v4.app.FragmentActivity;
import android.support.v4.app.FragmentManager;
import android.text.InputType;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ImageView;
import android.widget.TextView;
import android.widget.Toast;

import com.doctorcom.android.R;
import com.doctorcom.physician.net.NetConstantValues;
import com.doctorcom.physician.utils.CallBack;
import com.doctorcom.physician.utils.PreferLogo;
import com.doctorcom.physician.utils.Utils;

public class CallActivity extends FragmentActivity {
	
	@Override
	protected void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
        FragmentManager fm = getSupportFragmentManager();

        // Create the list fragment and add it as our sole content.
        if (fm.findFragmentById(android.R.id.content) == null) {
        	CallFragment setting = new CallFragment();
        	Bundle args = new Bundle();
        	args.putString("number", getIntent().getStringExtra("number"));
        	args.putBoolean("isActivity", true);
        	setting.setArguments(args);
            fm.beginTransaction().add(android.R.id.content, setting).commit();
        }
	}


	public static class CallFragment extends Fragment {

		private String number = "";
		private EditText screenEditText;
		private boolean isActivity;
		private ImageView ivPreferLogoImageView;

		@Override
		public void onCreate(Bundle savedInstanceState) {
			super.onCreate(savedInstanceState);
			Bundle bundle = getArguments();
			number = bundle.getString("number");
			isActivity = bundle.getBoolean("isActivity");
		}

		@Override
		public View onCreateView(LayoutInflater inflater, ViewGroup container, Bundle savedInstanceState) {
			View view = inflater.inflate(R.layout.fragment_call, container, false);
			ivPreferLogoImageView = (ImageView) view.findViewById(R.id.ivPreferLogo);
			PreferLogo.showPreferLogo(getActivity(), ivPreferLogoImageView);
			screenEditText = (EditText) view.findViewById(R.id.tvScreen);
			screenEditText.setInputType(InputType.TYPE_NULL);
			if(number != null) {
				setScreen(number);
			}
			Button backButton = (Button)view.findViewById(R.id.btBack);
			if (isActivity) {
				backButton.setVisibility(View.VISIBLE);
				backButton.setOnClickListener(new View.OnClickListener() {
					
					@Override
					public void onClick(View v) {
						getActivity().finish();
						
					}
				});

				TextView titleTextView = (TextView) view.findViewById(R.id.tvDC);
				titleTextView.setText(R.string.call_from_doctorcom);

			} else {
				backButton.setVisibility(View.GONE);
			}
			final ToneGenerator tonePlayer = new ToneGenerator(AudioManager.STREAM_MUSIC, 70);
			Button m0Button = (Button) view.findViewById(R.id.button0);
			m0Button.setOnClickListener(new View.OnClickListener() {

				@Override
				public void onClick(View v) {
					tonePlayer.startTone(ToneGenerator.TONE_DTMF_0, 100);
					setScreen("0");

				}
			});
			m0Button.setOnLongClickListener(new View.OnLongClickListener() {

				@Override
				public boolean onLongClick(View v) {
					setScreen("+");
					return true;
				}
			});
			Button m1Button = (Button) view.findViewById(R.id.button1);
			m1Button.setOnClickListener(new View.OnClickListener() {

				@Override
				public void onClick(View v) {
					tonePlayer.startTone(ToneGenerator.TONE_DTMF_1, 100);
					setScreen("1");

				}
			});
			Button m2Button = (Button) view.findViewById(R.id.button2);
			m2Button.setOnClickListener(new View.OnClickListener() {

				@Override
				public void onClick(View v) {
					tonePlayer.startTone(ToneGenerator.TONE_DTMF_2, 100);
					setScreen("2");

				}
			});
			Button m3Button = (Button) view.findViewById(R.id.button3);
			m3Button.setOnClickListener(new View.OnClickListener() {

				@Override
				public void onClick(View v) {
					tonePlayer.startTone(ToneGenerator.TONE_DTMF_3, 100);
					setScreen("3");

				}
			});
			Button m4Button = (Button) view.findViewById(R.id.button4);
			m4Button.setOnClickListener(new View.OnClickListener() {

				@Override
				public void onClick(View v) {
					tonePlayer.startTone(ToneGenerator.TONE_DTMF_4, 100);
					setScreen("4");

				}
			});
			Button m5Button = (Button) view.findViewById(R.id.button5);
			m5Button.setOnClickListener(new View.OnClickListener() {

				@Override
				public void onClick(View v) {
					tonePlayer.startTone(ToneGenerator.TONE_DTMF_5, 100);
					setScreen("5");

				}
			});
			Button m6Button = (Button) view.findViewById(R.id.button6);
			m6Button.setOnClickListener(new View.OnClickListener() {

				@Override
				public void onClick(View v) {
					tonePlayer.startTone(ToneGenerator.TONE_DTMF_6, 100);
					setScreen("6");

				}
			});
			Button m7Button = (Button) view.findViewById(R.id.button7);
			m7Button.setOnClickListener(new View.OnClickListener() {

				@Override
				public void onClick(View v) {
					tonePlayer.startTone(ToneGenerator.TONE_DTMF_7, 100);
					setScreen("7");

				}
			});
			Button m8Button = (Button) view.findViewById(R.id.button8);
			m8Button.setOnClickListener(new View.OnClickListener() {

				@Override
				public void onClick(View v) {
					tonePlayer.startTone(ToneGenerator.TONE_DTMF_8, 100);
					setScreen("8");

				}
			});
			Button m9Button = (Button) view.findViewById(R.id.button9);
			m9Button.setOnClickListener(new View.OnClickListener() {

				@Override
				public void onClick(View v) {
					tonePlayer.startTone(ToneGenerator.TONE_DTMF_9, 100);
					setScreen("9");

				}
			});
			Button mxButton = (Button) view.findViewById(R.id.buttonx);
			mxButton.setOnClickListener(new View.OnClickListener() {

				@Override
				public void onClick(View v) {
					tonePlayer.startTone(ToneGenerator.TONE_DTMF_S, 100);
					setScreen("*");

				}
			});
			Button mnButton = (Button) view.findViewById(R.id.buttonn);
			mnButton.setOnClickListener(new View.OnClickListener() {

				@Override
				public void onClick(View v) {
					tonePlayer.startTone(ToneGenerator.TONE_DTMF_P, 100);
					setScreen("#");

				}
			});
			Button callButton = (Button) view.findViewById(R.id.btCall);
			callButton.setOnClickListener(new View.OnClickListener() {

				@Override
				public void onClick(View v) {
					number = screenEditText.getText().toString();
					if (number.startsWith("+1")) {
						number = number.substring(2);
					}
					if (Utils.validatePhone(number)) {
						CallBack callBack = new CallBack(getActivity());
						callBack.call(NetConstantValues.CALL_ARBITRARY.PATH, number);
					} else {
						Toast.makeText(getActivity(), R.string.phone_number_warning, Toast.LENGTH_SHORT).show();
					}

				}
			});
			Button backSpaceButton = (Button) view.findViewById(R.id.btBackspace);
			backSpaceButton.setOnClickListener(new View.OnClickListener() {

				@Override
				public void onClick(View v) {
					if (!screenEditText.getText().toString().equals("")) {
						int cur = screenEditText.getSelectionStart();
						if (cur > 0) {
							screenEditText.getText().delete(cur - 1, cur);
						}
					}

				}
			});
			backSpaceButton.setOnLongClickListener(new View.OnLongClickListener() {

						@Override
						public boolean onLongClick(View v) {
							screenEditText.setText("");
							return true;
						}
					});

			return view;
		}

		protected void setScreen(String num) {
			screenEditText.getText().insert(screenEditText.getSelectionStart(), num);
		}
		@Override
		public void onHiddenChanged(boolean hidden) {
			super.onHiddenChanged(hidden);
			if (!hidden) {
				PreferLogo.showPreferLogo(getActivity(), ivPreferLogoImageView);
			}
		}
		
		
	}
}
