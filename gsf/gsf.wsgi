import os, sys

sys.path.append('/web/gsf')
sys.path.append('/web/gsf/gsf/')

os.environ['DJANGO_SETTINGS_MODULE'] = 'gsf.settings'

import django.core.handlers.wsgi

application = django.core.handlers.wsgi.WSGIHandler()
