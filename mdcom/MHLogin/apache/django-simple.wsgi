import os
import sys

django_projects_path = '/path/to/' # path to MHLogin directory, without the MHLogin directory in and of itself
if django_projects_path not in sys.path:
    sys.path.append(django_projects_path)

mhlogin_path = ''.join([django_projects_path,'MHLogin/'])
if mhlogin_path not in sys.path:
    sys.path.append(mhlogin_path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'MHLogin.settings'
os.environ['PYTHON_EGG_CACHE'] = ''.join([mhlogin_path,'/.python-eggs'])

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()

