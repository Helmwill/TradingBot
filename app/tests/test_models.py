from django.test import TestCase
from trading.models import HistoricalData

class HistoricalDataModelTest(TestCase):

    def test_historical_data_creation(self):
        historical_data = HistoricalData.objects.create(
            product_id='BTC-USD',
            timestamp='2022-01-01T00:00:00Z',
            low=40000.0,
            high=50000.0,
            open=45000.0,
            close=47000.0,
            volume=1000.0
        )
        self.assertEqual(historical_data.product_id, 'BTC-USD')
        self.assertEqual(historical_data.low, 40000.0)
