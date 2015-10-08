'''
Created on Oct 5, 2012

@author: kurtv
'''
import atexit
import os
import platform
import socket
import subprocess
import sys

from ctypes import cdll, c_int, c_char_p, c_void_p, string_at

from utils import cfunc, c_int_p
import driver_h	 # constants


class Driver(object):
	""" Base class neospeech driver """
	def __init__(self, server_ip="127.0.0.1", voice=driver_h.TTS_KATE_DB):
		# set default values, these can be modified later
		self.server_ip = server_ip
		self.server_port = driver_h.TTS_DATA_PORT  # default
		self.server_status_port = driver_h.TTS_STATUS_PORT  # default status port
		self.voice = voice  # can be changed but depends on license
		# detect os type and set dll either cdll or windll
		if sys.platform.lower() in ("win32", "win64"):
			from ctypes import windll
			self.dll = windll
		else:
			self.dll = cdll

	def request_status(self, ip, status_port):
		""" Abstract base class method, inheriting driver must implement this """
		raise NotImplementedError("Appropriate Neospeech driver must override"
				"this base class method.")

	def validate_config(self, ip, port, text, voice, fmt):
		""" Abstract base class method, inheriting driver must implement this """
		raise NotImplementedError("Appropriate Neospeech driver must override"
				"this base class method.")

	def generate_file_on_server(self, text, dirname, filename, fmt=driver_h.FORMAT_WAV):
		""" Abstract base class method, inheriting driver must implement this """
		raise NotImplementedError("Appropriate Neospeech driver must override"
				"this base class method.")

	def request_buffer(self, text, fmt=driver_h.FORMAT_WAV, reqfirst=True, oneframe=True):
		""" Abstract base class method, inheriting driver must implement this """
		raise NotImplementedError("Appropriate Neospeech driver must override"
				"this base class method.")

	def request_buffer_ex(self, text, fmt=driver_h.FORMAT_WAV, txt_fmt=driver_h.TEXT_NORMAL,
				volume=100, speed=100, pitch=100, dictnum=0, reqfirst=True, oneframe=True):
		""" Abstract base class method, inheriting driver must implement this """
		raise NotImplementedError("Appropriate Neospeech driver must override"
				"this base class method.")

	def shutdown(self):
		""" Shutdown the driver doing whatever cleanup appropriate """


LIB_DIR = os.path.dirname(os.path.abspath(__file__))
SO_FILE = "libttsapi_32.so" if platform.architecture()[0] == '32bit' else "libttsapi_64.so"
DEF_LIB_FILE = os.path.join(LIB_DIR, 'api', 'unix', SO_FILE)


