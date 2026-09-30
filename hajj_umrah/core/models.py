"""
core/models.py
Database models for the whole site: Trip, Booking, Review and the
SiteSettings singleton, plus the image-normalisation helper they share.
Used by: core/views.py, core/admin.py, dashboard/views.py, dashboard/forms.py,
         and every template via the site_settings processor.
"""
from io import BytesIO
from uuid import uuid4

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import models
from django.utils import timezone

# ---- Image pipeline limits -------------------------------------------
# Longest edge (px) allowed for a trip thumbnail / a customer review photo.
TRIP_THUMBNAIL_MAX = 1600
REVIEW_PHOTO_MAX = 400
# JPEG quality for re-encoded uploads; PNG output ignores it.
JPEG_QUALITY = 85


def _normalize_image(img_field, max_size, quality=JPEG_QUALITY):
    """Re-encode an image field.

    - Applies EXIF orientation rotation (ImageOps.exif_transpose) and strips metadata.
    - Downscales proportionally to fit within max_size x max_size (no cropping,
      never upscales).
    - Saves as JPEG (quality=85) unless the source had transparency, in which case
      it is kept as PNG.

    Args:
        img_field (FieldFile): The image file attached to the model.
        max_size (int): Longest allowed edge in pixels.
        quality (int): JPEG quality for the re-encoded file.

    Returns:
        tuple | None: ``(new_name, ContentFile)`` on success, or None when
            the file cannot be read — a corrupt upload must not break save().
    """
    from PIL import Image, ImageOps

    try:
        with img_field.open('rb') as fh:
            img = Image.open(fh)
            img = ImageOps.exif_transpose(img)
            has_alpha = img.mode in ('RGBA', 'LA') or (
                img.mode == 'P' and 'transparency' in img.info
            )
            if max(img.size) > max_size:
                img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            buf = BytesIO()
            if has_alpha:
                img.convert('RGBA').save(buf, 'PNG')
                ext = '.png'
            else:
                img.convert('RGB').save(buf, 'JPEG', quality=quality, optimize=True)
                ext = '.jpg'
    except Exception:
        return None
    return f'{uuid4().hex}{ext}', ContentFile(buf.getvalue())


class TripType(models.TextChoices):
    """The kinds of trip the agency sells (stored as slugs, shown in Arabic)."""

    HAJJ = 'hajj', 'الحج'
    UMRAH = 'umrah', 'العمرة'
    RAMADAN = 'ramadan', 'عمرة رمضان'


class BookingStatus(models.TextChoices):
    """Lifecycle of a booking request, from submission to completion."""

    PENDING = 'pending', 'قيد المراجعة'
    CONFIRMED = 'confirmed', 'تم التأكيد'
    REJECTED = 'rejected', 'مرفوض'
    COMPLETED = 'completed', 'مكتمل'


class ReviewStatus(models.TextChoices):
    """Moderation state of a review; only APPROVED is shown publicly."""

    PENDING = 'pending', 'قيد المراجعة'
    APPROVED = 'approved', 'منشور'
    REJECTED = 'rejected', 'مرفوض'


