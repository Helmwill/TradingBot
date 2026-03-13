from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trading', '0002_add_trade_ohlcvbar_models'),
    ]

    operations = [
        migrations.CreateModel(
            name='TradingError',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('instrument', models.CharField(max_length=50)),
                ('message', models.TextField()),
            ],
            options={
                'ordering': ['-timestamp'],
            },
        ),
    ]
