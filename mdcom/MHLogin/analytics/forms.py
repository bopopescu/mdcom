
from django import forms

months = (
			(1, 1), (2, 2), (3, 3), (4, 4), (5, 5),
			(6, 6), (7, 7), (8, 8), (9, 9), (10, 10),
			(11, 11), (12, 12),
		)
years = (
			(2009, 2009),
			(2010, 2010),
			(2011, 2011),
		)


class MonthForm(forms.Form):
	"""MonthForm class
	"""
	month = forms.ChoiceField(months)
	year = forms.ChoiceField(years)

