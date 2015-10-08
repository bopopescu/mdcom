#-*- coding: utf-8 -*-
'''
Created on 2013-3-22

@author: wxin
'''

from django.conf import settings
from django.db.models.query_utils import Q
from django.utils.safestring import mark_safe

from MHLogin.MHLOrganization.utils_org_type import can_we_create_this_type_under_that_type,\
			get_sub_types_by_typeid, get_parent_types_by_typeid
from MHLogin.MHLPractices.models import OrganizationRelationship, PracticeLocation, Pending_Association, \
	OrganizationSetting, OrganizationMemberOrgs, OrganizationType,\
	OrganizationTypeSubs
from MHLogin.MHLUsers.models import Administrator, OfficeStaff, Office_Manager, Provider,\
	Physician, NP_PA
from MHLogin.MHLUsers.utils import get_managed_practice,get_fullname
from MHLogin.utils import ImageHelper
from MHLogin.utils.constants import RESERVED_ORGANIZATION_TYPE_ID_SYSTEM, \
	RESERVED_ORGANIZATION_TYPE_ID_PRACTICE,\
	RESERVED_ORGANIZATION_ID_SYSTEM, DEFAULT_ORGANIZATION_TYPE_NAME,\
	RESERVED_ORGANIZATION_TYPE_ID_HOSPITAL, USER_TYPE_DOCTOR, USER_TYPE_NPPA,\
	USER_TYPE_MEDICAL_STUDENT, USER_TYPE_OFFICE_STAFF, USER_TYPE_OFFICE_MANAGER
from MHLogin.apps.smartphone.v1.utils import notify_user_tab_changed
from MHLogin.utils.mh_logging import get_standard_logger
from MHLogin.utils.latlon2mile import get_distance

logger = get_standard_logger('%s/MHLOrganization/utils.log' % (settings.LOGGING_ROOT),
							'MHLOrganization.utils', settings.LOGGING_LEVEL)

def get_orgs_I_can_manage(mhluser_id, parent_id=None, org_id_excluded=None,\
			org_type_id=None, clear_no_type_org=None, org_name=None, root_id=None):
	#todo this function need to be refactored
	""" Get organization relation I can managed.
	:param mhluser_id: is an instance of MHLUser's id
	:param parent_id: is org's id
	:param org_id_excluded: exclude this organization and its descent organizations.
	:param clear_no_type_org:  if True, clear the organization who don't have sub types
	:param org_type_id: is org's type id
	:param org_name: now it's org's name
	:param format: the format of the result
	:returns: list of organization relation
	"""
	is_public = None
	if (Administrator.objects.filter(user__id=mhluser_id).exists()):
		q_f = Q()
		if org_id_excluded:
			org_ids_excluded = append_all_descent_organizations_ids([org_id_excluded])
			q_f = q_f & ~Q(organization__id__in=org_ids_excluded)
		org_relations = OrganizationRelationship.active_objects.filter(q_f)\
			.select_related('organization','parent')
	else:
		is_public = True
		office_staffs = OfficeStaff.objects.filter(user__id=mhluser_id)
		if len(office_staffs) == 1:
			office_staff = office_staffs[0]
		else:
			return []
		# get_managed_practice can only get the root managed practices
		managed_organizations = get_managed_practice(office_staff)
		org_ids = [org.id for org in managed_organizations]
		org_ids = append_all_descent_organizations_ids(org_ids, org_id_excluded=org_id_excluded)
		if org_ids:
			org_relations = OrganizationRelationship.active_objects.filter(\
				organization__id__in=org_ids).select_related('organization','parent')
		else:
			return []

	q_f = Q()
	if parent_id:
		q_f = q_f & Q(parent__id=parent_id)

	if org_type_id:
		q_f = q_f & Q(organization__organization_type__id=org_type_id)

	if clear_no_type_org:
		org_type_ids = OrganizationTypeSubs.objects.all().distinct()\
			.values_list("from_organizationtype__id", flat=True)

		type_ids_child_allow = None
		if org_id_excluded:
			try:
				org = PracticeLocation.objects.get(id=org_id_excluded)
				org_types = get_parent_types_by_typeid(org.organization_type.id, is_public=is_public)
				type_ids_child_allow = [org_type.id for org_type in org_types]
			except PracticeLocation.DoesNotExist:
				pass
		if type_ids_child_allow is not None:
			org_type_ids = list(set(org_type_ids) & set(type_ids_child_allow))

		if org_type_ids:
			q_f = q_f & Q(organization__organization_type__id__in=org_type_ids)

	if org_name:
		q_f = q_f & Q(organization__practice_name__icontains=org_name)

	org_relations = org_relations.filter(q_f)

	if root_id and root_id != RESERVED_ORGANIZATION_ID_SYSTEM:
		root_ids = get_all_child_org_ids([long(root_id)])
		org_relations = org_relations.filter(organization__pk__in=root_ids)
	
	org_relations = org_relations.order_by('organization__practice_name')
	return org_relations[:settings.MAX_ORG_TREE_NODES]

