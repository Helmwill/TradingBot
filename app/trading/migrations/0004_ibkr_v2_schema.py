from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Replace legacy Coinbase/cTrader schema with IBKR v2 schema.
    - Drop HistoricalData (legacy Coinbase model)
    - Rename Trade.instrument → ticker, price → fill_price, amount → quantity
    - Add Trade.status
    - Rename OHLCVBar.instrument → ticker
    - Rename TradingError.instrument → ticker
    """

    dependencies = [
        ('trading', '0003_add_tradingerror_model'),
    ]

    operations = [
        migrations.DeleteModel(name='HistoricalData'),

        migrations.RenameField(model_name='trade', old_name='instrument', new_name='ticker'),
        migrations.RenameField(model_name='trade', old_name='price', new_name='fill_price'),
        migrations.RenameField(model_name='trade', old_name='amount', new_name='quantity'),
        migrations.AddField(
            model_name='trade',
            name='status',
            field=models.CharField(default='Filled', max_length=20),
        ),

        migrations.RenameField(model_name='ohlcvbar', old_name='instrument', new_name='ticker'),

        migrations.RenameField(model_name='tradingerror', old_name='instrument', new_name='ticker'),
    ]
