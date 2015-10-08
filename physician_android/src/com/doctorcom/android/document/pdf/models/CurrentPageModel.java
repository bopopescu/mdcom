package com.doctorcom.android.document.pdf.models;

import com.doctorcom.android.document.pdf.events.CurrentPageListener;
import com.doctorcom.android.document.pdf.events.EventDispatcher;

public class CurrentPageModel extends EventDispatcher
{
    private int currentPageIndex;

    public void setCurrentPageIndex(int currentPageIndex)
    {
        if (this.currentPageIndex != currentPageIndex)
        {
            this.currentPageIndex = currentPageIndex;
            dispatch(new CurrentPageListener.CurrentPageChangedEvent(currentPageIndex));
        }
    }
}
