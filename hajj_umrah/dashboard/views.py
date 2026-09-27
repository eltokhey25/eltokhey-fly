"""
dashboard/views.py
Every staff-facing view: the overview, trip/booking/review management,
site settings, the media library, user administration and the preview.
Routed by: dashboard/urls.py. Access is gated per view by the decorators
in dashboard/permissions.py (staff_required / superuser_required).
"""
from datetime import timedelta
import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, logout
from django.contrib.auth.views import LoginView
from django.core.exceptions import PermissionDenied
from django.db.models import Q, Sum
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from core.models import Booking, BookingStatus, Review, ReviewStatus, SiteSettings, Trip
from core.whatsapp import (
    booking_confirmed_message,
    booking_created_message,
    booking_rejected_message,
    build_whatsapp_url,
    send_whatsapp,
)

from .forms import (
    BookingForm,
    DashboardLoginForm,
    MediaForm,
    SettingsForm,
    TripForm,
    UserForm,
)
from .models import MediaFile
from .permissions import staff_required, superuser_required

User = get_user_model()

logger = logging.getLogger(__name__)

# Homepage sections the dashboard can reorder, in their default order.
SECTION_SLUGS = ['hero', 'trips', 'why', 'cta']
SECTION_LABELS = {
    'hero': 'الغلاف الرئيسي (Hero)',
    'trips': 'قسم الرحلات',
    'why': 'لماذا تختارنا',
    'cta': 'جاهز تبدأ رحلتك',
}


def permission_denied(request, exception=None):
    """Render the branded 403 page.

    Wired as handler403 in config/urls.py, so it also catches a
    PermissionDenied raised anywhere inside the dashboard.

    Args:
        request (HttpRequest): The rejected request.
        exception (PermissionDenied): The exception raised, if any.

    Returns:
        HttpResponse: dashboard/403.html with a 403 status.
    """
    return render(request, 'dashboard/403.html', status=403)


def service_worker(request):
    """Serve dashboard-sw.js scoped to /dashboard/.

    Args:
        request (HttpRequest): The incoming request.

    Returns:
        HttpResponse: the worker script, with no-cache headers and a
            Service-Worker-Allowed scope of '/dashboard/' so it cannot
            control the public site.
    """
    sw_path = settings.BASE_DIR / 'static' / 'dashboard-sw.js'
    body = sw_path.read_text(encoding='utf-8') if sw_path.exists() else ''
    response = HttpResponse(body, content_type='application/javascript')
    response['Service-Worker-Allowed'] = '/dashboard/'
    response['Cache-Control'] = 'no-cache'
    return response


def offline(request):
    """Render the dashboard offline fallback.

    Args:
        request (HttpRequest): The incoming request.

    Returns:
        HttpResponse: dashboard/offline.html.
    """
    return render(request, 'dashboard/offline.html')


@staff_required
def overview(request):
    """Render the dashboard home: counters, recent bookings, a price chart.

    Args:
        request (HttpRequest): The incoming request.

    Returns:
        HttpResponse: dashboard/overview.html.
    """
    today = timezone.localdate()
    settings = SiteSettings.load()

    trips = Trip.objects.filter(is_active=True)
    upcoming = trips.filter(departure__gte=today).count()
    active_count = trips.count()

    bookings = Booking.objects.all()
    last_30 = bookings.filter(created_at__date__gte=today - timedelta(days=30)).count()

    remaining_sum = Trip.objects.aggregate(s=Sum('remaining'))['s'] or 0
    media_count = MediaFile.objects.count()

    chart_trips = list(trips.order_by('departure'))[:6]
    chart_data = []
    price_values = [
        int(t.price) for t in chart_trips
        if (t.price or '').strip().isdigit()
    ]
    price_max = max(price_values) if price_values else 1
    for trip in chart_trips:
        raw = (trip.price or '').strip()
        if raw.isdigit():
            val = int(raw)
            chart_data.append({
                'name': trip.name,
                'value': f'{val:,}',
                'pct': int(val / price_max * 100),
            })
        else:
            chart_data.append({'name': trip.name, 'value': raw, 'pct': None})

    trip_types = {
        'hajj': Trip.objects.filter(trip_type='hajj').count(),
        'umrah': Trip.objects.filter(trip_type='umrah').count(),
        'ramadan': Trip.objects.filter(trip_type='ramadan').count(),
    }

    context = {
        'settings': settings,
        'active_count': active_count,
        'upcoming_count': upcoming,
        'bookings_total': bookings.count(),
        'bookings_30': last_30,
        'remaining_sum': remaining_sum,
        'media_count': media_count,
        'latest_bookings': bookings[:6],
        'chart_data': chart_data,
        'trip_types': trip_types,
        'page': 'overview',
    }
    return render(request, 'dashboard/overview.html', context)


