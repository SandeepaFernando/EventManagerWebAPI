# Generated by Django 3.0.6 on 2020-06-28 11:02

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.datetime_safe


class Migration(migrations.Migration):

    dependencies = [
        ('EventMangerAPI', '0004_auto_20200623_2342'),
    ]

    operations = [
        migrations.CreateModel(
            name='EventComment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('comment', models.TextField(default='')),
                ('sentimentValue', models.IntegerField(default=-1)),
                ('commentedOn', models.DateTimeField(default=django.utils.datetime_safe.datetime.now)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('eventId', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='eventReviews', to='EventMangerAPI.Event')),
                ('userId', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reviews', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
