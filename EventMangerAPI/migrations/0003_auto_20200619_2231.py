# Generated by Django 3.0.6 on 2020-06-19 17:01

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('EventMangerAPI', '0002_auto_20200619_2201'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vendorskill',
            name='tagId',
            field=models.ForeignKey(blank=True, default='', on_delete=django.db.models.deletion.CASCADE, related_name='tag', to='EventMangerAPI.Skill'),
        ),
    ]