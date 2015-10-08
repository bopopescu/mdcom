# -*- coding: utf-8 -*-

'''
Created on 2012-10-19

@author: mwang
'''

from django.utils.translation import ugettext as _

# manage errors information.
ERROR_LIB = {
	'GE002': _('HTTP GET used when only POST is supported for this path.'),
	'GE010': _('Invalid ID.'),
	'GE021': _('Decryption error.'),
	'GE022': _('Key invalid error.'),
#	'GE031': '', # form errors

	'GE050': _('HTTP request header MDCOM_API_KEY missing.'),
	'GE051': _('MDCOM_API_KEY is invalid.'),
	'GE052': _('HTTP request header MDCOM_USER_UUID missing.'),
	'GE053': _('MDCOM_USER_UUID is an invalid uuid.'),
	'GE054': _('You can not access DoctorCom from this IP.'),

	'GE100': _('Interface deprecated.'),

	'DM002': _('Account disabled/inactivated.'),
	'DM020': _('User type unsupported.'),

	'IN002': _('This email address is already associated with a DoctorCom account.'),

	'TE002': _('Requested user doesn\'t have a pager.'),
	'TE003': _('Called number doesn\'t exist.'),
	'TE005': _('Requesting user doesn\'t have a mobile phone number defined.'),
	'TE006': _('Requesting practice doesn\'t have a phone number defined.'),

	'AM010': _('Invalid forwarding selection.'),
	'AM020': _('A user with this mobile phone number already exists.'),
	'MS002': _("Thank you for your interest in sharing files with DoctorCom's secure system." \
					+ "This share is compliments of DoctorCom and your file has been sent to the intended party." \
					+ "However, to have full access you'll need a subscription for only $25/month."),

	# 500 error
	'SYS500': '',
}