# --------------------------------------------------------------------------
# Trips
# --------------------------------------------------------------------------
@staff_required
def trip_list(request):
    """List trips with search plus active/hidden and type filters.

    Args:
        request (HttpRequest): Optional ?q=, ?stock= and ?type= filters.

    Returns:
        HttpResponse: dashboard/trips/list.html.
    """
    query = request.GET.get('q', '').strip()
    stock = request.GET.get('stock', '')
    ttype = request.GET.get('type', '')

    trips = Trip.objects.all()
    if query:
        trips = trips.filter(name__icontains=query)
    if ttype:
        trips = trips.filter(trip_type=ttype)
    if stock == 'available':
        trips = trips.filter(is_active=True)
    elif stock == 'hidden':
        trips = trips.filter(is_active=False)
    elif stock == 'full':
        trips = trips.filter(remaining=0)

    context = {
        'trips': trips.order_by('order', '-created_at'),
        'q': query,
        'filter_type': ttype,
        'filter_stock': stock,
        'trip_types': [
            ('', 'كل الأنواع'),
            ('hajj', 'الحج'),
            ('umrah', 'العمرة'),
            ('ramadan', 'عمرة رمضان'),
        ],
        'page': 'trips',
    }
    return render(request, 'dashboard/trips/list.html', context)


@staff_required
def trip_create(request):
    """Create a trip from the dashboard.

    Args:
        request (HttpRequest): GET renders the form, POST saves.

    Returns:
        HttpResponse: the form, or a redirect to the trip list.
    """
    form = TripForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        trip = form.save()
        if trip.is_active:
            messages.success(request, f'تمت إضافة الرحلة «{trip.name}» ونشرها على الموقع.')
        else:
            messages.success(request, f'تمت إضافة الرحلة «{trip.name}» وستظهر على الموقع بعد تفعيلها.')
        return redirect('dashboard:trip_edit', slug=trip.slug)
    context = {'form': form, 'title': 'إضافة رحلة جديدة', 'page': 'trips'}
    return render(request, 'dashboard/trips/form.html', context)


@staff_required
def trip_edit(request, slug):
    """Edit an existing trip, keyed by its public slug.

    Args:
        request (HttpRequest): GET renders the form, POST saves.
        slug (str): Slug of the trip to edit.

    Returns:
        HttpResponse: the form, or a redirect to the trip list.
    """
    trip = get_object_or_404(Trip, slug=slug)
    form = TripForm(request.POST or None, request.FILES or None, instance=trip)
    if request.method == 'POST' and form.is_valid():
        trip = form.save()
        if trip.is_active:
            messages.success(request, 'تم حفظ تعديلات الرحلة ونشرها على الموقع.')
        else:
            messages.success(request, 'تم حفظ تعديلات الرحلة، وهي الآن مخفية من الموقع.')
        return redirect('dashboard:trip_edit', slug=trip.slug)
    context = {'form': form, 'trip': trip, 'title': 'تعديل الرحلة', 'page': 'trips'}
    return render(request, 'dashboard/trips/form.html', context)