class UnixDriver(Driver):
	def __init__(self, libfile=DEF_LIB_FILE, server_ip="127.0.0.1", voice=driver_h.TTS_KATE_DB):
		super(UnixDriver, self).__init__(server_ip, int(voice))

		# this is important to set before creating cfuncs
		self.lib = self.dll.LoadLibrary(libfile)  # will raise OSError if fails

		# define function prototypes
		self.TTSRequestStatus = cfunc('TTSRequestStatus', self.lib, c_int,
									(c_char_p, 'szServer'),
									(c_int, 'nPort'))

		self.TTSRequestFile = cfunc('TTSRequestFile', self.lib, c_int,
									(c_char_p, 'szServer'),
									(c_int, 'nPort'),
									(c_char_p, 'pText'),
									(c_int, 'nTextLen'),
									(c_char_p, 'szSaveDir'),
									(c_char_p, 'szSaveFile'),
									(c_int, 'nSpeakerID'),
									(c_int, 'nVoiceFormat'))

		self._TTSRequestBuffer = cfunc('_TTSRequestBuffer', self.lib, c_void_p,
									(c_int_p, 'sockfd'),
									(c_char_p, 'szServer'),
									(c_int, 'nPort'),
									(c_char_p, 'pText'),
									(c_int, 'nTextLen'),
									(c_int_p, 'nVoiceLen'),
									(c_int, 'nSpeakerID'),
									(c_int, 'nVoiceFormat'),
									(c_int, 'bFirst'),
									(c_int, 'bAll'),
									(c_int_p, 'nReturn'),
									(driver_h.TTSKEY, 'szkey'))

		self._TTSRequestBufferEx = cfunc('_TTSRequestBufferEx', self.lib, c_void_p,
									(c_int_p, 'sockfd'),
									(c_char_p, 'szServer'),
									(c_int, 'nPort'),
									(c_char_p, 'pText'),
									(c_int, 'nTextLen'),
									(c_int_p, 'nVoiceLen'),
									(c_int, 'nSpeakerID'),
									(c_int, 'nVoiceFormat'),
									(c_int, 'nTextFormat'),
									(c_int, 'nVolume'),
									(c_int, 'nSpeed'),
									(c_int, 'nPitch'),
									(c_int, 'nDictNum'),
									(c_int, 'bFirst'),
									(c_int, 'bAll'),
									(c_int_p, 'nReturn'),
									(driver_h.TTSKEY, 'szkey'))

	def request_status(self, ip, status_port):
		""" Send a request status request to server """
		code = self.TTSRequestStatus(ip, status_port)
		return {'status': code, 'status_text': driver_h.SERVER_STATUS[code],
			'data': None}

	def validate_config(self, ip, port, text, voice, fmt):
		""" Helper utility to validate a config

		:returns: status dictionary
		"""
		# these are passed as pointers
		sock = c_int(0)
		buflen = c_int(0)
		code = c_int(0)
		key = driver_h.TTSKEY(0)
		# these are passed as values
		bFirst, bAll = 1, 1
		buf = self._TTSRequestBuffer(sock, ip, port, text, len(text), buflen, 
			voice, fmt, bFirst, bAll, code, key)

		return {'status': code.value, 'status_text': 
			driver_h.RESULT_CODES[code.value], 'data': buf}

	def generate_file_on_server(self, text, dirname, filename, fmt=driver_h.FORMAT_WAV):
		""" Tell server to generate voice file and store in dirname with format fileformat
		Note: This method for test, use request_buffer to get data back from server.
		"""
		code = self.TTSRequestFile(self.server_ip, self.server_port, text, len(text),
								dirname, filename, self.voice, fmt)
		return {'status': code, 'status_text': driver_h.RESULT_CODES[code],
			'data': None}

	def request_buffer(self, text, fmt=driver_h.FORMAT_WAV, reqfirst=True, oneframe=True):
		""" request byte array buffer from server in format fmt

		:returns: dictionary containing return code, code text, and data as bytearray
		"""
		# these are passed as pointers
		sock = c_int(0)
		buflen = c_int(0)
		code = c_int(0)
		key = driver_h.TTSKEY(0)
		# these are passed as values
		bFirst = 1 if reqfirst == True else 0
		bAll = 1 if oneframe == True else 0
		buf = self._TTSRequestBuffer(sock, self.server_ip, self.server_port, text,
					len(text), buflen, self.voice, fmt, bFirst, bAll, code, key)

		if (buf != None and code.value == driver_h.TTS_RESULT_SUCCESS):
			# buf is type <int> pointing to address, allocate memory
			# of buflen bytes and return python bytearray object
			buf = bytearray(string_at(buf, buflen))
			#print '-'.join("%02x" % b for b in buf[:32])

		return {'status': code.value, 'status_text':
			driver_h.RESULT_CODES[code.value], 'data': buf}

	def request_buffer_ex(self, text, fmt=driver_h.FORMAT_WAV, txt_fmt=driver_h.TEXT_NORMAL,
				volume=100, speed=100, pitch=100, dictnum=0, reqfirst=True, oneframe=True):
		""" request byte array buffer from server with extended parameters

		:returns: dictionary containing return code, code text, and data as bytearray
		"""
		# these are passed as pointers
		sock = c_int(0)
		buflen = c_int(0)
		code = c_int(0)
		key = driver_h.TTSKEY(0)
		# these are passed as values
		bFirst = 1 if reqfirst == True else 0
		bAll = 1 if oneframe == True else 0
		txt_fmt = c_int(int(txt_fmt))
		volume = c_int(int(volume))
		speed = c_int(int(speed))
		pitch = c_int(int(pitch))
		dictnum = c_int(int(dictnum))

		buf = self._TTSRequestBufferEx(sock, self.server_ip, self.server_port, text,
					len(text), buflen, self.voice, fmt, txt_fmt, volume, speed, pitch,
					dictnum, bFirst, bAll, code, key)

		if (buf != None and code.value == driver_h.TTS_RESULT_SUCCESS):
			# buf is type <int> pointing to address, allocate memory
			# of buflen bytes and return python bytearray object
			buf = bytearray(string_at(buf, buflen))
			#print '-'.join("%02x" % b for b in buf[:32])

		return {'status': code.value, 'status_text':
			driver_h.RESULT_CODES[code.value], 'data': buf}


