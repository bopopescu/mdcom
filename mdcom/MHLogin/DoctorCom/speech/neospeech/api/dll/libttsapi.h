/*
 * Copyright (c) 2000-2012 Voiceware Co., Ltd., All rights reserved.
 * 
 * VTAP API (VoiceText Access Protocol API)
*/


#define __VTAP_VER__	3.10.6.0


/* return code */
#define TTS_HOSTNAME_ERROR		-1
#define TTS_SOCKET_ERROR		-2
#define TTS_CONNECT_ERROR		-3
#define TTS_READWRITE_ERROR		-4
#define TTS_MEMORY_ERROR		-5
#define TTS_TEXT_ERROR			-6
#define TTS_VOICEFORMAT_ERROR	-7
#define TTS_PARAM_ERROR			-8
#define TTS_RESULT_ERROR		-9
#define TTS_SPEAKER_ERROR		-10
#define TTS_DISK_ERROR			-11
#define TTS_UNKNOWN_ERROR		-12
#define TTS_SSML_ERROR			-13
#define TTS_ENC_ERROR			-14
#define TTS_ABNORMAL_ERROR		-15
#define TTS_MAX_ERROR			-100
#define TTS_RESULT_CONTINUE		0
#define TTS_RESULT_SUCCESS		1

/* database name index */
#define TTS_JIHAE_DB						0
#define TTS_MINHO_DB						1
#define TTS_EUNJU_DB						2
#define TTS_JUNWOO_DB						3
#define TTS_NAYEON_DB						4
#define TTS_SUNYOUNG_DB						6
#define TTS_SUJIN_DB						8
#define TTS_YUMI_DB							10
#define TTS_GYURI_DB						11
#define TTS_DAYOUNG_DB						12
#define TTS_CHORONG_DB						13
#define TTS_HYERYUN_DB						14
#define TTS_HYUNA_DB						15
#define TTS_KATE_DB							100
#define TTS_PAUL_DB							101
#define TTS_JULIE_DB						103
#define TTS_LILY_DB							200
#define TTS_WANG_DB							201
#define TTS_HUI_DB							202
#define TTS_LIANG_DB						203
#define TTS_MIYU_DB							300
#define TTS_SHOW_DB							301
#define TTS_MISAKI_DB						302
#define TTS_HARUKA_DB						303
#define TTS_SAYAKA_DB						304
#define TTS_RYO_DB							305
#define TTS_VIOLETA_DB						400
#define TTS_BRIDGET_DB						500

// Voice Format Info
#define FORMAT_DEFAULT							0
#define FORMAT_WAV								1
#define FORMAT_PCM								2
#define FORMAT_MULAW							3
#define FORMAT_ALAW					 			4
#define FORMAT_ADPCM							5
#define FORMAT_ASF								6
#define FORMAT_WMA								7
#define FORMAT_32ADPCM							8
#define FORMAT_MP3								9
#define FORMAT_OGG								10
#define FORMAT_8BITWAV							11
#define FORMAT_AWAV								12
#define FORMAT_MUWAV							13
#define FORMAT_ADWAV							14
#define FORMAT_G726								15
#define FORMAT_8BITPCM							16
#define FORMAT_OUTPROC							17
#define FORMAT_OUTPROC_SYNC						18

/* text sorts */
#define TEXT_NORMAL		0
#define TEXT_SSML		1
#define TEXT_HTML		2
#define TEXT_EMAIL		3
#define TEXT_JEITA		4
#define TEXT_7BIT		5

/* server status */
#define TTS_SERVICE_ON		1
#define TTS_SERVICE_PAUSED	2
#define TTS_SERVICE_OFF		0

#define	MAX_MARK_NAME		512

typedef struct
{
	int nOffsetInStream;
	int nOffsetInBuffer;
	int nPosInText;
	char sMarkName[MAX_MARK_NAME];
} TTSMARK;

typedef char* TTSKEY;

