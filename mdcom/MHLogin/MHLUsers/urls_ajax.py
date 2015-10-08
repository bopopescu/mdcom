
from django.conf.urls import patterns


urlpatterns = patterns('MHLogin.MHLUsers.views_ajax',
	(r'^$', 'search_by_name_old'),
	(r'^New/$', 'search_by_name_new'),
	(r'getPendingPracticesTo/$', 'getPendingPracticesTo'),
	(r'getPendingPracticesFrom/$', 'getPendingPracticesFrom'),
	(r'getCurrentPractices/$', 'getCurrentPractices'),
	(r'PracticesSearch/$', 'PracticesSearch'),
	(r'addPracticeToProvider/$', 'addPracticeToProvider'),
	(r'rejectAssociation/$', 'rejectAssociation'),
	(r'addAssociationForPractice/$', 'addAssociationForPractice'),
	(r'resendAssociation/$', 'resendAssociation'),
	(r'removeAssociation/$', 'removeAssociation'),
	(r'makePracticeCurrent/$', 'makePracticeCurrent'),
	(r'removePractice/$', 'removePractice'),
	(r'removePracticeErrorCheck/$', 'removePracticeErrorCheck'),
	(r'SearchByProximity/$', 'search_by_proximity'),
	(r'GetProviders/$', 'get_providers_by_conds'),
	(r'GetMembersForOrg/$', 'get_members_for_org'),
)