class DummyEntry:
	""" Dummy entry class if jvm not able to start.  Note: Java not a requirement for
	production but useful for developers.  To get this working developer must have a
	reasonably recent version of java and the python py4j module installed. """
	def ttsRequestStatus(self, server_ip, status_port):
		return driver_h.TTS_STATUS_DUMMY_DRIVER

	def ttsRequestFile(self, server_ip, server_port, text, dirname, filename, voice, fileformat):
		return driver_h.TTS_DUMMY_DRIVER

	def ttsRequestBuffer(self, server_ip, server_port, text, voice, fmt, bFirst, bAll):
		return driver_h.TTS_DUMMY_DRIVER

	def ttsRequestBufferEx(self, server_ip, server_port, text, voice, fmt, txt_fmt,
				volume, speed, pitch, dictnum, bFirst, bAll):
		return driver_h.TTS_DUMMY_DRIVER


DEF_GW_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'api', 'java')


class JavaDriver(Driver):
	"""
	 Java Neospeech driver checks if we get import error. If error then JavaDriver
	 not supported and warn that both java and py4j python packages are required
	 for this driver. This is not a production requirement as neospeech driver will
	 use the UnixDriver.
	"""
	def __init__(self, gw_dir=DEF_GW_DIR, server_ip="127.0.0.1", voice=driver_h.TTS_KATE_DB):
		super(JavaDriver, self).__init__(server_ip, int(voice))
		self.status = False
		try:
			from py4j.java_gateway import JavaGateway
			from py4j.protocol import Py4JNetworkError
			try:
				from py4j.version import __version__
			except ImportError:      # for backwards compatibility, py4j
				__version__ = '0.7'  # started including version at 0.8
			try:
				# try to connect to neo java gateway, if unable try to load it
				gateway = JavaGateway()
				self.status = gateway.entry_point.get_gw_status()
			except (socket.error, Py4JNetworkError):
				# load the neospeech java gateway and try to connect to it
				# add py4j and voiceware.jar to java classpath before launching
				jsep, sep = ":", os.sep
				py4j_dir = os.path.join(sys.prefix, 'share', 'py4j')
				if sys.platform.lower() == 'cygwin':
					# convert posix path to windows for java
					jsep, sep = ';', '\\'
					gw_dir = subprocess.Popen(["cygpath", "-paw", gw_dir],
						stdout=subprocess.PIPE).communicate()[0].rstrip('\n')
					py4j_dir = subprocess.Popen(["cygpath", "-paw", py4j_dir],
						stdout=subprocess.PIPE).communicate()[0].rstrip('\n')
				elif sys.platform.lower() in ("win32", "win64"):
					jsep = ';'
				py4j_jar = sep.join([py4j_dir, ('py4j' + __version__ + '.jar')])
				if not os.path.exists(py4j_jar):
					raise ImportError("Py4j .jar not found: %s, using dummy driver" % (py4j_jar))
				cpath = jsep.join([gw_dir, py4j_jar, gw_dir + sep + 'voiceware.jar'])
				cmd = ["java", "-cp", cpath, "Gateway"]
				if '--noreload' in sys.argv: cmd.append("--die-on-broken-pipe")
				subprocess.Popen(cmd)
				gateway = JavaGateway()
				self.status = False
				while (self.status == False):
					try:  # retry connetion until gateway is ready
						self.status = gateway.entry_point.get_gw_status()
					except (socket.error, Py4JNetworkError):
						continue
			# all set, ready to go
			self.py4j_gw = gateway 	# reference later to close connection
			self.neo_gw = gateway.entry_point
		except ImportError:
			# not supported use dummy entry
			self.neo_gw = DummyEntry()
			self.py4j_gw = None

	def shutdown(self):
		""" Shutdown the driver doing whatever cleanup appropriate """
		# Note: Do not shutdown gateway as other java drivers may be using it.
		# atexit.register(cleanup) cleans up the gateway if we are using it.

	def request_status(self, ip, status_port):
		""" Send a request status request to server """
		code = self.neo_gw.ttsRequestStatus(ip, int(status_port))
		return {'status': code, 'status_text': driver_h.SERVER_STATUS[code],
			'data': None}

	def validate_config(self, ip, port, text, voice, fmt):
		""" Helper utility to validate a config

		:returns: status dictionary
		"""
		bFirst, bAll = 1, 1

		code = self.neo_gw.ttsRequestBuffer(ip, int(port), text, int(voice), int(fmt), bFirst, bAll)
		buf = self.neo_gw.ttsGetBufferData() if (code == driver_h.TTS_RESULT_SUCCESS) else None

		return {'status': code, 'status_text': driver_h.RESULT_CODES[code], 'data': buf}

	def generate_file_on_server(self, text, dirname, filename, fmt=driver_h.FORMAT_WAV):
		""" Tell server to generate voice file and store in dirname with format fileformat
		Note: This method for test, use request_buffer to get data back from server.
		"""
		code = self.neo_gw.ttsRequestFile(self.server_ip, int(self.server_port), text,
						dirname, filename, int(self.voice), int(fmt))
		return {'status': code, 'status_text': driver_h.RESULT_CODES[code],
			'data': None}

	def request_buffer(self, text, fmt=driver_h.FORMAT_WAV, reqfirst=True, oneframe=True):
		""" request byte array buffer from server in format fmt

		:returns: dictionary containing return code, code text, and data as bytearray
		"""
		bFirst = 1 if reqfirst == True else 0
		bAll = 1 if oneframe == True else 0

		code = self.neo_gw.ttsRequestBuffer(self.server_ip, int(self.server_port), text,
						int(self.voice), int(fmt), bFirst, bAll)
		buf = self.neo_gw.ttsGetBufferData() if (code == driver_h.TTS_RESULT_SUCCESS) else None

		return {'status': code, 'status_text': driver_h.RESULT_CODES[code], 'data': buf}

	def request_buffer_ex(self, text, fmt=driver_h.FORMAT_WAV, txt_fmt=driver_h.TEXT_NORMAL,
				volume=100, speed=100, pitch=100, dictnum=0, reqfirst=True, oneframe=True):
		""" request byte array buffer from server with extended parameters

		:returns: dictionary containing return code, code text, and data as bytearray
		"""
		bFirst = 1 if reqfirst == True else 0
		bAll = 1 if oneframe == True else 0

		code = self.neo_gw.ttsRequestBufferEx(self.server_ip, int(self.server_port), text,
						int(self.voice), int(fmt), int(txt_fmt),
						int(volume), int(speed), int(pitch), int(dictnum),
						bFirst, bAll)
		buf = self.neo_gw.ttsGetBufferData() if (code == driver_h.TTS_RESULT_SUCCESS) else None

		return {'status': code, 'status_text': driver_h.RESULT_CODES[code], 'data': buf}


