"""
config/wsgi.py
The synchronous entry point: `application` is what gunicorn (or mod_wsgi) loads.

WSGI runs one request at a time per worker, which is all this site needs - the
only slow thing in it is the AI chatbot, and that call already returns a cached
or fallback reply rather than blocking a queue.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_wsgi_application()
