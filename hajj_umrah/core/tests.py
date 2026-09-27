"""
core/tests.py
The public-site test suite: pages, bookings, reviews, the AI chatbot,
the chat HTTP API, WhatsApp notifications and API-key resolution.

Two habits run through the whole file and are worth knowing before adding
to it: every test that would call Groq mocks core.chatbot.requests, and
every test that depends on ordering builds its own trips in setUpTestData
so a test never inherits another test's rows.
"""

import json
import requests
import os
import re
import tempfile
from pathlib import Path
from unittest import mock
from urllib.parse import unquote

from django.core import mail
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from .chatbot import (
    GROQ_MODEL,
    MODEL_FALLBACKS,
    _build_messages,
    _extract_action,
    _resolve_api_key,
    _should_include_trips,
    build_system_prompt,
    detect_booking_intent,
    get_chatbot_response,
)
from .models import Booking, BookingStatus, Review, ReviewStatus, SiteSettings, Trip
from .views import CHAT_RATE_LIMIT_MESSAGE


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


class ChatCostControlTests(TestCase):
    """Token discipline: the account is capped at 6000 tokens/minute.

    Every test here protects one of the three levers that keep a real visitor
    inside that budget: skipping the trip list, caching repeated questions, and
    switching model instead of sleeping on an empty bucket.
    """

    def setUp(self):
        """Clear the reply cache and stub the API key for every test."""

        cache.clear()
        self.addCleanup(cache.clear)
        patcher = mock.patch('core.chatbot._resolve_api_key', return_value='test-key')
        patcher.start()
        self.addCleanup(patcher.stop)

    def ok(self, content='العمرة بـ 37900 جنيه'):
        """Build a fake 200 Groq response.

        Args:
            content (str): The assistant text the "model" returns.

        Returns:
            mock.Mock: A response shaped like requests' Response.
        """

        r = mock.Mock()
        r.status_code = 200
        r.headers = {}
        r.text = ''
        r.json = mock.Mock(return_value={
            'choices': [{'message': {'content': content}, 'finish_reason': 'stop'}],
            'usage': {'prompt_tokens': 100, 'completion_tokens': 10, 'total_tokens': 110},
        })
        return r

    # --- trip list gating ---

    def test_greeting_does_not_send_the_trip_list(self):
        """A greeting is answered without paying for the trip list."""

        with mock.patch('core.chatbot.requests.post', return_value=self.ok()) as post:
            get_chatbot_response('السلام عليكم')
        system = post.call_args.kwargs['json']['messages'][0]['content']
        self.assertNotIn('=== الرحلات', system)

    def test_trip_question_sends_the_trip_list(self):
        """A question about a trip does send the trip list."""

        with mock.patch('core.chatbot.requests.post', return_value=self.ok()) as post:
            get_chatbot_response('عايز أعرف الرحلات')
        system = post.call_args.kwargs['json']['messages'][0]['content']
        self.assertIn('=== الرحلات', system)

    def test_the_most_common_question_matches_a_trip_keyword(self):
        """"الأسعار" folds to "الاسعار", which no longer contains the
        substring "سعر" -- a keyword list without the folded form silently
        drops the single most asked question on the site."""
        self.assertTrue(_should_include_trips('الأسعار'))
        self.assertTrue(_should_include_trips('الاسعار'))
        self.assertTrue(_should_include_trips('كام سعر العمرة؟'))
        self.assertTrue(_should_include_trips('المواعيد Available؟'))

    def test_unrelated_messages_do_not_pay_for_trips(self):
        """Small talk never pays for the trip list."""

        for msg in ['السلام عليكم', 'مين انت', 'ازيك', 'شكرا', '']:
            with self.subTest(msg=msg):
                self.assertFalse(_should_include_trips(msg))

    def test_greeting_prompt_is_much_smaller_than_the_full_one(self):
        """A greeting prompt is dramatically smaller than the full one.

        This is the test that protects the 6000 tokens/minute budget: it
        fails loudly if someone puts the trip list back into every prompt.
        """

        for i in range(4):
            Trip.objects.create(
                name=f'رحلة {i}', slug=f'prompt-size-{i}', is_active=True,
                price=1000 + i, duration='5 يوم',
            )
        full = build_system_prompt(include_trips=True)
        lean = build_system_prompt(include_trips=False)
        self.assertNotIn('=== الرحلات', lean)
        self.assertIn('start_booking', lean, 'booking rules must survive the trim')
        self.assertLess(len(lean), len(full) * 0.75)

    # --- response cache ---

    def test_repeated_question_is_answered_once(self):
        """Asking the same short question twice costs one Groq call."""

        with mock.patch('core.chatbot.requests.post', return_value=self.ok()) as post:
            first = get_chatbot_response('الأسعار')
            second = get_chatbot_response('الأسعار')
        self.assertEqual(first, second)
        self.assertEqual(post.call_count, 1, 'the second identical question must be free')

    def test_cache_key_ignores_spacing_and_hamza_variants(self):
        """Same question, typed differently by two visitors: one Groq call."""
        with mock.patch('core.chatbot.requests.post', return_value=self.ok()) as post:
            get_chatbot_response('الأسعار')
            get_chatbot_response('  الأسعار  ')
        self.assertEqual(post.call_count, 1)

    def test_cache_key_is_stable_across_processes(self):
        """Python randomises str hashing per process, so a hash() key would
        miss in every gunicorn worker while the file cache grows forever."""
        import subprocess
        import sys
        code = (
            'import django,os,sys;'
            'sys.path.insert(0,".");'
            'os.environ.setdefault("DJANGO_SETTINGS_MODULE","config.settings");'
            'django.setup();'
            'from core.chatbot import _cache_key;'
            'print(_cache_key("الأسعار"))'
        )
        outputs = set()
        for seed in ('0', '12345'):
            out = subprocess.run(
                [sys.executable, '-c', code],
                capture_output=True, text=True, env={**os.environ, 'PYTHONHASHSEED': seed},
            )
            outputs.add(out.stdout.strip())
        self.assertEqual(len(outputs), 1, f'cache key is not stable: {outputs}')

    def test_long_or_contextual_questions_are_not_cached(self):
        """Long or conversational questions are never cached."""

        long_question = 'عايز اعرف ' + ('تفاصيل دقيقة عن البرنامج ' * 6)
        self.assertGreater(len(long_question), 60)
        with mock.patch('core.chatbot.requests.post', return_value=self.ok()) as post:
            get_chatbot_response(long_question)
            get_chatbot_response(long_question)          # long: never cached
            get_chatbot_response('الأسعار', [{'role': 'user', 'content': 'مرحبا'}])
            get_chatbot_response('الأسعار', [{'role': 'user', 'content': 'مرحبا'}])
            get_chatbot_response('الأسعار')
            get_chatbot_response('الأسعار')              # bare short: cached
        self.assertEqual(post.call_count, 5,
                         'only the bare short question may be served from cache')

    def test_booking_request_is_never_cached(self):
        """A booking request is never cached, so no stale offer is reused."""

        with mock.patch('core.chatbot.requests.post', return_value=self.ok('تمام')) as post:
            get_chatbot_response('عايز احجز')
            get_chatbot_response('عايز احجز')
        self.assertEqual(post.call_count, 2)

    # --- context window ---

    def test_history_is_trimmed_to_fit_a_small_context_model(self):
        """A 4k model has to lose turns that a 131k one would keep."""
        history = [{'role': 'user', 'content': 'سؤال طويل جداً ' * 60} for _ in range(6)]
        with mock.patch.dict('core.chatbot.MODEL_CONTEXT', {'allam-2-7b': 900}):
            sent = _build_messages('الأسعار', history, model='allam-2-7b')
        self.assertEqual(sent[0]['role'], 'system')
        self.assertEqual(sent[-1]['content'], 'الأسعار')
        self.assertLess(len(sent), 8, 'history must be dropped to fit 900 tokens')

    def test_history_is_kept_when_it_fits(self):
        """History that fits the model context is passed through intact."""

        history = [{'role': 'user', 'content': 'مرحبا'}] * 3
        with mock.patch('core.chatbot.requests.post', return_value=self.ok()) as post:
            get_chatbot_response('الأسعار', history)
        sent = post.call_args.kwargs['json']['messages']
        self.assertEqual(len(sent), 5)   # system + 3 + user

    # --- model chain ---

    def test_chain_starts_with_the_cheapest_model(self):
        """The fallback chain starts with the cheapest model."""

        self.assertEqual(GROQ_MODEL, 'allam-2-7b')
        with mock.patch('core.chatbot.requests.post', return_value=self.ok()) as post:
            get_chatbot_response('الأسعار')
        self.assertEqual(post.call_args.kwargs['json']['model'], 'allam-2-7b')

    def test_every_model_in_the_chain_is_reachable(self):
        """A model that 404s would waste a round trip on every single message."""
        for model in MODEL_FALLBACKS:
            with self.subTest(model=model):
                self.assertNotIn(' ', model)


