"""
core/tests.py
The public-site test suite: pages, bookings, booking tracking, reviews and
WhatsApp notifications.

Two habits run through the whole file and are worth knowing before adding
to it: outbound email is asserted against the test outbox rather than sent,
and every test that depends on ordering builds its own trips in setUpTestData
so a test never inherits another test's rows.
"""

from unittest import mock
from urllib.parse import unquote

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Booking, BookingStatus, Review, ReviewStatus, SiteSettings, Trip


class PageViewTests(TestCase):
    """Smoke tests for the public pages and the booking form."""

    @classmethod
    def setUpTestData(cls):
        """Create two active trips and one inactive trip, once per class."""

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
        """The homepage lists the active trips."""

        resp = self.client.get(reverse('core:home'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'رحلة تجريبية')

    def test_trips_list(self):
        """The trips page lists the active trips."""

        resp = self.client.get(reverse('core:trips'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'رحلة تجريبية')

    def test_trip_detail(self):
        """A trip detail page renders for a known slug."""

        resp = self.client.get(reverse('core:trip_detail', args=['trip-test']))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'برنامج السير بالتفصيل')
        self.assertContains(resp, 'الانطلاق')

    def test_about_and_booking_pages(self):
        """The about and booking pages both render."""

        self.assertEqual(self.client.get(reverse('core:about')).status_code, 200)
        self.assertEqual(self.client.get(reverse('core:booking')).status_code, 200)

    def test_booking_post_valid(self):
        """A valid booking POST creates a booking and redirects."""

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
        """An invalid booking POST re-renders the form with errors."""

        resp = self.client.post(reverse('core:booking'), {
            'hu_booking_submit': '1',
            'hu_name': '',
            'hu_phone': '',
        })
        self.assertContains(resp, 'من فضلك أدخل الاسم ورقم الهاتف')

    def test_inactive_trip_hidden(self):
        """An inactive trip is hidden from the public pages."""

        Trip.objects.create(name='مخفية', slug='hidden', is_active=False)
        resp = self.client.get(reverse('core:home'))
        self.assertNotContains(resp, 'مخفية')
        resp2 = self.client.get(reverse('core:trip_detail', args=['hidden']))
        self.assertEqual(resp2.status_code, 404)


@override_settings(DEBUG=False)
class NotFoundTests(TestCase):
    """The custom 404 handler."""

    def test_custom_404(self):
        """An unknown URL returns the branded 404 page."""

        resp = self.client.get('/this-path-does-not-exist/')
        self.assertEqual(resp.status_code, 404)
        self.assertContains(resp, 'الصفحة غير موجودة', status_code=404)


class AdminTests(TestCase):
    """The Django admin."""

    def setUp(self):
        """Log in a superuser for the admin tests."""

        get_user_model().objects.create_superuser('admin', 'admin@example.com', 'secret123')
        SiteSettings.load()

    def test_admin_accessible(self):
        """The admin index is reachable for a superuser."""

        self.client.login(username='admin', password='secret123')
        self.assertEqual(self.client.get('/admin/').status_code, 200)
        self.assertEqual(self.client.get('/admin/core/trip/').status_code, 200)


@override_settings(ADMIN_NOTIFICATION_EMAIL='admin@example.com')
class BookingEmailTests(TestCase):
    """Booking notifications by email."""

    @classmethod
    def setUpTestData(cls):
        """Patch the mail outbox and store the booking POST payload."""

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
        """POST a booking and return the created Booking.

        Returns:
            Booking: The booking the public form just created.
        """

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
        """A booking with an email address sends one admin and one customer email."""

        with mock.patch('core.views.send_mail') as mock_send:
            resp = self._post_booking()

        self.assertContains(resp, 'تم استلام طلبك بنجاح')
        self.assertEqual(mock_send.call_count, 2)

        sent = [call.args for call in mock_send.call_args_list]
        admin_subject = f'حجز جديد: رحلة تجريبية — 2026-12-10 - محمد أحمد'
        self.assertIn((admin_subject, mock.ANY, None, ['admin@example.com']), sent)
        self.assertIn((mock.ANY, mock.ANY, None, ['customer@example.com']), sent)

    def test_booking_without_email_sends_only_admin_email(self):
        """A booking with no email address still notifies the admin."""

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
        """A failing mail backend does not lose the booking."""

        with mock.patch('core.views.logger'), \
                mock.patch('core.views.send_mail', side_effect=Exception('SMTP down')):
            resp = self._post_booking()

        self.assertContains(resp, 'تم استلام طلبك بنجاح')
        self.assertEqual(Booking.objects.filter(phone='01000000000').count(), 1)


class BookingTrackingTests(TestCase):
    """The public booking-tracking page."""

    @classmethod
    def setUpTestData(cls):
        """Create the trips used by the tracking tests."""

        SiteSettings.load()
        Trip.objects.create(
            name='رحلة تتبع', slug='track-trip', trip_type='umrah', is_active=True
        )

    def _make_booking(self, name='أحمد', phone='01012345678'):
        """Create a booking with sensible defaults.

        Returns:
            Booking: The unsaved booking.
        """

        return Booking.objects.create(
            name=name, phone=phone, trip_label='رحلة تتبع — 2026-12-10'
        )

    def test_reference_code_auto_generated_and_unique(self):
        """Every booking gets a unique reference code automatically."""

        b1 = self._make_booking()
        b2 = self._make_booking()
        self.assertRegex(b1.reference_code, r'^HJ-\d{4}-\d{4}$')
        self.assertNotEqual(b1.reference_code, b2.reference_code)
        self.assertEqual(
            Booking.objects.filter(reference_code=b1.reference_code).count(), 1
        )

    def test_booking_created_message_includes_reference_code(self):
        """The "booking created" WhatsApp message carries the reference code."""

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
        """Tracking by reference code finds the booking."""

        booking = self._make_booking()
        resp = self.client.get(reverse('core:track_booking'), {'q': booking.reference_code})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, booking.reference_code)
        self.assertContains(resp, booking.name)
        self.assertContains(resp, 'قيد المراجعة')

    def test_tracking_finds_by_phone(self):
        """Tracking by phone number finds the booking."""

        booking = self._make_booking()
        resp = self.client.get(reverse('core:track_booking'), {'q': booking.phone})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, booking.reference_code)
        self.assertContains(resp, booking.name)

    def test_tracking_unknown_code_shows_message(self):
        """An unknown reference code shows a message instead of a result."""

        resp = self.client.get(reverse('core:track_booking'), {'q': 'HJ-2000-9999'})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'لم نعثر على حجز مطابق')

    def test_tracking_confirmed_booking(self):
        """A confirmed booking shows its status on the tracking page."""

        booking = self._make_booking()
        booking.status = BookingStatus.CONFIRMED
        booking.save()
        resp = self.client.get(reverse('core:track_booking'), {'q': booking.reference_code})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'سيتم التواصل معك قريباً')
        self.assertContains(resp, 'تم التأكيد')

    def _wa_text(self, resp):
        """Return the text encoded in a WhatsApp deep link.

        Returns:
            str: The decoded message the link would send.
        """

        content = resp.content.decode()
        for chunk in content.split('class="track-wa"')[1:]:
            href = chunk.split('href="')[1].split('"')[0]
            return unquote(href.split('?text=')[1])
        return ''

    def test_tracking_confirmed_has_prefilled_whatsapp_link(self):
        """A confirmed booking offers a prefilled WhatsApp link."""

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
        """A pending booking offers a prefilled WhatsApp link."""

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
        """A completed booking shows the completed status."""

        booking = self._make_booking()
        booking.status = BookingStatus.COMPLETED
        booking.save()
        resp = self.client.get(reverse('core:track_booking'), {'q': booking.reference_code})
        self.assertContains(resp, 'تمت رحلتك بنجاح')


