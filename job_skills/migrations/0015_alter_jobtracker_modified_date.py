# Generated by Django 4.1.1 on 2022-10-01 16:56

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('job_skills', '0014_remove_parserdata_error_log_remove_skilldata_tracker_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='jobtracker',
            name='modified_date',
            field=models.DateField(default=django.utils.timezone.now),
        ),
    ]
