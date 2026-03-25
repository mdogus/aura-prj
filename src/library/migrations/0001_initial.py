from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('support', '0009_requestmaterial_revision_fields'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='LibraryItem',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                ('title', models.CharField(max_length=255, verbose_name='Başlık')),
                ('description', models.TextField(blank=True, verbose_name='Açıklama')),
                ('category', models.CharField(blank=True, max_length=64, verbose_name='Kategori')),
                (
                    'tags',
                    models.CharField(
                        blank=True,
                        help_text='Virgülle ayrılmış etiketler.',
                        max_length=255,
                        verbose_name='Etiketler',
                    ),
                ),
                ('is_active', models.BooleanField(default=True, verbose_name='Aktif')),
                ('added_at', models.DateTimeField(auto_now_add=True, verbose_name='Eklenme tarihi')),
                (
                    'added_by',
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='added_library_items',
                        to=settings.AUTH_USER_MODEL,
                        verbose_name='Ekleyen',
                    ),
                ),
                (
                    'material',
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='library_item',
                        to='support.requestmaterial',
                        verbose_name='Materyal',
                    ),
                ),
            ],
            options={
                'verbose_name': 'Kütüphane öğesi',
                'verbose_name_plural': 'Kütüphane öğeleri',
                'ordering': ['-added_at'],
            },
        ),
    ]
