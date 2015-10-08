
#import json
from urllib2 import URLError, HTTPError
from urlparse import urljoin

from twilio import twiml as twilio, TwilioRestException
from twilio.rest import TwilioRestClient
#from twilio.rest.resources import make_twilio_request

from django.http import HttpResponse
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from MHLogin.MHLUsers.models import Provider, MHLUser, OfficeStaff
from MHLogin.MHLUsers.utils import user_is_provider
from MHLogin.utils.decorators import TwilioAuthentication
from MHLogin.utils.mh_logging import get_standard_logger
from MHLogin.utils.admin_utils import mail_admins
from MHLogin.utils.twilio_utils import client

from models import SenderLookup


# Setting up logging
logger = get_standard_logger('%s/DoctorCom/sms.log' % (settings.LOGGING_ROOT),
							'DoctorCom.sms', settings.LOGGING_LEVEL)


def sendSMS_Twilio(request, message, msg_body):
	"""Sends the given message via Twilio. Note that if the message is longer
	than 160 characters, it will be appropriately fragmented, up to a limit of
	99 fragments.

	:param request: The HTTP Request object
	:param message: The MHLogin.DoctorCom.models.Message object to send.
	:returns: None
	:raises: Passes on Exceptions from msg_fragmenter() and twilioSMS_sender().
	"""
	logger.debug('%s: into sendMSM_Twilio with message from %s %s with body %s' %
					(request.session.session_key, message.sender.first_name,
						message.sender.last_name, msg_body))

	# Prepend the DoctorCom notification
	msg_body = _('DoctorCom msg from %(first_name)s %(last_name)s: %(msg_body)s') \
			% {
				'first_name': message.sender.first_name,
				'last_name': message.sender.last_name,
				'msg_body': msg_body
			}

	sms_msgs = msg_fragmenter(msg_body)  # pass Exceptions on to the parent
	sender_provider = user_is_provider(message.sender)

	recipient_pks = list(message.recipients.values_list('pk', flat=True))

	recipients = MHLUser.objects.in_bulk(recipient_pks)
	for recipient_key in recipients.keys():

		recipient = recipients[recipient_key]

		#if recipient is Office Staff, check for cell phone
		#any office staff cand send but only those with cell phone can receive
		#skip those without cell, they only get dashboard msq
		manager_info = OfficeStaff.objects.filter(user=recipient)
		if (manager_info.count() > 0 and not manager_info[0].user.mobile_phone):
			continue

		# sender's phone number
		callerID = None
		current_site = None
		if (sender_provider and sender_provider.mdcom_phone):
			callerID = sender_provider.mdcom_phone
			logger.debug('sender %s is provider. Current site is %s' %
				(sender_provider, sender_provider.current_site))
			current_site = sender_provider.current_site
		else:
			logger.debug('sender %s pk %i is not provider. No Current site.' %
				(message.sender, message.sender.pk))

		if (not callerID):
			# TODO: get caller ID from number pool!
			callerID = alternativeCallerID(message.sender, recipient)

		for msg_part in sms_msgs:
			logger.debug('%s: sending message to %s %s with body %s' %
				(request.session.session_key, recipient.first_name,
					recipient.last_name, msg_part))
			twilioSMS_sender(request, recipient, msg_part, callerID, current_site)


