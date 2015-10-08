# -*- coding: utf-8 -*-
"""
An errors library for all error codes in section A.1 of the Interface Document.
"""

from MHLogin.api.v1.utils import HttpJSONErrorResponse, HttpJSONServerErrorResponse

def err_GE002():
	return HttpJSONErrorResponse(errno='GE002')

def err_GE010():
	return HttpJSONErrorResponse(errno='GE010')

def err_GE021():
	return HttpJSONErrorResponse(errno='GE021')

def err_GE022():
	return HttpJSONErrorResponse(errno='GE022')

def err_GE031(form):
	return HttpJSONErrorResponse(form=form)

def err_GE100():
	return HttpJSONErrorResponse(errno='GE100')

def err_DM002():
	return HttpJSONErrorResponse(errno='DM002')

def err_DM020():
	return HttpJSONErrorResponse(errno='DM020')

def err_IN002():
	return HttpJSONErrorResponse(errno='IN002')

def err_TE002():
	return HttpJSONErrorResponse(errno='TE002')

def err_TE003():
	return HttpJSONErrorResponse(errno='TE003')

def err_TE005():
	return HttpJSONErrorResponse(errno='TE005')

def err_TE006():
	return HttpJSONErrorResponse(errno='TE006')

def err_AM020():
	return HttpJSONErrorResponse(errno='AM020')

def _err_AM010():
	return HttpJSONErrorResponse(errno='AM010')

def err_SYS500(message):
	return HttpJSONServerErrorResponse(message=message)
