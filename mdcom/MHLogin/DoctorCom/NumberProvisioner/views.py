
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.utils.translation import ugettext_lazy as _

from MHLogin.DoctorCom.NumberProvisioner.forms import LocalNumberForm
from MHLogin.DoctorCom.NumberProvisioner.utils import twilio_ConfigureProviderLocalNumber
from MHLogin.DoctorCom.IVR.models import VMBox_Config
from MHLogin.MHLUsers.utils import getCurrentUserInfo
from MHLogin.utils.templates import get_context


def provisionLocalNumber(request):
	# basic checks to ensure that the user may request a new phone number here
	#user = user_is_provider(request.user)
	user = getCurrentUserInfo(request)
	if (not user or not user.needConfigureProvisionLocalNumber):
		return HttpResponseRedirect('/')

	context = get_context(request)
	context['ajaxPageURL'] = reverse('MHLogin.DoctorCom.NumberProvisioner.views.AJAX_provisionLocalNumber')
	return render_to_response('DoctorCom/NumberProvisioner/provision_number.html', context)


def AJAX_provisionLocalNumber(request):
	"""
	Displays and handles the form to provision a new number. This only returns
	an HTML snippet pertaining to phone number allocation.
	.. document private functions
	.. autofunction:: _removeNumberPoolNumber
	"""
	# basic checks to ensure that the user may request a new phone number here
	#user = user_is_provider(request.user) # /user/ gets used later for setting the mdcom phone value
	user = getCurrentUserInfo(request)
	if (not user or not user.needConfigureProvisionLocalNumber):
		return HttpResponseRedirect('/')

	context = get_context(request)

	if (settings.DEBUG):
		context['debug'] = True

	if (request.method == 'POST'):
		numberForm = LocalNumberForm(request.POST)
		if (numberForm.is_valid()):
			pin = request.POST['pin']

			# LocalNumberForm, area_code, pin, mdcom_phone, mdcom_phone_sid
			mdcom_phone = numberForm.mdcom_phone
			mdcom_phone_sid = numberForm.mdcom_phone_sid
	
			user.mdcom_phone = mdcom_phone
			user.mdcom_phone_sid = mdcom_phone_sid
	
			#add doctorcom number
			if settings.CALL_ENABLE:
				user_type = ContentType.objects.get_for_model(user)
				config = VMBox_Config.objects.get(owner_type=user_type, owner_id=user.pk)
				config.change_pin(request, new_pin=pin)
				config.save()
				twilio_ConfigureProviderLocalNumber(user, user.mdcom_phone)

			user.save()
			context['new_number'] = "(%s) %s-%s" % (mdcom_phone[0:3],
				mdcom_phone[3:6], mdcom_phone[6:],)
			context['pin'] = pin
			return render_to_response('DoctorCom/NumberProvisioner/provision_complete.html', context)
	else:
		numberForm = LocalNumberForm()

	context['form'] = numberForm
	return render_to_response('DoctorCom/NumberProvisioner/local_number_form.html', context)


def _removeNumberPoolNumber(numberPoolQuerySet):
	"""
	Takes a Django QuerySet of NumberPool objects, and deletes the first item.
	This specific function is desirable since just removing numbers without
	concern to concurrency issues will lead to issues.

	Which is to say, if two people try to allocate the same number at once,
	we can run into a problem where the same number has delete() called on it
	twice. This function catches that error and returns False if the number
	could not be allocated.

	On success, returns a tuple ('phone_number', 'phone_number_sid'). Otherwise,
	returns False.
	"""

	new_number = False
	try:
		new_number = numberPoolQuerySet[0].delete()
	except IndexError:
		return False

	return new_number


def provisionTollFreeNumber(request):
	pass


def AJAX_provisionTollFreeNumber(request):
	pass

