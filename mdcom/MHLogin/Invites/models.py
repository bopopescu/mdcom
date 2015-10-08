
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.utils.http import urlencode
from django.db.models.signals import post_init
from django.core.urlresolvers import reverse
from MHLogin.Invites.utils import newInviteCode
from MHLogin.utils.constants import USER_TYPE_CHOICES

from django.core.mail import send_mail
from django.template.loader import render_to_string

from django.utils.translation import ugettext_lazy as _
import datetime


class Invitation(models.Model):
	code = models.CharField(max_length=8, unique=True)
	sender = models.ForeignKey(User, related_name="The user sending this invitation")
	recipient = models.EmailField(verbose_name=_('Email Address'))
	userType = models.IntegerField(choices=USER_TYPE_CHOICES, verbose_name=_("UserType"))
	typeVerified = models.BooleanField(default=False, verbose_name=_("TypeVerified"))

	#not used anymore, at some point this should be axed	
	createGroupPractice = models.BooleanField(default=False, verbose_name=_("CreateGroupPractice"))
	# Define if the created practice should automatically be assigned to the
	# group practice. Note that this only should be honored when creating
	# practices.
	assignGroupPractice = models.ForeignKey('MHLPractices.PracticeLocation',\
			related_name="assign group practice", null=True, blank=True,\
			default=None)

	# Set to True if this user is an office manager, and if the user should
	# be allowed to create a practice.
	createPractice = models.BooleanField(default=False, verbose_name=_("CreatePractice"))
	# Define if the created user should automatically be assigned to the
	# practice. Note that this only should be honored when creating office
	# staff and office manager users.
	assignPractice = models.ForeignKey('MHLPractices.PracticeLocation', 
		null=True, blank=True, default=None, verbose_name=_("AssignPractice"))

	requestTimestamp = models.DateTimeField(auto_now_add=True)
	testFlag = models.BooleanField(default=False, verbose_name=_("TestFlag"), 
		help_text=_("Check this if you don't want the recipient to be emailed."))

	def delete(self, canceller=None, createdUser=None, send_notice=False, 
			createdPractice=None, *args, **kwargs):
		# First, log this.
		log = InvitationLog()
		log.populateFromInvite(self)
		log.canceller = canceller
		log.createdUser = createdUser
		log.createdPractice = createdPractice
		log.save()

		super(Invitation, self).delete(*args, **kwargs)

	#modify by xlin in 20120604 to add user check for new requirement
	def email_invite(self, msg=''):
		if (self.testFlag):
			return None
		user = User.objects.filter(email=self.recipient)
		if user:
			self.error = _('This email address is already associated with a DoctorCom account.')
		else:
			emailContext = dict()
			emailContext['sender'] = '%s %s' % (self.sender.first_name, self.sender.last_name)
			emailContext['code'] = self.code
			emailContext['email'] = self.recipient
			emailContext['server_address'] = settings.SERVER_ADDRESS
			emailContext['msg'] = msg
			emailContext['registerurl'] = 'signup/'
	#		if(self.userType < 100):
	#			emailContext['registerurl'] = 'register/'
			emailContext['inviteurl'] = ''.join([settings.SERVER_ADDRESS, self.get_registerlink()])
			# typeconvert self.userType because some forms will assign it a string
			# value, which screws up this comparison.
			#add by xlin in 20120510
			if self.assignPractice:
				emailContext['practice_name'] = self.assignPractice.practice_name
				invitTitle = _('%s Invitation') %\
						self.assignPractice.organization_type.name
			else:
				emailContext['practice_name'] = 'DoctorCom'
				invitTitle = _('DoctorCom Invitation')

			self.userType = int(self.userType)
			msgBody = render_to_string('Invites/inviteIssueEmail.html', emailContext)
			send_mail(invitTitle, msgBody, settings.SERVER_EMAIL, [self.recipient, ], fail_silently=False)

	def get_registerlink(self, additionalArgs=None):
		args = urlencode({'code': self.code, 'signEmail': self.recipient, })
		if(additionalArgs):
			args.update(additionalArgs)

#		if (self.userType < 100):
#			return ''.join(['/register/?', args])
#		else:
		return ''.join([reverse('MHLogin.MHLSignup.views.register'), '?', args])

	def massmail_tuple(self, msg=''):
		if (self.testFlag):
			return None
		emailContext = dict()
		emailContext['sender'] = '%s %s' % (self.sender.first_name, self.sender.last_name)
		emailContext['code'] = self.code
		emailContext['email'] = self.recipient
		emailContext['server_address'] = settings.SERVER_ADDRESS
		emailContext['msg'] = msg
		emailContext['registerurl'] = 'signup/'

		#add by xlin in 20120511 to fix bug 826 that sales man send one invitation not find url address
		emailContext['inviteurl'] = ''.join([settings.SERVER_ADDRESS, self.get_registerlink()])
