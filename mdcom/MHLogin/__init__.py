try:
	from MHLogin._version import __version__
except ImportError:
	# setup.py generates _version.py.__version__ from recent production
	# source control tag.  Running setup.py in devl environments is not 
	# required but recommended.  To bypass create a _version.py file 
	# in MHLogin with __version__ declared in the form:  
	# __version__ = '1.60.1.a.b.c...' first 3 elements being user faced
	__version__ = '.unknown'