#this function is ivoked when user clicks submit on new message Text button, sms gets
#send to users with cell phones and dashboard message gets sent to all users
#Message object is created by caller
def sendSMS_Twilio_newMessage(request, message_body, attachments, msg_obj, recipient):
	if(msg_obj.sender):
		logger.debug('%s: into sendSMS_Twilio_newMessage with message from %s %s' %
			(request.session.session_key, msg_obj.sender.first_name,
				msg_obj.sender.last_name))
	else:
		logger.debug('%s: into sendSMS_Twilio_newMessage with system message')
	# shortcut variables
	sender = msg_obj.sender

	# Prepend the DoctorCom notification
	if (not sender):
		if(msg_obj.message_type == 'ANS'):
			message_body = _('Urgent DoctorCom answering service message from :%s') % \
				msg_obj.callback_number
			# for urgent calls where msg_obj.callback_number is < 10 digits, means they
			# did not add area code we try to extract it from caller id, this is only for ANS
			if (len(msg_obj.callback_number) < 10 and 'Caller' in
				request.session and len(request.session['Caller']) > 2):
				message_body += " Area Code From Caller Id :%s" % (request.session['Caller'][0:3])
		elif(msg_obj.message_type == 'VM'):
			message_body = _('DoctorCom voicemail from: %s') % msg_obj.callback_number
		else:
			message_body = _('DoctorCom notification: %s') % msg_obj.callback_number

	elif (not attachments):
		message_body = _('DoctorCom msg from %(first_name)s %(last_name)s') \
				% {
					'first_name': sender.first_name,
					'last_name': sender.last_name,
				}
	else:
		message_body = _('DoctorCom msg w/attachment from '
						'%(first_name)s %(last_name)s') \
				% {
					'first_name': sender.first_name,
					'last_name': sender.last_name,
				}

	sms_msgs = msg_fragmenter(message_body)  # pass Exceptions on to the parent

	# Caller ID to display. If None, we use alternative callerID to generate
	# sender/recipient caller ID pairings from the common Twilio CallerID pool.
	callerID = None

	# Populate callerID, current_site
	if sender:
		provider_info = Provider.objects.filter(user__pk=sender.pk).\
				values('mdcom_phone', 'current_site')
		if (len(provider_info) == 1):
			logger.debug('Sender %s is provider. Current site is %s' %
				(sender, provider_info[0]['current_site']))
			if (provider_info[0]['mdcom_phone']):
				callerID = provider_info[0]['mdcom_phone']
	else:
		logger.debug('System message notification')

	# Next, generate the recipients list.
	recipient_pks = list(msg_obj.recipients.values_list('pk', flat=True))
	recipient_pks.extend(list(msg_obj.ccs.values_list('pk', flat=True)))

#	recipients = MHLUser.objects.in_bulk(recipient_pks)

	if(msg_obj.sender):
		sender_name = ' '.join([msg_obj.sender.first_name, msg_obj.sender.last_name, ])
	else:
		sender_name = None

	#if recipient is Office Staff, check for cell phone
	#any office staff cand send but only those with cell phone can receive
	#skip those without cell, they only get dashboard msq
	#1/31/11 - added skipping providers without mobile phone - they will get
	#dashboard msg so ok not to receive sms comment out office manager logic in case
	#we even want to change back to not allow messaging without cell for providers
	#manager_info = OfficeStaff.objects.filter(user=recipient)
	#if (manager_info.count() > 0 and not manager_info[0].user.mobile_phone):
	#	continue
	if (not recipient.mobile_phone):
		return