def _move_trip(request, pk, up):
    """Swap a trip's `order` with its neighbour and redirect back.

    Shared by the move-up and move-down views. Ties in `order` are tolerated:
    the neighbour is resolved by creation date, so dragging a trip that two
    others share a position with still moves exactly one step.

    Args:
        request (HttpRequest): The POST request.
        pk (int): Primary key of the trip being moved.
        up (bool): True to move towards position 0, False to move down.

    Returns:
        HttpResponseRedirect: back to the trip list.
    """
    trip = get_object_or_404(Trip, pk=pk)
    rows = list(Trip.objects.order_by('order', '-created_at', 'id'))
    index = next((i for i, row in enumerate(rows) if row.pk == trip.pk), None)
    if index is None:
        return redirect('dashboard:trips')
    target = index - 1 if up else index + 1
    if target < 0 or target >= len(rows):
        if up:
            messages.info(request, f'«{trip.name}» في أول القائمة بالفعل.')
        else:
            messages.info(request, f'«{trip.name}» في آخر القائمة بالفعل.')
        return redirect('dashboard:trips')
    rows[index], rows[target] = rows[target], rows[index]
    for i, row in enumerate(rows):
        if row.order != i:
            Trip.objects.filter(pk=row.pk).update(order=i)
    if up:
        messages.success(request, f'تم رفع «{trip.name}» للأمام.')
    else:
        messages.success(request, f'تم إرجاع «{trip.name}» للخلف.')
    return redirect('dashboard:trips')


@staff_required
@require_POST
def trip_move_up(request, pk):
    """Move a trip one position earlier in the public list.

    Args:
        request (HttpRequest): POST only.
        pk (int): Primary key of the trip.

    Returns:
        HttpResponseRedirect: back to the trip list.
    """
    return _move_trip(request, pk, up=True)


@staff_required
@require_POST
def trip_move_down(request, pk):
    """Move a trip one position later in the public list.

    Args:
        request (HttpRequest): POST only.
        pk (int): Primary key of the trip.

    Returns:
        HttpResponseRedirect: back to the trip list.
    """
    return _move_trip(request, pk, up=False)


@staff_required
@require_POST
def trip_delete(request, slug):
    """Delete a trip after confirmation.

    Args:
        request (HttpRequest): POST only.
        slug (str): Slug of the trip to delete.

    Returns:
        HttpResponseRedirect: back to the trip list.
    """
    trip = get_object_or_404(Trip, slug=slug)
    if trip.thumbnail:
        trip.thumbnail.delete(save=False)
    messages.success(request, f'تم حذف الرحلة «{trip.name}».')
    trip.delete()
    return redirect('dashboard:trips')


# --------------------------------------------------------------------------
# Bookings
# --------------------------------------------------------------------------
@staff_required
def booking_list(request):
    """List bookings, newest first, filterable by status.

    Args:
        request (HttpRequest): Optional ?status= filter.

    Returns:
        HttpResponse: dashboard/bookings/list.html.
    """
    query = request.GET.get('q', '').strip()
    status = request.GET.get('status', '').strip()
    bookings = Booking.objects.all().order_by('-created_at')
    if query:
        bookings = bookings.filter(
            Q(name__icontains=query) | Q(phone__icontains=query)
            | Q(trip_label__icontains=query) | Q(reference_code__icontains=query)
        )
    if status in BookingStatus.values:
        bookings = bookings.filter(status=status)
    context = {
        'bookings': bookings,
        'q': query,
        'filter_status': status,
        'status_choices': BookingStatus.choices,
        'page': 'bookings',
    }
    return render(request, 'dashboard/bookings/list.html', context)


@staff_required
def booking_detail(request, pk):
    """Show one booking in full, with the actions available for its status.

    Args:
        request (HttpRequest): The incoming request.
        pk (int): Booking primary key.

    Returns:
        HttpResponse: dashboard/bookings/detail.html.
    """
    booking = get_object_or_404(Booking, pk=pk)
    if booking.status == BookingStatus.CONFIRMED:
        wa_msg = booking_confirmed_message(booking)
    elif booking.status == BookingStatus.REJECTED:
        wa_msg = booking_rejected_message(booking)
    else:
        wa_msg = booking_created_message(booking)
    context = {
        'booking': booking,
        'wa_url': build_whatsapp_url(booking.phone, wa_msg),
        'page': 'bookings',
    }
    return render(request, 'dashboard/bookings/detail.html', context)