class ChatApiErrorShapeTests(TestCase):
    """The widget branches on these, so their shape is part of the contract."""

    def setUp(self):
        """Clear the cache, so a cached reply cannot mask a 429 response."""
        cache.clear()

    def test_rate_limited_request_still_returns_json(self):
        """The widget reads reply from a 429 body; an HTML error page there is
        what used to surface as a fake connection failure."""
        url = reverse('core:chat_api')
        with mock.patch('core.views.get_chatbot_turn', return_value=('أهلاً', None)):
            with override_settings(CHAT_RATE_LIMIT_PER_HOUR=1, CHAT_RATE_LIMIT_GLOBAL_PER_HOUR=999):
                first = self.client.post(url, {'message': 'مرحبا'}, content_type='application/json')
                second = self.client.post(url, {'message': 'مرحبا'}, content_type='application/json')
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 429)
        self.assertEqual(second['Content-Type'].split(';')[0], 'application/json')
        self.assertEqual(second.json()['reply'], CHAT_RATE_LIMIT_MESSAGE)


class ChatPageTests(TestCase):
    """The mobile chat is a real page the floating launcher navigates to."""

    def setUp(self):
        """Log in a staff user, since the chat page needs no permissions."""

        SiteSettings.load()

    def test_chat_page_renders_thread(self):
        """The chat page renders its thread container."""

        resp = self.client.get(reverse('core:chat_page'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'مساعد الطوخي الذكي')
        for hook in ('id="chatbot-messages"', 'id="chatbot-input"', 'id="chatbot-send"'):
            self.assertContains(resp, hook)

    def test_chat_page_is_a_standalone_shell(self):
        """No site header/footer, and it must not be indexed: the transcript is
        built by JS, so a crawler would only ever see an empty page."""
        resp = self.client.get(reverse('core:chat_page'))
        self.assertNotContains(resp, 'site-header')
        self.assertNotContains(resp, 'site-footer')
        self.assertContains(resp, 'noindex')

    def test_chat_page_has_csrf_token_for_the_api(self):
        """chatbot.js posts to /api/chat/ with the token from this page."""
        resp = self.client.get(reverse('core:chat_page'))
        self.assertContains(resp, 'name="csrf-token"')

    def test_every_page_exposes_a_csrf_token_for_the_widget(self):
        """The widget used to read the token from a hidden form input that only
        the booking and review pages have, so on every other page it posted an
        empty token, Django answered 403 with an HTML body, and the visitor saw
        "تعذر الاتصال". The meta tag is the only token source that exists on
        every page, so every page the widget appears on must have one."""
        Trip.objects.create(name='رحلة', slug='csrf-trip', is_active=True, price='1000')
        urls = [
            reverse('core:home'),
            reverse('core:trips'),
            reverse('core:about'),
            reverse('core:chat_page'),
            reverse('core:booking'),
            reverse('core:track_booking'),
        ]
        for url in urls:
            with self.subTest(url=url):
                resp = self.client.get(url)
                self.assertEqual(resp.status_code, 200)
                self.assertContains(resp, 'name="csrf-token"')
                match = re.search(r'name="csrf-token" content="([^"]*)"', resp.content.decode())
                self.assertIsNotNone(match, f'{url} has no csrf-token meta')
                self.assertTrue(match.group(1), f'{url} ships an empty csrf token')

    def test_launcher_lives_on_every_page_and_points_at_the_chat_page(self):
        """The floating button is in the shared widget, so it is on the home
        page too, and it hands the mobile path to the JS."""
        resp = self.client.get(reverse('core:home'))
        self.assertContains(resp, 'chat-fab')
        self.assertContains(resp, 'id="chatbot-toggle"')
        self.assertContains(resp, 'data-chat-url="%s"' % reverse('core:chat_page'))

    def test_chat_button_is_not_in_the_header(self):
        """It was pulled out of the nav; it must not creep back in."""
        resp = self.client.get(reverse('core:home'))
        html = resp.content.decode()
        header = html[html.index('<header'):html.index('</header>')]
        self.assertNotIn('chatbot-toggle', header)
        self.assertNotIn('chat-fab', header)


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


class ChatbotPromptTests(TestCase):
    """The prompt is customer-facing data: no blanks, no 'None', no dup units."""

    def setUp(self):
        """Make sure the trip list is empty so prompts are predictable."""

        # 0002_seed_data creates demo trips; the assertions below are about
        # exactly which trips end up in the prompt, so start from a clean slate.
        Trip.objects.all().delete()

    def _trips_block(self):
        """Return just the trip section of the system prompt.

        Returns:
            str: The text between the trip block markers.
        """

        prompt = build_system_prompt(include_trips=True)
        return prompt[prompt.index('=== الرحلات'):prompt.index('=== نهاية')]

    def test_inactive_trips_are_excluded(self):
        """Inactive trips never reach the prompt."""

        Trip.objects.create(
            name='رحلة منشورة', slug='chat-on', is_active=True,
            price='1000', duration='5 يوم',
        )
        Trip.objects.create(name='رحلة مخفية', slug='chat-off', is_active=False)
        block = self._trips_block()
        self.assertIn('رحلة منشورة', block)
        self.assertNotIn('رحلة مخفية', block)

    def test_blank_fields_are_labelled_not_printed_as_none(self):
        """Blank fields are labelled, never printed as "None"."""

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
        """A duration that already has a unit does not get a second one."""

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
        """Dates are formatted as ISO strings, not Python date reprs."""

        Trip.objects.create(
            name='مواعيد', slug='chat-dates', is_active=True,
            departure='2026-12-10', return_date='2026-12-24', remaining=15,
        )
        block = self._trips_block()
        self.assertIn('الانطلاق: 2026-12-10', block)
        self.assertIn('العودة: 2026-12-24', block)
        self.assertIn('الأماكن: 15 مكان', block)

    def test_prompt_tells_model_not_to_invent_a_price(self):
        """The prompt tells the model never to invent a price."""

        prompt = build_system_prompt(include_trips=True)
        self.assertIn('لو الرحلة ليس لها سعر محدد', prompt)
        self.assertIn('السعر قريباً', prompt)
        self.assertIn('201095454012', prompt)

    def test_no_active_trips_falls_back_to_placeholder(self):
        """With no trips the prompt says so instead of leaving an empty block."""

        block = self._trips_block()
        self.assertIn('لا توجد رحلات متاحة', block)


class ChatbotResponseTests(TestCase):
    """get_chatbot_response: the happy path and the failure paths."""

    def setUp(self):
        """Clear the cache and make sure a real API key is never required."""

        # The response cache is file-backed and outlives the test database, so a
        # real answer cached by an earlier test would answer this one instead of
        # the mock.
        cache.clear()
        self.addCleanup(cache.clear)

    @staticmethod
    def fake_response(content='ok', finish='stop'):
        """A real requests.Response stand-in: status_code, text and json()."""
        r = mock.Mock()
        r.status_code = 200
        r.text = content
        r.json.return_value = {
            'choices': [{'message': {'content': content}, 'finish_reason': finish}],
            'usage': {'completion_tokens': 5},
        }
        r.raise_for_status.return_value = None
        return r

    @override_settings(GROQ_API_KEY='')
    @mock.patch.dict(os.environ, {}, clear=True)
    def test_missing_api_key_returns_arabic_fallback(self):
        """A missing API key returns the Arabic "unavailable" fallback."""

        reply = get_chatbot_response('ايش عندكم؟')
        self.assertIn('201095454012', reply)

    def test_timeout_and_error_return_fallbacks(self):
        """Timeouts and connection errors return Arabic fallbacks, not exceptions."""

        import requests

        with mock.patch('core.chatbot.requests.post', side_effect=requests.exceptions.Timeout):
            self.assertIn('بطيء', get_chatbot_response('x'))
        with mock.patch(
            'core.chatbot.requests.post',
            side_effect=requests.exceptions.RequestException('boom'),
        ):
            self.assertIn('201095454012', get_chatbot_response('x'))

    def test_successful_reply_is_returned(self):
        """A successful call returns the model's content."""

        with mock.patch('core.chatbot.requests.post', return_value=self.fake_response('  أهلاً بك  ')):
            reply = get_chatbot_response('ايش عندكم؟')
        self.assertEqual(reply, 'أهلاً بك')

    def test_history_is_trimmed_to_last_six(self):
        """Only the last six history messages are sent."""

        history = [{'role': 'user', 'content': f'm{i}'} for i in range(20)]
        with mock.patch('core.chatbot.requests.post', return_value=self.fake_response()) as post:
            get_chatbot_response('سؤال', history)
        sent = post.call_args.kwargs['json']['messages']
        self.assertEqual(sent[0]['role'], 'system')
        self.assertEqual(len(sent), 8)  # system + 6 history + user
        self.assertEqual(sent[-1]['content'], 'سؤال')

    def test_malformed_history_entries_are_ignored(self):
        """Malformed history entries are dropped instead of raising."""

        history = ['nope', {'role': 'system', 'content': 'x'}, {'role': 'user', 'content': 'y'}]
        with mock.patch('core.chatbot.requests.post', return_value=self.fake_response()) as post:
            get_chatbot_response('سؤال', history)
        sent = post.call_args.kwargs['json']['messages']
        self.assertEqual([m['role'] for m in sent], ['system', 'user', 'user'])


class ChatApiTests(TestCase):
    """POST /api/chat/: CSRF, parsing and the spend caps."""

    def setUp(self):
        """Reset the rate-limit counters and stub the chatbot reply."""

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
        """POST a JSON payload to the chat API.

        Args:
            payload (dict | None): Body to send; a default greeting when None.
            csrf (bool): Attach a valid CSRF token when True.
            **extra: Extra client kwargs (headers, REMOTE_ADDR …).

        Returns:
            django.test.Client: The HTTP response.
        """

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
        with mock.patch('core.views.get_chatbot_turn', return_value='ok') as call:
            resp = self._post(csrf=False)
        self.assertEqual(resp.status_code, 403)
        call.assert_not_called()

    def test_post_with_csrf_token_is_accepted(self):
        """A request carrying a valid CSRF token is accepted."""

        with mock.patch('core.views.get_chatbot_turn', return_value=('أهلاً', None)) as call:
            resp = self._post()
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['reply'], 'أهلاً')
        call.assert_called_once()

    def test_get_is_not_allowed(self):
        """GET on the chat API is not allowed."""

        self.assertEqual(self.client.get(self.url).status_code, 405)

    def test_page_exposes_csrf_token_for_the_widget(self):
        """chatbot.js reads meta[name=csrf-token]; without it every user 403s."""
        html = self.client.get(reverse('core:home')).content.decode()
        match = re.search(r'<meta name="csrf-token" content="([^"]+)"', html)
        self.assertIsNotNone(match, 'csrf-token meta tag missing from base.html')
        # Mirror the browser exactly: token from the page, sent as X-CSRFToken.
        with mock.patch('core.views.get_chatbot_turn', return_value=('أهلاً', None)):
            resp = self.client.post(
                self.url,
                data=json.dumps({'message': 'مرحبا'}),
                content_type='application/json',
                HTTP_X_CSRFTOKEN=match.group(1),
            )
        self.assertEqual(resp.status_code, 200)

    def test_empty_and_malformed_bodies_are_rejected(self):
        """Empty and malformed JSON bodies are rejected."""

        token = self._prime_csrf()
        with mock.patch('core.views.get_chatbot_turn') as call:
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
        """The per-IP cap on chat messages is enforced."""

        with mock.patch('core.views.get_chatbot_turn', return_value=('أهلاً', None)):
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
        with mock.patch('core.views.get_chatbot_turn', return_value=('أهلاً', None)):
            with override_settings(CHAT_RATE_LIMIT_PER_HOUR=2):
                for i in range(4):
                    self._post(
                        HTTP_X_FORWARDED_FOR=f'6.6.6.{i}, 1.2.3.4',
                        REMOTE_ADDR='10.0.0.1',
                    )
        self.assertEqual(cache.get('chat_ip_1.2.3.4'), 4)
        self.assertIsNone(cache.get('chat_ip_6.6.6.0'))

    def test_untrusted_proxy_falls_back_to_remote_addr(self):
        """An untrusted proxy header falls back to REMOTE_ADDR."""

        with mock.patch('core.views.get_chatbot_turn', return_value=('أهلاً', None)):
            with override_settings(TRUST_X_FORWARDED_FOR=False):
                self._post(HTTP_X_FORWARDED_FOR='6.6.6.6', REMOTE_ADDR='1.2.3.4')
        self.assertEqual(cache.get('chat_ip_1.2.3.4'), 1)
        self.assertIsNone(cache.get('chat_ip_6.6.6.6'))

    def test_global_cap_bounds_total_spend(self):
        """The global cap bounds total spend even across many IPs."""

        with mock.patch('core.views.get_chatbot_turn', return_value=('أهلاً', None)):
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


