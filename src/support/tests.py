from datetime import datetime, timedelta
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from notifications.models import Notification
from users.models import User

from .models import (
    RequestMaterial,
    RequestMessage,
    SupportRequest,
    SupportRequestActivityLog,
    SupportRequestInterventionNote,
)


class StudentRequestFlowTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            username="zeynep",
            email="zeynep@example.com",
            password="Testpass12345",
            role=User.Roles.VISUALLY_IMPAIRED_STUDENT,
            profile_completed=True,
        )
        self.other_student = User.objects.create_user(
            username="elif",
            email="elif@example.com",
            password="Testpass12345",
            role=User.Roles.VISUALLY_IMPAIRED_STUDENT,
            profile_completed=True,
        )
        self.coordinator = User.objects.create_user(
            username="koord",
            email="koord@example.com",
            password="Testpass12345",
            role=User.Roles.COORDINATOR,
            profile_completed=True,
        )
        self.advisor = User.objects.create_user(
            username="danisman",
            email="danisman@example.com",
            password="Testpass12345",
            role=User.Roles.ACADEMIC_ADVISOR,
            profile_completed=True,
        )
        self.volunteer = User.objects.create_user(
            username="gonullu",
            email="gonullu@example.com",
            password="Testpass12345",
            role=User.Roles.VOLUNTEER_STUDENT,
            profile_completed=True,
        )
        self.other_volunteer = User.objects.create_user(
            username="gonullu2",
            email="gonullu2@example.com",
            password="Testpass12345",
            role=User.Roles.VOLUNTEER_STUDENT,
            profile_completed=True,
        )

    def test_student_can_create_request(self):
        self.client.force_login(self.student)

        response = self.client.post(
            reverse("support:student_request_create"),
            {
                "title": "Istatistik finali icin destek",
                "category": SupportRequest.Categories.ACADEMIC,
                "course_name": "Istatistik 101",
                "topic": "Hipotez testleri",
                "description": "Notlarin ozetlenmesine ve tekrar planina ihtiyacim var.",
                "urgency": SupportRequest.Urgencies.HIGH,
                "duration_value": 3,
                "duration_unit": SupportRequest.DurationUnits.DAY,
                "requested_completion_date": (timezone.localdate() + timedelta(days=14)).isoformat(),
                "preferred_timing": "Hafta ici 18:00 sonrasi",
            },
        )

        self.assertRedirects(response, reverse("support:student_request_list"))
        self.assertTrue(
            SupportRequest.objects.filter(
                created_by=self.student,
                title="Istatistik finali icin destek",
            ).exists()
        )
        request_item = SupportRequest.objects.get(
            created_by=self.student,
            title="Istatistik finali icin destek",
        )
        self.assertEqual(request_item.duration_value, 3)
        self.assertEqual(request_item.duration_unit, SupportRequest.DurationUnits.DAY)
        expected_date = (timezone.localdate() + timedelta(days=14)).isoformat()
        self.assertEqual(str(request_item.requested_completion_date), expected_date)
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.coordinator,
                title="Yeni destek talebi oluşturuldu",
            ).exists()
        )
        self.assertTrue(
            SupportRequestActivityLog.objects.filter(
                request__title="Istatistik finali icin destek",
                action_type=SupportRequestActivityLog.ActionTypes.REQUEST_CREATED,
            ).exists()
        )

    def test_student_request_form_shows_updated_category_options(self):
        self.client.force_login(self.student)

        response = self.client.get(reverse("support:student_request_create"))

        self.assertContains(response, "Erişilebilir materyal hazırlama")
        self.assertContains(response, "Seslendirme")
        self.assertContains(response, "Sosyal etkinlik")
        self.assertContains(response, "Talebinize en uygun kategoriyi seçin.")
        self.assertContains(
            response,
            "Lütfen bir kategori seçin. Seçtiğiniz kategoriye ait kısa açıklama burada görünür.",
        )

    def test_student_request_list_renders_accessible_badges(self):
        SupportRequest.objects.create(
            created_by=self.student,
            title="Rozetli talep",
            category=SupportRequest.Categories.ACADEMIC,
            course_name="Matematik",
            topic="Türev",
            description="Açıklama",
            urgency=SupportRequest.Urgencies.MEDIUM,
            status=SupportRequest.Statuses.OPEN,
        )
        self.client.force_login(self.student)

        response = self.client.get(reverse("support:student_request_list"))

        self.assertContains(response, 'aria-label="Durum: Açık"', html=False)
        self.assertContains(response, 'aria-label="Aciliyet: Orta"', html=False)
        self.assertContains(response, 'aria-label="Kategori: Akademik destek"', html=False)
        self.assertContains(response, 'href="#icon-dot"', html=False)

    def test_duration_display_includes_automatic_deadline_and_remaining_time(self):
        request_item = SupportRequest.objects.create(
            created_by=self.student,
            title="Süreli talep",
            category=SupportRequest.Categories.ACADEMIC,
            course_name="Matematik",
            topic="Türev",
            description="Açıklama",
            duration_value=3,
            duration_unit=SupportRequest.DurationUnits.DAY,
        )
        request_item.created_at = timezone.make_aware(datetime(2026, 3, 19, 10, 0))
        request_item.save(update_fields=["created_at"])

        with patch("support.models.timezone.localdate", return_value=datetime(2026, 3, 19).date()):
            self.assertEqual(request_item.requested_duration_display, "3 gün içinde (22.03.2026 tarihine kadar)")
            self.assertEqual(request_item.remaining_time_display, "3 gün kaldı")
            self.assertIn("22.03.2026 tarihine kadar", request_item.timing_summary)
            self.assertIn("3 gün kaldı", request_item.timing_summary)

    def test_student_list_only_shows_own_requests(self):
        SupportRequest.objects.create(
            created_by=self.student,
            title="Benim talebim",
            category=SupportRequest.Categories.ACADEMIC,
            course_name="Fizik",
            topic="Optik",
            description="Aciklama",
        )
        SupportRequest.objects.create(
            created_by=self.other_student,
            title="Baska talep",
            category=SupportRequest.Categories.ACADEMIC,
            course_name="Kimya",
            topic="Denge",
            description="Aciklama",
        )

        self.client.force_login(self.student)
        response = self.client.get(reverse("support:student_request_list"))

        self.assertContains(response, "Benim talebim")
        self.assertNotContains(response, "Baska talep")

    def test_student_request_list_splits_active_and_closed_requests(self):
        SupportRequest.objects.create(
            created_by=self.student,
            title="Aktif talep kaydı",
            category=SupportRequest.Categories.ACADEMIC,
            course_name="Fizik",
            topic="Optik",
            description="Açıklama",
            status=SupportRequest.Statuses.OPEN,
        )
        SupportRequest.objects.create(
            created_by=self.student,
            title="Tamamlanan talep kaydı",
            category=SupportRequest.Categories.ACADEMIC,
            course_name="Kimya",
            topic="Denge",
            description="Açıklama",
            status=SupportRequest.Statuses.COMPLETED,
        )
        self.client.force_login(self.student)

        response = self.client.get(reverse("support:student_request_list"))

        self.assertContains(response, "Aktif talepler")
        self.assertContains(response, "Tamamlanan ve kapanan talepler")
        self.assertContains(response, "Aktif talep kaydı")
        self.assertContains(response, "Tamamlanan talep kaydı")

    def test_student_request_form_requires_duration_unit_when_duration_exists(self):
        self.client.force_login(self.student)

        response = self.client.post(
            reverse("support:student_request_create"),
            {
                "title": "Sure bilgisi eksik talep",
                "category": SupportRequest.Categories.ACADEMIC,
                "course_name": "Istatistik 101",
                "topic": "Hipotez testleri",
                "description": "Kisa surede destek ihtiyaci var.",
                "urgency": SupportRequest.Urgencies.HIGH,
                "duration_value": 3,
                "preferred_timing": "Hafta ici",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Süre girdiğinizde süre birimini de seçin.")

    def test_student_request_form_rejects_past_completion_date(self):
        self.client.force_login(self.student)
        past_date = (timezone.localdate() - timedelta(days=1)).isoformat()

        response = self.client.post(
            reverse("support:student_request_create"),
            {
                "title": "Gecmis tarihli talep",
                "category": SupportRequest.Categories.ACADEMIC,
                "course_name": "Istatistik 101",
                "topic": "Hipotez testleri",
                "description": "Gecmis tarih kabul edilmemeli.",
                "urgency": SupportRequest.Urgencies.HIGH,
                "requested_completion_date": past_date,
                "preferred_timing": "Hafta ici",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Son tarih bugünden daha eski bir gün olamaz.")

    def test_student_can_update_request_status(self):
        request_item = SupportRequest.objects.create(
            created_by=self.student,
            title="Tamamlanacak talep",
            category=SupportRequest.Categories.ACADEMIC,
            course_name="Matematik",
            topic="Integral",
            description="Aciklama",
        )
        self.client.force_login(self.student)

        response = self.client.post(
            reverse("support:student_request_status", args=[request_item.pk]),
            {"status": SupportRequest.Statuses.COMPLETED},
        )

        self.assertRedirects(
            response,
            reverse("support:student_request_detail", args=[request_item.pk]),
        )
        request_item.refresh_from_db()
        self.assertEqual(request_item.status, SupportRequest.Statuses.COMPLETED)

    def test_completed_student_request_detail_shows_closed_state_message(self):
        request_item = SupportRequest.objects.create(
            created_by=self.student,
            title="Kapanmis talep",
            category=SupportRequest.Categories.ACADEMIC,
            course_name="Matematik",
            topic="Limit",
            description="Aciklama",
            status=SupportRequest.Statuses.COMPLETED,
        )
        self.client.force_login(self.student)

        response = self.client.get(
            reverse("support:student_request_detail", args=[request_item.pk])
        )

        self.assertContains(response, "Bu talep artık kapalı")

    def test_student_request_detail_uses_student_friendly_material_copy(self):
        request_item = SupportRequest.objects.create(
            created_by=self.student,
            title="Kaynak dosya talebi",
            category=SupportRequest.Categories.ACADEMIC,
            course_name="Matematik",
            topic="Limit",
            description="Açıklama",
        )
        self.client.force_login(self.student)

        response = self.client.get(
            reverse("support:student_request_detail", args=[request_item.pk]),
            {"section": "materials"},
        )

        self.assertContains(response, "Kaynak dosyalar")
        self.assertContains(
            response,
            "Gönüllünün incelemesini istediğiniz ders notu, PDF, slayt veya görselleri burada paylaşabilirsiniz.",
        )
        self.assertContains(response, "Dosyayı ekle")

    def test_student_request_detail_can_open_messages_section(self):
        request_item = SupportRequest.objects.create(
            created_by=self.student,
            title="Mesaj sekmeli talep",
            category=SupportRequest.Categories.ACADEMIC,
            course_name="Matematik",
            topic="Limit",
            description="Aciklama",
            assigned_volunteer=self.volunteer,
            status=SupportRequest.Statuses.MATCHED,
        )
        RequestMessage.objects.create(
            request=request_item,
            author=self.student,
            body="Mesajlar bolumunu test ediyorum.",
        )
        self.client.force_login(self.student)

        response = self.client.get(
            reverse("support:student_request_detail", args=[request_item.pk]),
            {"section": "messages"},
        )

        self.assertContains(response, 'aria-current="page"', html=False)
        self.assertContains(response, "Mesajlar")
        self.assertContains(response, "Mesajlar bolumunu test ediyorum.")
        self.assertNotContains(
            response,
            "Gönüllünün incelemesini istediğiniz ders notu, PDF, slayt veya görselleri burada paylaşabilirsiniz.",
        )

    def test_student_request_detail_all_section_shows_counts_and_all_content(self):
        request_item = SupportRequest.objects.create(
            created_by=self.student,
            title="Tum bolumlu ogrenci talebi",
            category=SupportRequest.Categories.ACADEMIC,
            course_name="Matematik",
            topic="Limit",
            description="Aciklama",
            assigned_volunteer=self.volunteer,
            status=SupportRequest.Statuses.MATCHED,
        )
        RequestMessage.objects.create(
            request=request_item,
            author=self.student,
            body="Ogrenci mesaj kaydi",
        )
        RequestMaterial.objects.create(
            request=request_item,
            uploaded_by=self.student,
            title="Ders notu",
            description="Kaynak dosya",
            file=SimpleUploadedFile("not.txt", b"icerik", content_type="text/plain"),
        )
        self.client.force_login(self.student)

        response = self.client.get(
            reverse("support:student_request_detail", args=[request_item.pk]),
            {"section": "all"},
        )

        self.assertContains(response, "Aciklama")
        self.assertContains(response, "Ogrenci mesaj kaydi")
        self.assertContains(response, "Ders notu")
        self.assertContains(response, "request-detail-panel-all")
        self.assertContains(response, 'aria-label="Mesajlar: 1"', html=False)
        self.assertContains(response, 'aria-label="Kaynak dosyalar: 1"', html=False)

    def test_coordinator_can_view_requests(self):
        request_item = SupportRequest.objects.create(
            created_by=self.student,
            title="Koordinator goruntuler",
            category=SupportRequest.Categories.ACADEMIC,
            course_name="Tarih",
            topic="Osmanli",
            description="Aciklama",
        )
        self.client.force_login(self.coordinator)

        list_response = self.client.get(reverse("support:coordinator_request_list"))
        detail_response = self.client.get(
            reverse("support:coordinator_request_detail", args=[request_item.pk])
        )

        self.assertContains(list_response, "Koordinator goruntuler")
        self.assertContains(detail_response, "Koordinator goruntuler")
        self.assertContains(detail_response, "Konu:")
        self.assertNotContains(detail_response, "Matematik, yabancı dil, istatistik")

    def test_coordinator_request_list_marks_requests_with_coordination_notes(self):
        request_item = SupportRequest.objects.create(
            created_by=self.student,
            title="Koordinasyon notlu liste kaydi",
            category=SupportRequest.Categories.ACADEMIC,
            course_name="Tarih",
            topic="Modernizm",
            description="Aciklama",
        )
        SupportRequestInterventionNote.objects.create(
            request=request_item,
            author=self.coordinator,
            priority=SupportRequestInterventionNote.Priorities.HIGH,
            body="Listede gorunmeli",
        )
        self.client.force_login(self.coordinator)

        response = self.client.get(reverse("support:coordinator_request_list"))

        self.assertContains(response, "1 koordinasyon notu")
        self.assertContains(response, 'aria-label="1 koordinasyon notu"', html=False)

    def test_coordinator_request_list_shows_when_coordination_note_is_missing(self):
        request_item = SupportRequest.objects.create(
            created_by=self.student,
            title="Notsuz liste kaydi",
            category=SupportRequest.Categories.ACADEMIC,
            course_name="Tarih",
            topic="Modernizm",
            description="Aciklama",
        )
        self.client.force_login(self.coordinator)

        response = self.client.get(reverse("support:coordinator_request_list"))

        self.assertContains(response, request_item.title)
        self.assertContains(response, "Koordinasyon notu yok")
        self.assertContains(response, 'aria-label="Koordinasyon notu yok"', html=False)

    def test_academic_advisor_can_view_requests(self):
        request_item = SupportRequest.objects.create(
            created_by=self.student,
            title="Danisman goruntuler",
            category=SupportRequest.Categories.ACADEMIC,
            course_name="Edebiyat",
            topic="Siir analizi",
            description="Aciklama",
        )
        self.client.force_login(self.advisor)

        list_response = self.client.get(reverse("support:coordinator_request_list"))
        detail_response = self.client.get(
            reverse("support:coordinator_request_detail", args=[request_item.pk])
        )

        self.assertContains(list_response, "Danisman goruntuler")
        self.assertContains(detail_response, "Danisman goruntuler")

    def test_volunteer_cannot_access_coordinator_request_list(self):
        self.client.force_login(self.volunteer)

        response = self.client.get(reverse("support:coordinator_request_list"))

        self.assertEqual(response.status_code, 403)
        self.assertContains(
            response,
            "Bu sayfaya erişim izniniz yok",
            status_code=403,
        )

    def test_volunteer_can_view_open_requests(self):
        SupportRequest.objects.create(
            created_by=self.student,
            title="Acik talep",
            category=SupportRequest.Categories.ACADEMIC,
            course_name="Biyoloji",
            topic="Hucresel yapilar",
            description="Aciklama",
        )
        self.client.force_login(self.volunteer)

        response = self.client.get(reverse("support:volunteer_open_request_list"))

        self.assertContains(response, "Acik talep")

    def test_volunteer_request_detail_all_section_shows_counts_and_all_content(self):
        request_item = SupportRequest.objects.create(
            created_by=self.student,
            title="Tum bolumlu gonullu talebi",
            category=SupportRequest.Categories.ACADEMIC,
            course_name="Kimya",
            topic="Baglar",
            description="Aciklama",
            assigned_volunteer=self.volunteer,
            status=SupportRequest.Statuses.MATCHED,
        )
        RequestMessage.objects.create(
            request=request_item,
            author=self.student,
            body="Gonullu icin mesaj kaydi",
        )
        RequestMaterial.objects.create(
            request=request_item,
            uploaded_by=self.student,
            title="Kaynak PDF",
            description="Kaynak aciklamasi",
            file=SimpleUploadedFile("kaynak.txt", b"icerik", content_type="text/plain"),
        )
        self.client.force_login(self.volunteer)

        response = self.client.get(
            reverse("support:volunteer_request_detail", args=[request_item.pk]),
            {"section": "all"},
        )

        self.assertContains(response, "Aciklama")
        self.assertContains(response, "Gonullu icin mesaj kaydi")
        self.assertContains(response, "Kaynak PDF")
        self.assertContains(response, "request-detail-panel-all")
        self.assertContains(response, 'aria-label="Mesajlar: 1"', html=False)
        self.assertContains(response, 'aria-label="Kaynak dosyalar: 1"', html=False)

    def test_volunteer_can_claim_open_request(self):
        request_item = SupportRequest.objects.create(
            created_by=self.student,
            title="Ustlenilecek talep",
            category=SupportRequest.Categories.ACADEMIC,
            course_name="Ekonomi",
            topic="Arz-talep",
            description="Aciklama",
        )
        self.client.force_login(self.volunteer)

        response = self.client.post(
            reverse("support:volunteer_request_claim", args=[request_item.pk])
        )

        self.assertRedirects(
            response,
            reverse("support:volunteer_request_detail", args=[request_item.pk]),
        )
        request_item.refresh_from_db()
        self.assertEqual(request_item.assigned_volunteer, self.volunteer)
        self.assertEqual(request_item.status, SupportRequest.Statuses.MATCHED)
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.student,
                title="Bir gönüllü talebi üstlendi",
            ).exists()
        )

    def test_claimed_request_does_not_appear_in_other_volunteer_open_list(self):
        request_item = SupportRequest.objects.create(
            created_by=self.student,
            title="Paylasilmayan talep",
            category=SupportRequest.Categories.ACADEMIC,
            course_name="Kimya",
            topic="Baglar",
            description="Aciklama",
            assigned_volunteer=self.volunteer,
            status=SupportRequest.Statuses.MATCHED,
        )
        self.client.force_login(self.other_volunteer)

        response = self.client.get(reverse("support:volunteer_open_request_list"))

        self.assertNotContains(response, request_item.title)

    def test_volunteer_active_list_shows_assigned_requests(self):
        request_item = SupportRequest.objects.create(
            created_by=self.student,
            title="Aktif destek",
            category=SupportRequest.Categories.ACADEMIC,
            course_name="Felsefe",
            topic="Etik",
            description="Aciklama",
            assigned_volunteer=self.volunteer,
            status=SupportRequest.Statuses.MATCHED,
        )
        self.client.force_login(self.volunteer)

        response = self.client.get(reverse("support:volunteer_active_support_list"))

        self.assertContains(response, request_item.title)

    def test_coordinator_can_assign_volunteer(self):
        request_item = SupportRequest.objects.create(
            created_by=self.student,
            title="Koordinator atar",
            category=SupportRequest.Categories.ACADEMIC,
            course_name="Sosyoloji",
            topic="Alan arastirmasi",
            description="Aciklama",
        )
        self.client.force_login(self.coordinator)

        response = self.client.post(
            reverse("support:coordinator_request_assign", args=[request_item.pk]),
            {"volunteer": self.volunteer.pk},
        )

        self.assertRedirects(
            response,
            f"{reverse('support:coordinator_request_detail', args=[request_item.pk])}?section=management",
        )
        request_item.refresh_from_db()
        self.assertEqual(request_item.assigned_volunteer, self.volunteer)
        self.assertEqual(request_item.status, SupportRequest.Statuses.MATCHED)

    def test_student_can_post_message(self):
        request_item = SupportRequest.objects.create(
            created_by=self.student,
            title="Mesaj talebi",
            category=SupportRequest.Categories.ACADEMIC,
            course_name="Matematik",
            topic="Limit",
            description="Aciklama",
            assigned_volunteer=self.volunteer,
            status=SupportRequest.Statuses.MATCHED,
        )
        self.client.force_login(self.student)

        response = self.client.post(
            reverse("support:student_request_message_create", args=[request_item.pk]),
            {"body": "Ilk notlari biraz daha yapilandirmak istiyorum."},
        )

        self.assertRedirects(
            response,
            f"{reverse('support:student_request_detail', args=[request_item.pk])}?section=messages",
        )
        self.assertTrue(
            RequestMessage.objects.filter(
                request=request_item,
                author=self.student,
                body="Ilk notlari biraz daha yapilandirmak istiyorum.",
            ).exists()
        )
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.volunteer,
                title="Yeni talep mesajı",
            ).exists()
        )

    def test_volunteer_can_post_message_on_assigned_request(self):
        request_item = SupportRequest.objects.create(
            created_by=self.student,
            title="Gonullu mesaji",
            category=SupportRequest.Categories.ACADEMIC,
            course_name="Kimya",
            topic="Atom",
            description="Aciklama",
            assigned_volunteer=self.volunteer,
            status=SupportRequest.Statuses.MATCHED,
        )
        self.client.force_login(self.volunteer)

        response = self.client.post(
            reverse("support:volunteer_request_message_create", args=[request_item.pk]),
            {"body": "Bu aksam ilk oturumu baslatabiliriz."},
        )

        self.assertRedirects(
            response,
            f"{reverse('support:volunteer_request_detail', args=[request_item.pk])}?section=messages",
        )
        self.assertTrue(
            RequestMessage.objects.filter(
                request=request_item,
                author=self.volunteer,
                body="Bu aksam ilk oturumu baslatabiliriz.",
            ).exists()
        )

    def test_student_can_upload_material(self):
        request_item = SupportRequest.objects.create(
            created_by=self.student,
            title="Materyal talebi",
            category=SupportRequest.Categories.ACCESSIBLE_MATERIAL,
            course_name="Fizik",
            topic="Dalgalar",
            description="Aciklama",
        )
        self.client.force_login(self.student)
        upload = SimpleUploadedFile(
            "ozet.txt",
            b"Dalga konusu ozeti",
            content_type="text/plain",
        )

        response = self.client.post(
            reverse("support:student_request_material_create", args=[request_item.pk]),
            {
                "title": "Dalga ozeti",
                "description": "Kisa tekrar notu",
                "file": upload,
            },
        )

        self.assertRedirects(
            response,
            f"{reverse('support:student_request_detail', args=[request_item.pk])}?section=materials",
        )
        self.assertTrue(
            RequestMaterial.objects.filter(
                request=request_item,
                uploaded_by=self.student,
                title="Dalga ozeti",
            ).exists()
        )

    def test_student_can_upload_material_with_long_original_filename(self):
        request_item = SupportRequest.objects.create(
            created_by=self.student,
            title="Uzun dosya adli talep",
            category=SupportRequest.Categories.ACCESSIBLE_MATERIAL,
            course_name="Egitim",
            topic="Makale",
            description="Aciklama",
        )
        self.client.force_login(self.student)
        upload = SimpleUploadedFile(
            (
                "Sam et al. 2025 Challenges to Accessibility in Virtual Distance "
                "Education A Bibliometric Study.pdf"
            ),
            b"%PDF-1.4 test content",
            content_type="application/pdf",
        )

        response = self.client.post(
            reverse("support:student_request_material_create", args=[request_item.pk]),
            {
                "title": "Makale",
                "description": "Bu PDF'in ozetlenmesini istiyorum.",
                "file": upload,
            },
        )

        self.assertRedirects(
            response,
            f"{reverse('support:student_request_detail', args=[request_item.pk])}?section=materials",
        )
        material = RequestMaterial.objects.get(
            request=request_item,
            uploaded_by=self.student,
            title="Makale",
        )
        self.assertTrue(material.file.name.startswith("request_materials/"))
        self.assertLessEqual(len(material.file.name), 255)
        self.assertIn(".pdf", material.file.name)

    def test_student_material_upload_shows_inline_errors_when_invalid(self):
        request_item = SupportRequest.objects.create(
            created_by=self.student,
            title="Eksik dosya talebi",
            category=SupportRequest.Categories.ACCESSIBLE_MATERIAL,
            course_name="Fizik",
            topic="Dalgalar",
            description="Aciklama",
        )
        self.client.force_login(self.student)

        response = self.client.post(
            reverse("support:student_request_material_create", args=[request_item.pk]),
            {
                "title": "",
                "description": "Dosya secmeden gonderildi",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Dosya eklenemedi. Lütfen aşağıdaki alanları kontrol edin.",
        )
        self.assertContains(response, "Bu alan zorunludur.")
        self.assertContains(response, "Kaynak dosyalar")

    def test_volunteer_material_upload_shows_inline_errors_when_invalid(self):
        request_item = SupportRequest.objects.create(
            created_by=self.student,
            title="Gonullu materyal talebi",
            category=SupportRequest.Categories.ACADEMIC,
            course_name="Matematik",
            topic="Limit",
            description="Aciklama",
            assigned_volunteer=self.volunteer,
            status=SupportRequest.Statuses.MATCHED,
        )
        self.client.force_login(self.volunteer)

        response = self.client.post(
            reverse("support:volunteer_request_material_create", args=[request_item.pk]),
            {
                "title": "",
                "description": "Materyal secmeden gonderildi",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Materyal yüklenemedi. Lütfen aşağıdaki alanları kontrol edin.",
        )
        self.assertContains(response, "Bu alan zorunludur.")
        self.assertContains(response, "Kaynak dosyalar")

    def test_coordinator_detail_shows_messages_and_materials(self):
        request_item = SupportRequest.objects.create(
            created_by=self.student,
            title="Kayitli icerik",
            category=SupportRequest.Categories.ACADEMIC,
            course_name="Tarih",
            topic="Modernizm",
            description="Aciklama",
        )
        RequestMessage.objects.create(
            request=request_item,
            author=self.student,
            body="Bu materyalin sade ozetine ihtiyacim var.",
        )
        RequestMaterial.objects.create(
            request=request_item,
            uploaded_by=self.student,
            title="Makale notu",
            description="PDF ozet ciktisi",
            file=SimpleUploadedFile("makale.txt", b"icerik", content_type="text/plain"),
        )
        self.client.force_login(self.coordinator)

        messages_response = self.client.get(
            reverse("support:coordinator_request_detail", args=[request_item.pk]),
            {"section": "messages"},
        )
        materials_response = self.client.get(
            reverse("support:coordinator_request_detail", args=[request_item.pk]),
            {"section": "materials"},
        )

        self.assertContains(messages_response, "Bu materyalin sade ozetine ihtiyacim var.")
        self.assertContains(materials_response, "Makale notu")

    def test_coordinator_request_detail_can_open_messages_section(self):
        request_item = SupportRequest.objects.create(
            created_by=self.student,
            title="Koordinator sekmeli talep",
            category=SupportRequest.Categories.ACADEMIC,
            course_name="Tarih",
            topic="Modernizm",
            description="Aciklama",
        )
        RequestMessage.objects.create(
            request=request_item,
            author=self.student,
            body="Koordinator mesaj kaydini goruyor.",
        )
        self.client.force_login(self.coordinator)

        response = self.client.get(
            reverse("support:coordinator_request_detail", args=[request_item.pk]),
            {"section": "messages"},
        )

        self.assertContains(response, "Mesajlaşma kaydı")
        self.assertContains(response, "Koordinator mesaj kaydini goruyor.")
        self.assertNotContains(response, "Gönüllü ata")

    def helper_coordinator_request_detail_all_section_shows_counts_and_all_content(self):
        request_item = SupportRequest.objects.create(
            created_by=self.student,
            title="Tum bolumlu koordinator talebi",
            category=SupportRequest.Categories.ACADEMIC,
            course_name="Tarih",
            topic="Modernizm",
            description="Aciklama",
            assigned_volunteer=self.volunteer,
            status=SupportRequest.Statuses.MATCHED,
        )
        RequestMessage.objects.create(
            request=request_item,
            author=self.student,
            body="Koordinator tum gorunum mesaji",
        )
        RequestMaterial.objects.create(
            request=request_item,
            uploaded_by=self.student,
            title="Koordinator materyali",
            description="Aciklama",
            file=SimpleUploadedFile("materyal.txt", b"icerik", content_type="text/plain"),
        )
        SupportRequestInterventionNote.objects.create(
            request=request_item,
            author=self.coordinator,
            body="Koordinator mudahale notu",
        )
        SupportRequestActivityLog.objects.create(
            request=request_item,
            actor=self.coordinator,
            action_type=SupportRequestActivityLog.ActionTypes.STATUS_UPDATED,
            description="Koordinator kaydi",
        )
        self.client.force_login(self.coordinator)

        response = self.client.get(
            reverse("support:coordinator_request_detail", args=[request_item.pk]),
            {"section": "all"},
        )

        self.assertContains(response, "YÃ¶netim")
        self.assertContains(response, "MÃ¼dahale notlarÄ±")
        self.assertContains(response, "Ä°ÅŸlem geÃ§miÅŸi")
        self.assertContains(response, "Koordinator tum gorunum mesaji")
        self.assertContains(response, "Koordinator materyali")
        self.assertContains(response, "Koordinator mudahale notu")
        self.assertContains(response, "Koordinator kaydi")
        self.assertContains(response, 'aria-label="1 koordinasyon notu"', html=False)
        self.assertContains(response, 'aria-label="1 iÅŸlem kaydÄ±"', html=False)
        self.assertContains(response, 'aria-label="Koordinasyon notları: 1"', html=False)
        self.assertContains(response, 'aria-label="İşlem geçmişi: 1"', html=False)
        self.assertContains(response, 'aria-label="Mesajlar: 1"', html=False)
        self.assertContains(response, 'aria-label="Kaynak dosyalar: 1"', html=False)

    def test_coordinator_request_detail_all_section_renders_management_notes_history_and_counts(self):
        request_item = SupportRequest.objects.create(
            created_by=self.student,
            title="Tum bolumlu koordinator talebi v2",
            category=SupportRequest.Categories.ACADEMIC,
            course_name="Tarih",
            topic="Modernizm",
            description="Aciklama",
            assigned_volunteer=self.volunteer,
            status=SupportRequest.Statuses.MATCHED,
        )
        RequestMessage.objects.create(
            request=request_item,
            author=self.student,
            body="Koordinator tum gorunum mesaji",
        )
        RequestMaterial.objects.create(
            request=request_item,
            uploaded_by=self.student,
            title="Koordinator materyali",
            description="Aciklama",
            file=SimpleUploadedFile("materyal.txt", b"icerik", content_type="text/plain"),
        )
        SupportRequestInterventionNote.objects.create(
            request=request_item,
            author=self.coordinator,
            body="Koordinator mudahale notu",
        )
        SupportRequestActivityLog.objects.create(
            request=request_item,
            actor=self.coordinator,
            action_type=SupportRequestActivityLog.ActionTypes.STATUS_UPDATED,
            description="Koordinator kaydi",
        )
        self.client.force_login(self.coordinator)

        response = self.client.get(
            reverse("support:coordinator_request_detail", args=[request_item.pk]),
            {"section": "all"},
        )

        self.assertContains(
            response,
            reverse("support:coordinator_request_assign", args=[request_item.pk]),
        )
        self.assertContains(
            response,
            reverse("support:coordinator_request_status", args=[request_item.pk]),
        )
        self.assertContains(
            response,
            reverse("support:coordinator_request_priority", args=[request_item.pk]),
        )
        self.assertContains(response, "request-detail-panel-all")
        self.assertContains(response, "Koordinator tum gorunum mesaji")
        self.assertContains(response, "Koordinator materyali")
        self.assertContains(response, "Koordinator mudahale notu")
        self.assertContains(response, "Koordinator kaydi")
        self.assertContains(response, 'aria-label="1 mesaj"', html=False)
        self.assertContains(response, 'aria-label="1 kaynak dosya"', html=False)
        self.assertContains(response, 'aria-label="İşlem türü: Durum güncellendi"', html=False)

    def test_coordinator_can_filter_requests_by_status(self):
        SupportRequest.objects.create(
            created_by=self.student,
            title="Acik kayit",
            category=SupportRequest.Categories.ACADEMIC,
            course_name="Psikoloji",
            topic="Algı",
            description="Aciklama",
            status=SupportRequest.Statuses.OPEN,
        )
        SupportRequest.objects.create(
            created_by=self.student,
            title="Tamamlanan kayit",
            category=SupportRequest.Categories.ACADEMIC,
            course_name="Psikoloji",
            topic="Bellek",
            description="Aciklama",
            status=SupportRequest.Statuses.COMPLETED,
        )
        self.client.force_login(self.coordinator)

        response = self.client.get(
            reverse("support:coordinator_request_list"),
            {"status": SupportRequest.Statuses.OPEN},
        )

        self.assertContains(response, "Acik kayit")
        self.assertNotContains(response, "Tamamlanan kayit")

    def test_coordinator_can_update_request_status(self):
        request_item = SupportRequest.objects.create(
            created_by=self.student,
            title="Durum guncelleme",
            category=SupportRequest.Categories.ACADEMIC,
            course_name="Tarih",
            topic="Cumhuriyet",
            description="Aciklama",
            assigned_volunteer=self.volunteer,
            status=SupportRequest.Statuses.MATCHED,
        )
        self.client.force_login(self.coordinator)

        response = self.client.post(
            reverse("support:coordinator_request_status", args=[request_item.pk]),
            {"status": SupportRequest.Statuses.IN_PROGRESS},
        )

        self.assertRedirects(
            response,
            f"{reverse('support:coordinator_request_detail', args=[request_item.pk])}?section=management",
        )
        request_item.refresh_from_db()
        self.assertEqual(request_item.status, SupportRequest.Statuses.IN_PROGRESS)

    def test_coordinator_can_update_request_priority(self):
        request_item = SupportRequest.objects.create(
            created_by=self.student,
            title="Oncelikli talep",
            category=SupportRequest.Categories.ACADEMIC,
            course_name="Tarih",
            topic="Devrimler",
            description="Aciklama",
        )
        self.client.force_login(self.coordinator)

        response = self.client.post(
            reverse("support:coordinator_request_priority", args=[request_item.pk]),
            {"priority": SupportRequest.Priorities.CRITICAL},
        )

        self.assertRedirects(
            response,
            f"{reverse('support:coordinator_request_detail', args=[request_item.pk])}?section=management",
        )
        request_item.refresh_from_db()
        self.assertEqual(request_item.priority, SupportRequest.Priorities.CRITICAL)
        self.assertTrue(
            SupportRequestActivityLog.objects.filter(
                request=request_item,
                action_type=SupportRequestActivityLog.ActionTypes.PRIORITY_UPDATED,
            ).exists()
        )

    def test_coordinator_can_add_intervention_note(self):
        request_item = SupportRequest.objects.create(
            created_by=self.student,
            title="Mudahale notlu talep",
            category=SupportRequest.Categories.ACADEMIC,
            course_name="Matematik",
            topic="Turev",
            description="Aciklama",
        )
        self.client.force_login(self.coordinator)

        response = self.client.post(
            reverse("support:coordinator_request_note_create", args=[request_item.pk]),
            {
                "priority": SupportRequestInterventionNote.Priorities.CRITICAL,
                "body": "Ogrenciye donus suresi uzadi, oncelik yukseltilmeli.",
            },
        )

        self.assertRedirects(
            response,
            f"{reverse('support:coordinator_request_detail', args=[request_item.pk])}?section=notes",
        )
        self.assertTrue(
            SupportRequestInterventionNote.objects.filter(
                request=request_item,
                author=self.coordinator,
                priority=SupportRequestInterventionNote.Priorities.CRITICAL,
            ).exists()
        )

    def test_coordinator_overview_shows_intervention_notes_in_side_pane(self):
        request_item = SupportRequest.objects.create(
            created_by=self.student,
            title="Yan panel not talebi",
            category=SupportRequest.Categories.ACADEMIC,
            course_name="Matematik",
            topic="Integral",
            description="Aciklama",
        )
        SupportRequestInterventionNote.objects.create(
            request=request_item,
            author=self.coordinator,
            priority=SupportRequestInterventionNote.Priorities.CRITICAL,
            body="Oncelikli mudahale notu",
        )
        self.client.force_login(self.coordinator)

        response = self.client.get(
            reverse("support:coordinator_request_detail", args=[request_item.pk]),
            {"section": "overview"},
        )

        self.assertContains(response, "Koordinasyon notları")
        self.assertContains(response, "Oncelikli mudahale notu")
        self.assertContains(response, 'aria-label="Öncelik: Kritik önem"', html=False)

    def test_coordinator_can_filter_requests_by_priority(self):
        high_request = SupportRequest.objects.create(
            created_by=self.student,
            title="Kritik kayit",
            category=SupportRequest.Categories.ACADEMIC,
            course_name="Psikoloji",
            topic="Algı",
            description="Aciklama",
            priority=SupportRequest.Priorities.CRITICAL,
        )
        SupportRequest.objects.create(
            created_by=self.student,
            title="Normal kayit",
            category=SupportRequest.Categories.ACADEMIC,
            course_name="Psikoloji",
            topic="Bellek",
            description="Aciklama",
            priority=SupportRequest.Priorities.NORMAL,
        )
        self.client.force_login(self.coordinator)

        response = self.client.get(
            reverse("support:coordinator_request_list"),
            {"priority": SupportRequest.Priorities.CRITICAL},
        )

        self.assertContains(response, high_request.title)
        self.assertNotContains(response, "Normal kayit")

    def test_coordinator_can_filter_requests_by_deadline_pressure(self):
        due_soon_request = SupportRequest.objects.create(
            created_by=self.student,
            title="Suresi yaklasan kayit",
            category=SupportRequest.Categories.ACADEMIC,
            course_name="Psikoloji",
            topic="Algı",
            description="Aciklama",
            status=SupportRequest.Statuses.OPEN,
            requested_completion_date=timezone.localdate() + timedelta(days=2),
        )
        SupportRequest.objects.create(
            created_by=self.student,
            title="Tarihi uzak kayit",
            category=SupportRequest.Categories.ACADEMIC,
            course_name="Psikoloji",
            topic="Bellek",
            description="Aciklama",
            status=SupportRequest.Statuses.OPEN,
            requested_completion_date=timezone.localdate() + timedelta(days=10),
        )
        self.client.force_login(self.coordinator)

        response = self.client.get(
            reverse("support:coordinator_request_list"),
            {"deadline": "due_soon"},
        )

        self.assertContains(response, due_soon_request.title)
        self.assertNotContains(response, "Tarihi uzak kayit")
        self.assertEqual(response.context["due_soon_result_count"], 1)


class FileUploadSecurityTests(TestCase):
    """
    Dosya yükleme güvenlik testleri:
    - 5 MB boyut limiti sunucu tarafında uygulanmalıdır.
    - İzin verilmeyen MIME tipleri reddedilmelidir.
    - Diskten silinen dosyalara indirme isteği 404 dönmelidir.
    """

    def setUp(self):
        self.student = User.objects.create_user(
            username="guvenlik_ogrenci",
            email="guvenlik@example.com",
            password="Testpass12345",
            role=User.Roles.VISUALLY_IMPAIRED_STUDENT,
            profile_completed=True,
        )
        self.coordinator = User.objects.create_user(
            username="guvenlik_koord",
            email="guvenlik_koord@example.com",
            password="Testpass12345",
            role=User.Roles.COORDINATOR,
            profile_completed=True,
        )
        self.support_request = SupportRequest.objects.create(
            created_by=self.student,
            title="Güvenlik test talebi",
            category=SupportRequest.Categories.ACADEMIC,
            course_name="Test Dersi",
            topic="Test Konusu",
            description="Güvenlik testleri için oluşturuldu.",
        )

    def test_file_upload_rejects_oversized_file(self):
        """5 MB'ı aşan dosyalar sunucu tarafında reddedilmelidir."""
        self.client.force_login(self.student)
        # 6 MB içerik (5 MB limitini aşıyor)
        large_content = b"x" * (6 * 1024 * 1024)
        large_file = SimpleUploadedFile(
            "buyuk_dosya.pdf",
            large_content,
            content_type="application/pdf",
        )
        response = self.client.post(
            reverse(
                "support:student_request_material_create",
                args=[self.support_request.pk],
            ),
            {
                "title": "Büyük dosya",
                "description": "Boyutu aşıyor",
                "file": large_file,
            },
        )
        # Form hatayla dönmeli, kayıt oluşturulmamalı
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "5 MB")
        self.assertFalse(
            RequestMaterial.objects.filter(request=self.support_request).exists()
        )

    def test_file_upload_rejects_disallowed_mime_type(self):
        """İzin verilmeyen dosya türleri reddedilmelidir."""
        self.client.force_login(self.student)
        malicious_file = SimpleUploadedFile(
            "betik.py",
            b"import os; os.system('rm -rf /')",
            content_type="text/x-python",
        )
        response = self.client.post(
            reverse(
                "support:student_request_material_create",
                args=[self.support_request.pk],
            ),
            {
                "title": "Zararlı script",
                "description": "İzin verilmez",
                "file": malicious_file,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "desteklenmiyor")
        self.assertFalse(
            RequestMaterial.objects.filter(request=self.support_request).exists()
        )

    def test_file_upload_accepts_valid_pdf(self):
        """Geçerli PDF dosyaları kabul edilmelidir."""
        self.client.force_login(self.student)
        valid_pdf = SimpleUploadedFile(
            "ders_notu.pdf",
            b"%PDF-1.4 gecerli icerik",
            content_type="application/pdf",
        )
        response = self.client.post(
            reverse(
                "support:student_request_material_create",
                args=[self.support_request.pk],
            ),
            {
                "title": "Ders notu",
                "description": "Geçerli PDF",
                "file": valid_pdf,
            },
        )
        self.assertRedirects(
            response,
            reverse(
                "support:student_request_detail",
                args=[self.support_request.pk],
            )
            + "?section=materials",
        )
        self.assertTrue(
            RequestMaterial.objects.filter(
                request=self.support_request,
                title="Ders notu",
            ).exists()
        )

    def test_material_download_returns_404_when_file_missing_on_disk(self):
        """Diskten silinen dosyalara indirme isteği 500 yerine 404 dönmelidir."""
        material = RequestMaterial.objects.create(
            request=self.support_request,
            uploaded_by=self.student,
            title="Silinmiş dosya",
            description="Bu dosya diskte mevcut değil.",
            # Gerçekte var olmayan bir yol
            file="request_materials/2000/01/01/hayalet-dosya-000.pdf",
        )
        self.client.force_login(self.student)
        response = self.client.get(
            reverse("support:request_material_download", args=[material.pk])
        )
        self.assertEqual(response.status_code, 404)


class RoleAccessControlTests(TestCase):
    """
    Rol tabanlı erişim kontrolünün edge-case testleri.
    Yanlış roldeki kullanıcılar korumalı view'lara erişememeli.
    """

    def setUp(self):
        self.student = User.objects.create_user(
            username="rol_test_ogrenci",
            email="rol_ogrenci@example.com",
            password="Testpass12345",
            role=User.Roles.VISUALLY_IMPAIRED_STUDENT,
            profile_completed=True,
        )
        self.volunteer = User.objects.create_user(
            username="rol_test_gonullu",
            email="rol_gonullu@example.com",
            password="Testpass12345",
            role=User.Roles.VOLUNTEER_STUDENT,
            profile_completed=True,
        )
        self.advisor = User.objects.create_user(
            username="rol_test_danisman",
            email="rol_danisman@example.com",
            password="Testpass12345",
            role=User.Roles.ACADEMIC_ADVISOR,
            profile_completed=True,
        )
        self.support_request = SupportRequest.objects.create(
            created_by=self.student,
            title="Rol testi talebi",
            category=SupportRequest.Categories.ACADEMIC,
            course_name="Test",
            topic="Test",
            description="Açıklama.",
        )

    def test_volunteer_cannot_create_student_request(self):
        """Gönüllü öğrenci, görme engelli öğrenciye özel talep oluşturma sayfasına erişemez."""
        self.client.force_login(self.volunteer)
        response = self.client.get(reverse("support:student_request_create"))
        self.assertEqual(response.status_code, 403)

    def test_student_cannot_access_volunteer_open_request_list(self):
        """Görme engelli öğrenci, gönüllü açık talep listesine erişemez."""
        self.client.force_login(self.student)
        response = self.client.get(reverse("support:volunteer_open_request_list"))
        self.assertEqual(response.status_code, 403)

    def test_student_cannot_access_coordinator_request_list(self):
        """Görme engelli öğrenci, koordinatör talep listesine erişemez."""
        self.client.force_login(self.student)
        response = self.client.get(reverse("support:coordinator_request_list"))
        self.assertEqual(response.status_code, 403)

    def test_volunteer_cannot_access_coordinator_request_list(self):
        """Gönüllü öğrenci, koordinatör talep listesine erişemez."""
        self.client.force_login(self.volunteer)
        response = self.client.get(reverse("support:coordinator_request_list"))
        self.assertEqual(response.status_code, 403)

    def test_advisor_can_access_coordinator_request_list(self):
        """Akademik danışman, koordinatör talep listesini görüntüleyebilir."""
        self.client.force_login(self.advisor)
        response = self.client.get(reverse("support:coordinator_request_list"))
        self.assertEqual(response.status_code, 200)

    def test_unauthenticated_user_redirected_from_student_request_list(self):
        """Kimliği doğrulanmamış kullanıcı, giriş sayfasına yönlendirilmelidir."""
        response = self.client.get(reverse("support:student_request_list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response["Location"])

    def test_inactive_student_is_logged_out_and_redirected(self):
        """Deaktif edilmiş kullanıcı oturumu kapatılmalı ve giriş sayfasına yönlendirilmelidir."""
        self.student.is_active = False
        self.student.save()
        self.client.force_login(self.student)
        response = self.client.get(reverse("support:student_request_list"))
        # Deaktif kullanıcı login sayfasına yönlendirilmeli
        self.assertEqual(response.status_code, 302)

    def test_student_cannot_access_other_students_request_detail(self):
        """Öğrenci, başka bir öğrencinin talep detayına erişememeli."""
        other_student = User.objects.create_user(
            username="baska_ogrenci",
            email="baska@example.com",
            password="Testpass12345",
            role=User.Roles.VISUALLY_IMPAIRED_STUDENT,
            profile_completed=True,
        )
        self.client.force_login(other_student)
        response = self.client.get(
            reverse("support:student_request_detail", args=[self.support_request.pk])
        )
        self.assertEqual(response.status_code, 404)