class BookingActionTests(TestCase):
    """The dashboard confirm / reject / complete actions."""

    def setUp(self):
        """Create a staff user, a pending booking and a patched WhatsApp sender."""

        self.user = get_user_model().objects.create_user(
            'staff', 'staff@example.com', 'pass123', is_staff=True
        )
        self.client.login(username='staff', password='pass123')
        SiteSettings.load()
        self.booking = Booking.objects.create(name='محمد', phone='01000000000', trip_label='رحلة')

    def test_confirm_updates_status_and_sends_whatsapp(self):
        """Confirming sets the status and sends the WhatsApp message."""

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
        """Rejecting sets the status and sends the WhatsApp message."""

        with mock.patch('dashboard.views.send_whatsapp') as ws:
            resp = self.client.post(reverse('dashboard:booking_reject', args=[self.booking.pk]))
        self.assertRedirects(resp, reverse('dashboard:booking_detail', args=[self.booking.pk]))
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, BookingStatus.REJECTED)
        ws.assert_called_once()
        self.assertIn('❌', ws.call_args.args[1])

    def test_complete_updates_status(self):
        """Completing sets the status without sending a message."""

        self.booking.status = BookingStatus.CONFIRMED
        self.booking.save()
        resp = self.client.post(reverse('dashboard:booking_complete', args=[self.booking.pk]))
        self.assertRedirects(resp, reverse('dashboard:booking_detail', args=[self.booking.pk]))
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, BookingStatus.COMPLETED)

    def test_confirm_requires_post(self):
        """Confirming via GET is not allowed."""

        resp = self.client.get(reverse('dashboard:booking_confirm', args=[self.booking.pk]))
        self.assertEqual(resp.status_code, 405)

    def test_booking_list_status_filter(self):
        """The booking list can be filtered by status."""

        pending = self.booking
        confirmed = Booking.objects.create(
            name='سعيد', phone='01011111111', status=BookingStatus.CONFIRMED
        )
        resp = self.client.get(reverse('dashboard:bookings'), {'status': 'confirmed'})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'سعيد')
        self.assertNotContains(resp, pending.name)


