# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-08-08 09:56
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0002_auto_20170404_1259'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='transaction',
            name='lat',
        ),
        migrations.RemoveField(
            model_name='transaction',
            name='lon',
        ),
        migrations.AddField(
            model_name='transaction',
            name='address',
            field=models.TextField(blank=True),
        ),
    ]
