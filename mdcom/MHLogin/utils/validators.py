from django.core.exceptions import ValidationError
import datetime
import time
from django.utils.translation import ugettext_lazy as _

def validate_unixDateTime(value):
	if (value):
		epoch_date = datetime.datetime(1970, 1, 1, 0, 0)
		if (epoch_date > value):
			raise ValidationError(_('Date time field can not be before 01/01/1970 00:00.'))
	return value

def validate_unixDate(value):
	if (value):
		epoch_date = datetime.date(1970, 1, 1)
		if (epoch_date > value):
			raise ValidationError(_('Date field can not be before 01/01/1970.'))
	return value

def validate_fromNow(value):
	if (value):
		now = datetime.datetime.fromtimestamp(time.time())
		if (now > value):
			raise ValidationError(_('This time can not be earlier than now.'))
	return value

def validate_fromToday(value):
	if (value):
		today = datetime.date.today()
		today = datetime.datetime(today.year, today.month, today.day)
		if (today > value):
			raise ValidationError(_('This time can not be earlier than today.'))
	return value
