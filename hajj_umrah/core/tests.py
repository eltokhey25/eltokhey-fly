import json
import os
import re
import tempfile
from pathlib import Path
from unittest import mock
from urllib.parse import unquote

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from .chatbot import _resolve_api_key, build_system_prompt, get_chatbot_response
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

    def test_home_shows_reviews_after_hero_with_button_when_more_than_three(self):
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
        resp = self.client.get(reverse('core:home'))
        html = resp.content.decode()
        self.assertNotContains(resp, 'ثقة عملائنا هي رأس مالنا')
        self.assertNotContains(resp, 'reviews-home-grid')
        self.assertNotEqual(html.find('id="trips"'), -1)

    def test_home_reviews_button_hidden_when_three_or_less(self):
        for i in range(3):
            self._make(f'رأي {i}', ReviewStatus.APPROVED)
        resp = self.client.get(reverse('core:home'))
        self.assertContains(resp, 'آراء عملائنا')
        self.assertContains(resp, 'أكثر من 3 عميل سعيد')
        self.assertNotContains(resp, 'شاهد كل الآراء')

class TripPublicOrderingTests(TestCase):
    @classmethod
    def setUpTestData(cls):
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
        resp = self.client.get(reverse('core:home'))
        html = resp.content.decode()
        self.assertLess(html.find('الرحلة الأولى'), html.find('الرحلة الثانية'))
        self.assertLess(html.find('الرحلة الثانية'), html.find('الرحلة الثالثة'))

    def test_trips_list_orders_trips_by_order_field(self):
        resp = self.client.get(reverse('core:trips'))
        html = resp.content.decode()
        self.assertLess(html.find('الرحلة الأولى'), html.find('الرحلة الثانية'))
        self.assertLess(html.find('الرحلة الثانية'), html.find('الرحلة الثالثة'))

    def test_public_lists_respect_toggled_hidden_ordering(self):
        Trip.objects.filter(slug='pord-2').update(is_active=False)
        resp = self.client.get(reverse('core:home'))
        html = resp.content.decode()
        self.assertIn('الرحلة الأولى', html)
        self.assertNotIn('الرحلة الثانية', html)
        self.assertIn('الرحلة الثالثة', html)


class ChatbotPromptTests(TestCase):
    """The prompt is customer-facing data: no blanks, no 'None', no dup units."""

    def setUp(self):
        # 0002_seed_data creates demo trips; the assertions below are about
        # exactly which trips end up in the prompt, so start from a clean slate.
        Trip.objects.all().delete()

    def _trips_block(self):
        prompt = build_system_prompt()
        return prompt[prompt.index('=== الرحلات'):prompt.index('=== نهاية')]

    def test_inactive_trips_are_excluded(self):
        Trip.objects.create(
            name='رحلة منشورة', slug='chat-on', is_active=True,
            price='1000', duration='5 يوم',
        )
        Trip.objects.create(name='رحلة مخفية', slug='chat-off', is_active=False)
        block = self._trips_block()
        self.assertIn('رحلة منشورة', block)
        self.assertNotIn('رحلة مخفية', block)

    def test_blank_fields_are_labelled_not_printed_as_none(self):
        Trip.objects.create(name='ناقصة', slug='chat-blank', is_active=True)
        block = self._trips_block()
        self.assertNotIn('None', block)
        self.assertIn('- ناقصة | النوع: العمرة | السعر: قريباً (تواصل معنا)', block)
        self.assertIn('المدة: غير محدد', block)
        self.assertIn('الانطلاق: غير محدد', block)
        self.assertIn('العودة: غير محدد', block)
        self.assertIn('الأماكن: متاح', block)

    def test_priceless_trip_is_still_listed_with_its_name_and_type(self):
        """A trip with no price must stay visible, not be dropped."""
        Trip.objects.create(name='بلا سعر', slug='chat-noprice', is_active=True)
        block = self._trips_block()
        self.assertIn('بلا سعر', block)

    def test_duration_unit_is_not_duplicated(self):
        Trip.objects.create(
            name='مكتوبة', slug='chat-dur-1', is_active=True, duration='15 يوم'
        )
        Trip.objects.create(
            name='رقمية', slug='chat-dur-2', is_active=True, duration='7'
        )
        block = self._trips_block()
        self.assertIn('المدة: 15 يوم', block)
        self.assertIn('المدة: 7 يوم', block)
        self.assertNotIn('يوم يوم', block)

    def test_seeded_dates_are_formatted_iso(self):
        Trip.objects.create(
            name='مواعيد', slug='chat-dates', is_active=True,
            departure='2026-12-10', return_date='2026-12-24', remaining=15,
        )
        block = self._trips_block()
        self.assertIn('الانطلاق: 2026-12-10', block)
        self.assertIn('العودة: 2026-12-24', block)
        self.assertIn('الأماكن: 15 مكان', block)

    def test_prompt_tells_model_not_to_invent_a_price(self):
        prompt = build_system_prompt()
        self.assertIn('لو الرحلة ليس لها سعر محدد', prompt)
        self.assertIn('السعر قريباً', prompt)
        self.assertIn('201095454012', prompt)

    def test_no_active_trips_falls_back_to_placeholder(self):
        block = self._trips_block()
        self.assertIn('لا توجد رحلات متاحة', block)


