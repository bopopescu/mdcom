from MHLogin.MHLPractices.models import Pending_Association


def user_is_pendding_in_org(user_id, org):
	if not isinstance(user_id, int):
		raise  
	
	lst = Pending_Association.objects.filter(practice_location=org).\
			values_list('from_user', flat=True)
	rst = Pending_Association.objects.filter(practice_location=org).\
			values_list('to_user', flat=True)
	for item in lst:
		if int(item) == user_id:
			return True

	for item in rst:
		if int(item) == user_id:
			return True
	return False
