# Generated by Django 3.2.14 on 2022-12-12 18:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webapp', '0007_auto_20221207_1414'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='volunteer',
            constraint=models.UniqueConstraint(fields=('event', 'person'), name='only_volunteer_once'),
        ),
    ]