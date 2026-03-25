from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('support', '0008_add_supportrequest_indexes'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='requestmaterial',
            name='status',
            field=models.CharField(
                choices=[
                    ('draft', 'Taslak'),
                    ('revision_requested', 'Revizyon istendi'),
                    ('approved', 'Onaylandı'),
                ],
                default='draft',
                max_length=24,
            ),
        ),
        migrations.AddField(
            model_name='requestmaterial',
            name='version',
            field=models.PositiveSmallIntegerField(default=1),
        ),
        migrations.AddField(
            model_name='requestmaterial',
            name='parent_material',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='revisions',
                to='support.requestmaterial',
            ),
        ),
        migrations.AddField(
            model_name='requestmaterial',
            name='revision_note',
            field=models.TextField(
                blank=True,
                help_text='Koordinatörün revizyon talebi veya onay notu.',
            ),
        ),
        migrations.AlterField(
            model_name='supportrequestactivitylog',
            name='action_type',
            field=models.CharField(
                choices=[
                    ('request_created', 'Talep oluşturuldu'),
                    ('status_updated', 'Durum güncellendi'),
                    ('priority_updated', 'Öncelik güncellendi'),
                    ('volunteer_assigned', 'Gönüllü atandı'),
                    ('intervention_note', 'Müdahale notu eklendi'),
                    ('message_posted', 'Mesaj gönderildi'),
                    ('material_uploaded', 'Materyal yüklendi'),
                    ('material_revision_requested', 'Materyal revizyonu istendi'),
                    ('material_approved', 'Materyal onaylandı'),
                    ('material_revised', 'Materyal revize edildi'),
                ],
                max_length=32,
            ),
        ),
    ]
