# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-06-09 07:33
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Instruments',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('symbol', models.CharField(max_length=100)),
                ('token', models.CharField(max_length=100)),
                ('tick_size', models.CharField(max_length=100)),
                ('exchange', models.CharField(max_length=100)),
            ],
            options={
                'db_table': 'Instruments',
                'managed': True,
            },
        ),
    ]
