
from ctypes import c_int, c_char, c_char_p, Structure
from utils import StatusDict

""" default ports """
TTS_DATA_PORT = 7000
TTS_STATUS_PORT = 7777
TTS_ADMIN_PORT = 7100

"""" return codes """
TTS_SOCKET_ERROR, TTS_CONNECT_ERROR = -2, -3
TTS_READWRITE_ERROR, TTS_MEMORY_ERROR = -4, -5
TTS_TEXT_ERROR, TTS_VOICEFORMAT_ERROR = -6, -7
TTS_PARAM_ERROR, TTS_RESULT_ERROR = -8, -9
TTS_SPEAKER_ERROR, TTS_DISK_ERROR = -10, -11
TTS_UNKNOWN_ERROR, TTS_SSML_ERROR = -12, -13
TTS_ENC_ERROR, TTS_ABNORMAL_ERROR = -14, -15
TTS_MAX_ERROR, TTS_RESULT_CONTINUE = -100, 0
TTS_RESULT_SUCCESS, TTS_DUMMY_DRIVER = 1, 5555
TTS_NO_RESPONSE = -1
RESULT_CODES = StatusDict({
	TTS_SOCKET_ERROR: 'Socket Error', TTS_CONNECT_ERROR: 'Connect Error',
	TTS_READWRITE_ERROR: 'Readwrite Error', TTS_MEMORY_ERROR: 'Memory Error',
	TTS_TEXT_ERROR: 'Text Error', TTS_VOICEFORMAT_ERROR: 'Voice format Error',
	TTS_PARAM_ERROR: 'Param Error', TTS_RESULT_ERROR: 'Result Error',
	TTS_SPEAKER_ERROR: 'Speaker Error', TTS_DISK_ERROR: 'Disk Error',
	TTS_UNKNOWN_ERROR: 'Unknown Error', TTS_SSML_ERROR: 'SSML Error',
	TTS_ENC_ERROR: 'ENC Error', TTS_ABNORMAL_ERROR: 'Abnormal Error',
	TTS_MAX_ERROR: 'Max Error', TTS_RESULT_CONTINUE: 'Result continues',
	TTS_RESULT_SUCCESS: 'Result success', TTS_NO_RESPONSE: 'No response',
	TTS_DUMMY_DRIVER: 'Proper neospeech driver not configured, if using '
		'java make sure dependent py4j package is installed.',
	None: "Invalid - Server not responding."})
# create the inverse of above (note assumes no dupes)
RESULT_STRINGS = dict((v, k) for k, v in RESULT_CODES.items())

""" Available Voices - availability depends on license """
TTS_JIHAE_DB, TTS_MINHO_DB = 0, 1
TTS_EUNJU_DB, TTS_JUNWOO_DB = 2, 3
TTS_NAYEON_DB, TTS_SUNYOUNG_DB = 4, 6
TTS_SUJIN_DB, TTS_YUMI_DB = 8, 10
TTS_GYURI_DB, TTS_DAYOUNG_DB = 11, 12
TTS_CHORONG_DB, TTS_HYERYUN_DB = 13, 14
TTS_HYUNA_DB, TTS_KATE_DB = 15, 100   # Currently our license uses kate or julie
TTS_PAUL_DB, TTS_JULIE_DB = 101, 103  # but best to check configuration on server.
TTS_LILY_DB, TTS_WANG_DB = 200, 201   # I've asked neospeech to provide api to ask
TTS_HUI_DB, TTS_LIANG_DB = 202, 203   # for license details as part of their message
TTS_MIYU_DB, TTS_SHOW_DB = 300, 301   # api.  We have 1 year upgrade with them.
TTS_MISAKI_DB, TTS_HARUKA_DB = 302, 303
TTS_SAYAKA_DB, TTS_RYO_DB = 304, 305
TTS_VIOLETA_DB, TTS_BRIDGET_DB = 400, 500
VOICES = StatusDict({
	TTS_JIHAE_DB: 'Jihae', TTS_MINHO_DB: 'Mniho',
	TTS_EUNJU_DB: 'Eunu', TTS_JUNWOO_DB: 'Junwoo',
	TTS_NAYEON_DB: 'Nayeon', TTS_SUNYOUNG_DB: 'Sunyoung',
	TTS_SUJIN_DB: 'Sujin', TTS_YUMI_DB: 'Yumi',
	TTS_GYURI_DB: 'Gyuri', TTS_DAYOUNG_DB: 'Dayoung',
	TTS_CHORONG_DB: 'Chorong', TTS_HYERYUN_DB: 'Hyeryun',
	TTS_HYUNA_DB: 'Hyuna', TTS_KATE_DB: 'Kate',
	TTS_PAUL_DB: 'Paul', TTS_JULIE_DB: 'Julie',
	TTS_LILY_DB: 'Lily', TTS_WANG_DB: 'Wang',
	TTS_HUI_DB: 'Hui', TTS_LIANG_DB: 'Liang',
	TTS_MIYU_DB: 'Miyu', TTS_SHOW_DB: 'Show',
	TTS_MISAKI_DB: 'Misaki', TTS_HARUKA_DB: 'Haruka',
	TTS_SAYAKA_DB: 'Sayaka', TTS_RYO_DB: 'Ryo',
	TTS_VIOLETA_DB: 'Violetta', TTS_BRIDGET_DB: 'Bridget',
	None: "Invalid", })
VOICE_STRINGS = dict((v, k) for k, v in VOICES.items() if k is not None)