class ResolveApiKeyTests(TestCase):
    """The chatbot must find its key from whichever source the host provides."""

    def test_prefers_process_environment(self):
        """The process environment wins over everything else."""

        with mock.patch.dict(os.environ, {'GROQ_API_KEY': 'from-env'}):
            with override_settings(GROQ_API_KEY='from-settings'):
                self.assertEqual(_resolve_api_key(), 'from-env')

    def test_falls_back_to_django_settings(self):
        """Django settings are used when the environment has no key."""

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
        """With nothing configured the resolver returns empty and logs."""

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
        """A missing .env file is reported, not raised."""

        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.dict(os.environ, {}, clear=True):
                with override_settings(GROQ_API_KEY='', PROJECT_ROOT=Path(tmp) / 'nope'):
                    self.assertEqual(_resolve_api_key(), '')

    def test_chatbot_falls_back_to_whatsapp_when_key_missing(self):
        """With no key the chat API points the visitor at WhatsApp."""

        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.dict(os.environ, {}, clear=True):
                with override_settings(GROQ_API_KEY='', PROJECT_ROOT=Path(tmp)):
                    reply = get_chatbot_response('عايز أعمل عمرة')
        self.assertIn('201095454012', reply)


class BookingIntentTests(TestCase):
    """Booking intent must be deterministic, not model-dependent."""

    def test_positive_intents(self):
        """Clear booking phrasings all return the start_booking action."""

        for msg in ['عايز أحجز عمرة', 'احجزلي', 'أحجز', 'حجز', 'ابعتلي', 'سجلني', 'اكتبلي', 'نفسي أحجز']:
            with self.subTest(msg=msg):
                self.assertEqual(detect_booking_intent(msg), 'start_booking')

    def test_arabic_orthography_variants(self):
        """Orthography variants (إ/أ/آ, ى/ي) are still detected."""

        for msg in ['إحجزلي', 'احجز لى', 'نفسى احجز', 'ابغى حجز']:
            with self.subTest(msg=msg):
                self.assertEqual(detect_booking_intent(msg), 'start_booking')

    def test_negative_intents(self):
        """Ordinary questions do not trigger the booking action."""

        for msg in ['أسعار الحج', 'مفيش رحلة كويسة', 'مين رئيس مصر؟', '', None, 'السلام عليكم']:
            with self.subTest(msg=msg):
                self.assertIsNone(detect_booking_intent(msg))

    def test_action_tag_is_stripped_from_reply(self):
        """The model's JSON action tag is stripped from the reply text."""

        clean, action = _extract_action('يا سلام\n{"action": "start_booking"}\nهبدأ الحجز')
        self.assertEqual(action, 'start_booking')
        self.assertNotIn('action', clean)
        self.assertIn('هبدأ الحجز', clean)

    def test_plain_reply_has_no_action(self):
        """A plain reply produces no action."""

        clean, action = _extract_action('السعر 37900 جنيه')
        self.assertEqual(clean, 'السعر 37900 جنيه')
        self.assertIsNone(action)

    def test_prompt_mentions_booking(self):
        """The system prompt advertises the booking action to the model."""

        self.assertIn('start_booking', build_system_prompt())