#	if (not recipient.mobile_phone):
#		mail_admins('Skipped SMS messaging recipient %i'%recipient.pk,
#					'%s: Attempted to send message %s to user without mobile_phone: %i'%
#					(request.session.session_key, msg_obj.uuid, recipient.pk,))
#		logger.warn('%s: Attempted to send message %s to user without mobile_phone: %i'%
#				(request.session.session_key, msg_obj.uuid, recipient.pk,))
#
#		# Send an email instead.
#		try:
#			if(sender_name):
#				subject = ''.join(["New DoctorCom Message from ", sender_name])
#			else:
#				subject = ''.join(["New DoctorCom Message"])
#			body = "You've received a DoctorCom system message."
#			send_mail(
#					subject,
#					body,
#					settings.SERVER_EMAIL,
#					[user.email],
#					fail_silently=False
#				)
#		except SMTPException as e:
#			# Generate a unique error code
#			err_code = '-'.join(['DC-SMS', msg.pk,str(int(time())%10000000)])
#			logger.error('%s-%s: Mail send error to recipient %i'%(request.session.session_key,
#						err_code, recipient.pk,))
#			mail_admins('%s: Mail Send Error'%(err_code,), '\n'.join([e, err_code, inspect.trace(),]))
#		return

	if (not callerID and msg_obj.sender):
		sender_mhluser = MHLUser.objects.get(pk=msg_obj.sender.pk)
		recipient_mhluser = MHLUser.objects.get(pk=recipient.pk)
		callerID = alternativeCallerID(sender_mhluser, recipient_mhluser)
	elif(not callerID):
		callerID = settings.TWILIO_CALLER_ID

	msg_part_counter = 0  # Message part counter -- there's gotta be a better way to do this!

	for msg_part in sms_msgs:
		logger.debug('%s: sending message to %s %s with body %s' %
				(request.session.session_key, recipient.first_name,
					recipient.last_name, msg_part))
		try:
			twilioSMS_unloggedSender(request, recipient.mobile_phone, msg_part, sender=callerID)
		except TwilioRestException as e:
			err_email_body = '\n'.join([
					'SMS Send Error!',
					''.join(['Server: ', settings.SERVER_ADDRESS]),
					''.join(['Session: ', str(request.session.session_key)]),
					''.join(['Message: ', str(msg_obj.pk)]),
					''.join(['Sender: ', str(msg_obj.sender.pk) if msg_obj.sender else '']),
					''.join(['Recipient: ', str(recipient.pk)]),
					''.join(['Message part: ', str(msg_part_counter)]),
					''.join(['Exception: ', str(e)]),
					''.join(['Exception data (code): ', str(e.code)]),
				])
			mail_admins('SMS Send Error', err_email_body)
		except HTTPError as e:
			err_email_body = '\n'.join([
					'SMS Send Error!',
					''.join(['Server: ', settings.SERVER_ADDRESS]),
					''.join(['Session: ', str(request.session.session_key)]),
					''.join(['Message: ', str(msg_obj.pk)]),
					''.join(['Sender: ', str(msg_obj.sender.pk) if msg_obj.sender else '']),
					''.join(['Recipient: ', str(recipient.pk)]),
					''.join(['Message part: ', str(msg_part_counter)]),
					''.join(['Exception: ', str(e)]),
					#''.join(['Exception data: ', str(e.reason)]),
					''.join(['Exception data (read): ', str(e.read())]),
				])
			mail_admins('SMS Send Error', err_email_body)
		except URLError as e:
			err_email_body = '\n'.join([
					'SMS Send Error!',
					''.join(['Server: ', settings.SERVER_ADDRESS]),
					''.join(['Session: ', str(request.session.session_key)]),
					''.join(['Message: ', str(msg_obj.pk)]),
					''.join(['Sender: ', str(msg_obj.sender.pk) if msg_obj.sender else '']),
					''.join(['Recipient: ', str(recipient.pk)]),
					''.join(['Message part: ', str(msg_part_counter)]),
					''.join(['Exception: ', str(e)]),
					''.join(['Exception data: ', str(e.reason)]),
				])
			mail_admins('SMS Send Error', err_email_body)
		except IOError as e:
			# Generic exception handler -- this should generally not be hit.
			err_email_body = '\n'.join([
					'SMS Send Error!',
					''.join(['Server: ', settings.SERVER_ADDRESS]),
					''.join(['Session: ', str(request.session.session_key)]),
					''.join(['Message: ', str(msg_obj.pk)]),
					''.join(['Sender: ', str(msg_obj.sender.pk) if msg_obj.sender else '']),
					''.join(['Recipient: ', str(recipient.pk)]),
					''.join(['Message part: ', str(msg_part_counter)]),
					''.join(['Exception: ', str(e)]),
					''.join(['Exception data: ', str(e.args)]),
				])
			mail_admins('SMS Send Error', err_email_body)
		except Exception as e:
			raise
			# Generic exception handler -- this should generally not be hit.
			err_email_body = '\n'.join([
					'SMS Send Error!',
					'Unknown Exception Type',
					''.join(['Server: ', settings.SERVER_ADDRESS]),
					''.join(['Session: ', str(request.session.session_key)]),
					''.join(['Message: ', str(msg_obj.pk)]),
					''.join(['Sender: ', str(msg_obj.sender.pk) if msg_obj.sender else '']),
					''.join(['Recipient: ', str(recipient.pk)]),
					''.join(['Message part: ', str(msg_part_counter)]),
					''.join(['Exception: ', str(e)]),
				])
			mail_admins('SMS Send Error -- Unknown Exception Type', err_email_body)
		msg_part_counter += 1


def twilioSMS_sender(request, recipient, fragment, callerID, current_site=None, resend_of=None):
	abs_uri = '://'.join([settings.SERVER_PROTOCOL, settings.SERVER_ADDRESS])
	url = reverse('MHLogin.DoctorCom.SMS.views.twilioSMS_statusResponse')

	twilioSMS_unloggedSender(request, recipient.mobile_phone, fragment,
		sender=callerID, callBack=urljoin(abs_uri, url))