class Trip(models.Model):
    """A Hajj/Umrah departure — the core piece of content on the site.

    Homepage ordering is driven by the ``order`` field so staff can
    rearrange trips from the dashboard without touching dates.
    """

    name = models.CharField('اسم الرحلة', max_length=255)
    slug = models.SlugField('الرابط', max_length=255, unique=True)
    trip_type = models.CharField(
        'نوع الرحلة', max_length=20, choices=TripType.choices, default=TripType.UMRAH
    )
    description = models.TextField('نبذة عن الرحلة', blank=True)
    price = models.CharField(
        'السعر', max_length=100, blank=True,
        help_text='اتركه فارغاً لعرض «اكتب لنا»، أو اكتب نصاً حراً مثل «السعر قريباً».',
    )
    duration = models.CharField('المدة', max_length=50, blank=True)
    departure = models.DateField('تاريخ الخروج', null=True, blank=True)
    return_date = models.DateField('تاريخ العودة', null=True, blank=True)
    transport = models.CharField('وسيلة النقل', max_length=50, blank=True)
    capacity = models.PositiveIntegerField('الطاقة الاستيعابية', null=True, blank=True)
    remaining = models.PositiveIntegerField('الأماكن المتبقية', null=True, blank=True)
    is_active = models.BooleanField('معروضة على الموقع', default=True)
    order = models.PositiveIntegerField('ترتيب الظهور', default=0, db_index=True)
    thumbnail = models.ImageField(
        'صورة الرحلة (الصورة المصغرة)',
        upload_to='trip_thumbnails/%Y/%m/',
        blank=True,
        null=True,
    )
    itinerary = models.JSONField('برنامج السير', default=list)
    includes = models.JSONField('يشمل السعر', default=list)
    excludes = models.JSONField('لا يشمل السعر', default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Order trips by the dashboard's manual order, newest as tie-breaker."""
        # Manual order first, newest as the tie-breaker.
        ordering = ['order', '-created_at']
        verbose_name = 'رحلة'
        verbose_name_plural = 'الرحلات'

    def __str__(self):
        """Return the trip name (admin dropdowns and selects)."""
        return self.name

    def __init__(self, *args, **kwargs):
        """Snapshot the thumbnail name so save() can detect replacements.

        Args:
            *args: Positional args forwarded to Model.
            **kwargs: Keyword args forwarded to Model.
        """
        super().__init__(*args, **kwargs)
        # Snapshot used by save() to tell a new upload from an untouched field.
        self._original_thumbnail = self.thumbnail.name if self.thumbnail else None

    def save(self, *args, **kwargs):
        """Save the trip, normalising the thumbnail and removing the old file.

        A newly uploaded thumbnail is re-encoded (downscaled to
        TRIP_THUMBNAIL_MAX) under a random name, and the file it replaced is
        deleted from storage so uploads do not pile up.

        Args:
            *args: Positional args forwarded to Model.save().
            **kwargs: Keyword args forwarded to Model.save().

        Returns:
            None
        """
        adding = self._state.adding
        uploaded = self.thumbnail.name if self.thumbnail else None
        thumb_changed = adding or uploaded != self._original_thumbnail
        super().save(*args, **kwargs)
        if thumb_changed and uploaded:
            result = _normalize_image(self.thumbnail, TRIP_THUMBNAIL_MAX)
            if result:
                new_name, content = result
                current_name = self.thumbnail.name
                default_storage.delete(current_name)
                self.thumbnail.save(new_name, content, save=False)
                super().save(update_fields=['thumbnail'])
        if (
            not adding
            and uploaded
            and uploaded != self._original_thumbnail
            and self._original_thumbnail
        ):
            default_storage.delete(self._original_thumbnail)
        self._original_thumbnail = self.thumbnail.name if self.thumbnail else None

    @property
    def price_display(self):
        """Return the price as displayable Arabic text.

        A numeric price is formatted with thousands separators and a currency
        suffix, free text is shown verbatim, and an empty field falls back to a
        "coming soon" message.

        Returns:
            str: Text ready to drop into a template.
        """
        if not self.price:
            return 'السعر قريباً'
        text = str(self.price).strip()
        if text.isdigit():
            return f'{int(text):,} ج.م'
        return text


class Booking(models.Model):
    """A customer's booking request.

    Created from the public form, from the chat API, or by hand in the
    dashboard. The reference code is what the customer types into the
    tracking page.
    """

    reference_code = models.CharField('رقم الحجز', max_length=20, unique=True, blank=True)
    name = models.CharField('الاسم الكامل', max_length=255)
    phone = models.CharField('رقم الهاتف', max_length=50)
    email = models.EmailField('البريد الإلكتروني', max_length=254, blank=True)
    trip_label = models.CharField('الرحلة / الموعد', max_length=500, blank=True)
    trip_type = models.CharField('نوع الرحلة', max_length=50, blank=True)
    people = models.PositiveIntegerField('عدد الأفراد', default=1)
    notes = models.TextField('ملاحظات', blank=True)
    status = models.CharField(
        'حالة الحجز', max_length=20, choices=BookingStatus.choices,
        default=BookingStatus.PENDING,
    )
    confirmed_at = models.DateTimeField('تاريخ التأكيد', null=True, blank=True)
    handled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='تمت المعالجة بواسطة',
        related_name='handled_bookings',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """List bookings newest first in the admin."""
        ordering = ['-created_at']
        verbose_name = 'طلب حجز'
        verbose_name_plural = 'طلبات الحجز'

    def __str__(self):
        """Return "reference — customer — trip" for admin lists."""
        return f'{self.reference_code or "—"} — {self.name} — {self.trip_label or "بدون رحلة محددة"}'

    def save(self, *args, **kwargs):
        """Fill in the reference code and confirmation timestamp, then save.

        Args:
            *args: Positional args forwarded to Model.save().
            **kwargs: Keyword args forwarded to Model.save().

        Returns:
            None
        """
        if not self.reference_code:
            self.reference_code = self._generate_reference_code()
        if self.status == BookingStatus.CONFIRMED and not self.confirmed_at:
            self.confirmed_at = timezone.now()
        super().save(*args, **kwargs)

    @classmethod
    def _generate_reference_code(cls):
        """Build the next sequential booking reference for the current year.

        Codes look like "HJ-2026-0001": the year is embedded so they stay
        meaningful when sorted, and the retry loop guards against a collision
        caused by a hand-edited code.

        Returns:
            str: A reference code not yet in use.
        """
        prefix = f'HJ-{timezone.now().year}-'
        last = (
            cls.objects.filter(reference_code__startswith=prefix)
            .order_by('-reference_code')
            .values_list('reference_code', flat=True)
            .first()
        )
        number = 1
        if last:
            try:
                number = int(last.rsplit('-', 1)[1]) + 1
            except (ValueError, IndexError):
                number = cls.objects.filter(reference_code__startswith=prefix).count() + 1
        code = f'{prefix}{number:04d}'
        while cls.objects.filter(reference_code=code).exists():
            number += 1
            code = f'{prefix}{number:04d}'
        return code

    @property
    def status_label(self):
        """Return the Arabic label for the current status.

        Returns:
            str: e.g. 'قيد المراجعة'; falls back to the raw value if unknown.
        """
        return BookingStatus(self.status).label if self.status in BookingStatus.values else self.status

    @property
    def status_message(self):
        """Return the customer-facing sentence for the current status.

        Used by the tracking page to explain what happens next.

        Returns:
            str: Arabic message, or '' for an unrecognised status.
        """
        return {
            BookingStatus.PENDING: 'حجزك قيد المراجعة، سنتواصل معك خلال 24 ساعة',
            BookingStatus.CONFIRMED: 'سيتم التواصل معك قريباً',
            BookingStatus.REJECTED: 'نأسف، لم نتمكن من تأكيد حجزك. تواصل معنا للمزيد',
            BookingStatus.COMPLETED: 'تمت رحلتك بنجاح. شكراً لك',
        }.get(self.status, '')


# Countries offered in the review form dropdown.
REVIEW_COUNTRIES = [
    ('مصر', 'مصر'),
    ('السعودية', 'السعودية'),
    ('الإمارات', 'الإمارات'),
    ('الكويت', 'الكويت'),
    ('قطر', 'قطر'),
    ('البحرين', 'البحرين'),
    ('عُمان', 'عُمان'),
    ('الأردن', 'الأردن'),
    ('العراق', 'العراق'),
    ('اليمن', 'اليمن'),
    ('سوريا', 'سوريا'),
    ('لبنان', 'لبنان'),
    ('فلسطين', 'فلسطين'),
    ('ليبيا', 'ليبيا'),
    ('تونس', 'تونس'),
    ('الجزائر', 'الجزائر'),
    ('المغرب', 'المغرب'),
    ('السودان', 'السودان'),
    ('تركيا', 'تركيا'),
    ('المملكة المتحدة', 'المملكة المتحدة'),
    ('ألمانيا', 'ألمانيا'),
    ('فرنسا', 'فرنسا'),
    ('الولايات المتحدة', 'الولايات المتحدة'),
    ('كندا', 'كندا'),
    ('أستراليا', 'أستراليا'),
]

# Flag emoji per country, so reviews render without an image request.
COUNTRY_FLAGS = {
    'مصر': '🇪🇬',
    'السعودية': '🇸🇦',
    'الإمارات': '🇦🇪',
    'الكويت': '🇰🇼',
    'قطر': '🇶🇦',
    'البحرين': '🇧🇭',
    'عُمان': '🇴🇲',
    'الأردن': '🇯🇴',
    'العراق': '🇮🇶',
    'اليمن': '🇾🇪',
    'سوريا': '🇸🇾',
    'لبنان': '🇱🇧',
    'فلسطين': '🇵🇸',
    'ليبيا': '🇱🇾',
    'تونس': '🇹🇳',
    'الجزائر': '🇩🇿',
    'المغرب': '🇲🇦',
    'السودان': '🇸🇩',
    'تركيا': '🇹🇷',
    'المملكة المتحدة': '🇬🇧',
    'ألمانيا': '🇩🇪',
    'فرنسا': '🇫🇷',
    'الولايات المتحدة': '🇺🇸',
    'كندا': '🇨🇦',
    'أستراليا': '🇦🇺',
}


class Review(models.Model):
    """A customer review, moderated before it appears on the public site."""

    name = models.CharField('اسم العميل', max_length=255)
    country = models.CharField(
        'الدولة', max_length=100, choices=REVIEW_COUNTRIES, default='مصر'
    )
    photo = models.ImageField(
        'صورة العميل',
        upload_to='reviews/',
        blank=True,
        null=True,
    )
    rating = models.PositiveSmallIntegerField(
        'التقييم', choices=[(n, f'{n} نجوم') for n in range(1, 6)]
    )
    text = models.TextField('نص الرأي')
    trip = models.ForeignKey(
        Trip,
        verbose_name='الرحلة',
        related_name='reviews',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    status = models.CharField(
        'الحالة', max_length=20, choices=ReviewStatus.choices, default=ReviewStatus.PENDING
    )
    rejection_reason = models.CharField('سبب الرفض', max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField('تاريخ النشر', null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='تمت الموافقة بواسطة',
        related_name='approved_reviews',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    ip_address = models.GenericIPAddressField('عنوان IP', null=True, blank=True)

    class Meta:
        """List reviews newest first in the admin."""
        ordering = ['-created_at']
        verbose_name = 'رأي عميل'
        verbose_name_plural = 'آراء العملاء'

    def __str__(self):
        """Return "name — stars" for admin lists."""
        return f'{self.name} — {'⭐' * self.rating}'

    @property
    def country_flag(self):
        """Return the flag emoji for the review's country.

        Returns:
            str: Flag emoji, or '' when the country has no mapping.
        """
        return COUNTRY_FLAGS.get(self.country, '')

    def __init__(self, *args, **kwargs):
        """Snapshot the photo name so save() can detect replacements.

        Args:
            *args: Positional args forwarded to Model.
            **kwargs: Keyword args forwarded to Model.
        """
        super().__init__(*args, **kwargs)
        self._original_photo = self.photo.name if self.photo else None

    def save(self, *args, **kwargs):
        """Save the review, normalising the photo and deleting the old file.

        Args:
            *args: Positional args forwarded to Model.save().
            **kwargs: Keyword args forwarded to Model.save().

        Returns:
            None
        """
        adding = self._state.adding
        uploaded = self.photo.name if self.photo else None
        photo_changed = adding or uploaded != self._original_photo
        super().save(*args, **kwargs)
        if photo_changed and uploaded:
            self._normalize_photo()
        if not adding and photo_changed and self._original_photo:
            default_storage.delete(self._original_photo)
        self._original_photo = self.photo.name if self.photo else None

    def _normalize_photo(self):
        """Re-encode the review photo at REVIEW_PHOTO_MAX and swap the file.

        Returns:
            None
        """
        if not self.photo:
            return
        result = _normalize_image(self.photo, REVIEW_PHOTO_MAX)
        if not result:
            return
        new_name, content = result
        current_name = self.photo.name
        default_storage.delete(current_name)
        self.photo.save(new_name, content, save=False)
        super().save(update_fields=['photo'])


class SiteSettings(models.Model):
    """Singleton row (pk=1) holding the editable site copy and contacts.

    Every hero and section title lives here so staff can edit the homepage
    text from the dashboard without a deploy. Always read it via load().
    """

    company = models.CharField('اسم الشركة', max_length=255, default='الطوخي للحج والعمرة')
    phone = models.CharField('رقم الهاتف', max_length=50, blank=True)
    whatsapp = models.CharField('رقم الواتساب بصيغة دولية', max_length=50, blank=True)
    email = models.EmailField('البريد الإلكتروني', blank=True)
    address = models.CharField('العنوان', max_length=500, blank=True)
    facebook = models.URLField('رابط صفحة فيسبوك', blank=True)
    hero_title = models.CharField(max_length=255, default='رحلتك الروحانية تبدأ من هنا')
    hero_sub = models.TextField(
        default='تعرّف على رحلاتنا بتفاصيل كاملة لأيام السير، من نقطة الخروج حتى العودة، واحجز مكانك في المواعيد المتاحة.'
    )
    hero_btn = models.CharField(max_length=100, default='استكشف رحلات السنة')
    trips_title = models.CharField(max_length=255, default='رحلات السنة')
    trips_sub = models.TextField(
        default='جميع رحلات الحج والعمرة مرتبة حسب موعد الانطلاق، اضغط على أي رحلة لعرض برنامج السير بالتفصيل من الخروج حتى العودة.'
    )
    why_title = models.CharField(max_length=255, default='لماذا تختارنا؟')
    cta_title = models.CharField(max_length=255, default='جاهز تبدأ رحلتك المباركة؟')
    cta_sub = models.TextField(default='تواصل معنا الآن واحجز مكانك في أقرب رحلة.')
    section_order = models.JSONField(default=list)

    class Meta:
        """The settings row has no natural ordering, so keep it unsorted."""
        verbose_name = 'بيانات الموقع'
        verbose_name_plural = 'بيانات الموقع'

    @classmethod
    def load(cls):
        """Return the singleton settings row, creating and seeding it if absent.

        Returns:
            SiteSettings: The single row with pk=1. On first call it is created
                and ``section_order`` is given the default homepage order.
        """
        obj, _ = cls.objects.get_or_create(pk=1)
        if not obj.section_order:
            obj.section_order = ['hero', 'trips', 'why', 'cta']
            obj.save()
        return obj

    def __str__(self):
        """Return the company name (admin list label)."""
        return self.company