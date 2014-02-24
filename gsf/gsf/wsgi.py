"""
WSGI config for gsf project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/howto/deployment/wsgi/
"""

import os, sys

sys.path.append('/web/open-fusion-webapp/gsf')
sys.path.append('/web/open-fusion-webapp/gsf/gsf/')

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gsf.settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
