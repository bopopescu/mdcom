
from django import forms
from django.core.exceptions import ValidationError

from MHLogin.Administration.tech_admin import sites, options

from MHLogin.DoctorCom.speech.models import NeospeechConfig, VoiceClip
from MHLogin.DoctorCom.speech.utils import validate_no_other_active_configs
from MHLogin.DoctorCom.speech.neospeech import driver_h


class NeospeechConfigAdminForm(forms.ModelForm):
	def clean_is_active(self):
		if (self.cleaned_data['is_active'] == True):
			validate_no_other_active_configs(self.instance)
		return self.cleaned_data['is_active']

	def clean(self):
		""" Process entire form after field cleans verified """
		cleanf, driver = self.cleaned_data, self.instance.driver
		flds = ['server', 'server_port', 'status_port', 'encoding', 'voice_id', 'is_active']
		if all(fld in cleanf for fld in flds) and cleanf['is_active'] == True:
			stat = driver.request_status(cleanf['server'], cleanf['status_port'])
			if stat['status'] != driver_h.TTS_STATUS_SERVICE_ON:
				raise ValidationError("Validation error, message from "
					"neospeech: %s" % stat['status_text'])
			stat = driver.validate_config(cleanf['server'], cleanf['server_port'],
				"test", fmt=cleanf['encoding'], voice=cleanf['voice_id'])
			if stat['status'] != driver_h.TTS_RESULT_SUCCESS:
				raise ValidationError("Validation error, message from "
					"neospeech: %s" % stat['status_text'])
		return self.cleaned_data


class NeospeechConfigAdmin(options.TechAdmin):
	form = NeospeechConfigAdminForm

	list_display = ('name', 'spoken_lang', 'server', 'server_port',
				'status_port', 'admin_port', 'voice_id', 'encoding',
				'volume', 'speed', 'pitch', 'is_active')


class VoiceClipAdmin(options.TechAdmin):
	list_display = ('config', 'filename', '_get_spoken_text',
					'access_count', 'access_date', 'create_date')
	search_fields = ('spoken_text', )

	_get_spoken_text = lambda self, obj: "%s..." % (obj.spoken_text[:32])

	def __init__(self, model, admin_site):
		super(VoiceClipAdmin, self).__init__(model, admin_site)
		self._get_spoken_text.im_func.short_description = 'Spoken Text'


sites.register(NeospeechConfig, NeospeechConfigAdmin)
sites.register(VoiceClip, VoiceClipAdmin)