def append_all_descent_organizations_ids(organizations_ids, org_id_excluded=None):
	#todo this function need to be refactored
	""" append all descent organization ids into organizations_ids list
	:param organizations_ids: parent organization id list
	:returns: organization id list
	"""
	org_ids = []
	for org_id in organizations_ids:
		if org_id_excluded and org_id_excluded == org_id:
			continue
		org_ids.append(org_id)
		organization_ids_tmp = OrganizationRelationship.active_objects.filter(parent__id=org_id).values_list("organization__id", flat=True)
		if organization_ids_tmp:
			org_ids.extend(append_all_descent_organizations_ids(organization_ids_tmp, org_id_excluded=org_id_excluded))
	return set(org_ids)

def can_user_manage_this_org(org_id, mhluser_id):
	""" Check whether the user can manage the organization.
	:param org_id: is org's id
	:param mhluser_id: is MHLUser's id
	ret_data = {
		"can_manage_org": False,
		"Administrator": None,
		"Office_Manager": None,
	}
	"""
	ret_data = {
		"can_manage_org": False,
		"Administrator": None,
		"Office_Manager": None,
	}

	try:
		admin = Administrator.objects.get(user__pk=mhluser_id)
		ret_data["can_manage_org"] = True
		ret_data["Administrator"] = admin
		return ret_data
	except Administrator.DoesNotExist:
		pass

	manageer = get_org_manager_with_user(org_id, mhluser_id)
	ret_data["can_manage_org"] = manageer is not None
	ret_data["Office_Manager"] = manageer
	return ret_data

def get_org_manager_with_user(org_id, user_id):
	""" Get the manager for this org_id with user_id.
	:param org_id: is org's id
	:param user_id: is MHLUser's id
	:returns: an instance of Office_Manager
		Note: if user can manage this organization return manage relationship
			else return None
	"""
	try:
		user = OfficeStaff.objects.get(user__id=user_id)
		org_ids = user.practices.all().values_list("id", flat=True)
		if org_id not in org_ids:
			raise Office_Manager.DoesNotExist
		return Office_Manager.objects.get(user=user, practice__id=org_id)
	except OfficeStaff.DoesNotExist:
		return None
	except Office_Manager.DoesNotExist:
		try:
			org_relation = OrganizationRelationship.active_objects.get(organization__id=org_id)
			if org_relation.parent:
				return get_org_manager_with_user(org_relation.parent.id, user_id)
			else:
				return None
		except OrganizationRelationship.DoesNotExist:
			return None

def can_user_manage_org_module(mhluser_id):
	""" Check whether the user can manage organization module.
	:param mhluser_id: is a mhluser id
	:returns: {
		"can_manage_org": True or False,
		"Administrator": an instance of Administrator,
		"Office_Manager": list of Office_Manager
	}
	"""
	ret_data = {
		"can_manage_org": False,
		"Administrator": None,
		"Office_Manager": None,
	}

	try:
		admin = Administrator.objects.get(user__pk=mhluser_id)
		ret_data["can_manage_org"] = True
		ret_data["Administrator"] = admin
		return ret_data
	except Administrator.DoesNotExist:
		pass

	try:
		staff = OfficeStaff.objects.get(user__pk=mhluser_id)
		org_ids = staff.practices.all().values_list("id", flat=True)
		if org_ids:
			managers = list(Office_Manager.objects.filter(user=staff))
			if managers:
				ret_data["can_manage_org"] = True
				ret_data["Office_Manager"] = managers
	except OfficeStaff.DoesNotExist:
		pass
	return ret_data

