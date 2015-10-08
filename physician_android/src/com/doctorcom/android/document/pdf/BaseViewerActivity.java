package com.doctorcom.android.document.pdf;

import java.io.File;

import android.app.Activity;
import android.app.Dialog;
import android.content.SharedPreferences;
import android.net.Uri;
import android.os.Bundle;
import android.view.Gravity;
import android.view.Menu;
import android.view.MenuItem;
import android.view.ViewGroup;
import android.view.Window;
import android.view.WindowManager;
import android.widget.FrameLayout;
import android.widget.Toast;

import com.doctorcom.android.document.pdf.events.CurrentPageListener;
import com.doctorcom.android.document.pdf.events.DecodingProgressListener;
import com.doctorcom.android.document.pdf.models.CurrentPageModel;
import com.doctorcom.android.document.pdf.models.DecodingProgressModel;
import com.doctorcom.android.document.pdf.models.ZoomModel;
import com.doctorcom.android.document.pdf.views.PageViewZoomControls;
import com.doctorcom.physician.utils.DocLog;

public abstract class BaseViewerActivity extends Activity implements DecodingProgressListener, CurrentPageListener
{
    private static final int MENU_EXIT = 0;
    private static final int MENU_GOTO = 1;
    private static final int MENU_FULL_SCREEN = 2;
    private static final int DIALOG_GOTO = 0;
    private static final String DOCUMENT_VIEW_STATE_PREFERENCES = "DjvuDocumentViewState";
    private DecodeService decodeService;
    private DocumentView documentView;
    private ViewerPreferences viewerPreferences;
    private Toast pageNumberToast;
    private CurrentPageModel currentPageModel;
    private String mFilePath = "";

    private static final String TAG = "BaseViewerActivity";
    /**
     * Called when the activity is first created.
     */
    @Override
    public void onCreate(Bundle savedInstanceState)
    { 
    	super.onCreate(savedInstanceState);
    	try{
    		 	initDecodeService();
    	        final ZoomModel zoomModel = new ZoomModel();
    	        final DecodingProgressModel progressModel = new DecodingProgressModel();
    	        progressModel.addEventListener(this);
    	        currentPageModel = new CurrentPageModel();
    	        currentPageModel.addEventListener(this);
    	        documentView = new DocumentView(this, zoomModel, progressModel, currentPageModel);
    	        zoomModel.addEventListener(documentView);
    	        documentView.setLayoutParams(new ViewGroup.LayoutParams(ViewGroup.LayoutParams.FILL_PARENT, ViewGroup.LayoutParams.FILL_PARENT));
    	        decodeService.setContentResolver(getContentResolver());
    	        decodeService.setContainerView(documentView);
    	        documentView.setDecodeService(decodeService);
    	        String filePath = getIntent().getStringExtra("pdf_document");
    	        Uri uriFilePath = Uri.fromFile(new File((filePath)));
    	        decodeService.open(uriFilePath);
    	        mFilePath  = filePath;
    	        viewerPreferences = new ViewerPreferences(this);

    	        final FrameLayout frameLayout = createMainContainer();
    	        frameLayout.addView(documentView);
    	        frameLayout.addView(createZoomControls(zoomModel));
    	        setFullScreen();
    	        setContentView(frameLayout);

    	        final SharedPreferences sharedPreferences = getSharedPreferences(DOCUMENT_VIEW_STATE_PREFERENCES, 0);
    	        int currentPage = 0;
    	        if(sharedPreferences != null){
    	        	currentPage = sharedPreferences.getInt(filePath, 0);
    	        }
    	        documentView.goToPage(currentPage);
    	        documentView.showDocument();

    	        viewerPreferences.addRecent(uriFilePath);
    	}catch(Exception ex){
    		DocLog.e(TAG, "load pdf document exception",ex);
    		Toast.makeText(getApplicationContext(), "Load file error", Toast.LENGTH_LONG).show();
    		finish();
    	}
    }

