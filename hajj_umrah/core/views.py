import logging
import re
from urllib.parse import quote

from django.conf import settings
from django.core.mail import send_mail
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.template.response import TemplateResponse
from django.utils import timezone

from .models import Booking, SiteSettings, Trip

logger = logging.getLogger(__name__)


def _wa_trip_href(whatsapp, trip_name):
    number = re.sub(r'\D', '', whatsapp or '')
    if not number or not trip_name:
        return ''
    text = quote(f'أرغب في الحجز في رحلة: {trip_name}')
    return f'https://wa.me/{number}?text={text}'


def home(request):
    trips = Trip.objects.filter(is_active=True)
    context = {
        'trips': trips,
        'book_title': 'رحلات السنة',
        'book_sub': 'جميع رحلات الحج والعمرة مرتبة حسب موعد الانطلاق، اضغط على أي رحلة لعرض برنامج السير بالتفصيل من الخروج حتى العودة.',
    }
    return render(request, 'home.html', context)


def trips_list(request):
    trips = Trip.objects.filter(is_active=True)
    context = {'trips': trips}
    return render(request, 'trips.html', context)


def trip_detail(request, slug):
    trip = get_object_or_404(Trip, slug=slug, is_active=True)
    settings = SiteSettings.load()
    context = {
        'trip': trip,
        'wa_trip_href': _wa_trip_href(settings.whatsapp, trip.name),
    }
    return render(request, 'trip_detail.html', context)


def about(request):
    return render(request, 'about.html')


def _booking_summary_lines(booking):
    created = timezone.localtime(booking.created_at).strftime('%Y-%m-%d %H:%M')
    lines = [
        f'الاسم: {booking.name}',
        f'الهاتف: {booking.phone}',
    ]
    if booking.email:
        lines.append(f'البريد الإلكتروني: {booking.email}')
    lines.extend([
        f'الرحلة / الموعد: {booking.trip_label or "غير محدد"}',
        f'نوع الرحلة: {booking.trip_type or "غير محدد"}',
        f'عدد الأفراد: {booking.people}',
        f'ملاحظات: {booking.notes or "لا توجد"}',
        f'تاريخ الطلب: {created}',
    ])
    return '\n'.join(lines)


def _send_booking_emails(booking):
    admin_email = settings.ADMIN_NOTIFICATION_EMAIL or SiteSettings.load().email

    summary = _booking_summary_lines(booking)
    if admin_email:
        admin_subject = f'حجز جديد: {booking.trip_label or "بدون رحلة"} - {booking.name}'
        admin_body = f'طلب حجز جديد من الموقع:\n\n{summary}\n'
        try:
            send_mail(admin_subject, admin_body, None, [admin_email], fail_silently=True)
        except Exception:
            logger.exception('فشل إرسال إشعار الحجز إلى المشرف')

    if booking.email:
        customer_subject = 'تم استلام طلب الحجز الخاص بك'
        customer_body = (
            f'مرحباً {booking.name}،\n\n'
            'شكراً لتواصلك معنا. لقد استلمنا طلبك بنجاح، وسيتواصل معك فريقنا في أقرب وقت '
            'لتأكيد تفاصيل الحجز.\n\n'
            'ملخص طلبك:\n\n'
            f'{summary}\n\n'
            'جزاكم الله خيراً.\n'
            'فريق رحلات الحج والعمرة'
        )
        try:
            send_mail(customer_subject, customer_body, None, [booking.email], fail_silently=True)
        except Exception:
            logger.exception('فشل إرسال تأكيد الحجز إلى العميل')


def booking(request):
    msg = None
    ok = False

    if request.method == 'POST':
        name = request.POST.get('hu_name', '').strip()
        phone = request.POST.get('hu_phone', '').strip()
        if not name or not phone:
            msg = 'من فضلك أدخل الاسم ورقم الهاتف.'
        else:
            trip_label = request.POST.get('hu_departure', '').strip()
            trip_type = request.POST.get('hu_type', '').strip()
            email = request.POST.get('hu_email', '').strip()
            try:
                people = max(1, int(request.POST.get('hu_people', 1)))
            except (TypeError, ValueError):
                people = 1
            notes = request.POST.get('hu_notes', '').strip()

            booking = Booking.objects.create(
                name=name,
                phone=phone,
                email=email,
                trip_label=trip_label,
                trip_type=trip_type,
                people=people,
                notes=notes,
            )
            _send_booking_emails(booking)

            ok = True
            msg = 'تم استلام طلبك بنجاح، سنتواصل معك في أقرب وقت. جزاكم الله خيراً.'

    trips = Trip.objects.filter(is_active=True)
    context = {
        'trips': trips,
        'form_msg': msg,
        'form_ok': ok,
    }
    return render(request, 'booking.html', context)


def not_found(request, exception=None):
    return render(request, '404.html', status=404)


def robots_txt(request):
    return TemplateResponse(request, 'robots.txt', content_type='text/plain')