def get_possible_types_by_org_id(mhluser_id, org_id=None, parent_org_id=None):
	""" Get possible types for organization.
	:param mhluser_id: is an instance of MHLUser's id
	:param org_id: is org's id
	:param parent_org_id: is parent org's id
	:returns: list(OrganizationType)
	:raise: PracticeLocation.DoesNotExist Exception
	"""

	if not org_id and not parent_org_id:
		raise Exception

	is_public = None
	if not Administrator.objects.filter(user__id=mhluser_id).exists():
		is_public = True

	org_types_f_p = []
	# get possible types from new parent organization
	if parent_org_id:
		new_parent_org = PracticeLocation.objects.get(pk=parent_org_id)
		org_types_f_p = get_sub_types_by_typeid(
				new_parent_org.organization_type.id, is_public=is_public)

	if not org_id:
		return org_types_f_p

	# get possible types from old parent organization
	if not parent_org_id:
		org_rs = OrganizationRelationship.active_objects.filter(organization__id=org_id).select_related('parent')
		if org_rs and org_rs[0]:
			org_parent = org_rs[0].parent
			if not org_parent:
				org_type = OrganizationType.objects.get(id=RESERVED_ORGANIZATION_TYPE_ID_SYSTEM)
				org_types_f_p.append(org_type)
			else:
				if org_parent.organization_type:
					org_types_f_p = get_sub_types_by_typeid(org_parent.organization_type.id, is_public=is_public)

	# get possible types from child organization
	org_rs = OrganizationRelationship.active_objects.filter(parent__id=org_id).select_related('organization')
	if org_rs:
		org_types_f_p = set(org_types_f_p)
		for org_r in org_rs:
			child_type = org_r.organization.organization_type.id
			new_org_types_f_c = get_parent_types_by_typeid(child_type, is_public=is_public)
			org_types_f_p = org_types_f_p & set(new_org_types_f_c)
		return list(org_types_f_p)
	# if no child organization, then org_types_f_c is equal org_types_f_p
	else:
		return org_types_f_p


#Todo UT
def which_orgs_contain_this_user(user_id, type_id=None, in_tab=True, have_luxury_logo=None,\
			exclude_type_ids=None, exclude_org_ids=None, include_ancestor=False,\
			include_soft_link=True):
	""" Get organizations that contain this user.
	:param user_id: is MHLUser's id
	:param type_id: org type id
	:param in_tab: Ture or False
			if in_tab is True, function will filter the orgs can be displayed in the tab.
	:param have_luxury_logo: Ture or False or None
			if have_luxury_logo is True, function will filter the orgs can have luxury logo.
			if have_luxury_logo is None, function will don't add this filter.
	:param exclude_type_ids: org type id, exclude orgs whose type id is/in exclude_type_ids.
			Note: exclude_type_ids can'b integer or list of integer
	:param exclude_org_ids: org id, exclude orgs whose id is/in exclude_org_ids.
			Note: exclude_org_ids can'b integer or list of integer
	:param include_ancestor: whether include ancestor organization

	:returns: org list
	:raise OfficeStaff.DoesNotExist
	"""
	try:
		user = Provider.objects.get(user__id=user_id)
	except Provider.DoesNotExist:
		try:
			user = OfficeStaff.objects.get(user__id=user_id)
		except OfficeStaff.DoesNotExist:
			return []

	org_ids = user.practices.all().values_list("id", flat=True)
	org_ids = list(org_ids)

	full_org_ids = org_ids

	if include_soft_link or include_ancestor:
		ancestor_org_ids = get_all_parent_org_ids(org_ids)
		if include_soft_link:
			softlink_org_ids = list(OrganizationMemberOrgs.objects.filter(\
				to_practicelocation__pk__in=ancestor_org_ids)\
				.values_list("from_practicelocation__id", flat=True))
			full_org_ids += softlink_org_ids
	
		if include_ancestor:
			full_org_ids += ancestor_org_ids

	full_org_ids = list(set(full_org_ids))

	q_f = Q(id__in=full_org_ids)
	if type_id:
		q_f = q_f & Q(organization_type__id = type_id)

	setting_ids = None
	if in_tab or have_luxury_logo:
		q_f_setting = Q(delete_flag=False)
		if in_tab:
			q_f_setting = q_f_setting & Q(display_in_contact_list_tab=True)
		if have_luxury_logo:
			q_f_setting = q_f_setting & Q(can_have_luxury_logo=True)
		setting_ids = OrganizationSetting.objects.filter(q_f_setting).values_list("id", flat=True)
		if not setting_ids:
			return []

	if setting_ids:
		q_f = q_f & Q(Q(organization_setting__id__in = setting_ids)
					| Q(Q(Q(organization_setting__delete_flag = True)|Q(organization_setting=None)) 
						& Q(organization_type__organization_setting__id__in = setting_ids)))

	orgs = PracticeLocation.objects.filter(q_f).order_by('id')
	if have_luxury_logo:
		orgs = orgs.exclude(practice_photo=None).exclude(practice_photo='')

	if exclude_type_ids:
		if isinstance(exclude_type_ids, list):
			orgs = orgs.exclude(organization_type__id__in=exclude_type_ids)
		else:
			orgs = orgs.exclude(organization_type__id=exclude_type_ids)

	if exclude_org_ids:
		if isinstance(exclude_org_ids, list):
			orgs = orgs.exclude(id__in=exclude_org_ids)
		else:
			orgs = orgs.exclude(id=exclude_org_ids)

	return list(orgs)