def twilioSMS_unloggedSender(request, recipient, body, sender=settings.TWILIO_CALLER_ID, callBack=None):
	"""Sends an SMS message without logging it.

	:param request: The HTTP Request object
	:param recipient: The destination mobile phone number.
	:param body: The body of the message to be sent. The length of this MUST NOT be
		greater than 160 characters. An exception is raised if it is.
	:param sender: The "sender" of the SMS message. Note that this value MUST be a
		DoctorCom phone number (one that we own through our Twilio account).
		If it isn't, then urllib will raise an exception since Twilio will
		come back with HTTP status 400.
	:param callBack: The url to have Twilio call back to with the SMS delivery
			status. Default None.
	"""
	if (len(body) > 160):  # fragment?
		raise Exception('Message is too long: "%s"' % (body,))

	sms_resp = None
	try:
#		d = {
#			'From': sender,
#			'To': recipient,
#			'Body': body,
#			'Method': 'POST',
#			'StatusCallback': callBack or '',
#		}
#		auth, uri = client.auth, client.account_uri
#		resp = make_twilio_request('POST', uri + '/SMS/Messages', auth=auth, data=d)
#		sms_resp = json.loads(resp.content)
# 		2010-04-01 version
		sms_resp = client.sms.messages.create(body=body, to=recipient,
			from_=sender, status_callback=callBack)
	except TwilioRestException as re:
		msg = re.msg  # json.loads(re.msg)
		if (re.status == 400):
			logger.warn('%s: got HTTP400 from Twilio: %s' % 
					(str(request.session.session_key), msg))
		else:
			logger.error('%s: Got HTTP from Twilio: %s' % 
					(str(request.session.session_key), msg))

		# An error occurred, re-raise the exception
		raise TwilioRestException(re.status, re.uri, msg, re.code or 0)

	return sms_resp


def alternativeCallerID(sender, recipient):
	"""
	Creates a mapping between an SMS sender and recipient, should the sender
	NOT have a DoctorCom number.

	To create a mapping, just pass in the sender and recipient normally.

	To look up a mapping, pass the recipient and sender in reverse. That is, with the
	inbound sender as the function argument /recipient/, and the inbound recipient as
	the function argument /sender/.

	Arguments:
		sender - An MHLUser object; the sender of the SMS message
		recipient - An MHLUser object; the recipient of the SMS message
	Returns:
		A caller ID to send the user.
	"""

	# First, see if this mapping already exists.
	mapping = SenderLookup.objects.filter(user=sender).filter(mapped_user=recipient)
	if (mapping.count() == 1):
		mapping = mapping.get()
		mapping.save()  # update the timestamp
		return mapping.number
	if (mapping.count() > 1):
		import cPickle
		mail_admins('Django Error: Multiple SenderLookup Objects Found',
			cPickle.dumps(list(mapping.all())))
		return mapping[0].number

	# Okay, the mapping doesn't exist. Create it.

	# If the user hasn't exhausted the number pool....
	mapping_count = SenderLookup.objects.filter(mapped_user=recipient).count()
	if (mapping_count < len(settings.TWILIO_SMS_NUMBER_POOL)):
		# number pool hasn't been exhausted yet.
		lookup = SenderLookup(
				user=sender,
				mapped_user=recipient,
				number=settings.TWILIO_SMS_NUMBER_POOL[mapping_count],
			)
		lookup.save()
		return lookup.number
	else:
		oldest = SenderLookup.objects.filter(mapped_user=recipient).order_by('timestamp', 'pk')[0]

		sms_number = oldest.number
		oldest.delete()
		lookup = SenderLookup(
				user=sender,
				mapped_user=recipient,
				number=sms_number,
			)
		lookup.save()
		return lookup.number