    public void decodingProgressChanged(final int currentlyDecoding)
    {
        runOnUiThread(new Runnable()
        {
            public void run()
            {
                getWindow().setFeatureInt(Window.FEATURE_INDETERMINATE_PROGRESS, currentlyDecoding == 0 ? 10000 : currentlyDecoding);
            }
        });
    }

    public void currentPageChanged(int pageIndex)
    {
        final String pageText = (pageIndex + 1) + "/" + decodeService.getPageCount();
        if (pageNumberToast != null)
        {
            pageNumberToast.setText(pageText);
        }
        else
        {
            pageNumberToast = Toast.makeText(this, pageText, Toast.LENGTH_SHORT);
        }
        pageNumberToast.setGravity(Gravity.TOP | Gravity.LEFT,0,0);
        pageNumberToast.show();
        saveCurrentPage();
    }

    private void setWindowTitle()
    {
        final String name = new File(mFilePath).getName() ;
        getWindow().setTitle(name);
    }

    @Override
    protected void onPostCreate(Bundle savedInstanceState)
    {
        super.onPostCreate(savedInstanceState);
        setWindowTitle();
    }

    private void setFullScreen()
    {
        if (viewerPreferences.isFullScreen())
        {
            getWindow().requestFeature(Window.FEATURE_NO_TITLE);
            getWindow().setFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN, WindowManager.LayoutParams.FLAG_FULLSCREEN);
        }
        else
        {
            getWindow().requestFeature(Window.FEATURE_INDETERMINATE_PROGRESS);
        }
    }

    private PageViewZoomControls createZoomControls(ZoomModel zoomModel)
    {
        final PageViewZoomControls controls = new PageViewZoomControls(this, zoomModel);
        controls.setGravity(Gravity.RIGHT | Gravity.BOTTOM);
        zoomModel.addEventListener(controls);
        return controls;
    }

    private FrameLayout createMainContainer()
    {
        return new FrameLayout(this);
    }

    private void initDecodeService()
    {
        if (decodeService == null)
        {
            decodeService = createDecodeService();
        }
    }

    protected abstract DecodeService createDecodeService();

    @Override
    protected void onStop()
    {
        super.onStop();
    }

    @Override
    protected void onDestroy() {
        decodeService.recycle();
        decodeService = null;
        super.onDestroy();
    }

    private void saveCurrentPage()
    {
        final SharedPreferences sharedPreferences = getSharedPreferences(DOCUMENT_VIEW_STATE_PREFERENCES, 0);
        final SharedPreferences.Editor editor = sharedPreferences.edit();
        editor.putInt(mFilePath, documentView.getCurrentPage());
        editor.commit();
    }

    @Override
    public boolean onCreateOptionsMenu(Menu menu)
    {
        menu.add(0, MENU_EXIT, 0, "Exit");
        menu.add(0, MENU_GOTO, 0, "Go to page");
        final MenuItem menuItem = menu.add(0, MENU_FULL_SCREEN, 0, "Full screen").setCheckable(true).setChecked(viewerPreferences.isFullScreen());
        setFullScreenMenuItemText(menuItem);
        return true;
    }

    private void setFullScreenMenuItemText(MenuItem menuItem)
    {
        menuItem.setTitle("Full screen " + (menuItem.isChecked() ? "on" : "off"));
    }

    @Override
    public boolean onOptionsItemSelected(MenuItem item)
    {
        switch (item.getItemId())
        {
            case MENU_EXIT:
                System.exit(0);
                return true;
            case MENU_GOTO:
                showDialog(DIALOG_GOTO);
                return true;
            case MENU_FULL_SCREEN:
                item.setChecked(!item.isChecked());
                setFullScreenMenuItemText(item);
                viewerPreferences.setFullScreen(item.isChecked());

                finish();
                startActivity(getIntent());
                return true;
        }
        return false;
    }

    @Override
    protected Dialog onCreateDialog(int id)
    {
        switch (id)
        {
            case DIALOG_GOTO:
                return new GoToPageDialog(this, documentView, decodeService);
        }
        return null;
    }
}
