from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from core.models import Review, ReviewStatus, SiteSettings, Trip

User = get_user_model()


@override_settings(DEBUG=False)
class PermissionTests(TestCase):
    def setUp(self):
        self.super_pw = 'SuperPass123'
        self.staff_pw = 'StaffPass123'
        self.normal_pw = 'NormalPass123'
        self.super = User.objects.create_superuser('super', 'super@example.com', self.super_pw)
        self.staff = User.objects.create_user(
            'staff', 'staff@example.com', self.staff_pw, is_staff=True
        )
        self.normal = User.objects.create_user('normal', 'normal@example.com', self.normal_pw)

    def _login(self, username, password):
        self.assertTrue(self.client.login(username=username, password=password))

    # Staff restrictions -----------------------------------------------------
    def test_staff_cannot_access_users_list(self):
        self._login('staff', self.staff_pw)
        resp = self.client.get(reverse('dashboard:users'))
        self.assertEqual(resp.status_code, 403)
        self.assertContains(resp, 'غير مصرح', status_code=403)

    def test_staff_cannot_post_delete_user(self):
        self._login('staff', self.staff_pw)
        resp = self.client.post(reverse('dashboard:user_delete', args=[self.normal.pk]))
        self.assertEqual(resp.status_code, 403)
        self.assertTrue(User.objects.filter(pk=self.normal.pk).exists())

    def test_staff_cannot_promote_self_to_superuser(self):
        self._login('staff', self.staff_pw)
        self.assertEqual(
            self.client.get(reverse('dashboard:user_edit', args=[self.staff.pk])).status_code,
            403,
        )
        resp = self.client.post(
            reverse('dashboard:user_edit', args=[self.staff.pk]),
            {
                'username': 'staff',
                'email': 'staff@example.com',
                'is_staff': 'on',
                'is_active': 'on',
                'is_superuser': 'on',
            },
        )
        self.assertEqual(resp.status_code, 403)
        self.staff.refresh_from_db()
        self.assertFalse(self.staff.is_superuser)

    def test_staff_cannot_add_user(self):
        self._login('staff', self.staff_pw)
        self.assertEqual(
            self.client.get(reverse('dashboard:user_add')).status_code, 403
        )
        resp = self.client.post(
            reverse('dashboard:user_add'),
            {'username': 'hacker', 'password': 'HackPass123!'},
        )
        self.assertEqual(resp.status_code, 403)
        self.assertFalse(User.objects.filter(username='hacker').exists())

    def test_staff_cannot_edit_superuser(self):
        self._login('staff', self.staff_pw)
        resp = self.client.get(reverse('dashboard:user_edit', args=[self.super.pk]))
        self.assertEqual(resp.status_code, 403)

    # Normal users -----------------------------------------------------------
    def test_normal_user_no_dashboard_access(self):
        self._login('normal', self.normal_pw)
        self.assertEqual(
            self.client.get(reverse('dashboard:overview')).status_code, 403
        )
        self.assertEqual(
            self.client.get(reverse('dashboard:users')).status_code, 403
        )

    def test_normal_user_cannot_login_to_dashboard(self):
        resp = self.client.post(
            reverse('dashboard:login'),
            {'username': 'normal', 'password': self.normal_pw},
        )
        self.assertEqual(resp.status_code, 302)
        resp = self.client.get(reverse('dashboard:overview'))
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, f'{reverse("dashboard:login")}?next={reverse("dashboard:overview")}')

    # Superuser privileges ----------------------------------------------------
    def test_superuser_can_access_users(self):
        self._login('super', self.super_pw)
        resp = self.client.get(reverse('dashboard:users'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'staff')
        self.assertContains(resp, 'staff@example.com')
        self.assertContains(resp, 'إضافة مستخدم')

    def test_superuser_can_add_user(self):
        self._login('super', self.super_pw)
        resp = self.client.post(
            reverse('dashboard:user_add'),
            {
                'username': 'newadmin',
                'password': 'NewAdminPass123!',
                'email': 'new@example.com',
                'is_staff': 'on',
                'is_active': 'on',
            },
        )
        user = User.objects.get(username='newadmin')
        self.assertRedirects(resp, reverse('dashboard:user_edit', args=[user.pk]))
        self.assertTrue(user.is_staff)

    def test_superuser_can_change_roles(self):
        self._login('super', self.super_pw)
        resp = self.client.post(
            reverse('dashboard:user_edit', args=[self.staff.pk]),
            {
                'username': 'staff',
                'email': 'staff@example.com',
                'is_staff': 'on',
                'is_active': 'on',
                'is_superuser': 'on',
            },
        )
        self.assertEqual(resp.status_code, 302)
        self.staff.refresh_from_db()
        self.assertTrue(self.staff.is_superuser)

    def test_superuser_can_delete_other_user(self):
        self._login('super', self.super_pw)
        resp = self.client.post(reverse('dashboard:user_delete', args=[self.staff.pk]))
        self.assertRedirects(resp, reverse('dashboard:users'))
        self.assertFalse(User.objects.filter(pk=self.staff.pk).exists())

    def test_superuser_cannot_delete_self(self):
        self._login('super', self.super_pw)
        resp = self.client.post(reverse('dashboard:user_delete', args=[self.super.pk]))
        self.assertEqual(resp.status_code, 403)
        self.assertTrue(User.objects.filter(pk=self.super.pk).exists())

    def test_superuser_cannot_demote_self(self):
        self._login('super', self.super_pw)
        resp = self.client.post(
            reverse('dashboard:user_edit', args=[self.super.pk]),
            {
                'username': 'super',
                'email': 'super@example.com',
                'is_staff': 'on',
                'is_active': 'on',
            },
        )
        self.assertEqual(resp.status_code, 403)
        self.super.refresh_from_db()
        self.assertTrue(self.super.is_superuser)
        self.assertTrue(self.super.is_active)

    def test_superuser_content_access(self):
        self._login('super', self.super_pw)
        self.assertEqual(self.client.get(reverse('dashboard:overview')).status_code, 200)
        self.assertEqual(self.client.get(reverse('dashboard:trips')).status_code, 200)
        self.assertEqual(self.client.get(reverse('dashboard:bookings')).status_code, 200)


@override_settings(DEBUG=False)
class StaffContentAccessTests(TestCase):
    def setUp(self):
        self.staff_pw = 'StaffPass123'
        self.staff = User.objects.create_user(
            'staff', 'staff@example.com', self.staff_pw, is_staff=True
        )
        self.client.login(username='staff', password=self.staff_pw)

    def test_staff_can_manage_content(self):
        self.assertEqual(self.client.get(reverse('dashboard:overview')).status_code, 200)
        self.assertEqual(self.client.get(reverse('dashboard:trips')).status_code, 200)
        self.assertEqual(self.client.get(reverse('dashboard:bookings')).status_code, 200)
        self.assertEqual(self.client.get(reverse('dashboard:settings')).status_code, 200)
        self.assertEqual(self.client.get(reverse('dashboard:sections')).status_code, 200)
        self.assertEqual(self.client.get(reverse('dashboard:media')).status_code, 200)

    def test_staff_does_not_see_users_menu(self):
        resp = self.client.get(reverse('dashboard:overview'))
        self.assertNotContains(resp, 'المستخدمون')


@override_settings(DEBUG=False)
class ReviewActionTests(TestCase):
    def setUp(self):
        self.staff_pw = 'StaffPass123'
        self.staff = User.objects.create_user(
            'staffrev', 'staff@example.com', self.staff_pw, is_staff=True
        )
        self.client.login(username='staffrev', password=self.staff_pw)
        SiteSettings.load()
        self.review = Review.objects.create(
            name='أحمد', country='مصر', rating=5, text='تجربة ممتازة',
            status=ReviewStatus.PENDING,
        )

    def test_approve_publishes_and_sets_approver(self):
        resp = self.client.post(reverse('dashboard:review_approve', args=[self.review.pk]))
        self.assertRedirects(resp, reverse('dashboard:review_detail', args=[self.review.pk]))
        self.review.refresh_from_db()
        self.assertEqual(self.review.status, ReviewStatus.APPROVED)
        self.assertIsNotNone(self.review.approved_at)
        self.assertEqual(self.review.approved_by, self.staff)

    def test_reject_sets_status_and_saves_reason(self):
        resp = self.client.post(
            reverse('dashboard:review_reject', args=[self.review.pk]),
            {'rejection_reason': 'يحتوي إساءة'},
        )
        self.assertRedirects(resp, reverse('dashboard:review_detail', args=[self.review.pk]))
        self.review.refresh_from_db()
        self.assertEqual(self.review.status, ReviewStatus.REJECTED)
        self.assertEqual(self.review.rejection_reason, 'يحتوي إساءة')

    def test_delete_removes_review(self):
        resp = self.client.post(reverse('dashboard:review_delete', args=[self.review.pk]))
        self.assertRedirects(resp, reverse('dashboard:reviews'))
        self.assertFalse(Review.objects.filter(pk=self.review.pk).exists())

    def test_actions_require_post(self):
        self.assertEqual(
            self.client.get(reverse('dashboard:review_approve', args=[self.review.pk])).status_code,
            405,
        )

    def test_list_filter_by_status(self):
        approved = Review.objects.create(
            name='منشور', country='السعودية', rating=4, text='رأي',
            status=ReviewStatus.APPROVED,
        )
        resp = self.client.get(reverse('dashboard:reviews'), {'status': 'approved'})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'منشور')
        self.assertNotContains(resp, self.review.name)

    def test_only_staff_can_manage_reviews(self):
        self.client.logout()
        resp = self.client.post(reverse('dashboard:review_approve', args=[self.review.pk]))
        self.assertEqual(resp.status_code, 302)
        normal_pw = 'NormalPass123'
        normal = User.objects.create_user('normalrev', 'n@example.com', normal_pw)
        self.client.login(username='normalrev', password=normal_pw)
        resp = self.client.get(reverse('dashboard:reviews'))
        self.assertEqual(resp.status_code, 403)

