# Generated by Django 3.0.4 on 2020-03-25 16:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0008_auto_20200325_1556'),
    ]

    operations = [
        migrations.AddField(
            model_name='article',
            name='label',
            field=models.TextField(default=''),
        ),
    ]