#Todo UT
def get_prefer_logo(mhluser_id, current_practice=None):
	""" Get user's prefer logo.
	:param mhluser_id: is id of MHLUser
	:returns: logo url string
	"""

	prefer_logo = ''
	custom_logos = get_custom_logos(mhluser_id, current_practice=current_practice)
	if custom_logos and len(custom_logos) > 0:
		prefer_logo = custom_logos[0]["logo"]
	return prefer_logo

#Todo UT
def get_custom_logos(mhluser_id, current_practice=None):
	""" Get user's custom logos.
	:param mhluser_id: is id of MHLUser
	:param current_practice: is an instance of PracticeLocation
	:returns: list of logo url string
	"""

	orgs = which_orgs_contain_this_user(mhluser_id, in_tab=None, have_luxury_logo=True,\
						exclude_type_ids=RESERVED_ORGANIZATION_TYPE_ID_SYSTEM, \
						include_ancestor=True)

	if not orgs:
		orgs = []

	current_practice_in = False
	custom_logos = []
	org_ids = []
	if orgs:
		for org in orgs:
			if org.id not in org_ids:
				logo = get_org_logo(org)
				if logo and not logo == '/media/images/photos/hospital_icon.jpg':
					custom_logos.append({
							'logo': logo
						})
					org_ids.append(org.id)
					if current_practice and current_practice.id == org.id:
						current_practice_in = True

	if not current_practice_in and current_practice:
		logo = get_org_logo(current_practice)
		if logo and not logo == '/media/images/photos/hospital_icon.jpg':
			custom_logos.append({
						'logo': logo
					})

	return custom_logos

#Todo UT
def get_org_logo(org):
	""" Get org's logo.
	:param org: an instance of PracticeLocation
	:returns: logo url string
	"""
	if org and isinstance(org, PracticeLocation):
		logo = ImageHelper.get_image_by_type(org.practice_photo, size='Large',\
				type='Practice', resize_type='img_size_logo')
	return logo


def get_org_members(org_id, user_name=None, user_email=None):
	""" Get organization's members.
	:param org_id: is org's id
	:param user_name: filter these member whose first_name/last_name contains user_name 
	:param user_email: filter these member whose email contains user_email 
	:returns: user list(provider or staff)
	"""
	providers = get_org_providers(org_id, user_name=user_name, user_email=user_email)
	staffs = get_org_staff(org_id, user_name=user_name, user_email=user_email)

	providers.extend(staffs)
	return providers

def get_org_staff(org_id, user_name=None, user_email=None):
	""" Get organization's staff.
	:param org_id: is org's id
	:param user_name: filter these staff whose first_name/last_name contains user_name 
	:param user_email: filter these staff whose email contains user_email 
	:returns: user list(staff)
	"""

	q_f = Q(practices__id=org_id)
	if user_name:
		q_f = q_f & Q(Q(user__first_name__icontains=user_name) | Q(user__last_name__icontains=user_name))

	if user_email:
		q_f = q_f & Q(user__email__icontains=user_email)

	return list(OfficeStaff.objects.filter(q_f))

def get_org_all_staff(org_id):
	""" Get all organization's staff.
	:param org_id: is org's id
	:returns: user list(staff)
	"""
	return get_org_staff(org_id)

def get_org_providers(org_id, user_name=None, user_email=None):
	""" Get organization's providers.
	:param org_id: is org's id
	:param user_name: filter these providers whose first_name/last_name contains user_name 
	:param user_email: filter these providers whose email contains user_email 
	:returns: user list(provider)
	"""
	q_f = Q(practices__id=org_id)
	if user_name:
		q_f = q_f & Q(Q(user__first_name__icontains=user_name) | Q(user__last_name__icontains=user_name))

	if user_email:
		q_f = q_f & Q(user__email__icontains=user_email)

	return list(Provider.objects.filter(q_f))


def get_org_all_providers(org_id):
	""" Get all organization's providers.
	:param org_id: is org's id
	:returns: user list(provider)
	"""
	return get_org_providers(org_id)

def is_user_in_this_org(org_id, user_id=None, user_name=None, user_email=None):
	""" Check the user whether in this organization
		At least, one of user_id, user_name, user_email is not None. 
	:param org_id: is org's id
	:param user_id: is mhluser's id
	:param user_name: is user's name(first_name or last_name)
	:param user_email: is user's user_email
	:returns: True or False 
	"""
	if user_id is None and user_name is None and user_email is None:
		return False

	q_f = Q(practices__id=org_id)

	if user_id:
		q_f = q_f & Q(user__id=user_id)

	if user_name:
		q_f = q_f & Q(Q(user__first_name__icontains=user_name) | Q(user__last_name__icontains=user_name))

	if user_email:
		q_f = q_f & Q(user__email__icontains=user_email)

	return Provider.objects.filter(q_f).exists() \
		or OfficeStaff.objects.filter(q_f).exists()

