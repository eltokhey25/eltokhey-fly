"""
core/whatsapp.py
WhatsApp notification helpers: phone normalisation, deep-link building and the
Arabic message templates sent at each booking status change.
Used by: core/views.py (booking + tracking), dashboard/views.py (confirm/reject).
"""
import logging
import re
from urllib.parse import quote

# Module-level logger; named after the module so messages are attributable.
logger = logging.getLogger(__name__)


def normalize_phone(phone):
    """Strip every non-digit character from a phone number.

    Args:
        phone (str): Raw phone number in any format (spaces, dashes, + prefix).

    Returns:
        str: Digits only, e.g. '+966 50 123 4567' -> '966501234567'.
             Empty string when the input holds no digits.
    """
    return re.sub(r'\D', '', phone or '')


def build_whatsapp_url(phone, message):
    """Build a click-to-chat wa.me deep link with a prefilled message.

    Args:
        phone (str): Destination number in any format.
        message (str): Prefilled Arabic body; URL-encoded automatically.

    Returns:
        str: Full wa.me URL, or '' when the number has no digits (nothing to
             link to, so the caller can skip the notification).
    """
    number = normalize_phone(phone)
    if not number:
        return ''
    # quote() percent-encodes the Arabic text and newlines for the query string.
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
    """Message sent to the customer the moment a booking request is received.

    Args:
        booking (Booking): The freshly saved booking.

    Returns:
        str: Arabic confirmation-of-receipt with the reference code and the
             24-hour follow-up promise.
    """
    trip = booking.trip_label or 'غير محددة'
    return (
        f'مرحباً {booking.name}، تم استلام طلب حجزك رقم {booking.reference_code} '
        f'لرحلة {trip}. سنتواصل معك للتأكيد خلال 24 ساعة.'
    )


def booking_confirmed_message(booking):
    """Short message sent when staff confirm a booking.

    Args:
        booking (Booking): The confirmed booking.

    Returns:
        str: One-line Arabic confirmation.
    """
    trip = booking.trip_label or 'غير محددة'
    return f'✅ تم تأكيد حجزك رقم {booking.reference_code} لرحلة {trip}'


def booking_rejected_message(booking):
    """Message sent when staff decline a booking request.

    Args:
        booking (Booking): The rejected booking.

    Returns:
        str: One-line Arabic apology carrying the reference code.
    """
    return f'❌ نأسف، لم نتمكن من تأكيد حجزك رقم {booking.reference_code}'


def booking_track_confirmed_message(booking):
    """Prefilled message behind the WhatsApp button on the tracking page.

    Used when the tracked booking is confirmed: it restates every detail the
    customer needs so staff do not have to re-collect them over the phone.

    Args:
        booking (Booking): The booking being tracked.

    Returns:
        str: Multi-line Arabic message with reference, name, trip, party size
             and phone number.
    """
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
    """Prefilled message for a booking that is still under review.

    Args:
        booking (Booking): The booking being tracked.

    Returns:
        str: Short multi-line Arabic follow-up message.
    """
    return (
        'السلام عليكم،\n'
        'بتابع بخصوص حجزي قيد المراجعة:\n\n'
        f'🎫 رقم الحجز: {booking.reference_code}\n'
        f'👤 الاسم: {booking.name}\n\n'
        'برجاء إفادتي بحالة الحجز.'
    )