#-*- coding: utf-8 -*-
# This file is used to store global constants.
import re
from django.conf import settings
from django.utils.translation import ugettext as _

UUID_RE = re.compile('[0-9a-f]{32}$')

LANGUAGE_CODE_DE = 'de'
LANGUAGE_CODE_EN_US = 'en-us'

GENDER_CHOICES_US = (
	('M', _('Male')),
	('F', _('Female')),
)
GENDER_CHOICES_DE = (
	('M', 'Männlich'),
	('F', 'Weiblich'),
)
L10N_GENDER_CHOICES = {
	LANGUAGE_CODE_DE:GENDER_CHOICES_DE,
	LANGUAGE_CODE_EN_US:GENDER_CHOICES_US
}

GENDER_CHOICES = L10N_GENDER_CHOICES[settings.FORCED_LANGUAGE_CODE]

SPECIALTY_CHOICES_US = (
	('AC', 'Acupuncture'),
	('AD', 'Addiction Medicine'),
	('AL', 'Allergy and Immunology'),
	('AN', 'Anesthesiology'),
	('CH', 'Cardiology'),
	('CM', 'Cardiovascular Medicine'),
	('CT', 'Cardiovascular/Thoracic Surgery'),
	('CY', 'Clinical Hypnosis'),
	('DS', 'Dermatology'),
	('DT', 'Dentistry'),
	('EL', 'Electrophysiology'),
	('EM', 'Elecrodiagnostic Medicine'),
	('EN', 'Endocrinology, Diabetes and Metabolism'),
	('ER', 'Emergency Medicine'),
	('FP', 'Family Practice'),
	('GA', 'Gastroenterology'),
	('GO', 'Gynecological Oncology'),
	('GP', 'General Practice'),
	('GS', 'General Surgery'),
	('GY', 'Gynecology'),
	('HS', 'Hand Surgery'),
	('HE', 'Hematology/Oncology'),
	('HO', 'Hospitalist'),
	('ID', 'Infectious Disease'),
	('IG', 'Integrative Medicine'),
	('IM', 'Internal Medicine'),
	('IR', 'Interventional Radiology'),
	('NE', 'Nephrology'),
	('NM', 'Nuclear Medicine'),
	('NP', 'Neonatal-Perinatal Medicine'),
	('NS', 'Neurosurgery'),
	('NU', 'Neurology'),
	('OC', 'Occupational Medicine'),
	('OG', 'Obstetrics and Gynecology'),
	('OM', 'Oral and Maxillofacial Surgery'),
	('ON', 'Oncology'),
	('OP', 'Ophthalmology'),
	('OR', 'Orthopedic Medicine'),
	('OS', 'Orthopedic Surgery'),
	('OT', 'Otolaryngology'),
	('PH', 'Palliative Care - Hospice'),
	('PA', 'Pathology'),
	('PC', 'Primary Care'),
	('PD', 'Pediatrics'),
	('PG', 'Psychology'),
	('PL', 'Pulmonary Medicine'),
	('PM', 'Physical Medicine and Rehabilitiation'),
	('PN', 'Pain Management'),
	('PO', 'Podiatry (Feet)'),
	('PR', 'Plastic/Reconstructive Surgery'),
	('PS', 'Psychiatry'),
	('PY', 'Physiology'),
	('RA', 'Radiology'),
	('RH', 'Rheumatology'),
	('RO', 'Radiation Oncology'),
	('RS', 'Robotics Surgery'),
	('SM', 'Sleep Medicine'),
	('SP', 'Sports Medicine'),
	('SW', 'Surgical Weight Loss'),
	('UC', 'Urgent Care'),
	('UR', 'Urology'),
	('VS', 'Vascular Surgery')
)