def has_sent_org_invitation_to_this_user(org_id, user_id):
	""" Check whether the organization has sent an invitation to this user
	:param org_id: is org's id
	:param user_id: is mhluser's id
	:returns: True or False 
	"""

	return Pending_Association.objects.filter(to_user__id=user_id, practice_location__id=org_id).exists()

def get_member_orgs(org_id, org_type_id=None, org_name=None):
	""" Get organization's member organizations
	:param org_id: is org's id
	:param org_type_id: is organization's type id
	:param org_name: is organization's name
	:returns: query_set of OrganizationMemberOrgs
	:raise PracticeLocation.DoesNotExist
	"""

	qf = Q(from_practicelocation__pk=org_id)
	if org_name:
		qf = qf & Q(to_practicelocation__practice_name__icontains=org_name)

	if org_type_id:
		qf = qf & Q(to_practicelocation__organization_type__id=org_type_id)

	member_orgs = OrganizationMemberOrgs.objects.filter(qf).select_related('to_practicelocation')
	member_orgs = [
			org.to_practicelocation
		for org in member_orgs]

	return member_orgs

def save_member_org(org_id, member_org, billing_flag=None):
	""" Save organization relationship
	:param org_id: is org's id
	:param member_org: is an instance of PracticeLocation
	:raise PracticeLocation.DoesNotExist
	"""
	org = PracticeLocation.objects.get(id=org_id)
	org.save_member_org(member_org=member_org, billing_flag=None)

def get_org_sub_types(org_id, is_public=True):
	""" Get organization's sub types that can save for this organization.
	:param org_id: is org's id
	:returns: list(org type)
	:raise PracticeLocation.DoesNotExist
	"""
	org = PracticeLocation.objects.get(id=org_id)
	q_f = Q()
	if is_public:
		q_f = q_f & Q(is_public=True)
	return list(org.organization_type.subs.filter(q_f))

def can_we_move_this_org_under_that_org(sub_org, parent_org):
	""" Check this of organization can be created under that organization
	:param sub_org: sub organization
	:param parent_org: parent organization
	:returns: True or False
	"""
	if not can_we_create_this_type_under_that_type(sub_org.organization_type.id, \
			parent_org.organization_type.id):
		return False

	can = True
	org = parent_org
	while(org is not None):
		try:
			_org_relation = OrganizationRelationship.active_objects.get(organization=org)
			if _org_relation and _org_relation.parent:
				org = _org_relation.parent
				if org.id == sub_org.id:
					can = False
					break
			else:
				break
		except OrganizationRelationship.DoesNotExist:
			break
	return can

#Todo UT
def can_we_move_this_org_under_that_org_byid(mhluser_id, sub_org_id, parent_org_id):
	""" Check this of organization can be created under that organization
	:param sub_org_id: sub organization id
	:param parent_org_id: parent organization id
	:returns: True or False
	:raise PracticeLocation.DoesNotExist
	"""
	types = get_possible_types_by_org_id(mhluser_id, org_id=sub_org_id, parent_org_id=parent_org_id)
	return types and len(types)>0

#Todo UT
def get_all_related_org_ids_below_this_org(org_ids):
	""" Get all related organizations below this organization of the org_id
	:param org_ids: organization id or id's list
	:returns: {
		"self_tree_ids": org id set in the current organization tree.
		"member_org_tree_ids": org id set in each member organization tree of current organization.
		"all_tree_ids": union of self_tree_ids and member_org_tree_ids
	}
	"""
	if not org_ids:
		return {
			"self_tree_ids": set(),
			"member_org_tree_ids": set(),
			"all_tree_ids": set()
		}

	if not isinstance(org_ids, list):
		org_ids = [org_ids]
	qf = Q(from_practicelocation__pk__in=org_ids)
	member_org_ids = list(OrganizationMemberOrgs.objects.filter(qf).values_list('to_practicelocation__id', flat=True))
	if not member_org_ids:
		member_org_ids = []

	member_org_tree_ids = append_all_descent_organizations_ids(member_org_ids)
	self_tree_ids = append_all_descent_organizations_ids(org_ids)
	all_tree_ids = member_org_tree_ids | self_tree_ids

	ret_data = {
		"self_tree_ids": self_tree_ids,
		"member_org_tree_ids": member_org_tree_ids,
		"all_tree_ids": all_tree_ids
	}
	logger.debug("All related organization ids: %s"%str(ret_data))
	return ret_data

