import os
import sys

sys.path.append('/home/sandy/django')
sys.path.append('/home/sandy/django/dss')
os.environ['DJANGO_SETTINGS_MODULE'] = 'dss.settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