@override_settings(DEBUG=False)
class TripVisibilityTests(TestCase):
    def setUp(self):
        self.staff_pw = 'StaffPass123'
        self.staff = User.objects.create_user(
            'tripvis', 'tripvis@example.com', self.staff_pw, is_staff=True
        )
        self.client.login(username='tripvis', password=self.staff_pw)
        SiteSettings.load()
        self.trip = Trip.objects.create(
            name='رحلة عامة', slug='public-trip', trip_type='umrah', is_active=True
        )

    def _edit_payload(self, trip, is_active):
        payload = {
            'name': trip.name,
            'slug': trip.slug,
            'trip_type': trip.trip_type,
            'description': trip.description,
            'price': trip.price,
            'duration': trip.duration,
            'departure': trip.departure or '',
            'return_date': trip.return_date or '',
            'transport': trip.transport,
            'capacity': trip.capacity or '',
            'remaining': trip.remaining if trip.remaining is not None else '',
            'itinerary_json': '[]',
            'includes_list': '',
            'excludes_list': '',
        }
        if is_active:
            payload['is_active'] = 'on'
        return payload

    def test_hiding_trip_removes_from_public_and_unhiding_restores(self):
        self.assertContains(self.client.get(reverse('core:home')), self.trip.name)

        resp = self.client.post(
            reverse('dashboard:trip_edit', args=[self.trip.slug]),
            self._edit_payload(self.trip, is_active=False),
        )
        self.assertRedirects(resp, reverse('dashboard:trip_edit', args=[self.trip.slug]))
        self.trip.refresh_from_db()
        self.assertFalse(self.trip.is_active)

        self.assertNotContains(self.client.get(reverse('core:home')), self.trip.name)
        self.assertNotContains(self.client.get(reverse('core:trips')), self.trip.name)
        self.assertEqual(
            self.client.get(reverse('core:trip_detail', args=[self.trip.slug])).status_code,
            404,
        )

        resp = self.client.post(
            reverse('dashboard:trip_edit', args=[self.trip.slug]),
            self._edit_payload(self.trip, is_active=True),
        )
        self.assertRedirects(resp, reverse('dashboard:trip_edit', args=[self.trip.slug]))
        self.trip.refresh_from_db()
        self.assertTrue(self.trip.is_active)
        self.assertContains(self.client.get(reverse('core:home')), self.trip.name)
        self.assertEqual(
            self.client.get(reverse('core:trip_detail', args=[self.trip.slug])).status_code,
            200,
        )

    def test_create_trip_with_toggle_off_is_hidden_on_public_site(self):
        resp = self.client.post(reverse('dashboard:trip_add'), {
            'name': 'رحلة جديدة مخفية',
            'slug': 'hidden-new',
            'trip_type': 'umrah',
            'itinerary_json': '[]',
            'includes_list': '',
            'excludes_list': '',
        })
        self.assertRedirects(resp, reverse('dashboard:trip_edit', args=['hidden-new']))
        trip = Trip.objects.get(slug='hidden-new')
        self.assertFalse(trip.is_active)
        self.assertNotContains(self.client.get(reverse('core:home')), 'رحلة جديدة مخفية')
        self.assertEqual(
            self.client.get(reverse('core:trip_detail', args=['hidden-new'])).status_code,
            404,
        )

    def test_trips_list_shows_status_badges_and_order_controls(self):
        hidden = Trip.objects.create(
            name='رحلة مخفية', slug='hidden-list', trip_type='umrah', is_active=False
        )
        resp = self.client.get(reverse('dashboard:trips'))
        self.assertContains(resp, 'مفعّلة')
        self.assertContains(resp, 'مخفية')
        self.assertContains(resp, 'استخدم الأسهم لترتيب ظهور الرحلات على الموقع')
        self.assertContains(
            resp, reverse('dashboard:trip_move_up', args=[self.trip.pk])
        )
        self.assertContains(
            resp, reverse('dashboard:trip_move_down', args=[hidden.pk])
        )

    def test_trips_list_filters_status(self):
        hidden = Trip.objects.create(
            name='مرشّحة فقط', slug='hidden-filter', trip_type='umrah', is_active=False
        )
        resp = self.client.get(reverse('dashboard:trips'), {'stock': 'hidden'})
        self.assertContains(resp, 'مرشّحة فقط')
        self.assertNotContains(resp, self.trip.name)
        resp = self.client.get(reverse('dashboard:trips'), {'stock': 'available'})
        self.assertContains(resp, self.trip.name)
        self.assertNotContains(resp, 'مرشّحة فقط')


