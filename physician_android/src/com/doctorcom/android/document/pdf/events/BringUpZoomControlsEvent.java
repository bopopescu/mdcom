package com.doctorcom.android.document.pdf.events;

public class BringUpZoomControlsEvent extends SafeEvent<BringUpZoomControlsListener>
{
    @Override
    public void dispatchSafely(BringUpZoomControlsListener listener)
    {
        listener.toggleZoomControls();
    }
}
