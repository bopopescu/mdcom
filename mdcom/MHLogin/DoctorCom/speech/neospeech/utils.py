

from ctypes import CFUNCTYPE, POINTER, c_int

c_int_p = POINTER(c_int)


def cfunc(fname, lib, ret, *args):
	""" Helper to build a C function.

	Example function having default values:
	a_c_function = cfunc('name_of_c_func', lib, c_int,
                   (c_int, 'enum_struct')
                   (c_int, 'buf_length')
                   (c_char_p, 'a_ptr')
                   (c_int, 'option')
	And calling it:
	rc = a_c_function(SAMPLE_ENUM_VAL2, 99, None, 0)

	:param fname: the name of the function
	:param lib: the C-library, eg. the Linux/Unix .so, Mac .dylib, or
		Windows .dll file
	:param ret: the return object of the function
	:param *args: C function parameters which are each a 2 tuple consisting of:
		(c_type, name_of_parameter)
	:returns: a fully functional python function that calls a c-function
	"""

	ctypes = []
	#  cflags = [] # not yet
	for arg in args:
		ctypes.append(arg[0])
		# we can store flags later, for now get this working
		#cflags.append(arg[1])

	return CFUNCTYPE(ret, *ctypes)((fname, lib))  # ,tuple(cflags))


class StatusDict(dict):
	"""Implementation Status dictionary for neospeech."""
	def __getitem__(self, key):
		try:
			return dict.__getitem__(self, key)
		except KeyError, keyerr:
			return "Invalid key %s in %s" % (str(keyerr), self)

