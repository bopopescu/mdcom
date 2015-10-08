# -*- coding: utf-8 -*-
'''
Created on 2012-10-12

@author: mwang
'''
from MHLogin.api.v1.business_messaging import getReceivedMessagesLogic, \
	getSentMessagesLogic, getMessageLogic, deleteMessageLogic, deleteMessagesLogic, \
	getAttachmentLogic, composeMessageLogic, getReferPDFLogic, updateReferLogic, \
	markMessageLogic, composeReferLogic
from MHLogin.api.v1.decorators import APIAuthentication


@APIAuthentication
def getReceivedMessages(request, return_python=False):
	return getReceivedMessagesLogic(request, return_python=False)


@APIAuthentication
def getSentMessages(request, return_python=False):
	return getSentMessagesLogic(request, return_python=False)


@APIAuthentication
def getMessage(request, message_id):
	return getMessageLogic(request, message_id)


@APIAuthentication
def deleteMessage(request, message_id):
	return deleteMessageLogic(request, message_id)


@APIAuthentication
def deleteMessages(request):
	return deleteMessagesLogic(request)


@APIAuthentication
def getAttachment(request, message_id, attachment_id):
	return getAttachmentLogic(request, message_id, attachment_id)


@APIAuthentication
def composeMessage(request):
	return composeMessageLogic(request)


@APIAuthentication
def composeADS(request):
	return composeMessageLogic(request, recipients_together=False)


@APIAuthentication
def composeRefer(request):
	return composeReferLogic(request)


@APIAuthentication
def getReferPDF(request, refer_id):
	return getReferPDFLogic(request, refer_id)


@APIAuthentication
def updateRefer(request, refer_id):
	return updateReferLogic(request, refer_id)


@APIAuthentication
def markMessageRead(request):
	return markMessageLogic(request, read_flag=True)


@APIAuthentication
def markMessageUnread(request):
	return markMessageLogic(request, read_flag=False)
