from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from support.models import (
    SupportRequest,
    SupportRequestActivityLog,
    SupportRequestInterventionNote,
)
from users.models import User, UserManagementAction


class DashboardRoutingTests(TestCase):
    def test_unfinished_profile_redirects_to_onboarding(self):
        user = User.objects.create_user(
            username='selin',
            email='selin@example.com',
            password='Testpass12345',
            role=User.Roles.VISUALLY_IMPAIRED_STUDENT,
        )
        self.client.force_login(user)

        response = self.client.get(reverse('dashboard:home'))

        self.assertRedirects(response, reverse('users:profile_onboarding'))

    def test_completed_student_profile_redirects_to_student_dashboard(self):
        user = User.objects.create_user(
            username='arda',
            email='arda@example.com',
            password='Testpass12345',
            role=User.Roles.VISUALLY_IMPAIRED_STUDENT,
            profile_completed=True,
        )
        self.client.force_login(user)

        response = self.client.get(reverse('dashboard:home'))

        self.assertRedirects(response, reverse('dashboard:student'))

    def test_completed_advisor_profile_redirects_to_advisor_dashboard(self):
        user = User.objects.create_user(
            username='danisman',
            email='danisman@example.com',
            password='Testpass12345',
            role=User.Roles.ACADEMIC_ADVISOR,
            profile_completed=True,
        )
        self.client.force_login(user)

        response = self.client.get(reverse('dashboard:home'))

        self.assertRedirects(response, reverse('dashboard:advisor'))


