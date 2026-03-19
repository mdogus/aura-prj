from django.test import TestCase
from django.urls import reverse

from users.models import User

from .models import Notification


class NotificationCenterTests(TestCase):
    def test_user_can_mark_all_notifications_read(self):
        user = User.objects.create_user(
            username='bildirim',
            email='bildirim@example.com',
            password='Testpass12345',
            role=User.Roles.VOLUNTEER_STUDENT,
            profile_completed=True,
        )
        Notification.objects.create(recipient=user, title='Yeni bildirim')
        self.client.force_login(user)

        response = self.client.post(reverse('notifications:mark_all_read'))

        self.assertRedirects(response, reverse('notifications:list'))
        self.assertEqual(
            Notification.objects.filter(recipient=user, is_read=False).count(),
            0,
        )
        self.assertIsNotNone(Notification.objects.get(recipient=user).read_at)

    def test_unread_filter_empty_state_uses_specific_message(self):
        user = User.objects.create_user(
            username='bildirim2',
            email='bildirim2@example.com',
            password='Testpass12345',
            role=User.Roles.VOLUNTEER_STUDENT,
            profile_completed=True,
        )
        Notification.objects.create(
            recipient=user,
            title='Okunmuş bildirim',
            is_read=True,
        )
        self.client.force_login(user)

        response = self.client.get(reverse('notifications:list'), {'filter': 'unread'})

        self.assertContains(response, 'Okunmamış bildirim yok')

    def test_inactive_user_is_redirected_from_notification_center(self):
        user = User.objects.create_user(
            username='pasif_bildirim',
            email='pasif_bildirim@example.com',
            password='Testpass12345',
            role=User.Roles.VOLUNTEER_STUDENT,
            profile_completed=True,
            is_active=False,
        )
        self.client.force_login(user)

        response = self.client.get(reverse('notifications:list'), follow=True)

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('notifications:list')}",
        )

    def test_opening_notification_marks_it_read_and_redirects(self):
        user = User.objects.create_user(
            username='bildirim3',
            email='bildirim3@example.com',
            password='Testpass12345',
            role=User.Roles.VOLUNTEER_STUDENT,
            profile_completed=True,
        )
        notification = Notification.objects.create(
            recipient=user,
            title='Talebe git',
            target_url='/support/requests/1/',
        )
        self.client.force_login(user)

        response = self.client.get(reverse('notifications:open', args=[notification.pk]))

        self.assertRedirects(response, '/support/requests/1/', fetch_redirect_response=False)
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)
        self.assertIsNotNone(notification.read_at)

    def test_user_can_mark_single_notification_read(self):
        user = User.objects.create_user(
            username='bildirim4',
            email='bildirim4@example.com',
            password='Testpass12345',
            role=User.Roles.VOLUNTEER_STUDENT,
            profile_completed=True,
        )
        notification = Notification.objects.create(recipient=user, title='Tek bildirim')
        self.client.force_login(user)

        response = self.client.post(
            reverse('notifications:mark_read', args=[notification.pk]),
            follow=True,
        )

        self.assertRedirects(response, reverse('notifications:list'))
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)

    def test_notification_list_renders_open_and_mark_read_actions(self):
        user = User.objects.create_user(
            username='bildirim5',
            email='bildirim5@example.com',
            password='Testpass12345',
            role=User.Roles.VOLUNTEER_STUDENT,
            profile_completed=True,
        )
        notification = Notification.objects.create(
            recipient=user,
            title='Aksiyonlu bildirim',
            target_url='/support/requests/1/',
        )
        self.client.force_login(user)

        response = self.client.get(reverse('notifications:list'))

        self.assertContains(
            response,
            reverse('notifications:open', args=[notification.pk]),
        )
        self.assertContains(
            response,
            reverse('notifications:mark_read', args=[notification.pk]),
        )
        self.assertContains(response, 'Okundu işaretle')

    def test_notification_list_renders_type_icon_and_label(self):
        user = User.objects.create_user(
            username='bildirim6',
            email='bildirim6@example.com',
            password='Testpass12345',
            role=User.Roles.VOLUNTEER_STUDENT,
            profile_completed=True,
        )
        Notification.objects.create(
            recipient=user,
            title='Yeni mesaj alındı',
            body='Talep içindeki yeni mesajı görüntüleyin.',
        )
        self.client.force_login(user)

        response = self.client.get(reverse('notifications:list'))

        self.assertContains(response, 'Bildirim türü: Mesaj')
        self.assertContains(response, 'href="#icon-chat"', html=False)