SPECIALTY_CHOICES_DE = (
	('AH', 'Anästhesiologie'),
	('AT', 'Anatomie'),
	('AR', 'Arbeitsmedizin'),
	('AU', 'Augenheilkunde'),
	('BI', 'Biochemie'),
	('CH', 'Chirurgie'),
	('FG', 'Frauenheilkunde und Geburtshilfe'),
	('HO', 'Hals-Nasen-Ohrenheilkunde'),
	('HG', 'Haut- und Geschlechtskrankheiten'),
	('HU', 'Humangenetik'),
	('HY', 'Hygiene und Umweltmedizin'),
	('IA', 'Innere und Allgemeinmedizin (Hausarzt)'),
	('KJ', 'Kinder- und Jugendmedizin'),
	('KP', 'Kinder- und Jugendpsychiatrie und -psychotherapie'),
	('LA', 'Laboratoriumsmedizin'),
	('MI', 'Mikrobiologie, Virologie und Infektionsepidemiologie'),
	('MG', 'Mund-Kiefer-Gesichtschirurgie'),
	('NC', 'Neurochirurgie'),
	('NL', 'Neurologie'),
	('NM', 'Nuklearmedizin'),
	('OG', 'Öffentliches Gesundheitswesen'),
	('PA', 'Pathologie'),
	('PH', 'Pharmakologie'),
	('PR', 'Physikalische und Rehabilitative Medizin'),
	('PS', 'Physiologie'),
	('PP', 'Psychiatrie und Psychotherapie'),
	('PM', 'Psychosomatische Medizin und Psychotherapie'),
	('RA', 'Radiologie'),
	('RE', 'Rechtsmedizin'),
	('ST', 'Strahlentherapie'),
	('TR', 'Transfusionsmedizin'),
	('UR', 'Urologie'),
	('ZA', 'Zahnmedizin'),
)

L10N_SPECIALTY_CHOICES = {
	LANGUAGE_CODE_DE:SPECIALTY_CHOICES_DE,
	LANGUAGE_CODE_EN_US:SPECIALTY_CHOICES_US
}

SPECIALTY_CHOICES = L10N_SPECIALTY_CHOICES[settings.FORCED_LANGUAGE_CODE]

CARE_TYPE_CHOICES = (
	('I', _('Inpatient')),
	('O', _('Outpatient')),
)

YESNO_CHOICE = (
	('Y', _('Yes')),
	('N', _('No')),
)

# TODO:
# The following choices are being used for Providers at this point. It should
# probably be renamed to reflect this.
STAFF_TYPE_CHOICES = (
	('AT', _('Attending')),
	('FE', _('Fellow')),
	('CR', _('Chief Resident')),
	('RE', _('Resident')),
	('IN', _('Intern')),
	('ST', _('Medical or Dental Student')),
	#('CM', 'Case Manager'), # Disabled since physicians can't be these types.
	#('SW', 'Social Worker'), # Disabled since physicians can't be these types
)

STAFF_TYPE_CHOICES_EXTRA = (
	('FA', _('Faculty Attending')),
	('CR', _('Chief Resident')),
	('RE', _('Resident')),
	('IN', _('Intern')),
	('C4', _('4th Year Medical Student')),
	('C3', _('3rd Year Medical Student')),
	('CM', _('Case Manager')),
	('SW', _('Social Worker')),
	('NS', _('Non Staff')),
)