class ChatBookingApiTests(TestCase):
    """POST /api/chat/booking/: creating a booking from the chat widget."""

    def setUp(self):
        """Set up a staff user, a trip and a CSRF-primed client."""

        cache.clear()  # the hourly caps are file-backed and outlive the test
        self.trip = Trip.objects.create(
            name='عمرة اختبار', slug='omra-test', trip_type='عمرة', price='50000',
        )
        self.url = '/api/chat/booking/'
        self.payload = {
            'trip_id': self.trip.pk,
            'name': 'أحمد محمد',
            'phone': '01095454012',
            'email': 'ahmed@example.com',
            'number_of_people': 3,
            'notes': 'ملاحظة',
        }

    def post(self, **over):
        """POST the booking payload, with per-test overrides.

        Returns:
            django.test.Client: The HTTP response.
        """

        data = dict(self.payload)
        data.update(over)
        return self.client.post(self.url, data=json.dumps(data), content_type='application/json')

    def test_creates_booking_with_reference_code(self):
        """A valid payload creates a booking with a reference code."""

        r = self.post()
        self.assertEqual(r.status_code, 201)
        body = r.json()
        self.assertTrue(body['ok'])
        self.assertTrue(body['reference_code'].startswith('HJ-'))
        booking = Booking.objects.get(reference_code=body['reference_code'])
        self.assertEqual(booking.name, 'أحمد محمد')
        self.assertEqual(booking.people, 3)
        self.assertEqual(booking.status, BookingStatus.PENDING)
        self.assertEqual(booking.trip_label, 'عمرة اختبار')

    def test_sends_admin_and_customer_email(self):
        """A created booking sends the admin and customer emails."""

        with override_settings(ADMIN_NOTIFICATION_EMAIL='admin@example.com'):
            self.post()
        self.assertEqual(len(mail.outbox), 2)
        self.assertIn('admin@example.com', mail.outbox[0].to)
        self.assertEqual(Booking.objects.count(), 1)

    def test_requires_name(self):
        """A missing name is rejected."""

        self.assertEqual(self.post(name='').status_code, 400)

    def test_rejects_bad_phone(self):
        """A malformed phone number is rejected."""

        self.assertEqual(self.post(phone='abc').status_code, 400)

    def test_rejects_bad_email(self):
        """A malformed email address is rejected."""

        self.assertEqual(self.post(email='nope').status_code, 400)

    def test_rejects_unknown_trip(self):
        """An unknown trip id is rejected."""

        self.assertEqual(self.post(trip_id=99999).status_code, 400)
        self.assertEqual(Booking.objects.count(), 0)

    def test_trip_id_is_optional(self):
        """The trip id is optional."""

        r = self.post(trip_id=None, trip_name='حج على حسب seas')
        self.assertEqual(r.status_code, 201)
        self.assertEqual(Booking.objects.get().trip_label, 'حج على حسب seas')

    def test_rejects_get(self):
        """GET on the booking API is not allowed."""

        self.assertEqual(self.client.get(self.url).status_code, 405)

    def test_rejects_invalid_json(self):
        """An unparseable JSON body is rejected."""

        r = self.client.post(self.url, data='{oops', content_type='application/json')
        self.assertEqual(r.status_code, 400)

    def test_people_is_clamped(self):
        """The people count is clamped into a sane range."""

        r = self.post(number_of_people='9999')
        self.assertEqual(r.status_code, 201)
        self.assertEqual(Booking.objects.get().people, 50)

    def test_get_is_blocked_without_csrf_token(self):
        """No csrf_exempt: a third-party site must not create bookings."""
        c = Client(enforce_csrf_checks=True)
        r = c.post(self.url, data=json.dumps(self.payload), content_type='application/json')
        self.assertEqual(r.status_code, 403)
        self.assertEqual(Booking.objects.count(), 0)

    def test_works_with_csrf_token(self):
        """The booking API works when a CSRF token is supplied."""

        c = Client(enforce_csrf_checks=True)
        c.get('/')
        token = c.cookies['csrftoken'].value
        r = c.post(
            self.url,
            data=json.dumps(self.payload),
            content_type='application/json',
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(r.status_code, 201)
        self.assertEqual(Booking.objects.count(), 1)


class ChatTripsApiTests(TestCase):
    """GET /api/chat/trips/: the trip list the chatbot quotes from."""

    def test_returns_only_active_trips(self):
        """Only active trips are returned."""

        Trip.objects.create(name='نشطة', slug='active-one', is_active=True)
        Trip.objects.create(name='مخفية', slug='hidden-one', is_active=False)
        r = self.client.get('/api/chat/trips/')
        self.assertEqual(r.status_code, 200)
        names = [t['name'] for t in r.json()['trips']]
        self.assertIn('نشطة', names)
        self.assertNotIn('مخفية', names)

    def test_includes_price_display(self):
        """Each trip includes a display-ready price."""

        Trip.objects.create(name='بغير سعر', slug='no-price', price='', is_active=True)
        r = self.client.get('/api/chat/trips/')
        self.assertTrue(r.json()['trips'][-1]['price_display'])


class GroqErrorHandlingTests(TestCase):
    """Each Groq failure mode must map to its own message and log line."""

    def setUp(self):
        """Clear the cache so rate-limit fallbacks are never replayed."""

        cache.clear()
        patcher = mock.patch('core.chatbot._resolve_api_key', return_value='test-key')
        patcher.start()
        self.addCleanup(patcher.stop)

    def reply_for(self, side_effect=None, return_value=None):
        """Call the chatbot with requests.post mocked.

        Args:
            side_effect (list): Per-call exception or response to raise/return.
            return_value (mock.Mock): Single response returned every call.

        Returns:
            str: The reply the visitor would see.
        """

        with mock.patch('core.chatbot.requests.post', **({} if side_effect is None else {'side_effect': side_effect})):
            if side_effect is None:
                with mock.patch('core.chatbot.requests.post', return_value=return_value):
                    return get_chatbot_response('مرحبا')
            return get_chatbot_response('مرحبا')

    def fake(self, status=200, payload=None, text='', headers=None):
        """Build a fake Groq response.

        Args:
            status (int): HTTP status code.
            payload (dict): Decoded JSON body.
            text (str): Raw body, for the error log.
            headers (dict): Response headers, needed by the 429 path.

        Returns:
            mock.Mock: A response shaped like requests' Response.
        """

        r = mock.Mock()
        r.status_code = status
        r.text = text
        # The 429 path logs the response headers, so a mock without a real dict
        # there would blow up on dict(Mock()).
        r.headers = headers or {}
        r.json = mock.Mock(return_value=payload or {})
        return r

    def ok_payload(self, content='أهلاً', finish='stop'):
        """Build a well-formed success body.

        Args:
            content (str): The assistant text.
            finish (str): The finish_reason to report.

        Returns:
            dict: A JSON body Groq would have returned.
        """

        return {'choices': [{'message': {'content': content}, 'finish_reason': finish}],
                'usage': {'completion_tokens': 10}}

    def test_timeout_says_connection_is_slow(self):
        """A timeout tells the visitor the connection is slow."""

        with self.assertLogs('core.chatbot', level='ERROR') as logs:
            reply = self.reply_for(side_effect=requests.exceptions.Timeout())
        self.assertIn('بطيء', reply)
        self.assertNotIn('خطأ في الإعداد', reply)
        self.assertTrue(any('TIMEOUT' in line for line in logs.output), logs.output)

    def test_401_says_configuration_error_and_stops_early(self):
        """A 401 is reported as a configuration error and stops the chain."""

        bad = self.fake(status=401, text='{"error":{"message":"invalid api key"}}')
        with self.assertLogs('core.chatbot', level='ERROR') as logs:
            with mock.patch('core.chatbot.requests.post', return_value=bad) as post:
                reply = get_chatbot_response('مرحبا')
        self.assertIn('خطأ في الإعداد', reply)
        self.assertEqual(post.call_count, 1, 'auth errors must not walk the fallback chain')
        self.assertTrue(any('401' in line for line in logs.output), logs.output)

    def test_429_switches_model_immediately_without_sleeping(self):
        """A 429 must not be retried on the same model.

        The bucket is per model *and* per minute, so sleeping 1.5s and asking
        the same model again spends a round trip to be refused identically, and
        the sleep used to push the whole turn past the host gateway timeout --
        which is what visitors actually saw as "تعذر الاتصال".
        """
        limited = self.fake(status=429, text='{"error":{"message":"Rate limit reached"}}')
        good = self.fake(200, self.ok_payload())
        with mock.patch('core.chatbot.time.sleep') as slept:
            with mock.patch('core.chatbot.requests.post', side_effect=[limited, good]) as post:
                reply = get_chatbot_response('مرحبا')
        self.assertEqual(reply, 'أهلاً')
        used = [c.kwargs['json']['model'] for c in post.call_args_list]
        self.assertEqual(len(used), 2, '429 must go straight to the next model')
        self.assertNotEqual(used[0], used[1])
        slept.assert_not_called()

    def test_persistent_429_walks_every_fallback(self):
        """Groq caps limits per model, so each 429 has to change model."""
        limited = self.fake(status=429, text='{"error":{"message":"Rate limit reached on tokens per minute"}}')
        good = self.fake(200, self.ok_payload())
        # Every model but the last refuses, so the chain has to survive
        # len-1 refusals and still find an answer.
        exhausted = [limited] * (len(MODEL_FALLBACKS) - 1) + [good]
        with mock.patch('core.chatbot.time.sleep') as slept:
            with mock.patch('core.chatbot.requests.post', side_effect=exhausted) as post:
                reply = get_chatbot_response('مرحبا')
        self.assertEqual(reply, 'أهلاً')
        used = [c.kwargs['json']['model'] for c in post.call_args_list]
        self.assertEqual(len(used), len(MODEL_FALLBACKS))
        self.assertEqual(len(set(used)), len(MODEL_FALLBACKS),
                         'every 429 must reach a different model')
        slept.assert_not_called()

    def test_429_exhausted_tells_the_visitor_to_wait(self):
        """When every model is rate limited the visitor is told to wait."""

        limited = self.fake(status=429, text='{"error":{"message":"Rate limit reached"}}')
        with mock.patch('core.chatbot.requests.post', return_value=limited):
            reply = get_chatbot_response('مرحبا')
        self.assertIn('زحمة', reply)
        self.assertIn('201095454012', reply)
        self.assertNotIn('بطيء', reply)

    def test_429_retry_after_header_is_surfaced_to_the_visitor(self):
        """A Retry-After header is surfaced to the visitor."""

        limited = self.fake(status=429, text='{"error":{"message":"Rate limit reached"}}')
        limited.headers = {'retry-after': '42'}
        with mock.patch('core.chatbot.requests.post', return_value=limited):
            reply = get_chatbot_response('مرحبا')
        self.assertIn('42', reply)

    def test_rate_limited_reply_is_never_cached(self):
        """A cached failure would keep failing for the whole TTL even after
        the limit resets, which is worse than no cache at all."""
        limited = self.fake(status=429, text='{"error":{"message":"Rate limit reached"}}')
        with mock.patch('core.chatbot.requests.post', return_value=limited) as post:
            first = get_chatbot_response('الأسعار')
            second = get_chatbot_response('الأسعار')
        self.assertEqual(first, second)
        self.assertEqual(post.call_count, len(MODEL_FALLBACKS) * 2,
                         'a failure must never be served from cache')

    def test_empty_reasoning_reply_is_retried_not_shown_as_busy(self):
        """An empty reasoning-only reply is retried, not shown as "busy"."""

        empty = self.fake(200, self.ok_payload(content='', finish='length'))
        good = self.fake(200, self.ok_payload(content='رد كامل'))
        with mock.patch('core.chatbot.requests.post', side_effect=[empty, good]):
            reply = get_chatbot_response('مرحبا')
        self.assertEqual(reply, 'رد كامل')

    def test_network_exception_logs_its_type(self):
        """A network exception logs its exception type."""

        with self.assertLogs('core.chatbot', level='ERROR') as logs:
            reply = self.reply_for(side_effect=requests.exceptions.ConnectionError('boom'))
        self.assertIn('خطأ', reply)
        self.assertTrue(any('ConnectionError' in line for line in logs.output), logs.output)

    def test_malformed_json_is_a_parse_error(self):
        """A malformed JSON body is treated as a parse error."""

        r = mock.Mock()
        r.status_code = 200
        r.text = 'not json'
        r.json = mock.Mock(side_effect=ValueError('bad'))
        with self.assertLogs('core.chatbot', level='ERROR') as logs:
            with mock.patch('core.chatbot.requests.post', return_value=r):
                reply = get_chatbot_response('مرحبا')
        self.assertIn('خطأ', reply)
        self.assertTrue(any('PARSE' in line for line in logs.output), logs.output)

    def test_request_uses_20s_timeout_and_larger_budget(self):
        """The request uses the 20s timeout and the larger token budget."""

        with mock.patch('core.chatbot.requests.post', return_value=self.fake(200, self.ok_payload())) as post:
            get_chatbot_response('مرحبا')
        self.assertEqual(post.call_args.kwargs['timeout'], 20)
        self.assertEqual(post.call_args.kwargs['json']['max_tokens'], 1200)

    def test_fallback_chain_is_ordered_and_usable(self):
        """Offline guard: the primary must lead a non-empty, duplicate-free chain."""
        self.assertTrue(MODEL_FALLBACKS)
        self.assertEqual(MODEL_FALLBACKS[0], GROQ_MODEL)
        self.assertEqual(len(MODEL_FALLBACKS), len(set(MODEL_FALLBACKS)))
        for model in MODEL_FALLBACKS:
            self.assertIsInstance(model, str)
            self.assertNotIn(' ', model)
