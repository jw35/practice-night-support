# Generated by Django 3.2.14 on 2023-01-28 11:52

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('custom_user', '0010_alter_user_options'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='user',
            options={'permissions': [('administrator', 'Is system administrator')]},
        ),
    ]