STATE_CHOICES_US = (
	('AL', 'Alabama'),
	('AK', 'Alaska'),
	('AZ', 'Arizona'),
	('CA', 'California'),
	('CO', 'Colorado'),
	('CT', 'Connecticut'),
	('DE', 'Delaware'),
	('DC', 'District of Columbia'),
	('FL', 'Florida'),
	('GA', 'Georgia'),
	('GU', 'Guam'),
	('HI', 'Hawaii'),
	('ID', 'Idaho'),
	('IL', 'Illinois'),
	('IN', 'Indiana'),
	('IA', 'Iowa'),
	('KS', 'Kansas'),
	('KY', 'Kentucky'),
	('LA', 'Louisiana'),
	('ME', 'Maine'),
	('MD', 'Maryland'),
	('MA', 'Massachusetts'),
	('MI', 'Michigan'),
	('MN', 'Minnesota'),
	('MS', 'Mississippi'),
	('MO', 'Missouri'),
	('MT', 'Montana'),
	('NE', 'Nebraska'),
	('NV', 'Nevada'),
	('NH', 'New Hampshire'),
	('NJ', 'New Jersey'),
	('NM', 'New Mexico'),
	('NY', 'New York'),
	('NC', 'North Carolina'),
	('ND', 'North Dakota'),
	('OH', 'Ohio'),
	('OK', 'Oklahoma'),
	('OR', 'Oregon'),
	('PA', 'Pennsylvania'),
	('RI', 'Rhode Island'),
	('SC', 'South Carolina'),
	('SD', 'South Dakota'),
	('TN', 'Tennessee'),
	('TX', 'Texas'),
	('UT', 'Utah'),
	('VT', 'Vermont'),
	('VA', 'Virginia'),
	('WA', 'Washington'),
	('WV', 'West Virginia'),
	('WI', 'Wisconsin'),
	('WY', 'Wyoming'),
)

STATE_CHOICES_DE = (
	('BW', 'Baden-Württemberg'),
	('BY', 'Bayern'),
	('BE', 'Berlin'),
	('BB', 'Brandenburg'),
	('HB', 'Bremen'),
	('HH', 'Hamburg'),
	('HE', 'Hessen'),
	('MV', 'Mecklenburg-Vorpommern'),
	('NI', 'Niedersachsen'),
	('NW', 'Nordrhein-Westfalen'),
	('RP', 'Rheinland-Pfalz'),
	('SL', 'Saarland'),
	('SN', 'Sachsen'),
	('ST', 'Sachsen-Anhalt'),
	('SH', 'Schleswig-Holstein'),
	('TH', 'Thüringen'),
)

L10N_STATE = {
	LANGUAGE_CODE_DE:STATE_CHOICES_DE,
	LANGUAGE_CODE_EN_US:STATE_CHOICES_US
}

STATE_CHOICES = L10N_STATE[settings.FORCED_LANGUAGE_CODE]

ALL_NATION_CHOICES = {
	LANGUAGE_CODE_DE:(
		('de', 'Deutschland'),
	),
	LANGUAGE_CODE_EN_US:(
		('us', 'United States'),
	)
}

NATION_CHOICES = ALL_NATION_CHOICES[settings.FORCED_LANGUAGE_CODE]

BILLING_STATUS_CHOICES = (
		('AR', _('Active - Rebill')),
		('AE', _('Active - Cancel')),
		('NC', _('Not Active - Canceled')),
		('NE', _('Not Active - Expired')),
)

FORWARD_CHOICES = (
	('MO', _('Mobile')),
	('OF', _('Office')),
	('OT', _('Other')),
	('VM', _('Voicemail')),
)

CALLER_ANSSVC_CHOICES = (
	('NO', 'None'),
	('MO', 'Mobile'),
	('OF', 'Office'),
	('OT', 'Other'),
)

ROLE_TYPE = (
	(2, _('Super Manager')),
	(1, _('Manager')),
)

ROLE_TYPE_MEMBER = (
	(0, _('Member')),
)

ALL_MEMBER_ROLE_TYPES = ROLE_TYPE+ROLE_TYPE_MEMBER

SMART_PHONE_OPTIONS = (
	(True, _('Enabled')),
	(False, _('Disabled')),
)

PARTNER_PERMISSION_CHOICES = (
	(1, _('All')),
	(2, _('Created')),
)

ORG_SIZE_TYPE = (
		(0, _('Small')),
		(1, _('Middle')),
		(2, _('Large')),
		)
ORG_POSITION_TYPE = (
		(0, _('Top')),
		(1, _('Inside of Tab Block')),
		)

ALL_DATE_FORMAT = {
	LANGUAGE_CODE_DE:'%Y-%m-%d',
	LANGUAGE_CODE_EN_US:'%m/%d/%Y'
}
DATE_FORMAT = ALL_DATE_FORMAT[settings.FORCED_LANGUAGE_CODE]

