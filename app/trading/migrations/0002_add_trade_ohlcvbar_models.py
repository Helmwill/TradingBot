# Generated manually on 2026-03-13 (TimescaleDB not running in CI at migration time)
# S4.1: Add Trade and OHLCVBar models

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trading', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Trade',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                ('timestamp', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('instrument', models.CharField(max_length=50)),
                ('action', models.CharField(max_length=4)),
                ('price', models.DecimalField(decimal_places=8, max_digits=20)),
                ('amount', models.DecimalField(decimal_places=8, max_digits=20)),
                ('signal_meta', models.JSONField(default=dict)),
                ('order_id', models.CharField(blank=True, max_length=100)),
            ],
            options={
                'ordering': ['-timestamp'],
            },
        ),
        migrations.CreateModel(
            name='OHLCVBar',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                ('timestamp', models.DateTimeField(db_index=True)),
                ('instrument', models.CharField(max_length=50)),
                ('open', models.DecimalField(decimal_places=8, max_digits=20)),
                ('high', models.DecimalField(decimal_places=8, max_digits=20)),
                ('low', models.DecimalField(decimal_places=8, max_digits=20)),
                ('close', models.DecimalField(decimal_places=8, max_digits=20)),
                ('volume', models.DecimalField(decimal_places=8, max_digits=20)),
            ],
            options={
                'ordering': ['-timestamp'],
            },
        ),
        migrations.AddIndex(
            model_name='trade',
            index=models.Index(fields=['instrument', 'timestamp'], name='trading_tra_instrum_idx'),
        ),
        migrations.AddIndex(
            model_name='ohlcvbar',
            index=models.Index(fields=['instrument', 'timestamp'], name='trading_ohl_instrum_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='ohlcvbar',
            unique_together={('instrument', 'timestamp')},
        ),
    ]
