"""
config/wsgi.py
The synchronous entry point: `application` is what gunicorn (or mod_wsgi) loads.

WSGI runs one request at a time per worker, which is all this site needs - the
public pages are database reads and the POSTs are a form save plus two emails.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_wsgi_application()
