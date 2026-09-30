"""
core/views.py
Public site views: pages, the booking form, booking tracking,
review submission and the PWA plumbing.
Routed by: core/urls.py. Renders: templates/*.html.
"""
import logging
import re
from datetime import timedelta
from urllib.parse import quote

from django.conf import settings
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.response import TemplateResponse
from django.utils import timezone

from .forms import ReviewForm
from .models import Booking, BookingStatus, Review, ReviewStatus, SiteSettings, Trip
from .whatsapp import (
    booking_created_message,
    booking_track_confirmed_message,
    booking_track_pending_message,
    send_whatsapp,
)

logger = logging.getLogger(__name__)


def _wa_trip_href(whatsapp, trip_name):
    """Build a WhatsApp deep link that pre-fills a request for one trip.

    Args:
        whatsapp (str): Agency WhatsApp number from SiteSettings.
        trip_name (str): Name of the trip the visitor is looking at.

    Returns:
        str: wa.me URL, or '' when either value is missing.
    """
    number = re.sub(r'\D', '', whatsapp or '')
    if not number or not trip_name:
        return ''
    text = quote(f'أرغب في الحجز في رحلة: {trip_name}')
    return f'https://wa.me/{number}?text={text}'


def _client_ip(request):
    """Best-effort client IP for rate limiting.

    Never trust the left-most X-Forwarded-For entry: that is client-supplied
    and trivially spoofable to dodge the limit. Behind a single trusted proxy
    the real client address is the right-most entry the proxy appended.

    Args:
        request (HttpRequest): The incoming request.

    Returns:
        str: The caller's IP address, or 'unknown' when the server exposes
            neither REMOTE_ADDR nor a trusted X-Forwarded-For entry.
    """
    if settings.TRUST_X_FORWARDED_FOR:
        forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
        if forwarded:
            candidate = forwarded.rsplit(',', 1)[-1].strip()
            if candidate:
                return candidate
    return request.META.get('REMOTE_ADDR', '') or 'unknown'


def home(request):
    """Render the homepage.

    Shows the active trips and the three most recently published reviews,
    plus the total review count used to decide whether the reviews block
    gets a "see all" button.

    Args:
        request (HttpRequest): The incoming request.

    Returns:
        HttpResponse: home.html rendered with trips and latest_reviews.
    """
    trips = Trip.objects.filter(is_active=True)
    approved = Review.objects.filter(status=ReviewStatus.APPROVED)
    context = {
        'trips': trips,
        'latest_reviews': approved.select_related('trip').order_by(
            '-approved_at', '-created_at'
        )[:3],
        'reviews_count': approved.count(),
        'book_title': 'رحلات السنة',
        'book_sub': 'جميع رحلات الحج والعمرة مرتبة حسب موعد الانطلاق، اضغط على أي رحلة لعرض برنامج السير بالتفصيل من الخروج حتى العودة.',
    }
    return render(request, 'home.html', context)


def reviews_list(request):
    """Render the paginated list of approved reviews.

    Args:
        request (HttpRequest): Carries an optional ?page= query parameter.

    Returns:
        HttpResponse: reviews.html with 12 reviews per page.
    """
    reviews = Review.objects.filter(status=ReviewStatus.APPROVED).order_by('-approved_at', '-created_at')
    paginator = Paginator(reviews, 12)
    page = paginator.get_page(request.GET.get('page'))
    context = {
        'reviews': page.object_list,
        'page_obj': page,
        'paginator': paginator,
    }
    return render(request, 'reviews.html', context)


