
from django.template import Library, Node, TemplateSyntaxError
from django.contrib.auth.models import User
from MHLogin.MHLOrganization.utils import can_user_manage_org_module

register = Library()

class GetOrgMenuVarNode(Node):
	"""
	Get org menu true/false value

	Syntax::

		{% get_org_menu_var as context_name %}

	Example usage::

		{% get_org_menu_var as org_menu %}
	"""
	def __init__(self, ctxvar):
		self.ctxvar = ctxvar

	def render(self, context):
		if (self.ctxvar in context):
			raise TemplateSyntaxError("Template variable '%s' already declared "
				"in this template context" % self.ctxvar)
		context[self.ctxvar] = 'false'
		if 'sender_types' in context:
			ret_data = can_user_manage_org_module(context['sender_types']['MHLUser'])
			mgrs = ret_data["Office_Manager"]
			if ret_data["can_manage_org"]:
				context[self.ctxvar] = 'true'
		return ''

@register.tag
def get_org_menu_var(parser, token):
	""" template format: {% get_org_menu_var as org_menu %} """
	contents = token.split_contents()
	if len(contents) != 3 or contents[-2] != 'as': 
		raise TemplateSyntaxError("template format is: {% get_org_menu_var as some_var %}")

	return GetOrgMenuVarNode(contents[-1])
