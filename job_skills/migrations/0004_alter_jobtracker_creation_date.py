# Generated by Django 4.1 on 2022-09-18 12:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('job_skills', '0003_jobtracker_creation_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='jobtracker',
            name='creation_date',
            field=models.DateField(auto_now_add=True),
        ),
    ]
