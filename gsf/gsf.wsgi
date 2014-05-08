import os, sys

sys.path.append('/web/open-fusion-webapp/gsf')
sys.path.append('/web/open-fusion-webapp/gsf/gsf/')
sys.path.append('/web/open-fusion-webapp/gsf/api/')

os.environ['DJANGO_SETTINGS_MODULE'] = 'gsf.settings'

import django.core.handlers.wsgi

application = django.core.handlers.wsgi.WSGIHandler()
