# Generated by Django 3.0.4 on 2020-03-17 18:04

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(max_length=10)),
                ('email', models.EmailField(max_length=254)),
                ('password', models.CharField(max_length=20)),
                ('date', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Date de parution')),
                ('signup_confirmation', models.BooleanField(default=False)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'nom utilisateur',
                'ordering': ['date'],
            },
        ),
        migrations.CreateModel(
            name='Actif',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.CharField(max_length=100)),
                ('monnaie', models.CharField(max_length=20)),
                ('api', models.CharField(max_length=20)),
                ('quantite', models.FloatField()),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='compte.Profile')),
            ],
            options={
                'verbose_name': 'porte_monnaie',
            },
        ),
    ]
