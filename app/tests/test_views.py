import json
from django.test import TestCase, Client
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User

class TradingBotViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.token = self.get_token_for_user(self.user)

    def get_token_for_user(self, user):
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)

    def test_health_check_view(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)
        response = self.client.get(reverse('health_check'))
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"message": "Health check: status ok"})

    def test_coinbase_historical_data_view(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)
        response = self.client.get(reverse('coinbase_historical_data_view'), {
            'product_id': 'BTC-USD',
            'start': '2022-01-01T00:00:00Z',
            'end': '2022-01-31T00:00:00Z'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('BTC-USD', response.json())