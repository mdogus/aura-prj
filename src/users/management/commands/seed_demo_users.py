from datetime import timedelta

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils import timezone

from notifications.models import Notification
from notifications.services import create_notification
from support.models import RequestMaterial, RequestMessage, SupportRequest
from users.models import User


ADMIN_PASSWORD = "AuraPilot123!"
SEED_USER_PASSWORD = "AuraPilot123!"

DEMO_NOTIFICATION_TITLES = [
    "Demo bildirim: yeni talep incelemenizi bekliyor",
    "Demo bildirim: kaynak dosya eklendi",
    "Demo bildirim: koordinasyon notu girildi",
    "Demo bildirim: destek bulusmasi planlandi",
]

PILOT_CORE_USERS = [
    {
        "username": "danisman1",
        "email": "danisman1@aura.local",
        "first_name": "Selin",
        "last_name": "Arslan",
        "role": User.Roles.ACADEMIC_ADVISOR,
        "university": "Anadolu University",
        "department": "Education",
        "preferred_communication": "Platform mesajlaşması",
        "support_topics": "Akademik planlama, ders stratejisi, materyal rehberliği",
        "availability_notes": "Hafta içi gündüz",
        "profile_completed": True,
    },
    {
        "username": "danisman2",
        "email": "danisman2@aura.local",
        "first_name": "Burcu",
        "last_name": "Aydin",
        "role": User.Roles.ACADEMIC_ADVISOR,
        "university": "Anadolu University",
        "department": "Special Education",
        "preferred_communication": "Platform mesajlaşması",
        "support_topics": "Erişilebilir öğrenme, ders düzenleme, sınav hazırlık",
        "availability_notes": "Hafta içi öğleden sonra",
        "profile_completed": True,
    },
    {
        "username": "koordinator1",
        "email": "koordinator1@aura.local",
        "first_name": "Merve",
        "last_name": "Yildiz",
        "role": User.Roles.COORDINATOR,
        "university": "Anadolu University",
        "department": "Student Affairs",
        "preferred_communication": "Platform mesajlaşması",
        "profile_completed": True,
        "is_staff": True,
    },
    {
        "username": "koordinator2",
        "email": "koordinator2@aura.local",
        "first_name": "Can",
        "last_name": "Kurt",
        "role": User.Roles.COORDINATOR,
        "university": "Anadolu University",
        "department": "Accessibility Office",
        "preferred_communication": "Platform mesajlaşması",
        "profile_completed": True,
        "is_staff": True,
    },
]

DEMO_USERS = [
    {
        "username": "ogrenci1",
        "email": "ogrenci1@aura.local",
        "first_name": "Zeynep",
        "last_name": "Kara",
        "role": User.Roles.VISUALLY_IMPAIRED_STUDENT,
        "university": "Anadolu University",
        "department": "Psychology",
        "preferred_communication": "Platform mesajlaşması",
        "accessibility_needs": "Erişilebilir PDF ve görsel betimleme desteği",
        "support_topics": "Akademik destek, ders materyali, sınav hazırlık",
        "availability_notes": "Hafta içi öğleden sonra",
        "profile_completed": True,
    },
    {
        "username": "ogrenci2",
        "email": "ogrenci2@aura.local",
        "first_name": "Mert",
        "last_name": "Celik",
        "role": User.Roles.VISUALLY_IMPAIRED_STUDENT,
        "university": "Anadolu University",
        "department": "History",
        "preferred_communication": "Platform mesajlaşması",
        "accessibility_needs": "Seslendirme ve kaynak erişimi desteği",
        "support_topics": "Kaynak erişimi, seslendirme, sosyal etkinlik",
        "availability_notes": "Hafta içi akşam, hafta sonu öğleden sonra",
        "profile_completed": True,
    },
    {
        "username": "gonullu1",
        "email": "gonullu1@aura.local",
        "first_name": "Emre",
        "last_name": "Kaya",
        "role": User.Roles.VOLUNTEER_STUDENT,
        "university": "Anadolu University",
        "department": "Computer Engineering",
        "preferred_communication": "Platform mesajlaşması",
        "support_topics": "Programlama, matematik, ders çalışma, materyal düzenleme",
        "availability_notes": "Pazartesi ve Çarşamba akşamları",
        "profile_completed": True,
    },
    {
        "username": "gonullu2",
        "email": "gonullu2@aura.local",
        "first_name": "Elif",
        "last_name": "Sahin",
        "role": User.Roles.VOLUNTEER_STUDENT,
        "university": "Anadolu University",
        "department": "Guidance and Psychological Counseling",
        "preferred_communication": "Platform mesajlaşması",
        "support_topics": "Seslendirme, özet çıkarma, kaynak bulma, sosyal eşlik",
        "availability_notes": "Salı ve Perşembe gündüz",
        "profile_completed": True,
    },
]

