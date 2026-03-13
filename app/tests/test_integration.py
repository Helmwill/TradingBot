"""
Integration tests for all API endpoints.
All cTrader API calls are mocked — no live Pepperstone API is used.
"""
import pytest
from unittest.mock import patch, MagicMock
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
@patch('trading.views._ctrader_client')
def test_bot_status_returns_running(mock_client):
    mock_client.get_spot_price.return_value = 175.50
    response = auth_client().get('/bot/status/')
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'running'
    assert 'instruments' in data
    assert isinstance(data['instruments'], list)
    assert 'uptime_seconds' in data


@pytest.mark.django_db
@patch('trading.views._ctrader_client')
def test_bot_trades_returns_list(mock_client):
    response = auth_client().get('/bot/trades/')
    assert response.status_code == 200
    data = response.json()
    assert 'trades' in data
    assert 'total' in data
    assert isinstance(data['trades'], list)


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


@pytest.mark.django_db
@patch('trading.views._ctrader_client')
def test_current_prices_endpoint(mock_client):
    mock_client.get_spot_price.return_value = 175.50
    response = auth_client().get('/current_prices/', {'symbol': 'AAPL'})
    assert response.status_code == 200
    assert response.json()['price'] == 175.50


@pytest.mark.django_db
def test_bot_trades_pagination():
    response = auth_client().get('/bot/trades/', {'page': 1, 'page_size': 10})
    assert response.status_code == 200
    data = response.json()
    assert data['page'] == 1
    assert data['page_size'] == 10


@pytest.mark.django_db
def test_unauthenticated_request_rejected():
    for path in ['/bot/status/', '/bot/trades/', '/buy/', '/sell/', '/current_prices/']:
        response = APIClient().get(path)
        assert response.status_code == 401, f"{path} should require auth"
