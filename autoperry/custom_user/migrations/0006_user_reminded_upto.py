# Generated by Django 3.2.14 on 2023-01-02 18:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('custom_user', '0005_alter_user_send_notifications'),
    ]

    operations = [
        migrations.AddField(
            model_name='User',
            name='reminded_upto',
            field=models.DateTimeField(blank=True, help_text='End date of most recent reminder run', null=True),
        ),
    ]