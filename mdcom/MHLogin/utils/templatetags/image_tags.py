# -*- coding: utf-8 -*-
"""
	Based off: (Thanks to  R. BECK)
	http://djangosnippets.org/snippets/2268/

	Simplified without caching.  If we decide to do caching use django's cache in  
	settings.py rather than spippet's fixed /tmp directory as our data is sensitive.  
"""
import re
import base64
import os
import Image
try:
	from cStringIO import StringIO
except ImportError:
	from StringIO import StringIO

from django.conf import settings
from django.template import TemplateSyntaxError, Node, Library, Template

register = Library()

templatevar_re = re.compile("\{\{(.+)\}\}")
media_re = re.compile("\{\{MEDIA_ROOT|MEDIA_URL\}\}")


class InlineImgNode(Node):
	"""
	Image node parser for rendering html inline base64 image

	Examples:
	{% inline_img src="/media/images/002.gif" height="200px" width="200px" alt="{{my_var}}" %}
	{% inline_img src="{{MEDIA_URL}}images/001.jpg" height="200px" width="200px" alt="001" %}
	{% inline_img src="upload/images/logo_corp_264.png" alt="corp" %}
	{% inline_img src="{{MEDIA_URL}}images/001.jpg" width="200px" alt="lala" %}
	{% inline_img src="{{MEDIA_URL}}images/001.jpg" height="200px" width="200px" alt="my image" %}
	{% inline_img src="{{MEDIA_URL}}images/001.jpg" %}
	"""
	def __init__(self, attributes):
		""" Parse out attributes into key/vals used in render """
		self.attrs = {}
		for attr_pair in attributes:
			try:
				k, v = attr_pair.split('=', 1)
			except ValueError, val_err:
				raise TemplateSyntaxError(u"Syntax Error :", val_err)
			self.attrs[k] = v

		if 'src' not in self.attrs:
			raise TemplateSyntaxError(u"You have to specify a non-empty src attribute")

	def get_b64_img(self, img):
		""" Helper to return base64 string representation of image """
		try:
			out = StringIO()
			base64.encode(open(img.filename, 'r'), out)
			content = out.getvalue().replace('\n', '')
		except IOError:
			content = ''
		return content

	def render(self, context):
		""" Set src to base64 of image instead of path and set height/width if present """
		img_path = self.attrs.get('src')
		if media_re.search(img_path):
			img_path = img_path.replace('{{MEDIA_ROOT}}', '').replace('{{MEDIA_URL}}', '')

		img_path = os.path.join(settings.MEDIA_ROOT, img_path.replace('"', ''))
		try:
			img = Image.open(img_path)
			mime = 'image/%s' % img.format
			# grab image's size info if not explicitly set in attributes
			if 'width' not in self.attrs:
				self.attrs['width'] = '%spx' % img.size[0]
			if 'height' not in self.attrs:
				self.attrs['height'] = '%spx' % img.size[1]

			self.attrs['src'] = 'data:%s;base64,%s' % (mime, self.get_b64_img(img))
		except IOError:
			self.attrs['src'] = ''

		for k, v in self.attrs.iteritems():
			if templatevar_re.search(v):
				self.attrs[k] = Template(v).render(context)

		return "<img %s />" % ' '.join(
			['%s=%s' % (k, v if v else '""') for k, v in self.attrs.iteritems()])


@register.tag(name="inline_img")
def do_inline_img(parser, token):
	return InlineImgNode(token.split_contents()[1:])

