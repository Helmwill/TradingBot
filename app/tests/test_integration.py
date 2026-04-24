"""
Integration tests for all API endpoints.
All IBKR calls are mocked — no live IB Gateway connection is used.
"""
import json
import pytest
from unittest.mock import patch, MagicMock
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken


def auth_client(username='inttest'):
    user = User.objects.create_user(username=username, password='pass')
    refresh = RefreshToken.for_user(user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION='Bearer ' + str(refresh.access_token))
    return client


MOCK_ORDER = {
    'order_id': 'integration-001',
    'status': 'Filled',
    'ticker': 'AAPL',
    'action': 'BUY',
    'quantity': 5,
    'fill_price': 175.50,
}


@pytest.mark.django_db
def test_bot_status_returns_running():
    response = auth_client('status_int').get('/bot/status/')
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'running'
    assert data['broker'] == 'Interactive Brokers'
    assert 'tickers' in data
    assert isinstance(data['tickers'], list)
    assert 'market_open' in data
    assert 'uptime_seconds' in data


@pytest.mark.django_db
def test_bot_trades_returns_list():
    response = auth_client('trades_int').get('/bot/trades/')
    assert response.status_code == 200
    data = response.json()
    assert 'trades' in data
    assert 'total' in data
    assert isinstance(data['trades'], list)


@pytest.mark.django_db
@patch('trading.views.IBKRConnector')
def test_buy_then_sell_creates_two_trade_records(mock_connector_class):
    from trading.models import Trade
    mock_connector = MagicMock()
    mock_connector.place_market_order.return_value = MOCK_ORDER
    mock_connector_class.return_value = mock_connector

    client = auth_client('buy_sell_int')
    client.post('/buy/', data=json.dumps({'ticker': 'AAPL', 'quantity': '5'}),
                content_type='application/json')
    mock_connector.place_market_order.return_value = {**MOCK_ORDER, 'action': 'SELL'}
    client.post('/sell/', data=json.dumps({'ticker': 'AAPL', 'quantity': '5'}),
                content_type='application/json')

    assert Trade.objects.filter(ticker='AAPL').count() == 2


@pytest.mark.django_db
def test_market_historical_with_ticker():
    response = auth_client('hist_int').get('/market/historical/', {'ticker': 'AAPL'})
    assert response.status_code == 200
    assert 'bars' in response.json()


@pytest.mark.django_db
def test_market_historical_missing_ticker():
    response = auth_client('hist_int2').get('/market/historical/')
    assert response.status_code == 400


@pytest.mark.django_db
def test_bot_trades_pagination():
    response = auth_client('page_int').get('/bot/trades/', {'page': 1, 'page_size': 10})
    assert response.status_code == 200
    data = response.json()
    assert data['page'] == 1
    assert data['page_size'] == 10


@pytest.mark.django_db
def test_unauthenticated_request_rejected():
    for path in ['/bot/status/', '/bot/trades/', '/buy/', '/sell/', '/current_prices/']:
        response = APIClient().get(path)
        assert response.status_code == 401, f"{path} should require auth"
