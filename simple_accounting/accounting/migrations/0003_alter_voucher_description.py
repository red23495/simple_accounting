# Generated by Django 3.2.16 on 2023-01-21 19:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounting', '0002_auto_20230121_1927'),
    ]

    operations = [
        migrations.AlterField(
            model_name='voucher',
            name='description',
            field=models.TextField(blank=True, null=True),
        ),
    ]
