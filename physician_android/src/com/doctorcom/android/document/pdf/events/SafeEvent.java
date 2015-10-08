package com.doctorcom.android.document.pdf.events;

import java.lang.reflect.Method;
import java.util.Locale;

public abstract class SafeEvent<T> implements Event<T>
{
    private final Class<?> listenerType;

    protected SafeEvent()
    {
        listenerType = getListenerType();
    }

    private Class<?> getListenerType()
    {		
    	String errorInfo;
		if (Locale.getDefault().getLanguage().contains("de")) {
			errorInfo = "dispatchSafely method nicht gefunden";
		} else {
			errorInfo = "Couldn't find dispatchSafely method";
		}

        for (Method method : getClass().getMethods())
        {
            if ("dispatchSafely".equals(method.getName()) && !method.isSynthetic())
            {
                return method.getParameterTypes()[0];
            }
        }
        throw new RuntimeException(errorInfo);
    }

    @SuppressWarnings({"unchecked"})
    public final void dispatchOn(Object listener)
    {
        if (listenerType.isAssignableFrom(listener.getClass()))
        {
            dispatchSafely((T) listener);
        }
    }

    public abstract void dispatchSafely(T listener);
}
