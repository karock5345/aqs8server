# Generated by Django 4.2.16 on 2024-09-30 19:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0027_userprofile_index_i_userprofile_index_q_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Domain',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, unique=True)),
                ('title', models.CharField(max_length=200)),
                ('logo', models.CharField(max_length=200)),
            ],
        ),
    ]