def format_tree_data(org_rs, is_flat=False):
	"""Format Tree Data: format organization relation ship as a tree.
	:param org_rs: organization relations
	:param is_flat: If we need to format tree to flat.
	"""
	org_rs_tree_data =  []
	for org in org_rs:
		is_leaf = True
		if org.organization and org.organization.organization_type\
			and org.organization.organization_type.subs.all():
			is_leaf = False
		org_rs_tree_data.append({
			'data': org.organization.practice_name,
			'treedepth': 0,
			'id': org.organization.id,
			'parent_id': org.parent.id if org.parent else None,
			'attr':{
				'id': org.organization.id,
				'name': org.organization.practice_name,
				'is_leaf':is_leaf,
				'class':'org_icon%d' %(org.organization.organization_type.id)
			},
			'children':[],
			'is_child':False
		})

	for td in org_rs_tree_data:
		for tpd in org_rs_tree_data:
			if td['id'] == tpd['parent_id']:
				td['children'].append(tpd)
				tpd['is_child'] = True

	result = []
	for td in org_rs_tree_data:
		if not td['is_child']:
			result.append(td)

	if is_flat:
		return format_tree_data_child(result, depth=0, org_list=[])

	return result

def format_tree_data_child(result, depth=0, org_list=[]):
	"""Format Tree Data Child: format tree as flat for select choice.
	:param result: data as tree
	:param depth: in the depth of the tree
	:param org_list: flat result
	"""
	for org in result:
		org_list.append((unicode(org['id']), \
				mark_safe(depth*4*'&nbsp;'+org['data'])))

		if org['children']:
			depth += 1
			format_tree_data_child(org['children'], depth, org_list)
			depth -= 1
	return org_list

def can_we_remove_this_org(org_id, mhluser_id):
	"""Can We Remove This Org: If organization is system organization we can 
	not delete it. If current user is not administrator we can't delete it. If
	this organization have children we can't delete it.
	:param org_id: current organization id
	:param mhluser_id: current user id
	"""
	if org_id == RESERVED_ORGANIZATION_ID_SYSTEM:
		return False

	if not Administrator.objects.filter(user__id=mhluser_id).exists():
		return False

	if OrganizationRelationship.active_objects.filter(parent__id=org_id).exists():
		return False

	return True

def get_org_type_name(org, none_text=DEFAULT_ORGANIZATION_TYPE_NAME):
	"""Get org's type name 
	:param org: an instance of organization
	:param none_text: if org_type or org_type name is None, then return none_text
	:return organization type's name
	"""
	if org and org.organization_type and org.organization_type.name:
		return org.organization_type.name
	else:
		return none_text

def get_all_parent_org_ids(org_id_list=[], exclude_id=RESERVED_ORGANIZATION_ID_SYSTEM):
	org_id_list = list(set(org_id_list))
	count = len(org_id_list)
	org_parents = OrganizationRelationship.active_objects.filter(\
			organization__id__in=org_id_list)\
			.select_related('organization','parent')
	if exclude_id is not None:
		org_parents = org_parents.exclude(parent__id=exclude_id)
	org_id_list += org_parents.values_list("parent__id", flat=True)
	org_id_list = list(set(org_id_list))
	if count != len(org_id_list):
		return get_all_parent_org_ids(org_id_list, exclude_id=exclude_id)
	return org_id_list

def get_all_child_org_ids(org_id_list=[]):
	org_id_list = list(set(org_id_list))
	count = len(org_id_list)
	orgs = OrganizationRelationship.active_objects.filter(\
			parent__id__in=org_id_list)\
			.select_related('organization','parent')
	org_id_list += orgs.values_list("organization__id", flat=True)
	org_id_list = list(set(org_id_list))
	if count != len(org_id_list):
		return get_all_child_org_ids(org_id_list)
	return org_id_list

def get_other_organizations(user_id):
	"""get other organizations:
	:param user_id: MHLUser's id
	:return PracticeLocation list
	:raise ValueError
	"""
	if not user_id:
		return []
	user_id = int(user_id)

	exclude_type_ids = [
			RESERVED_ORGANIZATION_TYPE_ID_PRACTICE,
			RESERVED_ORGANIZATION_TYPE_ID_HOSPITAL
		]
	orgs = which_orgs_contain_this_user(user_id, in_tab=None, \
				exclude_type_ids=exclude_type_ids)
	return [{
			'id':org.id,
			'name':org.practice_name,
			'address1':org.practice_address1,
			'address2':org.practice_address2,
			'city':org.practice_city,
			'state':org.practice_state,
			'zip':org.practice_zip
	}for org in orgs]

