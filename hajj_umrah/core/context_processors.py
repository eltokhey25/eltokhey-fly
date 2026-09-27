"""
core/context_processors.py
Injects site-wide template context (company details, phone/WhatsApp links and
the review badge count) into every public page.
Registered in: config/settings.py -> TEMPLATES -> context_processors.
"""
import re
from urllib.parse import quote

from .models import Review, ReviewStatus, SiteSettings, TripType


def _digits(value):
    """Keep only digits and a leading '+' so the value is safe in a tel: URL.

    Args:
        value (str): Phone number as typed by the site owner.

    Returns:
        str: e.g. '+966501234567'; empty string for empty input.
    """
    return re.sub(r'[^\d+]', '', value or '')


def _wa_href(whatsapp):
    """Build the header's WhatsApp deep link with a default inquiry message.

    Args:
        whatsapp (str): WhatsApp number as configured in SiteSettings.

    Returns:
        str: wa.me URL, or '' when no number is configured so the template can
             hide the link entirely.
    """
    number = re.sub(r'\D', '', whatsapp or '')
    if not number:
        return ''
    text = quote('أهلًا، أرغب في الاستفسار عن رحلات الحج والعمرة المتاحة حاليًا')
    return f'https://wa.me/{number}?text={text}'


def site_settings(request):
    """Provide the context every public template relies on.

    Args:
        request (HttpRequest): Unused beyond the processor contract; kept so
            the signature matches Django's context-processor protocol.

    Returns:
        dict: Keys bound in config/settings.py:
            - site: the singleton SiteSettings row
            - trip_types: [{'slug', 'name'}] for filter chips
            - phone_tel_href / whatsapp_href: ready-made header links
            - pending_reviews_count: badge number for the dashboard
    """
    # load() caches the singleton row and creates it on first access.
    settings = SiteSettings.load()
    return {
        'site': settings,
        'trip_types': [
            {'slug': t.value, 'name': t.label}
            for t in TripType
        ],
        'phone_tel_href': 'tel:' + _digits(settings.phone) if settings.phone else None,
        'whatsapp_href': _wa_href(settings.whatsapp),
        # Cheap COUNT for the "reviews awaiting moderation" badge.
        'pending_reviews_count': Review.objects.filter(
            status=ReviewStatus.PENDING
        ).count(),
    }