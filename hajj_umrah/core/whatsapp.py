import logging
import re
from urllib.parse import quote

logger = logging.getLogger(__name__)


def normalize_phone(phone):
    return re.sub(r'\D', '', phone or '')


def build_whatsapp_url(phone, message):
    number = normalize_phone(phone)
    if not number:
        return ''
    return f'https://wa.me/{number}?text={quote(message)}'


def send_whatsapp(phone, message):
    """Send a WhatsApp notification to a customer.

    No WhatsApp Business/Cloud API is connected yet, so this builds a wa.me
    deep link (openable on the phone/browser) and logs it. Once a real
    provider (Twilio, WhatsApp Cloud API…) is configured, wire it up here —
    every notification in the project funnels through this one function so
    the provider swap stays invisible to the rest of the code.
    """
    url = build_whatsapp_url(phone, message)
    if not url:
        return ''
    logger.info('WhatsApp notification -> %s : %s', phone, url)
    return url


def booking_created_message(booking):
    trip = booking.trip_label or 'غير محددة'
    return (
        f'مرحباً {booking.name}، تم استلام طلب حجزك رقم {booking.reference_code} '
        f'لرحلة {trip}. سنتواصل معك للتأكيد خلال 24 ساعة.'
    )


def booking_confirmed_message(booking):
    trip = booking.trip_label or 'غير محددة'
    return f'✅ تم تأكيد حجزك رقم {booking.reference_code} لرحلة {trip}'


def booking_rejected_message(booking):
    return f'❌ نأسف، لم نتمكن من تأكيد حجزك رقم {booking.reference_code}'


def booking_track_confirmed_message(booking):
    trip = booking.trip_label or 'غير محدد'
    return (
        'السلام عليكم،\n'
        'أتابع بخصوص حجزي المؤكد:\n\n'
        f'🎫 رقم الحجز: {booking.reference_code}\n'
        f'👤 الاسم: {booking.name}\n'
        f'🕋 الرحلة: {trip}\n'
        f'👥 عدد الأفراد: {booking.people}\n'
        f'📞 رقم التواصل: {booking.phone}\n\n'
        'برجاء تزويدي بتفاصيل الدفع والمواعيد النهائية.\n'
        'شكراً لكم.'
    )


def booking_track_pending_message(booking):
    return (
        'السلام عليكم،\n'
        'بتابع بخصوص حجزي قيد المراجعة:\n\n'
        f'🎫 رقم الحجز: {booking.reference_code}\n'
        f'👤 الاسم: {booking.name}\n\n'
        'برجاء إفادتي بحالة الحجز.'
    )