class ReviewTests(TestCase):
    """Customer reviews: submission, moderation and homepage display."""

    @classmethod
    def setUpTestData(cls):
        """Create the trip the reviews will be attached to."""

        cls.trip = Trip.objects.create(
            name='رحلة مراجعات', slug='reviews-trip', trip_type='umrah', is_active=True
        )
        SiteSettings.load()

    def _make(self, name, status, rating=5, with_trip=False):
        """Create a review.

        Returns:
            Review: The unsaved review.
        """

        return Review.objects.create(
            name=name,
            country='مصر',
            rating=rating,
            text=f'رأي {name}',
            trip=self.trip if with_trip else None,
            status=status,
        )

    def test_only_approved_reviews_appear_on_list(self):
        """Only approved reviews appear on the public reviews page."""

        self._make('منشور أحمد', ReviewStatus.APPROVED)
        self._make('قيد محمد', ReviewStatus.PENDING)
        self._make('مرفوض حاتم', ReviewStatus.REJECTED)
        resp = self.client.get(reverse('core:reviews'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'منشور أحمد')
        self.assertNotContains(resp, 'قيد محمد')
        self.assertNotContains(resp, 'مرفوض حاتم')

    def test_reviews_list_page_with_trip_name(self):
        """The reviews page shows the trip name on each review."""

        self._make('منشور مع رحلة', ReviewStatus.APPROVED, with_trip=True)
        resp = self.client.get(reverse('core:reviews'))
        self.assertContains(resp, 'رحلة مراجعات')

    def test_submit_creates_pending_review_and_redirects(self):
        """Submitting a review stores it as pending and redirects."""

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
        """One submission per IP per 24 hours; the rest are rate limited."""

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
        """A filled honeypot field silently swallows the submission."""

        self.client.post(reverse('core:review_submit'), {
            'name': 'روبوت',
            'country': 'مصر',
            'rating': '5',
            'text': 'سبام',
            'website': 'http://spam.example.com',
        })
        self.assertEqual(Review.objects.count(), 0)

    def test_submit_requires_rating(self):
        """A review without a rating is rejected."""

        resp = self.client.post(reverse('core:review_submit'), {
            'name': 'بدون تقييم',
            'country': 'مصر',
            'text': 'نص ما',
        })
        self.assertEqual(Review.objects.count(), 0)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'اختر تقييمك')

    def test_pagination_12_per_page(self):
        """The reviews page paginates 12 per page."""

        for i in range(13):
            Review.objects.create(
                name=f'عميل {i}', country='مصر', rating=5,
                text='نص', status=ReviewStatus.APPROVED,
            )
        resp = self.client.get(reverse('core:reviews'))
        self.assertContains(resp, 'عميل 12')
        self.assertNotContains(resp, 'عميل 0')
        self.assertContains(resp, 'صفحات الآراء')

    def test_home_shows_reviews_after_hero_with_button_when_more_than_three(self):
        """More than three approved reviews adds a "see all" button."""

        for i in range(4):
            self._make(f'منشور الصفحة الرئيسية {i}', ReviewStatus.APPROVED, with_trip=(i == 0))
        self._make('قيد مخفي', ReviewStatus.PENDING)
        resp = self.client.get(reverse('core:home'))
        html = resp.content.decode()
        self.assertContains(resp, 'منشور الصفحة الرئيسية 1')
        self.assertContains(resp, 'منشور الصفحة الرئيسية 3')
        self.assertNotContains(resp, 'قيد مخفي')
        self.assertContains(resp, 'ثقة عملائنا هي رأس مالنا')
        self.assertContains(resp, 'أكثر من 4 عميل سعيد')
        self.assertContains(resp, 'شاهد كل الآراء')
        self.assertLess(html.find('آراء عملائنا'), html.find('id="trips"'))

    def test_home_reviews_section_hidden_without_approved(self):
        """With no approved reviews the homepage hides the section."""

        resp = self.client.get(reverse('core:home'))
        html = resp.content.decode()
        self.assertNotContains(resp, 'ثقة عملائنا هي رأس مالنا')
        self.assertNotContains(resp, 'reviews-home-grid')
        self.assertNotEqual(html.find('id="trips"'), -1)

    def test_home_reviews_button_hidden_when_three_or_less(self):
        """Three or fewer reviews hide the "see all" button."""

        for i in range(3):
            self._make(f'رأي {i}', ReviewStatus.APPROVED)
        resp = self.client.get(reverse('core:home'))
        self.assertContains(resp, 'آراء عملائنا')
        self.assertContains(resp, 'أكثر من 3 عميل سعيد')
        self.assertNotContains(resp, 'شاهد كل الآراء')