class ChatbotResponseTests(TestCase):
    @override_settings(GROQ_API_KEY='')
    @mock.patch.dict(os.environ, {}, clear=True)
    def test_missing_api_key_returns_arabic_fallback(self):
        reply = get_chatbot_response('ايش عندكم؟')
        self.assertIn('201095454012', reply)

    def test_timeout_and_error_return_fallbacks(self):
        import requests

        with mock.patch('core.chatbot.requests.post', side_effect=requests.exceptions.Timeout):
            self.assertIn('مشغول', get_chatbot_response('x'))
        with mock.patch(
            'core.chatbot.requests.post',
            side_effect=requests.exceptions.RequestException('boom'),
        ):
            self.assertIn('201095454012', get_chatbot_response('x'))

    def test_successful_reply_is_returned(self):
        payload = {'choices': [{'message': {'content': '  أهلاً بك  '}}]}
        with mock.patch('core.chatbot.requests.post') as post:
            post.return_value.json.return_value = payload
            post.return_value.raise_for_status.return_value = None
            reply = get_chatbot_response('ايش عندكم؟')
        self.assertEqual(reply, 'أهلاً بك')

    def test_history_is_trimmed_to_last_six(self):
        history = [{'role': 'user', 'content': f'm{i}'} for i in range(20)]
        with mock.patch('core.chatbot.requests.post') as post:
            post.return_value.json.return_value = {
                'choices': [{'message': {'content': 'ok'}}]
            }
            post.return_value.raise_for_status.return_value = None
            get_chatbot_response('سؤال', history)
        sent = post.call_args.kwargs['json']['messages']
        self.assertEqual(sent[0]['role'], 'system')
        self.assertEqual(len(sent), 8)  # system + 6 history + user
        self.assertEqual(sent[-1]['content'], 'سؤال')

    def test_malformed_history_entries_are_ignored(self):
        history = ['nope', {'role': 'system', 'content': 'x'}, {'role': 'user', 'content': 'y'}]
        with mock.patch('core.chatbot.requests.post') as post:
            post.return_value.json.return_value = {
                'choices': [{'message': {'content': 'ok'}}]
            }
            post.return_value.raise_for_status.return_value = None
            get_chatbot_response('سؤال', history)
        sent = post.call_args.kwargs['json']['messages']
        self.assertEqual([m['role'] for m in sent], ['system', 'user', 'user'])


