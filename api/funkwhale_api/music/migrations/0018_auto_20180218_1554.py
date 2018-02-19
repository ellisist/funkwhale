# Generated by Django 2.0.2 on 2018-02-18 15:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('music', '0017_auto_20171227_1728'),
    ]

    operations = [
        migrations.AddField(
            model_name='trackfile',
            name='mimetype',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AlterField(
            model_name='importjob',
            name='source',
            field=models.CharField(max_length=500),
        ),
        migrations.AlterField(
            model_name='importjob',
            name='status',
            field=models.CharField(choices=[('pending', 'Pending'), ('finished', 'Finished'), ('errored', 'Errored'), ('skipped', 'Skipped')], default='pending', max_length=30),
        ),
    ]
