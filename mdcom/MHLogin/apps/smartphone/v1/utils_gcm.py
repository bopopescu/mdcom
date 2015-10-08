import urllib
import urllib2

GCM_URL = 'https://android.googleapis.com/gcm/send'

class GCM(object):

	def __init__(self, api_key):
		self.api_key = api_key

	def construct_payload(self, registration_ids, data=None, collapse_key=None,
							delay_while_idle=False, time_to_live=None):

		payload = {'registration_id': registration_ids}
		if data:
			for k in data.keys():
				payload.update({'data.%s' % k: data[k]})

		if delay_while_idle:
			payload['delay_while_idle'] = delay_while_idle

		if time_to_live:
			payload['time_to_live'] = time_to_live
			if collapse_key is None:
				raise Exception("collapse_key is required when time_to_live is provided")

		if collapse_key:
			payload['collapse_key'] = collapse_key

		return payload

	def make_request(self, data):
		headers = {
			'Authorization': 'key=%s' % self.api_key
		}
		
		data = urllib.urlencode(data)
		req = urllib2.Request(GCM_URL, data, headers)

		try:
			response = urllib2.urlopen(req).read()
		except urllib2.HTTPError as e:
			if e.code == 400:
				raise Exception("The request could not be parsed as JSON")
			elif e.code == 401:
				raise Exception("There was an error authenticating the sender account")
			# TODO: handle 503 and Retry-After
		except urllib2.URLError as e:
			raise Exception("There was an internal error in the GCM server while trying to process the request")
		return response


	def plaintext_request(self, registration_id, data=None, collapse_key=None,
							delay_while_idle=False, time_to_live=None):

		if not registration_id:
			raise Exception("Missing registration_id")

		payload = self.construct_payload(
			registration_id, data, collapse_key,
			delay_while_idle, time_to_live
		)
		return self.make_request(payload)