DEMO_REQUEST_DEFINITIONS = [
    {
        "title": "İstatistik finali için tekrar desteği",
        "created_by": "ogrenci1",
        "assigned_volunteer": "gonullu1",
        "category": SupportRequest.Categories.ACADEMIC,
        "course_name": "İstatistik 101",
        "topic": "Hipotez testleri ve örnek soru çözümü",
        "description": "Final öncesi konu özeti ve örnek soru tekrarına ihtiyacım var.",
        "urgency": SupportRequest.Urgencies.HIGH,
        "status": SupportRequest.Statuses.MATCHED,
        "duration_value": 3,
        "duration_unit": SupportRequest.DurationUnits.DAY,
        "requested_completion_date_offset": 3,
        "preferred_timing": "Salı 18:00 sonrası",
        "messages": [
            ("ogrenci1", "Özellikle hipotez testleri kısmında desteğe ihtiyacım var."),
            ("gonullu1", "Bu akşam birlikte kısa bir tekrar planı çıkarabiliriz."),
        ],
    },
    {
        "title": "PDF materyalinin erişilebilir özetlenmesi",
        "created_by": "ogrenci1",
        "assigned_volunteer": "gonullu1",
        "category": SupportRequest.Categories.ACCESSIBLE_MATERIAL,
        "course_name": "Developmental Psychology",
        "topic": "Makale özetleme",
        "description": "Bir PDF makalenin erişilebilir ve kısa bir özetine ihtiyacım var.",
        "urgency": SupportRequest.Urgencies.MEDIUM,
        "status": SupportRequest.Statuses.IN_PROGRESS,
        "duration_value": 1,
        "duration_unit": SupportRequest.DurationUnits.WEEK,
        "requested_completion_date_offset": 7,
        "preferred_timing": "Bu hafta içinde",
        "material": {
            "uploaded_by": "ogrenci1",
            "title": "Makale özet notları",
            "description": "PDF içeriğinin okunabilir özet versiyonu.",
            "filename": "makale-ozeti.txt",
            "content": "Bu dosya, demo ortamı için üretilmiş örnek materyal içeriğidir.",
        },
    },
    {
        "title": "Osmanlıca metin için seslendirme desteği",
        "created_by": "ogrenci2",
        "assigned_volunteer": "gonullu2",
        "category": SupportRequest.Categories.AUDIO_NARRATION,
        "course_name": "Ottoman Turkish",
        "topic": "Metin seslendirme",
        "description": "Sınav öncesi çalışabilmem için iki sayfalık metnin seslendirilmesine ihtiyacım var.",
        "urgency": SupportRequest.Urgencies.MEDIUM,
        "status": SupportRequest.Statuses.MATCHED,
        "duration_value": 2,
        "duration_unit": SupportRequest.DurationUnits.DAY,
        "requested_completion_date_offset": 2,
        "preferred_timing": "Çarşamba öğleden sonra",
        "messages": [
            ("ogrenci2", "Dosyadaki açıklamaları sesli çalışabileceğim biçimde almak istiyorum."),
            ("gonullu2", "Bu akşam ilk bölümü seslendirebilirim."),
        ],
    },
    {
        "title": "Grafik ve tablo betimleme desteği",
        "created_by": "ogrenci1",
        "assigned_volunteer": "gonullu2",
        "category": SupportRequest.Categories.VISUAL_DESCRIPTION,
        "course_name": "Research Methods",
        "topic": "Grafik yorumlama",
        "description": "Sunum içindeki grafik ve tabloların açıklayıcı biçimde betimlenmesine ihtiyacım var.",
        "urgency": SupportRequest.Urgencies.HIGH,
        "status": SupportRequest.Statuses.OPEN,
        "duration_value": 1,
        "duration_unit": SupportRequest.DurationUnits.WEEK,
        "requested_completion_date_offset": 5,
        "preferred_timing": "Hafta içi 16:00 sonrası",
    },
    {
        "title": "Kütüphane kaynağına erişim desteği",
        "created_by": "ogrenci2",
        "assigned_volunteer": None,
        "category": SupportRequest.Categories.RESOURCE_ACCESS,
        "course_name": "Modern History",
        "topic": "Arşiv kaynağı bulma",
        "description": "Kütüphanede belirli iki kaynağa ulaşmak ve tarama planı yapmak için desteğe ihtiyacım var.",
        "urgency": SupportRequest.Urgencies.MEDIUM,
        "status": SupportRequest.Statuses.OPEN,
        "duration_value": 4,
        "duration_unit": SupportRequest.DurationUnits.DAY,
        "requested_completion_date_offset": 4,
        "preferred_timing": "Perşembe 11:00 sonrası",
    },
    {
        "title": "Birlikte ders çalışma oturumu planlama",
        "created_by": "ogrenci1",
        "assigned_volunteer": "gonullu1",
        "category": SupportRequest.Categories.JOINT_STUDY,
        "course_name": "Cognitive Psychology",
        "topic": "Düzenli tekrar oturumu",
        "description": "Haftalık tekrar ve soru çözümü için kısa bir çalışma planı oluşturmak istiyorum.",
        "urgency": SupportRequest.Urgencies.LOW,
        "status": SupportRequest.Statuses.COMPLETED,
        "duration_value": 1,
        "duration_unit": SupportRequest.DurationUnits.MONTH,
        "requested_completion_date_offset": 14,
        "preferred_timing": "Hafta sonu öğleden sonra",
        "messages": [
            ("gonullu1", "İlk oturumu tamamladık, gelecek hafta aynı düzende ilerleyebiliriz."),
        ],
    },
    {
        "title": "Kampüs etkinliğine katılım için eşlik",
        "created_by": "ogrenci2",
        "assigned_volunteer": "gonullu2",
        "category": SupportRequest.Categories.SOCIAL_ACTIVITY,
        "course_name": "Sosyal katılım",
        "topic": "Kulüp etkinliği eşliği",
        "description": "Hafta sonu kulüp etkinliğine katılım sırasında kısa süreli eşlik desteği istiyorum.",
        "urgency": SupportRequest.Urgencies.LOW,
        "status": SupportRequest.Statuses.IN_PROGRESS,
        "duration_value": 2,
        "duration_unit": SupportRequest.DurationUnits.DAY,
        "requested_completion_date_offset": 6,
        "preferred_timing": "Cumartesi 14:00",
    },
]

