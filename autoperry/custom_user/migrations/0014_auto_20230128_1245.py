# Generated by Django 3.2.14 on 2023-01-28 12:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('custom_user', '0013_alter_user_tower'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='send_other',
            field=models.BooleanField(default=True, help_text='Send other emails', verbose_name='send other emails'),
        ),
        migrations.AlterField(
            model_name='user',
            name='send_notifications',
            field=models.BooleanField(default=True, help_text='Send emails about your events', verbose_name='send event emails'),
        ),
    ]