#Todo UT
def which_orgs_contain_this_org(org_id, type_id=None, org_name=None):
	""" Get organizations that contain this organization.
	:param org_id: is organization's id
	:param type_id: org type id
	:returns: org list
	"""

	if not org_id:
		return []

	try:
		org_id = int(org_id)
	except ValueError:
		return[]

	setting_ids = OrganizationSetting.objects.filter(can_have_member_organization=True).values_list("id", flat=True)
	if not setting_ids:
		return []

	qf = Q(to_practicelocation__pk=org_id)
	qf = qf & Q(Q(from_practicelocation__organization_setting__id__in = setting_ids)
				| Q(Q(Q(from_practicelocation__organization_setting__delete_flag = True)
					|Q(from_practicelocation__organization_setting=None)) 
				& Q(from_practicelocation__organization_type__organization_setting__id__in = setting_ids)))

	if org_name:
		qf = qf & Q(from_practicelocation__practice_name__icontains=org_name)

	if type_id:
		qf = qf & Q(from_practicelocation__organization_type__id=type_id)

	member_orgs = OrganizationMemberOrgs.objects.filter(qf).select_related('from_practicelocation')
	ret_orgs = []
	for org_re in member_orgs:
		org = org_re.from_practicelocation
		ret_orgs.append({
				'relation_id': org_re.id,
				'name': org.practice_name,
				'address1': org.practice_address1,
				'address2': org.practice_address2,
				'city': org.practice_city,
				'state': org.practice_state,
				'zip': org.practice_zip,
				'type': org.organization_type.name if org.organization_type else '',
			})
	return ret_orgs

def get_exclude_provider_ids(org):
	""" Get provider id list excluded from Provider.
		eg. if org don't support Doctor, then exclude these doctor's provider id.
	:param org: is an instance of PracticeLocation
	:returns: id list
	:raise ValueError
	"""
	if not org or not isinstance(org, PracticeLocation):
		raise ValueError
	exclude_provider_ids = []
	if not org.get_setting_attr("can_have_physician"):
		exclude_provider_ids.extend(Physician.active_objects.all().values_list('user__id', flat=True))
	if not org.get_setting_attr("can_have_nppa"):
		exclude_provider_ids.extend(NP_PA.active_objects.all().values_list('user__id', flat=True)) 
	if not org.get_setting_attr("can_have_medical_student"):
		exclude_provider_ids.extend(Provider.active_objects.filter(clinical_clerk=True).values_list('id', flat=True))
	exclude_provider_ids = set(exclude_provider_ids)
	return exclude_provider_ids

def get_all_org_have_these_settings(setting_ids=None, org_type_id=None, order_by='practice_name'):
	""" Get all organizations that have these settings.
	:param setting_ids: setting id list.
		Note: if setting_ids is None, then don't filter with settings.
	:param org_type_id: org type id.
	:param order_by: order by this field. 
	:returns: organization list
	:raise ValueError,FieldError
	"""
	if setting_ids is not None and not isinstance(setting_ids, list):
		raise ValueError
	q_f = Q()
	if org_type_id is not None:
		org_type_id = int(org_type_id)
		q_f = q_f & Q(organization_type__id = org_type_id)

	if setting_ids is not None:
		q_f = q_f & Q(Q(organization_setting__id__in = setting_ids)
					| Q(Q(Q(organization_setting__delete_flag = True)|Q(organization_setting=None)) 
						& Q(organization_type__organization_setting__id__in = setting_ids)))

	orgs = PracticeLocation.objects.filter(q_f).order_by(order_by)
	return list(orgs)

def get_all_org_have_this_type_user(org_type_id=None, user_type_flag=None, order_by='practice_name'):
	""" Get all organizations that have this type user.
	:param org_type_id: org type id.
	:param user_type_flag: user type flag
			<option value="1">Doctor</option>
			<option value="2">NP/PA/Midwife</option>
			<option value="10">Med/Dental Student</option>
			<option value="100">Office Manager</option>
			<option value="101">Office Staff</option>
			<option value="300">Broker/Contractor</option>.
	:param order_by: order by this field. 
	:returns: organization list
	:raise ValueError,FieldError
	"""

	setting_ids = None
	if user_type_flag:
		user_type_flag = int(user_type_flag)
		q_f = None
		if USER_TYPE_DOCTOR == user_type_flag:
			q_f = Q(can_have_physician=True)
		elif USER_TYPE_NPPA == user_type_flag:
			q_f = Q(can_have_nppa=True)
		elif USER_TYPE_MEDICAL_STUDENT == user_type_flag:
			q_f = Q(can_have_medical_student=True)
		elif USER_TYPE_OFFICE_STAFF == user_type_flag:
			q_f = Q(can_have_staff=True)|Q(can_have_nurse=True)|Q(can_have_dietician=True)
		elif USER_TYPE_OFFICE_MANAGER == user_type_flag:
			q_f = Q(can_have_manager=True)
		if q_f is not None:
			setting_ids = list(OrganizationSetting.objects.filter(q_f).values_list("id", flat=True))

	return get_all_org_have_these_settings(setting_ids, org_type_id=org_type_id, order_by=order_by)

