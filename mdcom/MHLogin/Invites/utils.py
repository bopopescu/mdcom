import datetime
import random
import thread

from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _

from MHLogin.MHLCallGroups.models import CallGroupMember
from MHLogin.MHLPractices.models import Pending_Association, Log_Association, \
	Pending_Org_Association
from MHLogin.MHLPractices.utils import mail_managers
from MHLogin.MHLUsers.models import Provider
from MHLogin.MHLUsers.utils import get_managed_practice, get_practice_org,\
	get_fullname
from MHLogin.utils import ImageHelper
from MHLogin.utils.constants import RESERVED_ORGANIZATION_TYPE_ID_PRACTICE, \
	USER_TYPE_OFFICE_MANAGER
from MHLogin.MHLCallGroups.Scheduler.views_multicallgroup import get_call_group_penddings
from MHLogin.apps.smartphone.v1.utils import notify_user_tab_changed

def newInviteCode():
	chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ345789'
	return ''.join([random.choice(chars) for x in range(8)])


def getUserInvitationPendings(mhluser, user_type, all_in_one=True):
	"""
	Get user's all invitation pendings list.

	:param mhluser: is an instance of MHLUser.
	:parm user_type: is user's type.
		About the number of user_type, please read USER_TYPE_CHOICES in the MHLogin.utils.contants.py 
	:parm all_in_one: use only one key to store all types of pendings, or not.

		The items in the list like following structure:
			{
				"pending_id": pending id,
				"type": pending type,
				"content": {
					# some custom data, related pending type.
				},
			}
	"""
	# get organization pendding list
	org_invitations = []
	pend_org = Pending_Association.objects.filter(to_user=mhluser).exclude(
		practice_location__organization_type__id=RESERVED_ORGANIZATION_TYPE_ID_PRACTICE).\
			order_by('created_time')
	for p in pend_org:
		from_user = p.from_user
		org = p.practice_location
		p = {
				"pending_id": p.pk,
				"type": "Org",
				"content": {
					"invitation_sender": get_fullname(from_user),
					"org_logo": ImageHelper.get_image_by_type(org.practice_photo, 
						size='Large', type='', resize_type='img_size_logo'),
					"org_name": org.practice_name,
					'role': 'provider'
				},
			}
		org_invitations.append(p)

	# get practice pendding list
	practice_invitations = []
	if 1 == user_type:
		pend_practice = Pending_Association.objects.filter(to_user=mhluser, 
			practice_location__organization_type__id=RESERVED_ORGANIZATION_TYPE_ID_PRACTICE).\
				order_by('created_time')
		for p in pend_practice:
			from_user = p.from_user
			practice = p.practice_location
			p = {
					"pending_id": p.pk,
					"type": "Practice",
					"content": {
						"invitation_sender": get_fullname(from_user),
						"role": 'provider',
						"practice_logo": ImageHelper.get_image_by_type(practice.practice_photo, 
							size='Large', type='', resize_type='img_size_logo'),
						"practice_name": practice.practice_name,
						'practice_addr1': practice.practice_address1,
						'practice_addr2': practice.practice_address2,
						'practice_zip': practice.practice_zip,
						'practice_id': practice.id,
						'practice_city': practice.practice_city,
						'practice_state': practice.practice_state,
					},
				}
			practice_invitations.append(p)

	if all_in_one:
		org_invitations.extend(practice_invitations)
		return {'invitations': org_invitations}
	else:
		return {
				'org_invitationst': org_invitations,
				'practice_invitations': practice_invitations
			}


def acceptToJoinPractice(mhluser, pending_id, provider=None):
	"""
	Accept to join Practice.

	:param mhluser: is an instance of MHLUser.
	:parm pending_id: invitation pending's id.
	:parm provider: is an instance of Provider.
	"""
	try:
		association = Pending_Association.objects.get(pk=pending_id)
		practice = association.practice_location
	
		if not provider:
			provider = get_object_or_404(Provider, user=mhluser)
	
		provider.practices.add(practice)
		current_practice = provider.current_practice
		#update current practice if needed
		new_current_practice = get_practice_org(practice)
		if (current_practice == None and new_current_practice):
			provider.current_practice = new_current_practice
			provider.save()

		#remove association record
		log_association = Log_Association()
		log_association.association_id = association.id
		log_association.from_user_id = association.from_user_id
		log_association.to_user_id = association.to_user_id
		log_association.practice_location_id = association.practice_location.id
		log_association.action_user_id = mhluser.id
		log_association.action = 'ACC'
		log_association.created_time = datetime.datetime.now()
	
		log_association.save()
	
		association.delete()
	
		# Add the provider to the call group.
		if (not CallGroupMember.objects.filter(
						call_group=practice.call_group, member=provider).exists()):
			CallGroupMember(
					call_group=practice.call_group,
					member=provider,
					alt_provider=1).save()

		# send notification to related users
		thread.start_new_thread(notify_user_tab_changed, (mhluser.id,))

		return {
				"success": True,
				"message": _('You have successfully joined %s organization.')\
							%(practice.practice_name)
			}
	except Pending_Association.DoesNotExist:
		return {
				"success": False,
				"message": _("You already have been added to the organization"
					" or your invitation has been canceled from other client.")
			}