@TwilioAuthentication()
def twilioSMS_statusResponse(request):
	# request.POST contains, as a failing example:
	# <QueryDict: {
	#				u'AccountSid': [u'AC0d586a0cd63a017a15042803b749fa3f'],
	#				u'From': [u'6503183753'],
	#				u'SmsSid': [u'SMc38aee85b7b24085f479e593ff65e18d'],
	#				u'SmsStatus': [u'failed'],
	#				u'To': [u'9196277711']}>
	# and as a successful example:
	#<QueryDict: {
	#				u'AccountSid': [u'AC0d586a0cd63a017a15042803b749fa3f'],
	#				u'From': [u'6503183753'],
	#				u'SmsSid': [u'SMd7e06e049322a8cfa2fee0a48f951c1d'],
	#				u'SmsStatus': [u'sent'],
	#				u'To': [u'9196277711']}>,

	logger.debug('%s: into twilioSMS_statusResponse' % (request.session.session_key,))

	#brian - review please
	# TODO: Data sanitation is necessary on the following request.POST values.
	# For the time being, we're just going to trust Twilio.
	#status = request.POST['SmsStatus']
	#sid = request.POST['SmsSid']

	#msg = MessageLog.objects.get(twilio_sid=sid)
	#if (status == "sent"):
	#	msg.twilio_status = 'SU'
	#elif (status == "failed"):
	#	msg.twilio_status = 'FA'
	#else:
	#	import cPickle
	#	mail_admins('Django Error: Unknown Twilio SMS Status',
		#	cPickle.dumps(request.POST))
	#msg.save()

	return HttpResponse(str(twilio.Response()), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)


@TwilioAuthentication()
def twilioSMS_incoming(request):

	logger.debug('%s: into twilioSMS_incoming' % (request.session.session_key,))

	# TODO: Data sanitation is necessary on the following request.POST values.
	# For the time being, we're just going to trust Twilio.
	status = request.POST['SmsStatus']
	sid = request.POST['SmsSid']
	from_no = request.POST['From']
	to_no = request.POST['To']
	body = request.POST['Body']

	# First, check to ensure that the sender is a DoctorCom user.
	fromQuerySet = MHLUser.objects.filter(mobile_phone=from_no)
	if (not fromQuerySet.count()):
		# TODO: Reply back with an error.
		pass
	if (fromQuerySet.count() > 1):
		# More than one user has this mobile phone number!
		raise Exception('More than one user has the sender\'s mobile phone number')
		# TODO: mail_admins, then iterate over all recipients with messages.
	fromUser = fromQuerySet.get()

	toQuerySet = Provider.objects.filter(mdcom_phone=to_no)
	if (not toQuerySet.count()):
		# this is either an unassigned number, or this is from the generic SMS
		# number pool.
		if (to_no in settings.TWILIO_SMS_NUMBER_POOL):
			lookupEntry = SenderLookup.objects.filter(number=to_no).filter(mapped_user=fromUser).get()
			lookupEntry.save()  # update the timestamp
			toUser = lookupEntry.user
		else:
			mail_admins('Django Error: Incoming SMS message to unassigned number',
				repr(request.POST))
			return HttpResponse(str(twilio.Response()), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)
	else:
		toUser = toQuerySet.get().user

	#build dashboard message to send along with sms
	from ..Messaging.models import Message, MessageRecipient
	message = Message(sender=fromUser, sender_site=None,
			message_type='SMS', subject="DoctorCom msg from %s %s" %
				(fromUser.first_name, fromUser.last_name))
	message.save()

	#formatted_body = ''.join(['DoctorCom msg from ', fromUser.first_name, ' ',
	#   fromUser.last_name, ': ', body])
	message_body = message.save_body(body)
	MessageRecipient(message=message, user=toUser).save()
	#message Send() also takes care of SMS, comment out sendSMS_Twilio(request, message, message_body)
	message.send(request, message_body)

	#sendSMS_Twilio(request, message, message_body)
	return HttpResponse(str(twilio.Response()), mimetype=settings.TWILIO_RESPONSE_MIMETYPE)


