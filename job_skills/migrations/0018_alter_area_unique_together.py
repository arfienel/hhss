# Generated by Django 4.1.1 on 2022-10-05 05:55

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('job_skills', '0017_area_jobtracker_areas'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='area',
            unique_together={('hh_id', 'name')},
        ),
    ]
