from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from notifications.models import Notification
from support.models import SupportRequest

from .models import User, UserManagementAction


class UserFlowTests(TestCase):
    def test_signup_creates_user_and_logs_them_in(self):
        response = self.client.post(
            reverse("users:signup"),
            {
                "username": "ayse",
                "email": "ayse@example.com",
                "first_name": "Ayse",
                "last_name": "Yilmaz",
                "role": User.Roles.VISUALLY_IMPAIRED_STUDENT,
                "password1": "Testpass12345",
                "password2": "Testpass12345",
            },
        )

        self.assertRedirects(
            response,
            reverse("dashboard:home"),
            fetch_redirect_response=False,
        )
        self.assertTrue(User.objects.filter(username="ayse").exists())

    def test_profile_onboarding_marks_profile_completed(self):
        user = User.objects.create_user(
            username="mert",
            email="mert@example.com",
            password="Testpass12345",
            role=User.Roles.VOLUNTEER_STUDENT,
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse("users:profile_onboarding"),
            {
                "university": "Bogazici University",
                "department": "Computer Engineering",
                "preferred_communication": "Mesajlasma",
                "accessibility_needs": "",
                "support_topics": "Matematik, programlama",
                "availability_notes": "Hafta ici aksam",
            },
        )

        self.assertRedirects(
            response,
            reverse("dashboard:home"),
            fetch_redirect_response=False,
        )
        user.refresh_from_db()
        self.assertTrue(user.profile_completed)

    def test_coordinator_can_toggle_user_active_state(self):
        coordinator = User.objects.create_user(
            username="koord",
            email="koord@example.com",
            password="Testpass12345",
            role=User.Roles.COORDINATOR,
            profile_completed=True,
        )
        managed_user = User.objects.create_user(
            username="gonullu",
            email="gonullu@example.com",
            password="Testpass12345",
            role=User.Roles.VOLUNTEER_STUDENT,
            profile_completed=True,
        )
        self.client.force_login(coordinator)

        response = self.client.post(
            reverse("users:coordinator_user_toggle_active", args=[managed_user.pk]),
            {"note": "Politika ihlali nedeniyle hesap gecici olarak kapatildi."},
        )

        self.assertRedirects(
            response,
            reverse("users:coordinator_user_detail", args=[managed_user.pk]),
        )
        managed_user.refresh_from_db()
        self.assertFalse(managed_user.is_active)
        self.assertTrue(
            UserManagementAction.objects.filter(
                target_user=managed_user,
                actor=coordinator,
                action_type=UserManagementAction.ActionTypes.DEACTIVATED,
            ).exists()
        )

    def test_coordinator_can_filter_users_by_active_state(self):
        coordinator = User.objects.create_user(
            username="koord2",
            email="koord2@example.com",
            password="Testpass12345",
            role=User.Roles.COORDINATOR,
            profile_completed=True,
        )
        User.objects.create_user(
            username="aktif_user",
            email="aktif_user@example.com",
            password="Testpass12345",
            role=User.Roles.VOLUNTEER_STUDENT,
            is_active=True,
            profile_completed=True,
        )
        inactive_user = User.objects.create_user(
            username="pasif_user",
            email="pasif_user@example.com",
            password="Testpass12345",
            role=User.Roles.VOLUNTEER_STUDENT,
            is_active=False,
            profile_completed=True,
        )
        self.client.force_login(coordinator)

        response = self.client.get(
            reverse("users:coordinator_user_list"),
            {"active": "inactive"},
        )

        self.assertContains(response, inactive_user.username)
        self.assertNotContains(response, "aktif_user")

    def test_user_list_shows_summary_metrics_and_quick_filters(self):
        coordinator = User.objects.create_user(
            username="koord_metrics",
            email="koord_metrics@example.com",
            password="Testpass12345",
            role=User.Roles.COORDINATOR,
            profile_completed=True,
        )
        User.objects.create_user(
            username="eksik_profil",
            email="eksik_profil@example.com",
            password="Testpass12345",
            role=User.Roles.VISUALLY_IMPAIRED_STUDENT,
            profile_completed=False,
        )
        self.client.force_login(coordinator)

        response = self.client.get(reverse("users:coordinator_user_list"))

        self.assertContains(response, "Listelenen kullanıcı")
        self.assertContains(response, "Pasif kullanıcılar")
        self.assertContains(response, "Profili eksik olanlar")
        self.assertGreaterEqual(response.context["incomplete_profile_count"], 1)

    def test_user_list_renders_accessible_role_and_state_badges(self):
        coordinator = User.objects.create_user(
            username="koord3",
            email="koord3@example.com",
            password="Testpass12345",
            role=User.Roles.COORDINATOR,
            profile_completed=True,
        )
        volunteer = User.objects.create_user(
            username="rozetli_gonullu",
            email="rozetli_gonullu@example.com",
            password="Testpass12345",
            role=User.Roles.VOLUNTEER_STUDENT,
            is_active=False,
            profile_completed=False,
        )
        self.client.force_login(coordinator)

        response = self.client.get(reverse("users:coordinator_user_list"))

        self.assertContains(response, volunteer.username)
        self.assertContains(response, 'aria-label="Rol: Gönüllü öğrenci"', html=False)
        self.assertContains(response, 'aria-label="Kullanıcı durumu: Pasif"', html=False)
        self.assertContains(response, 'aria-label="Profil durumu: Profil eksik"', html=False)
        self.assertContains(response, 'href="#icon-pause"', html=False)

    def test_user_detail_shows_request_and_notification_summary(self):
        coordinator = User.objects.create_user(
            username="koord_detail",
            email="koord_detail@example.com",
            password="Testpass12345",
            role=User.Roles.COORDINATOR,
            profile_completed=True,
        )
        volunteer = User.objects.create_user(
            username="detay_gonullu",
            email="detay_gonullu@example.com",
            password="Testpass12345",
            role=User.Roles.VOLUNTEER_STUDENT,
            profile_completed=True,
        )
        student = User.objects.create_user(
            username="detay_ogrenci",
            email="detay_ogrenci@example.com",
            password="Testpass12345",
            role=User.Roles.VISUALLY_IMPAIRED_STUDENT,
            profile_completed=True,
        )
        SupportRequest.objects.create(
            created_by=student,
            assigned_volunteer=volunteer,
            title="Detay destek kaydi",
            category=SupportRequest.Categories.ACADEMIC,
            course_name="Matematik",
            topic="Turev",
            description="Aciklama",
            status=SupportRequest.Statuses.IN_PROGRESS,
        )
        Notification.objects.create(
            recipient=volunteer,
            title="Okunmamis bildirim",
            body="Detay paneli icin",
        )
        self.client.force_login(coordinator)

        response = self.client.get(
            reverse("users:coordinator_user_detail", args=[volunteer.pk])
        )

        self.assertContains(response, "Kullanım özeti")
        self.assertContains(response, "Üstlendiği destek")
        self.assertContains(response, "Okunmamış bildirim")
        self.assertEqual(response.context["user_request_summary"]["assigned_count"], 1)
        self.assertEqual(
            response.context["user_request_summary"]["unread_notification_count"],
            1,
        )


