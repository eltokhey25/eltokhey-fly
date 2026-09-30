"""
core/apps.py
App configuration for the public site.
Registered in config/settings.py -> INSTALLED_APPS as 'core'.
"""
from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Public site app: trips, bookings, reviews and SEO."""

    name = 'core'
    verbose_name = 'الحج والعمرة'