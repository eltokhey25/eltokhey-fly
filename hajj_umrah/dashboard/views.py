from datetime import timedelta
import logging

from django.contrib import messages
from django.contrib.auth import get_user_model, logout
from django.contrib.auth.views import LoginView, LogoutView
from django.core.exceptions import PermissionDenied
from django.db.models import Q, Sum
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from core.models import Booking, BookingStatus, SiteSettings, Trip
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

SECTION_SLUGS = ['hero', 'trips', 'why', 'cta']
SECTION_LABELS = {
    'hero': 'الغلاف الرئيسي (Hero)',
    'trips': 'قسم الرحلات',
    'why': 'لماذا تختارنا',
    'cta': 'جاهز تبدأ رحلتك',
}


def permission_denied(request, exception=None):
    return render(request, 'dashboard/403.html', status=403)


@staff_required
def overview(request):
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
        'trips': trips.order_by('-is_active', 'departure'),
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
    form = TripForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        form.instance.is_active = True
        trip = form.save()
        messages.success(request, f'تمت إضافة الرحلة «{trip.name}» ونشرها فوراً.')
        return redirect('dashboard:trip_edit', slug=trip.slug)
    context = {'form': form, 'title': 'إضافة رحلة جديدة', 'page': 'trips'}
    return render(request, 'dashboard/trips/form.html', context)


@staff_required
def trip_edit(request, slug):
    trip = get_object_or_404(Trip, slug=slug)
    form = TripForm(request.POST or None, request.FILES or None, instance=trip)
    if request.method == 'POST' and form.is_valid():
        trip = form.save()
        messages.success(request, 'تم حفظ تعديلات الرحلة ونشرها على الموقع.')
        return redirect('dashboard:trip_edit', slug=trip.slug)
    context = {'form': form, 'trip': trip, 'title': 'تعديل الرحلة', 'page': 'trips'}
    return render(request, 'dashboard/trips/form.html', context)


@staff_required
@require_POST
def trip_delete(request, slug):
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
    booking = get_object_or_404(Booking, pk=pk)
    messages.success(request, f'تم حذف طلب الحجز «{booking.name}».')
    booking.delete()
    return redirect('dashboard:bookings')


def _book_current_user(booking):
    booking.handled_by = request.user


@staff_required
@require_POST
def booking_confirm(request, pk):
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
# Site settings & sections
# --------------------------------------------------------------------------
@staff_required
def settings_edit(request):
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
    files = MediaFile.objects.all()
    context = {'files': files, 'page': 'media'}
    return render(request, 'dashboard/media/list.html', context)


@staff_required
def media_upload(request):
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
    users = User.objects.all().order_by('-is_superuser', '-is_staff', 'username')
    context = {'users': users, 'page': 'users'}
    return render(request, 'dashboard/users/list.html', context)


@superuser_required
def user_create(request):
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
    template_name = 'dashboard/login.html'
    authentication_form = DashboardLoginForm
    redirect_authenticated_user = True

    def get_redirect_url(self):
        return reverse('dashboard:overview')

    def dispatch(self, request, *args, **kwargs):
        if self.redirect_authenticated_user and request.user.is_authenticated:
            if request.user.is_staff or request.user.is_superuser:
                return HttpResponseRedirect(self.get_redirect_url())
            logout(request)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        user = self.request.user
        if not (user.is_staff or user.is_superuser):
            logout(self.request)
            messages.error(self.request, 'هذا الحساب ليس لديه صلاحية دخول لوحة التحكم.')
            return redirect('dashboard:login')
        return response


@staff_required
def dashboard_logout(request):
    logout(request)
    return redirect('dashboard:login')