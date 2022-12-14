# Generated by Django 3.2.14 on 2022-12-12 18:08

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('webapp', '0008_volunteer_only_volunteer_once'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='helpers',
            field=models.ManyToManyField(related_name='events_volunteered', through='webapp.Volunteer', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='event',
            name='owner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='events_owned', to=settings.AUTH_USER_MODEL),
        ),
    ]
