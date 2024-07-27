# Generated by Django 4.0.4 on 2024-07-19 21:38

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('train_station', '0004_alter_ticket_journey_alter_ticket_order'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='journey',
            options={'ordering': ['-departure_time']},
        ),
        migrations.AlterModelOptions(
            name='order',
            options={'ordering': ['-created_at']},
        ),
        migrations.AlterModelOptions(
            name='station',
            options={'ordering': ['name']},
        ),
        migrations.AlterModelOptions(
            name='train',
            options={'ordering': ['name']},
        ),
        migrations.AlterUniqueTogether(
            name='station',
            unique_together={('name', 'latitude', 'longitude')},
        ),
    ]