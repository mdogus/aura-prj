from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("support", "0006_alter_requestmaterial_file"),
    ]

    operations = [
        migrations.AddField(
            model_name="supportrequestinterventionnote",
            name="priority",
            field=models.CharField(
                choices=[
                    ("normal", "Normal"),
                    ("high", "Yüksek önem"),
                    ("critical", "Kritik önem"),
                ],
                default="normal",
                max_length=16,
            ),
        ),
    ]