def review_submit(request):
    """Accept a customer review and queue it for moderation.

    GET renders the empty form. On a valid POST the review is stored as
    PENDING (never published directly) together with the submitter's IP.

    Anti-spam, in order of cost:
        1. a honeypot field rejected in ReviewForm.clean_website
        2. one submission per IP per 24h, enforced below

    Args:
        request (HttpRequest): GET renders, POST submits.

    Returns:
        HttpResponse: the form, or a redirect to the reviews list.
    """
    if request.method == 'POST':
        ip = _client_ip(request)
        form = ReviewForm(request.POST, request.FILES)
        if form.is_valid():
            # Rate limit: one review per IP per 24h. A blocked submission
            # still shows the thank-you message so a bot learns nothing.
            rate_limited = Review.objects.filter(
                ip_address=ip,
                created_at__gte=timezone.now() - timedelta(hours=24),
            ).exists()
            if not rate_limited:
                review = form.save(commit=False)
                review.status = ReviewStatus.PENDING
                review.ip_address = ip
                review.save()
            messages.success(
                request,
                'شكراً لك! تم استلام رأيك وسيتم مراجعته قريباً قبل النشر.',
            )
            return redirect('core:reviews')
    else:
        form = ReviewForm()
    context = {'form': form}
    return render(request, 'review_submit.html', context)


def trips_list(request):
    """Render every active trip, optionally filtered by a search term.

    Args:
        request (HttpRequest): Optional ?q= term matched against the trip
            name and description.

    Returns:
        HttpResponse: trips.html with the matching active trips.
    """
    query = (request.GET.get('q') or '').strip()
    trips = Trip.objects.filter(is_active=True)
    if query:
        trips = trips.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )
    context = {
        'trips': trips,
        'trip_search_query': query,
    }
    return render(request, 'trips.html', context)


def trip_detail(request, slug):
    """Render one trip, with related trips and a WhatsApp booking link.

    Args:
        request (HttpRequest): The incoming request.
        slug (str): URL slug of the trip.

    Returns:
        HttpResponse: trip_detail.html; 404 for a missing or hidden trip,
            because get_object_or_404 filters on is_active=True so staff can
            unpublish a trip without leaving it indexable.
    """
    trip = get_object_or_404(Trip, slug=slug, is_active=True)
    settings = SiteSettings.load()
    context = {
        'trip': trip,
        'related_trips': Trip.objects.filter(is_active=True).exclude(pk=trip.pk)[:3],
        'wa_trip_href': _wa_trip_href(settings.whatsapp, trip.name),
    }
    return render(request, 'trip_detail.html', context)


def about(request):
    """Render the static about page.

    Args:
        request (HttpRequest): The incoming request.

    Returns:
        HttpResponse: about.html.
    """
    return render(request, 'about.html')


