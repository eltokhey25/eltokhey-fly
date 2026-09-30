"""
core/__init__.py
The public-facing app: models, public pages, booking and review intake, the
WhatsApp notifications and the sitemap.

Trip, Booking, Review and the SiteSettings singleton live here rather than in
dashboard because the public site reads them too. Staff accounts are Django's
own auth.User — this project defines no custom user model.
"""
