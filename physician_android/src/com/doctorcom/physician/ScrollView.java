package com.doctorcom.physician;

import com.doctorcom.physician.PageControlView.OnPointedListener;

import android.content.Context;
import android.util.AttributeSet;
import android.view.GestureDetector;
import android.view.GestureDetector.SimpleOnGestureListener;
import android.view.MotionEvent;
import android.view.View;
import android.view.ViewConfiguration;
import android.view.ViewGroup;
import android.widget.Scroller;

public class ScrollView extends ViewGroup implements OnPointedListener{

	private GestureDetector gesture;
	private Context context;
	private boolean fling;
	private Scroller scroller;
	private OnScreenChangeListener onScreenChangeListener;

	public ScrollView(Context context) {
		super(context);
		this.context = context;
		gesture = new GestureDetector(context, new GestureListener());
		scroller = new Scroller(context);
	}

	public ScrollView(Context context, AttributeSet att) {
		super(context, att);
		this.context = context;
		gesture = new GestureDetector(context, new GestureListener());
		scroller = new Scroller(context);
	}

	@Override
	protected void onLayout(boolean changed, int l, int t, int r, int b) {
		for (int i = 0; i < getChildCount(); i++) {
			View child = (View) getChildAt(i);
			child.layout(getWidth() * i, 0, getWidth() * (i + 1), getHeight());
		}
	}

	@Override
	protected void onMeasure(int widthMeasureSpec, int heightMeasureSpec) {
		// TODO Auto-generated method stub
		super.onMeasure(widthMeasureSpec, heightMeasureSpec);
		final int count = getChildCount();
		for (int i = 0; i < count; i++) {
			getChildAt(i).measure(widthMeasureSpec, heightMeasureSpec);
		}
	}

	@Override
	public boolean onTouchEvent(MotionEvent ev) {
		gesture.onTouchEvent(ev);
		switch (ev.getAction()) {
		case MotionEvent.ACTION_MOVE:
			break;
		case MotionEvent.ACTION_UP:
			System.out.println("action_up...");
			if (!fling) {
				scrollToScreen();
			}
			fling = false;
			break;
		}
		return true;
	}

	/**
	 * 用来计算拖动一段距离后，要显示哪个界面
	 */
	private void scrollToScreen() {
		int leftWidth = getScrollX();
		int tabs = leftWidth / getWidth();
		int len = leftWidth - tabs * getWidth();
		if (len < getWidth() / 2) {
			// scrollTo(tabs*getWidth(),0);
			scroller.startScroll(leftWidth, 0, -len, 0, len * 2);
		} else {
			// scrollTo((tabs+1)*getWidth(),0);
			scroller.startScroll(leftWidth, 0, getWidth() - len, 0, len * 2);
			tabs = tabs + 1;
		}
		if (onScreenChangeListener != null) {
			onScreenChangeListener.screenChange(tabs, getChildCount());
		}
		invalidate();
	}

	@Override
	public void computeScroll() {
		if (scroller.computeScrollOffset()) {
			scrollTo(scroller.getCurrX(), 0);
			postInvalidate();
		}
	}

	class GestureListener extends SimpleOnGestureListener {

		@Override
		public boolean onDoubleTap(MotionEvent e) {
			return super.onDoubleTap(e);
		}

		@Override
		public boolean onDown(MotionEvent e) {
			return super.onDown(e);
		}

		@Override
		public boolean onFling(MotionEvent e1, MotionEvent e2, float velocityX,
				float velocityY) {
			if (Math.abs(velocityX) > ViewConfiguration.get(context)
					.getScaledMinimumFlingVelocity()) {
				scrollToScreen();
				fling = true;
			}
			return true;
		}

		@Override
		public void onShowPress(MotionEvent e) {
			super.onShowPress(e);
		}

		@Override
		public void onLongPress(MotionEvent e) {
			super.onLongPress(e);
		}

		@Override
		public boolean onScroll(MotionEvent e1, MotionEvent e2,
				float distanceX, float distanceY) {
			if (distanceX > 0
					&& getScrollX() < (getChildCount() - 1) * getWidth()
					|| distanceX < 0 && getScrollX() > 0) {
				scrollBy((int) distanceX, 0);
			}
			return true;
		}

		@Override
		public boolean onSingleTapUp(MotionEvent e) {
			return super.onSingleTapUp(e);
		}
	}

	public interface OnScreenChangeListener {
		void screenChange(int currentTab, int totalTab);
	}

	public void setOnScreenChangeListener(
			OnScreenChangeListener onScreenChangeListener) {
		this.onScreenChangeListener = onScreenChangeListener;
	}

	public void initPageControlView() {
		if (onScreenChangeListener != null) {
			onScreenChangeListener.screenChange(0, getChildCount());
		}
	}

	@Override
	public void onFinishPointed(int position) {
		scrollTo(position*getWidth(),0);
		invalidate();
		if (onScreenChangeListener != null) {
			onScreenChangeListener.screenChange(position, getChildCount());
		}
		
	}
}