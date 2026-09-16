from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Booking, SiteSettings, Trip


class PageViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        Trip.objects.create(
            name='رحلة تجريبية',
            slug='trip-test',
            trip_type='umrah',
            price=15000,
            duration='15 يوم',
            departure='2026-12-10',
            return_date='2026-12-24',
            transport='طيران',
            capacity=45,
            remaining=10,
            is_active=True,
            itinerary=[{'title': 'الانطلاق', 'city': 'القاهرة', 'desc': 'وصف'}],
            includes=['تذكرة طيران'],
            excludes=['المصروفات الشخصية'],
        )
        SiteSettings.load()

    def test_home_renders_trips(self):
        resp = self.client.get(reverse('core:home'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'رحلة تجريبية')

    def test_trips_list(self):
        resp = self.client.get(reverse('core:trips'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'رحلة تجريبية')

    def test_trip_detail(self):
        resp = self.client.get(reverse('core:trip_detail', args=['trip-test']))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'برنامج السير بالتفصيل')
        self.assertContains(resp, 'الانطلاق')

    def test_about_and_booking_pages(self):
        self.assertEqual(self.client.get(reverse('core:about')).status_code, 200)
        self.assertEqual(self.client.get(reverse('core:booking')).status_code, 200)

    def test_booking_post_valid(self):
        resp = self.client.post(reverse('core:booking'), {
            'hu_booking_submit': '1',
            'hu_name': 'محمد أحمد',
            'hu_phone': '01000000000',
            'hu_departure': 'رحلة تجريبية — 2026-12-10',
            'hu_type': 'عمرة',
            'hu_people': '2',
            'hu_notes': 'ملاحظات',
        })
        self.assertContains(resp, 'تم استلام طلبك بنجاح')
        self.assertEqual(Booking.objects.filter(phone='01000000000').count(), 1)

    def test_booking_post_invalid(self):
        resp = self.client.post(reverse('core:booking'), {
            'hu_booking_submit': '1',
            'hu_name': '',
            'hu_phone': '',
        })
        self.assertContains(resp, 'من فضلك أدخل الاسم ورقم الهاتف')

    def test_inactive_trip_hidden(self):
        Trip.objects.create(name='مخفية', slug='hidden', is_active=False)
        resp = self.client.get(reverse('core:home'))
        self.assertNotContains(resp, 'مخفية')
        resp2 = self.client.get(reverse('core:trip_detail', args=['hidden']))
        self.assertEqual(resp2.status_code, 404)


@override_settings(DEBUG=False)
class NotFoundTests(TestCase):
    def test_custom_404(self):
        resp = self.client.get('/this-path-does-not-exist/')
        self.assertEqual(resp.status_code, 404)
        self.assertContains(resp, 'الصفحة غير موجودة', status_code=404)


class AdminTests(TestCase):
    def setUp(self):
        get_user_model().objects.create_superuser('admin', 'admin@example.com', 'secret123')
        SiteSettings.load()

    def test_admin_accessible(self):
        self.client.login(username='admin', password='secret123')
        self.assertEqual(self.client.get('/admin/').status_code, 200)
        self.assertEqual(self.client.get('/admin/core/trip/').status_code, 200)