DLL_FILE = "libttsapi.dll" if sys.platform.lower() == 'win32' else os.path.join("x64", "libttsapi.dll")
DEF_DLL_FILE = os.path.join(LIB_DIR, 'api', 'dll', DLL_FILE)


class WinDriver(UnixDriver):
	def __init__(self, libfile=DEF_DLL_FILE, server_ip="127.0.0.1", voice=driver_h.TTS_KATE_DB):
		# call super, only difference is library driver
		super(WinDriver, self).__init__(libfile, server_ip, int(voice))


def cleanup():
	""" General cleanup, if running a java gateway shut it down.  This is called
	after server shutdown, unittest, or test_driver completion.  If drivers setup
	static instances or gateways that stay around their cleanup should go here.
	"""
	try:
		from py4j.java_gateway import JavaGateway
		try:
			gateway = JavaGateway()
			gateway.shutdown()
		except socket.error:
			pass
	except ImportError:
		pass


def create_neo_driver(server_ip="127.0.0.1"):
	""" Helper to create neospeech driver depending on platform.

	:returns: the neospeech driver appropriate for platform
	"""
	plat = sys.platform.lower()
	if plat == 'linux2':
		driver_klass = UnixDriver
	elif plat == 'win32' or plat == 'win64':
		driver_klass = WinDriver
	elif plat == 'cygwin':
		driver_klass = JavaDriver  # cygwin doesn't like neo's .dll's
	elif plat == 'darwin':
		driver_klass = JavaDriver  # for our mac folks until neo makes .dylibs for us
	else:
		driver_klass = Driver  # unsupported, methods will throw exceptions

	return driver_klass(server_ip=server_ip)


# cleanup processes
atexit.register(cleanup)