@staff_required
def booking_create(request):
    """Create a booking by hand, for walk-ins and phone enquiries.

    Args:
        request (HttpRequest): GET renders the form, POST saves.

    Returns:
        HttpResponse: the form, or a redirect to the booking detail.
    """
    form = BookingForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        booking = form.save()
        messages.success(request, f'تم حفظ طلب الحجز باسم «{booking.name}».')
        return redirect('dashboard:booking_detail', pk=booking.pk)
    context = {'form': form, 'title': 'إضافة طلب حجز', 'page': 'bookings'}
    return render(request, 'dashboard/bookings/form.html', context)


@staff_required
@require_POST
def booking_delete(request, pk):
    """Delete a booking record.

    Args:
        request (HttpRequest): POST only.
        pk (int): Booking primary key.

    Returns:
        HttpResponseRedirect: back to the booking list.
    """
    booking = get_object_or_404(Booking, pk=pk)
    messages.success(request, f'تم حذف طلب الحجز «{booking.name}».')
    booking.delete()
    return redirect('dashboard:bookings')


def _book_current_user(booking):
    """Stamp the acting staff member onto a booking they just handled.

    Args:
        booking (Booking): The booking being actioned.

    Returns:
        None
    """
    booking.handled_by = request.user


@staff_required
@require_POST
def booking_confirm(request, pk):
    """Confirm a pending booking and notify the customer.

    Sets the status, stamps confirmed_at and the handling staff member, then
    sends the confirmation email and the WhatsApp deep link.

    Args:
        request (HttpRequest): POST only.
        pk (int): Booking primary key.

    Returns:
        HttpResponseRedirect: back to the booking detail.
    """
    booking = get_object_or_404(Booking, pk=pk)
    booking.status = BookingStatus.CONFIRMED
    booking.confirmed_at = timezone.now()
    booking.handled_by = request.user
    booking.save(update_fields=['status', 'confirmed_at', 'handled_by'])
    try:
        send_whatsapp(booking.phone, booking_confirmed_message(booking))
    except Exception:
        logger.exception('فشل إرسال واتساب تأكيد الحجز')
    messages.success(
        request,
        f'تم تأكيد حجز «{booking.name}» رقم {booking.reference_code}.',
    )
    return redirect('dashboard:booking_detail', pk=booking.pk)


@staff_required
@require_POST
def booking_reject(request, pk):
    """Reject a pending booking and notify the customer.

    Args:
        request (HttpRequest): POST only, with an optional `notes` reason.
        pk (int): Booking primary key.

    Returns:
        HttpResponseRedirect: back to the booking detail.
    """
    booking = get_object_or_404(Booking, pk=pk)
    booking.status = BookingStatus.REJECTED
    booking.handled_by = request.user
    booking.save(update_fields=['status', 'handled_by'])
    try:
        send_whatsapp(booking.phone, booking_rejected_message(booking))
    except Exception:
        logger.exception('فشل إرسال واتساب رفض الحجز')
    messages.error(
        request,
        f'تم رفض حجز «{booking.name}» رقم {booking.reference_code}.',
    )
    return redirect('dashboard:booking_detail', pk=booking.pk)


@staff_required
@require_POST
def booking_complete(request, pk):
    """Mark a confirmed booking as completed once the trip has run.

    Args:
        request (HttpRequest): POST only.
        pk (int): Booking primary key.

    Returns:
        HttpResponseRedirect: back to the booking detail.
    """
    booking = get_object_or_404(Booking, pk=pk)
    booking.status = BookingStatus.COMPLETED
    booking.handled_by = request.user
    booking.save(update_fields=['status', 'handled_by'])
    messages.success(
        request,
        f'تم تحديد حجز «{booking.name}» كرحلة مكتملة.',
    )
    return redirect('dashboard:booking_detail', pk=booking.pk)


