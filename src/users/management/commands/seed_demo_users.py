from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from notifications.models import Notification
from notifications.services import create_notification
from support.models import RequestMaterial, RequestMessage, SupportRequest
from users.models import User


ADMIN_PASSWORD = 'AuraPilot123!'
SEED_USER_PASSWORD = 'AuraPilot123!'

DEMO_NOTIFICATION_TITLES = [
    'Demo bildirim: destek planı hazır',
    'Demo bildirim: yeni materyal incelenebilir',
]

DEMO_REQUEST_TITLES = [
    'İstatistik finali için tekrar desteği',
    'PDF materyalinin erişilebilir özetlenmesi',
]

DEMO_USERS = [
    {
        'username': 'gorme1',
        'email': 'gorme1@aura.local',
        'first_name': 'Ayse',
        'last_name': 'Demir',
        'role': User.Roles.VISUALLY_IMPAIRED_STUDENT,
        'university': 'Bogazici University',
        'department': 'Psychology',
        'preferred_communication': 'Platform mesajlaşması',
        'support_topics': 'Psikoloji, istatistik, PDF özetleme',
        'availability_notes': 'Hafta içi akşam',
        'profile_completed': True,
    },
    {
        'username': 'gonullu1',
        'email': 'gonullu1@aura.local',
        'first_name': 'Emre',
        'last_name': 'Kaya',
        'role': User.Roles.VOLUNTEER_STUDENT,
        'university': 'Bogazici University',
        'department': 'Computer Engineering',
        'preferred_communication': 'Platform mesajlaşması',
        'support_topics': 'Programlama, matematik, ders çalışma',
        'availability_notes': 'Pazartesi ve Çarşamba akşamları',
        'profile_completed': True,
    },
]

PILOT_CORE_USERS = [
    {
        'username': 'danisman1',
        'email': 'danisman1@aura.local',
        'first_name': 'Selin',
        'last_name': 'Arslan',
        'role': User.Roles.ACADEMIC_ADVISOR,
        'university': 'Bogazici University',
        'department': 'Education',
        'preferred_communication': 'Platform mesajlaşması',
        'support_topics': 'Akademik planlama, ders stratejisi, materyal rehberliği',
        'availability_notes': 'Hafta içi gündüz',
        'profile_completed': True,
    },
    {
        'username': 'koordinator1',
        'email': 'koordinator1@aura.local',
        'first_name': 'Merve',
        'last_name': 'Yildiz',
        'role': User.Roles.COORDINATOR,
        'university': 'Bogazici University',
        'department': 'Student Affairs',
        'preferred_communication': 'Platform mesajlaşması',
        'profile_completed': True,
        'is_staff': True,
    },
]


