
"""
 Base class admin site for TechUser admin, this may also be used as a general purpose
 admin tool once tech admin features are fully implemented.  Tech Admin allows admin
 personalized access to Hospital System groups without explicitly assigning individual
 permissions which is needed in Django's Admin model if the user is not super-user.
"""

from django.conf import settings
from django.contrib.admin import AdminSite
from django.contrib.admin.widgets import RelatedFieldWidgetWrapper
from django.db.models.base import ModelBase
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

from MHLogin.Administration.tech_admin.options import TechAdmin
from MHLogin.Administration.tech_admin.utils import is_techadmin, monkeypatch_method


class TechAdminSite(AdminSite):
	""" MHLogin custom tech admin site, subset of default django admin site with
	special permissions for technical users of various Hospital Systems.  Depending
	on groups and permissions they will be able to add/delete/modify users and settings
	depending on which group they are in.  Work in progress class/modules are in flux.
	"""

	# use our custom index template which doesn't show history
	index_template = "tech_admin/index.html"

	def __init__(self, name=None, app_name='admin', root_path='/tech_admin/'):
		super(TechAdminSite, self).__init__(name, app_name)
		self.root_path = root_path

	def has_permission(self, request):
		"""
		:returns: True if user is active and has either superuser or techadmin
		access.  If tech-admin then permission model is used to determine what
		models they can view/delete/modify.
		"""
		return request.user.is_active and (request.user.is_superuser or
										request.user.is_staff or
										is_techadmin(request.user))

	def password_change(self, request):
		"""
		Override Admin Site's password_change for the admin, we need to pass in our custom
		Form.  Unfortunately AdminSite does not have a password_change_form variable in 
		self as does the UserAdmins do, so redirect to our password form
		"""
		from MHLogin.MHLUsers.views import change_password
		from django.core.urlresolvers import resolve
		view = resolve(request.path).namespace + ':password_change_done'
		return change_password(request, redirect_view=view)

	# override base class register and allow setting templates
	def register(self, model_or_iterable, admin_class=None, **options):
		templates = options.pop('templates',  # if not there set default for tech_admin
							{'chg_form_tmpl': 'tech_admin/change_form.html',
							'chg_list_tmpl': 'tech_admin/change_list.html',
							'chg_pass_tmpl': 'tech_admin/change_password.html'})
		# call parent class register and then setup templates if using
		admin_class = TechAdmin if admin_class == None else admin_class
		super(TechAdminSite, self).register(model_or_iterable, admin_class, **options)

		# after adminmodel instantiated in parent function set custom templates if using
		if templates != None:
			change_form_template = templates.get('chg_form_tmpl', None)
			change_list_template = templates.get('chg_list_tmpl', None)
			change_pass_template = templates.get('chg_pass_tmpl', None)

			# can be a list check if not, if not make it so
			if isinstance(model_or_iterable, ModelBase):
				model_or_iterable = [model_or_iterable]

			for m in model_or_iterable:
				# get the admin model for each model and set their template(s)
				self._registry[m].change_form_template = change_form_template
				self._registry[m].change_list_template = change_list_template
				self._registry[m].change_user_password_template = change_pass_template


# create the TechAdmin site
tech_admin_site = TechAdminSite(app_name='tech_admin', root_path='/dcAdmin/tech_admin/', 
							name='admin')


def register(model_or_iterable, klass=None):
	""" Helper registers both TechAdmin and regular admin if we still decide to use.
		When we remove support for regular admin we can just comment out the one line
		below instead of everywhere we used to register admins.
	"""
	from django.contrib import admin

	tech_admin_site.register(model_or_iterable, klass)
	admin.site.register(model_or_iterable, klass)


from MHLogin.Administration.tech_admin.tech_admin import tech_admin_register
tech_admin_register()