# --------------------------------------------------------------------------
# Reviews
# --------------------------------------------------------------------------
@staff_required
def review_list(request):
    """Render the review moderation queue.

    Args:
        request (HttpRequest): Optional ?status= filter.

    Returns:
        HttpResponse: dashboard/reviews/list.html.
    """
    status = request.GET.get('status', '').strip()
    query = request.GET.get('q', '').strip()
    reviews = Review.objects.select_related('trip', 'approved_by').all()
    if status in ReviewStatus.values:
        reviews = reviews.filter(status=status)
    if query:
        reviews = reviews.filter(
            Q(name__icontains=query) | Q(country__icontains=query)
            | Q(text__icontains=query) | Q(trip__name__icontains=query)
        )
    context = {
        'reviews': reviews,
        'q': query,
        'filter_status': status,
        'status_choices': ReviewStatus.choices,
        'pending_count': Review.objects.filter(status=ReviewStatus.PENDING).count(),
        'page': 'reviews',
    }
    return render(request, 'dashboard/reviews/list.html', context)


@staff_required
def review_detail(request, pk):
    """Show a single review before moderating it.

    Args:
        request (HttpRequest): The incoming request.
        pk (int): Review primary key.

    Returns:
        HttpResponse: dashboard/reviews/detail.html.
    """
    review = get_object_or_404(Review, pk=pk)
    context = {'review': review, 'page': 'reviews'}
    return render(request, 'dashboard/reviews/detail.html', context)


@staff_required
@require_POST
def review_approve(request, pk):
    """Publish a review to the public site.

    Args:
        request (HttpRequest): POST only.
        pk (int): Review primary key.

    Returns:
        HttpResponseRedirect: back to the review list.
    """
    review = get_object_or_404(Review, pk=pk)
    review.status = ReviewStatus.APPROVED
    review.approved_at = timezone.now()
    review.approved_by = request.user
    review.rejection_reason = ''
    review.save(update_fields=['status', 'approved_at', 'approved_by', 'rejection_reason'])
    messages.success(request, f'تم نشر رأي «{review.name}» على الموقع.')
    return redirect('dashboard:review_detail', pk=review.pk)


@staff_required
@require_POST
def review_reject(request, pk):
    """Keep a review unpublished and record why.

    Args:
        request (HttpRequest): POST only, with a `reason` field.
        pk (int): Review primary key.

    Returns:
        HttpResponseRedirect: back to the review list.
    """
    review = get_object_or_404(Review, pk=pk)
    review.status = ReviewStatus.REJECTED
    review.rejection_reason = request.POST.get('rejection_reason', '').strip()[:500]
    review.save(update_fields=['status', 'rejection_reason'])
    messages.error(request, f'تم رفض رأي «{review.name}».')
    return redirect('dashboard:review_detail', pk=review.pk)


@staff_required
@require_POST
def review_delete(request, pk):
    """Delete a review outright.

    Args:
        request (HttpRequest): POST only.
        pk (int): Review primary key.

    Returns:
        HttpResponseRedirect: back to the review list.
    """
    review = get_object_or_404(Review, pk=pk)
    if review.photo:
        review.photo.delete(save=False)
    messages.success(request, f'تم حذف رأي «{review.name}».')
    review.delete()
    return redirect('dashboard:reviews')


# --------------------------------------------------------------------------
# Site settings & sections
# --------------------------------------------------------------------------
@staff_required
def settings_edit(request):
    """Edit the SiteSettings singleton (company details and page copy).

    Args:
        request (HttpRequest): GET renders, POST saves.

    Returns:
        HttpResponse: dashboard/settings.html.
    """
    instance = SiteSettings.load()
    form = SettingsForm(request.POST or None, instance=instance)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'تم حفظ بيانات الموقع وتحديثه فوراً.')
        return redirect('dashboard:settings')
    context = {'form': form, 'settings': instance, 'page': 'settings'}
    return render(request, 'dashboard/settings.html', context)


