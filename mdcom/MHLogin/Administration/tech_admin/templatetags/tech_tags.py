
from django.template import Library, Node, TemplateSyntaxError
from django.contrib.auth.models import User

from MHLogin.Administration.tech_admin.utils import is_techadmin, is_readonly_admin

register = Library()


class GetTechMenuVarNode(Node):
	"""
	Get tech menu true/false value

	Syntax::

		{% get_tech_menu_var as context_name %}

	Example usage::

		{% get_tech_menu_var as some_var %}
	"""
	def __init__(self, ctxvar):
		self.ctxvar = ctxvar

	def render(self, context):
		if (self.ctxvar in context):
			raise TemplateSyntaxError("Template variable '%s' already declared "
				"in this template context" % self.ctxvar)
		context[self.ctxvar] = 'false'
		if 'sender_types' in context:
			# show tech menu if Administrator or tech-admin or read-only admin
			if 'Administrator' in context['sender_types']:
				context[self.ctxvar] = 'true'
			else:
				if 'MHLUser' in context['sender_types']:
					user = User.objects.get(id=context['sender_types']['MHLUser'])
					if is_techadmin(user) or is_readonly_admin(user):
						context[self.ctxvar] = 'true'
		return ''


@register.tag
def get_tech_menu_var(parser, token):
	""" template format: {% get_tech_menu_var as some_var %} """
	contents = token.split_contents()
	if len(contents) != 3 or contents[-2] != 'as': 
		raise TemplateSyntaxError("template format is: {% get_tech_menu_var as some_var %}")

	return GetTechMenuVarNode(contents[-1])


"""
TODO: add more template tags for Sales and mention to china team  
about adding template tags to their menu_template_xyz.html  

Good docs:

https://docs.djangoproject.com/en/dev/howto/custom-template-tags/#writing-custom-template-tags
http://codespatter.com/2009/01/22/how-to-write-django-template-tags/


class TechMenuNode(Node):
	def render(self, context):
		menu = ""
		if 'Administrator' in context['sender_types'] or is_techadmin(context['user']) or \
				is_readonly_admin(context['user']):
			menu = "<li><a href='/dcAdmin/tech_admin/'>Admin</a></li>"
		return menu


@register.tag
def tech_admin_menu(parser, token):
	return TechMenuNode()

"""