def rejectToJoinPractice(mhluser, pending_id):
	"""
	Reject to join Practice.

	:param mhluser: is an instance of MHLUser.
	:parm pending_id: invitation pending's id.
	"""
	try:
		association = Pending_Association.objects.get(to_user=mhluser, pk=pending_id)
		practice = association.practice_location
	
		log_association = Log_Association()
	
		log_association.association_id = association.id
		log_association.from_user_id = association.from_user_id
		log_association.to_user_id = association.to_user_id
		log_association.practice_location_id = association.practice_location.id
		log_association.action_user_id = mhluser.id
		log_association.action = 'REJ'
		log_association.created_time = datetime.datetime.now()
	
		log_association.save()
		association.delete()
	
		mail_managers(practice,
						_('DoctorCom: Request To Join Practice Rejected'),
						"""Dear Manager,

We're sorry, but {{provider_fullname}} turned down your request to join {{practice_name}}.

Best,
DoctorCom Staff
""",
	
					practice_name=practice.practice_name,
					provider_fullname=get_fullname(mhluser),
					)
		return {
				"success": True,
				"message": _('You have declined %s\'s invitation.')\
						%(practice.practice_name)
			}
	except Pending_Association.DoesNotExist:
		return {
				"success": False,
				"message": _("You already have been added to the organization"
					" or your invitation has been canceled from other client.")
			}

def getInvitationPendings(request_host, mhluser, role_user, user_type):
	user_type = int(user_type)
	invitations = []
	pend_practice = Pending_Association.objects.filter(to_user=mhluser).order_by('created_time')
	for p in pend_practice:
		from_user = p.from_user
		practice = p.practice_location
		logo_path = ImageHelper.get_image_by_type(practice.practice_photo, 
			size='Large', type='', resize_type='img_size_logo')
		if not logo_path == '':
			logo_path = '%s%s' % (request_host, logo_path)
		org_name = practice.practice_name
		member_invitations_content_context = {
			"invitation_sender": get_fullname(from_user),
			"role": 'provider',
			'org_type': practice.organization_type.name,
			"org_logo": logo_path,
			"org_name": org_name,
			'org_addr1': practice.practice_address1,
			'org_addr2': practice.practice_address2,
			'org_zip': practice.practice_zip,
			'org_id': practice.id,
			'org_city': practice.practice_city,
			'org_state': practice.practice_state,
		}
		member_invitations_content = render_to_string(
			'MHLOrganization/member_invitation_for_app.html', 
				member_invitations_content_context)
		p = {
				"pending_id": p.pk,
				"type": "1",
				"content": member_invitations_content
			}
		invitations.append(p)

	if user_type == USER_TYPE_OFFICE_MANAGER:
		managed_organizations = get_managed_practice(role_user)
		org_ids = [org.id for org in managed_organizations]
		pendings = Pending_Org_Association.objects.filter(
			to_practicelocation__id__in=org_ids).select_related('from_practicelocation', 
				'to_practicelocation')

		for p in pendings:
			logo_path = ImageHelper.get_image_by_type(
				p.from_practicelocation.practice_photo, "Middle", 'Practice', 'img_size_logo')
			if not logo_path == '':
				logo_path = '%s%s' % (request_host, logo_path)
			from_practicelocation_name = p.from_practicelocation.practice_name
			to_practicelocation_name = p.to_practicelocation.practice_name
			member_org_invitations_content_context = {
				'pending_id': p.id,
				'sender_name': get_fullname(p.sender),
				'from_practicelocation_logo': logo_path,
				'from_practicelocatin_type': p.from_practicelocation.organization_type.name,
				'from_practicelocation_name': from_practicelocation_name,
				'to_practicelocation_name': to_practicelocation_name,
				'to_practicelocatin_type': p.to_practicelocation.organization_type.name,
			}
			member_org_invitations_content = render_to_string(
				'MHLOrganization/member_org_invitation_for_app.html', 
					member_org_invitations_content_context)
			p = {
				"pending_id": p.pk,
				"type": "2",
				"content": member_org_invitations_content
			}
			invitations.append(p)
	call_group_penddings = []
	for p in get_call_group_penddings(mhluser.id):
		p_content = render_to_string(
				'App/call_group_invitation_for_app.html', p)
		call_group_penddings.append({
			"pending_id": p['id'],
			"type": "3",
			"content": p_content
		})

	return {'invitations': invitations,\
			'call_group_penddings': call_group_penddings}
