import os, sys

sys.path.append('/gsf')
sys.path.append('/gsf/gsf/')
sys.path.append('/gsf/api/')

os.environ['DJANGO_SETTINGS_MODULE'] = 'gsf.settings'

import django.core.handlers.wsgi

application = django.core.handlers.wsgi.WSGIHandler()
