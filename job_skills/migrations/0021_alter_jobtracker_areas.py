# Generated by Django 4.1.1 on 2022-10-08 19:01

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('job_skills', '0020_remove_jobtracker_areas_jobtracker_areas'),
    ]

    operations = [
        migrations.AlterField(
            model_name='jobtracker',
            name='areas',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.IntegerField(), default=[], size=None),
        ),
    ]
