from unittest import mock
from urllib.parse import unquote

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Booking, BookingStatus, Review, ReviewStatus, SiteSettings, Trip


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


@override_settings(ADMIN_NOTIFICATION_EMAIL='admin@example.com')
class BookingEmailTests(TestCase):
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
        )
        SiteSettings.load()

    def _post_booking(self, email='customer@example.com'):
        return self.client.post(reverse('core:booking'), {
            'hu_booking_submit': '1',
            'hu_name': 'محمد أحمد',
            'hu_phone': '01000000000',
            'hu_email': email,
            'hu_departure': 'رحلة تجريبية — 2026-12-10',
            'hu_type': 'عمرة',
            'hu_people': '2',
            'hu_notes': 'ملاحظات',
        })

    def test_booking_sends_admin_and_customer_emails(self):
        with mock.patch('core.views.send_mail') as mock_send:
            resp = self._post_booking()

        self.assertContains(resp, 'تم استلام طلبك بنجاح')
        self.assertEqual(mock_send.call_count, 2)

        sent = [call.args for call in mock_send.call_args_list]
        admin_subject = f'حجز جديد: رحلة تجريبية — 2026-12-10 - محمد أحمد'
        self.assertIn((admin_subject, mock.ANY, None, ['admin@example.com']), sent)
        self.assertIn((mock.ANY, mock.ANY, None, ['customer@example.com']), sent)

    def test_booking_without_email_sends_only_admin_email(self):
        with mock.patch('core.views.send_mail') as mock_send:
            resp = self._post_booking(email='')

        self.assertContains(resp, 'تم استلام طلبك بنجاح')
        self.assertEqual(mock_send.call_count, 1)
        subject, body, from_email, recipients = mock_send.call_args.args
        self.assertEqual(recipients, ['admin@example.com'])
        self.assertIn('حجز جديد', subject)
        for field in ('محمد أحمد', '01000000000', 'رحلة تجريبية', 'عدد الأفراد: 2', 'تاريخ الطلب'):
            self.assertIn(field, body)

    def test_email_failure_does_not_break_booking(self):
        with mock.patch('core.views.logger'), \
                mock.patch('core.views.send_mail', side_effect=Exception('SMTP down')):
            resp = self._post_booking()

        self.assertContains(resp, 'تم استلام طلبك بنجاح')
        self.assertEqual(Booking.objects.filter(phone='01000000000').count(), 1)


class BookingTrackingTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        SiteSettings.load()
        Trip.objects.create(
            name='رحلة تتبع', slug='track-trip', trip_type='umrah', is_active=True
        )

    def _make_booking(self, name='أحمد', phone='01012345678'):
        return Booking.objects.create(
            name=name, phone=phone, trip_label='رحلة تتبع — 2026-12-10'
        )

    def test_reference_code_auto_generated_and_unique(self):
        b1 = self._make_booking()
        b2 = self._make_booking()
        self.assertRegex(b1.reference_code, r'^HJ-\d{4}-\d{4}$')
        self.assertNotEqual(b1.reference_code, b2.reference_code)
        self.assertEqual(
            Booking.objects.filter(reference_code=b1.reference_code).count(), 1
        )

    def test_booking_created_message_includes_reference_code(self):
        with mock.patch('core.views.send_whatsapp') as ws, \
                mock.patch('core.views._send_booking_emails'):
            self.client.post(reverse('core:booking'), {
                'hu_name': 'محمود',
                'hu_phone': '01098765432',
                'hu_departure': 'رحلة تتبع',
                'hu_type': 'عمرة',
            })
        ws.assert_called_once()
        booking = Booking.objects.get(phone='01098765432')
        self.assertIn(booking.reference_code, ws.call_args.args[1])

    def test_tracking_finds_by_code(self):
        booking = self._make_booking()
        resp = self.client.get(reverse('core:track_booking'), {'q': booking.reference_code})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, booking.reference_code)
        self.assertContains(resp, booking.name)
        self.assertContains(resp, 'قيد المراجعة')

    def test_tracking_finds_by_phone(self):
        booking = self._make_booking()
        resp = self.client.get(reverse('core:track_booking'), {'q': booking.phone})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, booking.reference_code)
        self.assertContains(resp, booking.name)

    def test_tracking_unknown_code_shows_message(self):
        resp = self.client.get(reverse('core:track_booking'), {'q': 'HJ-2000-9999'})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'لم نعثر على حجز مطابق')

    def test_tracking_confirmed_booking(self):
        booking = self._make_booking()
        booking.status = BookingStatus.CONFIRMED
        booking.save()
        resp = self.client.get(reverse('core:track_booking'), {'q': booking.reference_code})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'سيتم التواصل معك قريباً')
        self.assertContains(resp, 'تم التأكيد')

    def _wa_text(self, resp):
        content = resp.content.decode()
        for chunk in content.split('class="track-wa"')[1:]:
            href = chunk.split('href="')[1].split('"')[0]
            return unquote(href.split('?text=')[1])
        return ''

    def test_tracking_confirmed_has_prefilled_whatsapp_link(self):
        settings = SiteSettings.load()
        settings.whatsapp = '+20 100 1234567'
        settings.save()
        booking = self._make_booking(name='يوسف')
        booking.status = BookingStatus.CONFIRMED
        booking.save()
        resp = self.client.get(reverse('core:track_booking'), {'q': booking.reference_code})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'wa.me/201001234567?text=')
        self.assertContains(resp, 'تواصل عبر واتساب بخصوص الحجز')
        self.assertContains(resp, 'noopener noreferrer')
        message = self._wa_text(resp)
        self.assertIn('أتابع بخصوص حجزي المؤكد', message)
        self.assertIn(booking.reference_code, message)
        self.assertIn('يوسف', message)
        self.assertIn('رحلة تتبع', message)
        self.assertIn('برجاء تزويدي بتفاصيل الدفع والمواعيد النهائية', message)

    def test_tracking_pending_has_prefilled_whatsapp_link(self):
        settings = SiteSettings.load()
        settings.whatsapp = '+20 100 1234567'
        settings.save()
        booking = self._make_booking(name='كريم')
        booking.status = BookingStatus.PENDING
        booking.save()
        resp = self.client.get(reverse('core:track_booking'), {'q': booking.reference_code})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'wa.me/201001234567?text=')
        self.assertContains(resp, 'تواصل عبر واتساب بخصوص الحجز')
        message = self._wa_text(resp)
        self.assertIn('بتابع بخصوص حجزي قيد المراجعة', message)
        self.assertIn(booking.reference_code, message)
        self.assertIn('كريم', message)
        self.assertIn('برجاء إفادتي بحالة الحجز', message)

    def test_tracking_completed_booking(self):
        booking = self._make_booking()
        booking.status = BookingStatus.COMPLETED
        booking.save()
        resp = self.client.get(reverse('core:track_booking'), {'q': booking.reference_code})
        self.assertContains(resp, 'تمت رحلتك بنجاح')


class BookingActionTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            'staff', 'staff@example.com', 'pass123', is_staff=True
        )
        self.client.login(username='staff', password='pass123')
        SiteSettings.load()
        self.booking = Booking.objects.create(name='محمد', phone='01000000000', trip_label='رحلة')

    def test_confirm_updates_status_and_sends_whatsapp(self):
        with mock.patch('dashboard.views.send_whatsapp') as ws:
            resp = self.client.post(reverse('dashboard:booking_confirm', args=[self.booking.pk]))
        self.assertRedirects(resp, reverse('dashboard:booking_detail', args=[self.booking.pk]))
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, BookingStatus.CONFIRMED)
        self.assertIsNotNone(self.booking.confirmed_at)
        self.assertEqual(self.booking.handled_by, self.user)
        ws.assert_called_once()
        self.assertIn('✅', ws.call_args.args[1])
        self.assertIn(self.booking.reference_code, ws.call_args.args[1])

    def test_reject_updates_status_and_sends_whatsapp(self):
        with mock.patch('dashboard.views.send_whatsapp') as ws:
            resp = self.client.post(reverse('dashboard:booking_reject', args=[self.booking.pk]))
        self.assertRedirects(resp, reverse('dashboard:booking_detail', args=[self.booking.pk]))
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, BookingStatus.REJECTED)
        ws.assert_called_once()
        self.assertIn('❌', ws.call_args.args[1])

    def test_complete_updates_status(self):
        self.booking.status = BookingStatus.CONFIRMED
        self.booking.save()
        resp = self.client.post(reverse('dashboard:booking_complete', args=[self.booking.pk]))
        self.assertRedirects(resp, reverse('dashboard:booking_detail', args=[self.booking.pk]))
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, BookingStatus.COMPLETED)

    def test_confirm_requires_post(self):
        resp = self.client.get(reverse('dashboard:booking_confirm', args=[self.booking.pk]))
        self.assertEqual(resp.status_code, 405)

    def test_booking_list_status_filter(self):
        pending = self.booking
        confirmed = Booking.objects.create(
            name='سعيد', phone='01011111111', status=BookingStatus.CONFIRMED
        )
        resp = self.client.get(reverse('dashboard:bookings'), {'status': 'confirmed'})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'سعيد')
        self.assertNotContains(resp, pending.name)


class ReviewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.trip = Trip.objects.create(
            name='رحلة مراجعات', slug='reviews-trip', trip_type='umrah', is_active=True
        )
        SiteSettings.load()

    def _make(self, name, status, rating=5, with_trip=False):
        return Review.objects.create(
            name=name,
            country='مصر',
            rating=rating,
            text=f'رأي {name}',
            trip=self.trip if with_trip else None,
            status=status,
        )

    def test_only_approved_reviews_appear_on_list(self):
        self._make('منشور أحمد', ReviewStatus.APPROVED)
        self._make('قيد محمد', ReviewStatus.PENDING)
        self._make('مرفوض حاتم', ReviewStatus.REJECTED)
        resp = self.client.get(reverse('core:reviews'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'منشور أحمد')
        self.assertNotContains(resp, 'قيد محمد')
        self.assertNotContains(resp, 'مرفوض حاتم')

    def test_reviews_list_page_with_trip_name(self):
        self._make('منشور مع رحلة', ReviewStatus.APPROVED, with_trip=True)
        resp = self.client.get(reverse('core:reviews'))
        self.assertContains(resp, 'رحلة مراجعات')

    def test_submit_creates_pending_review_and_redirects(self):
        resp = self.client.post(reverse('core:review_submit'), {
            'name': 'أحمد محمود',
            'country': 'مصر',
            'rating': '5',
            'text': 'رحلة ممتازة جداً',
            'trip': self.trip.pk,
        })
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['Location'], reverse('core:reviews'))
        review = Review.objects.get(name='أحمد محمود')
        self.assertEqual(review.status, ReviewStatus.PENDING)
        self.assertEqual(review.trip, self.trip)
        follow = self.client.get(resp['Location'])
        self.assertContains(follow, 'شكراً لك')

    def test_rate_limit_one_submission_per_ip_per_24h(self):
        for i in range(2):
            resp = self.client.post(reverse('core:review_submit'), {
                'name': f'مستخدم {i}',
                'country': 'مصر',
                'rating': '4',
                'text': 'رأي سريع',
            })
            self.assertEqual(resp.status_code, 302)
            resp = self.client.get(resp.url)
        self.assertEqual(Review.objects.count(), 1)

    def test_honeypot_blocks_spam(self):
        self.client.post(reverse('core:review_submit'), {
            'name': 'روبوت',
            'country': 'مصر',
            'rating': '5',
            'text': 'سبام',
            'website': 'http://spam.example.com',
        })
        self.assertEqual(Review.objects.count(), 0)

    def test_submit_requires_rating(self):
        resp = self.client.post(reverse('core:review_submit'), {
            'name': 'بدون تقييم',
            'country': 'مصر',
            'text': 'نص ما',
        })
        self.assertEqual(Review.objects.count(), 0)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'اختر تقييمك')

    def test_pagination_12_per_page(self):
        for i in range(13):
            Review.objects.create(
                name=f'عميل {i}', country='مصر', rating=5,
                text='نص', status=ReviewStatus.APPROVED,
            )
        resp = self.client.get(reverse('core:reviews'))
        self.assertContains(resp, 'عميل 12')
        self.assertNotContains(resp, 'عميل 0')
        self.assertContains(resp, 'صفحات الآراء')

    def test_home_shows_latest_approved_reviews(self):
        self._make('منشور الصفحة الرئيسية', ReviewStatus.APPROVED)
        self._make('قيد مخفي', ReviewStatus.PENDING)
        resp = self.client.get(reverse('core:home'))
        self.assertContains(resp, 'شاهد كل الآراء')
        self.assertContains(resp, 'منشور الصفحة الرئيسية')
        self.assertNotContains(resp, 'قيد مخفي')