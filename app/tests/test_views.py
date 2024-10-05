import json
from django.test import TestCase, Client
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from unittest.mock import patch
from django.conf import settings

class TradingBotViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.token = self.get_token_for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)

    def get_token_for_user(self, user):
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)

    def test_health_check_view(self):
        response = self.client.get(reverse('health_check'))
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"message": "Health check: status ok"})

    @patch('requests.get')
    def test_coinbase_historical_data_view(self, mock_get):
        mock_response = [
            [1633024800, 43000.0, 44000.0, 43500.0, 43800.0, 120.0],
            [1633028400, 43800.0, 44500.0, 43900.0, 44200.0, 80.0]
        ]
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_response

        response = self.client.get(reverse('coinbase_historical_data_view'), {
            'product_id': 'BTC-USD',
            'granularity': '300'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)
        self.assertEqual(len(response.json()), 2)

    @patch('requests.get')
    def test_current_prices_view(self, mock_get):
        mock_response = {
            "trade_id": 4729088,
            "price": "50000.00",
            "size": "0.01000000",
            "time": "2023-10-10T15:45:13.646456Z",
            "bid": "49999.99",
            "ask": "50000.01",
            "volume": "1000.123456",
            "best_bid": "49999.99",
            "best_ask": "50000.01",
            "last_size": "0.01000000"
        }
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_response

        response = self.client.get(reverse('current_prices_view'), {'product_id': 'BTC-USD'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['price'], "50000.00")

    @patch('requests.post')
    @patch('requests.get')
    def test_buy_request(self, mock_get, mock_post):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "price": "50000.00"
        }
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "id": "order_id_123",
            "status": "done"
        }

        response = self.client.post(reverse('buy_request'), json.dumps({
            'product_id': 'BTC-USD',
            'amount': '100.00'
        }), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('id', response.json())
        self.assertEqual(response.json()['status'], 'done')

    @patch('requests.post')
    @patch('requests.get')
    def test_sell_request(self, mock_get, mock_post):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "price": "50000.00"
        }
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "id": "order_id_123",
            "status": "done"
        }

        response = self.client.post(reverse('sell_request'), json.dumps({
            'product_id': 'BTC-USD',
            'amount': '0.01'
        }), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('id', response.json())
        self.assertEqual(response.json()['status'], 'done')