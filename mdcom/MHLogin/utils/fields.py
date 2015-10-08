
import six
from django.db import models
from django.forms.widgets import CheckboxInput

try:
	from django_localflavor_us.models import PhoneNumberField
except ImportError:  # remove when django 1.5 fully integrated
	from django.contrib.localflavor.us.models import PhoneNumberField

import uuid


# Taken from http://gist.github.com/374662
class UUIDField(models.CharField):
	"""
	A field which stores a UUID value in hex format. This may also have
	the Boolean attribute 'auto' which will set the value on initial save to a
	new UUID value (calculated using the UUID1 method). Note that while all
	UUIDs are expected to be unique we enforce this with a DB constraint.
	"""
	# Modified from http://www.davidcramer.net/code/420/improved-uuidfield-in-django.html
	__metaclass__ = models.SubfieldBase

	def __init__(self, auto=False, *args, **kwargs):
		if kwargs.get('primary_key', False):
			assert auto, "Must pass auto=True when using UUIDField as primary key."
		self.auto = auto
		# Set this as a fixed value, we store UUIDs in text.
		kwargs['max_length'] = 32
		if auto:
			# Do not let the user edit UUIDs if they are auto-assigned.
			kwargs['editable'] = False
			kwargs['blank'] = True
			kwargs['unique'] = True
		super(UUIDField, self).__init__(*args, **kwargs)

	def db_type(self, connection):
		return 'varchar(36)'

	def pre_save(self, model_instance, add):
		"""Ensures that we auto-set values if required. See CharField.pre_save."""
		value = getattr(model_instance, self.attname, None)
		if not value and self.auto:
			# Assign a new value for this attribute if required.
			value = uuid.uuid4().hex
			setattr(model_instance, self.attname, value)
		return value

	def to_python(self, value):
		if not value:
			return None
		if len(value) != 32:
			value = value.replace('-', '')
		assert len(value) == 32
		return value

try:
	from south.modelsinspector import add_introspection_rules
except ImportError:
	pass
else:
	add_introspection_rules([
        (
            [UUIDField],  # Class(es) these apply to
            [],  # Positional arguments (not used)
            {  # Keyword argument
                "auto": ["auto", {"default": "False"}],
            },
        ),
    ], ["^common\.fields\.UUIDField"])  # XXX Change this to where yours is stored. Better solution?
# End Taken from http://gist.github.com/374662


class MHLPhoneNumberField(PhoneNumberField):

	def to_python(self, value):
		number = super(MHLPhoneNumberField, self).to_python(value)
		if number:
			return number.replace('-', '').replace("(", "").replace(") ", "")
		else:
			return ''

	def formfield(self, **kwargs):
		from django.conf import settings
		if (not settings.CALL_ENABLE):
			from django.forms.fields import CharField as form_CharField
			from django.db.models.fields import CharField as model_CharField
			defaults = {'form_class': form_CharField}
			defaults.update(kwargs)
			return super(model_CharField, self).formfield(**defaults)
		else:
			return super(PhoneNumberField, self).formfield(**kwargs)


class MHLCheckboxInput(CheckboxInput):
	def value_from_datadict(self, data, files, name):
		""" 
		Overridden, revert to Django 1.3's CheckboxInput, see Redmines 2046, 2047.  
		When we remove Django form processing in APP and API (2046) this will go away.

		Django 1.5 casted return value to bool and bool('0') is True.  Django 1.3 didn't, 
		it's an arguable change since BooleanField did validation in its own clean().  
		However we use Django's form processing in our Smartphone API, our phones send 
		back the string '0' for false boolean fields.  Long term solution is to not use 
		Django's form processing in this one-way direction, since our smartphone
		views return json and not rendered by forms. 

		TODO: This function is temporary, when finished Redmine: 
			https://redmine.mdcom.com/issues/2046
		will make this class and function obsolete and can be removed.
		"""
		if name not in data:
			# A missing value means False because HTML form submission does not
			# send results for unselected checkboxes.
			return False
		value = data.get(name)
		# Translate true and false strings to boolean values.
		values = {'true': True, 'false': False}
		if isinstance(value, six.string_types):
			value = values.get(value.lower(), value)
		return value  # Django 1.5 casted to bool  

