

class KMSException(Exception):
	"""
	Base exception for all KMS exceptions.
	"""
	pass


class KeyInvalidException(KMSException):
	"""
	General exception when wrong credentials are given to decrypt private RSA
	key or if a user does not have a matching private key for a given publickey.
	For example in the case where a user may be trying to decrypt a message sent
	to a practice in which they were not granted access to.
	"""
	pass
