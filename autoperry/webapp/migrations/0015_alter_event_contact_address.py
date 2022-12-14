# Generated by Django 3.2.14 on 2022-12-30 15:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webapp', '0014_auto_20221230_1547'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='contact_address',
            field=models.EmailField(default='missing', help_text="Email address for the event, defaults to owner's address", max_length=254),
        ),
    ]
