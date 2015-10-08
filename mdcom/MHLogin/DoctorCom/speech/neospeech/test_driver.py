
import sys

from optparse import OptionParser
from subprocess import call

# import local neospeech driver and constants
import driver
from driver_h import TTS_JULIE_DB, TTS_DATA_PORT, TTS_STATUS_PORT, TTS_RESULT_SUCCESS


def test_driver(dtype="java", ip="127.0.0.1", text=None, voice=TTS_JULIE_DB, speed=100,
		pitch=100, outfile="test.wav", dataport=TTS_DATA_PORT, status_port=TTS_STATUS_PORT):
	if dtype == "unix":
		drv = driver.UnixDriver
	elif dtype == "java":
		drv = driver.JavaDriver
	else:
		drv = driver.WinDriver

	neo_driver = drv(server_ip=ip, voice=voice)
	neo_driver.server_port = dataport
	neo_driver.server_status_port = status_port

	stat = neo_driver.request_status(ip, status_port)
	print stat['status_text']

#	text = "My momma told me not to sell drugs"
#	text = "Danger DANGER Will Robinson!!!!"
#	rc = neo_driver.generate_file_on_server(text, "test", "sample")
#	print rc['status_text']

	text = text or "Press 1 if you are having a heart attack, "\
		"press 2 if you are having a stroke, press 3 if you just want attention, or "\
		"press 4 to continue"

	stat = neo_driver.request_buffer_ex(text, speed=speed, pitch=pitch)
	print stat['status_text']

	if (stat['status'] == TTS_RESULT_SUCCESS):
		f = open(outfile, mode='wb')
		f.write(stat['data'])
		f.close()

	return stat['status']


if __name__ == '__main__':
	""" test neospeech drivers outside of django and our project"""
	usage = """"usage: %prog [options] <platform>
	This test intentionally does not determine the platform so loading wrong
	libraries can occur, which is a test in itself.  Other problems arise if you
	are running cygwin in Windows.  The java driver should work on Mac, Windows,
	and Unix/Linux systems with a reasonable version of java.  Test the unix driver
	only on linux2/unix systems not Darwin, BSD, etc.  If you are running the
	non-cygwin Python for Windows the windows driver should work. If you use Java
	make sure python package py4j is installed. To get the latest pip install py4j
	however this is the version tested with our java based neo driver:

	pip install py4j --upgrade
	"""
	parser = OptionParser(usage, epilog="platform: unix, java, or win")
	parser.add_option("-s", "--server-ip", action="store",
					dest="server", default="127.0.0.1",
					help="Neospeech ttssrv server address. Will accept dns name, "
					"ipv4, or ipv6 string, default: %default")
	parser.add_option("-t", "--text-say", action="store",
					dest="textsay", default=None,
					help="Text to say, outputs to a .wav sound file")
	parser.add_option("--speed", action="store",
					dest="speed", default=100,
					help="Speed at which to speak, default: %default")
	parser.add_option("--pitch", action="store",
					dest="pitch", default=100,
					help="Pitch at which to speak, default: %default")
	parser.add_option("-v", "--voice", action="store",
					dest="voice", default=TTS_JULIE_DB,
					help="Voice Id to use, license dependent. For supported voices "
					"check your neospeech configuration.  For a list of all voices "
					"check the driver_h.py VOICES structure, default: %default")
	parser.add_option("-o", "--out-file", action="store",
					dest="outputfile", default="test.wav",
					help="Default is %default")
	parser.add_option("-p", "--play", action="store_true",
					dest="play", default=False,
					help="Play audio file, default: %default")

	(opts, args) = parser.parse_args()

	if (len(args) == 1 and args[0] in ["unix", "java", "win"]):
		rc = test_driver(args[0], opts.server, opts.textsay, opts.voice,
						opts.speed, opts.pitch, opts.outputfile)
		if (rc == TTS_RESULT_SUCCESS):
			print ("Output file: %s" % opts.outputfile)
			if opts.play:
				plat = sys.platform.lower()
				if plat == 'darwin':
					call('afplay -d ' + opts.outputfile, shell=True)
				# check other platforms -> linux2, win32, win64, cygwin, etc...
	else:
		parser.print_help()

