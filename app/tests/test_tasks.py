"""
Tests for the Celery trading tasks.
All cTrader API calls and signal layer calls are mocked — no live API, no live Celery broker.
"""
import pytest
from unittest.mock import patch, MagicMock
from decimal import Decimal


MOCK_SIGNAL_BUY = {'action': 'BUY', 'confidence': 0.8, 'metadata': {}}
MOCK_SIGNAL_HOLD = {'action': 'HOLD', 'confidence': 0.0, 'metadata': {}}
MOCK_ORDER = {
    'order_id': 'task-test-001',
    'status': 'FILLED',
    'symbol': 'AAPL',
    'side': 'BUY',
    'volume': 1.0,
    'price': 175.50,
}


@pytest.mark.django_db
@patch('trading.tasks.CTraderClient')
@patch('trading.tasks.create_signal_layer')
def test_trading_cycle_buy_creates_trade(mock_create_layer, mock_client_class):
    from trading.tasks import run_trading_cycle
    from trading.models import Trade

    mock_client = MagicMock()
    mock_client.get_ohlcv_bars.return_value = _make_ohlcv_df()
    mock_client.place_order.return_value = MOCK_ORDER
    mock_client_class.return_value = mock_client

    mock_layer = MagicMock()
    mock_layer.get_signal.return_value = MOCK_SIGNAL_BUY
    mock_create_layer.return_value = mock_layer

    result = run_trading_cycle('AAPL')

    assert result['action'] == 'BUY'
    assert Trade.objects.filter(instrument='AAPL', action='BUY').exists()
    trade = Trade.objects.get(instrument='AAPL', action='BUY')
    assert trade.order_id == 'task-test-001'
    assert trade.price == Decimal('175.5')


@pytest.mark.django_db
@patch('trading.tasks.CTraderClient')
@patch('trading.tasks.create_signal_layer')
def test_trading_cycle_hold_creates_no_trade(mock_create_layer, mock_client_class):
    from trading.tasks import run_trading_cycle
    from trading.models import Trade

    mock_client = MagicMock()
    mock_client.get_ohlcv_bars.return_value = _make_ohlcv_df()
    mock_client_class.return_value = mock_client

    mock_layer = MagicMock()
    mock_layer.get_signal.return_value = MOCK_SIGNAL_HOLD
    mock_create_layer.return_value = mock_layer

    count_before = Trade.objects.count()
    result = run_trading_cycle('AAPL')

    assert result['action'] == 'HOLD'
    assert Trade.objects.count() == count_before


@pytest.mark.django_db
@patch('trading.tasks.CTraderClient')
@patch('trading.tasks.create_signal_layer')
def test_trading_cycle_saves_ohlcv_bars(mock_create_layer, mock_client_class):
    from trading.tasks import run_trading_cycle
    from trading.models import OHLCVBar

    mock_client = MagicMock()
    mock_client.get_ohlcv_bars.return_value = _make_ohlcv_df(n=5)
    mock_client_class.return_value = mock_client

    mock_layer = MagicMock()
    mock_layer.get_signal.return_value = MOCK_SIGNAL_HOLD
    mock_create_layer.return_value = mock_layer

    run_trading_cycle('TSLA')

    assert OHLCVBar.objects.filter(instrument='TSLA').count() == 5


@pytest.mark.django_db
@patch('trading.tasks.CTraderClient')
@patch('trading.tasks.create_signal_layer')
def test_trading_cycle_retries_on_ctrader_error(mock_create_layer, mock_client_class):
    from trading.tasks import run_trading_cycle
    from trading.ctrader_client import CTraderClientError

    mock_client = MagicMock()
    mock_client.get_ohlcv_bars.side_effect = CTraderClientError("connection refused")
    mock_client_class.return_value = mock_client
    mock_create_layer.return_value = MagicMock()

    with pytest.raises(CTraderClientError):
        run_trading_cycle('AAPL')


def _make_ohlcv_df(n=20):
    import pandas as pd
    import numpy as np
    close = 175.0 + np.random.randn(n).cumsum()
    return pd.DataFrame({
        'timestamp': pd.date_range('2025-01-01', periods=n, freq='1h'),
        'open': close - 0.1, 'high': close + 0.5,
        'low': close - 0.5, 'close': close,
        'volume': np.abs(np.random.randn(n) * 1000) + 500,
    })
