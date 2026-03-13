import json
import pytest
from unittest.mock import patch
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken


def auth_client():
    user = User.objects.create_user(username='viewer', password='pass')
    refresh = RefreshToken.for_user(user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION='Bearer ' + str(refresh.access_token))
    return client


@pytest.mark.django_db
def test_health_check_returns_200():
    client = auth_client()
    response = client.get(reverse('health_check'))
    assert response.status_code == 200
    assert response.json() == {"message": "Health check: status ok"}


@pytest.mark.django_db
def test_health_check_requires_auth():
    response = APIClient().get(reverse('health_check'))
    assert response.status_code == 401


@pytest.mark.django_db
def test_historical_data_returns_501():
    client = auth_client()
    response = client.get(reverse('historical-data'))
    assert response.status_code == 501


@pytest.mark.django_db
@patch('trading.views._ctrader_client')
def test_current_prices_returns_price(mock_client):
    mock_client.get_spot_price.return_value = 175.50
    client = auth_client()
    response = client.get(reverse('current_prices'), {'symbol': 'AAPL'})
    assert response.status_code == 200
    data = response.json()
    assert data['symbol'] == 'AAPL'
    assert data['price'] == 175.50


@pytest.mark.django_db
def test_current_prices_missing_symbol_returns_400():
    client = auth_client()
    response = client.get(reverse('current_prices'))
    assert response.status_code == 400


@pytest.mark.django_db
@patch('trading.views._ctrader_client')
def test_buy_request_success(mock_client):
    mock_client.place_order.return_value = {
        'order_id': 'test-buy-001',
        'status': 'FILLED',
        'symbol': 'AAPL',
        'side': 'BUY',
        'volume': 1.0,
        'price': 175.50,
    }
    client = auth_client()
    response = client.post(
        reverse('buy_request'),
        json.dumps({'symbol': 'AAPL', 'amount': '1.0'}),
        content_type='application/json',
    )
    assert response.status_code == 200
    assert response.json()['order_id'] == 'test-buy-001'


@pytest.mark.django_db
@patch('trading.views._ctrader_client')
def test_sell_request_success(mock_client):
    mock_client.place_order.return_value = {
        'order_id': 'test-sell-001',
        'status': 'FILLED',
        'symbol': 'TSLA',
        'side': 'SELL',
        'volume': 0.5,
        'price': 195.30,
    }
    client = auth_client()
    response = client.post(
        reverse('sell_request'),
        json.dumps({'symbol': 'TSLA', 'amount': '0.5'}),
        content_type='application/json',
    )
    assert response.status_code == 200
    assert response.json()['order_id'] == 'test-sell-001'


@pytest.mark.django_db
def test_buy_request_missing_params_returns_400():
    client = auth_client()
    response = client.post(
        reverse('buy_request'),
        json.dumps({'symbol': 'AAPL'}),
        content_type='application/json',
    )
    assert response.status_code == 400


@pytest.mark.django_db
@patch('trading.views._ctrader_client')
def test_buy_creates_trade_record(mock_client):
    from trading.models import Trade
    mock_client.place_order.return_value = {
        'order_id': 'test-trade-record',
        'status': 'FILLED',
        'symbol': 'AAPL',
        'side': 'BUY',
        'volume': 1.0,
        'price': 175.50,
    }
    client = auth_client()
    count_before = Trade.objects.count()
    client.post(
        reverse('buy_request'),
        json.dumps({'symbol': 'AAPL', 'amount': '1.0'}),
        content_type='application/json',
    )
    assert Trade.objects.count() == count_before + 1
    trade = Trade.objects.latest('timestamp')
    assert trade.instrument == 'AAPL'
    assert trade.action == 'BUY'
