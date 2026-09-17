import re
from urllib.parse import quote

from .models import Review, ReviewStatus, SiteSettings, TripType


def _digits(value):
    return re.sub(r'[^\d+]', '', value or '')


def _wa_href(whatsapp):
    number = re.sub(r'\D', '', whatsapp or '')
    if not number:
        return ''
    text = quote('أهلًا، أرغب في الاستفسار عن رحلات الحج والعمرة المتاحة حاليًا')
    return f'https://wa.me/{number}?text={text}'


def site_settings(request):
    settings = SiteSettings.load()
    return {
        'site': settings,
        'trip_types': [
            {'slug': t.value, 'name': t.label}
            for t in TripType
        ],
        'phone_tel_href': 'tel:' + _digits(settings.phone) if settings.phone else None,
        'whatsapp_href': _wa_href(settings.whatsapp),
        'pending_reviews_count': Review.objects.filter(
            status=ReviewStatus.PENDING
        ).count(),
    }