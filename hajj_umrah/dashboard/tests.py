from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from core.models import Review, ReviewStatus, SiteSettings

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