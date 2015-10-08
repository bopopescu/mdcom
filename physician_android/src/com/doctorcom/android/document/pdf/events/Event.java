package com.doctorcom.android.document.pdf.events;

public interface Event<T>
{
    void dispatchOn(Object listener);
}
