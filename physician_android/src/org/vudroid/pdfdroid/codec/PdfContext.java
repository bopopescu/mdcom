package org.vudroid.pdfdroid.codec;

import android.content.ContentResolver;

import com.doctorcom.android.document.pdf.VuDroidLibraryLoader;
import com.doctorcom.android.document.pdf.codec.CodecContext;
import com.doctorcom.android.document.pdf.codec.CodecDocument;

public class PdfContext implements CodecContext
{
    static
    {
        VuDroidLibraryLoader.load();
    }

    public CodecDocument openDocument(String fileName)
    {
        return PdfDocument.openDocument(fileName, "");
    }

    public void setContentResolver(ContentResolver contentResolver)
    {
        //TODO
    }

    public void recycle() {
    }
}