class ChatApiTests(TestCase):
    def setUp(self):
        cache.clear()
        self.url = reverse('core:chat_api')
        # The chatbot endpoint must keep CSRF protection, and Django's default
        # test client silently bypasses it, so use a strict one here.
        self.client = Client(enforce_csrf_checks=True)
        Trip.objects.create(
            name='رحلة', slug='api-trip', is_active=True, price='1000', duration='5 يوم'
        )

    def _prime_csrf(self):
        """Load a page so Django sets the csrftoken cookie, like a real visitor."""
        self.client.get(reverse('core:home'))
        return self.client.cookies['csrftoken'].value

    def _post(self, payload=None, csrf=True, **extra):
        if csrf:
            extra.setdefault('HTTP_X_CSRFTOKEN', self._prime_csrf())
        return self.client.post(
            self.url,
            data=json.dumps(payload if payload is not None else {'message': 'مرحبا'}),
            content_type='application/json',
            **extra,
        )

    def test_post_without_csrf_token_is_rejected(self):
        """CSRF must stay on: otherwise any site can spend our Groq credits."""
        with mock.patch('core.views.get_chatbot_response', return_value='ok') as call:
            resp = self._post(csrf=False)
        self.assertEqual(resp.status_code, 403)
        call.assert_not_called()

    def test_post_with_csrf_token_is_accepted(self):
        with mock.patch('core.views.get_chatbot_response', return_value='أهلاً') as call:
            resp = self._post()
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['reply'], 'أهلاً')
        call.assert_called_once()

    def test_get_is_not_allowed(self):
        self.assertEqual(self.client.get(self.url).status_code, 405)

    def test_page_exposes_csrf_token_for_the_widget(self):
        """chatbot.js reads meta[name=csrf-token]; without it every user 403s."""
        html = self.client.get(reverse('core:home')).content.decode()
        match = re.search(r'<meta name="csrf-token" content="([^"]+)"', html)
        self.assertIsNotNone(match, 'csrf-token meta tag missing from base.html')
        # Mirror the browser exactly: token from the page, sent as X-CSRFToken.
        with mock.patch('core.views.get_chatbot_response', return_value='أهلاً'):
            resp = self.client.post(
                self.url,
                data=json.dumps({'message': 'مرحبا'}),
                content_type='application/json',
                HTTP_X_CSRFTOKEN=match.group(1),
            )
        self.assertEqual(resp.status_code, 200)

    def test_empty_and_malformed_bodies_are_rejected(self):
        token = self._prime_csrf()
        with mock.patch('core.views.get_chatbot_response') as call:
            self.assertEqual(self._post({'message': '   '}).status_code, 400)
            self.assertEqual(self._post({}).status_code, 400)
            for body in ('not json', '[1,2]', '"a string"'):
                resp = self.client.post(
                    self.url,
                    data=body,
                    content_type='application/json',
                    HTTP_X_CSRFTOKEN=token,
                )
                self.assertEqual(resp.status_code, 400, body)
        call.assert_not_called()

    def test_per_ip_cap_is_enforced(self):
        with mock.patch('core.views.get_chatbot_response', return_value='أهلاً'):
            with override_settings(CHAT_RATE_LIMIT_PER_HOUR=3):
                codes = [self._post(REMOTE_ADDR='1.2.3.4').status_code for _ in range(5)]
        self.assertEqual(codes[:3], [200, 200, 200])
        self.assertEqual(codes[3:], [429, 429])

    def test_spoofed_x_forwarded_for_does_not_reset_the_cap(self):
        """A client-supplied XFF must not hand out a fresh quota per request.

        Behind the proxy the header arrives as "<anything the client sent>,
        <address the proxy appended>". Only the right-most entry is trusted, so
        every one of these requests shares the real visitor's single bucket.
        """
        with mock.patch('core.views.get_chatbot_response', return_value='أهلاً'):
            with override_settings(CHAT_RATE_LIMIT_PER_HOUR=2):
                for i in range(4):
                    self._post(
                        HTTP_X_FORWARDED_FOR=f'6.6.6.{i}, 1.2.3.4',
                        REMOTE_ADDR='10.0.0.1',
                    )
        self.assertEqual(cache.get('chat_ip_1.2.3.4'), 4)
        self.assertIsNone(cache.get('chat_ip_6.6.6.0'))

    def test_untrusted_proxy_falls_back_to_remote_addr(self):
        with mock.patch('core.views.get_chatbot_response', return_value='أهلاً'):
            with override_settings(TRUST_X_FORWARDED_FOR=False):
                self._post(HTTP_X_FORWARDED_FOR='6.6.6.6', REMOTE_ADDR='1.2.3.4')
        self.assertEqual(cache.get('chat_ip_1.2.3.4'), 1)
        self.assertIsNone(cache.get('chat_ip_6.6.6.6'))

    def test_global_cap_bounds_total_spend(self):
        with mock.patch('core.views.get_chatbot_response', return_value='أهلاً'):
            with override_settings(
                CHAT_RATE_LIMIT_PER_HOUR=100, CHAT_RATE_LIMIT_GLOBAL_PER_HOUR=2
            ):
                codes = [
                    self._post(REMOTE_ADDR=f'10.0.0.{i}').status_code for i in range(4)
                ]
        self.assertEqual(codes[:2], [200, 200])
        self.assertEqual(codes[2:], [429, 429])