ALL_DATETIME_FORMAT = {
	LANGUAGE_CODE_DE:'%Y-%m-%d %H:%M',
	LANGUAGE_CODE_EN_US:'%m/%d/%Y %H:%M'
}
DATETIME_FORMAT = ALL_DATETIME_FORMAT[settings.FORCED_LANGUAGE_CODE]

USER_TYPE_DOCTOR = 1
USER_TYPE_NPPA = 2
USER_TYPE_NURSE = 3
USER_TYPE_DIETICIAN = 4
USER_TYPE_MEDICAL_STUDENT = 10
USER_TYPE_OFFICE_MANAGER = 100
USER_TYPE_OFFICE_STAFF = 101
USER_TYPE_TECH_ADMIN = -1
USER_TYPE_BROKER = 300


USER_TYPE_CHOICES_US = (
	# 0<x<100 is provider classes
	(1, _('Doctor')),
	(2, _('NP/PA/Midwife')),
	#(3, 'Nurse'),
	
	(10, _('Med/Dental Student')),
	
	# 99<x<200 is for support staff types
	(100, _('Office Manager')),
	(101, _('Office Staff')),
	
	# 199<x<300 is for patients
	#(200, 'Office Manager'),

	# 300<x<400 is for broker
	(300, _('Broker/Contractor')),

	#(0,'Let User Choose'),
)
USER_TYPE_CHOICES_DE = (
	(1, 'Arzt'),
	(2, 'Belegarzt'),
	(10, 'Med. / Dent. Student'),
	(100, 'Praxisverwalter'),
	(101, 'Praxispersonal'),
	(300, 'Broker/Contractor'),
)
L10N_USER_TYPE_CHOICES = {
	LANGUAGE_CODE_DE:USER_TYPE_CHOICES_DE,
	LANGUAGE_CODE_EN_US:USER_TYPE_CHOICES_US
}

USER_TYPE_CHOICES = L10N_USER_TYPE_CHOICES[settings.FORCED_LANGUAGE_CODE]
#user types that managers are allowed to invite
#needs to be a subset of USER_TYPE_CHOICES
#modify by xlin in 20120509 
MANAGER_INVITE_CHOICES = (
	(1, _('Doctor')),
	(2, _('NP/PA/Midwife')),
	(101, _('Office Staff')),
	(10, _('Med/Dental Student')),
)

PROVIDER_INVITE_CHOICES_US = (
	(1, _('Doctor')),
	(2, _('NP/PA/Midwife')),
	(10, _('Med/Dental Student')),
)

PROVIDER_INVITE_CHOICES_DE = (
	(1, "Arzt"),
	(2, "Belegarzt"),
	(10, "Med. / Dent. Student"),
)

L10N_PROVIDER_INVITE_CHOICES = {
	LANGUAGE_CODE_DE:PROVIDER_INVITE_CHOICES_DE,
	LANGUAGE_CODE_EN_US:PROVIDER_INVITE_CHOICES_US
}

PROVIDER_INVITE_CHOICES = L10N_PROVIDER_INVITE_CHOICES[settings.FORCED_LANGUAGE_CODE]

PROVIDER_CREATE_CHOICES = PROVIDER_INVITE_CHOICES

STAFF_CREATE_CHOICES = (
	(101, _('Staff')),
	(3, _('Nurse')),
	(4, _('Dietician')),
)

#update by xlin 20120802 to fix bug that office manager send
#invitation to doctor,nppa,student and office staff in staff page.
OFFICE_STAFF_INVITE_CHOICES = (
	(1, _('Doctor')),
	(2, _('NP/PA/Midwife')),
	(10, _('Med/Dental Student')),
	(100, _('Office Manager')),
	(101, _('Office Staff')),
)
#user types that sales staff are allowed to invite
#needs to be a subset of USER_TYPE_CHOICES
SALES_INVITE_CHOICES = (
	(1, _('Doctor')),
	(2, _('NP/PA/Midwife')),
	(100, _('Office Manager')),
)