@override_settings(DEBUG=False)
class TripOrderTests(TestCase):
    def setUp(self):
        self.staff_pw = 'StaffPass123'
        self.staff = User.objects.create_user(
            'tripord', 'tripord@example.com', self.staff_pw, is_staff=True
        )
        self.client.login(username='tripord', password=self.staff_pw)
        SiteSettings.load()
        self.t1 = Trip.objects.create(name='رحلة أولى', slug='ord-1', trip_type='umrah', order=0)
        self.t2 = Trip.objects.create(name='رحلة ثانية', slug='ord-2', trip_type='umrah', order=1)
        self.t3 = Trip.objects.create(name='رحلة ثالثة', slug='ord-3', trip_type='umrah', order=2)
        Trip.objects.exclude(pk__in=[self.t1.pk, self.t2.pk, self.t3.pk]).delete()

    def _orders_by_slug(self):
        return {t.slug: t.order for t in Trip.objects.all()}

    def test_move_up_swaps_orders(self):
        resp = self.client.post(reverse('dashboard:trip_move_up', args=[self.t2.pk]))
        self.assertRedirects(resp, reverse('dashboard:trips'))
        orders = self._orders_by_slug()
        self.assertEqual(orders['ord-2'], 0)
        self.assertEqual(orders['ord-1'], 1)
        self.assertEqual(orders['ord-3'], 2)

    def test_move_down_swaps_orders(self):
        resp = self.client.post(reverse('dashboard:trip_move_down', args=[self.t2.pk]))
        self.assertRedirects(resp, reverse('dashboard:trips'))
        orders = self._orders_by_slug()
        self.assertEqual(orders['ord-1'], 0)
        self.assertEqual(orders['ord-2'], 2)
        self.assertEqual(orders['ord-3'], 1)

    def test_move_up_on_first_does_nothing(self):
        resp = self.client.post(reverse('dashboard:trip_move_up', args=[self.t1.pk]))
        self.assertRedirects(resp, reverse('dashboard:trips'))
        orders = self._orders_by_slug()
        self.assertEqual(orders, {'ord-1': 0, 'ord-2': 1, 'ord-3': 2})

    def test_move_down_on_last_does_nothing(self):
        resp = self.client.post(reverse('dashboard:trip_move_down', args=[self.t3.pk]))
        self.assertRedirects(resp, reverse('dashboard:trips'))
        orders = self._orders_by_slug()
        self.assertEqual(orders, {'ord-1': 0, 'ord-2': 1, 'ord-3': 2})

    def test_move_with_ties_still_reorders(self):
        equal = Trip.objects.create(
            name='مساوٍ', slug='ord-eq', trip_type='umrah', order=1
        )
        resp = self.client.post(reverse('dashboard:trip_move_up', args=[equal.pk]))
        self.assertRedirects(resp, reverse('dashboard:trips'))
        orders = self._orders_by_slug()
        self.assertEqual(orders['ord-eq'], 0)
        self.assertEqual(orders['ord-2'], 2)

    def test_move_requires_post(self):
        resp = self.client.get(reverse('dashboard:trip_move_up', args=[self.t2.pk]))
        self.assertEqual(resp.status_code, 405)
        resp = self.client.get(reverse('dashboard:trip_move_down', args=[self.t2.pk]))
        self.assertEqual(resp.status_code, 405)

    def test_move_requires_staff(self):
        self.client.logout()
        normal_pw = 'NormalPass123'
        normal = User.objects.create_user('normaltrip', 'n@example.com', normal_pw)
        self.client.login(username='normaltrip', password=normal_pw)
        resp = self.client.post(reverse('dashboard:trip_move_up', args=[self.t2.pk]))
        self.assertEqual(resp.status_code, 403)
        orders = self._orders_by_slug()
        self.assertEqual(orders, {'ord-1': 0, 'ord-2': 1, 'ord-3': 2})

        self.client.logout()
        resp = self.client.post(reverse('dashboard:trip_move_up', args=[self.t2.pk]))
        self.assertEqual(resp.status_code, 302)