def get_common_org_ids(sender_id, recipient_id, type_id=RESERVED_ORGANIZATION_TYPE_ID_PRACTICE):
	sender_org_ids = [o.id for o in which_orgs_contain_this_user(sender_id,\
			type_id=type_id, in_tab=None, include_soft_link=False)]
	recipient_org_ids = [o.id for o in \
			which_orgs_contain_this_user(recipient_id, type_id=type_id,\
			in_tab=None, include_soft_link=False)]
	if not sender_org_ids or not recipient_org_ids:
		return []
	sender_org_parent_ids = get_all_parent_org_ids(sender_org_ids)
	recipient_org_parents = get_all_parent_org_ids(recipient_org_ids)
	if not sender_org_parent_ids or not recipient_org_parents:
		return []
	common_parent_org_ids = list(set(sender_org_parent_ids)\
			.intersection(set(recipient_org_parents)))
	common_org_ids = list(set(recipient_org_ids)\
			.intersection(set(get_all_child_org_ids(common_parent_org_ids))))
	return sorted(common_org_ids)

def get_user_network_org_ids(user_id):
	""" Get user's network organization ids.
	:param user_id: is MHLUser's id
	:returns: org id list
	"""
	if user_id is None:
		return []

	org_ids = [o.id for o in which_orgs_contain_this_user(user_id,\
			in_tab=None, include_soft_link=False)]

	parent_ids = get_all_parent_org_ids(org_ids)
	network_org_ids = append_all_descent_organizations_ids(parent_ids)
	return list(network_org_ids)

def get_more_providers(sender_id, specialty, base_geo=None): 
	"""
	Get more providers with this specialty
	:param sender_id: MHLUser's id,
	:type sender_id: int
	:param specialty: search condition - specialty
	:type specialty: str
	:returns: list of user information like following:
		[{
			'id': '',
			'title': "" (ike "Dr."),
			'name': '',
			'distance': '',
			'photo': ''
		}]
	:raise ValueError
	"""
	if sender_id is None or specialty is None:
		raise ValueError

	org_ids = get_user_network_org_ids(sender_id)
	phys = Physician.objects.filter(user__practices__id__in=org_ids,
								specialty=specialty).distinct()

	base_flag = 0
	if base_geo is not None and "longit" in base_geo and "lat" in base_geo:
		longit = base_geo["longit"]
		lat = base_geo["lat"]
		if "base_flag" in base_geo:
			base_flag = int(base_geo["base_flag"])
		if longit is None or lat is None:
			base_flag = 0

	providers = [{
			'id': phy.user.id,
			'title': "" if phy.user.clinical_clerk else "Dr.",
			'name': get_fullname(phy.user),
			'distance': get_distance(phy.user.lat, phy.user.longit, \
					lat, longit) if base_flag > 0 else '',
			'base_flag': base_flag if phy.user.lat and phy.user.longit else 0,
			'specialty': phy.get_specialty_display(),
			'photo': ImageHelper.get_image_by_type(phy.user.photo, "Middle", "Provider")
		} for phy in phys]
	providers = sorted(providers, key=lambda k: k['distance'])
	return providers

def notify_org_users_tab_chanaged(org_ids, include_member_org=False, \
				include_self_tree=False):
	"""Notify all users in the org and child org tab changed.
		:org_id, organization's id or id's list
		:include_member_org, True or False,
			if True, notify all member organization's users.
		:include_self_tree, True or False,
			if True, nofify all users in the tree below org_ids.
	"""
	logger.debug("Params: org_ids: %s, include_member_org: %s, include_self_tree: %s"\
				%(str(org_ids), str(include_member_org), str(include_self_tree)))
	if org_ids is None:
		return False
	if not isinstance(org_ids, list):
		if isinstance(org_ids, set):
			org_ids = list(org_ids)
		else:
			org_ids = [org_ids]

	if include_member_org or include_self_tree:
		rel_id_dict = get_all_related_org_ids_below_this_org(org_ids)
		if include_member_org and include_self_tree: 
			rel_id_set = rel_id_dict["all_tree_ids"]
		else:
			if include_member_org:
				rel_id_set = rel_id_dict["member_org_tree_ids"]
				rel_id_set = rel_id_set | set(org_ids)
			else:
				rel_id_set = rel_id_dict["self_tree_ids"]
		org_ids = list(rel_id_set)

	logger.debug("related org ids: %s"%str(org_ids))
	staff_user_ids = list(OfficeStaff.objects.filter(practices__in=org_ids)\
		.values_list("user__id", flat=True))
	provider_user_ids = list(Provider.objects.filter(practices__in=org_ids)\
		.values_list("user__id", flat=True))
	all_user_ids = list(set(staff_user_ids+provider_user_ids))
	notify_user_tab_changed(all_user_ids)
	logger.debug("related user ids: %s"%str(all_user_ids))
	return True