#		if(self.userType < 100):
#			emailContext['registerurl'] = 'register/'

		# typeconvert self.userType because some forms will assign it a string
		# value, which screws up this comparison.
		self.userType = int(self.userType)

		if self.assignPractice:
			emailContext['practice_name'] = self.assignPractice.practice_name
		else:
			emailContext['practice_name'] = 'DoctorCom'

		msgBody = render_to_string('Invites/inviteIssueEmail.html', emailContext)
		#print msgBody
		return(_('DoctorCom Invitation'), msgBody, settings.SERVER_EMAIL, [self.recipient, ])

	#modify by xlin in 20120604 to change this method when there is a user in User table not resend mail
	def resend_invite(self, msg='', sender=''):

		if (self.testFlag):
			return None
		if not User.objects.filter(email=self.recipient):
			emailContext = dict()
			if sender:
				emailContext['sender'] = sender
			else:
				emailContext['sender'] = '%s %s' % (self.sender.first_name, self.sender.last_name)
			emailContext['code'] = self.code
			emailContext['email'] = self.recipient
			emailContext['server_address'] = settings.SERVER_ADDRESS
			emailContext['msg'] = msg
			emailContext['registerurl'] = 'signup/'
	#		if(self.userType < 100):
	#			emailContext['registerurl'] = 'register/'
			emailContext['inviteurl'] = ''.join([settings.SERVER_ADDRESS, self.get_registerlink()])
			#add by xlin in 20120510
			if self.assignPractice:
				emailContext['practice_name'] = self.assignPractice.practice_name
				org_type_name = ""
				if self.assignPractice and self.assignPractice.organization_type:
					org_type_name = self.assignPractice.organization_type.name
				invitTitle = _('%s Invitation Resend') % org_type_name
			else:
				emailContext['practice_name'] = 'DoctorCom'
				invitTitle = _('DoctorCom Invitation Resend')
			msgBody = render_to_string('Invites/inviteIssueEmail.html', emailContext)
			#print msgBody
			send_mail(invitTitle, msgBody, settings.SERVER_EMAIL, [self.recipient, ], fail_silently=False)
			self.requestTimestamp = datetime.datetime.now()
			self.save()
		else:
			self.error = _('This email address is already associated with a DoctorCom account.')

	def generate_code(self):
		"""
			Gets executed automagically by the post_init signal handler. Do not
			run this directly unless you know what you're doing.
		"""
		newCode = newInviteCode()
		while (Invitation.objects.filter(code=newCode).count()):
			newCode = newInviteCode()
		self.code = newCode

	def sanitize(self):
		from MHLogin.Administration.data_sanitation.generators import genEmail
		self.recipient = genEmail()

	def __unicode__(self):
		return _('Invitation for %s') % self.recipient

	#add by xlin in 20120510 to add cancel method
	def cancel_invitation(self):
		if not User.objects.filter(email=self.recipient):
			emailContext = dict()
			emailContext['code'] = self.code
			emailContext['email'] = self.recipient
			emailContext['server_address'] = settings.SERVER_ADDRESS
			if self.assignPractice:
				emailContext['type'] = self.assignPractice
			else:
				emailContext['type'] = 'DoctorCom'
			msgBody = render_to_string('Invites/inviteRevokeEmail.html', emailContext)
			send_mail(_('DoctorCom Invitation Cancelled'), msgBody, 
				settings.SERVER_EMAIL, [self.recipient], fail_silently=False)
		self.delete()

	def save_invitation(self, msg):
		if not User.objects.filter(email=self.recipient):
			self.email_invite(msg)
			self.save()
		else:
			self.error = _('This email address is already associated with a DoctorCom account.')


def Invitation_SignalHandler_PostInit(sender, instance, **kwargs):
	if (not instance.code):
		instance.generate_code()
post_init.connect(Invitation_SignalHandler_PostInit, sender=Invitation)


class InvitationLog(models.Model):
	code = models.CharField(max_length=8)
	sender = models.ForeignKey(User, related_name="The user who sent this invitation")
	recipient = models.EmailField()
	userType = models.IntegerField(choices=USER_TYPE_CHOICES)
	typeVerified = models.BooleanField(default=False)
	requestTimestamp = models.DateTimeField()

	# If this invitation was cancelled, the below shall record who cancelled it.
	canceller = models.ForeignKey(User, null=True, blank=True, 
		related_name="The user who cancelled this invitation")

	# This field is used to record when this invitation was
	# invalidated, or when this invitation was responded to.
	responseTimestamp = models.DateTimeField(auto_now_add=True)

	# If this user responded and created an account, the resulting user shall
	# be recorded below. If the user failed to respond, this shall be null, and
	# the field /responseTimestamp/ shall record when this invitation was
	# invalidated.
	createdUser = models.ForeignKey(User, null=True, blank=True)
	createdPractice = models.ForeignKey('MHLPractices.PracticeLocation', 
		null=True, blank=True, default=None)

	testFlag = models.BooleanField(default=False)

	def populateFromInvite(self, invitation):
		self.code = invitation.code
		self.sender = invitation.sender
		self.recipient = invitation.recipient
		self.userType = invitation.userType
		self.typeVerified = invitation.typeVerified
		self.requestTimestamp = invitation.requestTimestamp
		self.testFlag = invitation.testFlag

	def sanitize(self):
		from MHLogin.Administration.data_sanitation.generators import genEmail
		self.recipient = genEmail()

	def __unicode__(self):
		return _('Invitation log entry for %s') % self.recipient

