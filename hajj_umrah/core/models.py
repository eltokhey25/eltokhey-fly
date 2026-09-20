from io import BytesIO
from uuid import uuid4

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import models
from django.utils import timezone

TRIP_THUMBNAIL_MAX = 1600
REVIEW_PHOTO_MAX = 400
JPEG_QUALITY = 85


def _normalize_image(img_field, max_size, quality=JPEG_QUALITY):
    """Re-encode an image field.

    - Applies EXIF orientation rotation (ImageOps.exif_transpose) and strips metadata.
    - Downscales proportionally to fit within max_size x max_size (no cropping,
      never upscales).
    - Saves as JPEG (quality=85) unless the source had transparency, in which case
      it is kept as PNG.

    Returns ``(new_name, ContentFile)`` or ``None`` when the file can't be read.
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
    HAJJ = 'hajj', 'الحج'
    UMRAH = 'umrah', 'العمرة'
    RAMADAN = 'ramadan', 'عمرة رمضان'


class BookingStatus(models.TextChoices):
    PENDING = 'pending', 'قيد المراجعة'
    CONFIRMED = 'confirmed', 'تم التأكيد'
    REJECTED = 'rejected', 'مرفوض'
    COMPLETED = 'completed', 'مكتمل'


class ReviewStatus(models.TextChoices):
    PENDING = 'pending', 'قيد المراجعة'
    APPROVED = 'approved', 'منشور'
    REJECTED = 'rejected', 'مرفوض'


class Trip(models.Model):
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
        ordering = ['order', '-created_at']
        verbose_name = 'رحلة'
        verbose_name_plural = 'الرحلات'

    def __str__(self):
        return self.name

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_thumbnail = self.thumbnail.name if self.thumbnail else None

    def save(self, *args, **kwargs):
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
        if not self.price:
            return 'اكتب لنا'
        text = str(self.price).strip()
        if text.isdigit():
            return f'{int(text):,} ج.م'
        return text


class Booking(models.Model):
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
        ordering = ['-created_at']
        verbose_name = 'طلب حجز'
        verbose_name_plural = 'طلبات الحجز'

    def __str__(self):
        return f'{self.reference_code or "—"} — {self.name} — {self.trip_label or "بدون رحلة محددة"}'

    def save(self, *args, **kwargs):
        if not self.reference_code:
            self.reference_code = self._generate_reference_code()
        if self.status == BookingStatus.CONFIRMED and not self.confirmed_at:
            self.confirmed_at = timezone.now()
        super().save(*args, **kwargs)

    @classmethod
    def _generate_reference_code(cls):
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
        return BookingStatus(self.status).label if self.status in BookingStatus.values else self.status

    @property
    def status_message(self):
        return {
            BookingStatus.PENDING: 'حجزك قيد المراجعة، سنتواصل معك خلال 24 ساعة',
            BookingStatus.CONFIRMED: 'سيتم التواصل معك قريباً',
            BookingStatus.REJECTED: 'نأسف، لم نتمكن من تأكيد حجزك. تواصل معنا للمزيد',
            BookingStatus.COMPLETED: 'تمت رحلتك بنجاح. شكراً لك',
        }.get(self.status, '')


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
        ordering = ['-created_at']
        verbose_name = 'رأي عميل'
        verbose_name_plural = 'آراء العملاء'

    def __str__(self):
        return f'{self.name} — {'⭐' * self.rating}'

    @property
    def country_flag(self):
        return COUNTRY_FLAGS.get(self.country, '')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_photo = self.photo.name if self.photo else None

    def save(self, *args, **kwargs):
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
    company = models.CharField('اسم الشركة', max_length=255, default='الطوخي فلاي')
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
        verbose_name = 'بيانات الموقع'
        verbose_name_plural = 'بيانات الموقع'

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        if not obj.section_order:
            obj.section_order = ['hero', 'trips', 'why', 'cta']
            obj.save()
        return obj

    def __str__(self):
        return self.company