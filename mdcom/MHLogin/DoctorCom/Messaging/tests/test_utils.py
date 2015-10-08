
'''
Created on 2013-6-23

@author: mwang
'''
from django.test import TestCase

from MHLogin.DoctorCom.Messaging.utils import get_prefix_from_subject,\
	remove_prefix_from_subject, clean_subject_prefix

class CleanMessageSubjectTest(TestCase):
	subs = [
		{"subject": None, "prefix": "", "no_prefix": "", "cleaned_subject":""},

		{"subject": "Re:test", "prefix": "Re:", "no_prefix": "test", "cleaned_subject":"Re: test"},
		{"subject": "RE:test", "prefix": "RE:", "no_prefix": "test", "cleaned_subject":"RE: test"},
		{"subject": "Fw:test", "prefix": "Fw:", "no_prefix": "test", "cleaned_subject":"Fw: test"},
		{"subject": "FW:test", "prefix": "FW:", "no_prefix": "test", "cleaned_subject":"FW: test"},

		{"subject": "Re:Fw:test", "prefix": "Re:", "no_prefix": "test", "cleaned_subject":"Re: test"},
		{"subject": "RE:Fw:test", "prefix": "RE:", "no_prefix": "test", "cleaned_subject":"RE: test"},
		{"subject": "Re:FW:test", "prefix": "Re:", "no_prefix": "test", "cleaned_subject":"Re: test"},
		{"subject": "RE:FW:test", "prefix": "RE:", "no_prefix": "test", "cleaned_subject":"RE: test"},
		{"subject": "Fw:Re:test", "prefix": "Fw:", "no_prefix": "test", "cleaned_subject":"Fw: test"},
		{"subject": "FW:Re:test", "prefix": "FW:", "no_prefix": "test", "cleaned_subject":"FW: test"},
		{"subject": "Fw:RE:test", "prefix": "Fw:", "no_prefix": "test", "cleaned_subject":"Fw: test"},
		{"subject": "FW:RE:test", "prefix": "FW:", "no_prefix": "test", "cleaned_subject":"FW: test"},

		{"subject": "Re:Re:test", "prefix": "Re:", "no_prefix": "test", "cleaned_subject":"Re: test"},
		{"subject": "RE:Re:test", "prefix": "RE:", "no_prefix": "test", "cleaned_subject":"RE: test"},
		{"subject": "Re:RE:test", "prefix": "Re:", "no_prefix": "test", "cleaned_subject":"Re: test"},
		{"subject": "RE:RE:test", "prefix": "RE:", "no_prefix": "test", "cleaned_subject":"RE: test"},
		{"subject": "Fw:Fw:test", "prefix": "Fw:", "no_prefix": "test", "cleaned_subject":"Fw: test"},
		{"subject": "FW:Fw:test", "prefix": "FW:", "no_prefix": "test", "cleaned_subject":"FW: test"},
		{"subject": "Fw:FW:test", "prefix": "Fw:", "no_prefix": "test", "cleaned_subject":"Fw: test"},
		{"subject": "FW:FW:test", "prefix": "FW:", "no_prefix": "test", "cleaned_subject":"FW: test"},

		{"subject": "Re:teRE:st", "prefix": "Re:", "no_prefix": "teRE:st", "cleaned_subject":"Re: teRE:st"},
		{"subject": "RE:teRe:st", "prefix": "RE:", "no_prefix": "teRe:st", "cleaned_subject":"RE: teRe:st"},
		{"subject": "Fw:teFW:st", "prefix": "Fw:", "no_prefix": "teFW:st", "cleaned_subject":"Fw: teFW:st"},
		{"subject": "FW:teFw:st", "prefix": "FW:", "no_prefix": "teFw:st", "cleaned_subject":"FW: teFw:st"},

		{"subject": "Re:", "prefix": "Re:", "no_prefix": "", "cleaned_subject":"Re:"},
		{"subject": "RE:", "prefix": "RE:", "no_prefix": "", "cleaned_subject":"RE:"},
		{"subject": "Fw:", "prefix": "Fw:", "no_prefix": "", "cleaned_subject":"Fw:"},
		{"subject": "FW:", "prefix": "FW:", "no_prefix": "", "cleaned_subject":"FW:"},

		{"subject": "FW: FW: FW: test dicom suffix ", "prefix": "FW:", "no_prefix": "test dicom suffix", "cleaned_subject":"FW: test dicom suffix"},
	]

	def test_get_prefix_from_subject(self):
		for sub in self.subs:
			self.assertEqual(sub["prefix"], get_prefix_from_subject(sub["subject"]))

	def test_remove_prefix_from_subject(self):
		for sub in self.subs:
			self.assertEqual(sub["no_prefix"], remove_prefix_from_subject(sub["subject"]))

	def test_clean_subject_prefix(self):
		for sub in self.subs:
			self.assertEqual(sub["cleaned_subject"], clean_subject_prefix(sub["subject"]))
