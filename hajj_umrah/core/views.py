import re
from urllib.parse import quote

from django.core.mail import send_mail
from django.http import Http404
from django.shortcuts import get_object_or_404, render

from .models import Booking, SiteSettings, Trip


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
            try:
                people = max(1, int(request.POST.get('hu_people', 1)))
            except (TypeError, ValueError):
                people = 1
            notes = request.POST.get('hu_notes', '').strip()

            Booking.objects.create(
                name=name,
                phone=phone,
                trip_label=trip_label,
                trip_type=trip_type,
                people=people,
                notes=notes,
            )

            admin_email = SiteSettings.load().email or 'ahmedeltokhey55@gmail.com'
            subject = f'طلب حجز جديد — {name}'
            body = (
                'طلب حجز جديد من الموقع:\n\n'
                f'الاسم: {name}\n'
                f'الهاتف: {phone}\n'
                f'الرحلة: {trip_label}\n'
                f'النوع: {trip_type}\n'
                f'عدد الأفراد: {people}\n'
                f'ملاحظات: {notes}\n'
            )
            try:
                send_mail(subject, body, None, [admin_email], fail_silently=True)
            except Exception:
                pass

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