import json
from django.test import TestCase, Client
import responses
from django.urls import reverse

class TradingBotTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    @responses.activate
    def test_buy_order(self):
        # Mock the Coinbase API response
        responses.add(
            responses.POST,
            'https://api-public.sandbox.pro.coinbase.com/orders',
            json={"id": "test-order-id", "status": "done"},
            status=200
        )

        # Perform the buy request
        response = self.client.post(reverse('buy_request'), data=json.dumps({
            'product_id': 'BTC-USD',
            'amount': '10'
        }), content_type='application/json')

        self.assertEqual(response.status_code, 200)
        self.assertIn('id', response.json())
        self.assertEqual(response.json()['status'], 'done')

    @responses.activate
    def test_sell_order(self):
        # Mock the Coinbase API response
        responses.add(
            responses.POST,
            'https://api-public.sandbox.pro.coinbase.com/orders',
            json={"id": "test-order-id", "status": "done"},
            status=200
        )

        # Perform the sell request
        response = self.client.post(reverse('sell_request'), data=json.dumps({
            'product_id': 'BTC-USD',
            'amount': '10'
        }), content_type='application/json')

        self.assertEqual(response.status_code, 200)
        self.assertIn('id', response.json())
        self.assertEqual(response.json()['status'], 'done')