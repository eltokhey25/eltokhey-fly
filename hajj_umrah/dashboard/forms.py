import json
import secrets

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.utils.text import slugify

from core.models import Booking, SiteSettings, Trip, TripType

from .models import MediaFile

User = get_user_model()


class DashboardLoginForm(AuthenticationForm):
    username = forms.CharField(
        label='اسم المستخدم',
        widget=forms.TextInput(attrs={'class': 'input', 'placeholder': 'اسم المستخدم'}),
    )
    password = forms.CharField(
        label='كلمة المرور',
        widget=forms.PasswordInput(attrs={'class': 'input', 'placeholder': 'كلمة المرور'}),
    )

    error_messages = {
        'invalid_login': 'اسم المستخدم أو كلمة المرور غير صحيحة.',
        'inactive': 'هذا الحساب غير مفعّل.',
    }


class TripForm(forms.ModelForm):
    itinerary_json = forms.CharField(
        widget=forms.HiddenInput(), required=False, label=''
    )
    includes_list = forms.CharField(
        label='يشمل السعر (بند في كل سطر)',
        widget=forms.Textarea(attrs={'class': 'input textarea', 'rows': 5, 'dir': 'rtl'}),
        required=False,
    )
    excludes_list = forms.CharField(
        label='لا يشمل السعر (بند في كل سطر)',
        widget=forms.Textarea(attrs={'class': 'input textarea', 'rows': 4, 'dir': 'rtl'}),
        required=False,
    )
    remove_thumbnail = forms.BooleanField(
        label='إزالة الصورة الحالية',
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'switch-input'}),
    )

    class Meta:
        model = Trip
        fields = [
            'name', 'slug', 'trip_type', 'description', 'price', 'duration',
            'departure', 'return_date', 'transport', 'capacity', 'remaining',
            'is_active', 'thumbnail',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'input'}),
            'slug': forms.TextInput(attrs={'class': 'input ltr'}),
            'trip_type': forms.Select(attrs={'class': 'input'}),
            'description': forms.Textarea(attrs={'class': 'input textarea', 'rows': 4, 'dir': 'rtl'}),
            'price': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': 'مثال: 32000 أو «السعر قريباً»',
            }),
            'duration': forms.TextInput(attrs={'class': 'input'}),
            'departure': forms.DateInput(attrs={'class': 'input', 'type': 'date'}),
            'return_date': forms.DateInput(attrs={'class': 'input', 'type': 'date'}),
            'transport': forms.TextInput(attrs={'class': 'input'}),
            'capacity': forms.NumberInput(attrs={'class': 'input'}),
            'remaining': forms.NumberInput(attrs={'class': 'input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'switch-input'}),
            'thumbnail': forms.FileInput(attrs={'class': 'file-input', 'accept': 'image/*'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        labels = {
            'name': 'اسم الرحلة',
            'slug': 'الرابط (الـ Slug)',
            'trip_type': 'نوع الرحلة',
            'description': 'نبذة عن الرحلة',
            'price': 'السعر',
            'duration': 'مدة الرحلة',
            'departure': 'تاريخ الخروج',
            'return_date': 'تاريخ العودة',
            'transport': 'وسيلة النقل',
            'capacity': 'الطاقة الاستيعابية',
            'remaining': 'الأماكن المتبقية',
            'is_active': 'إظهار الرحلة على الموقع',
            'thumbnail': 'صورة الرحلة (الصورة المصغرة)',
            'remove_thumbnail': 'إزالة الصورة الحالية',
        }
        for name, label in labels.items():
            self.fields[name].label = label
        self.fields['slug'].required = False
        self._original_thumbnail = None
        if self.instance and self.instance.pk and self.instance.thumbnail:
            self._original_thumbnail = self.instance.thumbnail.name
        if not self.instance.pk:
            self.fields['is_active'].initial = True
        if self.instance and self.instance.pk:
            self.fields['itinerary_json'].initial = json.dumps(
                self.instance.itinerary, ensure_ascii=False
            )
            self.fields['includes_list'].initial = '\n'.join(self.instance.includes)
            self.fields['excludes_list'].initial = '\n'.join(self.instance.excludes)
        else:
            if not self.fields['itinerary_json'].initial:
                self.fields['itinerary_json'].initial = json.dumps(
                    [{'title': '', 'city': '', 'desc': ''}], ensure_ascii=False
                )

    def clean(self):
        cleaned = super().clean()
        try:
            steps = json.loads(self.data.get('itinerary_json') or '[]')
        except (TypeError, ValueError):
            steps = []
        cleaned['itinerary'] = []
        for step in steps if isinstance(steps, list) else []:
            if not isinstance(step, dict):
                continue
            title = str(step.get('title') or '').strip()
            city = str(step.get('city') or '').strip()
            desc = str(step.get('desc') or '').strip()
            if title or desc:
                cleaned['itinerary'].append({'title': title, 'city': city, 'desc': desc})

        def _lines(name):
            return [
                line.strip()
                for line in (self.data.get(name, '') or '').splitlines()
                if line.strip()
            ]

        cleaned['includes'] = _lines('includes_list')
        cleaned['excludes'] = _lines('excludes_list')
        self._ensure_slug(cleaned)
        return cleaned

    def _ensure_slug(self, cleaned):
        name = cleaned.get('name')
        slug = cleaned.get('slug')
        if slug:
            return
        if not name:
            return
        base = slugify(name)
        if not base:
            base = slugify(cleaned.get('trip_type') or '') or 'umrah'
        candidate = base
        taken = Trip.objects.exclude(pk=self.instance.pk if self.instance.pk else None)
        counter = 1
        while taken.filter(slug=candidate).exists():
            counter += 1
            candidate = f'{base}-{counter}'
        cleaned['slug'] = candidate

    def save(self, commit=True):
        for field in ('itinerary', 'includes', 'excludes'):
            setattr(self.instance, field, self.cleaned_data.get(field, []))
        new_image = self.files.get('thumbnail')
        if self.cleaned_data.get('remove_thumbnail') and not new_image:
            if self.instance.thumbnail:
                self.instance.thumbnail.delete(save=False)
            self.instance.thumbnail = None
        trip = super().save(commit=commit)
        if commit and new_image and self._original_thumbnail:
            stored = trip.thumbnail.name if trip.thumbnail else ''
            if stored and stored != self._original_thumbnail:
                Trip._meta.get_field('thumbnail').storage.delete(self._original_thumbnail)
        return trip


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['name', 'phone', 'email', 'trip_label', 'trip_type', 'people', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'input'}),
            'phone': forms.TextInput(attrs={'class': 'input ltr'}),
            'email': forms.EmailInput(attrs={'class': 'input ltr'}),
            'trip_label': forms.TextInput(attrs={'class': 'input'}),
            'trip_type': forms.Select(attrs={'class': 'input'}),
            'people': forms.NumberInput(attrs={'class': 'input', 'min': 1}),
            'notes': forms.Textarea(attrs={'class': 'input textarea', 'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        labels = {
            'name': 'الاسم الكامل',
            'phone': 'رقم الهاتف',
            'email': 'البريد الإلكتروني',
            'trip_label': 'الرحلة / الموعد',
            'trip_type': 'نوع الرحلة',
            'people': 'عدد الأفراد',
            'notes': 'ملاحظات',
        }
        for name, label in labels.items():
            self.fields[name].label = label
        self.fields['trip_type'].widget = forms.Select(attrs={'class': 'input'})
        self.fields['trip_type'].choices = [
            ('غير محدد', 'غير محدد'),
            (TripType.UMRAH.label, TripType.UMRAH.label),
            (TripType.RAMADAN.label, TripType.RAMADAN.label),
            (TripType.HAJJ.label, TripType.HAJJ.label),
        ]


class SettingsForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        fields = [
            'company', 'phone', 'whatsapp', 'email', 'address', 'facebook',
            'hero_title', 'hero_sub', 'hero_btn',
            'trips_title', 'trips_sub', 'why_title',
            'cta_title', 'cta_sub',
        ]
        widgets = {
            'company': forms.TextInput(attrs={'class': 'input'}),
            'phone': forms.TextInput(attrs={'class': 'input ltr'}),
            'whatsapp': forms.TextInput(attrs={'class': 'input ltr'}),
            'email': forms.EmailInput(attrs={'class': 'input ltr'}),
            'address': forms.TextInput(attrs={'class': 'input'}),
            'facebook': forms.URLInput(attrs={'class': 'input ltr'}),
            'hero_title': forms.TextInput(attrs={'class': 'input'}),
            'hero_sub': forms.Textarea(attrs={'class': 'input textarea', 'rows': 3}),
            'hero_btn': forms.TextInput(attrs={'class': 'input'}),
            'trips_title': forms.TextInput(attrs={'class': 'input'}),
            'trips_sub': forms.Textarea(attrs={'class': 'input textarea', 'rows': 3}),
            'why_title': forms.TextInput(attrs={'class': 'input'}),
            'cta_title': forms.TextInput(attrs={'class': 'input'}),
            'cta_sub': forms.Textarea(attrs={'class': 'input textarea', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        labels = {
            'company': 'اسم الشركة',
            'phone': 'رقم الهاتف',
            'whatsapp': 'رقم الواتساب (بصيغة دولية)',
            'email': 'البريد الإلكتروني',
            'address': 'العنوان',
            'facebook': 'رابط صفحة فيسبوك',
            'hero_title': 'عنوان الغلاف الرئيسي',
            'hero_sub': 'وصف الغلاف الرئيسي',
            'hero_btn': 'نص زر الغلاف',
            'trips_title': 'عنوان قسم الرحلات',
            'trips_sub': 'وصف قسم الرحلات',
            'why_title': 'عنوان قسم «لماذا تختارنا»',
            'cta_title': 'عنوان قسم الدعوة للحجز',
            'cta_sub': 'وصف قسم الدعوة للحجز',
        }
        for name, label in labels.items():
            self.fields[name].label = label


class UserForm(forms.ModelForm):
    password = forms.CharField(
        label='كلمة المرور',
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'input', 'autocomplete': 'new-password'}),
        help_text='في الإضافة تُكملها إلزامياً، وفي التعديل اتركها فارغة للإبقاء على نفسها.',
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_active', 'is_staff', 'is_superuser']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'input ltr'}),
            'first_name': forms.TextInput(attrs={'class': 'input'}),
            'last_name': forms.TextInput(attrs={'class': 'input'}),
            'email': forms.EmailInput(attrs={'class': 'input ltr'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'switch-input'}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'switch-input'}),
            'is_superuser': forms.CheckboxInput(attrs={'class': 'switch-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        labels = {
            'username': 'اسم المستخدم',
            'first_name': 'الاسم الأول',
            'last_name': 'الاسم الأخير',
            'email': 'البريد الإلكتروني',
            'is_active': 'الحساب نشط',
            'is_staff': 'يمكنه دخول لوحة التحكم',
            'is_superuser': 'صلاحيات مسؤول كاملة',
        }
        for name, label in labels.items():
            self.fields[name].label = label

    def clean_username(self):
        username = self.cleaned_data['username']
        qs = User.objects.filter(username__iexact=username)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('هذا اسم المستخدم مستخدم من قبل.')
        return username

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password')
        if password:
            user.set_password(password)
        if commit:
            user.save()
        return user


class MediaForm(forms.ModelForm):
    class Meta:
        model = MediaFile
        fields = ['title', 'file', 'alt']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'input'}),
            'alt': forms.TextInput(attrs={'class': 'input'}),
            'file': forms.FileInput(attrs={'class': 'file-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        labels = {'title': 'عنوان الملف', 'file': 'الملف', 'alt': 'النص البديل'}
        for name, label in labels.items():
            self.fields[name].label = label