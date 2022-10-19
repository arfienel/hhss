# Generated by Django 4.1.1 on 2022-10-18 18:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('job_skills', '0024_alter_area_hh_id_alter_area_name'),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name='area',
            name='job_skills__hh_id_316a4d_idx',
        ),
        migrations.AlterField(
            model_name='area',
            name='hh_id',
            field=models.IntegerField(db_index=True, unique=True),
        ),
        migrations.AlterField(
            model_name='area',
            name='name',
            field=models.CharField(db_index=True, max_length=1000),
        ),
    ]