@staff_required
def sections_view(request):
    """Reorder and show/hide the homepage sections.

    Args:
        request (HttpRequest): POST persists the new order.

    Returns:
        HttpResponse: dashboard/sections.html.
    """
    instance = SiteSettings.load()
    if request.method == 'POST':
        order = request.POST.getlist('order', [])
        clean = [
            slug for slug in order
            if slug in SECTION_SLUGS and slug not in [slug for slug in order[:order.index(slug)]]
        ]
        for slug in SECTION_SLUGS:
            if slug not in clean:
                clean.append(slug)
        instance.section_order = clean
        instance.save()
        messages.success(request, 'تم حفظ ترتيب أقسام الصفحة الرئيسية.')
        return redirect('dashboard:sections')

    context = {
        'sections': [{'slug': s, 'label': SECTION_LABELS[s]} for s in instance.section_order],
        'page': 'sections',
    }
    return render(request, 'dashboard/sections.html', context)


# --------------------------------------------------------------------------
# Media library
# --------------------------------------------------------------------------
@staff_required
def media_list(request):
    """List the reusable media library.

    Args:
        request (HttpRequest): The incoming request.

    Returns:
        HttpResponse: the media page, with the upload form.
    """
    files = MediaFile.objects.all()
    context = {'files': files, 'page': 'media'}
    return render(request, 'dashboard/media/list.html', context)


@staff_required
def media_upload(request):
    """Upload an image into the media library.

    Args:
        request (HttpRequest): POST carries title, alt and the file.

    Returns:
        HttpResponseRedirect: back to the media list.
    """
    form = MediaForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        media = form.save()
        messages.success(request, f'تم رفع الملف «{media}».')
        return redirect('dashboard:media')
    context = {'form': form, 'title': 'رفع ملف جديد', 'page': 'media'}
    return render(request, 'dashboard/media/upload.html', context)


@staff_required
@require_POST
def media_delete(request, pk):
    """Delete a media entry and its file from storage.

    Args:
        request (HttpRequest): POST only.
        pk (int): MediaFile primary key.

    Returns:
        HttpResponseRedirect: back to the media list.
    """
    media = get_object_or_404(MediaFile, pk=pk)
    if media.file:
        media.file.delete(save=False)
    messages.success(request, f'تم حذف الملف «{media}».')
    media.delete()
    return redirect('dashboard:media')


# --------------------------------------------------------------------------
# Users (superusers only)
# --------------------------------------------------------------------------
@superuser_required
def user_list(request):
    """List staff accounts. Superusers only.

    Args:
        request (HttpRequest): The incoming request.

    Returns:
        HttpResponse: dashboard/users/list.html.
    """
    users = User.objects.all().order_by('-is_superuser', '-is_staff', 'username')
    context = {'users': users, 'page': 'users'}
    return render(request, 'dashboard/users/list.html', context)


@superuser_required
def user_create(request):
    """Create a staff account. Superusers only.

    Args:
        request (HttpRequest): GET renders the form, POST saves.

    Returns:
        HttpResponse: the form, or a redirect to the user list.
    """
    form = UserForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        if not form.cleaned_data.get('password'):
            form.add_error('password', 'كلمة المرور إلزامية عند إنشاء مستخدم.')
        else:
            user = form.save()
            messages.success(request, f'تم إنشاء المستخدم «{user.username}».')
            return redirect('dashboard:user_edit', pk=user.pk)
    context = {'form': form, 'title': 'إضافة مستخدم', 'page': 'users'}
    return render(request, 'dashboard/users/form.html', context)


