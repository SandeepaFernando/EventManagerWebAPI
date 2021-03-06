# Generated by Django 3.0.6 on 2020-06-19 16:31

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.datetime_safe


class Migration(migrations.Migration):

    dependencies = [
        ('EventMangerAPI', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(default='')),
                ('eventDate', models.DateTimeField(default=django.utils.datetime_safe.datetime.now)),
                ('venue', models.TextField(default='')),
                ('noOfGuests', models.IntegerField(default=0)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('organizer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='events', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AlterField(
            model_name='vendorskill',
            name='tagId',
            field=models.ForeignKey(blank=True, default='', on_delete=django.db.models.deletion.CASCADE, to='EventMangerAPI.Skill'),
        ),
        migrations.CreateModel(
            name='EventTags',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('eventId', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='eventTags', to='EventMangerAPI.Event')),
                ('tagId', models.ForeignKey(blank=True, default='', on_delete=django.db.models.deletion.CASCADE, to='EventMangerAPI.Skill')),
            ],
        ),
    ]
