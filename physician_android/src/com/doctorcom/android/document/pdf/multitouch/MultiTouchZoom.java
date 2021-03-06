package com.doctorcom.android.document.pdf.multitouch;

import android.view.MotionEvent;

public interface MultiTouchZoom {
    boolean onTouchEvent(MotionEvent ev);

    boolean isResetLastPointAfterZoom();

    void setResetLastPointAfterZoom(boolean resetLastPointAfterZoom);
}