@superuser_required
def user_edit(request, pk):
    """Edit a staff account, including its role. Superusers only.

    Args:
        request (HttpRequest): GET renders the form, POST saves.
        pk (int): User primary key.

    Returns:
        HttpResponse: the form, or a redirect to the user list.
    """
    user = get_object_or_404(User, pk=pk)
    form = UserForm(request.POST or None, instance=user)
    if request.method == 'POST' and form.is_valid():
        if user == request.user:
            data = form.cleaned_data
            if not (data.get('is_superuser') and data.get('is_staff') and data.get('is_active')):
                raise PermissionDenied('لا يمكنك إزالة صلاحياتك أو تعطيل حسابك الحالي.')
        user = form.save()
        messages.success(request, f'تم حفظ بيانات المستخدم «{user.username}».')
        return redirect('dashboard:user_edit', pk=user.pk)
    context = {'form': form, 'user': user, 'title': 'تعديل مستخدم', 'page': 'users'}
    return render(request, 'dashboard/users/form.html', context)


@superuser_required
@require_POST
def user_delete(request, pk):
    """Delete a staff account. Superusers only, and never yourself.

    Args:
        request (HttpRequest): POST only.
        pk (int): User primary key.

    Returns:
        HttpResponseRedirect: back to the user list.
    """
    user = get_object_or_404(User, pk=pk)
    if user == request.user:
        raise PermissionDenied('لا يمكنك حذف حسابك الحالي.')
    messages.success(request, f'تم حذف المستخدم «{user.username}».')
    user.delete()
    return redirect('dashboard:users')


# --------------------------------------------------------------------------
# Live preview
# --------------------------------------------------------------------------
@staff_required
def preview(request):
    """Render the public homepage inside the dashboard chrome.

    Lets staff edit copy and check the result without a second tab. Read-only:
    saving still happens on the real pages.

    Args:
        request (HttpRequest): The incoming request.

    Returns:
        HttpResponse: dashboard/preview.html wrapping home.html.
    """
    preview_pages = [
        ('/', 'الرئيسية'),
        ('/trips/', 'كل الرحلات'),
        ('/about/', 'من نحن'),
        ('/booking/', 'تواصل وحجز'),
    ]
    for trip in Trip.objects.filter(is_active=True):
        preview_pages.append((f'/trips/{trip.slug}/', f'🚌 {trip.name}'))

    url = request.GET.get('url', '/')
    context = {
        'preview_pages': preview_pages,
        'selected_url': url,
        'page': 'preview',
    }
    return render(request, 'dashboard/preview.html', context)


class DashboardLoginView(LoginView):
    """Dashboard login page, wired to the branded form and template.

Replaces Django's LoginView to (a) use DashboardLoginForm, (b) keep the
Arabic template, and (c) send staff to the dashboard instead of the site.
    """
    template_name = 'dashboard/login.html'
    authentication_form = DashboardLoginForm
    redirect_authenticated_user = True

    def get_redirect_url(self):
        """Send a freshly logged-in user to the dashboard, not the site.

        Returns:
            str: The dashboard overview URL.
        """
        return reverse('dashboard:overview')

    def dispatch(self, request, *args, **kwargs):
        """Bounce an already-authenticated visitor away from the login page.

        Args:
            request (HttpRequest): The incoming request.
            *args: Positional args forwarded to LoginView.
            **kwargs: Keyword args forwarded to LoginView.

        Returns:
            HttpResponse: A redirect when already logged in, otherwise the
                normal LoginView response.
        """
        if self.redirect_authenticated_user and request.user.is_authenticated:
            if request.user.is_staff or request.user.is_superuser:
                return HttpResponseRedirect(self.get_redirect_url())
            logout(request)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        """Log the user in and honour an intended ?next= destination.

        Args:
            form (AuthenticationForm): The validated login form.

        Returns:
            HttpResponseRedirect: To ?next= when it is a safe local URL,
                otherwise to the dashboard overview.
        """
        response = super().form_valid(form)
        user = self.request.user
        if not (user.is_staff or user.is_superuser):
            logout(self.request)
            messages.error(self.request, 'هذا الحساب ليس لديه صلاحية دخول لوحة التحكم.')
            return redirect('dashboard:login')
        return response


@staff_required
def dashboard_logout(request):
    """Log the current staff member out.

    Args:
        request (HttpRequest): POST only.

    Returns:
        HttpResponseRedirect: to the dashboard login.
    """
    logout(request)
    return redirect('dashboard:login')