def _booking_summary_lines(booking):
    """Render a booking as the plain-text body shared by both emails.

    Args:
        booking (Booking): The booking to summarise.

    Returns:
        str: Newline-separated Arabic field list, reused by the admin
            notification and the customer acknowledgement so the two can
            never drift apart.
    """
    created = timezone.localtime(booking.created_at).strftime('%Y-%m-%d %H:%M')
    lines = [
        f'رقم الحجز: {booking.reference_code}',
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
    """Email the agency about a new booking and acknowledge the customer.

    The admin address comes from settings.ADMIN_NOTIFICATION_EMAIL and
    falls back to SiteSettings.email. Both sends are best-effort: a mail
    failure is logged and swallowed, because losing the booking request
    itself would be far worse than losing the notification.

    Args:
        booking (Booking): The booking that was just saved.

    Returns:
        None
    """
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
    """Public booking request form.

    Validated by hand rather than with a Form class because the markup is
    hand-rolled in booking.html and only name/phone are mandatory.

    On success the booking is stored, both emails are sent and a WhatsApp
    deep link is produced for the visitor.

    Args:
        request (HttpRequest): POST carries the hu_* fields; GET may carry
            ?trip=<id> to preselect a trip.

    Returns:
        HttpResponse: booking.html with form_msg/form_ok feedback.
    """
    msg = None
    ok = False

    if request.method == 'POST':
        # Manual validation: name and phone are the only required fields.
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
            try:
                send_whatsapp(booking.phone, booking_created_message(booking))
            except Exception:
                logger.exception('فشل إنشاء إشعار واتساب للحجز')

            ok = True
            msg = 'تم استلام طلبك بنجاح، سنتواصل معك في أقرب وقت. جزاكم الله خيراً.'

    trips = Trip.objects.filter(is_active=True)
    # ?trip=<id> preselects a trip for the visitor, e.g. when a trip card
    # links straight into this form.
    preselected = request.GET.get('trip')
    preselected_trip = None
    if preselected and preselected.isdigit():
        preselected_trip = trips.filter(pk=int(preselected)).first()
    context = {
        'trips': trips,
        'preselected_trip': preselected_trip,
        'form_msg': msg,
        'form_ok': ok,
    }
    return render(request, 'booking.html', context)


def _find_booking(q):
    """Look up a booking from whatever the visitor typed into tracking.

    Tried in order, most to least strict:
        1. exact reference code (case-insensitive)
        2. exact phone match
        3. digits-only phone match, so '050 123 4567' finds '0501234567'

    Args:
        q (str): Raw query string from ?q=.

    Returns:
        Booking | None: The most recent match, or None when nothing fits.
    """
    query = (q or '').strip()
    if not query:
        return None
    booking = (
        Booking.objects.filter(reference_code__iexact=query)
        .order_by('-created_at')
        .first()
    )
    if booking:
        return booking
    booking = (
        Booking.objects.filter(phone__iexact=query)
        .order_by('-created_at')
        .first()
    )
    if booking:
        return booking
    # Last resort: compare digit-only phone numbers so cosmetic
    # formatting differences do not break tracking.
    digits = re.sub(r'\D', '', query)
    if digits:
        for candidate in Booking.objects.order_by('-created_at').only('pk', 'phone'):
            if re.sub(r'\D', '', candidate.phone or '') == digits:
                return candidate
    return None


def track_booking(request):
    """Show where a booking request stands.

    Args:
        request (HttpRequest): Carries ?q= (reference code or phone).

    Returns:
        HttpResponse: track_booking.html; `not_found` drives the error
            message and the two wa_*_msg values pre-fill the WhatsApp button
            for the visitor to send from their own phone.
    """
    q = (request.GET.get('q') or '').strip()
    booking = _find_booking(q) if q else None
    context = {
        'booking': booking,
        'not_found': bool(q) and booking is None,
        'q': q,
        'track_statuses': BookingStatus.values,
        'wa_confirmed_msg': booking_track_confirmed_message(booking) if booking else '',
        'wa_pending_msg': booking_track_pending_message(booking) if booking else '',
    }
    return render(request, 'track_booking.html', context)


def not_found(request, exception=None):
    """Render the branded 404 page.

    Wired as handler404 in config/urls.py.

    Args:
        request (HttpRequest): The incoming request.
        exception (Exception): The exception Django raised, if any.

    Returns:
        HttpResponse: 404.html with a 404 status.
    """
    return render(request, '404.html', status=404)


def service_worker(request):
    """Serve sw.js from the source tree with no-cache headers.

    Served by a view rather than from staticfiles so the worker always
    reaches the browser: Service-Worker-Allowed widens its scope to '/',
    and no-cache makes the browser re-check it on every load, which is what
    lets a VERSION bump inside the file actually roll out.

    Args:
        request (HttpRequest): The incoming request.

    Returns:
        HttpResponse: the worker script as application/javascript.
    """
    sw_path = settings.BASE_DIR / 'static' / 'sw.js'
    body = sw_path.read_text(encoding='utf-8') if sw_path.exists() else ''
    response = HttpResponse(body, content_type='application/javascript')
    response['Service-Worker-Allowed'] = '/'
    response['Cache-Control'] = 'no-cache'
    return response


def offline(request):
    """Render the PWA offline fallback page.

    Args:
        request (HttpRequest): The incoming request.

    Returns:
        HttpResponse: offline.html.
    """
    return render(request, 'offline.html')


def robots_txt(request):
    """Serve /robots.txt from templates/robots.txt.

    Args:
        request (HttpRequest): The incoming request.

    Returns:
        TemplateResponse: the robots file as text/plain.
    """
    return TemplateResponse(request, 'robots.txt', content_type='text/plain')
