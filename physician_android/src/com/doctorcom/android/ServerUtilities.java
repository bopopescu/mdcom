/*
 * Copyright 2012 Google Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.doctorcom.android;

import static com.doctorcom.android.CommonUtilities.SERVER_URL;
import static com.doctorcom.android.CommonUtilities.TAG;

import java.util.HashMap;
import java.util.Map;
import java.util.Random;

import org.json.JSONObject;

import android.content.Context;
import android.content.Intent;

import com.doctorcom.physician.AppValues;
import com.doctorcom.physician.net.NetConstantValues;
import com.doctorcom.physician.net.http.NetConncet;
import com.doctorcom.physician.utils.DocLog;
import com.google.android.gcm.GCMRegistrar;

/**
 * Helper class used to communicate with the demo server.
 */
public final class ServerUtilities {

    private static final int MAX_ATTEMPTS = 5;
    private static final int BACKOFF_MILLI_SECONDS = 2000;
    private static final Random random = new Random();

    /**
     * Register this account/device pair within the server.
     *
     * @return whether the registration succeeded or not.
     */
    public static boolean register(final Context context, final String regId) {
        DocLog.i(TAG, "registering device (regId = " + regId + ")");
        AppValues appValues = new AppValues(context);
        String serverUrl = SERVER_URL;
        Map<String, String> params = new HashMap<String, String>();
        params.put(NetConstantValues.NOTIFICATION.TOKEN, regId);
        long backoff = BACKOFF_MILLI_SECONDS + random.nextInt(1000);
        // Once GCM returns a registration id, we need to register it in the
        // demo server. As the server might be down, we will retry it a couple
        // times.
        for (int i = 1; i <= MAX_ATTEMPTS; i++) {
            DocLog.d(TAG, "Attempt #" + i + " to register");
            try {
                post(context, serverUrl, params, appValues.getDcomDeviceId());
                GCMRegistrar.setRegisteredOnServer(context, true);
				context.stopService(new Intent("com.doctorcom.physician.message"));
                return true;
            } catch (Exception e) {
                // Here we are simplifying and retrying on any error; in a real
                // application, it should retry only on unrecoverable errors
                // (like HTTP error code 503).
                DocLog.e(TAG, "Failed to register on attempt " + i, e);
                if (i == MAX_ATTEMPTS) {
                	context.startService(new Intent("com.doctorcom.physician.message"));
                    break;
                }
                try {
                    DocLog.d(TAG, "Sleeping for " + backoff + " ms before retry");
                    Thread.sleep(backoff);
                } catch (InterruptedException e1) {
                    // Activity finished before we complete - exit.
                    DocLog.d(TAG, "Thread interrupted: abort remaining retries!");
                    Thread.currentThread().interrupt();
                    return false;
                }
                // increase backoff exponentially
                backoff *= 2;
            }
        }
        return false;
    }

    /**
     * Unregister this account/device pair within the server.
     */
    static void unregister(final Context context, final String regId) {
        DocLog.i(TAG, "unregistering device (regId = " + regId + ")");
        GCMRegistrar.setRegisteredOnServer(context, false);

    }

    /**
     * Issue a POST request to the server.
     *
     * @param endpoint POST address.
     * @param params request parameters.
     *
     * @throws Exception.
     */
    private static void post(Context context, String endpoint, Map<String, String> params, String deviceId)
            throws Exception {
    	NetConncet netConncet = new NetConncet(context, endpoint, params);
    	String result = netConncet.connect(0);
    	JSONObject jsonObj = new JSONObject(result);
    	if (!jsonObj.isNull("errno")) {
    		 throw new Exception("Post failed with error " + result);
    	}

      }
}