DEMO_REQUEST_TITLES = [item["title"] for item in DEMO_REQUEST_DEFINITIONS]


class Command(BaseCommand):
    help = (
        "Create AURA seed data. "
        'Use --dataset demo for rich sample data or --dataset pilot for a clean pilot baseline.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dataset",
            choices=("demo", "pilot"),
            default="demo",
            help='Seed profile to create. "demo" adds sample users and requests, "pilot" keeps a clean starting set.',
        )
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Remove known seed data first so the selected dataset can be recreated cleanly.",
        )

    def handle(self, *args, **options):
        dataset = options["dataset"]

        if options["reset"]:
            self.reset_seed_data()

        _, admin_created = self.create_or_update_admin()
        core_created_count = self.create_or_update_users(PILOT_CORE_USERS)
        demo_created_count = 0

        if dataset == "demo":
            demo_created_count = self.create_or_update_users(DEMO_USERS)
            self.seed_demo_requests_and_notifications()
        else:
            self.remove_demo_request_data()
            self.remove_demo_users()

        self.stdout.write(
            self.style.SUCCESS(
                self.build_summary(
                    dataset=dataset,
                    admin_created=admin_created,
                    core_created_count=core_created_count,
                    demo_created_count=demo_created_count,
                )
            )
        )

    def create_or_update_admin(self):
        admin_user, created = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@aura.local",
                "first_name": "AURA",
                "last_name": "Admin",
                "role": User.Roles.COORDINATOR,
                "is_staff": True,
                "is_superuser": True,
                "profile_completed": True,
            },
        )
        admin_user.email = "admin@aura.local"
        admin_user.role = User.Roles.COORDINATOR
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.profile_completed = True
        admin_user.set_password(ADMIN_PASSWORD)
        admin_user.save()
        return admin_user, created

    def create_or_update_users(self, user_payloads):
        created_count = 0
        for payload in user_payloads:
            username = payload["username"]
            user, created = User.objects.get_or_create(
                username=username,
                defaults=payload,
            )
            for field, value in payload.items():
                setattr(user, field, value)
            user.set_password(SEED_USER_PASSWORD)
            user.save()
            if created:
                created_count += 1
        return created_count

    def seed_demo_requests_and_notifications(self):
        self.remove_demo_request_data()

        created_requests = {}
        today = timezone.localdate()

        for definition in DEMO_REQUEST_DEFINITIONS:
            request_item = SupportRequest.objects.create(
                created_by=User.objects.get(username=definition["created_by"]),
                assigned_volunteer=(
                    User.objects.get(username=definition["assigned_volunteer"])
                    if definition["assigned_volunteer"]
                    else None
                ),
                title=definition["title"],
                category=definition["category"],
                course_name=definition["course_name"],
                topic=definition["topic"],
                description=definition["description"],
                urgency=definition["urgency"],
                status=definition["status"],
                duration_value=definition["duration_value"],
                duration_unit=definition["duration_unit"],
                requested_completion_date=today + timedelta(days=definition["requested_completion_date_offset"]),
                preferred_timing=definition["preferred_timing"],
            )
            created_requests[definition["title"]] = request_item

            for author_username, body in definition.get("messages", []):
                RequestMessage.objects.get_or_create(
                    request=request_item,
                    author=User.objects.get(username=author_username),
                    body=body,
                )

            material_definition = definition.get("material")
            if material_definition:
                material, _ = RequestMaterial.objects.get_or_create(
                    request=request_item,
                    uploaded_by=User.objects.get(username=material_definition["uploaded_by"]),
                    title=material_definition["title"],
                    defaults={
                        "description": material_definition["description"],
                    },
                )
                if not material.file:
                    material.description = material_definition["description"]
                    material.file.save(
                        material_definition["filename"],
                        ContentFile(material_definition["content"].encode("utf-8")),
                        save=True,
                    )

        Notification.objects.filter(title__in=DEMO_NOTIFICATION_TITLES).delete()

        create_notification(
            recipient=User.objects.get(username="ogrenci1"),
            title="Demo bildirim: yeni talep incelemenizi bekliyor",
            body="Kütüphane kaynağına erişim desteği talebi açık durumda ve gönüllü bekliyor.",
            actor=User.objects.get(username="koordinator1"),
            support_request=created_requests["Kütüphane kaynağına erişim desteği"],
        )
        create_notification(
            recipient=User.objects.get(username="gonullu1"),
            title="Demo bildirim: kaynak dosya eklendi",
            body="PDF materyalinin erişilebilir özetlenmesi talebine yeni kaynak dosya eklendi.",
            actor=User.objects.get(username="ogrenci1"),
            support_request=created_requests["PDF materyalinin erişilebilir özetlenmesi"],
        )
        create_notification(
            recipient=User.objects.get(username="koordinator1"),
            title="Demo bildirim: koordinasyon notu girildi",
            body="İstatistik finali için tekrar desteği talebi için yeni koordinasyon takibi gerekli.",
            actor=User.objects.get(username="danisman1"),
            support_request=created_requests["İstatistik finali için tekrar desteği"],
        )
        create_notification(
            recipient=User.objects.get(username="gonullu2"),
            title="Demo bildirim: destek bulusmasi planlandi",
            body="Osmanlıca metin için seslendirme desteği talebi için çalışma zamanı netleşti.",
            actor=User.objects.get(username="ogrenci2"),
            support_request=created_requests["Osmanlıca metin için seslendirme desteği"],
        )

    def remove_demo_request_data(self):
        materials = list(
            RequestMaterial.objects.filter(request__title__in=DEMO_REQUEST_TITLES)
        )
        for material in materials:
            if material.file:
                material.file.delete(save=False)

        Notification.objects.filter(title__in=DEMO_NOTIFICATION_TITLES).delete()
        SupportRequest.objects.filter(title__in=DEMO_REQUEST_TITLES).delete()

    def remove_demo_users(self):
        User.objects.filter(
            username__in=[payload["username"] for payload in DEMO_USERS]
        ).delete()

    def reset_seed_data(self):
        self.remove_demo_request_data()
        self.remove_demo_users()
        Notification.objects.filter(title__in=DEMO_NOTIFICATION_TITLES).delete()

    def build_summary(
        self,
        *,
        dataset,
        admin_created,
        core_created_count,
        demo_created_count,
    ):
        lines = [
            f"Seed veri profili hazir: {dataset}",
            f"Admin: admin / {ADMIN_PASSWORD}",
            f"Operasyon kullanici sifresi: {SEED_USER_PASSWORD}",
            f"Olusturulan yeni cekirdek kullanici sayisi: {core_created_count}",
            f"Olusturulan yeni demo kullanici sayisi: {demo_created_count}",
            f"Admin yeni olustu mu: {'evet' if admin_created else 'hayir'}",
        ]

        if dataset == "pilot":
            lines.extend(
                [
                    "Pilot baslangic seti: admin + 2 koordinator + 2 akademik danisman",
                    "Pilot baslangic setinde ornek talep, mesaj, materyal ve bildirim yok.",
                ]
            )
        else:
            lines.extend(
                [
                    "Demo seti: admin + 2 koordinator + 2 akademik danisman + 2 ogrenci + 2 gonullu",
                    "Demo setinde farkli kategorilerde, sure bilgisi eklenmis birden fazla ornek talep bulunur.",
                ]
            )

        return "\n".join(lines)
