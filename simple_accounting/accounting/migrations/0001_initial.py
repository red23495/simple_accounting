# Generated by Django 4.1.5 on 2023-01-21 07:07

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Account',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=256)),
                ('account_number', models.CharField(db_index=True, max_length=32, unique=True)),
                ('account_type', models.IntegerField(choices=[(1, 'Asset'), (2, 'Liability'), (3, 'Equity'), (4, 'Revenue'), (5, 'Expense')])),
                ('description', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('inactive', models.BooleanField(default=False)),
                ('parent', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='accounting.account')),
            ],
        ),
    ]