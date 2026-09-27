"""
config/asgi.py
The asynchronous entry point: `application` is what uvicorn/daphne loads.

Nothing in the project requires ASGI today; it is here so an async server can be
dropped in later without touching a single view. See DEPLOY.md.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_asgi_application()
