# Generated by Django 3.2.14 on 2022-12-30 16:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webapp', '0015_alter_event_contact_address'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='contact_address',
            field=models.EmailField(blank=True, help_text="Email address for the event, defaults to owner's address", max_length=254, null=True),
        ),
    ]