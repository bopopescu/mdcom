#-*- coding: utf-8 -*-
'''
Created on 2013-4-5

@author: wxin
'''
import time
import thread

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _

from MHLogin.MHLPractices.models import Pending_Org_Association, \
	Log_Org_Association
from MHLogin.MHLUsers.utils import get_all_practice_managers,get_fullname
from MHLogin.MHLOrganization.utils import notify_org_users_tab_chanaged
from MHLogin.utils.mh_logging import get_standard_logger

logger = get_standard_logger('%s/MHLOrganization/utils_org_member.log' % (settings.LOGGING_ROOT),
							'MHLOrganization.utils_org_member', settings.LOGGING_LEVEL)

def send_mail_to_org_manager(org, subject, body_template_file, body_context):
	mgrs = get_all_practice_managers(org)
	for mgr in mgrs:
		body_context.update({
				'manager_fullname': get_fullname(mgr.user)
			})
		body = render_to_string(body_template_file, body_context)
		send_mail(
				subject,
				body,
				settings.SERVER_EMAIL,
				[mgr.user.email],
				fail_silently=False
			)

def send_invite_mail_to_org_manager(pending):
	sender = pending.sender
	from_org = pending.from_practicelocation
	to_org = pending.to_practicelocation
	from_org_type = from_org.organization_type.name if from_org.organization_type else ""
	subject = _('DoctorCom: Invitation To Join %s') % str(from_org_type)
	body_template_file = "MHLOrganization/MemberOrg/invite_email_send.html"
	body_context = {
			'sender_fullname':get_fullname(sender),
			"to_org_type": to_org.organization_type.name if to_org.organization_type else "",
			"to_org_name": to_org.practice_name,
			"from_org_type": from_org_type,
			"from_org_name": from_org.practice_name
		}
	send_mail_to_org_manager(to_org, subject, body_template_file, body_context)

def send_cancel_mail_to_org_manager(pending):
	sender = pending.sender
	from_org = pending.from_practicelocation
	to_org = pending.to_practicelocation
	from_org_type = from_org.organization_type.name if from_org.organization_type else ""
	subject = _('DoctorCom: Invitation To Join %s Withdrawn') % (from_org_type)
	body_template_file = "MHLOrganization/MemberOrg/invite_email_cancel.html"
	body_context = {
			"from_org_type": from_org.organization_type.name,
			"from_org_name":from_org.practice_name
		}
	send_mail_to_org_manager(to_org, subject, body_template_file, body_context)
	
def accept_member_org_invite(mhluser_id, pending_id):
	pending = Pending_Org_Association.objects.filter(id=pending_id)
	ret_data = {}
	if pending and len(pending)>0:
		pending = pending[0]
		pending_log = Log_Org_Association(
				association_id = pending.id,
				from_practicelocation_id = pending.from_practicelocation_id,
				to_practicelocation_id=pending.to_practicelocation_id,
				sender_id=pending.sender_id,
				action_user_id = mhluser_id,
				action = 'ACC',
				create_time = time.time()
			)
		pending_log.save()
		pending.from_practicelocation.save_member_org(member_org=pending.to_practicelocation)
		pending.delete()
		from_practicelocation_name = pending.from_practicelocation.practice_name
		to_practicelocation_name = pending.to_practicelocation.practice_name

		# send notification to related users
		thread.start_new_thread(notify_org_users_tab_chanaged,\
			(pending.to_practicelocation.id,), {"include_self_tree": True})

		ret_data = {
				"success": True,
				"message": _('Your organization %(to_practicelocation_name)s '
	'have successfully joined %(from_practicelocation_name)s organization.')\
							%{
								"to_practicelocation_name": to_practicelocation_name,
								"from_practicelocation_name": from_practicelocation_name
							}
			}
		logger.debug("return: %s"%str(ret_data))
	else:
		ret_data = {
				"success": False,
				"message": _('Your organization already has been added to the '
				'organization or you declined the invitation from other client.')
			}
	logger.debug("return: %s"%str(ret_data))
	return ret_data

def rejected_member_org_invite(mhluser_id, fullname, pending_id):
	pending = Pending_Org_Association.objects.filter(id=pending_id)
	if pending and len(pending) > 0:
		pending = pending[0]
		pending_log = Log_Org_Association(
				association_id = pending.id,
				from_practicelocation_id = pending.from_practicelocation_id,
				to_practicelocation_id=pending.to_practicelocation_id,
				sender_id=pending.sender_id,
				action_user_id = mhluser_id,
				action = 'REJ',
				create_time = time.time()
			)
		pending_log.save()
		pending.delete()

		from_org = pending.from_practicelocation
		to_org = pending.to_practicelocation
		from_org_type = from_org.organization_type.name if from_org.organization_type else ""
		subject = _('DoctorCom:	Request	To Join %s Rejected') % (from_org_type)
		body_template_file = "MHLOrganization/MemberOrg/invite_email_reject.html"
		body_context = {
				'manager_fullname':fullname,
				'sender_fullname':get_fullname(pending.sender),
				'to_org_name': to_org.practice_name,
				'from_org_name': from_org.practice_name,
			}

		body = render_to_string(body_template_file, body_context)
		send_mail(
				subject,
				body,
				settings.SERVER_EMAIL,
				[pending.sender.email],
				fail_silently=False
			)
		to_practicelocation_name = pending.to_practicelocation.practice_name

		return {
				"success": True,
				"message": _('You have declined %s\'s invitation.')\
					%(to_practicelocation_name)
			}
	else:
		return {
				"success": False,
				"message": _('Your organization already has been added to the '
				'organization or you declined the invitation from other client.')
			}