class CoordinatorDashboardTests(TestCase):
    def setUp(self):
        self.coordinator = User.objects.create_user(
            username='koordinator',
            email='koordinator@example.com',
            password='Testpass12345',
            role=User.Roles.COORDINATOR,
            profile_completed=True,
        )
        self.student = User.objects.create_user(
            username='ogrenci',
            email='ogrenci@example.com',
            password='Testpass12345',
            role=User.Roles.VISUALLY_IMPAIRED_STUDENT,
            profile_completed=True,
        )
        self.volunteer = User.objects.create_user(
            username='gonullu',
            email='gonullu@example.com',
            password='Testpass12345',
            role=User.Roles.VOLUNTEER_STUDENT,
            profile_completed=True,
        )
        self.passive_user = User.objects.create_user(
            username='pasif_gonullu',
            email='pasif_gonullu@example.com',
            password='Testpass12345',
            role=User.Roles.VOLUNTEER_STUDENT,
            profile_completed=True,
            is_active=False,
        )

    def test_coordinator_dashboard_shows_critical_and_management_sections(self):
        critical_request = SupportRequest.objects.create(
            created_by=self.student,
            title='Kritik erişilebilir ders notu',
            category=SupportRequest.Categories.ACCESSIBLE_MATERIAL,
            course_name='Türk Dili',
            topic='Final özeti',
            description='Ders notunun hızlıca erişilebilir hale getirilmesi gerekiyor.',
            urgency=SupportRequest.Urgencies.HIGH,
            priority=SupportRequest.Priorities.CRITICAL,
            status=SupportRequest.Statuses.OPEN,
        )
        SupportRequestActivityLog.objects.create(
            request=critical_request,
            actor=self.coordinator,
            action_type=SupportRequestActivityLog.ActionTypes.PRIORITY_UPDATED,
            description='Koordinatör talebi kritik önceliğe aldı.',
        )
        SupportRequestInterventionNote.objects.create(
            request=critical_request,
            author=self.coordinator,
            priority=SupportRequestInterventionNote.Priorities.HIGH,
            body='İlk gönüllü eşleşmesi bekleniyor.',
        )
        UserManagementAction.objects.create(
            target_user=self.passive_user,
            actor=self.coordinator,
            action_type=UserManagementAction.ActionTypes.DEACTIVATED,
            note='Kimlik doğrulama tamamlanana kadar hesap pasife alındı.',
        )

        self.client.force_login(self.coordinator)

        response = self.client.get(reverse('dashboard:coordinator'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Kritik erişilebilir ders notu')
        self.assertContains(response, 'İlk gönüllü eşleşmesi bekleniyor.')
        self.assertContains(response, 'Yüksek önem')
        self.assertContains(response, 'Son koordinasyon notları')
        self.assertContains(
            response,
            'Kimlik doğrulama tamamlanana kadar hesap pasife alındı.',
        )

    def test_coordinator_dashboard_counts_unassigned_and_critical_requests(self):
        SupportRequest.objects.create(
            created_by=self.student,
            title='Atanmamış açık talep',
            category=SupportRequest.Categories.ACADEMIC,
            course_name='Matematik',
            topic='Türev',
            description='Birlikte soru çözümü desteği gerekiyor.',
            priority=SupportRequest.Priorities.HIGH,
            status=SupportRequest.Statuses.OPEN,
        )
        SupportRequest.objects.create(
            created_by=self.student,
            assigned_volunteer=self.volunteer,
            title='Eşleşmiş kritik talep',
            category=SupportRequest.Categories.JOINT_STUDY,
            course_name='İstatistik',
            topic='Vize hazırlığı',
            description='Kısa sürede çalışma planı çıkarılmalı.',
            priority=SupportRequest.Priorities.CRITICAL,
            status=SupportRequest.Statuses.MATCHED,
        )
        SupportRequest.objects.create(
            created_by=self.student,
            title='Tamamlanmış kritik talep',
            category=SupportRequest.Categories.VISUAL_DESCRIPTION,
            course_name='Tarih',
            topic='Grafik açıklaması',
            description='Bu talep daha önce tamamlandı.',
            priority=SupportRequest.Priorities.CRITICAL,
            status=SupportRequest.Statuses.COMPLETED,
        )

        self.client.force_login(self.coordinator)

        response = self.client.get(reverse('dashboard:coordinator'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['unmatched_request_count'], 1)
        self.assertEqual(response.context['critical_request_count'], 1)
        self.assertEqual(response.context['inactive_user_count'], 1)

    def test_coordinator_dashboard_renders_accessible_request_badges(self):
        SupportRequest.objects.create(
            created_by=self.student,
            title='Rozet kontrol talebi',
            category=SupportRequest.Categories.ACCESSIBLE_MATERIAL,
            course_name='Türk Dili',
            topic='Final özeti',
            description='Açıklama',
            urgency=SupportRequest.Urgencies.HIGH,
            priority=SupportRequest.Priorities.CRITICAL,
            status=SupportRequest.Statuses.OPEN,
        )
        self.client.force_login(self.coordinator)

        response = self.client.get(reverse('dashboard:coordinator'))

        self.assertContains(response, 'aria-label="Öncelik: Kritik öncelik"', html=False)
        self.assertContains(response, 'aria-label="Durum: Açık"', html=False)
        self.assertContains(response, 'aria-label="Kategori: Erişilebilir materyal hazırlama"', html=False)
        self.assertContains(response, 'href="#icon-alert"', html=False)

    def test_coordinator_dashboard_shows_timing_attention_and_quick_links(self):
        due_soon_request = SupportRequest.objects.create(
            created_by=self.student,
            title='Süresi yaklaşan talep',
            category=SupportRequest.Categories.ACADEMIC,
            course_name='Matematik',
            topic='Limit',
            description='Açıklama',
            status=SupportRequest.Statuses.OPEN,
            requested_completion_date=timezone.localdate() + timedelta(days=2),
        )
        overdue_request = SupportRequest.objects.create(
            created_by=self.student,
            title='Süresi geçen talep',
            category=SupportRequest.Categories.ACADEMIC,
            course_name='Tarih',
            topic='Özet',
            description='Açıklama',
            status=SupportRequest.Statuses.MATCHED,
            requested_completion_date=timezone.localdate() - timedelta(days=1),
        )
        self.client.force_login(self.coordinator)

        response = self.client.get(reverse('dashboard:coordinator'))

        self.assertContains(response, 'Süresi yaklaşan talepler')
        self.assertContains(response, due_soon_request.title)
        self.assertContains(response, overdue_request.title)
        self.assertContains(response, 'Atanmamış aktifler')
        self.assertContains(response, 'Süresi geçenler')
        self.assertEqual(response.context['due_soon_request_count'], 1)
        self.assertEqual(response.context['overdue_request_count'], 1)


class VolunteerDashboardTests(TestCase):
    def setUp(self):
        self.volunteer = User.objects.create_user(
            username='gonullu_panel',
            email='gonullu_panel@example.com',
            password='Testpass12345',
            role=User.Roles.VOLUNTEER_STUDENT,
            profile_completed=True,
            support_topics='Akademik destek, kaynak erişimi',
            availability_notes='Hafta içi öğleden sonra',
        )
        self.student = User.objects.create_user(
            username='ogrenci_panel',
            email='ogrenci_panel@example.com',
            password='Testpass12345',
            role=User.Roles.VISUALLY_IMPAIRED_STUDENT,
            profile_completed=True,
        )

    def test_volunteer_dashboard_shows_score_panel_and_breakdown(self):
        SupportRequest.objects.create(
            created_by=self.student,
            assigned_volunteer=self.volunteer,
            title='Tamamlanan akademik destek',
            category=SupportRequest.Categories.ACADEMIC,
            course_name='Matematik',
            topic='Türev',
            description='Açıklama',
            status=SupportRequest.Statuses.COMPLETED,
        )
        SupportRequest.objects.create(
            created_by=self.student,
            assigned_volunteer=self.volunteer,
            title='Aktif kaynak erişimi',
            category=SupportRequest.Categories.RESOURCE_ACCESS,
            course_name='Tarih',
            topic='Makale taraması',
            description='Açıklama',
            status=SupportRequest.Statuses.IN_PROGRESS,
        )
        SupportRequest.objects.create(
            created_by=self.student,
            title='Açık sınav hazırlık talebi',
            category=SupportRequest.Categories.EXAM_PREPARATION,
            course_name='Fizik',
            topic='Deneme çözümü',
            description='Açıklama',
            status=SupportRequest.Statuses.OPEN,
        )

        self.client.force_login(self.volunteer)

        response = self.client.get(reverse('dashboard:volunteer'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Gönüllü puanı')
        self.assertContains(response, 'Toplam puan')
        self.assertContains(response, 'Katkı seviyesi: Aktif Ortak')
        self.assertContains(response, 'aria-label="Gönüllü seviyesi: Aktif Ortak"', html=False)
        self.assertContains(response, 'Bir sonraki seviye:')
        self.assertContains(response, 'Seviye yolu')
        self.assertContains(response, 'Bu hafta hedefin')
        self.assertContains(response, 'İstekli')
        self.assertContains(response, 'Aktif Ortak')
        self.assertContains(response, 'Yol Arkadaşı')
        self.assertContains(response, 'AURA Elçisi')
        self.assertContains(response, 'En çok katkı verdiğiniz alanlar')
        self.assertContains(response, 'Son tamamlanan destek')
        self.assertContains(response, 'Haftalık seri')
        self.assertContains(response, 'Son 30 gün katkısı')
        self.assertContains(response, 'Seri bonusu')
        self.assertContains(response, '30 gün bonusu')
        self.assertContains(response, 'Tamamlanan akademik destek')
        self.assertContains(response, 'Açık sınav hazırlık talebi')
        self.assertContains(response, 'Kaynak erişimi')
        self.assertEqual(response.context['volunteer_score'], 53)
        self.assertEqual(response.context['completed_support_count'], 1)
        self.assertEqual(response.context['active_support_count'], 1)
        self.assertEqual(response.context['supported_category_count'], 2)
        self.assertEqual(response.context['weekly_streak'], 1)
        self.assertEqual(response.context['recent_30_day_support_count'], 2)
        self.assertEqual(response.context['streak_score_bonus'], 4)
        self.assertEqual(response.context['recent_activity_score_bonus'], 4)
        self.assertEqual(response.context['volunteer_level']['label'], 'Aktif Ortak')
        self.assertEqual(response.context['next_volunteer_level']['label'], 'Yol Arkadaşı')
