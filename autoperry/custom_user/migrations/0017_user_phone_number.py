# Generated by Django 3.2.14 on 2023-03-12 10:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('custom_user', '0016_user_uuid'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='phone_number',
            field=models.CharField(blank=True, help_text='Optional, useful in case of last-minute cancellations and changes of plan', max_length=64),
        ),
    ]
