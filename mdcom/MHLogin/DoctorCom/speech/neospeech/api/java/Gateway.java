
import java.lang.String;
import java.io.IOException;
import java.io.BufferedReader;
import java.io.InputStreamReader;

import py4j.GatewayServer;
import voiceware.libttsapi;

class Gateway
{
    private libttsapi m_ttsapi;

    /* Default c'tor create libttsapi instance used by our gateway to 
     * communicate with our python app */
    public Gateway() 
    {
        m_ttsapi = new libttsapi();
    }
    
    /* python client will call this and get socket error if gateway not up */
    public boolean get_gw_status()
    {
        return true;
    }

    /* server status port is default to 7777 */
    public int ttsRequestStatus(String ipaddr, int status_port)
    {
        int rc;
        try 
        {
            rc = m_ttsapi.ttsRequestStatus(ipaddr, status_port);
        } 
        catch (IOException e)
        {
            rc = -9;
        }
        return rc;
    }

    /* function name misleading, tells server to generate a file on the server */
    public int ttsRequestFile(String ipaddr, int port, String text, String dir, 
            String filename, int speakerId, int voiceFormat)
    {
        int rc;
        try 
        {
            rc = m_ttsapi.ttsRequestFile(ipaddr, port, text, dir, 
                    filename, speakerId, voiceFormat);
        } 
        catch (IOException e) 
        {
            rc = -9;
        }
        return rc;
    }

    /* return buffer from tts server */
    public int ttsRequestBuffer(String ipaddr, int port, String text, int speakerId, 
            int bufformat, int reqfirst, int oneframe)
    {
        int rc;
        try 
        {
            rc = m_ttsapi.ttsRequestBuffer(ipaddr, port, text, speakerId, 
                    bufformat, reqfirst, oneframe);
        } 
        catch (IOException e) 
        {
            rc = -9;
        }
        return rc;
    }

    /* return buffer from tts server extended version */
    public int ttsRequestBufferEx(String ipaddr, int port, String text, int speakerId, 
            int bufformat, int textformat, int volume, int speed, int pitch,
            int dictnum, int reqfirst, int oneframe)
    {
        int rc;
        try 
        {
            rc = m_ttsapi.ttsRequestBufferEx(ipaddr, port, text, speakerId, 
                    bufformat, textformat, volume, speed, pitch, dictnum, 
                    reqfirst, oneframe);
        } 
        catch (IOException e) 
        {
            rc = -9;
        }
        return rc;
    }

    /* Typically after if ttsRequestBuffer() successfull to get buffer contents */ 
    public byte[] ttsGetBufferData()
    {
        return m_ttsapi.szVoiceData;
    }

    /* main entry point for Neospeech Gateway */
    public static void main(String[] args) 
    {
        int     port = GatewayServer.DEFAULT_PORT;
        boolean dieOnBrokenPipe = false;

        if (args.length > 0) 
        {   // java really needs a builtin option parser
            if (args[0].equals("--die-on-broken-pipe"))
                dieOnBrokenPipe = true;
            if (!dieOnBrokenPipe || (args.length - 1) > 0)
                port = Integer.parseInt(args[args.length - 1]);
        }

        GatewayServer gatewayServer = new GatewayServer(new Gateway(), port);
        gatewayServer.start();

        //System.out.println("" + port + " " + dieOnBrokenPipe);

        if (dieOnBrokenPipe == true)
        {   // Exit on EOF or broken pipe, ensures server dies if parent dies.
            BufferedReader stdin = new BufferedReader(new InputStreamReader(System.in));
            try 
            {
                stdin.readLine();
                System.exit(0);
            } 
            catch (java.io.IOException e) 
            {
                System.exit(1);
            }        
        }
    }
}

