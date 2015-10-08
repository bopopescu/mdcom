package com.doctorcom.android.document.pdf.events;

public interface ZoomListener
{
    void zoomChanged(float newZoom, float oldZoom);

    void commitZoom();

    public class CommitZoomEvent extends SafeEvent<ZoomListener>
    {
        @Override
        public void dispatchSafely(ZoomListener listener)
        {
            listener.commitZoom();
        }
    }
}
