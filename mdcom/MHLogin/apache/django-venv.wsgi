
import site
import sys
import copy

from os import environ
from os.path import join, dirname, abspath, exists

base = dirname(dirname(abspath(__file__)))
origpath = copy.copy(sys.path)
try:
    sys.path[0:0] = [dirname(base)]  # prepend mdcom dir to path before import
    from MHLogin.apache._django_venv import BASE_VENV
    site_packages = join(BASE_VENV, 'lib', 'python%s' % sys.version[:3], 'site-packages')
except (Exception, ImportError) as e:
    site_packages = join(base, 'virtualenv', 'lib', 'python%s' % sys.version[:3], 'site-packages')
    sys.stderr.write("Optional BASE_VENV not used, using default: %s\n" % site_packages)
finally:
    sys.path = origpath  # restore path
    
assert(exists(site_packages)), "site_packages: %s does not exist\n" % site_packages

prev_sys_path = list(sys.path)

site.addsitedir(site_packages)
sys.real_prefix = sys.prefix
sys.prefix = base

new_sys_path = []
for item in list(sys.path):
    if item not in prev_sys_path:
        new_sys_path.append(item)
        sys.path.remove(item)
sys.path[:0] = new_sys_path

django_projects_path = dirname(base)
if django_projects_path not in sys.path:
    sys.path.append(django_projects_path)

mhlogin_path = join(django_projects_path, 'MHLogin')
if mhlogin_path not in sys.path:
    sys.path.append(mhlogin_path)

environ['DJANGO_SETTINGS_MODULE'] = 'MHLogin.settings'
environ['PYTHON_EGG_CACHE'] = join(mhlogin_path, '.python-eggs')

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()