class TripPublicOrderingTests(TestCase):
    """The public pages must follow the dashboard's manual trip order."""

    @classmethod
    def setUpTestData(cls):
        """Create trips whose creation order is the opposite of `order`."""

        SiteSettings.load()
        Trip.objects.create(
            name='الرحلة الأولى', slug='pord-1', trip_type='umrah', order=0, is_active=True
        )
        Trip.objects.create(
            name='الرحلة الثانية', slug='pord-2', trip_type='umrah', order=1, is_active=True
        )
        Trip.objects.create(
            name='الرحلة الثالثة', slug='pord-3', trip_type='umrah', order=2, is_active=True
        )

    def test_home_orders_trips_by_order_field(self):
        """The homepage lists trips by the `order` field."""

        resp = self.client.get(reverse('core:home'))
        html = resp.content.decode()
        self.assertLess(html.find('الرحلة الأولى'), html.find('الرحلة الثانية'))
        self.assertLess(html.find('الرحلة الثانية'), html.find('الرحلة الثالثة'))

    def test_trips_list_orders_trips_by_order_field(self):
        """The trips page lists trips by the `order` field."""

        resp = self.client.get(reverse('core:trips'))
        html = resp.content.decode()
        self.assertLess(html.find('الرحلة الأولى'), html.find('الرحلة الثانية'))
        self.assertLess(html.find('الرحلة الثانية'), html.find('الرحلة الثالثة'))

    def test_public_lists_respect_toggled_hidden_ordering(self):
        """The hidden-then-active ordering switch is respected."""

        Trip.objects.filter(slug='pord-2').update(is_active=False)
        resp = self.client.get(reverse('core:home'))
        html = resp.content.decode()
        self.assertIn('الرحلة الأولى', html)
        self.assertNotIn('الرحلة الثانية', html)
        self.assertIn('الرحلة الثالثة', html)


class PriceDisplayTests(TestCase):
    """Every price surface (card, detail page, dashboard) reads price_display."""

    def test_missing_price_reads_as_coming_soon(self):
        """A missing price reads as "coming soon"."""

        self.assertEqual(Trip(name='x').price_display, 'السعر قريباً')

    def test_numeric_price_keeps_thousands_separator(self):
        """A numeric price keeps its thousands separator."""

        self.assertEqual(Trip(name='x', price='37900').price_display, '37,900 ج.م')

    def test_free_text_price_is_shown_verbatim(self):
        """A free-text price is shown verbatim."""

        self.assertEqual(Trip(name='x', price='قريبا').price_display, 'قريبا')

    def test_templates_render_coming_soon_for_priceless_trip(self):
        """The templates render "coming soon" for a priceless trip."""

        Trip.objects.all().delete()
        trip = Trip.objects.create(
            name='رحلة بلا سعر', slug='pd-1', is_active=True, price='',
        )
        for url in (
            reverse('core:home'),
            reverse('core:trips'),
            reverse('core:trip_detail', args=[trip.slug]),
        ):
            html = self.client.get(url).content.decode()
            self.assertIn('السعر قريباً', html, url)
            self.assertNotIn('اكتب لنا', html, url)

    def test_missing_dates_degrade_gracefully(self):
        """Missing dates degrade gracefully instead of raising."""

        Trip.objects.all().delete()
        trip = Trip.objects.create(name='بلا مواعيد', slug='pd-2', is_active=True)
        html = self.client.get(reverse('core:trip_detail', args=[trip.slug])).content.decode()
        self.assertIn('قريباً', html)
        self.assertNotIn(' departures', html)
