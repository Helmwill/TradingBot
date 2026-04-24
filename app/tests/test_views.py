"""
View tests — all IBKR calls mocked, no live connections.
"""
import json
import pytest
from unittest.mock import patch, MagicMock
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken


def make_auth_client(username='testuser_view'):
    user = User.objects.create_user(username=username, password='pass')
    refresh = RefreshToken.for_user(user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION='Bearer ' + str(refresh.access_token))
    return client


MOCK_ORDER = {
    'order_id': 'test-order-001',
    'status': 'Filled',
    'ticker': 'AAPL',
    'action': 'BUY',
    'quantity': 5,
    'fill_price': 175.50,
}


@pytest.mark.django_db
def test_health_check_returns_200():
    client = make_auth_client('hc_user')
    response = client.get(reverse('health_check'))
    assert response.status_code == 200
    assert response.json() == {"message": "Health check: status ok"}


@pytest.mark.django_db
def test_health_check_requires_auth():
    response = APIClient().get(reverse('health_check'))
    assert response.status_code == 401


@pytest.mark.django_db
def test_historical_data_missing_ticker_returns_400():
    client = make_auth_client('hist_user')
    response = client.get(reverse('historical-data'))
    assert response.status_code == 400


@pytest.mark.django_db
def test_historical_data_returns_bars():
    client = make_auth_client('hist_user2')
    response = client.get(reverse('historical-data'), {'ticker': 'AAPL'})
    assert response.status_code == 200
    assert 'bars' in response.json()


@pytest.mark.django_db
@patch('trading.views.IBKRConnector')
def test_current_prices_returns_price(mock_connector_class):
    import pandas as pd
    import numpy as np
    mock_connector = MagicMock()
    mock_connector.get_bars.return_value = pd.DataFrame({
        'timestamp': pd.date_range('2025-01-01', periods=5, freq='1min'),
        'open': [174]*5, 'high': [176]*5, 'low': [173]*5,
        'close': [175.50]*5, 'volume': [1000]*5,
    })
    mock_connector_class.return_value = mock_connector
    client = make_auth_client('price_user')
    response = client.get(reverse('current_prices'), {'ticker': 'AAPL'})
    assert response.status_code == 200
    assert response.json()['ticker'] == 'AAPL'
    assert response.json()['price'] == 175.50


@pytest.mark.django_db
def test_current_prices_missing_ticker_returns_400():
    client = make_auth_client('price_user2')
    response = client.get(reverse('current_prices'))
    assert response.status_code == 400


@pytest.mark.django_db
@patch('trading.views.IBKRConnector')
def test_buy_request_success(mock_connector_class):
    mock_connector = MagicMock()
    mock_connector.place_market_order.return_value = MOCK_ORDER
    mock_connector_class.return_value = mock_connector
    client = make_auth_client('buy_user')
    response = client.post(
        reverse('buy_request'),
        json.dumps({'ticker': 'AAPL', 'quantity': '5'}),
        content_type='application/json',
    )
    assert response.status_code == 200
    assert response.json()['order_id'] == 'test-order-001'


@pytest.mark.django_db
@patch('trading.views.IBKRConnector')
def test_sell_request_success(mock_connector_class):
    mock_connector = MagicMock()
    mock_connector.place_market_order.return_value = {**MOCK_ORDER, 'action': 'SELL'}
    mock_connector_class.return_value = mock_connector
    client = make_auth_client('sell_user')
    response = client.post(
        reverse('sell_request'),
        json.dumps({'ticker': 'TSLA', 'quantity': '2'}),
        content_type='application/json',
    )
    assert response.status_code == 200


@pytest.mark.django_db
def test_buy_request_missing_params_returns_400():
    client = make_auth_client('buy_user2')
    response = client.post(
        reverse('buy_request'),
        json.dumps({'ticker': 'AAPL'}),
        content_type='application/json',
    )
    assert response.status_code == 400


@pytest.mark.django_db
@patch('trading.views.IBKRConnector')
def test_buy_creates_trade_record(mock_connector_class):
    from trading.models import Trade
    mock_connector = MagicMock()
    mock_connector.place_market_order.return_value = MOCK_ORDER
    mock_connector_class.return_value = mock_connector
    client = make_auth_client('buy_user3')
    count_before = Trade.objects.count()
    client.post(
        reverse('buy_request'),
        json.dumps({'ticker': 'AAPL', 'quantity': '5'}),
        content_type='application/json',
    )
    assert Trade.objects.count() == count_before + 1
    trade = Trade.objects.latest('timestamp')
    assert trade.ticker == 'AAPL'
    assert trade.action == 'BUY'


@pytest.mark.django_db
def test_bot_status_returns_running():
    client = make_auth_client('status_user')
    response = client.get(reverse('bot_status'))
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'running'
    assert data['broker'] == 'Interactive Brokers'
    assert 'tickers' in data
    assert 'market_open' in data
    assert isinstance(data['tickers'], list)


@pytest.mark.django_db
def test_bot_trades_returns_list():
    client = make_auth_client('trades_user')
    response = client.get(reverse('bot_trades'))
    assert response.status_code == 200
    data = response.json()
    assert 'trades' in data
    assert 'total' in data


@pytest.mark.django_db
def test_bot_trades_pagination():
    client = make_auth_client('trades_user2')
    response = client.get(reverse('bot_trades'), {'page': 1, 'page_size': 10})
    assert response.status_code == 200
    data = response.json()
    assert data['page'] == 1
    assert data['page_size'] == 10


@pytest.mark.django_db
def test_unauthenticated_request_rejected():
    for path in ['/bot/status/', '/bot/trades/', '/buy/', '/sell/', '/current_prices/']:
        response = APIClient().get(path)
        assert response.status_code == 401, f"{path} should require auth"
