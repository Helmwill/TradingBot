"""
Tests for Celery trading tasks.
All IBKR calls and signal engine calls are mocked — no live connections.
"""
import pytest
from unittest.mock import patch, MagicMock
from decimal import Decimal


MOCK_SIGNAL_BUY = {'action': 'BUY', 'confidence': 0.8, 'indicators': {}}
MOCK_SIGNAL_HOLD = {'action': 'HOLD', 'confidence': 0.0, 'indicators': {}}
MOCK_ORDER_FILLED = {
    'order_id': 'task-test-001',
    'status': 'Filled',
    'ticker': 'AAPL',
    'action': 'BUY',
    'quantity': 5,
    'fill_price': 175.50,
}


def _make_ohlcv_df(n=100):
    import pandas as pd
    import numpy as np
    rng = np.random.default_rng(42)
    close = 175.0 + rng.standard_normal(n).cumsum() * 0.5
    return pd.DataFrame({
        'timestamp': pd.date_range('2025-01-01', periods=n, freq='5min'),
        'open': close - 0.1, 'high': close + 0.5,
        'low': close - 0.5, 'close': close,
        'volume': rng.uniform(1000, 5000, n),
    })


@pytest.mark.django_db
@patch('trading.tasks.is_market_open', return_value=True)
@patch('trading.tasks.IBKRConnector')
@patch('trading.tasks.create_signal_engine')
def test_buy_signal_creates_trade(mock_engine_factory, mock_connector_class, mock_market_open):
    from trading.tasks import run_trading_cycle
    from trading.models import Trade

    mock_connector = MagicMock()
    mock_connector.get_bars.return_value = _make_ohlcv_df()
    mock_connector.place_market_order.return_value = MOCK_ORDER_FILLED
    mock_connector_class.return_value = mock_connector

    mock_engine = MagicMock()
    mock_engine.evaluate.return_value = MOCK_SIGNAL_BUY
    mock_engine_factory.return_value = mock_engine

    result = run_trading_cycle('AAPL')

    assert result['action'] == 'BUY'
    assert Trade.objects.filter(ticker='AAPL', action='BUY').exists()
    trade = Trade.objects.get(ticker='AAPL', action='BUY')
    assert trade.order_id == 'task-test-001'
    assert trade.fill_price == Decimal('175.5')


@pytest.mark.django_db
@patch('trading.tasks.is_market_open', return_value=True)
@patch('trading.tasks.IBKRConnector')
@patch('trading.tasks.create_signal_engine')
def test_hold_signal_creates_no_trade(mock_engine_factory, mock_connector_class, mock_market_open):
    from trading.tasks import run_trading_cycle
    from trading.models import Trade

    mock_connector = MagicMock()
    mock_connector.get_bars.return_value = _make_ohlcv_df()
    mock_connector_class.return_value = mock_connector

    mock_engine = MagicMock()
    mock_engine.evaluate.return_value = MOCK_SIGNAL_HOLD
    mock_engine_factory.return_value = mock_engine

    count_before = Trade.objects.count()
    result = run_trading_cycle('AAPL')

    assert result['action'] == 'HOLD'
    assert Trade.objects.count() == count_before


@pytest.mark.django_db
@patch('trading.tasks.is_market_open', return_value=True)
@patch('trading.tasks.IBKRConnector')
@patch('trading.tasks.create_signal_engine')
def test_ohlcv_bars_are_persisted(mock_engine_factory, mock_connector_class, mock_market_open):
    from trading.tasks import run_trading_cycle
    from trading.models import OHLCVBar

    mock_connector = MagicMock()
    mock_connector.get_bars.return_value = _make_ohlcv_df(n=5)
    mock_connector_class.return_value = mock_connector

    mock_engine = MagicMock()
    mock_engine.evaluate.return_value = MOCK_SIGNAL_HOLD
    mock_engine_factory.return_value = mock_engine

    run_trading_cycle('TSLA')

    assert OHLCVBar.objects.filter(ticker='TSLA').count() == 5


@pytest.mark.django_db
@patch('trading.tasks.is_market_open', return_value=False)
def test_market_closed_returns_early(mock_market_open):
    from trading.tasks import run_trading_cycle
    result = run_trading_cycle('AAPL')
    assert result['action'] == 'MARKET_CLOSED'


@pytest.mark.django_db
@patch('trading.tasks.is_market_open', return_value=True)
@patch('trading.tasks.IBKRConnector')
@patch('trading.tasks.create_signal_engine')
def test_ibkr_error_triggers_retry(mock_engine_factory, mock_connector_class, mock_market_open):
    from trading.tasks import run_trading_cycle
    from trading.broker.ibkr import IBKRError

    mock_connector = MagicMock()
    mock_connector.get_bars.side_effect = IBKRError("connection refused")
    mock_connector_class.return_value = mock_connector
    mock_engine_factory.return_value = MagicMock()

    with pytest.raises(IBKRError):
        run_trading_cycle('AAPL')