#if defined(__cplusplus)
	extern "C" {
#endif

#if !defined(DllExport)
	#if defined(WIN32) || defined(WIN64)
		#define DllExport       __declspec( dllexport )		
	#else
		#define DllExport       extern
		
	#endif
#endif

#if defined(WIN32) || defined(WIN64)
	#include <Winsock2.h>		
	#include <windows.h>
#else
	#define SOCKET	int
	#define	INVALID_SOCKET	-1
#endif

/************************************************************/
/* TTS Plain text APIs					    */
/************************************************************/
DllExport int TTSRequestFile(char* szServer, int nPort, char* pText, int nTextLen, char* szSaveDir, char* szSaveFile, int nSpeakerID, int nVoiceFormat);
DllExport int TTSRequestFileSSML(char *szServer, int nPort, char *pText, int nTextLen, char *szSaveDir, char *szSaveFile, int nSpeakerID, int nVoiceFormat, int *pMarkSize, TTSMARK** ppTTSMark, int *pVoiceLen);

DllExport char* _TTSRequestBuffer(SOCKET* sockfd, char* szServer, int nPort, char* pText, int nTextLen, int* nVoiceLen, int nSpeakerID, int nVoiceFormat, int bFirst, int bAll, int* nReturn, TTSKEY* szkey);
//DllExport char* _TTSRequestBuffer_Sync(SOCKET* sockfd, char* szServer, int nPort, char* pText, int nTextLen, int* nVoiceLen, int nSpeakerID, int nVoiceFormat, int bFirst, int bAll, int* nReturn, TTSKEY* szkey);

// expanded format functions, for volume, speed, pitch, dictionary number
DllExport int TTSRequestFileEx(char* szServer, int nPort, char* pText, int nTextLen, char* szSaveDir, char* szSaveFile, int nSpeakerID, int nVoiceFormat, int nTextFormat, int nVolume, int nSpeed, int nPitch, int nDictNum);
//DllExport int TTSRequestFileEx_SSML(char *szServer, int nPort, char *pText, int nTextLen, char *szSaveDir, char *szSaveFile, int nSpeakerID, int nVoiceFormat, int nVolume, int nSpeed, int nPitch, int nDictNum, int *pMarkSize, TTSMARK** ppTTSMark, int *pVoiceLen);

DllExport char* _TTSRequestBufferEx(SOCKET* sockfd, char* szServer, int nPort, char* pText, int nTextLen, int* nVoiceLen, int nSpeakerID, int nVoiceFormat, int nTextFormat, int nVolume, int nSpeed, int nPitch, int nDictNum, int bFirst, int bAll, int* nReturn, TTSKEY* szkey);
//DllExport char* _TTSRequestBufferEx_Sync(SOCKET* sockfd, char* szServer, int nPort, char* pText, int nTextLen, int* nVoiceLen, int nSpeakerID, int nVoiceFormat, int c, int nVolume, int nSpeed, int nPitch, int nDictNum, int bFirst, int bAll, int* nReturn, TTSKEY* szkey);

/************************************************************/
/* TTS SSML text APIs					    */
/************************************************************/
DllExport char* _TTSRequestBufferSSMLEx(SOCKET* sockfd, char* szServer, int nPort, char* pText, int nTextLen, int* nVoiceLen, int nSpeakerID, int nVoiceFormat, int nVolume, int nSpeed, int nPitch, int nDictNum, int* pMarkSize, TTSMARK** ppTTSMark, int bFirst, int* nReturn, TTSKEY* szkey);
DllExport void TTSBufferFree(char* pBuffer);

/************************************************************/
/* Admin Status TTS APIs				    */
/************************************************************/
DllExport int TTSRequestStatus(char* szServer, int nPort);
DllExport void TTSSetTimeout(int nConnTime, int nReadWriteTime);

/************************************************************/
/* deprecated APIs					    */
/************************************************************/
DllExport char* TTSRequestBuffer(SOCKET* sockfd, char* szServer, int nPort, char* pText, int nTextLen, int* nVoiceLen, int nSpeakerID, int nVoiceFormat, int bFirst, int bAll, int* nReturn);
DllExport char* TTSRequestBufferEx(SOCKET* sockfd, char* szServer, int nPort, char* pText, int nTextLen, int* nVoiceLen, int nSpeakerID, int nVoiceFormat, int nTextFormat, int nVolume, int nSpeed, int nPitch, int nDictIndex, int bFirst, int bAll, int* nReturn);
DllExport char* TTSRequestBufferSSMLEx(SOCKET* sockfd, char* szServer, int nPort, char* pText, int nTextLen, int* nVoiceLen, int nSpeakerID, int nVoiceFormat, int nVolume, int nSpeed, int nPitch, int nDictNum, int* pMarkSize, TTSMARK** ppTTSMark, int bFirst, int* nReturn);

DllExport int InitSocket();
DllExport int RemoveSocket();

#if defined(__cplusplus)
    }
#endif /*_LIBTTSAPI_H_*/
