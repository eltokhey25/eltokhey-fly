from django.db import models


class TripType(models.TextChoices):
    HAJJ = 'hajj', 'الحج'
    UMRAH = 'umrah', 'العمرة'
    RAMADAN = 'ramadan', 'عمرة رمضان'


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
        ordering = ['departure', 'name']
        verbose_name = 'رحلة'
        verbose_name_plural = 'الرحلات'

    def __str__(self):
        return self.name

    @property
    def price_display(self):
        if not self.price:
            return 'اكتب لنا'
        text = str(self.price).strip()
        if text.isdigit():
            return f'{int(text):,} ج.م'
        return text


class Booking(models.Model):
    name = models.CharField('الاسم الكامل', max_length=255)
    phone = models.CharField('رقم الهاتف', max_length=50)
    trip_label = models.CharField('الرحلة / الموعد', max_length=500, blank=True)
    trip_type = models.CharField('نوع الرحلة', max_length=50, blank=True)
    people = models.PositiveIntegerField('عدد الأفراد', default=1)
    notes = models.TextField('ملاحظات', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'طلب حجز'
        verbose_name_plural = 'طلبات الحجز'

    def __str__(self):
        return f'{self.name} — {self.trip_label or "بدون رحلة محددة"}'


class SiteSettings(models.Model):
    company = models.CharField('اسم الشركة', max_length=255, default='رحلات الحج والعمرة')
    phone = models.CharField('رقم الهاتف', max_length=50, blank=True)
    whatsapp = models.CharField('رقم الواتساب بصيغة دولية', max_length=50, blank=True)
    email = models.EmailField('البريد الإلكتروني', blank=True)
    address = models.CharField('العنوان', max_length=500, blank=True)
    facebook = models.URLField('رابط صفحة فيسبوك', blank=True)
    hero_title = models.CharField(max_length=255, default='رحلات الحج والعمرة لكل مواسم السنة')
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