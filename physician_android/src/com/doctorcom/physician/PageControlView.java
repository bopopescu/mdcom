package com.doctorcom.physician;

import com.doctorcom.android.R;

import android.content.Context;
import android.util.AttributeSet;
import android.view.View;
import android.widget.ImageView;
import android.widget.LinearLayout;
 
public class PageControlView extends LinearLayout implements com.doctorcom.physician.ScrollView.OnScreenChangeListener{
    private Context context;
    private ScrollView mscrollView;
    
     
    public void setMscrollView(ScrollView mscrollView) {
		this.mscrollView = mscrollView;
	}

	public PageControlView(Context context) {
        super(context);
        this.context = context;
    }
 
    public PageControlView(Context context,AttributeSet attr){
        super(context,attr);
        this.context = context;
    }
    
    public interface OnPointedListener{
    	public void onFinishPointed(int position);
    }
     
    @Override
    public void screenChange(int currentTab, int totalTab) {
        this.removeAllViews();
        for(int i=0;i<totalTab;i++){
            ImageView iv = new ImageView(context);
            if(i==currentTab){
                iv.setImageResource(R.drawable.page_indicator_focused);
                iv.setScaleType(ImageView.ScaleType.CENTER_INSIDE);
            }else{
                iv.setImageResource(R.drawable.page_indicator);
                iv.setScaleType(ImageView.ScaleType.CENTER_INSIDE);
            }
            final int position = i;
            iv.setOnClickListener(new OnClickListener(){

				@Override
				public void onClick(View paramView) {
					mscrollView.onFinishPointed(position);
					
				}
            	
            });
            this.addView(iv);
        }
    }
}