PROVIDER_TYPE_CHOICES = (
	(1, _('Doctor')),
	(2, _('NP/PA/Midwife')),
	(10, _('Med/Dental Student')),
)

BROKER_TYPE_CHOICES = (
	(300, _('Broker/Contractor')),
)

ALL_SETTING_TIME_CHOICES = {
	LANGUAGE_CODE_EN_US:(
		(1, '12-hour clock'),
		(0, '24-hour clock'),
	),
	LANGUAGE_CODE_DE:(
		(1, '12-Stunden-Format'),
		(0, '24-Stunden-Format'),
	),
}

SETTING_TIME_CHOICES = ALL_SETTING_TIME_CHOICES[settings.FORCED_LANGUAGE_CODE]

#add by xlin 121025 for todo1045
LANGUAGE = {
	LANGUAGE_CODE_EN_US:'English',
	LANGUAGE_CODE_DE:'Deutsch',
}

ACCEPT_CALL_GROUP_PENDING = (
	(0,'New'),
	(1,'Accept'),
	(2,'Reject'),
)

ALL_TIME_ZONES_CHOICES = {
	LANGUAGE_CODE_EN_US:(
			('America/Los_Angeles', 'Pacific Time (PT)'),
			('America/New_York', 'Eastern Time (ET)'),
			('America/Chicago', 'Central Time (CT)'),
			('America/Boise', 'Mountain Time (MT)'),
			('America/Phoenix', 'Mountain Time - Arizona (MT)'),
			('America/Anchorage', 'Alaska Time (AKT)'),
			('Pacific/Honolulu', 'Hawaii Time (HT)'),
		),
	LANGUAGE_CODE_DE:(
			('Europe/Berlin', 'Mitteleuropäische Zeit (CET)'),
			('Europe/Madrid', 'Mitteleuropäische Sommerzeit (CEST)'),
			('Europe/London', 'Westeuropäische Zeit (WET)'),
			('Atlantic/Reykjavik', 'Westeuropäische Sommerzeit (WEST)'),
			('EET', 'Osteuropäische Zeit (EET)'),
			('Europe/Athens', 'Osteuropäische Sommerzeit (EEST)'),
			('Europe/Moscow', 'Moskauer Zeit'),
			('Europe/Kaliningrad', 'Kaliningrader Zeit'),
		),
}

TIME_ZONES_CHOICES = ALL_TIME_ZONES_CHOICES[settings.FORCED_LANGUAGE_CODE]

RESERVED_ORGANIZATION_ID_DOCTORCOM = -1

RESERVED_ORGANIZATION_TYPE_ID_SYSTEM = -1
RESERVED_ORGANIZATION_TYPE_ID_PRACTICE = 1
RESERVED_ORGANIZATION_TYPE_ID_GROUPPRACTICE = 2
RESERVED_ORGANIZATION_TYPE_ID_HOSPITAL = 3
RESERVED_ORGANIZATION_TYPE_ID_ASSOCIATION = 4

RESERVED_ORGANIZATION_TYPES_RESERVED = [
		RESERVED_ORGANIZATION_TYPE_ID_SYSTEM,
		RESERVED_ORGANIZATION_TYPE_ID_PRACTICE,
		RESERVED_ORGANIZATION_TYPE_ID_GROUPPRACTICE,
		RESERVED_ORGANIZATION_TYPE_ID_HOSPITAL,
		RESERVED_ORGANIZATION_TYPE_ID_ASSOCIATION,
	]

RESERVED_ORGANIZATION_ID_SYSTEM = -1

DEFAULT_ORGANIZATION_TYPE_NAME = _("Organization")

REFER_FORWARD_CHOICES_BOTH = 1
REFER_FORWARD_CHOICES_ONLY_MANAGER = 2
REFER_FORWARD_CHOICES = (
	(REFER_FORWARD_CHOICES_BOTH, _('Both office manager and I get a copy of referrals')),
	(REFER_FORWARD_CHOICES_ONLY_MANAGER, _('Send Referrals to my office manager only')),
)