class Command(BaseCommand):
    help = (
        'Create AURA seed data. '
        'Use --dataset demo for rich sample data or --dataset pilot for a clean pilot baseline.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dataset',
            choices=('demo', 'pilot'),
            default='demo',
            help='Seed profile to create. "demo" adds sample users and requests, "pilot" keeps a clean starting set.',
        )
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Remove known seed data first so the selected dataset can be recreated cleanly.',
        )

    def handle(self, *args, **options):
        dataset = options['dataset']

        if options['reset']:
            self.reset_seed_data()

        admin_user, admin_created = self.create_or_update_admin()
        core_created_count = self.create_or_update_users(PILOT_CORE_USERS)
        demo_created_count = 0

        if dataset == 'demo':
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
            username='admin',
            defaults={
                'email': 'admin@aura.local',
                'first_name': 'AURA',
                'last_name': 'Admin',
                'role': User.Roles.COORDINATOR,
                'is_staff': True,
                'is_superuser': True,
                'profile_completed': True,
            },
        )
        admin_user.email = 'admin@aura.local'
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
            username = payload['username']
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
        student = User.objects.get(username='gorme1')
        volunteer = User.objects.get(username='gonullu1')

        self.remove_demo_request_data()

        first_request = SupportRequest.objects.create(
            created_by=student,
            assigned_volunteer=volunteer,
            title='İstatistik finali için tekrar desteği',
            category=SupportRequest.Categories.ACADEMIC,
            course_name='İstatistik 101',
            topic='Hipotez testleri',
            description='Final öncesi konu özeti ve soru tekrarına ihtiyacım var.',
            urgency=SupportRequest.Urgencies.HIGH,
            preferred_timing='Salı 18:00 sonrası',
            status=SupportRequest.Statuses.MATCHED,
        )

        second_request = SupportRequest.objects.create(
            created_by=student,
            assigned_volunteer=volunteer,
            title='PDF materyalinin erişilebilir özetlenmesi',
            category=SupportRequest.Categories.ACCESSIBLE_MATERIAL,
            course_name='Developmental Psychology',
            topic='Makale özetleme',
            description='Bir PDF makalenin okunabilir özetine ihtiyacım var.',
            urgency=SupportRequest.Urgencies.MEDIUM,
            preferred_timing='Bu hafta içinde',
            status=SupportRequest.Statuses.IN_PROGRESS,
        )

        RequestMessage.objects.get_or_create(
            request=first_request,
            author=student,
            body='İstatistik finali için özellikle hipotez testleri kısmında desteğe ihtiyacım var.',
        )
        RequestMessage.objects.get_or_create(
            request=first_request,
            author=volunteer,
            body='Bu akşam birlikte bir tekrar planı çıkarabiliriz.',
        )

        material, _ = RequestMaterial.objects.get_or_create(
            request=second_request,
            uploaded_by=student,
            title='Makale özet notları',
            defaults={
                'description': 'PDF içeriğinin okunabilir özet versiyonu.',
            },
        )
        if not material.file:
            material.description = 'PDF içeriğinin okunabilir özet versiyonu.'
            material.file.save(
                'makale-ozeti.txt',
                ContentFile(
                    'Bu dosya, geliştirme ortamı için üretilmiş örnek materyal içeriğidir.'.encode(
                        'utf-8'
                    )
                ),
                save=True,
            )

        Notification.objects.filter(
            recipient__username__in=['gorme1', 'gonullu1', 'danisman1', 'koordinator1'],
            title__in=DEMO_NOTIFICATION_TITLES,
        ).delete()
        create_notification(
            recipient=student,
            title='Demo bildirim: destek planı hazır',
            body='İstatistik talebiniz için gönüllü ile ilk çalışma planı oluşturuldu.',
            actor=volunteer,
            support_request=first_request,
        )
        create_notification(
            recipient=volunteer,
            title='Demo bildirim: yeni materyal incelenebilir',
            body='PDF özet talebine eklenen materyali inceleyebilirsiniz.',
            actor=student,
            support_request=second_request,
        )

    def remove_demo_request_data(self):
        materials = list(
            RequestMaterial.objects.filter(
                request__title__in=DEMO_REQUEST_TITLES
            )
        )
        for material in materials:
            if material.file:
                material.file.delete(save=False)

        Notification.objects.filter(title__in=DEMO_NOTIFICATION_TITLES).delete()
        SupportRequest.objects.filter(title__in=DEMO_REQUEST_TITLES).delete()

    def remove_demo_users(self):
        User.objects.filter(
            username__in=[payload['username'] for payload in DEMO_USERS]
        ).delete()

    def reset_seed_data(self):
        self.remove_demo_request_data()
        self.remove_demo_users()
        Notification.objects.filter(
            recipient__username__in=['admin', 'danisman1', 'koordinator1'],
            title__in=DEMO_NOTIFICATION_TITLES,
        ).delete()

    def build_summary(
        self,
        *,
        dataset,
        admin_created,
        core_created_count,
        demo_created_count,
    ):
        lines = [
            f'Seed veri profili hazir: {dataset}',
            f'Admin: admin / {ADMIN_PASSWORD}',
            f'Operasyon kullanici sifresi: {SEED_USER_PASSWORD}',
            f'Olusturulan yeni cekirdek kullanici sayisi: {core_created_count}',
            f'Olusturulan yeni demo kullanici sayisi: {demo_created_count}',
            f'Admin yeni olustu mu: {"evet" if admin_created else "hayir"}',
        ]

        if dataset == 'pilot':
            lines.extend(
                [
                    'Pilot baslangic seti: admin + koordinator + akademik danisman',
                    'Pilot baslangic setinde ornek talep, mesaj, materyal ve bildirim yok.',
                ]
            )
        else:
            lines.extend(
                [
                    'Demo seti: admin + koordinator + akademik danisman + ogrenci + gonullu',
                    'Demo setinde iki ornek talep, mesajlar ve materyal bulunur.',
                ]
            )

        return '\n'.join(lines)
