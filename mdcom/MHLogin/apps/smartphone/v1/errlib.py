"""
An errors library for all error codes in section A.1 of the Interface Document.
"""
import json

from django.http import HttpResponseBadRequest
from django.utils.translation import ugettext as _


def err_GE002():
	err_obj = {
		'errno': 'GE002',
		'descr': _('HTTP GET used when only POST is supported for this path.'),
	}
	return HttpResponseBadRequest(content=json.dumps(err_obj), mimetype='application/json')


def err_GE010():
	err_obj = {
		'errno': 'GE010',
		'descr': _('Invalid ID.'),
	}
	return HttpResponseBadRequest(content=json.dumps(err_obj), mimetype='application/json')


def err_GE021():
	err_obj = {
		'errno': 'GE021',
		'descr': _('Decryption error.'),
	}
	return HttpResponseBadRequest(content=json.dumps(err_obj), mimetype='application/json')


def err_GE022():
	err_obj = {
		'errno': 'GE022',
		'descr': _('Key invalid error.'),
	}
	return HttpResponseBadRequest(content=json.dumps(err_obj), mimetype='application/json')


def err_GE031(form):
	err_obj = {
		'errno': 'GE031',
		'descr': form.errors,
	}
	return HttpResponseBadRequest(content=json.dumps(err_obj), mimetype='application/json')


def err_GE100():
	err_obj = {
		'errno': 'GE100',
		'descr': _('Interface deprecated.'),
	}
	return HttpResponseBadRequest(content=json.dumps(err_obj), mimetype='application/json')


def err_DM002():
	err_obj = {
		'errno': 'DM002',
		'descr': _('Account disabled/inactivated.'),
	}
	return HttpResponseBadRequest(content=json.dumps(err_obj), mimetype='application/json')

def err_DM005():
	err_obj = {
		'errno': 'DM005',
		'descr':  _('Your mobile account is currently not authorized.'),
	}
	return HttpResponseBadRequest(content=json.dumps(err_obj), mimetype='application/json')


def err_DM020():
	err_obj = {
		'errno': 'DM020',
		'descr': _('User type unsupported.'),
	}
	return HttpResponseBadRequest(content=json.dumps(err_obj), 	mimetype='application/json')


def err_IN002():
	err_obj = {
		'errno': 'IN002',
		'descr': _('This email address is already associated with a DoctorCom account.'),
	}
	return HttpResponseBadRequest(content=json.dumps(err_obj), mimetype='application/json')

def err_IN003():
	err_obj = {
		'errno': 'IN003',
		'descr': _('This message can not be found in DoctorCom.'),
	}
	return HttpResponseBadRequest(content=json.dumps(err_obj), mimetype='application/json')

def err_TE005():
	err_obj = {
		'errno': 'TE005',
		'descr': _('Requesting user doesn\'t have a mobile phone number defined.'),
	}
	return HttpResponseBadRequest(content=json.dumps(err_obj), 	mimetype='application/json')


def err_TE006():
	err_obj = {
		'errno': 'TE006',
		'descr': _('Requesting practice doesn\'t have a phone number defined.'),
	}
	return HttpResponseBadRequest(content=json.dumps(err_obj), 	mimetype='application/json')


def err_AM020():
	err_obj = {
		'errno': 'AM020',
		'descr': _('A user with this mobile phone number already exists.'),
	}
	return HttpResponseBadRequest(content=json.dumps(err_obj), 	mimetype='application/json')