class SeedDemoUsersCommandTests(TestCase):
    def test_demo_dataset_creates_sample_users_and_requests(self):
        output = StringIO()

        call_command("seed_demo_users", dataset="demo", stdout=output)

        self.assertTrue(User.objects.filter(username="ogrenci1").exists())
        self.assertTrue(User.objects.filter(username="ogrenci2").exists())
        self.assertTrue(User.objects.filter(username="gonullu1").exists())
        self.assertTrue(User.objects.filter(username="gonullu2").exists())
        self.assertTrue(User.objects.filter(username="danisman2").exists())
        self.assertTrue(User.objects.filter(username="koordinator2").exists())
        self.assertEqual(
            SupportRequest.objects.filter(title__icontains="İstatistik").count(),
            1,
        )
        self.assertEqual(SupportRequest.objects.count(), 7)
        self.assertIn("Seed veri profili hazir: demo", output.getvalue())

    def test_pilot_dataset_reset_removes_demo_data_and_keeps_clean_baseline(self):
        call_command("seed_demo_users", dataset="demo")

        output = StringIO()
        call_command("seed_demo_users", dataset="pilot", reset=True, stdout=output)

        self.assertTrue(User.objects.filter(username="admin").exists())
        self.assertTrue(User.objects.filter(username="koordinator1").exists())
        self.assertTrue(User.objects.filter(username="koordinator2").exists())
        self.assertTrue(User.objects.filter(username="danisman1").exists())
        self.assertTrue(User.objects.filter(username="danisman2").exists())
        self.assertFalse(User.objects.filter(username="ogrenci1").exists())
        self.assertFalse(User.objects.filter(username="ogrenci2").exists())
        self.assertFalse(User.objects.filter(username="gonullu1").exists())
        self.assertFalse(User.objects.filter(username="gonullu2").exists())
        self.assertEqual(
            SupportRequest.objects.filter(
                title__in=[
                    "İstatistik finali için tekrar desteği",
                    "PDF materyalinin erişilebilir özetlenmesi",
                    "Osmanlıca metin için seslendirme desteği",
                    "Grafik ve tablo betimleme desteği",
                    "Kütüphane kaynağına erişim desteği",
                    "Birlikte ders çalışma oturumu planlama",
                    "Kampüs etkinliğine katılım için eşlik",
                ]
            ).count(),
            0,
        )
        self.assertEqual(
            Notification.objects.filter(title__startswith="Demo bildirim").count(),
            0,
        )
        self.assertIn("Pilot baslangic seti", output.getvalue())
