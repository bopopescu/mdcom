
from django.db import models


TOLL_FREE_CODES = (
		'800', '888', '877', '866',
		# Reserved for future use, as per http://en.wikipedia.org/wiki/Toll-free_telephone_number
		# '855', '844', '833', '822', '880', '881', '882', '883', '884', '885',
		# '886', '887', '889',
)

INVALID_CODES = (
		'900', '211', '212', '311', '411', '511', '611', '711', '811', '911', '677',
)



class NumberPool(models.Model):
	number_sid = models.CharField(max_length=34)

	area_code = models.CharField(max_length=3, db_index=True)
	prefix = models.CharField(max_length=3)
	line_number = models.CharField(max_length=4)
	
	class Meta:
		unique_together = (('area_code', 'prefix', 'line_number'),)
	
	def delete(self):
		number = ''.join([self.area_code, self.prefix, self.line_number, ])
		number_sid = self.number_sid
		super(NumberPool, self).delete()
		return (number, number_sid)
	
	def __unicode__(self):
		return '(%s) %s-%s' % (self.area_code, self.prefix, self.line_number)
