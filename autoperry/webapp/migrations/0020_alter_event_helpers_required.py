# Generated by Django 3.2.14 on 2023-02-09 18:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webapp', '0019_alter_event_notes'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='helpers_required',
            field=models.IntegerField(verbose_name='helpers needed'),
        ),
    ]
