# Generated by Django 4.1.1 on 2022-10-29 15:49

from django.conf import settings
import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('job_skills', '0029_alter_jobtracker_exclude_from_search'),
    ]

    operations = [
        migrations.AlterField(
            model_name='jobtracker',
            name='areas',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.IntegerField(), blank=True, db_index=True, default=[], size=None),
        ),
        migrations.AlterField(
            model_name='jobtracker',
            name='employment_type',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=100), blank=True, db_index=True, default=[], size=None),
        ),
        migrations.AlterField(
            model_name='jobtracker',
            name='subscribers',
            field=models.ManyToManyField(blank=True, related_name='job_tracker_subs', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='jobtracker',
            name='work_schedule',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=100), blank=True, db_index=True, default=[], size=None),
        ),
    ]