class PriceDisplayTests(TestCase):
    """Every price surface (card, detail page, dashboard) reads price_display."""

    def test_missing_price_reads_as_coming_soon(self):
        self.assertEqual(Trip(name='x').price_display, 'السعر قريباً')

    def test_numeric_price_keeps_thousands_separator(self):
        self.assertEqual(Trip(name='x', price='37900').price_display, '37,900 ج.م')

    def test_free_text_price_is_shown_verbatim(self):
        self.assertEqual(Trip(name='x', price='قريبا').price_display, 'قريبا')

    def test_templates_render_coming_soon_for_priceless_trip(self):
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
        Trip.objects.all().delete()
        trip = Trip.objects.create(name='بلا مواعيد', slug='pd-2', is_active=True)
        html = self.client.get(reverse('core:trip_detail', args=[trip.slug])).content.decode()
        self.assertIn('قريباً', html)
        self.assertNotIn(' departures', html)


class ResolveApiKeyTests(TestCase):
    """The chatbot must find its key from whichever source the host provides."""

    def test_prefers_process_environment(self):
        with mock.patch.dict(os.environ, {'GROQ_API_KEY': 'from-env'}):
            with override_settings(GROQ_API_KEY='from-settings'):
                self.assertEqual(_resolve_api_key(), 'from-env')

    def test_falls_back_to_django_settings(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with override_settings(GROQ_API_KEY='from-settings'):
                self.assertEqual(_resolve_api_key(), 'from-settings')

    def test_falls_back_to_dotenv_file(self):
        """Covers hosts where nothing loaded .env before settings ran."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / '.env').write_text('GROQ_API_KEY=from-dotenv-file\n')
            with mock.patch.dict(os.environ, {}, clear=True):
                with override_settings(GROQ_API_KEY='', PROJECT_ROOT=root):
                    self.assertEqual(_resolve_api_key(), 'from-dotenv-file')

    def test_returns_empty_and_logs_when_nothing_is_configured(self):
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.dict(os.environ, {}, clear=True):
                with override_settings(GROQ_API_KEY='', PROJECT_ROOT=Path(tmp)):
                    with self.assertLogs('core.chatbot', level='ERROR') as logs:
                        self.assertEqual(_resolve_api_key(), '')
        self.assertTrue(
            any('not set' in line for line in logs.output),
            logs.output,
        )

    def test_missing_dotenv_is_reported_not_raised(self):
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.dict(os.environ, {}, clear=True):
                with override_settings(GROQ_API_KEY='', PROJECT_ROOT=Path(tmp) / 'nope'):
                    self.assertEqual(_resolve_api_key(), '')

    def test_chatbot_falls_back_to_whatsapp_when_key_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.dict(os.environ, {}, clear=True):
                with override_settings(GROQ_API_KEY='', PROJECT_ROOT=Path(tmp)):
                    reply = get_chatbot_response('عايز أعمل عمرة')
        self.assertIn('201095454012', reply)
