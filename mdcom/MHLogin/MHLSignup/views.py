
# Create your views here.
from django.conf import settings
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.utils.http import urlencode
from django.utils.translation import ugettext as _
from MHLogin.Invites.models import Invitation
from MHLogin.MHLUsers.models import Provider, Broker
from MHLogin.MHLSignup.forms import InvitationEntryForm
from MHLogin.utils.templates import get_context


redirecturls = {
	1: 'Provider/',
	2: 'Provider/',
	10: 'Provider/',
	100: 'Practice/',
	101: 'Staff/',
	300: 'Broker/',
}

createnowredirecturls = {
	1: 'Provider2/',
	2: 'Provider2/',
	# add medical student by xlin in 20120619
	10: 'Provider2/',
	100: 'Practice2/',
	101: 'Staff2/',
}

def register(request):
	context = get_context(request)
	if(request.method == "POST"):
		data = request.POST
	else:
		data = request.GET
	form = InvitationEntryForm(data)
	if(form.is_valid()):
		invite = Invitation.objects.get(code=form.cleaned_data['code'])
		urls = createnowredirecturls if 'createnow' in data else redirecturls
		if(invite.userType in urls):
			#url = ''.join([urls[invite.userType], '?', 
				#urlencode({'0-code':invite.code, '0-email': invite.recipient})])
			url = ''.join([urls[invite.userType], '?', 
				urlencode({'code':invite.code, 'signEmail': invite.recipient})])
			return HttpResponseRedirect(url)
		else:
			raise Exception(_("Don't know what to do with userType %d") % invite.userType)
	if(not data):
		form = InvitationEntryForm()
	context['form'] = form
	return render_to_response("MHLSignup/signup.html", context)


def success(request):
	context = get_context(request)
	return render_to_response('MHLSignup/signup_success.html', context)


def provider_success(request):
	context = get_context(request)
	if settings.CALL_ENABLE:
		userid = request.session.get('userId')
		context['pin'] = request.session.get('pin')
		try:
			code = Provider.objects.filter(id=userid)[0].mdcom_phone
		except:
			code = Broker.objects.filter(user__id=userid)[0].mdcom_phone
		code = '(' + code[:3] + ') ' + code[3:6] + '-' + code[6:]
		context['area_code'] = code
		return render_to_response('MHLSignup/signup_success_number.html', context)
	else:
		return render_to_response('MHLSignup/signup_success.html', context)


def broker_success(request):
	context = get_context(request)
	#return render_to_response('MHLSignup/brokersignup_success.html', context)
	return render_to_response('MHLSignup/signup_success.html', context)

