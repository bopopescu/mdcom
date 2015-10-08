
from django.db import models
from django.db.models.query import QuerySet
from django.db.models.fields.related import OneToOneField
from django.core.exceptions import ObjectDoesNotExist


class InheritanceManager(models.Manager):
	""" Use Inheritance manager to return actual class from id in baseclass SpeechConfig """
	use_for_related_fields = True

	def get_query_set(self):
		return InheritanceQuerySet(self.model)

	def select_subclasses(self, *subclasses):
		return self.get_query_set().select_subclasses(*subclasses)

	def get_subclass(self, *args, **kwargs):
		return self.get_query_set().select_subclasses().get(*args, **kwargs)


class InheritanceQuerySet(QuerySet):
	""" This class uses introspection on the given model to find subclasses.  Also override
	the standard QuerySet iterator to iterate through subclasses and return non-null
	chlid class instance or base class if none found.
	"""
	def select_subclasses(self, *subclasses):
		""" Introspect on the model to find subclasses. We can find all the OneToOne
		relationships to the model that could be from subclasses: they will be instances
		of SingleRelatedObjectDescriptor then filter further to related subclass.
		"""
		if not subclasses:
			subclasses = [rel.var_name for rel in self.model._meta.get_all_related_objects()
						  if isinstance(rel.field, OneToOneField)
						  and issubclass(rel.field.model, self.model)]
		new_qs = self.select_related(*subclasses)
		new_qs.subclasses = subclasses
		return new_qs

	def _clone(self, klass=None, setup=False, **kwargs):
		""" Override _clone to pass along extra info about children."""
		for name in ['subclasses', '_annotated']:
			if hasattr(self, name):
				kwargs[name] = getattr(self, name)
		return super(InheritanceQuerySet, self)._clone(klass, setup, **kwargs)

	def annotate(self, *args, **kwargs):
		qset = super(InheritanceQuerySet, self).annotate(*args, **kwargs)
		qset._annotated = [a.default_alias for a in args] + kwargs.keys()
		return qset

	def iterator(self):
		""" Override the iterator method on QuerySet. Since each superclass instance will
		now have a prepopulated attribute for its appropriate subclass we just need to
		iterate through the subclasses and return instead the one that happens to be non
		null (falling back of course to just returning the superclass if no subclass
		instances exist).
		"""
		it = super(InheritanceQuerySet, self).iterator()
		if getattr(self, 'subclasses', False):
			for obj in it:
				for s in self.subclasses:
					try:
						sub_obj = getattr(obj, s)
					except ObjectDoesNotExist:
						sub_obj = None
					if sub_obj:
						break
				if not sub_obj:
					sub_obj = obj
				if getattr(self, '_annotated', False):
					for k in self._annotated:
						setattr(sub_obj, k, getattr(obj, k))

				yield sub_obj
		else:
			for obj in it:
				yield obj