""" Voice Format Info """
FORMAT_DEFAULT, FORMAT_WAV = 0, 1
FORMAT_PCM, FORMAT_MULAW = 2, 3
FORMAT_ALAW, FORMAT_ADPCM = 4, 5
FORMAT_ASF, FORMAT_WMA = 6, 7
FORMAT_32ADPCM, FORMAT_MP3 = 8, 9
FORMAT_OGG, FORMAT_8BITWAV = 10, 11
FORMAT_AWAV, FORMAT_MUWAV = 12, 13
FORMAT_ADWAV, FORMAT_G726 = 14, 15
FORMAT_8BITPCM, FORMAT_OUTPROC = 16, 17
FORMAT_OUTPROC_SYNC = 18
FORMAT = StatusDict({
	FORMAT_DEFAULT: 'default', FORMAT_WAV: 'wav',
	FORMAT_PCM: 'pcm', FORMAT_MULAW: 'mulaw', 
	FORMAT_ALAW: 'alaw', FORMAT_ADPCM: 'adpcm',
	FORMAT_ASF: 'asf', FORMAT_WMA: 'wma',
	FORMAT_32ADPCM: '32adpcm', FORMAT_MP3: 'mp3',
	FORMAT_OGG: 'ogg', FORMAT_8BITWAV: '8bitwav',
	FORMAT_AWAV: 'awav', FORMAT_MUWAV: 'muwav',
	FORMAT_ADWAV: 'adwav', FORMAT_G726: 'g726',
	FORMAT_8BITPCM: '8bitpcm', FORMAT_OUTPROC: 'outprc',
	None: 'Invalid', })
FORMAT_STRINGS = dict((v, k) for k, v in FORMAT.items() if k is not None)
FORMAT_KEYS = [k for k in FORMAT.keys() if k is not None]

""" text format/sorts """
TEXT_NORMAL = 0
TEXT_SSML = 1
TEXT_HTML = 2
TEXT_EMAIL = 3
TEXT_JEITA = 4
TEXT_7BIT = 5

""" Server Status, listens to status messages on port 7777 default """
TTS_STATUS_SERVICE_ON = 1
TTS_STATUS_SERVICE_PAUSED = 2
TTS_STATUS_SERVICE_OFF = 0
TTS_STATUS_NO_RESPONSE = -1
TTS_STATUS_CONNECT_ERROR = -3
TTS_STATUS_DUMMY_DRIVER = 5555
SERVER_STATUS = StatusDict({
		TTS_STATUS_SERVICE_ON: "Service On",
		TTS_STATUS_SERVICE_PAUSED: "Service Paused",
		TTS_STATUS_SERVICE_OFF: "Service Off",
		TTS_STATUS_NO_RESPONSE: "No response",
		TTS_STATUS_CONNECT_ERROR: "Connect error",
		TTS_STATUS_DUMMY_DRIVER: 'Proper neospeech driver not configured, if using '
		'java make sure dependent py4j package is installed.',
		None: "Invalid"})

""" Mark maximum length """
MAX_MARK_NAME = 512

""" Types and structures """
TTSKEY = c_char_p


class TTSMARK(Structure):
	""" Python equivalent of TTSMARK structure """
	_fields_ = [
			('nOffsetInStream', c_int),
			('nOffsetInBuffer', c_int),
			('nPosInText', c_int),
			('sMarkName', c_char * MAX_MARK_NAME),
		]

"""

# Maps to c header file:
typedef struct
{
	int nOffsetInStream;
	int nOffsetInBuffer;
	int nPosInText;
	char sMarkName[MAX_MARK_NAME];
} TTSMARK;

"""


""" Function prototypes maps to c header file, python prototypes defined in UnixDriver:

 /* Admin Status TTS APIs */
DllExport int TTSRequestStatus(char *szServer, int nPort);

 /* TTS Plain text APIs					    */
DllExport int TTSRequestFile(char *szServer, int nPort, char *pText, int nTextLen,
		char *szSaveDir, char *szSaveFile, int nSpeakerID, int nVoiceFormat);

DllExport int TTSRequestFileSSML(char *szServer, int nPort, char *pText, int nTextLen,
		char *szSaveDir, char *szSaveFile, int nSpeakerID, int nVoiceFormat,
		int *pMarkSize, TTSMARK **ppTTSMark, int *pVoiceLen);

DllExport int TTSRequestFileEx(char *szServer, int nPort, char *pText, int nTextLen,
		char *szSaveDir, char *szSaveFile, int nSpeakerID, int nVoiceFormat,
		int nTextFormat, int nVolume, int nSpeed, int nPitch, int nDictIndex);

DllExport char *_TTSRequestBuffer(int *sockfd, char *szServer, int nPort, char *pText,
		int nTextLen, int *nVoiceLen, int nSpeakerID, int nVoiceFormat, int bFirst,
		int bAll, int *nReturn, TTSKEY *szkey);

DllExport char *_TTSRequestBufferEx(int *sockfd, char *szServer, int nPort, char *pText,
		int nTextLen, int *nVoiceLen, int nSpeakerID, int nVoiceFormat, int nTextFormat,
		int nVolume, int nSpeed, int nPitch, int nDictIndex, int bFirst, int bAll,
		int *nReturn, TTSKEY *szkey);

/* TTS SSML text APIs */
DllExport char *_TTSRequestBufferSSMLEx(int *sockfd, char *szServer, int nPort,
		char *pText, int nTextLen, int *nVoiceLen, int nSpeakerID, int nVoiceFormat,
		int nVolume, int nSpeed, int nPitch, int nDictIndex, int* pMarkSize,
		TTSMARK **ppTTSMark, int bFirst, int *nReturn, TTSKEY *szkey);
"""

