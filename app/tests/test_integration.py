"""
Integration tests. Day 2 will fill these in fully once /bot/status/ and /bot/trades/ exist.
Tests marked xfail are expected to fail until those endpoints are built.
"""
import pytest
from unittest.mock import patch
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken


def auth_client():
    user = User.objects.create_user(username='inttest', password='pass')
    refresh = RefreshToken.for_user(user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION='Bearer ' + str(refresh.access_token))
    return client


MOCK_ORDER = {
    'order_id': 'integration-001',
    'status': 'FILLED',
    'symbol': 'AAPL',
    'side': 'BUY',
    'volume': 1.0,
    'price': 175.50,
}


@pytest.mark.django_db
@pytest.mark.xfail(reason="Not built yet — coming in Day 2")
def test_bot_status_endpoint(authenticated_client):
    response = authenticated_client.get('/bot/status/')
    assert response.status_code == 200
    assert response.json()['status'] == 'running'


@pytest.mark.django_db
@pytest.mark.xfail(reason="Not built yet — coming in Day 2")
def test_bot_trades_endpoint(authenticated_client):
    response = authenticated_client.get('/bot/trades/')
    assert response.status_code == 200


@pytest.mark.django_db
@patch('trading.views._ctrader_client')
def test_buy_then_sell_creates_two_trade_records(mock_client):
    from trading.models import Trade
    mock_client.place_order.return_value = MOCK_ORDER
    client = auth_client()
    client.post('/buy/', data={'symbol': 'AAPL', 'amount': '1.0'}, format='json')
    mock_client.place_order.return_value = {**MOCK_ORDER, 'side': 'SELL'}
    client.post('/sell/', data={'symbol': 'AAPL', 'amount': '1.0'}, format='json')
    assert Trade.objects.filter(instrument='AAPL').count() == 2


@pytest.mark.django_db
def test_market_historical_returns_501():
    response = auth_client().get('/market/historical/')
    assert response.status_code == 501
