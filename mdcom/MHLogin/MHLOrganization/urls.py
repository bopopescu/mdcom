try:
	from django.conf.urls import patterns
except ImportError:  # remove when django 1.5 fully integrated
	from django.conf.urls.defaults import patterns

urlpatterns = patterns('MHLogin.MHLOrganization',
	(r'^List/$', 'views.org_list'),
	(r'^TreeData/$', 'views.org_tree'),

	(r'^Add/$', 'views.org_add'),
	(r'^View/$', 'views.org_view'),
	(r'^Remove/$', 'views.org_remove'),
	(r'^Move/$', 'views.org_move'),
	(r'^DragMove/$', 'views.org_drag_move'),
	(r'^Save/$', 'views.org_save'),
	(r'^Edit/$', 'views.org_edit'),
	
	(r'^MemberOrg/View/$', 'views.member_org_view'),
	(r'^MemberOrg/InviteStep1/$', 'views.member_org_invite_step1'),
	(r'^MemberOrg/InviteStep2/$', 'views.member_org_invite_step2'),
	(r'^MemberOrg/InviteStep3/$', 'views.member_org_invite_step3'),
	(r'^MemberOrg/Remove/$', 'views.member_org_remove'),
	(r'^MemberOrg/CancelInvitation/(?P<pending_id>\d+)/$', 'views.member_org_cancel_invite'),
	(r'^MemberOrg/ResendInvitation/(?P<pending_id>\d+)/$', 'views.member_org_resend_invite'),
	(r'^MemberOrg/IncomingInvitation/$', 'views.member_org_invite_incoming'),
	(r'^MemberOrg/AcceptInvite/(?P<pending_id>\d+)/$', 'views.member_org_accept_invite'),
	(r'^MemberOrg/RejectInvite/(?P<pending_id>\d+)/$', 'views.member_org_rejected_invite'),

	(r'^MemberOrg/ShowMemberOrg/$', 'views.member_org_show_org'),
	(r'^MemberOrg/ShowInvitation/$', 'views.member_org_show_invite'),

	(r'^OrgSetting/$', 'views.org_setting_edit'),

	(r'^InformationSub/IVRView/$', 'views.information_sub_ivr_view'),
	(r'^InformationSub/PinChange/$', 'views.information_sub_pin_change'),
	(r'^InformationSub/HourEdit/$', 'views.information_sub_hour_edit'),
	(r'^InformationSub/HolidayView/$', 'views.information_sub_holiday_view'),
	(r'^InformationSub/HolidayAdd/(?P<holiday_id>\d+)/$', 'views.information_sub_holiday_add'),
	
	(r'^Member/View/$', 'views.member_view'),
	(r'^Member/ProviderCreate/$', 'views.member_provider_create'),
	(r'^Member/StaffCreate/$', 'views.member_staff_create'),

	# ------------------

#	(r'^Staff/newProvider/$', 'views.newProvider'),
#	(r'^Staff/newStaff/$', 'views.newStaff'),
	(r'Member/AJAX/StaffSearch/$', 'views_member.staffSearch'),
	(r'Member/AJAX/ProviderList/$', 'views_member.currentProviders'),
	(r'Member/AJAX/StaffList/$', 'views_member.currentOfficeStaff'),

	(r'Member/AJAX/GetInvitePending/$', 'views_member.get_invite_pending'),

	(r'Member/AJAX/addAssociation/$', 'views_member.addAssociation'),
	(r'Member/AJAX/resendAssociation/$', 'views_member.resendAssociation'),
	(r'Member/AJAX/removeAssociation/$', 'views_member.removeAssociation'),
	(r'Member/AJAX/rejectAssociation/$', 'views_member.rejectAssociation'),
	(r'Member/AJAX/addProviderToPractice/$', 'views_member.addProviderToPractice'),
	(r'Member/AJAX/CheckProviderSchedule/$', 'views_member.checkProviderSchedule'),
	(r'Member/AJAX/RemoveProvider/$', 'views_member.removeProvider'),
	(r'Member/AJAX/ChangeSmartphonePermission/$', 'views_member.changeSmartphonePermission'),
	# add by xlin 20120301 to add new view to remove staff, change role, get provider, etc	
	(r'Member/AJAX/ChangeRole/$', 'views_member.changeRole'),
	(r'Member/AJAX/RemoveStaff/$', 'views_member.removeStaff'),
	(r'Member/AJAX/getInvitations/', 'views_member.getInvitations'),
	(r'Member/AJAX/resendInvitation/', 'views_member.resendInvitation'),
	(r'Member/AJAX/cancelInvitation/', 'views_member.cancelInvitation'),
	(r'Member/AJAX/cancelExistInvitation/', 'views_member.cancelExistInvitation'),
	(r'Member/AJAX/sendNewProviderEmail/', 'views_member.sendNewProviderEmail'),
	# done xlin 
	(r'Member/AJAX/checkPenddingExist/', 'views_member.checkPenddingExist'),
	(r'Member/AJAX/valideInvitation/', 'views_member.valideInvitation'),

	(r'Member/InviteProvider/$', 'views.invite_provider'),
	(r'Member/InviteStaff/$', 'views.invite_staff'),

	(r'^Invite/View/$', 'views.invite_view'),
)