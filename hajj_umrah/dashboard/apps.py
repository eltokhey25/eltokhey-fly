"""
dashboard/apps.py
App configuration for the staff dashboard.
Registered in config/settings.py -> INSTALLED_APPS as 'dashboard'.
"""
from django.apps import AppConfig


class DashboardConfig(AppConfig):
    """Staff dashboard app: content, bookings, reviews, media and users."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dashboard'
    verbose_name = 'لوحة التحكم'