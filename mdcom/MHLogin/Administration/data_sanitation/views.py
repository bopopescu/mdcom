
from django.conf import settings

from django.shortcuts import render_to_response
#from django.contrib.auth.models import User

from MHLogin.Administration.data_sanitation.forms import sanitationConfirmationForm
from MHLogin.MHLUsers.decorators import RequireAdministrator
from MHLogin.utils.templates import get_context
from django.utils.translation import ugettext_lazy as _

# sanitation generators
import generators


@RequireAdministrator
def cleanDB(request):
	context = get_context(request)

	if (settings.SERVER_ADDRESS == "www.mdcom.com"):
		return render_to_response('data_sanitation/production_error.html', context)
	if (not settings.DEBUG):
		raise Exception(_('Debug mode must be set to sanitize data'))

	context = get_context(request)

	if (request.method == "POST"):
		form = sanitationConfirmationForm(request.POST)
		if (form.is_valid()):
			# always run clean_MHLUsers first since other clean functions will
			# pull from the user's name
			clean_MHLUsers()
			clean_DoctorCom()
			clean_Billing()
			clean_Invites()
			clean_followup()
	else:
		form = sanitationConfirmationForm()

	context['form'] = form
	context['server_address'] = settings.SERVER_ADDRESS
	context['server_port'] = settings.SERVER_PORT
	return render_to_response('data_sanitation/confirmation.html', context)


def clean_Billing():
	from MHLogin.Billing.models import BillingAccount
	from MHLogin.MHLUsers.models import MHLUser

	accounts = BillingAccount.objects.all()
	for account in accounts:
		mhluser = MHLUser.objects.get(pk=account.user.pk)

		account.address1 = mhluser.address1
		account.address2 = mhluser.address2
		account.city = mhluser.city
		account.state = mhluser.state
		account.cc_num = '1234567890123456'
		account.cc_exp_month = '01'
		account.cc_exp_year = '15'
		account.save()


def clean_DoctorCom():
	from MHLogin.DoctorCom.models import PagerLog

	pages = PagerLog.objects.all()
	for page in pages:
		page.callback = generators.genPhone()
		page.save()

	clean_DoctorCom_IVR()


def clean_DoctorCom_IVR():
	from MHLogin.DoctorCom.IVR.models import VMBox_Config, VMMessage

	configs = VMBox_Config.objects.all()
	for config in configs:
		config.sanitize()
		config.save()

	msgs = VMMessage.objects.all()
	for msg in msgs:
		msg.sanitize()
		msg.save()


def clean_Invites():
	from MHLogin.Invites.models import Invitation, InvitationLog

	invites = Invitation.objects.all()
	for invite in invites:
		invite.sanitize()
		invite.save()

	invite_logs = InvitationLog.objects.all()
	for log in invite_logs:
		log.sanitize()
		log.save()


def clean_followup():
	from MHLogin.followup.models import FollowUps

	follow_ups = FollowUps.objects.all()
	for follow_up in follow_ups:
		follow_up.sanitize()
		follow_up.save()


def clean_MHLUsers():
	from MHLogin.MHLUsers.models import Provider, MHLUser, OfficeStaff

	providers = Provider.objects.all()
	for provider in providers:
		if (provider.office_address1):
			provider.office_address1 = generators.genAddress1()
		if (provider.office_address2):
			provider.office_address2 = generators.genAddress2()
		if (provider.office_phone):
			provider.office_phone = generators.genPhone()
		if (provider.pager):
			provider.pager = generators.genPhone()
		if (provider.pager_extension):
			provider.pager_extension = ''
		if (provider.mdcom_phone):
			provider.mdcom_phone = generators.genPhone()
		provider.save()

	officeStaffers = OfficeStaff.objects.all()
	for officeStaff in officeStaffers:
		if (officeStaff.office_address1):
			officeStaff.office_address1 = generators.genAddress1()
		if (officeStaff.office_address2):
			officeStaff.office_address2 = generators.genAddress2()
		if (officeStaff.office_phone):
			officeStaff.office_phone = generators.genPhone()
		if (officeStaff.pager):
			officeStaff.pager = generators.genPhone()
		if (officeStaff.pager_extension):
			officeStaff.pager_extension = ''
		#if (officeStaff.mdcom_phone):
		#	officeStaff.mdcom_phone = generators.genPhone()
		officeStaff.save()

	users = MHLUser.objects.all()
	for user in users:
		if (user.gender == 'M'):
			user.first_name = generators.genMaleFirstName()
		else:
			user.first_name = generators.genFemaleFirstName()
		user.last_name = generators.genSurname()
		user.username = generators.genUsername(user.first_name, user.last_name, user.id).lower()
		user.email = generators.genEmail(user.username)
		if (user.phone):
			user.phone = generators.genPhone()
		if (user.mobile_phone):
			user.mobile_phone = generators.genPhone()
		if (user.address1):
			user.address1 = generators.genAddress1()
		if (user.address2):
			user.address2 = generators.genAddress2()
		if (user.photo):
			user.photo = None
		user.set_password('demo')
		user.save()

	# reset the username for user id=2 (Brian's administrator user)
	adminUser = MHLUser.objects.get(id=2)
	adminUser.username = 'admin'
	adminUser.save()

	# create new users for Maria and Miriam

