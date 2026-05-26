# Generated for Tugas 3 secure coding update.

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="employeeprofile",
            name="position",
            field=models.CharField(
                default="Staff",
                max_length=80,
                validators=[
                    django.core.validators.RegexValidator(
                        "^[A-Za-zÀ-ÿ0-9 .,'/&()\\-]{2,80}$",
                        "Jabatan mengandung karakter tidak valid.",
                    )
                ],
            ),
        ),
        migrations.AlterField(
            model_name="employeeprofile",
            name="employee_id",
            field=models.CharField(
                max_length=20,
                unique=True,
                validators=[
                    django.core.validators.RegexValidator(
                        "^EMP-?[0-9]{3,8}$",
                        "Format ID karyawan harus seperti EMP001 atau EMP-0001.",
                    )
                ],
            ),
        ),
    ]