def msg_fragmenter(message, max_length=160):
	"""Splits the given message string into a series of messages, suitable for
	   transmission via SMS (if the default max_length is used).

	  Known Issues:
	  	This function is ONLY guaranteed to work on messages which fragment into
	  	<100 segments.

	  TODO:
	  	Update this codebase to raise specific exceptions, rather than generic ones.

	:param message: A string, to be fragmented
	:param max_length: The maximum length for any given message, in characters.
	:returns: A list of strings, each of which comprises a message. If fragmenting is
	   	necessary, all messages will be appended with an ellipses (...), and
	   	only the first message will be appended with the message number over
	   	total number of messages.
	   	Additionally, if fragmenting is necessary, all messages except the first
	   	will be prepended with the message number over the total number of
	   	messages.
	   	If fragmentation is NOT necessary, the message will simply be returned
	   	as the only element of a list.
	   	Note that fragmentation will only occur over word boundaries (i.e., the
	   	message is split on spaces).
	:raises:
	  	- generic Exception if fragmentation results in >100 messages.
	  	- generic Exception if any fragment ultimately results in a message with length > max_length.
		- generic Exception if a single word is longer than the message body can carry.
	"""

	# Dev notes:
	# 1. Ellipses at the end of messages will be separated from the text with
	#    a space.
	# 2. We're going to assume a maximum message fragment count of 99. If there
	#    are more than that, this code MAY EXCEED MAX_LENGTH!

	if (len(message) <= max_length):
		return [message]

	words = message.split()

	# output is a list of lists. The list of lists is because Python's string
	# implementation is based on constants, and lots of string operations
	# command a very high runtime expense. Generating a list of strings, then
	# joining them all at the end is cheaper, by far.
	# Also, the first element of each message is the total character count for
	# that message.
	output = [[0, ], ]
	message_count = 1  # The current message number, and in the end, the total message count

	# indices aren't exactly a Pythonic way of doing things, but this is
	# ultimately (in the long run) not going to be run much.
	idx = 0

	# Loop over message to generate the first message
	while (idx < len(words)):
		if (len(words[idx]) >= max_length - 9):  # -9 for the reason below in if(output[-1][0]....
			raise Exception("There's a word that exceeds the maximum length.")
		# Note: the below line (the if condition) technically is off-by one, but
		# is off-by-one in a conservative fashion (i.e., will produce a maximum
		# length of max_length - 1), so it is being left alone as it will help
		# to couch us against errors.
		if (output[-1][0] + len(words[idx]) + 9 > max_length):
			# +9 to account for the space, ellipses, space, 1 / message_count maximum
			# 9-character postfix. the first message is complete -- nothing more can be
			# put into it without exceeding max_length.
			output[-1].append('... 1/')
			output[-1][0] += 6
			message_count += 1
			break
		else:
			output[-1][0] += 1 + len(words[idx])  # +1 to account for a space character.
			output[-1].append(words[idx])
			output[-1].append(' ')
		idx += 1

	output.append([6, '2/', ': '])  # Start the next message.

	# Now generate the rest of the messages
	while (idx < len(words)):
		if (len(words[idx]) >= max_length - 9):  # -9 for the reason below in if(output[-1][0]....
			raise Exception("There's a word that exceeds the maximum length.")
		# Note: the below line (the if condition) technically is off-by one, but
		# is off-by-one in a conservative fashion (i.e., will produce a maximum
		# length of max_length - 1), so it is being left alone as it will help
		# to couch us against errors.
		if (output[-1][0] + len(words[idx]) + 9 > max_length): 
			# +4 to account for the ellipses 3-character postfix, plus an off-by-one error couch.
			# the next message is complete -- nothing more can be put into it
			# without exceeding max_length.
			output[-1].append('...')
			output[-1][0] += 3
			message_count += 1
			output.append([0, '%i/' % (message_count,), ': '])
			output[-1][0] += len(output[-1][1]) + 2 + 2
			# 2 is for the total message count maximum length, 2 is len(output[-1][2])
		else:
			output[-1][0] += 1 + len(words[idx])  # +1 to account for a space character.
			output[-1].append(words[idx])
			output[-1].append(' ')
			idx += 1

	# first message gets treated differently than the others
	first_message = output.pop(0)
	first_message.pop(0)  # drop the length
	first_message.append(str(message_count))
	joined = ''.join(first_message)

	if (len(joined) > max_length):  # sanity check
		raise Exception('first_message was too long. len(first_message) '
					'is %i and message is \'%s\'' % (len(joined), message))

	final_output = [joined, ]

	for msg in output:
		msg.pop(0)  # drop the length
		msg.insert(1, str(message_count))  # add in the total number of messages

		# All messages except the first have an appended space. Eliminate it.
		if (msg[-1] == ' '):
			msg.pop()

		joined = ''.join(msg)

		if (len(joined) > max_length):  # sanity check
			raise Exception('This message was too long. len(message) '
						'is %i, message_count is %i and message is \'%s\'' %
							(len(joined), msg[0], message))

		final_output.append(joined)

	if (len(final_output) > 99):
		raise Exception('Message too long.')

	return final_output

